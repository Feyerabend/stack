"""
Smoke test for the TAC IR (SELFHOST M7, slice 1 — tac.lark).

tac.lark is pure data (the three-address-code IR) plus a byte-faithful port of
tac.py's `pretty` / `_instr_str` and the Function counter helpers.  It depends
on parse.lark only for `Maybe`/`Just`/`Nothing` (ICall dst, IReturn val), and
the M7 pipeline is assembled by CONCATENATION rather than `import` (see the note
in parse_difftest.py / SELFHOST §7).  So this smoke concatenates

    lex.lark body + parse.lark body + tac.lark (full, incl. its smoke main)

under one module and runs it through the CEK interpreter (07/src/cek.py).

Unlike tastsmoke, tac.lark HAS a Python twin (tac.py), so this is a true
differential: we build the *identical* program in tac.py, take its `pretty()`
as the golden, and demand the CEK-run tac.lark smoke emit exactly those bytes
(plus the trailing newline Python's `print` adds).  A green run proves the IR
ADTs construct/destructure and that the pretty printer is byte-identical to the
oracle it will be diffed against at M7.2.

Usage:
    python3 self/tests/tac_smoke.py            # exits 0 on success
"""

from __future__ import annotations
import sys, subprocess, pathlib

HERE  = pathlib.Path(__file__).resolve().parent          # self/tests
SELF  = HERE.parent                                       # self
ROOT  = SELF.parent                                       # lark
SRC   = ROOT / "07" / "src"
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
TAC   = SELF / "tac.lark"

MAIN_MARKER = "\nfn main(io : IO) : IO ="


def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)


def make_driver() -> str:
    # lex + parse: bodies only (drop module headers, imports, smoke mains).
    # lex is required because parse.lark builds on its Token type + Copy impls;
    # parse is required for Maybe/Just/Nothing used by ICall/IReturn.
    lex_body   = LEX.read_text().split(MAIN_MARKER, 1)[0]
    parse_body = PARSE.read_text().split(MAIN_MARKER, 1)[0]
    lex_body   = _strip_lines(lex_body, ("module ",))
    parse_body = _strip_lines(parse_body, ("module ", "import "))
    # tac: keep its smoke main; drop only the module header.
    tac_full   = _strip_lines(TAC.read_text(), ("module ", "import "))
    return ("module Selfhost\n\n"
            + lex_body + "\n"
            + parse_body + "\n"
            + tac_full + "\n")


def golden() -> str:
    """The oracle: build the SAME program in tac.py and pretty-print it."""
    sys.path.insert(0, str(SRC))
    from tac import (TAC, Function, IBinOp, IReturn, ILabel, IAssign, ICall,
                     IAlloc, IGetTag, IGetField, ICondJump, IAllocClosure,
                     IClosureCall, IUnary, Tmp, Const, pretty)

    add = Function("add", ("a", "b"))
    t0  = add.fresh("t")
    add.emit(IBinOp(t0, "+", Tmp("a"), Tmp("b")))
    add.emit(IReturn(t0))

    g = Function("main", ())
    r = g.fresh("t")
    g.emit(ILabel(".L0"))
    g.emit(IAssign(r, Const(42)))
    g.emit(ICall(None, "print", (Tmp("io"), Const("hi"))))
    g.emit(ICall(r, "add", (Const(1), Const(2))))
    g.emit(IAlloc(Tmp("c"), "Red", ()))
    g.emit(IAlloc(Tmp("p"), "()", (Tmp("a"), Const(True))))
    g.emit(IGetTag(Tmp("tg"), Tmp("c")))
    g.emit(IGetField(Tmp("fld"), Tmp("p"), 1))
    g.emit(ICondJump(Const(False), ".T", ".F"))
    g.emit(IAllocClosure(Tmp("cl0"), "f", ()))
    g.emit(IAllocClosure(Tmp("cl1"), "g", (Tmp("a"),)))
    g.emit(IClosureCall(Tmp("z"), Tmp("cl1"), Const(None)))
    g.emit(IUnary(Tmp("n"), "-", Tmp("x")))
    g.emit(IReturn(None))

    return pretty(TAC([add, g], frozenset()))


def main() -> None:
    want = golden()
    driver = make_driver()
    tmp = HERE / "_tacdriver.lark"
    tmp.write_text(driver)
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=120)
    finally:
        tmp.unlink(missing_ok=True)

    if r.returncode != 0:
        print("  FAIL  tac.lark smoke — CEK crash")
        tail = (r.stderr or r.stdout).strip().splitlines()[-4:] or ["?"]
        for line in tail:
            print(f"        {line}")
        sys.exit(1)

    # Python's `print(arg.s)` in the CEK appends one newline; pretty() already
    # ends with one, so the emitted bytes are `want + "\n"`.
    if r.stdout == want + "\n":
        n = want.count("\n")
        print(f"  ok    tac.lark smoke  ({n} lines, IR builds + pretty == tac.py)")
        sys.exit(0)

    print("  FAIL  tac.lark smoke — output mismatch vs tac.py")
    want_lines = (want + "\n").splitlines()
    got_lines  = r.stdout.splitlines()
    for i in range(max(len(want_lines), len(got_lines))):
        a = want_lines[i] if i < len(want_lines) else "<none>"
        b = got_lines[i]  if i < len(got_lines)  else "<none>"
        if a != b:
            print(f"        line {i}: want={a!r}")
            print(f"                 got ={b!r}")
    sys.exit(1)


if __name__ == "__main__":
    main()
