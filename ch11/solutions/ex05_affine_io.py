"""
Chapter 11, Exercise 5 — solution code.

Affine typing enforces resource correctness statically. (a) write a Lark program
that misuses the IO token and identify the exact rule that rejects it.
(b) describe a property stronger than "used at most once" (e.g. "used exactly
once") and what would change to enforce it. (c) why is "used exactly once"
(linear) a heavier burden than "at most once" (affine), and why did Lark choose
the lighter one?

How to run:   python3 ex05_affine_io.py
Expected:     "misuse -> AffineError('io'); correct threading -> OK"

(a) The misuse uses the IO token twice; the rejecting rule is the affine-variable
    check in infer's Var case: a locally-bound non-Copy variable's use count is
    incremented on each read, and reaching 2 raises AffineError. `IO` has no
    `impl Copy`, so it is tracked; the second read of `io` trips the rule.

(b) "USED EXACTLY ONCE" (linear). On top of the at-most-once check (reject a
    second use), the type system would also have to reject ZERO uses: at every
    binding's end of scope it must verify the count is exactly 1, not ≤ 1. So the
    change is to add a "must be consumed" obligation — a check at scope exit (and
    at function return for parameters) that every linear binding was used, not
    just that it was not over-used.

(c) Linear is HEAVIER because the programmer must thread and consume *every*
    resource on *every* path — no dropping a value, no early return that leaves a
    token unused; you must explicitly discard what you do not need. Affine
    ("at most once") lets values be silently dropped, which matches how people
    actually write code (you often stop using something). Lark chose affine
    because it buys the property that matters for its back end — a resource is
    never used twice, so no aliasing and no runtime ownership checks
    (Chapter 9) — without forcing the programmer to account for every unused
    value, which is the ergonomic cost linear types impose.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "06", "src"))

import lexer    # noqa: E402
import parser   # noqa: E402
import infer    # noqa: E402

MISUSE = """module M
fn two_prints(io : IO) : IO =
    let a = print(io, "hello") in
    print(io, "world")
"""

CORRECT = """module M
fn two_prints(io : IO) : IO =
    let io = print(io, "hello") in
    let io = print(io, "world") in
    io
"""


def typecheck(src):
    return infer.typecheck(parser.Parser(lexer.Lexer(src).tokenize()).parse())


if __name__ == "__main__":
    try:
        typecheck(MISUSE)
        misuse = "no error"
    except infer.AffineError as e:
        misuse = f"AffineError({e!s})"
    assert misuse.startswith("AffineError") and "io" in misuse, misuse

    typecheck(CORRECT)        # raises if not OK

    print(f"misuse -> {misuse}; correct threading -> OK")
