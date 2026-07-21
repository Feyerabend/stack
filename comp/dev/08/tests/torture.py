"""Torture: hostile-but-legal programs, each on a wall clock.

The other harnesses ask whether the checker is RIGHT.  This one asks whether it
ANSWERS — because the two failures a verifier may not have are a wrong answer and
no answer, and only the first has a test suite pointing at it.

Every program below is legal Lark, and every one of them is unreasonable: three
thousand terms in one expression, a predicate that is a conjunction of three
hundred comparisons, a thousand nested lets, a constructor term four hundred deep.
Nobody writes these.  The point is that the checker's failure mode on them must
still be a VERDICT — `ok`, `unproved`, a type error, a refinement error, or an
honest "I gave up on a budget".  A traceback is not a verdict, and neither is a
prompt that never comes back.

What it caught, the day it was written (all five now fixed):

  * four RecursionErrors, raw, straight out of parser/infer/refine — the checker
    walks a program with the C stack, and Python's default limit is 1000, so a
    program deeper than that CRASHED where it should have said something.  Fixed
    by walking on a thread with a real stack and classifying what is left as
    TooDeep — a stated limit, not a stack trace.

  * a HANG on `wide_conj`.  Every fence in solver.py was LOCAL (a split budget
    re-armed per call) while every caller LOOPED, so the total work in one query
    had no bound at all.  Fixed by a global purse, and by bounding the SIZE of a
    linear system rather than the number of them: Fourier–Motzkin is quadratic per
    elimination, so counting calls bounds nothing.

  * and, once the stack was raised, a hang that the crash had been HIDING:
    translating `1 + 1 + … + 1` re-derived the linearity of the whole subtree at
    every level of a walk that already visits every node.  173 million calls on an
    800-term sum.  The overflow had been mercy-killing a cubic algorithm.

That last one is the lesson worth keeping: a crash can be a symptom of a cost, and
fixing the crash without measuring the cost just moves the failure somewhere the
tests cannot see it.

Run: make torture   (or: python3 tests/torture.py [limit-seconds])
"""
import os
import subprocess
import sys
import tempfile
import textwrap
import time

HERE  = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "..", "src", "refine.py")
LIMIT = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0


# -- The programs ---------------------------------------------------------------
#
# Each is a (name, source) pair.  Nothing here is expected to PROVE anything; the
# expectation is only that the checker comes back and says which of the things it
# is allowed to say.

def _cases() -> dict[str, str]:
    cs: dict[str, str] = {}

    # Depth, in an expression.  The parser, the type-checker and the refinement
    # walk all recurse through this, and each of them used to overflow.
    cs["deep_expr"] = ("module M\nfn main(io : IO) : IO = print(io, show("
                       + "1 + " * 3000 + "1))\n")

    # Depth, inside a PREDICATE — the term the solver is handed, not just the
    # program it is about.
    deep_p = " + ".join(["x"] * 800)
    cs["deep_pred"] = f"""\
module M
fn f(x : Int, y : {{v : Int | v == {deep_p}}}) : Int = y
fn main(io : IO) : IO = print(io, show(f(1, 2)))
"""

    # Disequalities: `v /= k` splits into `v < k` or `v > k`, so k of them is 2^k
    # cases.  The solver must give up rather than enumerate them.
    diseqs = " and ".join(f"v != {i}" for i in range(40))
    cs["many_diseq"] = f"""\
module M
fn f(x : {{v : Int | {diseqs}}}) : Int = x
fn main(io : IO) : IO = print(io, show(f(100)))
"""

    # Boolean structure: DPLL's search is exponential in the atoms.  Thirty binary
    # choices is a billion assignments if anything ever enumerates them.
    disj = " and ".join(f"(v + {i} == {i} or v + {i} == {i + 1})" for i in range(30))
    cs["dpll_blowup"] = f"""\
module M
fn f(x : {{v : Int | {disj}}}) : Int = x
fn main(io : IO) : IO = print(io, show(f(0)))
"""

    # Coefficients big enough that the Omega test's exact rational arithmetic has
    # to actually be exact.  Python's ints are unbounded; this is here so that a
    # day when they are not, the harness notices.
    cs["huge_lits"] = """\
module M
fn f(x : {v : Int | v * 1000000000000000000000 >= 1000000000000000000000}) : Int = x
fn main(io : IO) : IO = print(io, show(f(2)))
"""

    # A long chain of lets: deep expression AND deep environment, and the
    # environment is copied at every binder.
    lets = "".join(f"  let x{i} = x{i-1} + 1 in\n" for i in range(1, 1200))
    cs["deep_lets"] = f"""\
module M
fn f(x0 : Int) : Int =
{lets}  x1199
fn main(io : IO) : IO = print(io, show(f(0)))
"""

    # A deep constructor TERM.  Since V2.2 a constructor is a term in the logic and
    # measure equations are instantiated at the constructor terms the program
    # mentions, so this one is aimed squarely at the axiom machinery.
    cons = "Cons(1, " * 400 + "Nil" + ")" * 400
    cs["deep_con"] = f"""\
module M
type List a = | Nil | Cons of a, List(a)
measure len(xs : List(Int)) : {{v : Int | v >= 0}} =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + len(rest)
  end
fn f(xs : List(Int)) : {{v : Int | v >= 0}} = len_of(xs)
fn len_of(xs : List(Int)) : {{v : Int | v == len(xs)}} =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => let n = len_of(rest) in 1 + n
  end
fn main(io : IO) : IO = print(io, show(f({cons})))
"""

    # A measure applied at the wrong arity, inside a predicate.  The checker must
    # decline to know what `len(xs, xs)` is — and must not decide it is `true`.
    cs["measure_arity"] = """\
module M
type List a = | Nil | Cons of a, List(a)
measure len(xs : List(Int)) : Int =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + len(rest)
  end
fn f(xs : List(Int), n : {v : Int | v == len(xs, xs)}) : Int = n
fn main(io : IO) : IO = print(io, show(f(Nil, 0)))
"""

    # A refinement on a FLOAT.  `v == v` is valid in the logic and false at run
    # time for NaN: this must be an error, and never a fact (V2.2', finding 1).
    cs["float_pred"] = """\
module M
fn f(x : {v : Float | v == v}) : Float = x
fn main(io : IO) : IO = io
"""

    # A predicate mentioning a name that is nowhere in scope.
    cs["unbound_pred"] = """\
module M
fn f(x : {v : Int | v == nowhere}) : Int = x
fn main(io : IO) : IO = print(io, show(f(1)))
"""

    # Mutually recursive measures.  Neither is structural in the other's argument,
    # so the induction has no well-founded order to appeal to — and must say so
    # rather than loop.
    cs["mutual_measure"] = """\
module M
type List a = | Nil | Cons of a, List(a)
measure a(xs : List(Int)) : {v : Int | v >= 0} =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + b(rest)
  end
measure b(xs : List(Int)) : {v : Int | v >= 0} =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + a(rest)
  end
fn main(io : IO) : IO = io
"""

    # Width, in the number of obligations: 300 divisions, each with its own guard.
    divs = "\n".join(f"fn d{i}(a : Int, b : {{v : Int | v != 0}}) : Int = a / b"
                     for i in range(300))
    cs["many_vcs"] = f"""\
module M
{divs}
fn main(io : IO) : IO = print(io, show(d0(1, 1)))
"""

    # Width, in ONE formula: 300 comparisons conjoined.  This is the one that
    # hung — a single linear system with 300 rows, eliminated pairwise.
    wide = " and ".join(f"v + {i} >= {i}" for i in range(300))
    cs["wide_conj"] = f"""\
module M
fn f(x : {{v : Int | {wide}}}) : Int = x
fn main(io : IO) : IO = print(io, show(f(0)))
"""

    # And the degenerate one, which is here because a harness that only tests the
    # extremes has never tested the ordinary.
    cs["empty"] = "module M\nfn main(io : IO) : IO = io\n"
    return cs


# -- The run --------------------------------------------------------------------
#
# In a subprocess, because the two failures being hunted are exactly the two a
# library call cannot survive: a hang has to be killed from outside, and a stack
# overflow is not reliably catchable from inside.

def main() -> int:
    cases = _cases()
    tmp   = tempfile.mkdtemp(prefix="lark-torture-")
    rows  = []

    for name, text in cases.items():
        path = os.path.join(tmp, name + ".lark")
        with open(path, "w") as fh:
            fh.write(textwrap.dedent(text))

        t0 = time.time()
        try:
            r = subprocess.run([sys.executable, CHECK, path],
                               capture_output=True, text=True, timeout=LIMIT)
        except subprocess.TimeoutExpired:
            rows.append((name, "HANG", LIMIT, f"no answer in {LIMIT:.0f}s"))
            continue

        dt   = time.time() - t0
        out  = (r.stdout + r.stderr).strip().splitlines()
        last = out[-1] if out else "(silence)"

        # A traceback is the failure this harness exists for: it is the checker
        # saying nothing, at length.
        if "Traceback" in r.stderr:
            rows.append((name, "CRASH", dt, last[:64]))
        else:
            said = ("ok"       if r.returncode == 0 else
                    "unproved" if r.returncode == 1 else "error")
            rows.append((name, said, dt, last[:64]))

    print(f"torture — {len(rows)} hostile programs, {LIMIT:.0f}s each\n")
    print(f"  {'program':<16} {'verdict':<9} {'time':>7}  said")
    print("  " + "-" * 74)
    bad = 0
    for name, verdict, dt, said in rows:
        if verdict in ("CRASH", "HANG"):
            bad += 1
        print(f"  {name:<16} {verdict:<9} {dt:6.2f}s  {said}")

    if bad:
        print(f"\n  {bad} of {len(rows)} did not answer — a crash is not a verdict, "
              f"and neither is a hang.")
        return 1
    print(f"\n  {len(rows)} of {len(rows)} answered. Every hostile program got a "
          f"verdict: proved, unproved, rejected, or honestly abandoned.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
