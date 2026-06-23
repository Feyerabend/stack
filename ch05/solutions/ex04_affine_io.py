"""
Chapter 5, Exercise 4 — solution code.

A function double-consumes an affine IO token; the checker raises AffineError on
the final bare `io`. (a) trace the Tracked counts; (b) rewrite it correctly;
(c) explain why shadowing a non-Copy binding is not a second use.

How to run:   python3 ex04_affine_io.py
Expected:     "buggy -> AffineError('io'); fixed -> OK"

This drives the REAL Lark checker (lark/07/src/infer.py). The chapter's example
writes `let _ = print(io, "world") in`; Lark's `let` binds a NAME (not `_`), so
the runnable version names that result `r`. The affine behaviour is identical.

(a) TRACKED COUNTS for the buggy version
      fn two_prints(io : IO) : IO =
          let io = print(io, "hello") in   # rebinds io; new io -> count 0
          let r  = print(io, "world") in   # uses io once -> count 1
          io                               # uses io again -> count 2 -> ERROR
    After line 2: tracked = {io: 0} (the *new* io; the old one was consumed when
    it was read inside print(io,"hello") and then replaced).
    After line 3's `print(io, "world")`: tracked = {io: 1, r: 0}.
    At the final bare `io`: the read does tracked["io"] += 1 -> 2, and since
    2 > 1 the checker raises AffineError('io').

(b) FIX: thread io, never reusing a consumed token — shadow it each step.
      fn two_prints(io : IO) : IO =
          let io = print(io, "hello") in
          let io = print(io, "world") in
          io

(c) WHY SHADOWING IS NOT A SECOND USE. A `let io = ...` does not READ the old io
    a second time; the old io is read once (inside the right-hand side) and then
    the name is REBOUND. In infer.py's LetExpr case, the rebinding runs
    `tracked.pop(n, None)` — discarding the old binding's counter entirely — and
    then, because IO is non-Copy, installs a fresh `tracked[io] = 0` for the new
    value. So each shadow starts a brand-new affine life at count 0; the only
    way to hit count 2 is to read the *same* binding twice, as the bug does.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "07", "src"))

from lexer import Lexer       # noqa: E402
from parser import Parser     # noqa: E402
import infer as I             # noqa: E402

BUGGY = """module M
fn two_prints(io : IO) : IO =
    let io = print(io, "hello") in
    let r  = print(io, "world") in
    io
"""

FIXED = """module M
fn two_prints(io : IO) : IO =
    let io = print(io, "hello") in
    let io = print(io, "world") in
    io
"""


def typecheck(src):
    return I.typecheck(Parser(Lexer(src).tokenize()).parse())


if __name__ == "__main__":
    # buggy: the final bare `io` is io's second use -> AffineError
    try:
        typecheck(BUGGY)
        bug = "no error"
    except I.AffineError as e:
        bug = f"AffineError({e!s})"
    assert bug.startswith("AffineError") and "io" in bug, bug

    # fixed: shadowing rebinds io each step; every binding is used once
    typecheck(FIXED)          # raises if not OK

    print(f"buggy -> {bug}; fixed -> OK")
