"""
Chapter 13, Exercise 2(b) — solution code (a model of the phenomenon).

The planted division bug survived uniform generation. This script shows
*why* with a small probabilistic model, and how edge-biasing repairs it.

How to run:   python3 ex02_edge_bias.py
Expected:     under uniform divisor values the planted bug (x/0 = -2
              instead of -1) needs on the order of thousands of programs
              to be seen even in a friendly model; with the divisor drawn
              from {0, 1, -1} half the time it is caught within a handful.

The model is deliberately generous to uniform generation: each "program"
contains one division whose divisor is a random i32 drawn from a modest
range, and the bug is *observed* whenever the divisor is exactly 0 (the
real generator must also route the wrong value into printed output, which
only lowers the odds further). Even so, the corner is a corner: the
probability of hitting divisor == 0 uniformly in [-2^15, 2^15] is about
1/65_000, so the expected number of programs to detection is about
65_000 — and section 13.3's real run of 300 uniformly generated programs
was never going to see it. Biasing the divisor to {0, 1, -1} half the
time lifts the hit probability to about 1/6 per program, so detection is
expected within about six programs; the chapter's shrunk counterexample,
show((0 / 0)), then falls out in about a second.

The moral is the boxed principle, not the arithmetic: nothing but the
planted bug reveals which of "nothing is wrong" and "I am not looking"
the fuzzer's silence means.
"""

import random

TRIALS = 200          # repeated experiments, for a stable average
RANGE = 2**15         # divisor magnitude in the uniform model


def programs_until_caught(rng: random.Random, biased: bool) -> int:
    """How many generated 'programs' until one exercises divisor == 0."""
    n = 0
    while True:
        n += 1
        if biased and rng.random() < 0.5:
            divisor = rng.choice([0, 1, -1])
        else:
            divisor = rng.randint(-RANGE, RANGE)
        if divisor == 0:          # the planted x/0 = -2 fires and diverges
            return n
        if n > 5_000_000:         # safety net; never reached in practice
            return n


def main() -> None:
    rng = random.Random(13)
    uniform = sum(programs_until_caught(rng, False) for _ in range(TRIALS)) / TRIALS
    biased = sum(programs_until_caught(rng, True) for _ in range(TRIALS)) / TRIALS
    print(f"programs until the planted x/0 bug is caught (mean of {TRIALS} runs):")
    print(f"  uniform divisors in [-{RANGE}, {RANGE}]: {uniform:10.1f}")
    print(f"  divisor from {{0, 1, -1}} half the time:  {biased:10.1f}")
    print("A 300-program uniform run was silence, not safety; the edge bias")
    print("turns the corner case into an expected-within-ten event.")


if __name__ == "__main__":
    main()
