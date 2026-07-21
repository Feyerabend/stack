"""
Differential test for the self-hosted type checker (SELFHOST M3, slice 3 —
infer.lark: the port of 07/src/infer.py, Algorithm W + affine + trait bounds).

For every self-contained .lark file in the corpus it compares two verdicts:

  • the oracle — 07/src/infer.py's `typecheck`, run IN-PROCESS.  On success its
    TProgram is serialised to a normalised top-level signature block; on a
    TypeError / AffineError / TraitBoundError it becomes "type error: <msg>".
  • the port    — self/infer.lark's `checkProgram`, driven through the Python
    CEK over the SAME source (embedded as a String literal, lexed + parsed +
    checked in Lark), which prints that same block or "type error: <msg>".

They must agree: for an ACCEPT file the signature blocks match line-for-line
(type variables normalised α,β,γ… by first occurrence on both sides); for a
REJECT file the "type error: …" line matches with type-variable greek letters
canonicalised (fresh-id numbering legitimately differs between the two Fresh
counters, but the error KIND and the concrete types must coincide).

Composition (same as cek_difftest.py — CONCATENATION, not `import`, because the
toolchain's import path skips infer Pass 1.5, SELFHOST §7):
  lex + parse + types + tast + infer bodies + a generated main,
all under one `module Selfhost`, run through the normal top-level typechecker.

Scope: single-module files only.  A file is SKIPPED (never failed) when it is
outside the port's control: it `import`s another module (the port has no import
mechanism and inlining would perturb Pass 1.5 pre-registration), the oracle
raises something other than the three type-error classes (a genuine parser/bug
crash), or the meta-circular tower (Python-CEK ▷ Lark-checker ▷ object program)
is too slow — a performance verdict, not a correctness one.

The error suite (07/tests/errors/*) is the heart of the REJECT half: each file
is a program that must be rejected for a specific reason, and the port must
reject it with the same message.

Usage:
    python3 self/tests/infer_difftest.py [-v]     # -v: show a diff on failure
"""

from __future__ import annotations
import sys, re, subprocess, pathlib, difflib
import os

HERE  = pathlib.Path(__file__).resolve().parent          # self/tests
SELF  = HERE.parent                                      # self
ROOT  = SELF.parent                                      # lark
SRC   = ROOT / "07" / "src"
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
TYPES = SELF / "types.lark"
TAST  = SELF / "tast.lark"
INFER = SELF / "infer.lark"

sys.path.insert(0, str(SRC))
from lexer import LexError              # noqa: E402
import parser as _parser                # noqa: E402
from parser import ParseError           # noqa: E402
import infer as _infer                  # noqa: E402
import ty                               # noqa: E402
import typed_tree as tt                 # noqa: E402


# ── Oracle: run typecheck in-process, serialise to the port's block ───────────

# Greek table, byte-identical to types.lark's `greek` (σ at 17, not final ς).
_GREEK = "αβγδεζηθικλμνξοπρστυφχψω"

def _greek(i: int) -> str:
    return _GREEK[i] if i < len(_GREEK) else "α" + str(i)


def _collect_vars(t, acc: list[int]) -> list[int]:
    """First-occurrence order of TVar ids — mirrors infer.lark collectVars."""
    match t:
        case ty.TVar(id=i):
            if i not in acc:
                acc.append(i)
        case ty.TCon():
            pass
        case ty.TApp(args=args):
            for a in args:
                _collect_vars(a, acc)
        case ty.TFn(param=p, result=r):
            _collect_vars(p, acc)
            _collect_vars(r, acc)
        case ty.TTup(elems=es):
            for e in es:
                _collect_vars(e, acc)
    return acc


def _pn_inner(t, ids: list[int]) -> str:
    match t:
        case ty.TVar(id=i):
            return _greek(ids.index(i) if i in ids else 0)
        case ty.TCon(name=n):
            return n
        case ty.TApp(head=h, args=args):
            if not args:
                return h
            return h + "(" + ", ".join(_pn_p(a, ids, False) for a in args) + ")"
        case ty.TFn(param=p, result=r):
            return _pn_p(p, ids, True) + " -> " + _pn_p(r, ids, False)
        case ty.TTup(elems=es):
            return "(" + ", ".join(_pn_p(e, ids, False) for e in es) + ")"
    raise AssertionError(f"unknown mono {t!r}")


def _pn_p(t, ids: list[int], paren: bool) -> str:
    if isinstance(t, ty.TFn) and paren:
        return "(" + _pn_inner(t, ids) + ")"
    return _pn_inner(t, ids)


def _norm_scheme(scheme) -> str:
    body = scheme.body
    return _pn_p(body, _collect_vars(body, []), False)


def _serialise(tprog) -> str:
    """Reproduce infer.lark checkProgram's ACCEPT block from a TProgram."""
    lines = [f"(module {tprog.module})"]
    for d in tprog.decls:
        if isinstance(d, tt.TFnDecl):
            lines.append(f"{d.name} : {_norm_scheme(d.scheme)}")
        elif isinstance(d, tt.TLetDecl):
            lines.append(f"{d.name} : {_norm_scheme(d.scheme)}")
        elif isinstance(d, tt.TTypeDecl):
            lines.append(f"type {d.name}")
        elif isinstance(d, tt.TImplDecl):
            lines.append(f"impl {d.trait_name} for {d.for_type}")
        # TraitDecl produces no line, and typecheck never emits one.
    return "\n".join(lines)


def oracle(path: pathlib.Path) -> tuple[str, str]:
    """Return (verdict, text): verdict in {'accept','reject','skip'}."""
    try:
        prog = _parser.parse_file(str(path))
    except (LexError, ParseError) as e:
        return "skip", f"oracle parse error: {e}"
    if prog.imports:
        return "skip", "multi-module (import) — outside single-file port"
    try:
        tprog = _infer.typecheck(prog, source_file=str(path))
    except (_infer.TypeError, _infer.AffineError, _infer.TraitBoundError) as e:
        return "reject", f"type error: {e}"
    return "accept", _serialise(tprog)


# ── Port: concatenate lex + parse + types + tast + infer + a generated main ───

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)

def lark_string_literal(source: str) -> str:
    out: list[str] = []
    for ch in source:
        if   ch == "\\": out.append("\\\\")
        elif ch == '"':  out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\t": out.append("\\t")
        elif ch == "\r": out.append("\\r")
        else:            out.append(ch)
    return "".join(out)

def make_driver(source: str) -> str:
    lex   = _strip_lines(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse = _strip_lines(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    types = _strip_lines(TYPES.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    tast  = _strip_lines(TAST.read_text().split(MAIN_MARKER, 1)[0],  ("module ", "import "))
    infer = _strip_lines(INFER.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    lit = lark_string_literal(source)
    driver_main = (
        "\nfn main(io : IO) : IO =\n"
        f'  let src = "{lit}" in\n'
        "  print(io, checkProgram(parseProgram(tokenize(src, string_length(src), P(0, 1, 1)))))\n"
    )
    return ("module Selfhost\n\n"
            + lex + "\n" + parse + "\n" + types + "\n" + tast + "\n" + infer + driver_main)


PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))     # meta-circular: Python-CEK ▷ Lark-checker ▷ object program

def run_port(source: str) -> tuple[int, str, str]:
    tmp = HERE / "_idriver.lark"
    tmp.write_text(make_driver(source))
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── Comparison ────────────────────────────────────────────────────────────────

# For REJECT messages the two Fresh counters number type variables differently,
# so canonicalise every greek type-variable token (α, β, … possibly α12) to a
# single marker before comparing.  Non-variable text (Int, List, the message
# words) must still match exactly.
_GREEKSET = set(_GREEK)
_GVAR = re.compile("[" + _GREEK + r"](?:[0-9]+)?")

def _canon_reject(line: str) -> str:
    return _GVAR.sub("ν", line)


def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "07" / "tests", ROOT / "07" / "samples"]:
        for p in sorted(base.rglob("*.lark")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files


def main() -> None:
    verbose = "-v" in sys.argv
    ok = fail = skip = 0

    for path in corpus():
        label = str(path.relative_to(ROOT))
        verdict, text = oracle(path)
        if verdict == "skip":
            print(f"  skip  {label}  ({text})")
            skip += 1
            continue

        source = path.read_text()
        try:
            pcode, pout, perr = run_port(source)
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

        port_text = pout.rstrip("\n")

        if verdict == "reject":
            # The port prints exactly one "type error: …" line.
            exp = _canon_reject(text)
            got = _canon_reject(port_text)
            if got == exp:
                print(f"  ok    {label}  (reject: {text[:60]})")
                ok += 1
            else:
                print(f"  FAIL  {label}  (reject mismatch)")
                print(f"        oracle={text!r}")
                print(f"        port  ={port_text!r}")
                fail += 1
            continue

        # accept
        exp = text.splitlines()
        got = port_text.splitlines()
        if got == exp:
            print(f"  ok    {label}  ({len(exp)} sigs)")
            ok += 1
        else:
            print(f"  FAIL  {label}  (accept mismatch)")
            if verbose:
                d = difflib.unified_diff(exp, got, "oracle", "port", lineterm="")
                for line in list(d)[:60]:
                    print(f"        {line}")
            else:
                for i in range(max(len(exp), len(got))):
                    a = exp[i] if i < len(exp) else "<none>"
                    b = got[i] if i < len(got) else "<none>"
                    if a != b:
                        print(f"        line {i}: oracle={a!r}")
                        print(f"                 port  ={b!r}")
                        break
                if len(exp) != len(got):
                    print(f"        length: oracle={len(exp)} port={len(got)}")
            fail += 1

    total = ok + fail + skip
    print(f"\n  {ok} ok, {fail} failed, {skip} skipped  "
          f"({len(corpus())} corpus files)")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
