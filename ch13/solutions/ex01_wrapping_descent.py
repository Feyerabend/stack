"""
Chapter 13, Exercise 1(b) — solution code.

Prove that `n - 1` is not a well-founded descent on wrapping i32 integers,
by exhibiting the infinite descending chain.

How to run:   python3 ex01_wrapping_descent.py
Expected:     the wrap INT_MIN - 1 = INT_MAX shown; the "descending" step
              relation shown to contain a cycle (hence an infinite chain);
              and a concrete countdown, f(n) = f(n - 2) from an odd start,
              shown never to reach its base case.

A relation is well-founded exactly when it admits no infinite descending
chain. The claimed descent is the step  n  >  n - 1  (wrapping). But on a
wrapping i32 the step relation is a single cycle through all 2^32 values:
follow it long enough and you return to where you started, so the chain

    0 > -1 > -2 > ... > INT_MIN > INT_MAX > ... > 1 > 0 > -1 > ...

descends forever. No measure into the naturals can strictly decrease along
a cycle, so no totality checker can certify this step — which is why the
checker's diagnostic says "recurse on data, not on integers": structural
descent into constructors has no wrap, so it is well-founded by
construction.

The cycle also breaks real programs, not just the metatheory. Stepping by
2 preserves parity, and the modulus 2^32 is even, so from an odd start
`f(n) = if n == 0 then 0 else f(n - 2)` visits odd values only and never
meets its base case: a genuinely non-terminating countdown.
"""

INT_MIN = -2**31
INT_MAX = 2**31 - 1
MOD = 2**32


def wrap(n: int) -> int:
    """Two's-complement wrapping to i32 (the Phase 8 Int)."""
    return (n + 2**31) % MOD - 2**31


def main() -> None:
    # The wrap itself: "below INT_MIN lies INT_MAX."
    assert wrap(INT_MIN - 1) == INT_MAX
    print(f"INT_MIN - 1 wraps to {wrap(INT_MIN - 1)}  (= INT_MAX)")

    # The step relation n -> n - 1 has a cycle: starting anywhere, after
    # exactly 2^32 steps you are back where you started. We do not take
    # 2^32 steps; the cycle follows from wrap() being a bijection with
    # wrap(n) - 1 = wrap(n - 1). Demonstrate the crossing point:
    chain = [3, 2, 1, 0, -1]
    print("descending chain:", " > ".join(map(str, chain)), "> ...")
    print(f"... > {INT_MIN} > {wrap(INT_MIN - 1)} > ... and the chain has"
          f" re-entered positive territory: it never ends.")

    # The concrete divergent program: parity is invariant under n - 2,
    # and 2^32 is even, so an odd n never reaches 0.
    n, steps = 5, 0
    seen_parity = n % 2
    while steps < 10_000_000:
        if n == 0:
            raise AssertionError("reached the base case?!")
        n = wrap(n - 2)
        steps += 1
        assert n % 2 == seen_parity  # parity never changes
    print(f"f(n) = f(n - 2) from n = 5: {steps:,} steps taken, parity "
          f"still {'odd' if seen_parity else 'even'}, base case n == 0 "
          f"unreachable (parity argument) — a non-terminating countdown.")
    print("OK: wrapping integer descent is not well-founded.")


if __name__ == "__main__":
    main()
