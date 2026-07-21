"""
Solver soundness fuzz — the decision procedure against a reference semantics.

`solver.py` is ~780 lines of congruence closure, Omega and DPLL(T) that I wrote by
hand, and the refinement checker believes every word of it. So it gets tested the
way you test something you cannot afford to be wrong: against a brute-force
interpreter of the same logic, on thousands of formulas nobody chose.

**The two directions are not equally serious, and the test says so.**

    solver says UNSAT, a model exists   →  it INVENTED a contradiction
                                            ⇒ `valid()` says True
                                            ⇒ a false program is PROVED
                                            ⇒ FATAL.  Hard failure, every time.

    solver says SAT, no model in the box →  the model may simply be outside the box
                                            (Omega is exact over ℤ; my search is not)
                                            ⇒ counted, reported, never a failure.

That asymmetry is the whole design. The abstraction in `Theory._project` only ever
*drops* constraints, so the solver can fail to find a contradiction that exists —
which rejects a good program, and is annoying — but it must never find one that
does not, which accepts a bad program, and is fatal. This fuzz is the assertion of
that, run against random input rather than argued in a comment.

The third property is the one the checker actually depends on, so it is tested
directly rather than inferred:

    valid(hyps, goal) == True  ⇒  no assignment satisfies hyps and falsifies goal.

**Uninterpreted functions are given their real semantics, not a stand-in.** Every
distinct application term gets its own value in an assignment, and assignments that
violate functional consistency — the same arguments mapping to different results —
are *filtered out*. That is exactly what "uninterpreted, but a function" means, and
it is what makes a congruence bug visible here instead of in a program.

    python3 08/tests/solver_fuzz.py [N] [seed]      # or: make -C 08 fuzz

Deterministic: same seed, same formulas, same verdict. Default 3000 cases, seed 7.
"""

from __future__ import annotations
import itertools, pathlib, random, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pred                                                    # noqa: E402
import solver                                                  # noqa: E402
from pred import (Num, Var, Neg, Arith, App, BoolLit,          # noqa: E402
                  Top, Bot, Cmp, Atom, Not, And, Or, Implies)
from solver import Sorts, INT, BOOL                            # noqa: E402


# The box the reference interpreter searches.  Small on purpose: the point is to
# make the search exhaustive over *something*, not to make it big.
LO, HI = -3, 3
DOMAIN = range(LO, HI + 1)

IVARS = ["x", "y", "z"]
BVARS = ["p", "q"]
UFS   = ["f", "g"]          # f : Int -> Int,  g : Int -> Int

SORTS = Sorts(
    var={**{v: INT for v in IVARS}, **{b: BOOL for b in BVARS}},
    fn={u: INT for u in UFS},
)


# -- Generators -----------------------------------------------------------------

def gen_iterm(rng: random.Random, depth: int) -> object:
    """A linear integer term.  Multiplication is literal x term, always — the
    generator cannot produce `x * y`, because `pred` cannot represent it."""
    if depth <= 0:
        return rng.choice([Num(rng.randint(-5, 5)), Var(rng.choice(IVARS))])
    match rng.randint(0, 6):
        case 0 | 1:
            return Num(rng.randint(-5, 5))
        case 2 | 3:
            return Var(rng.choice(IVARS))
        case 4:
            return Arith(rng.choice("+-"),
                         gen_iterm(rng, depth - 1), gen_iterm(rng, depth - 1))
        case 5:
            return Arith("*", Num(rng.randint(-3, 3)), gen_iterm(rng, depth - 1))
        case _:
            return App(rng.choice(UFS), (gen_iterm(rng, depth - 1),))


def gen_formula(rng: random.Random, depth: int) -> object:
    if depth <= 0:
        return gen_atom(rng)
    match rng.randint(0, 8):
        case 0 | 1 | 2 | 3:
            return gen_atom(rng)
        case 4:
            return Not(gen_formula(rng, depth - 1))
        case 5:
            return And(gen_formula(rng, depth - 1), gen_formula(rng, depth - 1))
        case 6:
            return Or(gen_formula(rng, depth - 1), gen_formula(rng, depth - 1))
        case 7:
            return Implies(gen_formula(rng, depth - 1), gen_formula(rng, depth - 1))
        case _:
            return rng.choice([Top(), Bot()])


def gen_atom(rng: random.Random) -> object:
    if rng.random() < 0.15:
        return Atom(Var(rng.choice(BVARS)))
    op = rng.choice(["==", "/=", "<", "<=", ">", ">="])
    return Cmp(op, gen_iterm(rng, 2), gen_iterm(rng, 2))


# -- The reference semantics ----------------------------------------------------

def app_terms(fs: list) -> list:
    """Every distinct application term, innermost first, so a nested `f(g(x))` can
    be evaluated once its argument has a value."""
    out: list = []

    def walk_t(t) -> None:
        match t:
            case App(args=args):
                for a in args:
                    walk_t(a)
                if t not in out:
                    out.append(t)
            case Neg(term=x):
                walk_t(x)
            case Arith(left=l, right=r):
                walk_t(l); walk_t(r)

    def walk_f(f) -> None:
        match f:
            case Cmp(left=l, right=r):
                walk_t(l); walk_t(r)
            case Atom(term=t):
                walk_t(t)
            case Not(f=g):
                walk_f(g)
            case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
                walk_f(l); walk_f(r)

    for f in fs:
        walk_f(f)
    return out


class Eval:
    """Evaluate a term or formula under an assignment.  `apps` maps an application
    term to its value; a term whose argument is outside the box has no value, and
    the assignment is then simply not a witness (`Undef`)."""

    class Undef(Exception):
        pass

    def __init__(self, ivals: dict, bvals: dict, apps: dict):
        self.ivals, self.bvals, self.apps = ivals, bvals, apps

    def term(self, t) -> int:
        match t:
            case Num(value=n):
                return n
            case Var(name=n):
                if n in self.ivals:
                    return self.ivals[n]
                raise Eval.Undef(n)
            case Neg(term=x):
                return -self.term(x)
            case Arith(op=op, left=l, right=r):
                a, b = self.term(l), self.term(r)
                return a + b if op == "+" else a - b if op == "-" else a * b
            case App():
                if t in self.apps:
                    return self.apps[t]
                raise Eval.Undef(str(t))
        raise Eval.Undef(str(t))

    def formula(self, f) -> bool:
        match f:
            case Top():
                return True
            case Bot():
                return False
            case Cmp(op=op, left=l, right=r):
                a, b = self.term(l), self.term(r)
                return {"==": a == b, "/=": a != b, "<": a < b,
                        "<=": a <= b, ">": a > b, ">=": a >= b}[op]
            case Atom(term=Var(name=n)):
                return self.bvals[n]
            case Atom(term=BoolLit(value=v)):
                return v
            case Not(f=g):
                return not self.formula(g)
            case And(left=l, right=r):
                return self.formula(l) and self.formula(r)
            case Or(left=l, right=r):
                return self.formula(l) or self.formula(r)
            case Implies(left=l, right=r):
                return (not self.formula(l)) or self.formula(r)
        raise Eval.Undef(str(f))


# Above this many enumerated dimensions the exhaustive search stops being
# exhaustive-in-reasonable-time.  A skipped case is reported, never silently
# counted as agreement — a fuzz that quietly skips what it cannot handle is a fuzz
# that passes.
MAX_DIMS = 5


class TooBig(Exception):
    pass


def brute_model(fs: list):
    """Search the box exhaustively for a model of `fs`, or return None.

    Only the variables and application terms the formula MENTIONS are enumerated —
    the others are free, and enumerating them multiplies the search by a factor
    that buys nothing.

    UF is given its real semantics: each application term gets its own value, and
    an assignment is DISCARDED if two applications of the same symbol have equal
    arguments but different values.  Without that filter this would be testing a
    solver for a logic nobody uses.
    """
    apps  = app_terms(fs)
    used  = set()
    for f in fs:
        used |= pred.free_vars(f)
    ivars = sorted(v for v in IVARS if v in used)
    bvars = sorted(v for v in BVARS if v in used)

    if len(ivars) + len(apps) > MAX_DIMS:
        raise TooBig()

    for ivals in itertools.product(DOMAIN, repeat=len(ivars)):
        iv = dict(zip(ivars, ivals))
        for bvals in itertools.product([False, True], repeat=len(bvars)):
            bv = dict(zip(bvars, bvals))
            for avals in itertools.product(DOMAIN, repeat=len(apps)):
                av = dict(zip(apps, avals))
                ev = Eval(iv, bv, av)

                # Functional consistency: same symbol, same argument VALUES ⇒ same result.
                try:
                    sig: dict = {}
                    bad = False
                    for a in apps:
                        key = (a.fn, tuple(ev.term(x) for x in a.args))
                        if key in sig and sig[key] != av[a]:
                            bad = True
                            break
                        sig[key] = av[a]
                    if bad:
                        continue
                    if all(ev.formula(f) for f in fs):
                        return (iv, bv, av)
                except Eval.Undef:
                    continue
    return None


# -- The fuzz -------------------------------------------------------------------

def main() -> int:
    n    = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    rng  = random.Random(seed)

    print(f"solver soundness fuzz — {n} cases, seed {seed}, box [{LO},{HI}]\n")

    unsound = []          # solver said UNSAT; a model exists.  FATAL.
    invalid = []          # solver said VALID; a counterexample exists.  FATAL.
    unconfirmed = 0       # solver said SAT; no model in the box.  Fine — box is small.
    agreed = 0
    skipped = 0           # too many dimensions to brute-force.  Reported, never hidden.

    for i in range(n):
        # Half the cases are a satisfiability question, half an entailment one —
        # entailment is what the checker actually asks, so it gets tested directly.
        if i % 2 == 0:
            fs = [gen_formula(rng, 2) for _ in range(rng.randint(1, 3))]
            try:
                sat = solver.satisfiable(fs, SORTS)
            except Exception as e:                       # a crash is a failure
                print(f"  CRASH on {[pred.show(f) for f in fs]}\n    {e!r}")
                return 1
            try:
                model = brute_model(fs)
            except TooBig:
                skipped += 1
                continue
            if not sat and model is not None:
                unsound.append((fs, model))
            elif sat and model is None:
                unconfirmed += 1
            else:
                agreed += 1
        else:
            hyps = [gen_formula(rng, 2) for _ in range(rng.randint(1, 2))]
            goal = gen_formula(rng, 2)
            try:
                ok = solver.valid(hyps, goal, SORTS)
            except Exception as e:
                print(f"  CRASH on entailment\n    {e!r}")
                return 1
            # A counterexample: hyps hold, goal fails.
            try:
                cex = brute_model(hyps + [Not(goal)])
            except TooBig:
                skipped += 1
                continue
            if ok and cex is not None:
                invalid.append((hyps, goal, cex))
            else:
                agreed += 1

        if (i + 1) % 500 == 0:
            print(f"  {i + 1:5d} cases   {len(unsound) + len(invalid)} unsound, "
                  f"{unconfirmed} unconfirmed-SAT, {skipped} skipped")

    print(f"\n  {agreed} agreed, {unconfirmed} SAT-with-no-model-in-box, "
          f"{skipped} too big to brute-force")

    if unsound or invalid:
        print(f"\n  ⛔ UNSOUND — {len(unsound) + len(invalid)} case(s). The solver "
              f"invented a contradiction, which means it can PROVE A FALSE PROGRAM.")
        for fs, model in unsound[:3]:
            print(f"\n    said UNSAT: {[pred.show(f) for f in fs]}")
            print(f"    but: {model}")
        for hyps, goal, cex in invalid[:3]:
            print(f"\n    said VALID: {[pred.show(h) for h in hyps]} ⊢ {pred.show(goal)}")
            print(f"    counterexample: {cex}")
        return 1

    print("\n  sound — the solver never claimed a contradiction that does not exist,\n"
          "  and never proved a goal that has a counterexample.")
    if unconfirmed:
        print(f"  ({unconfirmed} SAT answers had no witness inside [{LO},{HI}] — expected:\n"
              "   Omega is exact over ℤ, and a small box is not.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
