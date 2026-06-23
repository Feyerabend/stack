"""
Chapter 6, Exercise 5 — solution code.

I/O is threaded as the affine VIO token. (a) write a function that prints two
lines, threading the token, and show why the checker rejects the version that
reuses the original token for the second print. (b) state two properties the
language would lose if print were a direct effect, each tied to an earlier
guarantee.

How to run:   python3 ex05_io_affine.py
Expected:     "threaded -> OK & prints 2 lines; reused token -> AffineError('io')"

(b) IF print WERE A DIRECT EFFECT (call Python print, return VUnit, no token):
  1. PURITY / referential transparency is lost. With a token, evaluation order of
     effects is forced by data dependencies the type checker tracks; a direct
     effect makes output depend on the interpreter's evaluation order, which the
     pure semantics deliberately does not pin down. This is the property
     Chapter 5's affine discipline buys: each effect is sequenced because each
     token is used exactly once.
  2. The CODE-GENERATION LICENCE of Chapter 9 is lost. Because IO is affine and
     consumed once, the back end may treat the token as a zero-width value and
     emit no runtime ownership/aliasing checks (and reorder pure code freely
     around effects). A direct effect would reintroduce hidden ordering
     constraints the optimiser and code generator could not assume away — the
     soundness the proof of Chapter 11 relies on.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "04", "src"))

import lexer    # noqa: E402
import parser   # noqa: E402
import infer    # noqa: E402
import cek      # noqa: E402

THREADED = """module M
fn two_lines(io : IO) : IO =
  let io = print(io, "first") in
  let io = print(io, "second") in
  io
fn main(io : IO) : IO = two_lines(io)
"""

# reuses the ORIGINAL io for the second print instead of the threaded one
REUSED = """module M
fn two_lines(io : IO) : IO =
  let io2 = print(io, "first") in
  print(io, "second")
fn main(io : IO) : IO = two_lines(io)
"""


def typecheck(src):
    return infer.typecheck(parser.Parser(lexer.Lexer(src).tokenize()).parse())


if __name__ == "__main__":
    # (a) threaded version type-checks and, when run, prints two lines
    typecheck(THREADED)
    prog = parser.Parser(lexer.Lexer(THREADED).tokenize()).parse()
    tprog = infer.typecheck(prog)
    m = cek.Machine()
    env = cek.eval_program(prog, tprog, None, m)
    printed = []
    orig = cek.sys.stdout
    # capture stdout from the builtin print
    import io as _io
    buf = _io.StringIO(); cek.sys.stdout = buf
    try:
        cek.run(cek.apply(env["main"], cek.VIO(), [], m), m)
    finally:
        cek.sys.stdout = orig
    lines = [l for l in buf.getvalue().splitlines() if l]
    assert lines == ["first", "second"], lines

    # reused-token version is rejected by the affine checker
    try:
        typecheck(REUSED)
        reused = "no error"
    except infer.AffineError as e:
        reused = f"AffineError({e!s})"
    assert reused.startswith("AffineError") and "io" in reused, reused

    print(f"threaded -> OK & prints 2 lines; reused token -> {reused}")
