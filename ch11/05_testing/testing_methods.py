"""
Testing a compiler — Chapter 11, §11.5.

Three testing methods, three planted bugs, each bug found by exactly one method
— the point of the section: each catches what the others miss.

  * Differential testing  — run two implementations of the same spec on the same
    inputs and compare. Catches a DIVERGENCE between implementations.
  * Property-based testing — generate inputs and check a stated INVARIANT of one
    implementation. Catches a violated property, with no second implementation.
  * Fuzzing               — feed malformed/random input and check the program
    fails GRACEFULLY rather than crashing. Catches a robustness bug.

The toy artifact is a tiny integer-expression language. It carries three bugs:
  A. eval_fast  computes subtraction wrong  (a divergence from eval_ref)
  B. simplify   rewrites  e * 0  to  e        (a violated meaning-preservation invariant)
  C. parse      raises IndexError on truncated input (a crash, not a clean error)

Run:  python3 testing_methods.py
"""

from __future__ import annotations
from dataclasses import dataclass
import random


# ── A tiny expression language ────────────────────────────────────────────────

@dataclass(frozen=True)
class Num: n: int
@dataclass(frozen=True)
class Bin: op: str; l: object; r: object


def eval_ref(e):                       # the reference: correct
    if isinstance(e, Num): return e.n
    a, b = eval_ref(e.l), eval_ref(e.r)
    return {"+": a + b, "-": a - b, "*": a * b}[e.op]


def eval_fast(e):                      # BUG A: subtraction is backwards
    if isinstance(e, Num): return e.n
    a, b = eval_fast(e.l), eval_fast(e.r)
    return {"+": a + b, "-": b - a, "*": a * b}[e.op]      # b - a, should be a - b


def simplify(e):                       # BUG B: e * 0  ->  e  (should be 0)
    if isinstance(e, Num): return e
    l, r = simplify(e.l), simplify(e.r)
    if e.op == "*" and r == Num(0):
        return l                                            # WRONG: should be Num(0)
    return Bin(e.op, l, r)


def parse(s: str):                     # BUG C: truncated input crashes
    toks = list(s.replace(" ", ""))
    pos = 0
    def atom():
        nonlocal pos
        c = toks[pos]                  # IndexError if input ran out (no bounds check)
        if c == "(":
            pos += 1
            e = expr()
            pos += 1                    # consume ')' — also unchecked
            return e
        n = ""
        while pos < len(toks) and toks[pos].isdigit():
            n += toks[pos]; pos += 1
        return Num(int(n))
    def expr():
        nonlocal pos
        left = atom()
        while pos < len(toks) and toks[pos] in "+-*":
            op = toks[pos]; pos += 1
            left = Bin(op, left, atom())
        return left
    return expr()


# ── Generators ────────────────────────────────────────────────────────────────

def random_expr(depth: int):
    if depth == 0 or random.random() < 0.4:
        return Num(random.randint(0, 9))
    return Bin(random.choice("+-*"), random_expr(depth - 1), random_expr(depth - 1))

def random_string():
    return "".join(random.choice("0123456789+-*() ") for _ in range(random.randint(0, 8)))

def render(e):
    if isinstance(e, Num): return str(e.n)
    return f"({render(e.l)} {e.op} {render(e.r)})"


# ── The three methods ─────────────────────────────────────────────────────────

def differential(trials=2000):
    for _ in range(trials):
        e = random_expr(4)
        if eval_ref(e) != eval_fast(e):
            return f"{render(e)}:  ref={eval_ref(e)}  fast={eval_fast(e)}"
    return None

def property_based(trials=2000):
    for _ in range(trials):
        e = random_expr(4)
        if eval_ref(simplify(e)) != eval_ref(e):    # invariant: simplify preserves meaning
            return f"{render(e)}:  eval={eval_ref(e)}  eval(simplify)={eval_ref(simplify(e))}"
    return None

def fuzzing(trials=4000):
    for _ in range(trials):
        s = random_string()
        try:
            parse(s)
        except (IndexError, ValueError) as ex:          # a CRASH, not a clean parse error
            return f"input {s!r}  crashed with {type(ex).__name__}"
        except Exception:
            pass                                          # a graceful/expected failure: fine
    return None


if __name__ == "__main__":
    random.seed(11)
    print("Three methods, three planted bugs.\n")

    for name, run, bug, missed in [
        ("Differential",   differential,
         "A: eval_fast subtracts backwards",
         "property testing (no invariant catches a 2nd impl) and fuzzing (no crash)"),
        ("Property-based", property_based,
         "B: simplify rewrites e*0 to e",
         "differential testing (would need a correct 'simplify' to compare to) and fuzzing"),
        ("Fuzzing",        fuzzing,
         "C: parse crashes on truncated input",
         "differential and property testing (both feed only well-formed expressions)"),
    ]:
        found = run()
        print(f"{name} testing  ->  bug {bug}")
        print(f"    found: {found}")
        print(f"    the others miss it: {missed}\n")

    print("Each method catches a kind of bug the others structurally cannot.")
