"""
Chapter 5, Exercise 5 — solution code.

Lark's Copy trait carries no methods (impl Copy for T = {} is always empty).
(a) what does the checker do on this declaration (is_copy / copy_types)?
(b) a Point with Copy can be used twice without AffineError;
(c) a Handle without Copy cannot — at which step does the error fire?
(d) state the precise rule for what makes a binding enter Tracked.

How to run:   python3 ex05_copy_trait.py
Expected:     "Point(Copy) used twice -> OK; Handle(no Copy) used twice -> AffineError('h')"

This drives the REAL Lark checker (lark/07/src/infer.py).

(a) WHAT THE CHECKER DOES. The body is empty, so there are no methods to
    register. The declaration's only effect is on the set `copy_types`: in
    typecheck's pass 1, `isinstance(decl, ImplDecl) and decl.trait_name=="Copy"`
    adds the implementing type's name to `copy_types`. Thereafter `is_copy(t,
    copy_types)` returns True for that type (a TCon whose head name is in the
    set). Copy is a pure MARKER trait — it changes a set membership, nothing else.

(b)/(c) USING A VALUE TWICE. `fn dup(x) = (x, x)` reads x twice. Whether that is
    allowed is decided when x is BOUND (the parameter): in infer's parameter
    handling a binding enters `tracked` (with count 0) only if its type is NOT
    Copy. So:
      - Point is in copy_types  -> is_copy(Point) is True -> p never enters
        tracked -> the two reads are unconstrained -> OK.
      - Handle is not in copy_types -> is_copy(Handle) is False -> h enters
        tracked at 0 -> first read makes it 1, second read makes it 2 -> at the
        second read `tracked[h] > 1` fires AffineError('h').

(d) THE PRECISE RULE. A binding enters Tracked iff its (concrete) type is NOT
    Copy — i.e. iff there is no `impl Copy for T` for that type. The presence of
    the Copy impl is what keeps a binding OUT of Tracked; its absence is what
    puts it in. No other trait affects this.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "07", "src"))

from lexer import Lexer       # noqa: E402
from parser import Parser     # noqa: E402
import infer as I             # noqa: E402

POINT_COPY = """module M
type Point = | Point of Int, Int
impl Copy for Point = {}
fn dup(p : Point) : (Point, Point) = (p, p)
"""

HANDLE_NOCOPY = """module M
type Handle = | Handle of Int
fn dup(h : Handle) : (Handle, Handle) = (h, h)
"""


def typecheck(src):
    return I.typecheck(Parser(Lexer(src).tokenize()).parse())


if __name__ == "__main__":
    # (b) Point is Copy -> using it twice is fine.
    typecheck(POINT_COPY)     # raises if not OK

    # (c) Handle is not Copy -> using it twice raises on the second read.
    try:
        typecheck(HANDLE_NOCOPY)
        handle = "no error"
    except I.AffineError as e:
        handle = f"AffineError({e!s})"
    assert handle.startswith("AffineError") and "h" in handle, handle

    # (a)/(d) confirm the mechanism directly: is_copy keys off copy_types.
    # Nullary user types are TCon(name) (applied type constructors would be TApp).
    from ty import TCon
    assert I.is_copy(TCon("Point"), frozenset({"Point"})) is True
    assert I.is_copy(TCon("Handle"), frozenset({"Point"})) is False

    print(f"Point(Copy) used twice -> OK; "
          f"Handle(no Copy) used twice -> {handle}")
