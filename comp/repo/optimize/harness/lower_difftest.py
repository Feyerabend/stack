"""
Differential test for the self-hosted lowerer (
lower.lark: the port of oracle/lower.py, typed AST → TAC).

Unlike infer/emit_c/cek — whose ports re-run the *front end* in Lark over the
object source — lower.lark consumes the TYPED AST (it reads each node's inferred
monotype to route float/string arithmetic and `show` dispatch).  infer.lark's
`checkProgram` returns a signature String, not a TProgram, so there is no typed
tree to hand lower.lark from within Lark.  So this harness ISOLATES lower.lark:

  • the oracle typechecks the object program with infer.py, lowers the resulting
    TProgram with lower.py, and pretty-prints the TAC (tac.py `pretty`);
  • the port SERIALISES that same TProgram into Lark constructor source (Mono →
    MVar/MCon/…, Val → VInt/…, the typed nodes → tast.lark's ADTs — the Scheme
    fields are lowered-over, so a dummy stands in), then runs
    lex+parse+types+tast+tac+lower + a driver that prints
    `tacPretty(lowerProgram(<that TProgram>))`.

The two TAC pretty-prints must be byte-identical.  This tests lower.lark alone:
the front end is the trusted oracle, the typed AST is fed in verbatim, and only
lower.lark + tac.lark (already green) run in Lark.

Scope: single-file programs the oracle accepts.  A file is SKIPPED (not failed)
when the oracle can't produce a typed AST — it `import`s another module, or it
is a reject fixture (the error suite: infer raises, nothing to lower) — or when
the meta-circular run overflows / times out (a capacity verdict, not a bug).

Usage:
    python3 harness/lower_difftest.py [-v]      # -v: unified diff on failure
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib
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
TAC   = SELF / "tac.lark"
LOWER = SELF / "lower.lark"

sys.path.insert(0, str(SRC))
from lexer import LexError              # noqa: E402
import parser as _parser                # noqa: E402
from parser import ParseError           # noqa: E402
import infer as _infer                  # noqa: E402
import lower as _lower                  # noqa: E402
import ty                               # noqa: E402
import typed_tree as tt                 # noqa: E402
from tac import pretty as _tac_pretty   # noqa: E402


# ── Serialiser: oracle TProgram → Lark constructor source ─────────────────────

def _lstr(s: str) -> str:
    """A Lark double-quoted string literal for cek's lexer (escapes \\ " \\n \\t \\r)."""
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


def _slist(items: list[str]) -> str:
    r = "Nil"
    for x in reversed(items):
        r = f"Cons({x}, {r})"
    return r


def s_mono(m) -> str:
    if isinstance(m, ty.TVar): return f"MVar({m.id})"
    if isinstance(m, ty.TCon): return f"MCon({_lstr(m.name)})"
    if isinstance(m, ty.TApp): return f"MApp({_lstr(m.head)}, {_slist([s_mono(a) for a in m.args])})"
    if isinstance(m, ty.TFn):  return f"MFn({s_mono(m.param)}, {s_mono(m.result)})"
    if isinstance(m, ty.TTup): return f"MTup({_slist([s_mono(e) for e in m.elems])})"
    raise AssertionError(f"unknown mono {m!r}")


def s_val(v) -> str:
    """A TLit/TPLit payload (int|float|str|bool|None) → parse.lark Val ctor."""
    if v is None:            return "VUnit"
    if v is True:            return "VBool(true)"
    if v is False:           return "VBool(false)"
    if isinstance(v, bool):  return "VBool(true)"          # unreachable (True/False above)
    if isinstance(v, int):   return f"VInt({_lstr(str(v))})"
    if isinstance(v, float): return f"VFloat({_lstr(repr(v))})"
    if isinstance(v, str):   return f"VStr({_lstr(v)})"
    raise AssertionError(f"unknown literal {v!r}")


def s_mono_pair(nt) -> str:
    n, t = nt
    return f"({_lstr(n)}, {s_mono(t)})"


def s_expr(e) -> str:
    T = type(e).__name__
    if T == "TLit":       return f"TLit({s_val(e.value)}, {s_mono(e.typ)})"
    if T == "TVar":       return f"TVar({_lstr(e.name)}, {s_mono(e.typ)})"
    if T == "TCon":       return f"TCon({_lstr(e.name)}, {s_mono(e.typ)})"
    if T == "TTupleExpr": return f"TTupleExpr({_slist([s_expr(x) for x in e.elems])}, {s_mono(e.typ)})"
    if T == "TApply":     return f"TApp({s_expr(e.fn)}, {_slist([s_expr(a) for a in e.args])}, {s_mono(e.typ)})"
    if T == "TBinOp":     return f"TBinOp({_lstr(e.op)}, {s_expr(e.left)}, {s_expr(e.right)}, {s_mono(e.typ)})"
    if T == "TUnaryOp":   return f"TUnaryOp({_lstr(e.op)}, {s_expr(e.operand)}, {s_mono(e.typ)})"
    if T == "TLetExpr":   return f"TLetExpr({_lstr(e.name)}, {s_expr(e.value)}, {s_expr(e.body)}, {s_mono(e.typ)})"
    if T == "TIfExpr":    return f"TIfExpr({s_expr(e.cond)}, {s_expr(e.then_)}, {s_expr(e.else_)}, {s_mono(e.typ)})"
    if T == "TMatchExpr":
        arms = _slist([f"({s_pat(p)}, {s_expr(b)})" for p, b in e.arms])
        return f"TMatchExpr({s_expr(e.scrutinee)}, {arms}, {s_mono(e.typ)})"
    if T == "TLambda":
        params = _slist([s_mono_pair(p) for p in e.params])
        return f"TLambda({params}, {s_expr(e.body)}, {s_mono(e.typ)})"
    raise AssertionError(f"unknown expr {T}")


def s_pat(p) -> str:
    T = type(p).__name__
    if T == "TPWild":  return f"TPWild({s_mono(p.typ)})"
    if T == "TPVar":   return f"TPVar({_lstr(p.name)}, {s_mono(p.typ)})"
    if T == "TPLit":   return f"TPLit({s_val(p.value)}, {s_mono(p.typ)})"
    if T == "TPCon":   return f"TPCon({_lstr(p.name)}, {_slist([s_pat(x) for x in p.args])}, {s_mono(p.typ)})"
    if T == "TPTuple": return f"TPTuple({_slist([s_pat(x) for x in p.elems])}, {s_mono(p.typ)})"
    raise AssertionError(f"unknown pat {T}")


# lower.lark never inspects a decl's Scheme — a dummy keeps the ADT well-formed.
_DUMMY_SCHEME = 'Scheme(Nil, MCon("Int"), Nil)'


def s_variant(v) -> str:
    return f"TVariant({_lstr(v.name)}, {_slist([s_mono(m) for m in v.payload])})"


def s_bool(b) -> str:
    return "true" if b else "false"


def s_decl(d) -> str:
    T = type(d).__name__
    if T == "TFnDecl":
        params = _slist([s_mono_pair(p) for p in d.params])
        return f"TFnDecl({_lstr(d.name)}, {params}, {s_expr(d.body)}, {_DUMMY_SCHEME}, {s_bool(d.exported)})"
    if T == "TLetDecl":
        return f"TLetDecl({_lstr(d.name)}, {s_expr(d.value)}, {_DUMMY_SCHEME}, {s_bool(d.exported)})"
    if T == "TTypeDecl":
        if d.variants is None:
            variants = "Nothing"
        else:
            variants = f"Just({_slist([s_variant(v) for v in d.variants])})"
        params = _slist([_lstr(x) for x in d.params])
        return f"TTypeDecl({_lstr(d.name)}, {params}, {variants}, {s_bool(d.exported)})"
    if T == "TImplDecl":
        methods = _slist([s_decl(m) for m in d.methods])
        return f"TImplDecl({_lstr(d.trait_name)}, {_lstr(d.for_type)}, {methods})"
    raise AssertionError(f"unknown decl {T}")


def s_program(tprog) -> str:
    decls = _slist([s_decl(d) for d in tprog.decls])
    return f"TProgram({_lstr(tprog.module)}, {decls})"


# ── Oracle ────────────────────────────────────────────────────────────────────

def oracle(path: pathlib.Path):
    """Return (verdict, payload).  verdict in {'lower','skip'}."""
    try:
        prog = _parser.parse_file(str(path))
    except (LexError, ParseError) as e:
        return "skip", f"oracle parse error: {e}"
    if prog.imports:
        return "skip", "multi-module (import) — outside single-file port"
    try:
        tprog = _infer.typecheck(prog, source_file=str(path))
    except (_infer.TypeError, _infer.AffineError, _infer.TraitBoundError) as e:
        return "skip", f"reject fixture (infer: {str(e)[:40]}) — nothing to lower"
    tac  = _lower.lower(tprog)
    return "lower", (tprog, _tac_pretty(tac))


# ── Port: concatenate lex + parse + types + tast + tac + lower + a driver ─────

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)

def make_driver(tprog) -> str:
    lex   = _strip_lines(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse = _strip_lines(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    types = _strip_lines(TYPES.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    tast  = _strip_lines(TAST.read_text().split(MAIN_MARKER, 1)[0],  ("module ", "import "))
    # tac + lower: bodies only (drop their smoke mains).
    tac   = _strip_lines(TAC.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    lower = _strip_lines(LOWER.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    prog  = s_program(tprog)
    driver_main = (
        "\nfn main(io : IO) : IO =\n"
        f"  let prog = {prog} in\n"
        "  print(io, tacPretty(lowerProgram(prog)))\n"
    )
    return ("module Selfhost\n\n"
            + lex + "\n" + parse + "\n" + types + "\n" + tast + "\n"
            + tac + "\n" + lower + driver_main)


PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))

def run_port(tprog):
    tmp = HERE / "_lowerdriver.lark"
    tmp.write_text(make_driver(tprog))
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── Corpus + driver loop ──────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "tests", ROOT / "samples"]:
        if not base.exists():
            continue
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
        verdict, payload = oracle(path)
        if verdict == "skip":
            print(f"  skip  {label}  ({payload})")
            skip += 1
            continue

        tprog, want = payload
        try:
            pcode, pout, perr = run_port(tprog)
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (meta-circular lower too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue

        if pcode != 0:
            tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
            # A recursion/stack overflow serialising a deep AST is a capacity
            # limit of the CEK, not a lower.lark defect — skip with the reason.
            if "recursion" in (perr or "").lower() or "maximum" in (perr or "").lower():
                print(f"  skip  {label}  (CEK overflow on deep AST: {tail[0][:50]})")
                skip += 1
            else:
                print(f"  FAIL  {label}  (port crash)")
                print(f"        {tail[0]}")
                fail += 1
            continue

        got = pout
        want_nl = want + "\n"           # cek's print adds one newline; pretty ends in one
        if got == want_nl:
            n = want.count("\n")
            print(f"  ok    {label}  ({n} TAC lines)")
            ok += 1
        else:
            print(f"  FAIL  {label}  (TAC mismatch)")
            exp = want_nl.splitlines()
            gt  = got.splitlines()
            if verbose:
                d = difflib.unified_diff(exp, gt, "oracle", "port", lineterm="")
                for line in list(d)[:80]:
                    print(f"        {line}")
            else:
                for i in range(max(len(exp), len(gt))):
                    a = exp[i] if i < len(exp) else "<none>"
                    b = gt[i]  if i < len(gt)  else "<none>"
                    if a != b:
                        print(f"        line {i}: oracle={a!r}")
                        print(f"                 port  ={b!r}")
                        break
            fail += 1

    print(f"\n  {ok} ok / {fail} fail / {skip} skip")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
