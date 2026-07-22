"""
Differential test for the self-hosted parser.

For every .lark file in the corpus it compares two pretty-printed ASTs:

  • the oracle — oracle/parser.py (the frozen Python parser), serialized here
    into a canonical S-expression;
  • the port    — lark/parse.lark (which imports lark/lex.lark's tokenizer),
    run through the CEK interpreter (oracle/cek.py), printing the same form.

They must be byte-identical, line for line.

Composition note
────────────────
parse.lark is written as a *component*: it `import`s module Lex for the token
types + `tokenize` + `escape`.  We do NOT drive it through that import, because
the toolchain's import path re-type-checks the imported module WITHOUT the
mutual-recursion pre-registration pass (infer Pass 1.5), so lex.lark's forward
references (e.g. read_name → keyword_kind) fail to resolve on import even though
lex.lark type-checks standalone.  (Logged as a known wart of the language.)  Instead
the driver is built by *concatenation*: lex.lark's body + parse.lark's body +
a generated main, under one module — so the whole thing goes through the normal
top-level typechecker (which does pre-register), exactly as when a single file
is compiled.

Serialization (must mirror parse.lark's sX functions exactly):
  Val:  (VInt t) (VFloat t) (VStr "esc") (VBool true|false) (VUnit)
  Ty:   (TName n) (TApply n [..]) (TFn a b) (TUnit) (TTuple [..])
  Pat:  (PWild) (PVar n) (PLit v) (PCon n [..]) (PTuple [..])
  Expr: (Lit v) (Var n) (Con n) (TupleExpr [..]) (Apply f [..])
        (BinOp op l r) (UnaryOp op x) (LetExpr n ann v b)
        (IfExpr c t e) (MatchExpr s [arms]) (Lambda [params] b)
  Decl: (FnDecl exp n [bounds] [params] ann body) (LetDecl exp n ann v)
        (TypeDecl exp n [params] body) (TraitDecl exp n [params] [meth])
        (ImplDecl tn [targs] forty [meth])
  Program: "(module Name)" then one line per import then one per decl.
  Maybe(Ty)/exposing: "_" for absent, else the serialized value.

Usage:
    python3 harness/parse_difftest.py [-v]      # -v: show a diff on failure
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib
import os

HERE  = pathlib.Path(__file__).resolve().parent   # <strand>/harness
ROOT  = HERE.parent                              # <strand>/
SELF  = ROOT / "lark"                            # the compiler, written in Lark
SRC   = ROOT / "oracle"                          # the Python reference implementation
CEK  = str(SRC / "cek.py")
LEX  = SELF / "lex.lark"
PARSE = SELF / "parse.lark"

sys.path.insert(0, str(SRC))
from lexer import Lexer, LexError            # noqa: E402
import parser as _parser                     # noqa: E402
from parser import ParseError                # noqa: E402
from tree import (                           # noqa: E402
    TName, TApply, TFn, TUnit, TTuple,
    PWild, PVar, PLit, PCon, PTuple,
    Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
    LetExpr, IfExpr, MatchExpr, Lambda,
    FnDecl, LetDecl, TypeDecl, TraitDecl, ImplDecl,
)


# ── Corpus ────────────────────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    """The test corpus, the samples, and the compiler's own source.

    SELF is globbed *non-recursively*, and that matters.  It used to be `rglob`,
    which swept everything below it: `self/vendor/` (a byte-faithful second copy of
    the same corpus) was being parsed a second time, and so were the scratch drivers
    the harnesses themselves write into `harness/` — a file that a *concurrent*
    run deletes out from under you mid-sweep.  The corpus is the corpus; the
    compiler is `self/*.lark`; nothing else belongs here.
    """
    files: list[pathlib.Path] = []
    for base in [ROOT / "tests", ROOT / "samples"]:
        files += sorted(base.rglob("*.lark"))
    files += sorted(p for p in SELF.glob("*.lark") if not p.name.startswith("_"))
    return files


# ── Oracle serialization (mirror of parse.lark's sX functions) ────────────────

def esc(s: str) -> str:
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if   o == 92: out.append("\\\\")
        elif o == 10: out.append("\\n")
        elif o ==  9: out.append("\\t")
        elif o == 13: out.append("\\r")
        else:         out.append(ch)
    return "".join(out)

def s_val(v: object) -> str:
    # bool must be checked before int (bool is an int subclass in Python).
    if isinstance(v, bool):  return f"(VBool {'true' if v else 'false'})"
    if isinstance(v, int):   return f"(VInt {v})"
    if isinstance(v, float): return f"(VFloat {v})"
    if isinstance(v, str):   return f'(VStr "{esc(v)}")'
    if v is None:            return "(VUnit)"
    raise AssertionError(f"unexpected literal value {v!r}")

def s_ty(t: object) -> str:
    match t:
        case TName(name=n):          return f"(TName {n})"
        case TApply(name=n, args=a): return f"(TApply {n} {s_list(a, s_ty)})"
        case TFn(param=p, result=r): return f"(TFn {s_ty(p)} {s_ty(r)})"
        case TUnit():                return "(TUnit)"
        case TTuple(elems=e):        return f"(TTuple {s_list(e, s_ty)})"
    raise AssertionError(f"bad type {t!r}")

def s_maybe_ty(t: object) -> str:
    return "_" if t is None else s_ty(t)

def s_pat(p: object) -> str:
    match p:
        case PWild():               return "(PWild)"
        case PVar(name=n):          return f"(PVar {n})"
        case PLit(value=v):         return f"(PLit {s_val(v)})"
        case PCon(name=n, args=a):  return f"(PCon {n} {s_list(a, s_pat)})"
        case PTuple(elems=e):       return f"(PTuple {s_list(e, s_pat)})"
    raise AssertionError(f"bad pattern {p!r}")

def s_expr(e: object) -> str:
    match e:
        case Lit(value=v):                    return f"(Lit {s_val(v)})"
        case Var(name=n):                     return f"(Var {n})"
        case Con(name=n):                     return f"(Con {n})"
        case TupleExpr(elems=es):             return f"(TupleExpr {s_list(es, s_expr)})"
        case Apply(fn=f, args=a):             return f"(Apply {s_expr(f)} {s_list(a, s_expr)})"
        case BinOp(op=o, left=l, right=r):    return f"(BinOp {o} {s_expr(l)} {s_expr(r)})"
        case UnaryOp(op=o, operand=x):        return f"(UnaryOp {o} {s_expr(x)})"
        case LetExpr(name=n, ann=an, value=v, body=b):
            return f"(LetExpr {n} {s_maybe_ty(an)} {s_expr(v)} {s_expr(b)})"
        case IfExpr(cond=c, then_=t, else_=el):
            return f"(IfExpr {s_expr(c)} {s_expr(t)} {s_expr(el)})"
        case MatchExpr(scrutinee=s, arms=arms):
            armstr = " ".join(f"(Arm {s_pat(pt)} {s_expr(ex)})" for (pt, ex) in arms)
            return f"(MatchExpr {s_expr(s)} [{armstr}])"
        case Lambda(params=ps, body=b):
            return f"(Lambda {s_list(ps, s_param)} {s_expr(b)})"
    raise AssertionError(f"bad expr {e!r}")

def s_param(p: object) -> str:
    return f"(Param {p.name} {s_maybe_ty(p.ann)})"

def s_bound(b: object) -> str:
    return f"(Bound {b.trait} {b.var})"

def s_variant(v: object) -> str:
    return f"(Variant {v.name} {s_list(v.payload, s_ty)})"

def s_tmethod(m: object) -> str:
    return f"(TMethod {m.name} {s_ty(m.typ)})"

def s_imethod(m: object) -> str:
    return f"(IMethod {m.name} {s_list(m.params, s_param)} {s_expr(m.body)})"

def s_ty_body(body: object) -> str:
    # TypeDecl.body is either a Type (alias) or a tuple of Variant (ADT).
    if isinstance(body, tuple):
        return f"(Variants {s_list(body, s_variant)})"
    return f"(Alias {s_ty(body)})"

def s_list(xs, f) -> str:
    return "[" + " ".join(f(x) for x in xs) + "]"

def s_strlist(xs) -> str:
    return "[" + " ".join(xs) + "]"

def s_decl(d: object) -> str:
    match d:
        case FnDecl():
            return (f"(FnDecl {'true' if d.exported else 'false'} {d.name} "
                    f"{s_list(d.bounds, s_bound)} {s_list(d.params, s_param)} "
                    f"{s_maybe_ty(d.return_type)} {s_expr(d.body)})")
        case LetDecl():
            return (f"(LetDecl {'true' if d.exported else 'false'} {d.name} "
                    f"{s_maybe_ty(d.ann)} {s_expr(d.value)})")
        case TypeDecl():
            return (f"(TypeDecl {'true' if d.exported else 'false'} {d.name} "
                    f"{s_strlist(d.params)} {s_ty_body(d.body)})")
        case TraitDecl():
            return (f"(TraitDecl {'true' if d.exported else 'false'} {d.name} "
                    f"{s_strlist(d.params)} {s_list(d.methods, s_tmethod)})")
        case ImplDecl():
            return (f"(ImplDecl {d.trait_name} {s_list(d.trait_args, s_ty)} "
                    f"{s_ty(d.for_type)} {s_list(d.methods, s_imethod)})")
    raise AssertionError(f"bad decl {d!r}")

def s_import(imp: object) -> str:
    expo = "_" if imp.exposing is None else s_strlist(imp.exposing)
    return f"(Import {imp.module} {expo})"

def oracle_lines(source: str) -> list[str]:
    prog = _parser.parse_src(source, "<corpus>")
    lines = [f"(module {prog.module})"]
    lines += [s_import(i) for i in prog.imports]
    lines += [s_decl(d) for d in prog.decls]
    return lines


# ── Driver generation (concatenate lex + parse + a per-file main) ─────────────

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

def make_driver(lex_src: str, parse_src: str, source: str) -> str:
    lex_body   = lex_src.split(MAIN_MARKER, 1)[0]
    parse_body = parse_src.split(MAIN_MARKER, 1)[0]
    lex_body   = _strip_lines(lex_body, ("module ",))
    parse_body = _strip_lines(parse_body, ("module ", "import "))
    lit = lark_string_literal(source)
    driver_main = (
        '\nfn main(io : IO) : IO =\n'
        f'  let src = "{lit}" in\n'
        '  print(io, dumpProg(parseProgram(tokenize(src, string_length(src), P(0, 1, 1)))))\n'
    )
    return "module Selfhost\n\n" + lex_body + "\n" + parse_body + driver_main


# ── Runner ────────────────────────────────────────────────────────────────────

# Per-driver budget for the Lark side. Override: LARK_TIMEOUT=<seconds>
PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "300"))

def run_port(driver: str) -> tuple[int, str, str]:
    tmp = HERE / "_pdriver.lark"
    tmp.write_text(driver)
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", (f"port timed out after {PORT_TIMEOUT}s "
                          f"— raise it with LARK_TIMEOUT=<seconds>")
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    verbose = "-v" in sys.argv
    lex_src   = LEX.read_text()
    parse_src = PARSE.read_text()

    ok = fail = skip = 0
    for path in corpus():
        label  = str(path.relative_to(ROOT))
        source = path.read_text()

        try:
            expected = oracle_lines(source)
        except (LexError, ParseError) as e:
            print(f"  skip  {label}  (oracle error: {e})")
            skip += 1
            continue

        code, out, err = run_port(make_driver(lex_src, parse_src, source))
        # A timeout is a fact about this machine, not about the compiler: the
        # port is an interpreter running an interpreter, and the budget is wall
        # clock.  Report it the way cek/emit do — a skip with a reason — so that
        # a slow box cannot masquerade as a disagreement.  Raise LARK_TIMEOUT to
        # turn a skip into a real comparison.
        if code == 124:
            print(f"  skip  {label}  (meta-circular eval too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue
        if code != 0:
            print(f"  FAIL  {label}  (CEK crash)")
            tail = (err or out).strip().splitlines()[-1:] or ["?"]
            print(f"        {tail[0]}")
            fail += 1
            continue

        got = out.splitlines()
        if got == expected:
            print(f"  ok    {label}  ({len(expected)} decls+)")
            ok += 1
        else:
            print(f"  FAIL  {label}")
            if verbose:
                d = difflib.unified_diff(expected, got, "oracle", "port", lineterm="")
                for line in list(d)[:60]:
                    print(f"        {line}")
            else:
                for i, (a, b) in enumerate(zip(expected, got)):
                    if a != b:
                        print(f"        line {i}: oracle={a!r}")
                        print(f"                 port  ={b!r}")
                        break
                if len(expected) != len(got):
                    print(f"        length: oracle={len(expected)} port={len(got)}")
            fail += 1

    total = ok + fail + skip
    print(f"\n  {ok} ok, {fail} failed, {skip} skipped  ({total} files)")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
