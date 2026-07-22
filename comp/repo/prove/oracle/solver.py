"""
A decision procedure for QF-UFLIA, from scratch.

No Z3, no SMT-LIB, no external binary.  The plan's `--smt` escape hatch was there
to unblock the VC generator if this module turned out to be the long pole; it did
not, so it does not exist.  Lark's whole arc is "build it yourself, from silicon
to semantics", and a verifier that shells out to someone else's prover is a hole
in that arc — and, concretely, a hole in the Pico story, where there is no Z3.

Three layers, which is what "QF-UFLIA" spells out to:

  DPLL(T)              — the *QF* part: a formula is a boolean skeleton over
  (this file, §4)        theory atoms.  Enumerate the skeleton's models with
                         unit propagation; hand each one to the theory as a
                         conjunction of literals.  A formula is unsatisfiable iff
                         every boolean model is theory-inconsistent.

  congruence closure   — the *UF* part.  Union-find over the term DAG, plus the
  (§2)                   congruence rule: equal arguments give equal results.
                         `len(xs)` means nothing to us except that it equals
                         `len(ys)` when `xs == ys`.  That is the *only* thing a
                         refinement needs from an unmodelled function, and it is
                         free.

  the Omega test       — the *LIA* part: satisfiability of a conjunction of
  (§3)                   linear equalities and inequalities over the INTEGERS.
                         Not the rationals: `2x = 1` is unsatisfiable and a
                         checker that misses that is not checking Lark's Ints.

The two theories are combined the cheap, sound way (§3.4): every integer-sorted
term that arithmetic cannot see through — a variable, or an application like
`string_length(s)` — becomes one *column* in the linear system, keyed by its
congruence class.  Congruent terms therefore share a column automatically, which
is the CC → LIA channel; a Nelson–Oppen loop feeds equalities the other way.

Soundness is the property that matters and it is easy to see: the abstraction only
ever *drops* constraints, so the solver can fail to find a contradiction, but it
cannot invent one.  A missed contradiction rejects a good program (annoying); an
invented one accepts a bad program (fatal).  We only risk the annoying failure.
"""

from __future__ import annotations
import math
from dataclasses import dataclass, field

import pred
from pred import (
    Term, Num, BoolLit, Var, Neg, Arith, App,
    Formula, Top, Bot, Cmp, Atom, Not, And, Or, Implies,
    PredError,
)

INT, BOOL, OTHER = "int", "bool", "other"

# Guards.  A refinement VC that needs more than this is not a VC we understand.
MAX_CLAUSES  = 20000
MAX_OMEGA    = 400      # recursion depth / splinter budget
MAX_DISEQ    = 12       # disequalities to case-split: the split costs 2^k
MAX_SPLITS   = 20000    # Omega calls in ONE theory check
MAX_WORK     = 2_000_000  # theory work in ONE satisfiable() call — see Exhausted
MAX_LINEAR   = 256      # rows in ONE linear system: FM is quadratic per elimination


class Budget(Exception):
    """The solver ran out of room and stopped looking.

    Not an error, and never reported as one.  Every `except Budget` in this file
    resolves the same way — towards *consistent*, i.e. "I found no contradiction".
    That is the sound direction: a theory check that admits a model it cannot rule
    out makes `satisfiable` True, which makes `valid` False, which makes refine.py
    say "cannot prove".  Annoying, and safe.  Resolving the other way would let an
    exhausted budget *manufacture* a proof, which is the one thing a checker must
    never do.
    """


class Exhausted(Budget):
    """The budget for the WHOLE query is gone — abandon it, do not merely give up here.

    The distinction is the hardening finding, and it is the shape of every fence that
    has ever failed: EVERY FENCE HERE WAS LOCAL, AND EVERY CALLER LOOPS.  `MAX_SPLITS`
    bounds the Omega calls in one `_lia`, and is re-armed on the next one; `_propagate`
    calls `_lia` once per pair of shared terms (quadratically many), and DPLL calls
    `consistent` once per node of a search that is exponential in the atom count.  So
    the total work in a single `satisfiable()` had no bound at all, and a 300-conjunct
    predicate — an unremarkable thing for a program to write — ground for minutes.

    A checker that hangs has failed, and it has failed in a way that is WORSE than a
    wrong answer, because it never gets round to giving one.  So the budget is spent
    from one purse, held by the `Theory` that lives exactly as long as the query, and
    when it is empty the query is abandoned in the sound direction (`satisfiable` =
    True = "cannot prove").  `_lia` catches `Budget` and gives up locally; it must
    RE-RAISE this one, or the caller simply loops on an empty purse.
    """


# -- §1. Sorts ------------------------------------------------------------------
#
# The sorts come from the HM types refine.py already inferred — we do not
# re-derive them here.  A term is int-sorted, bool-sorted, or opaque; opaque terms
# (a String, a List) take part in equality reasoning only, never in arithmetic.

@dataclass(frozen=True)
class Sorts:
    var: dict[str, str] = field(default_factory=dict)   # variable  -> sort
    fn:  dict[str, str] = field(default_factory=dict)   # UF symbol -> result sort

    def of(self, t: Term) -> str:
        match t:
            case Num() | Neg() | Arith():
                return INT
            case BoolLit():
                return BOOL
            case Var(name=n):
                return self.var.get(n, OTHER)
            case App(fn=f):
                return self.fn.get(f, OTHER)
        return OTHER


# -- §2. Congruence closure -----------------------------------------------------
#
# Union-find over subterms, with the congruence rule applied to fixpoint: if the
# arguments of two applications of the same symbol are pairwise equal, the two
# applications are equal.  Applied to `+` and `-` as well, which is sound — they
# are functions too — and occasionally buys a fact arithmetic missed.

class Congruence:
    def __init__(self) -> None:
        self.parent: dict[Term, Term] = {}
        self.terms:  list[Term] = []
        # `terms` is unique and append-only, so a term's index is fixed the moment it
        # is added.  Keeping it here makes `Theory._column` O(1) instead of a linear
        # `terms.index(...)` scan run once per int-sorted term per projection per DPLL
        # node — which is where a wide predicate's time actually went.  Same column
        # names, same answers: this is a faster way to compute what it already computed.
        self.pos:    dict[Term, int] = {}

    def add(self, t: Term) -> None:
        if t in self.parent:
            return
        self.parent[t] = t
        self.pos[t] = len(self.terms)
        self.terms.append(t)
        for sub in _children(t):
            self.add(sub)

    def find(self, t: Term) -> Term:
        root = t
        while self.parent[root] != root:
            root = self.parent[root]
        while self.parent[t] != root:      # path compression
            self.parent[t], t = root, self.parent[t]
        return root

    def union(self, a: Term, b: Term) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb

    def merge(self, a: Term, b: Term) -> None:
        self.add(a)
        self.add(b)
        self.union(a, b)

    def saturate(self) -> None:
        """Apply the congruence rule until nothing changes."""
        changed = True
        while changed:
            changed = False
            sigs: dict[tuple, Term] = {}
            for t in self.terms:
                sig = _signature(t, self)
                if sig is None:
                    continue
                if sig in sigs:
                    if self.find(sigs[sig]) != self.find(t):
                        self.union(sigs[sig], t)
                        changed = True
                else:
                    sigs[sig] = t

    def equal(self, a: Term, b: Term) -> bool:
        self.add(a)
        self.add(b)
        return self.find(a) == self.find(b)


def _children(t: Term) -> tuple[Term, ...]:
    match t:
        case Neg(term=x):
            return (x,)
        case Arith(left=l, right=r):
            return (l, r)
        case App(args=args):
            return args
    return ()


def _signature(t: Term, cc: Congruence) -> tuple | None:
    """A term's congruence signature: its symbol plus the *classes* of its args."""
    match t:
        case Neg(term=x):
            return ("neg", cc.find(x))
        case Arith(op=op, left=l, right=r):
            return (op, cc.find(l), cc.find(r))
        case App(fn=f, args=args):
            return (f,) + tuple(cc.find(a) for a in args)
    return None


# -- §3. The Omega test — linear integer arithmetic ------------------------------
#
# A constraint is a dict {var: coefficient, CONST: k}, read as
#     Σ coeff·var + k  =  0     (an equality)
#     Σ coeff·var + k  >= 0     (an inequality)
# Satisfiability is decided over ℤ, exactly, by Pugh's Omega test: eliminate
# equalities (§3.1), then eliminate variables from the inequalities by
# Fourier–Motzkin with the dark-shadow refinement, splintering when the shadows
# disagree (§3.2).  Splintering is the difference between "decides LIA over the
# integers" and "decides LIA over the rationals and hopes".

CONST = ""
Lin = dict[str, int]


def _norm_eq(c: Lin) -> Lin | bool:
    """Normalise an equality; True = trivially satisfied, False = unsatisfiable."""
    vs = {k: v for k, v in c.items() if k != CONST and v != 0}
    k = c.get(CONST, 0)
    if not vs:
        return k == 0
    g = 0
    for v in vs.values():
        g = math.gcd(g, abs(v))
    if k % g != 0:
        return False                       # e.g. 2x = 1 — no integer solution
    out = {var: v // g for var, v in vs.items()}
    out[CONST] = k // g
    return out


def _norm_ineq(c: Lin) -> Lin | bool:
    """Normalise an inequality.  The floor is the integer tightening:
    3x + 2 >= 0  ⟺  x >= -2/3  ⟺  x >= 0  (over ℤ)."""
    vs = {k: v for k, v in c.items() if k != CONST and v != 0}
    k = c.get(CONST, 0)
    if not vs:
        return k >= 0
    g = 0
    for v in vs.values():
        g = math.gcd(g, abs(v))
    out = {var: v // g for var, v in vs.items()}
    out[CONST] = _floor_div(k, g)
    return out


def _floor_div(a: int, b: int) -> int:
    return a // b          # Python's // already floors toward -inf


def _scale(c: Lin, k: int) -> Lin:
    return {var: v * k for var, v in c.items()}


def _add(a: Lin, b: Lin) -> Lin:
    out = dict(a)
    for var, v in b.items():
        out[var] = out.get(var, 0) + v
    return {var: v for var, v in out.items() if v != 0 or var == CONST}


def _substitute(c: Lin, x: str, expr: Lin) -> Lin:
    """Replace variable x by the linear expression expr."""
    if x not in c or c[x] == 0:
        return c
    coef = c[x]
    rest = {var: v for var, v in c.items() if var != x}
    return _add(rest, _scale(expr, coef))


def _mod_hat(a: int, m: int) -> int:
    """Pugh's symmetric modulus: a - m·floor(a/m + 1/2), the residue in (-m/2, m/2]."""
    return a - m * _floor_div(2 * a + m, 2 * m)


def omega(eqs: list[Lin], ineqs: list[Lin], depth: int = 0) -> bool:
    """Is this conjunction of linear constraints satisfiable over the INTEGERS?"""
    if depth > MAX_OMEGA:
        raise Budget("omega: splinter budget exhausted")

    # THE SIZE OF THE SYSTEM IS ITSELF A BUDGET, and it is the one that was missing.
    # Fourier–Motzkin pairs every lower bound with every upper bound, so eliminating one
    # variable takes n rows to n²/4 — and the elimination recurses.  Bounding the NUMBER
    # of `omega` calls (which the purse does) therefore bounds nothing at all: a single
    # call on a wide-but-trivial predicate (`v + 0 >= 0 and v + 1 >= 1 and …`) grinds for
    # minutes inside ONE invocation.  The whole of 07's corpus and the whole `prove` suite
    # peak at EIGHT rows here, so a fence at 256 is thirty times the largest honest system
    # anyone has written, and it turns the blow-up into an honest "cannot prove".
    if len(eqs) + len(ineqs) > MAX_LINEAR:
        raise Budget("omega: linear system too large")

    eqs   = [dict(e) for e in eqs]
    ineqs = [dict(i) for i in ineqs]
    sigma = 0

    # -- §3.1 Eliminate the equalities --
    while True:
        norm_eqs: list[Lin] = []
        for e in eqs:
            r = _norm_eq(e)
            if r is False:
                return False
            if r is True:
                continue
            norm_eqs.append(r)              # type: ignore[arg-type]
        eqs = norm_eqs

        norm_ins: list[Lin] = []
        for i in ineqs:
            r = _norm_ineq(i)
            if r is False:
                return False
            if r is True:
                continue
            norm_ins.append(r)              # type: ignore[arg-type]
        ineqs = norm_ins

        if not eqs:
            break

        # Pick the equality holding the coefficient of smallest magnitude.
        best_e, best_x, best_a = None, None, None
        for e in eqs:
            for x, a in e.items():
                if x == CONST or a == 0:
                    continue
                if best_a is None or abs(a) < abs(best_a):
                    best_e, best_x, best_a = e, x, a
        assert best_e is not None and best_x is not None and best_a is not None
        e, x, a = best_e, best_x, best_a

        if abs(a) == 1:
            # Exact: solve for x and substitute it away.
            #   a·x + rest = 0  →  x = -a·rest   (because 1/a = a when a = ±1)
            expr = {var: -a * v for var, v in e.items() if var != x}
            others = [o for o in eqs if o is not e]
            eqs   = [_substitute(o, x, expr) for o in others]
            ineqs = [_substitute(i, x, expr) for i in ineqs]
            continue

        # |a| > 1: Pugh's modulus trick.  Introduce σ with
        #     m·σ = Σ mod_hat(a_i, m)·x_i + mod_hat(c, m),     m = |a| + 1
        # in which x's coefficient is exactly -1, so x can be solved for and
        # substituted away; the original equality survives with strictly smaller
        # coefficients, which is why this terminates.
        if a < 0:
            e = {var: -v for var, v in e.items()}
            a = -a
        m = a + 1
        sigma += 1
        s_var = f"$sigma{depth}_{sigma}"
        expr = {var: _mod_hat(v, m) for var, v in e.items() if var != x}
        expr[s_var] = -m
        expr.setdefault(CONST, 0)
        eqs   = [_substitute(o, x, expr) for o in eqs]
        ineqs = [_substitute(i, x, expr) for i in ineqs]

    # -- §3.2 Eliminate the variables from the inequalities --
    return _omega_ineqs(ineqs, depth)


def _omega_ineqs(ineqs: list[Lin], depth: int) -> bool:
    if depth > MAX_OMEGA:
        raise Budget("omega: shadow budget exhausted")

    work: list[Lin] = []
    for c in ineqs:
        r = _norm_ineq(c)
        if r is False:
            return False
        if r is True:
            continue
        work.append(r)                      # type: ignore[arg-type]

    if not work:
        return True

    variables: set[str] = set()
    for c in work:
        variables |= {k for k in c if k != CONST}
    if not variables:
        return True

    # Eliminate the variable that produces the fewest bound pairs.
    def cost(x: str) -> int:
        lo = sum(1 for c in work if c.get(x, 0) > 0)
        hi = sum(1 for c in work if c.get(x, 0) < 0)
        return lo * hi

    x = min(variables, key=cost)
    lowers = [c for c in work if c.get(x, 0) > 0]     # a·x >= -rest
    uppers = [c for c in work if c.get(x, 0) < 0]     # b·x <=  rest
    rest   = [c for c in work if c.get(x, 0) == 0]

    if not lowers or not uppers:
        # Unbounded on one side: x can always be chosen, so drop it.  Exact.
        return _omega_ineqs(rest, depth + 1)

    real: list[Lin] = []
    dark: list[Lin] = []
    for L in lowers:
        a = L[x]                                   # a > 0
        A = {k: v for k, v in L.items() if k != x}  # L is a·x + A >= 0
        for U in uppers:
            b = -U[x]                              # b > 0
            B = {k: v for k, v in U.items() if k != x}   # U is -b·x + B >= 0
            #   b·(a·x + A) >= 0  and  a·(-b·x + B) >= 0   add:  b·A + a·B >= 0
            comb = _add(_scale(A, b), _scale(B, a))
            real.append(comb)
            dark.append(_add(comb, {CONST: -((a - 1) * (b - 1))}))

    # When some side always has coefficient 1 the two shadows coincide: the
    # elimination is exact and there is nothing to splinter.  Every refinement VC
    # I have seen lands here — but "usually exact" is not a decision procedure,
    # which is why the rest of this function exists.
    exact = (all(abs(c[x]) == 1 for c in lowers)
             or all(abs(c[x]) == 1 for c in uppers))
    if exact:
        return _omega_ineqs(rest + real, depth + 1)

    if not _omega_ineqs(rest + real, depth + 1):
        return False                        # real shadow empty ⇒ no solution at all
    if _omega_ineqs(rest + dark, depth + 1):
        return True                         # dark shadow non-empty ⇒ integer solution

    # -- §3.3 The grey region: splinters --
    # Between the shadows the real relaxation has solutions but they may all be
    # fractional.  Pugh: any integer solution must then sit within a bounded
    # distance of one of the lower bounds, so enumerate those finitely many planes
    # exactly.  This is the step that makes the test complete over ℤ.
    b_max = max(-U[x] for U in uppers)
    for L in lowers:
        a = L[x]
        A = {k: v for k, v in L.items() if k != x}
        limit = (a * b_max - a - b_max) // b_max
        for i in range(0, max(limit, 0) + 1):
            #   a·x = -A + i     i.e.   a·x + A - i = 0
            eq = _add({x: a}, _add(A, {CONST: -i}))
            if omega([eq], work, depth + 1):
                return True
    return False


# -- §3.4 Theory check: congruence closure + Omega, combined --------------------

@dataclass
class Lit:
    """A theory literal: an atom with a polarity."""
    atom: Formula
    pos:  bool


class Theory:
    """Decide a *conjunction* of literals in UF ∪ LIA."""

    def __init__(self, sorts: Sorts) -> None:
        self.sorts = sorts
        # ONE PURSE FOR THE WHOLE QUERY.  A `Theory` is created per `satisfiable()` and
        # dies with it, so this counter bounds everything the query can spend — DPLL
        # nodes, propagation pairs, Omega calls — rather than bounding each of them
        # separately while they call each other in loops.  See `Exhausted`.
        self.work = 0
        # DID WE STOP LOOKING?  Every give-up below resolves towards "consistent", which
        # is sound — but it makes an *unproved* obligation and an *abandoned* one look
        # identical to the caller, and they are not the same sentence.  Record it, so
        # refine.py can say which one happened.
        self.gave_up = False

    def _spend(self, n: int = 1) -> None:
        self.work += n
        if self.work > MAX_WORK:
            raise Exhausted("theory: work budget exhausted")

    def consistent(self, lits: list[Lit]) -> bool:
        # Every DPLL node lands here, so spending at least once per call is what makes
        # the purse bound the boolean search as well as the arithmetic.
        self._spend(1 + len(lits))
        cc = Congruence()

        eq_pairs:  list[tuple[Term, Term]] = []
        neq_pairs: list[tuple[Term, Term]] = []
        arith:     list[tuple[str, Term, Term, bool]] = []   # (op, l, r, pos)

        for lit in lits:
            match lit.atom:
                case Cmp(op="==", left=l, right=r):
                    (eq_pairs if lit.pos else neq_pairs).append((l, r))
                    cc.add(l); cc.add(r)
                case Cmp(op="/=", left=l, right=r):
                    # `/=` is the `==` atom wearing the other polarity.  It is not
                    # a comparison — it must never reach the arithmetic branch,
                    # which only knows the ordering relations.
                    (neq_pairs if lit.pos else eq_pairs).append((l, r))
                    cc.add(l); cc.add(r)
                case Cmp(op=op, left=l, right=r):
                    arith.append((op, l, r, lit.pos))
                    cc.add(l); cc.add(r)
                case Atom(term=t):
                    # A Bool-sorted application used as a proposition: `sorted(xs)`.
                    # It is bridged to the term equality `t == true` (or `== false`),
                    # which is what lets congruence carry it — `sorted(xs)` and
                    # `sorted(ys)` share a truth value exactly when `xs == ys`, the same
                    # way `len(xs)` and `len(ys)` share a value.  The BoolLit is added to
                    # the closure HERE, not merely appended to eq_pairs, so that it is in
                    # `cc.terms` before the distinct-literals pass below: without it
                    # `true` and `false` are never asserted distinct, and a congruence
                    # that collapses `sorted(xs)==false` into `sorted(ys)==true` goes
                    # undetected.  The Int measures never needed this — their result is a
                    # term in an `==`, so its value literal is added by the Cmp branch —
                    # which is why the earlier Int-measure support could leave the solver untouched and the Bool-measure support cannot.
                    cc.add(t)
                    cc.add(BoolLit(lit.pos))
                    eq_pairs.append((t, BoolLit(lit.pos)))
                case Top():
                    if not lit.pos:
                        return False
                case Bot():
                    if lit.pos:
                        return False
                case _:
                    raise PredError(f"not a theory atom: {lit.atom!r}")

        # Distinct literals are distinct values: the solver must know 3 /= 4 and
        # true /= false, or `x == 3 and x == 4` looks satisfiable.
        lits_seen = [t for t in cc.terms if isinstance(t, (Num, BoolLit))]
        for i, a in enumerate(lits_seen):
            for b in lits_seen[i + 1:]:
                if type(a) is type(b) and a.value != b.value:
                    neq_pairs.append((a, b))

        for a, b in eq_pairs:
            cc.merge(a, b)

        # Nelson–Oppen, in the small: saturate congruence, project into the linear
        # system, and feed any equality the arithmetic *forces* back to congruence.
        # Iterate to fixpoint (each round strictly merges classes, so it ends).
        for _ in range(len(cc.terms) + 1):
            self._spend(len(cc.terms))
            cc.saturate()

            for a, b in neq_pairs:
                if cc.find(a) == cc.find(b):
                    return False            # a disequality collapsed — inconsistent

            eqs, ineqs, diseqs = self._project(cc, eq_pairs, neq_pairs, arith)
            if not self._lia(eqs, ineqs, diseqs):
                return False

            merged = self._propagate(cc, eqs, ineqs, diseqs)
            if not merged:
                return True

        return True

    # Project the literals into the linear system.  Every int-sorted term that
    # arithmetic cannot decompose (a variable, an application) becomes one column,
    # keyed by its *congruence class* — so `len(xs)` and `len(ys)` share a column
    # exactly when cc has proved `xs == ys`.  That is the whole CC → LIA channel.
    def _project(
        self,
        cc: Congruence,
        eq_pairs:  list[tuple[Term, Term]],
        neq_pairs: list[tuple[Term, Term]],
        arith:     list[tuple[str, Term, Term, bool]],
    ) -> tuple[list[Lin], list[Lin], list[tuple[Lin, Lin]]]:
        eqs:    list[Lin] = []
        ineqs:  list[Lin] = []
        diseqs: list[tuple[Lin, Lin]] = []

        def lin(t: Term) -> Lin:
            match t:
                case Num(value=n):
                    return {CONST: n}
                case Neg(term=x):
                    return _scale(lin(x), -1)
                case Arith(op="+", left=l, right=r):
                    return _add(lin(l), lin(r))
                case Arith(op="-", left=l, right=r):
                    return _add(lin(l), _scale(lin(r), -1))
                case Arith(op="*", left=Num(value=k), right=r):
                    return _scale(lin(r), k)
                case Arith(op="*", left=l, right=Num(value=k)):
                    return _scale(lin(l), k)
                case _:
                    # An opaque int term: one column, named by its class.
                    return {self._column(cc, t): 1}

        def is_int(t: Term) -> bool:
            return self.sorts.of(t) == INT

        for a, b in eq_pairs:
            if is_int(a) and is_int(b):
                eqs.append(_add(lin(a), _scale(lin(b), -1)))
        for a, b in neq_pairs:
            if is_int(a) and is_int(b):
                # A disequality costs an exponential: `_lia` case-splits every one of
                # them into `<` or `>`.  So do not pay for the ones arithmetic can
                # settle by looking at them.  `3 /= 4` is GROUND — its two sides have
                # no variables — and the distinctness axioms above generate one of
                # these for EVERY PAIR of integer literals in the query, so a formula
                # mentioning seven constants was arriving here with twenty-one
                # disequalities and asking for 2^21 calls to Omega.  That is the
                # difference between a solver and a hang.
                la, lb = lin(a), lin(b)
                d = _add(la, _scale(lb, -1))
                if not any(k != CONST and v for k, v in d.items()):
                    if d.get(CONST, 0) == 0:
                        # Ground and EQUAL, but asserted distinct: contradiction.
                        eqs.append({CONST: 1})
                    # Ground and distinct: true, and nothing to split on.
                    continue
                diseqs.append((la, lb))
        for op, l, r, pos in arith:
            if not (is_int(l) and is_int(r)):
                raise PredError(f"comparison on non-integer terms: {pred.show_term(l)} {op} {pred.show_term(r)}")
            d = _add(lin(l), _scale(lin(r), -1))       # d = l - r
            # Over ℤ, the strict forms tighten by one — this is where `x < n` and
            # `x <= n - 1` become the same fact, which is most of what bounds
            # checking needs.
            match (op, pos):
                case ("<=", True):    ineqs.append(_scale(d, -1))                  # r - l   >= 0
                case ("<=", False):   ineqs.append(_add(d, {CONST: -1}))           # l - r - 1 >= 0
                case ("<", True):     ineqs.append(_add(_scale(d, -1), {CONST: -1}))  # r - l - 1 >= 0
                case ("<", False):    ineqs.append(d)                              # l - r   >= 0
                case (">=", True):    ineqs.append(d)
                case (">=", False):   ineqs.append(_add(_scale(d, -1), {CONST: -1}))
                case (">", True):     ineqs.append(_add(d, {CONST: -1}))
                case (">", False):    ineqs.append(_scale(d, -1))
                case _:
                    raise PredError(f"unknown comparison: {op!r}")
        return eqs, ineqs, diseqs

    def _column(self, cc: Congruence, t: Term) -> str:
        cc.add(t)
        return f"$c{cc.pos[cc.find(t)]}"

    def _lia(
        self, eqs: list[Lin], ineqs: list[Lin], diseqs: list[tuple[Lin, Lin]]
    ) -> bool:
        """Omega, plus a case split per disequality: a /= b is a < b or a > b.

        The split is 2^k, so it is fenced twice — on the number of disequalities,
        and on the total number of Omega calls.  Both fences give up towards
        `True` (see `Budget`).  Before the fuzzer, neither existed, and a formula
        naming a dozen integer constants would sit here for the rest of the day.
        """
        if len(diseqs) > MAX_DISEQ:
            self.gave_up = True
            return True

        budget = MAX_SPLITS

        def go(k: int, extra: list[Lin]) -> bool:
            nonlocal budget
            if k == len(diseqs):
                budget -= 1
                if budget < 0:
                    raise Budget("lia: case-split budget exhausted")
                self._spend(1 + len(eqs) + len(ineqs) + len(extra))
                return omega(eqs, ineqs + extra)
            a, b = diseqs[k]
            d = _add(a, _scale(b, -1))
            lo = _add(d, {CONST: -1})                   # a - b - 1 >= 0   (a > b)
            hi = _add(_scale(d, -1), {CONST: -1})       # b - a - 1 >= 0   (a < b)
            return go(k + 1, extra + [lo]) or go(k + 1, extra + [hi])

        try:
            return go(0, [])
        except Exhausted:
            # NOT ours to swallow.  Giving up locally towards `True` is right when THIS
            # split is too big; it is wrong when the whole query is out of budget, because
            # our callers (`consistent`'s fixpoint, `_propagate`'s quadratic sweep, DPLL's
            # search) would simply carry on calling us.  The purse is empty: leave.
            raise
        except Budget:
            self.gave_up = True
            return True

    def _propagate(
        self,
        cc: Congruence,
        eqs: list[Lin],
        ineqs: list[Lin],
        diseqs: list[tuple[Lin, Lin]],
    ) -> bool:
        """Nelson–Oppen, the other direction: if arithmetic *forces* two shared
        terms equal, congruence must hear about it — otherwise `f(x)` and `f(y)`
        stay apart when `x <= y and y <= x` already pinned them together."""
        shared = [t for t in cc.terms
                  if self.sorts.of(t) == INT and isinstance(t, (Var, App))]
        reps: dict[Term, Term] = {}
        for t in shared:
            reps.setdefault(cc.find(t), t)
        classes = list(reps.values())

        merged = False
        for i, a in enumerate(classes):
            for b in classes[i + 1:]:
                if cc.find(a) == cc.find(b):
                    continue
                self._spend(1)      # quadratically many pairs, two `_lia` calls each
                ka, kb = self._column(cc, a), self._column(cc, b)
                d = {ka: 1, kb: -1, CONST: 0}
                # a /= b is impossible ⇒ a = b is entailed.
                lo = _add(d, {CONST: -1})
                hi = _add(_scale(d, -1), {CONST: -1})
                if not self._lia(eqs, ineqs + [lo], diseqs) and \
                   not self._lia(eqs, ineqs + [hi], diseqs):
                    cc.union(a, b)
                    merged = True
        return merged


# -- §4. DPLL(T) ----------------------------------------------------------------

def nnf(f: Formula, pos: bool = True) -> Formula:
    """Negation normal form: push `not` down to the atoms, drop `=>`."""
    match f:
        case Top():
            return Top() if pos else Bot()
        case Bot():
            return Bot() if pos else Top()
        case Not(f=g):
            return nnf(g, not pos)
        case And(left=l, right=r):
            return (And(nnf(l, True), nnf(r, True)) if pos
                    else Or(nnf(l, False), nnf(r, False)))
        case Or(left=l, right=r):
            return (Or(nnf(l, True), nnf(r, True)) if pos
                    else And(nnf(l, False), nnf(r, False)))
        case Implies(left=l, right=r):
            return (Or(nnf(l, False), nnf(r, True)) if pos
                    else And(nnf(l, True), nnf(r, False)))
        case Cmp() | Atom():
            return f if pos else Not(f)
    raise PredError(f"cannot normalise: {f!r}")


Clause = frozenset[tuple[Formula, bool]]     # a disjunction of literals


def cnf(f: Formula) -> list[Clause] | None:
    """Conjunctive normal form by distribution.  None = gave up (too large).

    Distribution can blow up in general; refinement VCs are small, and the budget
    is here to turn a blow-up into an honest "cannot decide" rather than a hang.
    """
    match f:
        case Top():
            return []
        case Bot():
            return [frozenset()]             # the empty clause: unsatisfiable
        case Cmp() | Atom():
            return [frozenset({(f, True)})]
        case Not(f=g) if isinstance(g, (Cmp, Atom)):
            return [frozenset({(g, False)})]
        case And(left=l, right=r):
            a, b = cnf(l), cnf(r)
            if a is None or b is None:
                return None
            out = a + b
            return None if len(out) > MAX_CLAUSES else out
        case Or(left=l, right=r):
            a, b = cnf(l), cnf(r)
            if a is None or b is None:
                return None
            if len(a) * len(b) > MAX_CLAUSES:
                return None
            return [x | y for x in a for y in b]
    raise PredError(f"not in NNF: {f!r}")


def _dpll(clauses: list[Clause], assign: dict[Formula, bool], theory: Theory) -> bool:
    """Satisfiable?  Unit-propagate, decide, and let the theory veto each model."""
    clauses = list(clauses)

    # Unit propagation.
    changed = True
    while changed:
        changed = False
        simplified: list[Clause] = []
        for c in clauses:
            lits = []
            sat_clause = False
            for (atom, pol) in c:
                if atom in assign:
                    if assign[atom] == pol:
                        sat_clause = True
                        break
                else:
                    lits.append((atom, pol))
            if sat_clause:
                continue
            if not lits:
                return False                 # conflict
            simplified.append(frozenset(lits))
        clauses = simplified

        for c in clauses:
            if len(c) == 1:
                (atom, pol), = tuple(c)
                assign[atom] = pol
                changed = True
                break

    if not _theory_ok(assign, theory):
        return False

    if not clauses:
        return True                          # a full, theory-consistent model

    # Decide.
    atom, _ = next(iter(next(iter(clauses))))
    for pol in (True, False):
        if _dpll(clauses, {**assign, atom: pol}, theory):
            return True
    return False


def _theory_ok(assign: dict[Formula, bool], theory: Theory) -> bool:
    return theory.consistent([Lit(a, p) for a, p in assign.items()])


def _satisfiable(fs: list[Formula], sorts: Sorts) -> tuple[bool, bool]:
    """(satisfiable?, did we give up?) — the honest pair, for callers who care.

    Both give-up paths answer `True` (satisfiable), which is the sound direction; the
    second element is there so that the answer's PROVENANCE survives.  "I found a model"
    and "I stopped looking, so assume there is one" are the same bit and different facts.
    """
    f = pred.conj(fs)
    clauses = cnf(nnf(f))
    if clauses is None:
        return True, True                    # cannot decide ⇒ assume satisfiable
    theory = Theory(sorts)
    try:
        return _dpll(clauses, {}, theory), theory.gave_up
    except (Budget, RecursionError):
        return True, True                    # ditto, and for the same reason


def satisfiable(fs: list[Formula], sorts: Sorts) -> bool:
    """Is the conjunction of fs satisfiable in UF ∪ LIA?"""
    return _satisfiable(fs, sorts)[0]


def decide(hyps: list[Formula], goal: Formula, sorts: Sorts) -> tuple[bool, bool]:
    """(proved?, gave up?).  `valid` is this, with the second answer thrown away."""
    sat, gave_up = _satisfiable(hyps + [Not(goal)], sorts)
    return (not sat), gave_up


def valid(hyps: list[Formula], goal: Formula, sorts: Sorts) -> bool:
    """Does `goal` follow from `hyps`?

    The one question the refinement checker ever asks.  Answered the standard way:
    the implication is valid exactly when its negation is unsatisfiable.

    A `False` here means "not proved", which is not quite "false" — the solver is
    sound but the *abstraction* into it is deliberately lossy (an unmodelled `f`
    really is unmodelled).  refine.py must therefore report a failed VC as
    "cannot prove", never as "your program is wrong".
    """
    return decide(hyps, goal, sorts)[0]


# -- CLI: a self-check of the decision procedure --------------------------------

if __name__ == "__main__":
    import sys

    x, y, n = Var("x"), Var("y"), Var("n")
    S = Sorts(var={"x": INT, "y": INT, "n": INT, "xs": OTHER, "ys": OTHER, "b": BOOL},
              fn={"len": INT})

    def le(a, b): return Cmp("<=", a, b)
    def lt(a, b): return Cmp("<", a, b)
    def eq(a, b): return Cmp("==", a, b)

    cases: list[tuple[str, bool, list[Formula], Formula]] = [
        # (name, expected, hypotheses, goal)
        ("x>=0 ⊢ x+1>0",        True,  [le(Num(0), x)], lt(Num(0), Arith("+", x, Num(1)))),
        ("x>0 ⊢ x/=0",          True,  [lt(Num(0), x)], Cmp("/=", x, Num(0))),
        ("⊬ x>=0",              False, [], le(Num(0), x)),
        ("transitivity",        True,  [le(x, y), le(y, n)], le(x, n)),
        ("bounds",              True,  [le(Num(0), x), lt(x, n), eq(y, x)], lt(y, n)),
        ("2x=1 unsat",          True,  [eq(Arith("*", Num(2), x), Num(1))], Bot()),
        ("congruence",          True,  [eq(Var("xs"), Var("ys"))],
                                       eq(App("len", (Var("xs"),)), App("len", (Var("ys"),)))),
        ("uf is opaque",        False, [], lt(Num(0), App("len", (Var("xs"),)))),
        ("uf + arith",          True,  [le(Num(0), x), lt(x, App("len", (Var("xs"),)))],
                                       lt(Num(0), App("len", (Var("xs"),)))),
        ("case split",          True,  [Or(eq(x, Num(1)), eq(x, Num(2)))], le(Num(1), x)),
        ("no-split counterex",  False, [Or(eq(x, Num(1)), eq(x, Num(2)))], eq(x, Num(1))),
        ("dark shadow",         True,  [le(Arith("*", Num(3), x), Num(2)),
                                        le(Num(2), Arith("*", Num(3), x))], Bot()),
        ("bool atom",           True,  [Atom(Var("b"))], Atom(Var("b"))),
        ("NO propagation",      True,  [le(x, y), le(y, x)],
                                       eq(App("len", (x,)), App("len", (y,)))),
    ]

    ok = fail = 0
    for name, expected, hyps, goal in cases:
        got = valid(hyps, goal, S)
        mark = "ok  " if got == expected else "FAIL"
        if got == expected:
            ok += 1
        else:
            fail += 1
        print(f"{mark} {name:<22} expected={str(expected):<5} got={got}")

    # The grey region (§3.3).  Both systems are built so that eliminating x is
    # INEXACT — every bound on x has |coefficient| > 1 — with a non-empty real
    # shadow and an empty dark one.  Neither can be decided by the shadows; only
    # splintering answers them, and it must answer both ways.  Without these two
    # rows the completeness path is dead code that no test would notice breaking.
    grey: list[tuple[str, bool, list[Lin]]] = [
        ("grey: SAT via splinter",   True,  [{"x": 2, "y": -1, CONST: 0},     # 2x >= y
                                             {"x": -3, "y": 1, CONST: 2},     # 3x <= y + 2
                                             {"y": 1, CONST: -3}]),           # y >= 3   → x=2,y=4
        ("grey: UNSAT via splinter", False, [{"x": 3, "y": -2, CONST: -2},    # 3x >= 2y + 2
                                             {"x": -2, "y": 3, CONST: 0},     # 2x <= 3y
                                             {"y": -1, CONST: 1}]),           # y <= 1   → no point
    ]
    for name, expected, system in grey:
        got = omega([], [dict(c) for c in system])
        mark = "ok  " if got == expected else "FAIL"
        ok, fail = (ok + 1, fail) if got == expected else (ok, fail + 1)
        print(f"{mark} {name:<22} expected={str(expected):<5} got={got}")

    print(f"\n{ok} ok / {fail} fail")
    sys.exit(1 if fail else 0)
