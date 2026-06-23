"""
Chapter 8, Exercise 4 — solution code.

x + 0.0 = x is unsound for floating point. (a) identify the value of x for which
it fails and state both results. (b) explain how the differential oracle would
catch a compiler that applied it. (c) x + 0 = x IS sound for Int — what is the
difference?

How to run:   python3 ex04_float_zero.py
Expected:     "x = -0.0: x + 0.0 = 0.0 but x = -0.0 (1/result: inf vs -inf); Int is exact"

(a) THE FAILING VALUE: x = -0.0 (negative zero). Under IEEE-754,
        (-0.0) + 0.0  ==  +0.0          (addition normalises the sign of zero)
    so the original expression yields +0.0, while the rewritten `x` yields -0.0.
    The two zeros compare == numerically but are observably different: their sign
    bit differs, and dividing exposes it — 1.0 / (+0.0) = +inf but
    1.0 / (-0.0) = -inf.

(b) THE DIFFERENTIAL ORACLE catches it by running the program before and after
    the rewrite on the same input and comparing OUTPUT. A program that prints
    1.0 / (x + 0.0) outputs `inf`; after the (unsound) rewrite to 1.0 / x it
    outputs `-inf`. The outputs differ, so the oracle rejects the rewrite with a
    concrete counterexample (x = -0.0) — exactly how a sound rewrite is told from
    a wrong one, with no appeal to aesthetics.

(c) THE DIFFERENCE: Int arithmetic has no negative zero, no NaN, and no rounding
    — every value has one representation and + is exact two's-complement. So
    x + 0 == x bit-for-bit for every Int x. Float's signed zero (and NaN, and
    rounding for non-zero addends) is what makes the "same" identity unsound:
    the equivalence that holds in the mathematical reals does not hold in IEEE-754.
"""

import math


def fails_for_float():
    x = -0.0
    original = x + 0.0      # what the program computes
    rewritten = x          # what `x + 0.0 => x` would substitute
    # numerically equal...
    assert original == rewritten            # 0.0 == -0.0 is True
    # ...but observably different via the sign of zero:
    assert math.copysign(1.0, original) == 1.0     # +0.0
    assert math.copysign(1.0, rewritten) == -1.0   # -0.0
    return original, rewritten


def sound_for_int():
    # No -0, NaN, or rounding: x + 0 == x for every Int.
    return all((x + 0) == x for x in range(-1000, 1001))


if __name__ == "__main__":
    original, rewritten = fails_for_float()
    inv_orig = math.inf if original == 0.0 else 1.0 / original
    inv_rew = 1.0 / rewritten if rewritten != 0.0 else math.copysign(math.inf, rewritten)
    # the observable divergence the oracle would see:
    obs_orig = 1.0 / (original)   if original  != 0.0 else math.copysign(math.inf, original)
    obs_rew  = 1.0 / (rewritten)  if rewritten != 0.0 else math.copysign(math.inf, rewritten)
    assert obs_orig == math.inf and obs_rew == -math.inf

    assert sound_for_int()

    print(f"x = -0.0: x + 0.0 = {original} but x = {rewritten} "
          f"(1/result: {obs_orig} vs {obs_rew}); Int is exact")
