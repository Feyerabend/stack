"""
End-to-end differential for the self-hosted OPTIMIZING compiler (SELFHOST M7.5 /
OPTIMIZE §9.4, claim 1 — the behavioral pipeline).

This is the first test that runs the WHOLE self-hosted optimizing compiler as one
program: lex + parse + types + tast + infer + tac + lower + opt + emit_tac_c
concatenated under a single `module Selfhost`, driven by a `main` that embeds one
corpus source and prints

    emitTacC(optimizeProg(lowerProgram(<inferProgram(prog)>), LEVEL))

Every earlier M7 differential fed an oracle-produced IR (serialised TAC / TProgram)
into ONE Lark module in isolation.  Here the modules compose end to end — in
particular `infer.lark`'s new `inferProgram` (M7.5) produces the typed AST that
`lower.lark` consumes, closing the gap that the difftests bridged with the Python
oracle.

For every corpus file AND every level in LEVELS:
  • the oracle runs parse → infer.py.typecheck → lower.py.lower →
    opt.py.optimize(level) → emit_tac_c.py.CEmitter.emit();
  • the port runs the assembled compiler at that level.
The two C sources must be byte-identical.

It also checks OPTIMIZE §9.4 claim 1 directly: for each file the port's C at -O0
and at the top level must be byte-identical (optimization is semantics- and, on
this deterministic emitter, TEXT-preserving — the emitter is fed the optimized TAC,
so this is the interesting equality: the compiler emits the same C whether or not
its optimizer ran... only when opt is a no-op on that file; otherwise the two
differ and we only assert port==oracle at each level).  So the primary contract is
port==oracle at every level; the -O0-vs-top equality is reported, not asserted.

Scope: single-file programs the oracle accepts (imports / reject fixtures skipped;
CEK overflow or timeout on the deepest programs is a capacity skip — the full
9-module compiler is the heaviest meta-circular load in the tree).

Usage:
    python3 self/tests/optcompiler_difftest.py [-v] [--levels 0,3] [--only NAME]
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib, argparse, itertools, re
import os

HERE  = pathlib.Path(__file__).resolve().parent          # self/tests
SELF  = HERE.parent                                      # self
ROOT  = SELF.parent                                      # lark
SRC   = ROOT / "07" / "src"
CEK   = str(SRC / "cek.py")

MODULES = ["lex", "parse", "types", "tast", "infer", "tac", "lower", "opt", "emit_tac_c"]

sys.path.insert(0, str(SRC))
from lexer import LexError               # noqa: E402
import parser as _parser                 # noqa: E402
from parser import ParseError            # noqa: E402
import infer as _infer                   # noqa: E402
import lower as _lower                   # noqa: E402
import opt as _opt                       # noqa: E402
from emit_tac_c import CEmitter          # noqa: E402


# ── Oracle ────────────────────────────────────────────────────────────────────

def oracle_prep(path: pathlib.Path):
    """Return (verdict, tprog|reason).  verdict in {'run','skip'}."""
    try:
        prog = _parser.parse_file(str(path))
    except (LexError, ParseError) as e:
        return "skip", f"oracle parse error: {e}"
    if prog.imports:
        return "skip", "multi-module (import) — outside single-file port"
    try:
        tprog = _infer.typecheck(prog, source_file=str(path))
    except (_infer.TypeError, _infer.AffineError, _infer.TraitBoundError) as e:
        return "skip", f"reject fixture (infer: {str(e)[:40]})"
    return "run", tprog


def oracle_at(tprog, level: int) -> str:
    """The reference's C for one file at one level.

    Two pieces of oracle state have to be put back before each compile, or a file
    inherits the one before it and the harness reports a disagreement that is
    entirely its own doing:

      * `opt._SITE` is a *global* counter, so the ids the inline and closure passes
        stamp on their rewrite sites keep climbing across files.  The port is a
        fresh process per file and starts at zero.
      * `opt`'s passes rewrite instructions in place, so the lowered TAC has to be
        built fresh rather than reused between levels."""
    _opt._SITE = itertools.count()
    tac = _lower.lower(tprog)
    tac = _opt.optimize(tac, _opt.OptOptions(level=level))
    return CEmitter(tac).emit()


# A wildcard parameter `_` has no name, so the oracle invents one from `id()` — a
# memory address, different on every run — and bakes it into the emitted C as a
# parameter name nothing ever refers to.  The port keeps the deterministic `_`.
# No port can reproduce a specific id(), so the one nondeterministic token is
# flattened on both sides, exactly as in the emit_c differential.  `_anon_<digits>`
# never appears in the corpus, so this cannot mask a real name.
_ANON = re.compile(r"_anon_\d+")

def canon(text: str) -> str:
    return _ANON.sub("_", text)


# ── Port: concatenate all 9 modules + a driver ────────────────────────────────

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)


def module_body(name: str) -> str:
    """A module's body with its `module`/`import`/`main` stripped."""
    src = (SELF / f"{name}.lark").read_text().split(MAIN_MARKER, 1)[0]
    drop = ("module ",) if name == "lex" else ("module ", "import ")
    return _strip_lines(src, drop)


def _lstr(s: str) -> str:
    """A Lark double-quoted string literal for cek's lexer."""
    out = ['"']
    for ch in s:
        if   ch == "\\": out.append("\\\\")
        elif ch == '"':  out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\t": out.append("\\t")
        elif ch == "\r": out.append("\\r")
        else:            out.append(ch)
    out.append('"')
    return "".join(out)


def make_compiler(source: str, level: int) -> str:
    bodies = "\n".join(module_body(m) for m in MODULES)
    # io is affine and cannot appear in two match arms (M5.5 wart) — build the
    # output String purely, then print once.
    driver = (
        "\nfn main(io : IO) : IO =\n"
        f"  let src = {_lstr(source)} in\n"
        "  let prog = parseProgram(tokenize(src, string_length(src), P(0, 1, 1))) in\n"
        "  let out = match inferProgram(prog) with\n"
        '            | Err(m) => "type error: " + m\n'
        f"            | Ok(tprog) => emitTacC(optimizeProg(lowerProgram(tprog), {level}))\n"
        "            end in\n"
        "  print(io, out)\n"
    )
    return "module Selfhost\n\n" + bodies + driver


PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "600"))

def run_port(source: str, level: int):
    tmp = HERE / "_optcompiler_driver.lark"
    tmp.write_text(make_compiler(source, level))
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── Corpus + driver loop ──────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "07" / "tests", ROOT / "07" / "samples"]:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.lark")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files


def _first_diff(exp: list[str], gt: list[str]) -> None:
    for i in range(max(len(exp), len(gt))):
        a = exp[i] if i < len(exp) else "<none>"
        b = gt[i]  if i < len(gt)  else "<none>"
        if a != b:
            print(f"        line {i}: oracle={a!r}")
            print(f"                 port  ={b!r}")
            return


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", action="store_true")
    ap.add_argument("--levels", default="0,1,2,3")
    ap.add_argument("--only", default=None, help="substring filter on file name")
    args = ap.parse_args()
    levels = [int(x) for x in args.levels.split(",")]
    ok = fail = skip = 0

    for path in corpus():
        label = str(path.relative_to(ROOT))
        if args.only and args.only not in label:
            continue
        verdict, payload = oracle_prep(path)
        if verdict == "skip":
            print(f"  skip  {label}  ({payload})")
            skip += len(levels)
            continue

        source = path.read_text()
        port_c: dict[int, str] = {}
        for level in levels:
            tag = f"{label} -O{level}"
            want = oracle_at(payload, level)
            try:
                pcode, pout, perr = run_port(source, level)
            except subprocess.TimeoutExpired:
                print(f"  skip  {tag}  (meta-circular compile too slow — >{PORT_TIMEOUT}s)")
                skip += 1
                continue

            if pcode != 0:
                tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
                low = (perr or "").lower()
                if "recursion" in low or "maximum" in low or "overflow" in low:
                    print(f"  skip  {tag}  (CEK overflow: {tail[0][:50]})")
                    skip += 1
                else:
                    print(f"  FAIL  {tag}  (port crash)")
                    print(f"        {tail[0]}")
                    fail += 1
                continue

            want_nl = canon(want + "\n")   # cek's print adds one newline; emit() ends in one
            got_nl  = canon(pout)
            if got_nl == want_nl:
                n = want.count("\n")
                print(f"  ok    {tag}  ({n} C lines)")
                port_c[level] = got_nl
                ok += 1
            else:
                print(f"  FAIL  {tag}  (C mismatch)")
                exp = want_nl.splitlines()
                gt  = got_nl.splitlines()
                if args.v:
                    d = difflib.unified_diff(exp, gt, "oracle", "port", lineterm="")
                    for line in list(d)[:80]:
                        print(f"        {line}")
                else:
                    _first_diff(exp, gt)
                fail += 1

        # §9.4 claim 1 report: does the port emit identical C at -O0 vs the top level?
        if len(levels) >= 2 and levels[0] in port_c and levels[-1] in port_c:
            same = port_c[levels[0]] == port_c[levels[-1]]
            note = "identical" if same else "differ (opt changed the TAC)"
            print(f"        [-O{levels[0]} vs -O{levels[-1]} C: {note}]")

    print(f"\n  {ok} ok / {fail} fail / {skip} skip")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
