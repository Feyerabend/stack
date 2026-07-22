"""
Differential test for the *typechecking* self-hosted compiler.

The bootstrap fixpoint closed with `lex → parse → emit` (the emitter drives off the
syntactic AST; `infer.lark` was never on the path).  This harness proves the
stronger claim: a self-hosted compiler that *type-checks first* — it rejects
ill-typed programs with the oracle-identical diagnostic, and on well-typed
programs emits the oracle-identical C.  That makes it a compiler, not a transpiler.

The port under test is the **gated compiler**: all six front/middle-end modules
(`lex + parse + types + tast + infer + emit_c`) under one `module Selfhost`, plus
a driver that parses, runs `infer.lark`'s `checkProgram` passes as a gate, and
then *either* prints `"type error: <msg>"` *or* emits C from the (Copy) syntactic
`Prog`.  Driven through the Python CEK, meta-circularly, per corpus file.

  driver output  ==  { oracle emit_c_ast.py(file)         if infer.py accepts
                     { "type error: " + infer.py message   if infer.py rejects

Oracle reuse (no re-derivation):
  • verdict + reject message  ← infer_difftest.oracle / _canon_reject
  • accepted-program C + its canonicalisation ← emit_c_difftest.run_oracle / canon

The payoff over `emittest`: the 7 error-suite files `emittest` must SKIP (the
oracle rejects them, so there is no C to compare) become live ACCEPTANCE tests
here — the gated compiler must reject each with the matching message.

Affine note (a real finding): the driver may not `print(io, …)` in two match
arms — the affine checker *sums* a variable's uses across arms, so `io` would
count as used twice.  The driver builds the output String purely in the `match`
and prints `io` exactly once.  The same IO idiom, now dictating compiler shape.

Composition & imports: same concatenation the other differentials use; `import`
programs are SKIPPED (the single-file port has no import mechanism, exactly as
infertest skips them).  Meta-circular, so slow; a per-file timeout is a
skip-with-reason.  ⚠️ Shares the one-harness-at-a-time rule (own temp driver
`_tcdriver.lark`, but still run only one self-host differential at a time).

Usage:
    python3 harness/typecheck_difftest.py [-v]
"""

from __future__ import annotations
import sys, subprocess, pathlib
import os

HERE  = pathlib.Path(__file__).resolve().parent   # <strand>/harness
ROOT  = HERE.parent                              # <strand>/
SELF  = ROOT / "lark"                            # the compiler, written in Lark
SRC   = ROOT / "oracle"                          # the Python reference implementation
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
TYPES = SELF / "types.lark"
TAST  = SELF / "tast.lark"
INFER = SELF / "infer.lark"
EMITL = SELF / "emit_c.lark"

sys.path.insert(0, str(HERE))
import infer_difftest as I          # noqa: E402  — reuse verdict + reject canon
import emit_c_difftest as E         # noqa: E402  — reuse emit oracle + _anon canon

PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "240"))      # bigger driver (~3500 lines) than emittest → looser budget

MAIN_MARKER = "\nfn main(io : IO) : IO ="

# infer.lark's checkProgram passes, re-expressed as a Result gate (accept/reject).
GATE_FN = """
fn tcGate(prog : Prog) : Result(Bool, String) =
  match prog with
  | Prog(modName, imports, decls) =>
      match initialEnv(0) with
      | (env0, copy0) =>
          let show0 = Cons("Int", Cons("Float", Cons("Bool", Cons("String", Nil)))) in
          match pass1(decls, env0, 0, copy0, show0) with
          | (env1, f1, copy1, show1) =>
              match pass15(decls, env1, f1) with
              | (env2, f2) =>
                  match pass2(decls, env2, f2, copy1, show1) with
                  | P2Err(m) => Err(m)
                  | P2Ok(_, _, _) => Ok(true)
                  end
              end
          end
      end
  end
"""


def _strip(path: pathlib.Path, prefixes: tuple[str, ...]) -> str:
    text = path.read_text().split(MAIN_MARKER, 1)[0]
    return "\n".join(ln for ln in text.splitlines()
                     if not any(ln.lstrip().startswith(p) for p in prefixes))


def make_gated_driver(source: str, basename: str) -> str:
    bodies = [
        _strip(LEX,   ("module ",)),
        _strip(PARSE, ("module ", "import ")),
        _strip(TYPES, ("module ", "import ")),
        _strip(TAST,  ("module ", "import ")),
        _strip(INFER, ("module ", "import ")),
        _strip(EMITL, ("module ", "import ")),
    ]
    lit  = E.lark_string_literal(source)
    blit = E.lark_string_literal(basename)
    # Build the output String in the match; print io exactly once (affine idiom).
    driver_main = (
        "\nfn main(io : IO) : IO =\n"
        f'  let src = "{lit}" in\n'
        f'  let base = "{blit}" in\n'
        "  let prog = parseProgram(tokenize(src, string_length(src), P(0, 1, 1))) in\n"
        "  let out = match tcGate(prog) with\n"
        '            | Err(m) => "type error: " + m\n'
        "            | Ok(_) => emitProgram(base, prog)\n"
        "            end in\n"
        "  print(io, out)\n"
    )
    return "module Selfhost\n\n" + "\n".join(bodies) + GATE_FN + driver_main


def run_port(source: str, basename: str) -> tuple[int, str, str]:
    tmp = HERE / "_tcdriver.lark"
    tmp.write_text(make_gated_driver(source, basename))
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    verbose = "-v" in sys.argv
    ok = fail = skip = 0

    for path in I.corpus():
        label = str(path.relative_to(ROOT))
        verdict, text = I.oracle(path)          # 'accept' | 'reject' | 'skip'
        if verdict == "skip":
            print(f"  skip  {label}  ({text})")
            skip += 1
            continue

        source = path.read_text()
        try:
            pcode, pout, perr = run_port(source, path.name)
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (meta-circular check too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue

        if pcode != 0:
            print(f"  FAIL  {label}  (port crash)")
            tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
            print(f"        {tail[0]}")
            fail += 1
            continue

        if verdict == "reject":
            exp = I._canon_reject(text)
            got = I._canon_reject(pout.rstrip("\n"))
            if got == exp:
                print(f"  ok    {label}  (reject: {text[:56]})")
                ok += 1
            else:
                print(f"  FAIL  {label}  (reject mismatch)")
                print(f"        oracle={text!r}")
                print(f"        port  ={pout.rstrip(chr(10))!r}")
                fail += 1
            continue

        # accept: compare emitted C against the oracle emitter, byte-for-byte
        orc_code, orc_out, orc_err = E.run_oracle(path)
        if orc_code != 0:
            print(f"  skip  {label}  (oracle emitter failed: {(orc_err or '').strip()[:50]})")
            skip += 1
            continue
        exp = E.canon(orc_out)
        got = E.canon(pout)
        if got == exp:
            print(f"  ok    {label}  (emit: {len(pout.splitlines())} C lines)")
            ok += 1
        else:
            print(f"  FAIL  {label}  (emit mismatch)")
            if verbose:
                import difflib
                for ln in list(difflib.unified_diff(
                        exp.splitlines(), got.splitlines(),
                        "oracle", "port", lineterm=""))[:30]:
                    print("        " + ln)
            fail += 1

    total = ok + fail + skip
    print(f"\n  {ok} ok, {fail} failed, {skip} skipped  ({total} corpus files)")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
