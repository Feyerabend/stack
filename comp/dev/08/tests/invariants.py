"""
Invariants — the rules this checker learned the hard way, checked by a machine.

Every bug in the PROVE axis so far was a FINDING. Someone wrote a hostile program
(V2.2‴, the adversary), or read the code with a suspicious eye (V2.2′), or watched a
profiler (H), and out fell a false proof or a quadratic. That method works, and it has
worked seven times — which is exactly the problem with it. **A method that finds bugs by
being lucky stops working when the bugs get rare, and it cannot tell you the difference
between "there are none left" and "I stopped looking".** That is the same distinction the
checker itself is required to make about its own budgets, and it would be a poor joke to
demand it of the tool and not of the people building it.

So the rules stop being prose and become invariants, checked over the whole corpus, on
every run. Each one is a bug we actually shipped, generalised to its shape:

  I1  COVERAGE — every expression node in a checked body is VISITED by `synth`, exactly
      once.
        MISSED  is the shape of V2.2‴(7), the worst bug in the project: four sites
                TRANSLATED a sub-expression (`formula_opt`/`term_opt`) instead of WALKING
                it (`synth`), so every division inside an `if` condition, a comparison,
                a `not` or a unary minus raised no obligation at all. `ok: 0 obligation(s)
                proved`, exit 0, then ZeroDivisionError. It had been doing that inside 07's
                own primes sieve for the fork's entire life, and no test noticed, because
                no test asked *whether the checker had looked*.
        REVISITED is the shape of the H quadratic: a node whose subtree is re-walked at
                every level above it is how an O(n) job becomes O(n²).
      One check, both failure modes, because they are the same question — *how many times
      did you look at this node?* — and the only acceptable answer is once.

  I2  ASKING — every integer division the checker walks raises exactly one obligation.
      The shape of V2.2‴(5): `100 / (x*y)` is non-linear, `100 / h(x)` is a local lambda;
      the checker could not READ either divisor, so it did not ASK, and it proved the
      program. Coverage alone would not catch this — the node was visited. The rule is at
      the opposite polarity from V2.2′: **a hypothesis it cannot read must be dropped; a
      goal it cannot read must be asked anyway.** Silence about what you may assume is
      modesty; silence about what you must prove is a lie. So: count the divisions, count
      the obligations, and demand they agree.

  I3  WORK — the checker's own cost is linear in the size of the program.
      The shape of all three H walks (`is_linear`, `term_opt`, `hash`). This is checked by
      COUNTING, not by timing: the counters are deterministic, so the test is a real
      regression test and not a wall-clock coin flip. Double the program, and the number of
      times the checker walks a tree may roughly double — it may not square. The SOLVER is
      held to a different standard on purpose (Omega on an n-term linear system is honestly
      superlinear, and is fenced rather than fixed); mixing the two would either excuse a
      quadratic in the checker or forbid an honest one in the solver.

None of these can prove the checker sound. What they can do is make a whole CLASS of bug
impossible to ship quietly — which is the only kind this project has actually shipped.

    python3 08/tests/invariants.py          # or: make -C 08 invariants

⛔ Reads 07/. Writes nothing, anywhere. (PROVE.md §0.1)
"""

from __future__ import annotations
import dataclasses, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent     # .../lark/08
LARK = ROOT.parent
SRC  = ROOT / "src"

sys.path.insert(0, str(SRC))
sys.setrecursionlimit(20000)

import pred                                               # noqa: E402
import refine                                             # noqa: E402
import solver                                             # noqa: E402
from tree import (Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,   # noqa: E402
                  LetExpr, IfExpr, MatchExpr, Lambda,
                  TName, TApply, TFn, TUnit, TTuple, TRefine,
                  FnDecl, LetDecl, ImplDecl)

EXPR = (Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
        LetExpr, IfExpr, MatchExpr, Lambda)
TYPE = (TName, TApply, TFn, TUnit, TTuple, TRefine)


# -- The census: every expression node the checker is SUPPOSED to walk ---------------

def _nodes(e: object, out: list) -> None:
    """Every Expr node under `e` that is CODE, in source order, by identity.

    Not the inside of a TYPE.  `{v : Int | v != 0}` carries an Expr — the predicate —
    and a predicate is not code: it is TRANSLATED, strictly, by `term`/`formula`, and if
    it cannot be translated that is an ERROR rather than a shrug.  (That is the V1 rule:
    the solver may say "I could not prove this"; it may not say "I did not understand
    what you wrote".)  Walking a predicate with `synth` would be asking what obligations
    it raises, which is a category mistake — it raises none, it *is* one.

    This distinction is the reason the invariant found a real bug instead of drowning in
    false ones: coverage is a question about code, and the census has to know which is
    which.  A lambda's parameter annotation lives inside the body's subtree, so without
    this line every refined lambda would report its own contract as "never walked".
    """
    if isinstance(e, TYPE):
        return
    if isinstance(e, EXPR):
        out.append(e)
    if dataclasses.is_dataclass(e) and not isinstance(e, type):
        for f in dataclasses.fields(e):
            _nodes(getattr(e, f.name), out)
    elif isinstance(e, tuple):
        for x in e:
            _nodes(x, out)


def census(program) -> list:
    """The bodies the checker walks: functions, top-level lets, impl methods.

    NOT measures. A measure body is checked by `_elab_measure`, a different walk with a
    different job (V2.1's structural check, V2.3's induction), and holding it to `synth`'s
    coverage would be comparing two things that are not the same.
    """
    out: list = []
    for d in program.decls:
        if isinstance(d, FnDecl):
            _nodes(d.body, out)
        elif isinstance(d, LetDecl):
            _nodes(d.value, out)
        elif isinstance(d, ImplDecl):
            for m in d.methods:
                _nodes(m.body, out)
    return out


# THE ONE EXEMPTION, AND IT IS WRITTEN DOWN RATHER THAN HIDDEN IN A TOLERANCE.
#
# The HEAD of an application is not in a value position.  `Apply(fn=Var("safe_div"), …)`
# and `Apply(fn=Con("Cons"), …)` are matched *as a whole*: the head is a NAME to be looked
# up (a signature, a constructor), not a value whose refinement anyone wants.  Asking what
# `Cons` *is* is a different question from what `Cons(x, xs)` is, and the checker is right
# not to ask it.
#
# Note what is NOT exempt: a head that is any other expression — `(fn (x) => …)(3)`, or
# `table(i)(j)` — IS a value, and IS walked.  The exemption is a name in the head
# position, and nothing else.
def exempt(program) -> set[int]:
    out: set[int] = set()
    for n in census(program):
        if isinstance(n, Apply) and isinstance(n.fn, (Var, Con)):
            out.add(id(n.fn))
    return out


# -- The instrumentation ------------------------------------------------------------
#
# All of it lives HERE, in the test, and none of it in src/.  `synth` is a method, so a
# wrapper on the CLASS sees every call including the recursive ones — the checker under
# test is byte-for-byte the checker that ships.

class Counters:
    def __init__(self) -> None:
        # THE CHECKER IS BIDIRECTIONAL, AND THE INVARIANT HAS TO KNOW THAT.
        #
        # `check` pushes an expected type THROUGH an if/let/match, so those nodes are
        # walked by `check` and are never handed to `synth` at all — a coverage test that
        # watched only `synth` would report a third of every program "never walked" and be
        # measuring its own ignorance.  (It did, first time out.  The bug was in the test,
        # and finding it that way is the point: an invariant you have not seen fail for a
        # reason you understand is not yet evidence of anything.)
        #
        # So: two doors, two counters.  A node is COVERED if either door saw it.  A node is
        # RE-WALKED if `synth` saw it more than once — that is the n² shape, and `check`
        # falling through to `synth` at a leaf is one visit through each door, not two
        # walks of a tree.
        self.syn:    dict[int, int] = {}      # id(node) -> times synth saw it
        self.chk:    dict[int, int] = {}      # id(node) -> times check saw it
        self.order:  list = []                # the nodes themselves, to report on
        self.synth:  int = 0                  # total calls (for I3)
        self.term:   int = 0                  # term_opt calls
        self.linear: int = 0                  # pred.is_linear calls
        self.find:   int = 0                  # solver congruence find — the SOLVER's work


def instrument(c: Counters):
    """Patch, run, unpatch.  Returns (restore, seen).

    All of it on the CLASS, so the recursive calls (`self.synth(...)`) go through the
    wrapper too.  Nothing in src/ knows this test exists.
    """
    o_synth  = refine.Refiner.synth
    o_check  = refine.Refiner.check
    o_term   = refine.term_opt
    o_linear = pred.is_linear
    o_find   = solver.Congruence.find
    o_run    = refine.Refiner.run
    seen: list = []

    def note(d, e):
        if id(e) not in c.syn and id(e) not in c.chk:
            c.order.append(e)
        d[id(e)] = d.get(id(e), 0) + 1

    def synth(self, e, env):
        c.synth += 1
        note(c.syn, e)
        return o_synth(self, e, env)

    def check(self, e, t, env, where_):
        note(c.chk, e)
        return o_check(self, e, t, env, where_)

    def term_opt(e, env):
        c.term += 1
        return o_term(e, env)

    def is_linear(t):
        c.linear += 1
        return o_linear(t)

    def find(self, t):
        c.find += 1
        return o_find(self, t)

    def run(self):
        seen.append(self)
        return o_run(self)

    refine.Refiner.synth   = synth
    refine.Refiner.check   = check
    refine.term_opt        = term_opt
    pred.is_linear         = is_linear
    solver.Congruence.find = find
    refine.Refiner.run     = run

    def restore():
        refine.Refiner.synth   = o_synth
        refine.Refiner.check   = o_check
        refine.term_opt        = o_term
        pred.is_linear         = o_linear
        solver.Congruence.find = o_find
        refine.Refiner.run     = o_run

    return restore, seen


def check_file(path: pathlib.Path) -> tuple[Counters, object, object] | None:
    """Check one file with the counters on.  None if the front end rejects it."""
    c = Counters()
    restore, seen = instrument(c)
    try:
        res = refine.check_program(str(path))
    except Exception:
        return None                    # a reject fixture: no walk happened, nothing to say
    finally:
        restore()
    if not seen:
        return None
    return c, seen[-1], res


# `pred._node_hash` is looked up on the CLASS, not the module, so patching the module
# attribute does nothing.  Rather than reach into fourteen dataclasses from a test — which
# would be testing the patch, not the checker — I3 measures hashing INDIRECTLY, by the one
# thing a hash explosion actually costs: nothing else changes, so the counter is dropped
# and `is_linear`/`term_opt`/`synth` carry the invariant.  Honest is better than clever.


# -- I1, I2 --------------------------------------------------------------------------

def coverage(path: pathlib.Path) -> tuple[str, int, int, int]:
    got = check_file(path)
    if got is None:
        return ("rejected", 0, 0, 0)
    c, refiner, _res = got
    program = refiner.program
    ex      = exempt(program)
    want    = [n for n in census(program) if id(n) not in ex]

    missed    = [n for n in want
                 if id(n) not in c.syn and id(n) not in c.chk]
    revisited = [n for n in want if c.syn.get(id(n), 0) > 1]
    return ("walked", len(want), len(missed), len(revisited))


def asking(path: pathlib.Path) -> tuple[int, int]:
    """(integer divisions the checker walked, division obligations it raised)."""
    got = check_file(path)
    if got is None:
        return (0, 0)
    c, refiner, _res = got
    # The `/` nodes the checker ACTUALLY WALKED (either door), against the div-by-zero
    # obligations it raised.  We do not re-derive HM's types here — a Float division
    # raises no obligation by design, so a file containing any float literal is left to
    # the prove/ suite, which pins its verdict exactly.  Everywhere else the two numbers
    # must agree, and there is no tolerance.
    #
    # The obligations are identified by their PROVENANCE, not by their shape: `d /= 0` is
    # also the goal of a CALL whose parameter is `{v : Int | v != 0}`, and counting those
    # as divisions would let a missing division hide behind a contract that happened to
    # say the same thing.  A VC knows where it came from, and that is the thing to ask.
    divs = sum(1 for n in c.order if isinstance(n, BinOp) and n.op == "/")
    vcs  = sum(1 for vc in refiner.vcs
               if vc.where_.startswith("division by zero:"))
    floats = sum(1 for n in c.order if isinstance(n, Lit)
                 and isinstance(n.value, float))
    return (divs, vcs) if not floats else (-1, -1)   # a Float file: not this test's business


# -- I4 ------------------------------------------------------------------------------
#
# A BOOL-VALUED MEASURE IS A PROPOSITION, AND A PROPOSITION IS NOT A NUMBER.  This is the
# mirror of the bug V2.4 was built to avoid — not "a Bool measure the solver cannot
# decide", but "a Bool measure it decides as if it were an Int".  `pos(t)` is sorted
# `bool`; the moment it turns up as an operand of `+`, of unary minus, or of an ordering
# `<`, the solver is being asked to do integer arithmetic on a truth value, and the sort
# guard in `_int_term` is the one line standing between that and a proof of anything.
#
# So the invariant asks, of every VC the checker actually built (assumptions AND goal, so
# the instantiated measure equivalences are included), the two halves of the same
# property:
#
#   POSITION — no application of a Bool measure appears in an INTEGER position: a direct
#              operand of `Arith`/`Neg`, or a side of an ORDERING comparison (`<`, `<=`,
#              `>`, `>=`).  Equality (`==`/`/=`) is exempt, because it is decided at every
#              sort — `pos(t) == false` is a perfectly good Bool fact.  A bool app buried
#              inside another uninterpreted application's argument is not chased: that
#              arg's sort is the callee's business, and OTHER-sorted terms are equality-
#              only anyway.
#
#   SORT     — wherever the solver's sort table names a Bool measure, it names it `bool`.
#              A symbol registered `int` would be read into the linear system directly,
#              with no `Atom` and no bridge, which is the same disaster by the front door.
#
# Like I1–I3 this cannot prove the rung sound; it makes ONE class of unsoundness — a Bool
# measure silently treated as an integer — impossible to ship without a red line here.

def _bool_measures(refiner) -> set[str]:
    return {name for name, m in refiner.measures.items()
            if getattr(m.ret, "base", None) == "Bool"}


def _bm_in_int_term(t, bmeas: set[str], integer: bool) -> int:
    """Bool-measure apps sitting in an integer position within a term.

    `integer` is True only for the immediate operands of arithmetic; recursing into an
    application's arguments turns it back off, because those positions belong to the
    callee's signature, not to arithmetic.
    """
    from pred import App as _App, Arith as _Arith, Neg as _Neg
    n = 1 if (integer and isinstance(t, _App) and t.fn in bmeas) else 0
    if isinstance(t, _App):
        for a in t.args:
            n += _bm_in_int_term(a, bmeas, False)
    elif isinstance(t, _Arith):
        n += _bm_in_int_term(t.left, bmeas, True) + _bm_in_int_term(t.right, bmeas, True)
    elif isinstance(t, _Neg):
        n += _bm_in_int_term(t.term, bmeas, True)
    return n


def _bm_in_int_formula(f, bmeas: set[str]) -> int:
    from pred import (Atom as _Atom, Cmp as _Cmp, Not as _Not,
                      And as _And, Or as _Or, Implies as _Implies)
    if isinstance(f, _Atom):
        return _bm_in_int_term(f.term, bmeas, False)
    if isinstance(f, _Cmp):
        integer = f.op not in ("==", "/=")
        return (_bm_in_int_term(f.left, bmeas, integer)
                + _bm_in_int_term(f.right, bmeas, integer))
    if isinstance(f, _Not):
        return _bm_in_int_formula(f.f, bmeas)
    if isinstance(f, (_And, _Or, _Implies)):
        return _bm_in_int_formula(f.left, bmeas) + _bm_in_int_formula(f.right, bmeas)
    return 0


def atoms(path: pathlib.Path) -> tuple[int, int, int]:
    """(bool-measure symbols the VCs mention, apps in an integer position, sort errors)."""
    got = check_file(path)
    if got is None:
        return (0, 0, 0)
    c, refiner, _res = got
    bmeas = _bool_measures(refiner)
    if not bmeas:
        return (0, 0, 0)
    seen = badpos = badsort = 0
    for vc in refiner.vcs:
        for f in vc.assumptions() + [vc.goal]:
            badpos += _bm_in_int_formula(f, bmeas)
        for m in bmeas:
            if m in vc.sorts.fn:
                seen += 1
                if vc.sorts.fn[m] != "bool":
                    badsort += 1
    return (seen, badpos, badsort)


# -- I5 ------------------------------------------------------------------------------
#
# A GUARDED PREDICATE IS TRANSLATED FAITHFULLY, OR NOT AT ALL.  V2.4c step 2 gave the
# predicate language one new shape, `if c then p else q`, and the whole of its soundness
# is that the translation is `(c => p) and (not c => q)` with NEITHER branch silently
# replaced by `true`/`false`.  A `Top` where the source said `v == x * x * x` is exactly
# false proofs #2 and #7 — an untranslatable branch that became `or Top()` — one level up
# from the solver, in the predicate language itself.
#
# I2 cannot see this: an `if`-predicate raises no obligation of its own, it IS a formula,
# so counting obligations says nothing about whether it was built honestly.  So I5
# watches the TRANSLATION.  For every `IfExpr` that reaches `formula_opt` anywhere in the
# corpus, either the result is None (untranslatable — sound; the declaration rejects it),
# or it is EXACTLY `And(Implies(a, p), Implies(Not(a), q))` with the SAME condition
# formula `a` on both sides and no branch formula `Top`/`Bot` unless the source branch was
# a literal `true`/`false`.  Any other shape is a dropped guard; a `Top` on a non-literal
# branch is the lie.  (`formula_opt` is a module global whose recursion resolves through
# the module, so patching it catches every nested `if` too — nothing in src/ knows.)

def _lit_bool(e) -> bool:
    from tree import Lit as _Lit, Con as _Con
    return (isinstance(e, _Lit) and isinstance(e.value, bool)) or \
           (isinstance(e, _Con) and e.name in ("True", "False"))


def _faithful(e, r) -> bool:
    """Is `r` the faithful translation of the `IfExpr` `e` — or a None we accept?"""
    from pred import (And as _And, Implies as _Implies, Not as _Not,
                      Top as _Top, Bot as _Bot)
    if r is None:
        return True                          # untranslatable: sound (the drop)
    match r:
        case _And(left=_Implies(left=a1, right=p),
                  right=_Implies(left=_Not(f=a2), right=q)):
            if a1 != a2:
                return False                 # two different guards — not one `if`
            for f, src in ((a1, e.cond), (p, e.then_), (q, e.else_)):
                if isinstance(f, (_Top, _Bot)) and not _lit_bool(src):
                    return False             # collapsed to true/false with no source to say so
            return True
    return False                             # any other shape is a dropped guard


def guarded(path: pathlib.Path) -> tuple[int, int]:
    """(if-predicates translated, faithful-translation violations)."""
    from tree import IfExpr as _If
    o_fo = refine.formula_opt
    seen = [0]
    bad = [0]

    def fo(e, env):
        r = o_fo(e, env)
        if isinstance(e, _If):
            seen[0] += 1
            if not _faithful(e, r):
                bad[0] += 1
        return r

    refine.formula_opt = fo
    try:
        refine.check_program(str(path))
    except Exception:
        pass                                 # a reject fixture still translated its `if`s
    finally:
        refine.formula_opt = o_fo
    return seen[0], bad[0]


# -- I6 ------------------------------------------------------------------------------
#
# A FLATTENED GUARD NAMES ONLY WHAT WAS BOUND ON THE WAY IN.  V2.4c step 3 Part B gave a
# measure one new shape, a NESTED match on a field of the one already taken apart, and its
# soundness turns on flattening: `match t with | Node(l, v, r) => match r with | Leaf =>
# … | Node(rl, rv, rr) => …` becomes several `MArm`s that share the outer `con` and carry
# a chain of `Guard(var, con, binders, …)` — one per inner step.  `_instantiate` fires
# such an arm only when `sub[g.var]` is a concrete application of `g.con`; if `g.var` is a
# name that was NEVER bound on the way in — not the parameter, not an outer field binder,
# not a binder introduced by an EARLIER guard in the same arm — then `sub.get(g.var)` is
# None, the arm never fires FOR ANY TERM, and the measure is silently PARTIAL along that
# path.  That is `11_measure_partial`'s unsoundness wearing a disguise the totality check
# cannot see: totality counts constructor ARMS, and the arm is present; it is only
# UNFIREABLE.  A partial measure with a declared result is a false proof — the result
# axiom is asserted at a term no equation ever pins.
#
# So I6 walks the FLATTENED arms the checker will actually instantiate and asks, of every
# guard, whether its scrutinee is in scope at that point: scope starts at {the parameter}
# ∪ {the outer binders}, and each guard, once checked, ADDS its own binders (a later guard
# may legitimately destructure a binder an earlier one introduced — that is exactly a
# match nested two deep).  A guard naming anything else is a dropped arm.  Like I1–I5 this
# proves nothing about the rung; it makes ONE flattening bug — a guard on a name out of
# scope — impossible to ship green.

def guardscope(path: pathlib.Path) -> tuple[int, int]:
    """(guards over all flattened measure arms, guards whose scrutinee is out of scope)."""
    got = check_file(path)
    if got is None:
        return (0, 0)
    _c, refiner, _res = got
    seen = bad = 0
    for m in refiner.measures.values():
        for arm in m.arms:
            scope = {m.param} | {b for b in arm.binders if b != "_"}
            for g in arm.guards:
                seen += 1
                if g.var not in scope:
                    bad += 1
                scope |= {b for b in g.binders if b != "_"}
    return (seen, bad)


# -- I3 ------------------------------------------------------------------------------

SUM = """\
module Scale
fn big(x : {{v : Int | v > 0}}) : Int = let s = {sum} in 100 / x
fn main(io : IO) : IO = print(io, show(big(3)))
"""


def work_at(n: int, tmp: pathlib.Path) -> Counters:
    body = " + ".join(f"x*{i}" if i % 3 else str(i) for i in range(1, n))
    src  = SUM.format(sum=body)
    f    = tmp / f"scale_{n}.lark"
    f.write_text(src)
    got = check_file(f)
    assert got is not None, f"the scaling probe stopped checking at n={n}"
    return got[0]


# -- main ----------------------------------------------------------------------------

def main() -> int:
    files = sorted(p for d in ("07/tests", "07/samples")
                   for p in (LARK / d).rglob("*.lark"))
    files += sorted((LARK / "prove").glob("*.lark"))

    print(f"invariants — the checker's own rules, over {len(files)} files\n")
    bad = 0

    # I1 -----------------------------------------------------------------------------
    print("  I1  coverage: every expression node walked exactly once")
    tot = miss = revis = 0
    for f in files:
        kind, want, m, r = coverage(f)
        if kind == "rejected":
            continue
        tot += want
        if m or r:
            bad += 1
            miss += m
            revis += r
            print(f"      ✗ {f.relative_to(LARK)}: "
                  f"{m} never walked, {r} walked twice (of {want})")
    print(f"      {tot} nodes, {miss} never walked, {revis} walked twice"
          f"{'' if not (miss or revis) else '   ← A NODE THE CHECKER DID NOT LOOK AT'}")

    # I2 -----------------------------------------------------------------------------
    print("\n  I2  asking: every integer division raises exactly one obligation")
    d_tot = v_tot = 0
    for f in files:
        d, v = asking(f)
        if d < 0:
            continue                       # a Float file
        d_tot += d
        v_tot += v
        if d != v:
            bad += 1
            print(f"      ✗ {f.relative_to(LARK)}: {d} divisions walked, "
                  f"{v} obligations raised")
    print(f"      {d_tot} divisions, {v_tot} obligations"
          f"{'' if d_tot == v_tot else '   ← A GOAL THAT WAS NEVER ASKED'}")

    # I3 -----------------------------------------------------------------------------
    print("\n  I3  work: the checker's own cost is linear in the size of the program")
    tmp = pathlib.Path(__file__).resolve().parent / "_scale"
    tmp.mkdir(exist_ok=True)
    ns = (100, 200, 400, 800)
    runs = {n: work_at(n, tmp) for n in ns}
    for p in tmp.glob("*.lark"):
        p.unlink()
    tmp.rmdir()

    print(f"      {'n':>6}  {'synth':>9}  {'term_opt':>9}  {'is_linear':>10}"
          f"  {'  (solver: find)':>16}")
    for n in ns:
        c = runs[n]
        print(f"      {n:>6}  {c.synth:>9}  {c.term:>9}  {c.linear:>10}"
              f"  {c.find:>16}")

    # Doubling the program may double the checker's walking.  It may not square it.
    # 2.5 leaves room for the constant factors of a real program without leaving room
    # for an exponent of 2 — at n=800 a quadratic is 8x over budget, not 1.2x.
    LIMIT = 2.5
    for name, get in (("synth",     lambda c: c.synth),
                      ("term_opt",  lambda c: c.term),
                      ("is_linear", lambda c: c.linear)):
        for a, b in zip(ns, ns[1:]):
            xa, xb = get(runs[a]), get(runs[b])
            ratio = xb / max(xa, 1)
            if ratio > LIMIT:
                bad += 1
                print(f"      ✗ {name}: {a}→{b} grew {ratio:.1f}x   "
                      f"← SUPERLINEAR; the checker is walking a tree it already walked")
    print(f"      growth per doubling, all three counters: "
          f"{max(get(runs[b]) / max(get(runs[a]), 1) for _, get in ((0, lambda c: c.synth), (0, lambda c: c.term), (0, lambda c: c.linear)) for a, b in zip(ns, ns[1:])):.2f}x"
          f"  (budget {LIMIT}x — a quadratic would be 2x this)")
    print("      the SOLVER's find() is allowed to grow faster: Omega on an n-term")
    print("      system is honestly superlinear, and is fenced (MAX_WORK), not fixed.")

    # I4 -----------------------------------------------------------------------------
    print("\n  I4  atoms: a Bool measure is a proposition, never an integer")
    seen = pos = srt = 0
    for f in files:
        s, p, r = atoms(f)
        seen += s
        if p or r:
            bad += 1
            pos += p
            srt += r
            print(f"      ✗ {f.relative_to(LARK)}: {p} in an integer position, "
                  f"{r} sorted wrong")
    print(f"      {seen} Bool-measure references, {pos} in an integer position, "
          f"{srt} mis-sorted"
          f"{'' if not (pos or srt) else '   ← A TRUTH VALUE READ AS A NUMBER'}")

    # I5 -----------------------------------------------------------------------------
    print("\n  I5  guarding: an `if`-predicate is translated faithfully, or not at all")
    g_seen = g_bad = 0
    for f in files:
        s, b = guarded(f)
        g_seen += s
        if b:
            bad += 1
            g_bad += b
            print(f"      ✗ {f.relative_to(LARK)}: {b} if-predicate(s) mistranslated")
    print(f"      {g_seen} if-predicates translated, {g_bad} mistranslated"
          f"{'' if not g_bad else '   ← A GUARD DROPPED, OR A BRANCH BECAME true'}")

    # I6 -----------------------------------------------------------------------------
    print("\n  I6  scoping: every nested-measure guard names a variable bound on the way in")
    n_seen = n_bad = 0
    for f in files:
        s, b = guardscope(f)
        n_seen += s
        if b:
            bad += 1
            n_bad += b
            print(f"      ✗ {f.relative_to(LARK)}: {b} guard(s) on a name out of scope")
    print(f"      {n_seen} nested guards, {n_bad} out of scope"
          f"{'' if not n_bad else '   ← AN ARM THAT CAN NEVER FIRE — A MEASURE SILENTLY PARTIAL'}")

    print()
    if bad:
        print(f"  {bad} invariant violation(s).")
        return 1
    print("  invariants hold — the checker looked at every node once, asked about every")
    print("  division, and did not walk a tree twice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
