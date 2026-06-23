"""
Meaning preservation — Chapter 8, §8.1.

An optimization is legal if and only if it preserves meaning, and the only way
to trust one is to check. This is the local model of Lark's differential
testing (`lark/06/tests/diff_test.py`): the optimizer proposes a rewrite, an
oracle runs the original and the rewritten program on many inputs and demands
identical results.

Here the "programs" are small arithmetic expressions, the oracle is a brute
differential check over random environments, and there are two candidate
optimizations: one sound (constant folding plus the identities `x+0` and `x*1`)
and one deliberately WRONG (`x - x => x`, which should be `0`). The checker
passes the first and catches the second with a concrete counterexample.

The lesson §8.1 draws: an optimization you cannot check is one you cannot
safely ship.

Run:  python3 equiv_check.py
"""

from __future__ import annotations
import random
from dataclasses import dataclass


# ── A tiny expression language ────────────────────────────────────────────────

@dataclass(frozen=True)
class Num:
    n: int

@dataclass(frozen=True)
class Var:
    name: str

@dataclass(frozen=True)
class Bin:
    op: str            # '+' | '-' | '*'
    l: "Expr"
    r: "Expr"

Expr = object


def ev(e: Expr, env: dict[str, int]) -> int:
    """The meaning of an expression: its value in an environment."""
    if isinstance(e, Num):
        return e.n
    if isinstance(e, Var):
        return env[e.name]
    a, b = ev(e.l, env), ev(e.r, env)
    return {"+": a + b, "-": a - b, "*": a * b}[e.op]


def variables(e: Expr) -> set[str]:
    if isinstance(e, Num):
        return set()
    if isinstance(e, Var):
        return {e.name}
    return variables(e.l) | variables(e.r)


# ── A sound optimization: constant folding + identities ──────────────────────

def fold(e: Expr) -> Expr:
    if isinstance(e, (Num, Var)):
        return e
    l, r = fold(e.l), fold(e.r)
    if isinstance(l, Num) and isinstance(r, Num):       # both constant: fold
        return Num(ev(Bin(e.op, l, r), {}))
    if e.op == "+" and r == Num(0):                     # x + 0  ->  x
        return l
    if e.op == "*" and r == Num(1):                     # x * 1  ->  x
        return l
    if e.op == "*" and (l == Num(0) or r == Num(0)):    # x * 0  ->  0
        return Num(0)
    return Bin(e.op, l, r)


# ── A WRONG optimization: x - x => x  (it should be 0) ───────────────────────

def buggy(e: Expr) -> Expr:
    if isinstance(e, (Num, Var)):
        return e
    l, r = buggy(e.l), buggy(e.r)
    if e.op == "-" and l == r:
        return l                                        # BUG: x - x is 0, not x
    return Bin(e.op, l, r)


# ── The oracle: differential check over random environments ──────────────────

def check(opt, original: Expr, trials: int = 2000):
    """Run original and opt(original) on random inputs; return the first
    environment on which they disagree, or None if all trials agreed."""
    rewritten = opt(original)
    names = sorted(variables(original))
    for _ in range(trials):
        env = {v: random.randint(-100, 100) for v in names}
        if ev(original, env) != ev(rewritten, env):
            return env, ev(original, env), ev(rewritten, env)
    return None


def render(e: Expr) -> str:
    if isinstance(e, Num):
        return str(e.n)
    if isinstance(e, Var):
        return e.name
    return f"({render(e.l)} {e.op} {render(e.r)})"


if __name__ == "__main__":
    #  (x - x) + ((3 + 4) * 1)
    expr = Bin("+",
               Bin("-", Var("x"), Var("x")),
               Bin("*", Bin("+", Num(3), Num(4)), Num(1)))

    print("expression:", render(expr))
    print()

    for name, opt in [("constant folding (sound)", fold),
                      ("x - x => x   (WRONG)",      buggy)]:
        print(f"  {render(expr)}")
        print(f"    --{name}-->")
        print(f"  {render(opt(expr))}")
        result = check(opt, expr)
        if result is None:
            print("    ORACLE: agrees on every input  ->  meaning preserved\n")
        else:
            env, was, now = result
            print(f"    ORACLE: COUNTEREXAMPLE  {env}: "
                  f"original = {was}, optimized = {now}  ->  REJECTED\n")
