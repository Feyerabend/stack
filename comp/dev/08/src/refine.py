"""
The refinement checker: refinement types, and the verification conditions they
generate (PROVE.md V1 steps 1–2).

It runs AFTER Hindley–Milner, never instead of it.  `infer.py` has already decided
that a program is well-typed and has erased every refinement doing so (see the one
`STRefine` case in `syntype_to_mono`); this pass walks the *syntactic* tree again —
the only tree that still holds the predicates — and asks a second, narrower
question: does each value flowing into each annotated position satisfy the
predicate written there?  Every "yes" is discharged by solver.py.  That layering is
the whole reason refinements are cheap to add: the HM skeleton is reused, not
rebuilt.

--------------------------------------------------------------------------------
THE AFFINE × REFINEMENT RULE  (PROVE.md §7 — settled here, before the VC generator
hard-codes an answer, which is what the plan asked for)

    Naming an affine binding in a predicate is a MENTION, not a USE.
    Predicates are use-neutral: they never consume.

So this is legal, and `xs` is still live afterwards:

    fn head(xs: List(Int), i: {v: Int | v >= 0 and v < len(xs)}) : Int = ...

even though `List(Int)` may be a non-Copy type and `xs` is named twice — once as a
parameter, once inside `i`'s predicate.

The rule is *enforced by construction* rather than by a check: refinements erase in
`syntype_to_mono` before `infer` ever traverses them, so `tracked[xs]` is never
incremented by a predicate.  There is no code that "allows" the mention; there is
simply no code that could count it.

Why it is SOUND — and this is the part that is specific to Lark, and is the
book-grade finding the plan predicted:

    Affinity in Lark restricts USE, not TRUTH.  Lark is pure: consuming a value
    moves it, it does not mutate it.  A value that was `sorted` before it was
    consumed is still `sorted` — there is no later state in which the predicate
    could have become false, because there is no later state at all.  So a fact
    proved about an affine binding stays valid for the rest of the scope, and the
    checker may keep using it in the logic long after the program has given the
    value away.

    In a language with mutation this is FALSE and the rule would be unsound: there,
    a moved-out value can be changed behind your back, and a predicate mentioning it
    would be a claim about a value that no longer exists.  The permission we grant
    ourselves here is paid for by purity, and by nothing else.

The corollary is a restriction, and it is what keeps the permission honest: a
predicate may only *apply* functions, never *evaluate* Lark code.  Every function
mentioned in a predicate is uninterpreted (§ "Predicates" below) — so a predicate
cannot run an affine value through anything, cannot force it, and cannot observe it.
It can only name it.  Mention, not use, all the way down.
--------------------------------------------------------------------------------

WHAT V1 DOES NOT DO (say it plainly — PROVE §7's "don't oversell V1 as V3"):

  - No refinement INFERENCE.  A position with no annotation gets `{v : b | true}`,
    which proves nothing and demands nothing.  Unannotated code therefore produces
    unproved obligations wherever a builtin has a precondition — that is not the
    checker failing, it is the checker declining to guess.  Inference is V2.
  - No MEASURES.  `len(xs)` is an uninterpreted symbol: the checker knows
    `xs == ys ⇒ len(xs) == len(ys)` and nothing else.  It does not know that `len`
    is non-negative, nor what `Cons` does to it.  That is V2, and until then a
    predicate over `len` can only relate lengths to each other.
  - No proof of the CHECKER.  V1's guarantee is "checked by a trusted tool", not
    "checked by a proven tool".  Only V3 (soundness in lcore) upgrades that.
"""

from __future__ import annotations
import sys, os
from dataclasses import dataclass, field
from typing import Union

sys.path.insert(0, os.path.dirname(__file__))

import pred
import solver
from pred import (
    Term, Num, BoolLit, Var as PVarT, Neg, Arith, App,
    Formula, Top, Bot, Cmp, Atom, Not, And, Or, Implies,
    PredError,
)
from solver import Sorts, INT, BOOL, OTHER

# THE FLOAT SORT, and it is the checker's, not the solver's.
#
# `OTHER` means "a value the logic may NAME but not open": it may be compared for
# equality and passed to an uninterpreted symbol, and congruence closure decides the
# rest.  That permission is safe for a String, a Buf, a List — and it is NOT SAFE FOR
# A FLOAT, because the logic's `==` is an equivalence relation and IEEE-754's is not:
#
#     x == x        is valid in the logic.  It is FALSE at run time when x is NaN,
#                   and `0.0 / 0.0` and `float_sqrt(-1.0)` both produce one.
#     0.0 == -0.0   is TRUE at run time, and they are DIFFERENT VALUES — so congruence
#                   would conclude f(0.0) == f(-0.0) for a function that can tell them
#                   apart (1.0 / x is +inf for one and -inf for the other).
#
# Reflexivity is wrong in one direction and substitutivity in the other, which is the
# whole of what OTHER hands out.  So a Float gets a sort of its own — one the solver
# has never heard of and will never see, because no term is ever built at it.  The
# guard is `_sort_of_term` + `term_opt`, and everything downstream inherits it: a
# constructor with a Float field is unnameable because its argument is, a predicate
# over Floats is a refinement ERROR rather than a silent lie, and every path ends in
# "cannot prove" — the sound direction, as V1′ requires.
FLOAT = "float"

import lexer as _lexer
import parser as _parser
import infer as _infer
import ty
from ty import Mono, TCon, TFn, Scheme
from tree import (
    Program, FnDecl, LetDecl, TypeDecl, TraitDecl, ImplDecl, MeasureDecl,
    TraitMethod, ImplMethod,
    Expr, Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
    LetExpr, IfExpr, MatchExpr, Lambda,
    Pat, PWild, PVar, PLit, PCon, PTuple,
    Type, TName, TApply, TFn as STFn, TUnit, TTuple, TRefine,
    Variant,
)
from typed_tree import TImplDecl


class RefineError(Exception):
    """A refinement that is malformed — not one that is unproved.

    The distinction matters: an unproved obligation is a *result* (reported, and
    the suite records it), while a malformed predicate is a *bug in the source*
    (raised, and checking stops)."""


# -- Refinement types -----------------------------------------------------------

@dataclass(frozen=True)
class RBase:
    """{ v : b | p } — a base type carrying a predicate.

    b is `Int`, `Bool`, or — since V2.0 — the name of any type the logic cannot
    look inside (an ADT, a String).  The last case is worth stating plainly, because
    it looks like a bigger extension than it is: the value binder of `{v : Buf |
    size(v) == size(b)}` is sorted OTHER, so `_int_term`'s guard keeps it out of
    arithmetic and ordering, and the ONLY things a predicate can do with it are the
    two the solver already decides at any sort — equality, and application of an
    uninterpreted symbol.  Congruence closure does not care what a Buf is.  No new
    theory, no new sort machinery; just permission to name a value we cannot open."""
    base: str
    vv:   str
    p:    Formula
    # The HM monotype this RType erases, carried for ONE purpose: when an ADT value
    # is destructured, `_bind_pattern` unifies the pattern against this to pin a
    # POLYMORPHIC field's sort (`Cons(x, _)` over `List(Int)` gives `x : Int`, not
    # OTHER).  compare=False so it is pure metadata — it never changes RBase equality
    # or hashing, and dropping it (subst, most rebuilds) is always the SOUND fallback:
    # a missing monotype means the field stays OTHER, exactly as before V2.4b.
    mono: "Mono | None" = field(default=None, compare=False)

@dataclass(frozen=True)
class RFun:
    """(x: S, ...) -> T — a DEPENDENT function type: T and later parameters may
    mention earlier parameter names.  That dependency is the only reason a
    contract like `i < len(xs)` can be written at all."""
    params: tuple[tuple[str, "RType"], ...]
    ret:    "RType"

@dataclass(frozen=True)
class RTuple:
    """(S, T, ...) — a product, refined componentwise.  PROVE.md V2.0.

    The components are POSITIONAL, and that is a deliberate limit: a component's
    predicate may mention any binder in scope *outside* the tuple (the parameter it
    was computed from, typically) but cannot mention a sibling component, because
    the surface syntax gives siblings no names to mention.  Nothing in Lark needs
    that yet — the borrow idiom relates both components to the *argument*, not to
    each other — and inventing names for them would be surface syntax invented for
    a use that does not exist."""
    comps: tuple["RType", ...]

@dataclass(frozen=True)
class ROpaque:
    """Everything the logic still does not model: Float, functions-as-values, and
    any ADT nobody wrote a refinement for.

    Opaque is not "ignored" — an opaque value still flows, and a VC that needs a
    fact about it simply will not be provable.  Sound, and visibly incomplete."""
    sort: str = OTHER

RType = Union[RBase, RFun, RTuple, ROpaque]


def rtrue(base: str) -> RBase:
    return RBase(base, "v", Top())


def _rtype_at_sort(s: str) -> RType:
    """A type carrying no information but the sort — what a skolem needs and all it
    needs: the logic must know whether it may do arithmetic on the thing it just
    invented a name for."""
    if s == INT:
        return rtrue("Int")
    if s == BOOL:
        return rtrue("Bool")
    return ROpaque()


def sort_of_rtype(r: RType) -> str:
    match r:
        case RBase(base="Int"):
            return INT
        case RBase(base="Bool"):
            return BOOL
        case RBase(base="Float"):
            return FLOAT
        case ROpaque(sort=s):
            return s
    return OTHER


def rtype_of_mono(m: Mono, adts: set[str] | None = None) -> RType:
    """The trivial refinement of an HM type: the type, refined by `true`.

    `adts` is the set of algebraic data types the program DECLARES, and passing it is
    what V2.2 needs: a value of a declared ADT gets `{v : List | true}` rather than
    ROpaque, so that `synth` will *selfify* it — `{v | v == r}` — and the value stays
    connected to its name.  Without that, `| Cons(_, r) => r` computes a list the
    logic knows the length of and then returns it as a value the logic has never
    heard of, and the fact is lost on the way out of the function.

    It costs nothing, for the reason V2.0 already established: the binder is sorted
    OTHER, so `_int_term` keeps it out of arithmetic, and the only operations left are
    equality and uninterpreted application — the two the solver decides at any sort.
    Naming is not opening.

    String and IO stay OPAQUE: they have no constructors, so no measure can ever say
    anything about them, and the logic is *linear integer* arithmetic — there is no
    sound way to pretend a String is an Int, and pretending is how verifiers end up
    proving things that are not true.

    A Float is opaque too, and then one step further: it is sorted FLOAT, which is
    UNSPEAKABLE — not even equality survives, for the reason given where FLOAT is
    defined.  Opaque says "you may name me but not open me"; Float may not even be
    named.
    """
    match m:
        case TCon(name="Int"):
            return rtrue("Int")
        case TCon(name="Bool"):
            return rtrue("Bool")
        case TCon(name="Float"):
            return ROpaque(sort=FLOAT)
        case TCon(name=n) if adts is not None and n in adts:
            return RBase(n, "v", Top(), mono=m)
        case ty.TApp(head=h) if adts is not None and h in adts:
            return RBase(h, "v", Top(), mono=m)
        case TFn():
            params: list[tuple[str, RType]] = []
            i = 0
            cur: Mono = m
            while isinstance(cur, TFn):
                params.append((f"$p{i}", rtype_of_mono(cur.param, adts)))
                cur = cur.result
                i += 1
            return RFun(tuple(params), rtype_of_mono(cur, adts))
    return ROpaque()


def result_mono(m: Mono) -> Mono:
    while isinstance(m, TFn):
        m = m.result
    return m


def _tvar_ids(m: Mono) -> set[int]:
    """Every type variable a type mentions — so a fresh supply can start above them."""
    match m:
        case ty.TVar(id=i):
            return {i}
        case ty.TApp(args=args):
            return set().union(*(_tvar_ids(a) for a in args)) if args else set()
        case TFn(param=p, result=r):
            return _tvar_ids(p) | _tvar_ids(r)
        case ty.TTup(elems=es):
            return set().union(*(_tvar_ids(e) for e in es)) if es else set()
    return set()


def sort_of_mono(m: Mono) -> str:
    match m:
        case TCon(name="Int"):
            return INT
        case TCon(name="Bool"):
            return BOOL
        case TCon(name="Float"):
            return FLOAT
    return OTHER


# -- Measures (PROVE.md V2.1) ---------------------------------------------------
#
# A measure is a GHOST function from a data structure into the logic: `len`, `size`,
# `sorted`.  Elaborated, it is a set of EQUATIONS — one per constructor —
#
#     len(Nil)          == 0
#     len(Cons(x, rest)) == 1 + len(rest)
#
# and that is the whole point: an equation is something the solver can use, where a
# Lark function body is not.  V2.1 builds and *checks* these; V2.2 is what hands them
# to the solver (at the terms a program actually mentions, never as an axiom schema).
#
# THE EQUATIONS ARE AXIOMS, AND THAT IS WHY THE CHECKING IS NOT OPTIONAL.  A
# non-terminating *program* function is harmless — it returns nothing, so its contract
# is vacuously kept, and V1 already leans on exactly that.  A non-terminating *measure*
# is fatal: `len(xs) == 1 + len(xs)` is an inconsistent axiom set, and from an
# inconsistency the checker proves every goal put to it, including the false ones.
# Termination is OPTIONAL for a contract and MANDATORY for a measure — which is the
# one-line reason `_elab_measure` below is as suspicious as it is.

@dataclass(frozen=True)
class Guard:
    """One step of a NESTED match, flattened (PROVE.md V2.4c step 3 Part B).

    A measure may take its argument apart more than once — a BST's `maxv` asks
    whether the right child is a `Leaf` or a `Node` — and each inner `match` on a
    bound field becomes, per inner arm, one of these: the binder `var` (a field bound
    further out) is required to be the constructor `con`, and its own fields are bound
    to `binders` (with `bsorts`).  A single measure arm with a nested match flattens
    into one `MArm` per (outer x inner x ...) path, each carrying the chain of guards
    that names the shape it is the equation for.

    The guards FIRE AT CONCRETE SUBFIELDS: an equation with a guard `r == Node(...)`
    is instantiated only where the term in the `r` position is literally a `Node`
    application — never by e-matching a `r == Node(...)` hypothesis across congruence,
    which would need a quantifier for the inner fields.  Where the subfield is opaque,
    no equation fires, which is the sound silence a flat measure already keeps at an
    opaque argument."""
    var:     str                # a binder bound further out (outer field, or an inner
                                #   field of an earlier guard) — the scrutinee
    con:     str                # the inner constructor this path requires it to be
    binders: tuple[str, ...]    # names bound to the inner constructor's fields
    bsorts:  tuple[str, ...]


@dataclass(frozen=True)
class MArm:
    """One constructor's equation, already in the logic.

    `binders` are the field names the pattern bound ("_" for a field it ignored);
    exactly one of `t` / `f` is set, according to the measure's result sort.

    `bsorts` is what V2.2 needs and V2.1 did not: to instantiate this equation at a
    term the program wrote, each field has to be checked to have the sort the
    measure's own declaration gave it.  A measure over `List(Int)` applied to a
    `List(Bool)` would otherwise substitute a Bool where the arm expects an Int, and
    a verifier that confuses sorts will eventually prove something false.

    `guards` is the flattened chain of a NESTED match (V2.4c step 3 Part B): empty for
    a measure that takes its argument apart exactly once, and one entry per inner arm
    along this path otherwise.  A single outer constructor can now own SEVERAL arms —
    one per inner path — which is why `con` is no longer a key with a single value."""
    con:     str
    binders: tuple[str, ...]
    bsorts:  tuple[str, ...]
    t:       Term | None      # Int-valued measure
    f:       Formula | None   # Bool-valued measure
    guards:  tuple[Guard, ...] = ()


@dataclass(frozen=True)
class Measure:
    """A well-formed measure: what V2.2 will read, and nothing it has to re-check."""
    name:  str
    param: str                            # the structural argument
    tycon: str                            # the ADT it takes apart
    extra: tuple[tuple[str, RType], ...]  # the non-structural parameters (V2.4)
    ret:   RBase                          # base + the declared refinement (V2.3 proves it)
    arms:  tuple[MArm, ...]

    def sort(self) -> str:
        return sort_of_rtype(self.ret)


def _syn_subst(t: Type, sub: dict[str, Type]) -> Type:
    """Instantiate an ADT's type parameters: the payload of `Cons of a, List(a)`
    read through `xs : List(Int)` gives `x : Int`, not `x : a`."""
    match t:
        case TName(name=n):
            return sub.get(n, t)
        case TApply(name=n, args=args):
            return TApply(n, tuple(_syn_subst(a, sub) for a in args))
        case TTuple(elems=es):
            return TTuple(tuple(_syn_subst(e, sub) for e in es))
        case STFn(param=p, result=r):
            return STFn(_syn_subst(p, sub), _syn_subst(r, sub))
    return t


def _rtrue_of_syn(t: Type) -> RType:
    """The trivial refinement of a *syntactic* type — enough to give a binder its
    sort, which is all a measure's arm needs of its fields."""
    b = _refinable_base(t)
    return RBase(b, "v", Top()) if b is not None else ROpaque()


def _measure_calls(e: Expr, names: set[str]) -> list[Apply]:
    """Every application of a declared measure inside an expression.

    The structural check is SYNTACTIC and it is done on the Lark expression, before
    translation, because translation is exactly what loses the distinction: `len(xs)`
    and `len(rest)` are both a perfectly good App to the logic.  The rule that keeps
    the axiom set consistent has to be applied while the difference is still visible.
    """
    out: list[Apply] = []

    def go(x: Expr) -> None:
        match x:
            case Apply(fn=Var(name=n), args=args):
                if n in names:
                    out.append(x)
                for a in args:
                    go(a)
            case Apply(fn=f, args=args):
                go(f)
                for a in args:
                    go(a)
            case BinOp(left=l, right=r):
                go(l); go(r)
            case UnaryOp(operand=x2):
                go(x2)
            case TupleExpr(elems=es):
                for x2 in es:
                    go(x2)
            case LetExpr(value=v, body=b):
                go(v); go(b)
            case IfExpr(cond=c, then_=t2, else_=e2):
                go(c); go(t2); go(e2)
            case MatchExpr(scrutinee=s, arms=arms):
                go(s)
                for _p, b in arms:
                    go(b)
            case Lambda(body=b):
                go(b)
            case _:
                pass

    go(e)
    return out


@dataclass(frozen=True)
class ResultAxiom:
    """What a symbol's result satisfies — and the parameter names its predicate is
    entitled to speak about.

    The names are the whole reason this is a class rather than an `RBase`.  A declared
    result may mention the symbol's own arguments:

        measure len(xs : List(Int)) : {v : Int | v >= 0 and (xs != Nil or v == 0)}

    and `xs` there means *the list this application is about* — nothing else.  Assert
    that refinement at `len(ys)` without substituting, and the formula still says `xs`:
    a name the checker does not own, which is either free (harmless, but a claim
    nobody wrote) or, worse, CAPTURED by whatever the obligation's own scope happens to
    call `xs`.  That is V2.2′(c)/(d) exactly — a symbol is a function, not a name — and
    it is not a hole to leave open a second time.

    So the instantiation is a substitution of the ARGUMENTS for the PARAMETERS, and the
    value binder is substituted last because it SHADOWS: in `measure f(v : …) : {v : Int
    | v >= 0}` the `v` in the predicate is the result, as it is in every refinement.

    `at` returns None when it cannot speak — a wrong arity, which no well-formed program
    produces but which a checker must not guess its way past.  Silence about what you may
    ASSUME is modesty; it is only silence about what you must PROVE that is a lie."""
    params: tuple[str, ...]
    r:      RBase

    def at(self, t: App) -> Formula | None:
        """The fact this axiom states about ONE application.  The single door: the
        induction PROVES `at(m(C(y…)))` and every obligation ASSUMES `at(m(t))`, so the
        statement proved is the statement asserted — by construction, not by care."""
        if len(t.args) != len(self.params):
            return None
        sub: dict[str, Term] = dict(zip(self.params, t.args))
        sub[self.r.vv] = t
        return pred.subst(self.r.p, sub)

    @property
    def trivial(self) -> bool:
        return isinstance(self.r.p, Top)


# -- Verification conditions ----------------------------------------------------

@dataclass
class VC:
    """One obligation: under `hyps`, prove `goal`.  `where_` is what to tell the
    user when it cannot be proved — a VC nobody can read is a VC nobody fixes."""
    where_: str
    hyps:   list[Formula]
    goal:   Formula
    sorts:  Sorts
    # constructor name -> the arms of every measure that has an equation for it.
    # Populated once, in Refiner.run(); the VC carries it because instantiating a
    # measure's equations is a property of the OBLIGATION (which terms does it
    # mention?), not of the program point that raised it.
    cons:   dict[str, tuple[tuple["Measure", MArm], ...]] = field(default_factory=dict)
    # symbol -> the refinement its RESULT satisfies, for the symbols whose result
    # refinement may be asserted HERE.  Also populated in Refiner.run(), and for the
    # same reason it must be: `string_length` names the primitive only in a program
    # that does not define one of its own — and an INDUCTION VC may not assume the
    # very refinement it is proving (see `_prove_measure`).
    results: dict[str, ResultAxiom] = field(default_factory=dict)
    # Is this the induction proof of a measure's own result refinement?  Only run()
    # reads it, to decide which `results` the VC is entitled to.
    ind:    bool = False

    def assumptions(self) -> list[Formula]:
        """The program's own facts, plus the axioms about uninterpreted symbols
        that this obligation happens to mention."""
        fs = self.hyps + [self.goal]
        return self.hyps + result_axioms(fs, self.results, self.sorts) + \
            measure_axioms(fs, self.cons, self.sorts)


# THE ONE THING THE LOGIC KNOWS ABOUT A PRIMITIVE, WRITTEN DOWN WHERE IT CAN BE READ.
#
# `string_length` is an uninterpreted symbol, so nothing in the logic rules out a
# string of length −1, and without this `string_slice(s, 0, string_length(s))` —
# slicing the whole of a string, which cannot fail — is unprovable.  Something has to
# say that a length is not negative.
#
# Until V2.3 that something was a bare set literal (`NONNEG_UF = {"string_length"}`)
# and a hard-coded `>= 0` buried in the axiom walk: a fact the checker knew and could
# not state.  Now it is written in the same language a program writes a contract in —
# `{v : Int | v >= 0}` — and it is asserted by the SAME mechanism that asserts a
# measure's declared result (`result_axioms`).  The difference between `string_length`
# and `len` is now exactly one thing, and it is the thing that matters:
#
#     `len` is PROVED (V2.3, by induction over its arms).
#     `string_length` is ASSUMED — String is primitive, it has no constructors, so
#     there are no arms to induct over and nothing to prove it FROM.
#
# This table is therefore the complete list of what the checker takes on faith about
# the primitives.  It is one line long, and that is the point of having a table: an
# axiom you cannot enumerate is an axiom you cannot audit.
#
# AN AXIOM IS ABOUT A FUNCTION, NOT ABOUT A NAME.  It is true of the *builtin*,
# because the builtin computes a length.  A program is free to declare `fn
# string_length(s : String) : Int = 0 - 4`, which overrides the builtin everywhere —
# including at run time — and asserting the axiom of THAT is a false proof, and it was
# one (`16_axiom`).  So Refiner.__init__ intersects this table with the names the
# program leaves alone.
PRIMITIVE_AXIOMS: dict[str, "ResultAxiom"] = {
    "string_length": ResultAxiom(("s",), RBase("Int", "v", Cmp(">=", PVarT("v"), Num(0)))),
    # `min`/`max` (V2.4c step 1).  Three facts, no more: two ORDERING bounds and the
    # DISJUNCTION that the result IS one of the two arguments.  The disjunction is not
    # decoration — it is the only thing that gives `min(a, b)` a LOWER bound, so it is
    # what proves `min(a, b) > 0` from `a > 0 and b > 0`; the two `<=` facts alone bound
    # it from above and would let the minimum be anything below.  Instantiated at each
    # `min`/`max` application an obligation mentions, never quantified — the same shadow
    # of a `forall` that `string_length` and every measure equation are.  Sound because
    # they are true of the BUILTIN (cek.py returns `a if a <= b else b`); a program that
    # declares its own `min` gets these DROPPED (Refiner.__init__, the `rebound` set),
    # which is `16_axiom`'s rule and the reason an axiom is about a function, not a name.
    "min": ResultAxiom(("a", "b"), RBase("Int", "v",
        And(And(Cmp("<=", PVarT("v"), PVarT("a")),
                Cmp("<=", PVarT("v"), PVarT("b"))),
            Or(Cmp("==", PVarT("v"), PVarT("a")),
               Cmp("==", PVarT("v"), PVarT("b")))))),
    "max": ResultAxiom(("a", "b"), RBase("Int", "v",
        And(And(Cmp(">=", PVarT("v"), PVarT("a")),
                Cmp(">=", PVarT("v"), PVarT("b"))),
            Or(Cmp("==", PVarT("v"), PVarT("a")),
               Cmp("==", PVarT("v"), PVarT("b")))))),
}


_ORDER_OPS = frozenset(("<", "<=", ">", ">="))


def _order_cmps_are_integer(f: Formula, sorts: Sorts) -> bool:
    """Would the solver ACCEPT every order comparison in `f`?

    An order comparison (`<`, `<=`, `>`, `>=`) on a non-integer term is what the
    solver's `arith` bucket RAISES on — it is not a fact it can decide, it is a
    malformed one.  Equalities are exempt: congruence decides `==`/`/=` at any sort.

    A result axiom is instantiated at whatever terms an obligation mentions, and one of
    them may be a skolem for an untranslatable argument, which lands at sort OTHER: the
    `min`/`max` axiom then reads `min($k1, $k2) <= $k1`, an order comparison on OTHER.
    `_instantiate` already declines a measure equation it cannot sort; this is the same
    rule for `result_axioms`, checked against the SAME table the solver will use, so an
    axiom the checker cannot state is dropped here rather than raised there.  Where it
    cannot speak it says nothing — the symbol's result stays opaque, sound and weaker."""
    ok = True

    def walk(g: Formula) -> None:
        nonlocal ok
        match g:
            case Cmp(op=op, left=l, right=r) if op in _ORDER_OPS:
                if sorts.of(l) != INT or sorts.of(r) != INT:
                    ok = False
            case Not(f=h):
                walk(h)
            case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
                walk(l); walk(r)
            case _:
                pass

    walk(f)
    return ok


def result_axioms(fs: list[Formula], results: dict[str, ResultAxiom],
                  sorts: Sorts) -> list[Formula]:
    """For every application `f(t…)` the formulas mention, what f's result satisfies.

    Instantiated at the terms that are there, never quantified — the same discipline
    as `measure_axioms` below, and for the same reason: `forall x. len(x) >= 0` would
    leave QF-UFLIA and take the decision procedure with it.  The quantifier-free
    shadow of that axiom is to assert it once at each application actually written.
    """
    if not results:
        return []
    out: list[Formula] = []
    seen: set[Term] = set()

    def walk_t(t: Term) -> None:
        match t:
            case App(fn=fn, args=args):
                for a in args:
                    walk_t(a)
                ax = results.get(fn)
                if ax is not None and t not in seen:
                    seen.add(t)
                    f = ax.at(t)
                    if f is not None and _order_cmps_are_integer(f, sorts):
                        out.append(f)
            case Neg(term=x):
                walk_t(x)
            case Arith(left=l, right=r2):
                walk_t(l); walk_t(r2)
            case _:
                pass

    def walk_f(f: Formula) -> None:
        match f:
            case Cmp(left=l, right=r):
                walk_t(l); walk_t(r)
            case Atom(term=t):
                walk_t(t)
            case Not(f=g):
                walk_f(g)
            case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
                walk_f(l); walk_f(r)
            case _:
                pass

    for f in fs:
        walk_f(f)
    return out


# -- Measures into the logic (PROVE.md V2.2) ------------------------------------
#
# THE WHOLE RUNG IS THIS: an equation is instantiated at a constructor term the
# obligation MENTIONS, and nowhere else.
#
#     len(Cons(3, Nil)) == 1 + len(Nil)        because the program wrote Cons(3, Nil)
#     len(Nil)          == 0                   because that term is inside the one above
#
# There is no axiom schema, no trigger, no e-matching, and above all no quantifier:
# `forall xs. len(Cons(x, xs)) == 1 + len(xs)` would leave QF-UFLIA and take the
# decision procedure with it.  What we do instead is the quantifier-free shadow of
# that axiom — instantiate it, once, at each term that is actually there.  The set is
# finite, and it closes in a SINGLE pass for a reason worth saying out loud: the
# subterms of a constructor term are constructor terms, and the walk already descends
# into them.  Nothing an equation introduces on its right-hand side is a new
# constructor application — an arm may only recurse on a FIELD, which is a term the
# walk has already seen.  V2.1's structural check, which was there to keep the axioms
# consistent, turns out to be what makes them terminate as well.
#
# That leaves exactly two ways a constructor term can enter a VC, and they are the
# "two hooks" of the plan:
#
#   BUILDING     `Cons(x, xs)` synthesises `{v | v == Cons(x, xs)}` (Refiner.synth).
#   DESTRUCTING  `| Cons(x, rest) =>` assumes `xs == Cons(x, rest)` (_walk_match).
#
# Note what the second one is NOT: it does not assume `len(xs) == 1 + len(rest)`
# directly.  It says the humbler thing — *what the scrutinee is* — and the equation
# follows, because the term `Cons(x, rest)` is now in the hypotheses and the walk
# below instantiates `len` at it, and congruence closure does the last step.  One
# mechanism, fed from two places, rather than two mechanisms that must agree.

def _instantiate(m: "Measure", arm: MArm, target: Term,
                 fields: tuple[Term | None, ...], sorts: Sorts,
                 extras: tuple[Term, ...] = ()) -> Formula | None:
    """`m(target, extras…) == body[fields/binders, extras/params]` — or None, if it
    cannot be stated.

    A measure with EXTRA parameters (V2.4c step 5: `lt(t, b)`) is instantiated with the
    extras carried alongside the structural argument — they are FIXED terms the caller
    supplies, so they go straight into the substitution and onto the left-hand side.
    The one who reaches here with `extras` is `measure_axioms`, which only knows them at
    an APPLICATION; a unary measure (the common case) passes none and is unchanged.

    Every None here is a fact we decline to know, never a fact we get wrong."""
    if len(extras) != len(m.extra):
        return None
    if len(fields) != len(arm.binders):
        return None

    sub: dict[str, Term] = {m.param: target}
    for (en, _er), et in zip(m.extra, extras):
        sub[en] = et            # the non-structural parameters, bound to the args
    for bn, bs, ft in zip(arm.binders, arm.bsorts, fields):
        if bn == "_":
            continue           # the arm ignores this field, so nothing to substitute
        if ft is None or sorts.of(ft) != bs:
            return None
        sub[bn] = ft

    # The NESTED match, one guard at a time (V2.4c step 3 Part B).  Each guard names a
    # field bound further out (in `sub` already, either an outer field or an inner
    # field of an earlier guard) and requires it to be a CONCRETE application of the
    # guard's constructor.  Where it is not — an opaque term, or the wrong constructor —
    # this equation is not the one for that shape, and we decline: None, never a guess.
    for g in arm.guards:
        scrut = sub.get(g.var)
        if not isinstance(scrut, App) or scrut.fn != g.con:
            return None
        if len(scrut.args) != len(g.binders):
            return None
        for bn, bs, ft in zip(g.binders, g.bsorts, scrut.args):
            if bn == "_":
                continue
            if sorts.of(ft) != bs:
                return None
            sub[bn] = ft

    lhs = App(m.name, (target,) + extras)
    if arm.t is not None:
        return Cmp("==", lhs, pred.subst_term(arm.t, sub))
    # A Bool-valued measure is not an equation but an EQUIVALENCE, and it has to be
    # spelled as two implications: the solver's atoms are terms, and `sorted(xs)` is
    # a proposition, so there is no `==` to hang it on.
    body = pred.subst(arm.f, sub)         # type: ignore[arg-type]
    a: Formula = Atom(lhs)
    return And(Or(Not(a), body), Or(a, Not(body)))


def measure_axioms(fs: list[Formula],
                   cons: dict[str, tuple[tuple["Measure", MArm], ...]],
                   sorts: Sorts) -> list[Formula]:
    """Every measure equation the formulas' own constructor terms call for.

    A UNARY measure fires exactly as it always has: at each constructor term the walk
    meets, once, and the subterms it recurses on are constructor terms the walk already
    descends into — so the axiom set closes in a single pass (V2.2).

    An EXTRA-PARAMETER measure (`lt(t, b)`, V2.4c step 5) cannot: its equation is about
    an APPLICATION, `lt(Node(l,x,r), b)`, and the extras (`b`) live only there.  So it
    fires DEMAND-DRIVEN.  A demand is an application `lt(c, b)` that some formula holds,
    and it is discharged by the SHAPE of its first argument:

      • CONSTRUCTOR-HEADED — `lt(Node(l,x,r), b)` — fire the arm and follow the
        equation's own recursive demands `lt(l, b)`, `lt(r, b)` DOWN the structure, the
        bound `b` fixed.  This is the whole of the BUILDING direction: `bst` unfolds to
        `lt(left, x)` at each node, and each such demand walks only its own subtree with
        its own bound.  It never crosses one node's bound with another's — the quadratic
        an all-pairs instantiation would suffer (every subtree × every bound) is exactly
        what following the structure avoids.

      • OPAQUE-HEADED — `lt(lc, b)` with `lc` a match binder — is the DESTRUCTING fact a
        consumer reads out of an abstract `bst(t)`; it stays an atom, no equation, no
        recursion.  Sound silence, and the reason a single-match `bst` can be taken
        apart at all.

    The one bridge to congruence the unary case gets for free is when the head is a
    VARIABLE the program equated to a constructor (`{q | lt(q, 10)}` at a call, with
    `$v == Node(…)`): the term `lt(Node(…), 10)` is never written, so pair the bound
    with the constructor terms of its sort and let equality close the gap — the same
    move the unary walk makes by firing on the bare constructor.  These variable heads
    come from contracts, not from an unfolding, so they are few and the bridge stays
    small."""
    if not cons:
        return []
    out: list[Formula] = []

    # Extra-parameter measures, indexed by name: their arms are triggered by an
    # application, not by the bare constructor the unary index (`cons`) keys on.
    mx: dict[str, list[tuple[Measure, MArm]]] = {}
    for arms in cons.values():
        for (m, arm) in arms:
            if m.extra:
                mx.setdefault(m.name, []).append((m, arm))

    seen_unary:  set[Term] = set()                       # ctor terms fired (unary)
    fired_extra: set[tuple[str, MArm, Term, tuple[Term, ...]]] = set()
    ctor_terms:  list[App] = []                          # all ctor terms, for the bridge
    ctor_seen:   set[App] = set()
    var_demands: list[tuple[str, tuple[Term, ...], str]] = []   # (name, extras, sort)
    bridged:     set[tuple[str, tuple[Term, ...], App]] = set()
    work:        list[Formula] = list(fs)

    def emit(g: Formula) -> None:
        out.append(g)
        work.append(g)          # a generated equation carries the next demands

    def fire_extra(name: str, c: App, extras: tuple[Term, ...]) -> None:
        """Discharge one constructor-headed demand `name(c, extras)`."""
        for (m, arm) in mx.get(name, ()):
            if arm.con != c.fn:
                continue
            key = (name, arm, c, extras)
            if key in fired_extra:
                continue
            fired_extra.add(key)
            g = _instantiate(m, arm, c, c.args, sorts, extras)
            if g is not None:
                emit(g)

    def note_ctor(c: App) -> None:
        if c in ctor_seen:
            return
        ctor_seen.add(c)
        ctor_terms.append(c)
        # A newly seen constructor term is a fresh bridge target for the variable
        # demands already registered.
        for (name, extras, srt) in var_demands:
            bridge(name, extras, c, srt)

    def bridge(name: str, extras: tuple[Term, ...], c: App, srt: str) -> None:
        if sorts.of(c) != srt:
            return              # only a constructor of the demanded ADT can match
        key = (name, extras, c)
        if key in bridged:
            return
        bridged.add(key)
        fire_extra(name, c, extras)

    def walk_t(t: Term) -> None:
        match t:
            case App(fn=fn, args=args):
                for a in args:
                    walk_t(a)
                if fn in cons:                       # a constructor term
                    c = t
                    note_ctor(c)
                    if c not in seen_unary:
                        seen_unary.add(c)
                        for (m, arm) in cons.get(fn, ()):
                            if m.extra:
                                continue             # not fired on the bare constructor
                            g = _instantiate(m, arm, c, args, sorts)
                            if g is not None:
                                emit(g)
                if fn in mx and args:                # an extra-param application: a demand
                    head, extras = args[0], tuple(args[1:])
                    if isinstance(head, App) and head.fn in cons:
                        fire_extra(fn, head, extras)         # constructor-headed
                    else:
                        srt = sorts.of(head)                 # variable/opaque-headed
                        var_demands.append((fn, extras, srt))
                        for c in list(ctor_terms):
                            bridge(fn, extras, c, srt)
            case Neg(term=x):
                walk_t(x)
            case Arith(left=l, right=r):
                walk_t(l); walk_t(r)
            case _:
                pass

    def walk_f(f: Formula) -> None:
        match f:
            case Cmp(left=l, right=r):
                walk_t(l); walk_t(r)
            case Atom(term=t):
                walk_t(t)
            case Not(f=g):
                walk_f(g)
            case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
                walk_f(l); walk_f(r)
            case _:
                pass

    while work:
        walk_f(work.pop())
    return out


# -- The environment ------------------------------------------------------------

@dataclass(frozen=True)
class Env:
    """Refinement types of the bindings in scope, the facts known about them, and
    the sorts the solver needs.  Immutable: every binder returns a new Env, so a
    path condition can never leak out of the branch that assumed it."""
    rtypes: dict[str, RType] = field(default_factory=dict)
    facts:  list[Formula]    = field(default_factory=list)
    vsorts: dict[str, str]   = field(default_factory=dict)
    fsorts: dict[str, str]   = field(default_factory=dict)

    # Translation memo: AST node (by identity) -> its term under THIS environment.
    #
    # `synth` walks every sub-expression exactly once, but at each node it asks for
    # the term of the whole expression rooted there, and that translation recurses
    # to the leaves: n nodes, each re-translating its own subtree, is n².  Within
    # one Env the translation of one AST node is a pure function of that node — it
    # reads rtypes/vsorts/fsorts, all fixed here, and never the facts — so the memo
    # belongs to the Env and dies with it.  A new binding makes a new Env and starts
    # a new memo, which is what keeps a shadowed name from being answered out of the
    # cache of the scope that did not have it.  Keyed by identity: hashing an Expr
    # is itself a walk of the subtree, so a value-keyed cache would pay the very
    # cost it is here to avoid.
    memo: dict[int, "Term | None"] = field(default_factory=dict, compare=False,
                                           repr=False)

    # The sort table of this scope, built on first ask and then kept.  See sorts().
    _sorts: "Sorts | None" = field(default=None, compare=False, repr=False)

    def bind(self, name: str, r: RType) -> "Env":
        """Bind a name, and — the important half — assert what is known about it.

        Binding `x : {v:Int | v > 0}` puts `x > 0` into the facts, with the value
        binder replaced by the name.  That substitution is how a refinement stops
        being a type and starts being something the solver can use.
        """
        rtypes = {**self.rtypes, name: r}
        vsorts = {**self.vsorts, name: sort_of_rtype(r)}
        facts  = list(self.facts)
        if isinstance(r, RBase) and not isinstance(r.p, Top):
            facts.append(pred.subst(r.p, {r.vv: PVarT(name)}))
        return Env(rtypes, facts, vsorts, self.fsorts)

    def assume(self, f: Formula) -> "Env":
        if isinstance(f, Top):
            return self
        return Env(self.rtypes, self.facts + [f], self.vsorts, self.fsorts)

    def sorts(self) -> Sorts:
        """The sort table for this scope — built once per Env, and READ-ONLY.

        An Env is immutable (`bind` and `assume` both return a new one), so its
        sort table is too, and rebuilding it was pure waste: two dict copies, once
        per node that wanted to know the sort of one term.  The table is therefore
        cached, and the price of the cache is a rule: **nobody writes into it.**
        The one caller that used to (subtyping, binding `$v`) now asks for
        `sorts_v`, which hands back a copy of its own.
        """
        s = self._sorts
        if s is None:
            s = Sorts(var={**self.vsorts, "$v": OTHER}, fn=dict(self.fsorts))
            object.__setattr__(self, "_sorts", s)
        return s

    def sorts_v(self, sort: str) -> Sorts:
        """A private sort table with the value binder `$v` at `sort`."""
        base = self.sorts()
        return Sorts(var={**base.var, "$v": sort}, fn=base.fn)


# -- Predicates: Lark expression → logic ----------------------------------------
#
# Two modes, and the difference between them is the difference between a promise
# and a guess:
#
#   STRICT (`term`/`formula`) — used for predicates the programmer WROTE.  Anything
#     outside the fragment is an error.  Silently weakening a predicate the user
#     wrote to `true` would mean the checker says "proved" about something it never
#     looked at.  That is the one failure mode a verifier may not have.
#
#   LENIENT (`term_opt`/`formula_opt`) — used when SYNTHESISING what is known about
#     an arbitrary program expression.  Here, not knowing is fine and normal: an
#     unrepresentable expression just yields no fact.  Weaker ⇒ fewer proofs, never
#     wrong proofs.

_CMP_OPS = {"==": "==", "!=": "/=", "<": "<", "<=": "<=", ">": ">", ">=": ">="}


def term(e: Expr, env: Env) -> Term:
    """Strict: translate a Lark expression into a logic term, or raise."""
    t = term_opt(e, env)
    if t is None:
        raise RefineError(
            f"not expressible in the predicate language: {_show_expr(e)}")
    return t


def _sort_of_term(t: Term, env: Env) -> str:
    """The sort of a term, read straight off the environment — no `Sorts` rebuilt.

    The cases agree with `Sorts.of` (solver.py) one for one; what differs is the
    cost.  `Env.sorts()` used to COPY both dictionaries on every call, and the
    per-node callers called it once per node — a fresh table of every variable in
    scope, built and thrown away, to answer a question about a single term.  The
    table is cached now, but a scope-sized object is still the wrong thing to reach
    for when the question is about one term, so these callers ask here instead."""
    match t:
        case Num() | Neg() | Arith():
            return INT
        case BoolLit():
            return BOOL
        case PVarT(name=n):
            return env.vsorts.get(n, OTHER)
        case App(fn=f):
            return env.fsorts.get(f, OTHER)
    return OTHER


def term_opt(e: Expr, env: Env) -> Term | None:
    """A term, unless the expression is a Float — see FLOAT, at the top of this file.

    The guard belongs HERE rather than at the handful of places a Float could sneak
    in, because `_term_opt` recurses through its own arguments: a term is refused the
    moment it is built, so a term that CONTAINS a Float is refused too (its argument
    was), and there is no path left to enumerate and forget.  A float literal never
    reached the logic in the first place — `Lit(1.5)` matches no case — so what this
    catches is a Float-typed *variable* and a call that *returns* one, which is how
    `if x == x then ... else ...` used to hand the checker a hypothesis that is false
    at run time.
    """
    key = id(e)
    if key in env.memo:
        return env.memo[key]
    t = _term_opt(e, env)
    if t is not None and _sort_of_term(t, env) == FLOAT:
        t = None
    env.memo[key] = t          # see Env.memo: the same node under the same Env twice
    return t                   # is the same term, and asking twice is how n became n²


def _term_opt(e: Expr, env: Env) -> Term | None:
    match e:
        case Lit(value=v) if isinstance(v, bool):
            return BoolLit(v)
        case Lit(value=v) if isinstance(v, int):
            return Num(v)
        case Var(name=n):
            return PVarT(n)
        case Con(name="True"):
            return BoolLit(True)
        case Con(name="False"):
            return BoolLit(False)
        case UnaryOp(op="-", operand=x):
            t = _int_term(x, env)
            return None if t is None else Neg(t)
        case BinOp(op=op, left=l, right=r) if op in ("+", "-", "*"):
            lt, rt = _int_term(l, env), _int_term(r, env)
            if lt is None or rt is None:
                return None
            out = Arith(op, lt, rt)
            # The linearity guard is the fragment's boundary.  A non-linear term is
            # not an error here — in LENIENT mode it is merely something we decline
            # to know.  term() turns the same None into the error, which is where the
            # user actually wrote it.
            #
            # `lt` and `rt` came out of this same function, which returns no term that
            # failed the guard, so the SUBTERMS ARE LINEAR ALREADY and only this node
            # is news: pred.linear_node, not pred.is_linear.  Asking the whole question
            # here re-walked the entire subtree at every level of a walk that already
            # visits every node — cubic, and `1 + 1 + … + 1` (3000 terms) never
            # returned.  pred.formula_linear checks the invariant at the solver's door,
            # so the cheap rule is checked rather than trusted.
            return out if pred.linear_node(out) else None
        case BinOp(op="/", left=l, right=r):
            # Integer division is not linear arithmetic.  Rather than lie about it,
            # make it an uninterpreted symbol: `x / 2` is some integer, and the only
            # thing the solver may conclude is that equal operands divide equally.
            lt, rt = _int_term(l, env), _int_term(r, env)
            if lt is None or rt is None:
                return None
            return App("$div", (lt, rt))
        case Apply(fn=Var(name=f), args=args):
            # A UF SYMBOL IS A GLOBAL FUNCTION, AND ONLY THAT.  The logic names its
            # symbols by source name, and source names shadow: a local `size` and the
            # global `size` a contract was written against would otherwise be one
            # symbol, and congruence would identify two different functions.  That is
            # a false proof, and it was one (`15_shadow`).
            #
            # `vsorts` holds the value variables — parameters, lets, match binders,
            # global values — and never a global function, so a name found there is
            # not the symbol the contract meant.  A locally bound function is then
            # unspeakable: its applications are no term at all.  Nothing is lost that
            # was ever sound, because a local function has no contract to be read off
            # and no equations to instantiate; it had congruence and nothing else, and
            # congruence is the very thing that was wrong.
            if f in env.vsorts:
                return None
            ts = [term_opt(a, env) for a in args]
            if any(t is None for t in ts):
                return None
            return App(f, tuple(t for t in ts if t is not None))

        # A CONSTRUCTOR IS A TERM (V2.2).  `Cons(x, xs)` becomes the uninterpreted
        # application `Cons(x, xs)` — which is the one move the whole rung rests on,
        # and it is almost free: the solver already decides equality and congruence
        # at any sort, so a constructor needs no new theory.  It needs a NAME, and
        # until now it did not have one, which is why `len(Cons(3, Nil))` was a term
        # about a value the logic could not point at.
        #
        # Congruence gives us exactly what a constructor deserves and no more: equal
        # fields build equal values.  It does NOT give injectivity (equal values had
        # equal fields), and we do not assert it — nothing here needs it, and an
        # axiom nobody needs is an axiom nobody has checked.
        case Con(name=c):
            return None if _con_arity(c, env) else App(c, ())
        case Apply(fn=Con(name=c), args=args):
            if _con_arity(c, env) != len(args):
                return None                # partial or over-applied: not a value
            ts = [term_opt(a, env) for a in args]
            if any(t is None for t in ts):
                return None
            return App(c, tuple(t for t in ts if t is not None))
    return None


def _con_arity(c: str, env: Env) -> int:
    """How many fields a constructor takes, read off the type HM already gave it."""
    r = env.rtypes.get(c)
    return len(r.params) if isinstance(r, RFun) else 0


def _int_term(e: Expr, env: Env) -> Term | None:
    """A term, but only if it is INT-sorted.

    The sort guard.  Arithmetic and the ordering relations are defined on integers
    and nowhere else, so a term whose sort we do not know — a variable bound by a
    tuple pattern, a call to a locally-bound function — must not be allowed into
    them.  Dropping it costs a fact (the VC may go unproved); admitting it would
    let the solver reason about a Float or a String as though it were an Int, and a
    verifier that does that will eventually prove something false.

    The failure is therefore silent and safe by design, and it is why every
    unsorted-variable path in this file ends in None rather than in a guess.
    """
    t = term_opt(e, env)
    if t is None:
        return None
    return t if _sort_of_term(t, env) == INT else None


def formula(e: Expr, env: Env) -> Formula:
    """Strict: translate a Lark expression into a logic formula, or raise."""
    f = formula_opt(e, env)
    if f is None:
        raise RefineError(
            f"not a predicate in the decidable fragment: {_show_expr(e)}")
    return f


def formula_opt(e: Expr, env: Env) -> Formula | None:
    match e:
        case Lit(value=True) | Con(name="True"):
            return Top()
        case Lit(value=False) | Con(name="False"):
            return Bot()
        case BinOp(op=op, left=l, right=r) if op in ("<", "<=", ">", ">="):
            # Ordering is integers-only — the sort guard again.
            lt, rt = _int_term(l, env), _int_term(r, env)
            if lt is None or rt is None:
                return None
            return Cmp(_CMP_OPS[op], lt, rt)
        case BinOp(op=op, left=l, right=r) if op in ("==", "!="):
            # Equality, by contrast, is fine at ANY sort — congruence closure does
            # not care what a String is — but the two sides must agree, or the atom
            # is nonsense rather than merely unknown.
            lt, rt = term_opt(l, env), term_opt(r, env)
            if lt is None or rt is None:
                return None
            if _sort_of_term(lt, env) != _sort_of_term(rt, env):
                return None
            return Cmp(_CMP_OPS[op], lt, rt)
        case BinOp(op="and", left=l, right=r):
            lf, rf = formula_opt(l, env), formula_opt(r, env)
            return None if lf is None or rf is None else And(lf, rf)
        case BinOp(op="or", left=l, right=r):
            lf, rf = formula_opt(l, env), formula_opt(r, env)
            return None if lf is None or rf is None else Or(lf, rf)
        case UnaryOp(op="not", operand=x):
            xf = formula_opt(x, env)
            return None if xf is None else Not(xf)
        case IfExpr(cond=c, then_=t, else_=e):
            # A GUARDED PREDICATE (V2.4c step 2).  `if c then p else q` means exactly
            # `(c => p) and (not c => q)` — faithful and complete, with neither branch
            # collapsing to true or false.  But it is admitted ONLY when all three of
            # c, p, q translate; the moment one does not, the whole predicate is None.
            #
            # This is V2.2's law one level up from the solver, and the same rule
            # `_branch` enforces for a program-position `if`: where the checker cannot
            # translate, it says NOTHING.  Returning None here means, at a refinement
            # declaration, the strict `formula()` REJECTS the contract (never an
            # `or Top()` on the branch it could not read — the shape of false proofs #2
            # and #7); and where `formula_opt` feeds an assumption-vs-goal, the caller's
            # own polarity handling drops the hypothesis / asks the goal.  A term-level
            # `if` (a conditional in INT position) is deliberately NOT translated: it
            # never reaches here, so it stays untranslatable, which is sound.
            cf = formula_opt(c, env)
            pf = formula_opt(t, env)
            qf = formula_opt(e, env)
            if cf is None or pf is None or qf is None:
                return None
            return And(Implies(cf, pf), Implies(Not(cf), qf))
        case _:
            # A Bool-sorted term used directly as a proposition: `b`, `is_sorted(xs)`.
            t = term_opt(e, env)
            if t is None:
                return None
            if _term_sort(t, env) != BOOL:
                return None
            return Atom(t)


def _term_sort(t: Term, env: Env) -> str:
    return _sort_of_term(t, env)


def _branch(c: Expr, env: Env) -> tuple[Formula | None, Env, Env]:
    """The two environments an `if` opens: (condition, then-env, else-env).

    THE RULE THIS EXISTS TO ENFORCE: *"I could not translate this"* is not *"this is
    true."*  Both `if` sites used to read

        cf = formula_opt(c, env) or Top()

    and that `or Top()` is a false proof waiting to be written.  An untranslatable
    condition became `true`, the else branch assumed `Not(Top())` — i.e. **FALSE** —
    and from false every obligation in it follows.  `if x * y > 0 then 0 else
    div(100, d)` was "proved" and divides by zero, and the condition was not exotic:
    it was merely NON-LINEAR, which is the ordinary way out of the fragment.

    A condition the logic cannot express constrains NOTHING, so neither branch learns
    anything and both are checked under the environment they already had.  The cost is
    proofs (a fact that was really there is not used); the alternative was a lie.

    This is V1′'s rule, and it now holds one level up from the solver: a checker that
    cannot say something must say NOTHING — never its negation, and never `true`.
    """
    cf = formula_opt(c, env)
    if cf is None:
        return None, env, env
    return cf, env.assume(cf), env.assume(Not(cf))


def _show_expr(e: Expr) -> str:
    """Just enough of the source to point at, for error messages."""
    match e:
        case Lit(value=v):
            return "true" if v is True else "false" if v is False else repr(v)
        case Var(name=n) | Con(name=n):
            return n
        case BinOp(op=op, left=l, right=r):
            return f"({_show_expr(l)} {op} {_show_expr(r)})"
        case UnaryOp(op=op, operand=x):
            return f"({op} {_show_expr(x)})"
        case Apply(fn=f, args=args):
            return f"{_show_expr(f)}(" + ", ".join(_show_expr(a) for a in args) + ")"
        case Lambda():
            return "fn(...)"
        case IfExpr():
            return "if ..."
        case MatchExpr():
            return "match ..."
        case LetExpr():
            return "let ..."
        case TupleExpr(elems=es):
            return "(" + ", ".join(_show_expr(e2) for e2 in es) + ")"
    return "<expr>"


# -- Substitution into refinement types -----------------------------------------

def subst_rtype(r: RType, sub: dict[str, Term]) -> RType:
    match r:
        case RBase(base=b, vv=v, p=p):
            inner = {k: t for k, t in sub.items() if k != v}   # v shadows
            return RBase(b, v, pred.subst(p, inner))
        case RFun(params=ps, ret=ret):
            sub2 = dict(sub)
            new_ps: list[tuple[str, RType]] = []
            for name, pr in ps:
                new_ps.append((name, subst_rtype(pr, sub2)))
                sub2.pop(name, None)                            # later params shadow
            return RFun(tuple(new_ps), subst_rtype(ret, sub2))
        case RTuple(comps=cs):
            return RTuple(tuple(subst_rtype(c, sub) for c in cs))
        case ROpaque():
            return r
    return r


# -- The checker ----------------------------------------------------------------

class Refiner:
    def __init__(self, program: Program, tprog: object, path: str) -> None:
        self.program = program
        self.path    = path
        self.vcs: list[VC] = []
        self._skolem = 0

        # Global signatures come from HM: refine.py never re-derives a type.  This
        # is the "layer on top of Hindley-Milner" of PROVE §2, made concrete —
        # everything below reads types infer.py computed, and where it needs a type
        # infer.py did not hand back (a constructor's, a pattern binder's) it calls
        # infer.py's own function for it rather than working one out for itself.
        self.schemes: dict[str, Scheme] = {}
        base_env, copy_types = _infer._initial_env()
        reg_fresh = ty.Fresh()
        for d in program.decls:
            if isinstance(d, TypeDecl):
                copy_types = _infer._register_type_decl(
                    d, base_env, reg_fresh, copy_types)
            elif isinstance(d, TraitDecl):
                _infer._register_trait_decl(d, base_env, reg_fresh)
        self.schemes.update(base_env)
        for d in tprog.decls:                                   # type: ignore[attr-defined]
            sc = getattr(d, "scheme", None)
            if sc is not None and hasattr(d, "name"):
                self.schemes[d.name] = sc

        # ONE fresh-variable supply, seeded above every type variable the schemes
        # already contain — which is the invariant a fresh supply is supposed to have
        # and which `_bind_pattern` was quietly breaking.  It built a NEW `ty.Fresh()`
        # per call, whose counter restarts at 0; `instantiate` then mapped a scheme's
        # quantified variable α₀ to a "fresh" α₀, and `ty.apply` chased α₀ ↦ α₀ until
        # Python ran out of stack.  `_bind_pattern` caught the RecursionError with a
        # bare `except Exception` and bound NOTHING, so the failure was invisible: a
        # constructor pattern over a POLYMORPHIC ADT — `| Cons(x, rest) =>` — gave its
        # binders no types at all, in V1, V2.0 and V2.1.  A monomorphic one (`| Buf(n)
        # =>`) was fine, because `instantiate` returns early when there is nothing to
        # quantify, which is exactly why the suite never noticed.
        self.fresh = ty.Fresh()
        self.fresh._n = 1 + max(
            (i for sc in self.schemes.values()
             for i in _tvar_ids(sc.body) | set(sc.qs)), default=0)

        self.fsorts: dict[str, str] = {
            name: sort_of_mono(result_mono(sc.body))
            for name, sc in self.schemes.items()
        }
        self.fsorts["$div"] = INT

        # The ADTs a measure may take apart, straight from the source: a measure's
        # arms are indexed by CONSTRUCTOR, so what it needs is the variant list, and
        # infer.py has already turned that into schemes that no longer show it.
        # Computed BEFORE the globals, because since V2.2 the globals need it: a
        # value of a declared ADT is one the logic may name.
        self.adts: dict[str, TypeDecl] = {
            d.name: d for d in program.decls
            if isinstance(d, TypeDecl) and isinstance(d.body, tuple)
        }
        self.adt_names: set[str] = set(self.adts)

        # The traits a program DECLARES, and the impl methods HM already typed.  A
        # trait is what gives an impl method a contract at all: the impl writes
        # `fn describe(c) = ...` with no types on it, so its parameters get their
        # refinements from the signature in the trait, and its HM types from the
        # TFnDecl infer.py built for the same body.  Keyed by (trait, type, method),
        # because the method NAME alone is not unique — that is the whole of what an
        # impl is for.
        self.traits: dict[str, TraitDecl] = {
            d.name: d for d in program.decls if isinstance(d, TraitDecl)
        }
        self.impl_tfns: dict[tuple[str, str, str], object] = {}
        for d in tprog.decls:                                   # type: ignore[attr-defined]
            if isinstance(d, TImplDecl):
                for tm in d.methods:
                    self.impl_tfns[(d.trait_name, d.for_type, tm.name)] = tm

        self.globals: dict[str, RType] = {}
        for name, sc in self.schemes.items():
            self.globals[name] = self._rtype_of_mono(sc.body)
        self.globals.update(_builtin_contracts())

        # Measures, in two passes — because a measure may call one declared after it,
        # and the caller's arm cannot be translated until the callee's SORT is known.
        # Signatures first, bodies second: the same shape as any recursive binding
        # group, and the reason a measure's result type is mandatory syntax.
        self.measures: dict[str, Measure] = {}
        self._measure_names: set[str] = {md.name for md in program.measures}
        # The DECLARED result refinements, read in the first pass with the sorts —
        # because a measure's arms may call a measure declared later, and the
        # induction hypothesis at such a call is that callee's declared result.  The
        # declaration is available before any body is elaborated; that is what a
        # signature is for.
        self._measure_rets: dict[str, ResultAxiom] = {}
        for md in program.measures:
            self.fsorts[md.name] = self._measure_sort(md)
        for md in program.measures:
            self._measure_rets[md.name] = ResultAxiom(
                tuple(p.name for p in md.params), self._measure_ret(md))
        for md in program.measures:
            m = self._elab_measure(md)
            self.measures[m.name] = m

        # Which ADT a constructor belongs to, and — the V2.2 index — which measure
        # equations fire at it.  A measure is TOTAL (V2.1 checks it), so every
        # constructor of its type has exactly one arm here.
        self.con_owner: dict[str, str] = {
            v.name: d.name for d in self.adts.values() for v in d.body  # type: ignore[union-attr]
        }
        self.con_arms: dict[str, tuple[tuple[Measure, MArm], ...]] = {}
        for m in self.measures.values():
            for arm in m.arms:
                self.con_arms[arm.con] = self.con_arms.get(arm.con, ()) + ((m, arm),)

        # WHOSE NAMES ARE STILL THE PRIMITIVES'.  A program may declare a function
        # called `string_length`, and then the symbol in a VC is that one — so the
        # builtin's axiom is not about it, and asserting it anyway proves false
        # things.  Keep the axiom only for the names the program leaves alone.
        rebound = ({d.name for d in program.decls
                    if isinstance(d, (FnDecl, LetDecl))}
                   | {tm.name for t in self.traits.values() for tm in t.methods}
                   | self._measure_names)
        self.prim_results: dict[str, ResultAxiom] = {
            n: ax for n, ax in PRIMITIVE_AXIOMS.items() if n not in rebound
        }
        # What an ordinary obligation may assume about a symbol's result: the
        # primitives' axioms, plus every measure's DECLARED result refinement — which
        # is an axiom no longer, because `_prove_measure` proves it by induction over
        # the arms.  An induction VC gets `prim_results` alone (run(), below).
        self.results: dict[str, ResultAxiom] = dict(self.prim_results)
        for name, ax in self._measure_rets.items():
            if not ax.trivial:
                self.results[name] = ax

        # Declared contracts override the HM-derived trivial ones.  AFTER the
        # measures: a contract is allowed to mention one (`i < len(xs)`), and until
        # `len` has a sort, `_int_term` will not let it into the arithmetic.
        for d in program.decls:
            if isinstance(d, FnDecl):
                self.globals[d.name] = self._fn_rtype(d)
            elif isinstance(d, LetDecl) and isinstance(d.ann, TRefine):
                self.globals[d.name] = self._rtype_of_syn(d.ann, self._base_env())
            elif isinstance(d, TraitDecl):
                # A trait method's contract is the one in the SIGNATURE, and a caller
                # may use it — but only because `_check_impl` now holds every impl to
                # it.  The two halves are one decision: a contract the callers read and
                # nobody checks is exactly the false proof V2.2′ was about.
                for tm in d.methods:
                    sc = self.schemes.get(tm.name)
                    if sc is not None:
                        self.globals[tm.name] = self._rtype_of_sig(
                            tm.typ, sc.body, self._base_env())

    # -- entry --

    def run(self) -> list[VC]:
        for d in self.program.decls:
            if isinstance(d, FnDecl):
                self._check_fn(d)
            elif isinstance(d, LetDecl):
                env = self._base_env()
                self.check(d.value, self.globals[d.name], env, f"let {d.name}")
            elif isinstance(d, ImplDecl):
                self._check_impl(d)
        for vc in self.vcs:
            vc.cons = self.con_arms
            # AN INDUCTION VC MAY NOT ASSUME WHAT IT IS PROVING.  Its goal is about
            # `len(Cons(x, rest))`, and `self.results` would cheerfully assert the
            # measure's declared result AT THAT VERY TERM — the goal would discharge
            # itself, and a bogus declaration would prove.  So the induction VCs get
            # the primitives' axioms only; the induction HYPOTHESIS is supplied by
            # hand, at the recursive occurrences, which are the terms the structural
            # check has already shown to be smaller.  That is the whole difference
            # between induction and assuming the conclusion.
            vc.results = self.prim_results if vc.ind else self.results
        return self.vcs

    def _base_env(self) -> Env:
        env = Env(rtypes=dict(self.globals), facts=[],
                  vsorts={}, fsorts=dict(self.fsorts))
        # Global *values* (not functions) can appear in predicates, so they need a
        # sort; global functions are UF symbols and are handled by fsorts.
        for name, r in self.globals.items():
            if not isinstance(r, RFun):
                env.vsorts[name] = sort_of_rtype(r)
        return env

    def _fresh(self, prefix: str = "$k") -> str:
        self._skolem += 1
        return f"{prefix}{self._skolem}"

    def _rtype_of_mono(self, m: Mono) -> RType:
        """`rtype_of_mono`, told which types are this program's ADTs — so a value of
        one is a value the logic can NAME (see rtype_of_mono's docstring)."""
        return rtype_of_mono(m, self.adt_names)

    # -- syntactic type → refinement type --

    def _rtype_of_syn(self, t: Type, env: Env, hm: Mono | None = None) -> RType:
        match t:
            case TRefine(var=v, base=b, pred=p):
                base_name = _refinable_base(b)
                if base_name is None:
                    # A tuple or a function.  V2.0 refines the COMPONENTS of a product,
                    # not the product itself, and there is nothing a predicate could say
                    # about a pair that it cannot say about its parts.
                    raise RefineError(
                        f"{self.path}: refinement on a type the logic cannot name "
                        f"({_syn_name(b)}); a predicate needs a value it can mention")
                # The value binder is in scope inside its own predicate — that is what
                # `v` IS — so it must have a sort before the predicate is translated.
                inner = env.bind(v, RBase(base_name, "v", Top()))
                f = formula(p, inner)          # STRICT: the user wrote this
                # Carry the ADT's monotype so a destructured field can be pinned
                # (V2.4b).  Only for ADTs, and best-effort: if the base does not
                # convert, mono stays None and the field falls back to OTHER.
                m: Mono | None = None
                if base_name in self.adt_names:
                    try:
                        m = _infer.syntype_to_mono(b, {}, self.fresh)
                    except FRONTEND_ERRORS:
                        m = None
                return RBase(base_name, v, f, mono=m)
            case TName(name="Int"):
                return rtrue("Int")
            case TName(name="Bool"):
                return rtrue("Bool")
            case TName(name="Float"):
                # The sort must be set on BOTH roads into a binder's type — this one,
                # for an ANNOTATED parameter, and `rtype_of_mono`, for an inferred one.
                # A default that is merely opaque is the wrong default for a Float: it
                # grants equality, and equality is the thing a Float may not have.
                return ROpaque(sort=FLOAT)
            case TTuple(elems=elems):
                return RTuple(tuple(self._rtype_of_syn(x, env) for x in elems))
            case STFn():
                return self._rtype_of_mono(hm) if hm is not None else ROpaque()
        return ROpaque()

    def _fn_rtype(self, d: FnDecl) -> RType:
        """A function's contract: annotations where given, `true` where not."""
        sc = self.schemes.get(d.name)
        monos: list[Mono] = []
        cur: Mono | None = sc.body if sc else None
        for _ in d.params:
            if isinstance(cur, TFn):
                monos.append(cur.param)
                cur = cur.result
            else:
                monos.append(TCon("?"))
                cur = None

        env = self._base_env()
        params: list[tuple[str, RType]] = []
        for p, m in zip(d.params, monos):
            if p.ann is not None:
                r = self._rtype_of_syn(p.ann, env, m)
            else:
                r = self._rtype_of_mono(m) if m is not None else ROpaque()
            params.append((p.name, r))
            env = env.bind(p.name, r)          # later params may mention earlier ones

        if d.return_type is not None:
            ret = self._rtype_of_syn(d.return_type, env, cur)
        else:
            ret = self._rtype_of_mono(cur) if cur is not None else ROpaque()
        return RFun(tuple(params), ret)

    # -- traits and impls (the V2.2″ hole) -----------------------------------------
    #
    # `refine.py` used to import `ImplDecl` and never match it, and an impl body was
    # therefore never walked.  The refinement on a trait method was *dropped* rather
    # than trusted, so a lying impl was not a false proof — but `n / 0` inside an impl
    # body raised no obligation at all and the checker printed `ok`, exit 0.  Silent
    # under-verification is the one failure mode a verifier may not have: it is not a
    # weak answer, it is a WRONG REPORT, and 07's own corpus uses impls.
    #
    # An impl method is checked exactly as an `fn` is, against the contract in the
    # TRAIT — which is also what makes a refined trait signature mean anything, since
    # `_check_impl` is what entitles a CALLER to read it.  The two are one decision.

    def _rtype_of_sig(self, t: Type, m: Mono | None, env: Env) -> RType:
        """A refinement type from a SIGNATURE — a trait method's declared type.

        A trait method has no parameter names to bind, so the refinements come from
        the syntax and everything else from the HM type: `_rtype_of_syn` where the
        author wrote `{v : Int | ...}`, `_rtype_of_mono` where they wrote a plain
        type.  Going through the mono for the plain part is what keeps a Float
        unspeakable and an ADT nameable rather than opaque.
        """
        if isinstance(t, TRefine):
            return self._rtype_of_syn(t, env)
        if isinstance(t, STFn):
            params: list[tuple[str, RType]] = []
            cur_t: Type = t
            cur_m: Mono | None = m
            i = 0
            while isinstance(cur_t, STFn):
                pm = cur_m.param if isinstance(cur_m, TFn) else None
                pr = self._rtype_of_sig(cur_t.param, pm, env)
                name = f"$p{i}"
                params.append((name, pr))
                env = env.bind(name, pr)
                cur_t = cur_t.result
                cur_m = cur_m.result if isinstance(cur_m, TFn) else None
                i += 1
            return RFun(tuple(params), self._rtype_of_sig(cur_t, cur_m, env))
        return self._rtype_of_mono(m) if m is not None else ROpaque()

    def _impl_rtype(self, d: ImplDecl, m: ImplMethod, tfn: object) -> RFun:
        """The contract an impl method must meet: the trait's signature, read at the
        impl's own parameter names and the impl's own HM types.

        The trait's type variable needs no substitution here, and that is not an
        oversight: the HM types come from `tfn`, which infer.py checked at the CONCRETE
        type already, and a refinement can only sit on a base the logic can name — never
        on the trait variable itself, which `_rtype_of_syn` rejects outright.  So the
        signature contributes exactly the predicates and nothing about the type.

        Where the trait is not declared in this file (`Copy`, `Show`), there is no
        signature to read and every part falls back to its HM type — a trivial contract,
        which is a contract, and the body is walked all the same.  Nothing is skipped.
        """
        sig: Type | None = None
        trait = self.traits.get(d.trait_name)
        if trait is not None:
            for tm in trait.methods:
                if tm.name == m.name:
                    sig = tm.typ
                    break

        tparams: tuple[tuple[str, Mono], ...] = getattr(tfn, "params", ())
        sc: Scheme | None = getattr(tfn, "scheme", None)
        cur_m: Mono | None = sc.body if sc is not None else None

        env = self._base_env()
        params: list[tuple[str, RType]] = []
        cur_t: Type | None = sig
        for i, p in enumerate(m.params):
            st: Type | None = None
            if isinstance(cur_t, STFn):
                st, cur_t = cur_t.param, cur_t.result
            else:
                cur_t = None
            pm: Mono | None = tparams[i][1] if i < len(tparams) else None
            if pm is None and isinstance(cur_m, TFn):
                pm = cur_m.param
            cur_m = cur_m.result if isinstance(cur_m, TFn) else None

            # An annotation on the impl method's own parameter wins over the trait's:
            # it is the more local thing the author wrote, and it is the only place an
            # impl can say something the trait did not.
            if p.ann is not None:
                r = self._rtype_of_syn(p.ann, env, pm)
            elif st is not None:
                r = self._rtype_of_sig(st, pm, env)
            else:
                r = self._rtype_of_mono(pm) if pm is not None else ROpaque()
            params.append((p.name, r))
            env = env.bind(p.name, r)

        if cur_t is not None:
            ret = self._rtype_of_sig(cur_t, cur_m, env)
        else:
            ret = self._rtype_of_mono(cur_m) if cur_m is not None else ROpaque()
        return RFun(tuple(params), ret)

    def _check_impl(self, d: ImplDecl) -> None:
        for m in d.methods:
            tname = _infer._for_type_name(d)
            tfn   = self.impl_tfns.get((d.trait_name, tname, m.name))
            r     = self._impl_rtype(d, m, tfn)
            env   = self._base_env()
            for (name, pr) in r.params:
                env = env.bind(name, pr)
            self.check(m.body, r.ret, env,
                       f"impl {d.trait_name} for {tname}: fn {m.name}: return value")

    # -- measures: surface → equations (PROVE.md V2.1) --

    def _measure_ret_base(self, md: MeasureDecl) -> str:
        b = md.return_type
        if isinstance(b, TRefine):
            b = b.base
        match b:
            case TName(name="Int"):
                return "Int"
            case TName(name="Bool"):
                return "Bool"
        raise RefineError(
            f"measure '{md.name}': the result type must be Int or Bool, not "
            f"{_syn_name(b)} — a measure's job is to hand the logic something it "
            f"can reason about, and those are the two sorts it has")

    def _measure_sort(self, md: MeasureDecl) -> str:
        return INT if self._measure_ret_base(md) == "Int" else BOOL

    def _elab_measure(self, md: MeasureDecl) -> Measure:
        """Check a measure and turn it into its equations.

        Everything here is a soundness condition wearing the clothes of a style rule.
        The arms become axioms about an uninterpreted symbol, so:

          - EXACTLY ONE ARM PER CONSTRUCTOR.  A missing arm leaves a value the logic
            would have to guess at; two arms for one constructor are two axioms that
            may disagree, and a symbol with contradictory axioms proves everything.
          - RECURSION ONLY ON THE FIELDS OF THE CONSTRUCTOR MATCHED.  Every equation
            then relates a term to strictly smaller terms, so the axiom set has a
            model (evaluate it bottom-up on any finite value) — which is the whole of
            why it is safe to assume.  `len(xs) == 1 + len(xs)` has none.
          - ARM BODIES IN THE FRAGMENT.  Translated STRICTLY: a measure the solver
            cannot state is not a measure, and quietly weakening it to `true` would
            be a checker claiming to have looked.
          - AND THE NAME IS ITS OWN.  A measure that shares a name with a function is
            two definitions of one symbol in the logic — the equations would be
            asserted about `len`, and every predicate saying `len` would mean the
            other one.  Rejected outright rather than silently shadowed.
        """
        name = md.name

        if name in self.schemes or name in self.globals:
            raise RefineError(
                f"measure '{name}' has the same name as a function or value; in the "
                f"logic they would be one symbol with two definitions")
        if name in self.measures:
            raise RefineError(f"measure '{name}' is declared twice")
        if not md.params:
            raise RefineError(
                f"measure '{name}' has no argument; a measure is defined by taking a "
                f"value apart, so it needs one to take apart")

        p0 = md.params[0]
        if p0.ann is None:
            raise RefineError(
                f"measure '{name}': the structural argument '{p0.name}' needs a type "
                f"annotation — its constructors are the measure's equations")
        head = _tycon_of(p0.ann)
        if head is None:
            raise RefineError(
                f"measure '{name}': '{p0.name}' must be a data type, not "
                f"{_syn_name(p0.ann)}")
        tycon, targs = head
        td = self.adts.get(tycon)
        if td is None:
            raise RefineError(
                f"measure '{name}': '{tycon}' is not an algebraic data type declared "
                f"in this program; there are no constructors to write arms for")
        variants: tuple[Variant, ...] = td.body    # type: ignore[assignment]
        if len(td.params) != len(targs):
            raise RefineError(
                f"measure '{name}': '{tycon}' takes {len(td.params)} type "
                f"argument(s), given {len(targs)}")
        tsub = dict(zip(td.params, targs))

        ret = self._measure_ret(md)
        extra: list[tuple[str, RType]] = []
        for p in md.params[1:]:
            if p.ann is None:
                raise RefineError(
                    f"measure '{name}': parameter '{p.name}' needs a type annotation")
            extra.append((p.name, _rtrue_of_syn(p.ann)))

        match md.body:
            case MatchExpr(scrutinee=Var(name=sn), arms=arms) if sn == p0.name:
                pass
            case _:
                raise RefineError(
                    f"measure '{name}' must be a match on '{p0.name}': one arm per "
                    f"constructor is what makes the body an equation set rather than "
                    f"a program")

        out: list[MArm] = []
        # (arm, the env its body was translated in, the body) — kept for V2.3, which
        # PROVES the declared result refinement one arm at a time and needs exactly
        # what the elaboration already had in its hands.  A nested arm's body is the
        # LEAF body under its guards, which is exactly what the induction proves at
        # the concrete-subfield target `_prove_measure` reconstructs from the guards.
        proofs: list[tuple[MArm, Env, Expr]] = []

        env0 = self._base_env().bind(p0.name, _rtrue_of_syn(p0.ann))
        for (n2, r2) in extra:
            env0 = env0.bind(n2, r2)
        self._elab_arms(name, ret, p0.name, p0.ann, arms, env0, out, proofs)

        m = Measure(name, p0.name, tycon, tuple(extra), ret, tuple(out))
        self._prove_measure(m, proofs)
        return m

    def _resolve_adt(self, ty: Type, name: str) -> tuple[tuple, dict[str, Type], str]:
        """The variants, type substitution, and name of the ADT a measure takes apart —
        for the structural argument and for any field a NESTED match takes apart in
        turn (V2.4c step 3 Part B).  The same checks either way: it must be a declared
        data type, applied to the right number of arguments."""
        head = _tycon_of(ty)
        if head is None:
            raise RefineError(
                f"measure '{name}': a measure takes apart a data type, not "
                f"{_syn_name(ty)}")
        tc, targs = head
        td = self.adts.get(tc)
        if td is None:
            raise RefineError(
                f"measure '{name}': '{tc}' is not an algebraic data type declared in "
                f"this program; there are no constructors to write arms for")
        if len(td.params) != len(targs):
            raise RefineError(
                f"measure '{name}': '{tc}' takes {len(td.params)} type argument(s), "
                f"given {len(targs)}")
        return td.body, dict(zip(td.params, targs)), tc      # type: ignore[return-value]

    def _arm_binders(self, name: str, c: str, pat: "PCon", v: "Variant",
                     tsub: dict[str, Type]) -> tuple[list[str], list[RType],
                                                     tuple[str, ...], list[Type]]:
        """The binders, field refinements, field sorts, and field SYNTACTIC TYPES of
        one constructor pattern.  The syntactic types are what a nested match needs
        and a flat one did not: to take a field apart in turn, its own ADT has to be
        recoverable.  Fields' types are read as the MEASURE's declaration instantiates
        them — `Cons of a, List(a)` through `xs : List(Int)` gives `Int, List(Int)`."""
        if len(pat.args) != len(v.payload):
            raise RefineError(
                f"measure '{name}': arm '{c}' binds {len(pat.args)} field(s), but "
                f"'{c}' has {len(v.payload)}")
        binders: list[str] = []
        for sp in pat.args:
            match sp:
                case PVar(name=bn):
                    binders.append(bn)
                case PWild():
                    binders.append("_")
                case _:
                    raise RefineError(
                        f"measure '{name}': arm '{c}' may only bind its fields to names "
                        f"or match one of them; a deeper pattern in the same position "
                        f"is not supported")
        ftypes = [_syn_subst(ft, tsub) for ft in v.payload]
        frs = [_rtrue_of_syn(ft) for ft in ftypes]
        bsorts = tuple(sort_of_rtype(r) for r in frs)
        return binders, frs, bsorts, ftypes

    def _elab_arms(self, name: str, ret: RBase, p0_name: str, p0_ann: Type,
                   arms: tuple, env0: Env,
                   out: list[MArm], proofs: list) -> None:
        """Turn a measure's match — outer, and any NESTED matches inside its arms —
        into the flat set of `MArm` equations (V2.4c step 3 Part B).

        The recursion mirrors the data: an outer arm fixes the constructor an equation
        is ABOUT; each inner match on a bound field splits that equation, per inner
        constructor, into one guarded equation apiece.  A single outer arm with a
        nested match therefore emits several `MArm`s that share `con` and differ in
        their `guards` — the flattening the plan calls for, done once, at elaboration.

        Every rule that made a flat measure sound is applied at EACH level: one arm per
        constructor, totality, binders-not-nested-patterns, structural recursion, and
        strict translation of the leaf.  A partial nested match is as fatal as a
        partial outer one — a shape with no equation is a term the logic must guess."""

        def emit_leaf(body: Expr, env: Env, fields: set[str],
                      outer: tuple, guards: tuple) -> None:
            con, obinders, obsorts = outer
            # Structural recursion, checked on THIS leaf against every field bound on
            # the path to it — outer fields and the inner fields of every guard alike.
            # All are strict subterms of the value the measure is defined on, so a
            # recursive call on any of them descends, and the axiom set keeps its model.
            for call in _measure_calls(body, self._measure_names):
                callee = call.fn.name           # type: ignore[union-attr]
                if not call.args:
                    raise RefineError(
                        f"measure '{name}': '{callee}' is applied to nothing")
                a0 = call.args[0]
                if not (isinstance(a0, Var) and a0.name in fields):
                    raise RefineError(
                        f"measure '{name}': the recursion is not structural — "
                        f"'{callee}' is applied to {_show_expr(a0)}, which is not a "
                        f"field taken apart on the way here. A measure's arms are "
                        f"ASSUMED, and recursion that does not descend makes them "
                        f"inconsistent: an inconsistent assumption proves every goal, "
                        f"including the false ones")
            try:
                if ret.base == "Int":
                    t = term(body, env)
                    if _sort_of_term(t, env) != INT:
                        raise RefineError(
                            f"the arm is not an integer: {_show_expr(body)}")
                    arm = MArm(con, tuple(obinders), obsorts, t, None, guards)
                else:
                    f = formula(body, env)
                    arm = MArm(con, tuple(obinders), obsorts, None, f, guards)
            except RefineError as e:
                raise RefineError(f"measure '{name}', arm '{con}': {e}") from None
            out.append(arm)
            proofs.append((arm, env, body))

        def do_body(body: Expr, env: Env, scope_types: dict[str, Type],
                    fields: set[str], outer: tuple, guards: tuple) -> None:
            match body:
                case MatchExpr(scrutinee=Var(name=sn), arms=inner) if sn in scope_types:
                    do_match(sn, scope_types[sn], inner, env, scope_types,
                             fields, outer, guards)
                case MatchExpr(scrutinee=s):
                    raise RefineError(
                        f"measure '{name}': a nested match must be on a field bound by "
                        f"an enclosing arm — {_show_expr(s)} is not one, so the "
                        f"recursion would no longer be visibly structural")
                case _:
                    emit_leaf(body, env, fields, outer, guards)

        def do_match(scrut_name: str, scrut_ty: Type, marms: tuple, env: Env,
                     scope_types: dict[str, Type], fields: set[str],
                     outer: tuple | None, guards: tuple) -> None:
            variants, tsub, tc = self._resolve_adt(scrut_ty, name)
            cons = {v.name: v for v in variants}
            seen: set[str] = set()
            for pat, body in marms:
                if not isinstance(pat, PCon):
                    raise RefineError(
                        f"measure '{name}': every arm must be a constructor pattern. A "
                        f"variable or '_' arm covers several constructors at once, and a "
                        f"measure needs exactly one equation for each")
                c = pat.name
                v = cons.get(c)
                if v is None:
                    raise RefineError(
                        f"measure '{name}': '{c}' is not a constructor of {tc}")
                if c in seen:
                    raise RefineError(
                        f"measure '{name}': constructor '{c}' has two arms; two "
                        f"equations for one term is an axiom set that can disagree with "
                        f"itself")
                seen.add(c)
                binders, frs, bsorts, ftypes = self._arm_binders(name, c, pat, v, tsub)
                env2 = env
                st2 = dict(scope_types)
                fields2 = set(fields)
                for bn, fr, fty in zip(binders, frs, ftypes):
                    if bn == "_":
                        continue
                    env2 = env2.bind(bn, fr)
                    st2[bn] = fty
                    fields2.add(bn)
                if outer is None:
                    # The top-level match: this arm names the constructor the equation
                    # is ABOUT.  Its binders become the equation's, and the guard chain
                    # starts empty.
                    new_outer: tuple = (c, tuple(binders), bsorts)
                    new_guards: tuple = ()
                else:
                    # A nested match: the equation is still about the OUTER constructor;
                    # this arm adds one guard — the matched field must be `c`.
                    new_outer = outer
                    new_guards = guards + (
                        Guard(scrut_name, c, tuple(binders), bsorts),)
                do_body(body, env2, st2, fields2, new_outer, new_guards)
            missing = [v.name for v in variants if v.name not in seen]
            if missing:
                raise RefineError(
                    f"measure '{name}' has no arm for {', '.join(missing)}; a measure "
                    f"must be TOTAL — a constructor with no equation is a term the logic "
                    f"would have to guess a value for")

        do_match(p0_name, p0_ann, arms, env0, {}, set(), None, ())

    def _prove_measure(self, m: Measure, proofs: list[tuple[MArm, Env, Expr]]) -> None:
        """PROVE the measure's declared result refinement — by structural induction
        over its own arms (PROVE.md V2.3).  One VC per constructor; no new solver.

        This is the rung that turns an AXIOM into a THEOREM.  Until now, the one fact
        the checker had about a UF symbol's result beyond congruence was a set literal
        (`NONNEG_UF`) saying that a length is not negative — a thing V1 knew and, in
        its own comment, conceded it "strictly should not have to."  Now the measure
        DECLARES it —

            measure len(xs : List(a)) : {v : Int | v >= 0}

        — and the declaration is checked.  What has to be shown is that the equations
        entail it at every term they define, which for a structural measure is:

            for each arm  C(y₁ … yₖ) => body
                assuming  the result refinement at every RECURSIVE occurrence  (the IH)
                prove     the result refinement at  m(C(y₁ … yₖ))

        and that is a FINITE set of quantifier-free obligations — one per constructor —
        which the existing solver discharges without learning a thing.  The equation
        itself needs no special handling: `m(C(y…))` is in the goal, so V2.2's walk
        instantiates the arm's own equation at it, and congruence does the rest.  The
        induction is *structural* because the arms are (V2.1 checks it): every
        recursive call is on a FIELD, so the IH is only ever assumed at a term that is
        strictly smaller, and the whole thing is a well-founded induction over the
        value — taken simultaneously over all the measures, since an arm may call any
        of them, and all of them descend.

        The one place this could go wrong is the one that would make it worthless: an
        induction VC must not be handed the very refinement it is proving as an axiom
        about arbitrary terms.  `run()` withholds it — see the comment there.
        """
        ax = self._measure_rets[m.name]
        if ax.trivial:
            return                       # nothing declared, nothing to prove
        for (arm, env, body) in proofs:
            # The constructor term this arm defines the measure AT.  A field the arm
            # ignored still needs a name: an equation is instantiated per POSITION, so
            # `Cons(_, rest)` builds `Cons($f1, rest)` — a skolem, sorted as the field
            # is declared, standing for the value the arm did not care about.
            fields: list[Term] = []
            for (bn, bs) in zip(arm.binders, arm.bsorts):
                if bn == "_":
                    bn = self._fresh("$f")
                    env = env.bind(bn, _rtype_at_sort(bs))
                fields.append(PVarT(bn))
            target = App(arm.con, tuple(fields))

            # A NESTED arm proves its result at the CONCRETE-subfield target — the same
            # shape its equation fires at (V2.4c step 3 Part B).  Each guard replaces
            # the field it names with a concrete application of its constructor, so the
            # induction is about `rdepth(Node(l, v, Leaf))`, exactly the term the
            # equation defines and the term an obligation will mention — not the opaque
            # `Node(l, v, r)`, which has no equation and would prove nothing.  Guards are
            # applied in order, so a guard on an inner field lands on a `PVarT` an
            # earlier guard has already placed in the target.
            gsub: dict[str, Term] = {}
            for g in arm.guards:
                gfields: list[Term] = []
                for (bn, bs) in zip(g.binders, g.bsorts):
                    if bn == "_":
                        bn = self._fresh("$f")
                        env = env.bind(bn, _rtype_at_sort(bs))
                    gfields.append(PVarT(bn))
                app = App(g.con, tuple(gfields))
                target = pred.subst_term(target, {g.var: app})
                gsub[g.var] = app

            # THE STATEMENT PROVED MUST BE THE STATEMENT ASSERTED, and a measure with
            # extra parameters (V2.4) is where that stops being automatic.  `drop(xs, i)`
            # is what a program writes; the induction must be about THAT application,
            # not about a 1-ary `drop(xs)` the logic has never seen — otherwise the
            # theorem is about a term nobody mentions while `result_axioms` asserts the
            # refinement at terms nobody proved.  The extras go in as FREE VARIABLES,
            # which in a QF entailment goal is exactly universal quantification over
            # them (the observation PROVE §V2.5 leans on), so nothing leaves the
            # fragment.  Until V2.4 lets an equation fire for such a measure, this
            # simply goes UNPROVED — which is the sound direction, and the honest one.
            args = (target,) + tuple(PVarT(n) for (n, _) in m.extra)

            # THE INDUCTION HYPOTHESIS, and it is exactly the recursive occurrences —
            # not a schema, not every term of the right sort.  `1 + len(rest)` is
            # non-negative because `len(rest)` is, and `len(rest)` is an application of
            # a measure to a field, which the structural check has already established.
            hyps = list(env.facts)
            for call in _measure_calls(body, self._measure_names):
                callee = call.fn.name                      # type: ignore[union-attr]
                cax = self._measure_rets.get(callee)
                t = term_opt(call, env)
                if cax is None or t is None or cax.trivial or not isinstance(t, App):
                    continue
                # A recursive call under a guard is about the CONCRETE inner term the
                # guard placed, not the opaque field: `rdepth(r)` in the source is
                # `rdepth(Node(rl, rv, rr))` here, exactly as the fired equation's RHS
                # will read it, so the IH and the equation speak of the same term.
                t = pred.subst_term(t, gsub)
                ih = cax.at(t)               # THE SAME DOOR the assertion goes through
                if ih is not None:
                    hyps.append(ih)

            # And the goal goes through it too — `ResultAxiom.at` is the ONE place a
            # declared result becomes a formula, so the theorem the induction discharges
            # and the fact an obligation later assumes cannot drift apart.  It is also
            # what substitutes the measure's PARAMETER: a declared result may say `xs`,
            # and `xs` means the list THIS application is about, never whatever the
            # obligation's own scope happens to call `xs`.
            goal = ax.at(App(m.name, args))
            if goal is None:
                raise RefineError(
                    f"measure {m.name}: cannot state its own declared result")
            self.vcs.append(VC(
                f"measure {m.name}: arm '{arm.con}' satisfies the declared result "
                f"{{{ax.r.vv} : {ax.r.base} | {pred.show(ax.r.p)}}}",
                hyps, goal, env.sorts(), ind=True))

    def _measure_ret(self, md: MeasureDecl) -> RBase:
        """The declared result type, as a refinement.  V2.1 recorded the predicate and
        did nothing with it; since V2.3 it is PROVED (`_prove_measure`, by induction
        over the arms) and then ASSERTED at every application of the measure a VC
        mentions (`result_axioms`) — which is what a declared result is FOR."""
        base = self._measure_ret_base(md)
        if not isinstance(md.return_type, TRefine):
            return rtrue(base)
        r = self._rtype_of_syn(md.return_type, self._base_env())
        return r if isinstance(r, RBase) else rtrue(base)

    def _check_fn(self, d: FnDecl) -> None:
        r = self.globals[d.name]
        if not isinstance(r, RFun):
            return
        env = self._base_env()
        for (name, pr) in r.params:
            env = env.bind(name, pr)
        self.check(d.body, r.ret, env, f"fn {d.name}: return value")

    # -- subtyping: the only place a VC is born --

    def subtype(self, s: RType, t: RType, env: Env, where_: str) -> None:
        """Γ ⊢ S <: T.  For base types this is exactly logical entailment:
        assume everything known, plus S's predicate about the value, and prove T's.
        """
        match (s, t):
            case (RBase(base=_, vv=v1, p=p1), RBase(base=_, vv=v2, p=p2)):
                if isinstance(p2, Top):
                    return                     # nothing to prove
                val = PVarT("$v")
                hyps = env.facts + [pred.subst(p1, {v1: val})]
                goal = pred.subst(p2, {v2: val})
                self.vcs.append(
                    VC(where_, hyps, goal, env.sorts_v(sort_of_rtype(t))))

            case (_, RBase(vv=v2, p=p2)) if not isinstance(p2, Top):
                # The source carries no information (an opaque value, or a function
                # where a base type was wanted).  The obligation is still emitted —
                # it will be provable only if the target's predicate is a tautology.
                val = PVarT("$v")
                self.vcs.append(VC(where_, list(env.facts),
                                   pred.subst(p2, {v2: val}),
                                   env.sorts_v(sort_of_rtype(t))))

            case (RFun(params=ps1, ret=r1), RFun(params=ps2, ret=r2)):
                # Contravariant in parameters, covariant in the result.  Getting this
                # backwards is the classic way to make a checker unsound, so it is
                # spelled out rather than skipped: the ARGUMENT flows from the
                # caller's expectation (ps2) into the callee (ps1).
                if len(ps1) != len(ps2):
                    return
                inner = env
                for (n1, a1), (n2, a2) in zip(ps1, ps2):
                    self.subtype(a2, a1, inner, f"{where_} (parameter {n1})")
                    inner = inner.bind(n1, a2)
                sub = {n1: PVarT(n2) for (n1, _), (n2, _) in zip(ps1, ps2)}
                self.subtype(subst_rtype(r1, sub), r2, inner, f"{where_} (result)")

            case (RTuple(comps=cs1), RTuple(comps=cs2)):
                # Componentwise, and covariant in every position — a product is not a
                # function, so there is no contravariance to get backwards here.
                if len(cs1) != len(cs2):
                    return
                for i, (c1, c2) in enumerate(zip(cs1, cs2)):
                    self.subtype(c1, c2, env, f"{where_} (component {i})")

            case (ROpaque(), RTuple(comps=cs2)):
                # The source is a product the logic could not synthesise anything
                # about.  Each component still owes its obligation, discharged from
                # nothing — provable only if the predicate is a tautology.
                for i, c2 in enumerate(cs2):
                    self.subtype(ROpaque(), c2, env, f"{where_} (component {i})")

            case _:
                return

    # -- synthesis --

    def synth(self, e: Expr, env: Env) -> RType:
        """What do we know about the value of e?  Weaker answers are always safe."""
        match e:
            case Lit(value=v) if isinstance(v, bool):
                return RBase("Bool", "v", Cmp("==", PVarT("v"), BoolLit(v)))
            case Lit(value=v) if isinstance(v, int):
                return RBase("Int", "v", Cmp("==", PVarT("v"), Num(v)))

            # THE THIRD ROAD INTO A FLOAT'S TYPE, and V2.2′(a) paved only two of them.
            # A binder gets its rtype from `rtype_of_mono` (inferred) or `_rtype_of_syn`
            # (annotated), and both were taught that a Float is UNSPEAKABLE.  A float
            # LITERAL goes through neither: it synthesises its own type, and it used to
            # fall through to a bare `ROpaque()` — sort OTHER, which grants EQUALITY.
            # So `let a = 0.0 / 0.0 in if a == a then … else …` put a NaN back into the
            # logic by the one door nobody had shut: the else branch assumed
            # `not (a == a)`, found it contradictory, and proved a division by zero
            # vacuously.  The same bug as V2.2′(a), reached by a different road.
            case Lit(value=v) if isinstance(v, float):
                return ROpaque(sort=FLOAT)

            # THE BUILDING HOOK (V2.2).  A saturated constructor application knows
            # what it is: `{v | v == Cons(x, xs)}`.  That single equality is the
            # whole of it — it puts the term into the obligation, and every measure
            # equation about that term follows from the walk in VC.assumptions().
            # The synthesised type says nothing about `len` and does not need to.
            case Con(name=c) if c in self.con_owner:
                return self._synth_con(c, (), env)
            case Apply(fn=Con(name=c), args=args) if c in self.con_owner:
                return self._synth_con(c, args, env)

            case Var(name=n) | Con(name=n):
                r = env.rtypes.get(n)
                if r is None:
                    return ROpaque()
                if isinstance(r, RBase):
                    # Selfification: the type of `x` is `{v | v == x}`.  x's own
                    # refinement is already a fact (Env.bind put it there), so this
                    # is not losing it — it is connecting the value to the name.
                    return RBase(r.base, "v", Cmp("==", PVarT("v"), PVarT(n)),
                                 mono=r.mono)
                return r

            case BinOp(op=op, left=l, right=r) if op in ("+", "-", "*", "/"):
                lt, rt = self.synth(l, env), self.synth(r, env)
                if op == "/" and sort_of_rtype(lt) != FLOAT \
                        and sort_of_rtype(rt) != FLOAT:
                    # A builtin contract with no signature to hang it on: integer
                    # division demands a non-zero divisor.  This is the div-by-zero
                    # freedom of PROVE V1.4, and it applies to EVERY `/` in the
                    # program, annotated or not.
                    #
                    # ⚠️ AND IT APPLIES TO THE DIVISIONS THE CHECKER DOES NOT UNDERSTAND,
                    # WHICH IS WHERE IT WENT WRONG TWICE.  The adversary found both.
                    #
                    #   `100 / (x * y)` — `term_opt` cannot express a NON-LINEAR divisor
                    #   and returned None, and the site raised NO OBLIGATION AT ALL.
                    #
                    #   `100 / help(...)` where `help` is a LOCAL lambda — V2.2′(c) made
                    #   a locally bound function unspeakable, so the divisor's type came
                    #   back opaque, and the old guard (`rt` must be an `RBase` of base
                    #   Int) declined to ask.
                    #
                    # Both printed `ok`, exit 0, and then divided by zero.  So the
                    # condition for ASKING is no longer "do I understand the divisor" —
                    # it is HM's, which has already ruled that this is an integer
                    # division, and the only thing that excuses the site is positively
                    # knowing the division is a Float's.
                    #
                    # This is V2.2′(b)'s rule at the OPPOSITE POLARITY, and the two must
                    # never be confused.  A HYPOTHESIS it cannot read must be DROPPED
                    # (assume nothing); a GOAL it cannot read must be ASKED ANYWAY, and
                    # then honestly go unproved.  Silence about what you may assume is
                    # modesty; silence about what you must prove is a lie.
                    #
                    # A divisor it cannot name gets a SKOLEM — a name for a value the
                    # checker cannot compute — which inherits whatever the divisor's own
                    # type promised, exactly as an argument's does in `_apply`.  If that
                    # type says `v != 0` the obligation is discharged and the program
                    # keeps its proof (`nz(x * y)` still proves); if it says nothing,
                    # `$k /= 0` is unprovable, which is the true answer.
                    denv = env
                    d = term_opt(r, env) \
                        if isinstance(rt, RBase) and rt.base == "Int" else None
                    if d is None:
                        k = self._fresh()
                        denv = env.bind(
                            k, rt if isinstance(rt, RBase) and rt.base == "Int"
                            else rtrue("Int"))
                        d = PVarT(k)
                    self.vcs.append(VC(
                        f"division by zero: {_show_expr(r)} must be non-zero",
                        list(denv.facts), Cmp("/=", d, Num(0)), denv.sorts()))
                # Float arithmetic yields a Float, and the sort must SURVIVE the
                # operation — otherwise `let a = f * f` hands the logic an OTHER-sorted
                # value again and the literal fix above is undone one line later.
                # Unspeakability is not a property of a literal; it is a property of the
                # values a Float can reach, and every road there has to carry it.
                if FLOAT in (sort_of_rtype(lt), sort_of_rtype(rt)):
                    return ROpaque(sort=FLOAT)
                t = term_opt(e, env)
                base = lt.base if isinstance(lt, RBase) else "Int"
                if t is not None and isinstance(lt, RBase) and isinstance(rt, RBase):
                    return RBase(base, "v", Cmp("==", PVarT("v"), t))
                return rtrue(base) if isinstance(lt, RBase) else ROpaque()

            case BinOp(op=op) if op in _CMP_OPS or op in ("and", "or"):
                # TRANSLATING AN EXPRESSION IS NOT WALKING IT, AND ONLY THE WALK
                # COLLECTS OBLIGATIONS.
                #
                # `formula_opt` and `term_opt` are TRANSLATORS: they turn an expression
                # into something the solver can read, and they are pure — they raise
                # nothing, they ask nothing.  `synth` is the WALK: it is the only thing
                # that visits a division and says "prove this divisor is non-zero".
                #
                # Every case that translated a sub-expression *instead of* synthesising
                # it therefore threw that sub-expression's obligations away, and a
                # comparison is exactly such a case — so
                #
                #     if (x / y) < x then ... else ...        with y = 0
                #
                # checked as `ok: 0 obligation(s) proved`, exit 0, and divided by zero.
                # (The adversary found it, in a Bool position, where nobody had thought
                # to look because nothing in a Bool position LOOKS partial.)  The same
                # was true of `not`, of unary minus, and of an `if`'s condition.
                #
                # The rule, and it is the same one the impl hole taught: EVERY
                # SUB-EXPRESSION IS WALKED EXACTLY ONCE, whether or not it is also
                # translated.  Anything the checker declines to understand it must still
                # LOOK AT.  `_walk` is that visit, and it is unconditional.
                #
                # (`and` and `or` are strict in Lark — the CEK evaluates both operands
                # before `binop` — so both sides are walked with no path condition.  A
                # short-circuiting `and` would owe the right operand the left one's
                # truth, and this line would be wrong.)
                self._walk(e, env)
                f = formula_opt(e, env)
                if f is None:
                    return rtrue("Bool")
                # `v <=> f`, spelled as two implications the solver can use.
                v = Atom(PVarT("v"))
                return RBase("Bool", "v", And(Or(Not(v), f), Or(v, Not(f))))

            case UnaryOp(op="not"):
                self._walk(e, env)
                f = formula_opt(e, env)
                if f is None:
                    return rtrue("Bool")
                v = Atom(PVarT("v"))
                return RBase("Bool", "v", And(Or(Not(v), f), Or(v, Not(f))))

            case UnaryOp(op="-", operand=x):
                # The operand is synthesised FIRST and unconditionally: `-(x / y)` owes
                # an obligation whether or not the negation itself is expressible.  It
                # used to be walked only when `term_opt` FAILED — so the better the
                # checker understood the expression, the less it checked it.
                xt = self.synth(x, env)
                t = term_opt(e, env)
                if t is not None:
                    return RBase("Int", "v", Cmp("==", PVarT("v"), t))
                return xt

            case Apply(fn=Var(name=fn), args=args) if fn in env.rtypes:
                return self._apply(fn, env.rtypes[fn], args, env, e)

            case LetExpr(name=n, ann=ann, value=val, body=body):
                env2 = self._bind_let(n, ann, val, env)
                return self.synth(body, env2)

            case IfExpr(cond=c, then_=th, else_=el):
                # A CONDITION IS AN EXPRESSION.  `_branch` only TRANSLATES it (and
                # rightly says nothing when it cannot); the walk is owed separately, or
                # `if (x / y) < x` is proved with no obligations at all.
                self.synth(c, env)
                cf, then_env, else_env = _branch(c, env)
                # The JOIN.  Rather than throw the branches away, keep each under the
                # condition that selected it: `{v | (c => v==then) and (not c => v==else)}`.
                # This is what lets `if x > 0 then x else 0 - x` be seen as non-negative
                # without the programmer annotating the `if`.
                #
                # (Each branch is synthesised ONCE.  It used to be twice — a walk, then
                # this join — which duplicated every obligation inside an `if` that sat
                # in a value position.  Sound, but the count was a lie, and a count is
                # what this project pins its tests to.)
                rt = self.synth(th, then_env)
                re = self.synth(el, else_env)
                if isinstance(rt, RBase) and isinstance(re, RBase) and rt.base == re.base:
                    v = PVarT("v")
                    pt = pred.subst(rt.p, {rt.vv: v})
                    pe = pred.subst(re.p, {re.vv: v})
                    # With no condition to case on, the value is still one branch's or
                    # the other's — `pt or pe` is what survives, and it is exactly the
                    # weakening of the join below.  (Weaker, never wrong.)
                    p = Or(pt, pe) if cf is None else \
                        And(Or(Not(cf), pt), Or(cf, pe))
                    return RBase(rt.base, "v", p)
                return rt if isinstance(rt, ROpaque) else rtrue(
                    rt.base if isinstance(rt, RBase) else "Int")

            case TupleExpr(elems=elems):
                return RTuple(tuple(self.synth(x, env) for x in elems))

            case MatchExpr():
                self._walk_match(e, env, None)
                return ROpaque()

            # A LAMBDA'S BODY IS CODE, AND CODE IS WALKED.  (V2.2‴'s rule, and the eighth
            # false proof — found by `tests/invariants.py`, which is the first thing in
            # this project to find one on purpose rather than by luck.)
            #
            # `check` walks a lambda's body when it has an RFun to push in (see below).
            # `synth` did not, and an unannotated `let h = fn (a) => …` goes through
            # `synth`.  So:
            #
            #     let h = fn (a : Int) => 100 / a in h(0)
            #
            # reported `ok: 0 obligation(s) proved`, exit 0, and then divided by zero.
            # The body was never looked at.  It is the same bug as the four `formula_opt`
            # sites — a piece of the program the checker never walked — wearing a
            # different hat, which is what makes it worth a paragraph: the rule "every
            # sub-expression is walked exactly once" is not a fact about expressions, it
            # is a fact about EVERY PLACE CODE CAN HIDE, and a lambda is one of them.
            #
            # The body is walked with the parameters bound to what is DECLARED about them
            # and nothing more.  An UNANNOTATED parameter is `ROpaque` — the checker knows
            # nothing, which is the truth: nothing constrains it, so a division by it is
            # provable only if it holds for EVERY value, and otherwise goes honestly
            # unproved.  An ANNOTATED parameter carries its refinement, and the body may
            # ASSUME it — but only because the type below makes every caller ESTABLISH it.
            #
            # The synthesised TYPE is an `RFun` carrying the parameters' refinements,
            # exactly as a top-level `fn` (see `_fn_rtype`).  That is the OTHER half of
            # the lambda story, and 22 fixed only the first: walking the body assumes each
            # parameter is WHAT ITS ANNOTATION SAYS (`fn (k : {v | v != 0}) => 100 / k`
            # proves `k != 0`), and that assumption is honest only if every CALL is made to
            # keep it.  Returning `ROpaque()` dropped the contract on the floor, so the
            # application discharged nothing — `let g = fn (k : {v | v != 0}) => 100 / k in
            # g(0)` was `ok: 1 obligation(s) proved`, exit 0, then ZeroDivisionError, the
            # ninth false proof.  With the `RFun`, `_apply` raises the precondition at the
            # call the same way it does for a named function, and the body may go on
            # assuming the parameter BECAUSE the caller is now made to establish it.
            case Lambda(params=ps, body=b):
                inner = env
                params: list[tuple[str, RType]] = []
                for p in ps:
                    prt = (self._rtype_of_syn(p.ann, inner) if p.ann is not None
                           else ROpaque())
                    params.append((p.name, prt))
                    inner = inner.bind(p.name, prt)
                ret = self.synth(b, inner)
                return RFun(tuple(params), ret)

            case BinOp(op=op):
                # A NEW OPERATOR MUST NOT BE ABLE TO ENTER THE LANGUAGE BEHIND THE
                # CHECKER'S BACK.  Every case above knows its operator by name; a BinOp
                # that reaches here is one the checker has never heard of, and the
                # fall-through below would hand it back as an opaque value — no
                # obligation, no error, `ok`, exit 0.
                #
                # That is not a hypothetical.  It is the shape of every hole this fork
                # has had: `ImplDecl` was imported and never matched, so impl bodies went
                # unwalked; a Float literal had no sort, so it was quietly OTHER.  The
                # front end grew a form and the checker did not notice, and silence read
                # as approval.  `%` is the one waiting to happen — the CEK already
                # divides for it (`l.n - int(l.n / r.n) * r.n`, which traps on 0) and
                # only the LEXER is keeping it out of the language.
                #
                # So: an operator the checker does not know is an error in the CHECKER,
                # and it says so, loudly, instead of proving the program.  Whoever adds
                # `%` to the lexer will meet this line before they meet a false proof —
                # and what they owe here is a divisor obligation, exactly as `/` does.
                raise RefineError(
                    f"the refinement checker does not know the operator '{op}' — it was "
                    f"added to the language without being taught here. If it can fail "
                    f"(as '%' can, on a zero divisor), it owes an obligation at this "
                    f"site; if it cannot, add it to the arithmetic case above.")
        # Everything else — tuples, constructors with payload, strings: opaque.
        # Sub-expressions still get walked, so their own VCs are not lost.
        self._walk(e, env)
        return ROpaque()

    def _synth_con(self, c: str, args: tuple[Expr, ...], env: Env) -> RType:
        """What a constructor application is: itself.

        The arguments are synthesised first and unconditionally — a field may hold a
        division, or a call to a builtin with a precondition, and those obligations
        belong to the program whether or not the constructor around them turns out to
        be nameable."""
        for a in args:
            self.synth(a, env)
        if _con_arity(c, env) != len(args):
            return ROpaque()          # partial application: a function, not a value
        ts = [term_opt(a, env) for a in args]
        if any(t is None for t in ts):
            # A field the logic cannot name (a Float, a lambda).  The value is still a
            # perfectly good `List`; we simply cannot say WHICH one, so we say nothing.
            return ROpaque()
        t = App(c, tuple(x for x in ts if x is not None))
        return RBase(self.con_owner[c], "v", Cmp("==", PVarT("v"), t))

    def _con_field_sort(self, c: str, i: int) -> str:
        """The sort a measure gives field `i` of constructor `c`.

        Only a measure knows this, and only because it declared the type argument:
        `Cons of a, List(a)` says field 0 has sort OTHER, but `measure len(xs :
        List(Int))` says it has sort Int, and the second is the one an equation is
        going to be instantiated against.  Where the measures disagree — different
        measures over different instantiations of the same ADT — we take neither, and
        the equation is dropped rather than mis-sorted."""
        ss = {arm.bsorts[i] for (_m, arm) in self.con_arms.get(c, ())
              if i < len(arm.bsorts)}
        return ss.pop() if len(ss) == 1 else OTHER

    def _pat_term(self, p: Pat, env: Env,
                  want: str = OTHER) -> tuple[Term | None, Env]:
        """The term a sub-pattern names, for the destructuring hook.

        A wildcard is SKOLEMISED rather than given up on, and that is worth a line: a
        field the program declined to name still exists, so naming it ourselves loses
        nothing and keeps the equation.  `| Cons(x, _) =>` therefore still yields
        `len(xs) == 1 + len($f1)` — weak, but it is the fact V2.3 will multiply by
        `len >= 0` to get `len(xs) >= 1`.  A nested constructor pattern rebuilds its
        own term, so the equations compose without any special case for depth."""
        match p:
            case PVar(name=n):
                return PVarT(n), env
            case PLit(value=v) if isinstance(v, bool):
                return BoolLit(v), env
            case PLit(value=v) if isinstance(v, int):
                return Num(v), env
            case PCon(name=c2, args=ps2) if c2 in self.con_owner and \
                    _con_arity(c2, env) == len(ps2):
                ts: list[Term] = []
                for i, sp in enumerate(ps2):
                    t2, env = self._pat_term(sp, env, self._con_field_sort(c2, i))
                    if t2 is None:
                        return None, env
                    ts.append(t2)
                return App(c2, tuple(ts)), env
            case PWild():
                k = self._fresh("$f")
                return PVarT(k), env.bind(k, _rtype_at_sort(want))
        return None, env

    def _apply(self, fn: str, ft: RType, args: tuple[Expr, ...],
               env: Env, whole: Expr) -> RType:
        if not isinstance(ft, RFun) or len(ft.params) != len(args):
            for a in args:
                self.synth(a, env)
            return ROpaque()

        sub: dict[str, Term] = {}
        inner = env
        for (pname, prt), arg in zip(ft.params, args):
            art = self.synth(arg, inner)
            expected = subst_rtype(prt, sub)
            # THE CALL-SITE OBLIGATION.  This one line is most of what a refinement
            # checker is: the argument must satisfy the parameter's contract, with
            # earlier arguments already substituted in — which is why `i < len(xs)`
            # can talk about the `xs` that was passed a moment ago.
            self.subtype(art, expected, inner,
                         f"call to {fn}: argument '{pname}'")

            t = term_opt(arg, inner)
            if t is None:
                # An argument the logic cannot name gets a skolem constant, and the
                # skolem inherits whatever the argument's own type promised.
                k = self._fresh()
                inner = inner.bind(k, art)
                t = PVarT(k)
            sub[pname] = t

        return subst_rtype(ft.ret, sub)

    def _bind_let(self, n: str, ann: Type | None, val: Expr, env: Env) -> Env:
        if ann is not None:
            declared = self._rtype_of_syn(ann, env)
            self.check(val, declared, env, f"let {n}")
            return env.bind(n, declared)
        r = self.synth(val, env)
        return env.bind(n, r)

    # -- checking --

    def check(self, e: Expr, t: RType, env: Env, where_: str) -> None:
        """Check e against t.  Structural where it pays: pushing the expected type
        THROUGH an if/let/match keeps each branch's path condition available when
        its obligation is discharged.  Synthesise-then-subtype would prove the same
        VCs with the hypotheses thrown away, and fail on programs that are fine."""
        match e:
            case IfExpr(cond=c, then_=th, else_=el):
                self.synth(c, env)          # the condition is walked, not just read
                _cf, then_env, else_env = _branch(c, env)
                self.check(th, t, then_env, where_)
                self.check(el, t, else_env, where_)
                return

            case LetExpr(name=n, ann=ann, value=val, body=body):
                env2 = self._bind_let(n, ann, val, env)
                self.check(body, t, env2, where_)
                return

            case MatchExpr():
                self._walk_match(e, env, (t, where_))
                return

            case TupleExpr(elems=elems) if isinstance(t, RTuple) and \
                    len(elems) == len(t.comps):
                # Push the expected type INTO the components, for the same reason
                # check() pushes it through an if: the obligation is then reported at
                # the component the programmer actually wrote.
                for i, (x, c) in enumerate(zip(elems, t.comps)):
                    self.check(x, c, env, f"{where_} (component {i})")
                return

            case Lambda(params=ps, body=body) if isinstance(t, RFun) and \
                    len(ps) == len(t.params):
                inner = env
                for p, (_, pr) in zip(ps, t.params):
                    inner = inner.bind(p.name, pr)
                sub = {n: PVarT(p.name)
                       for (n, _), p in zip(t.params, ps)}
                self.check(body, subst_rtype(t.ret, sub), inner, where_)
                return

        r = self.synth(e, env)
        self.subtype(r, t, env, where_)

    def _walk_match(self, e: MatchExpr, env: Env,
                    expect: "tuple[RType, str] | None") -> None:
        """Match arms, with the path conditions a literal pattern gives us.

        Only literal patterns speak to the logic in V1: `| 0 =>` tells us the
        scrutinee is 0, and — because the arms are tried in order — reaching arm k
        tells us it was NOT any earlier literal.  That negative information is free
        and is what makes `match n with | 0 => ... | _ => 100 / n end` provable.

        THE DESTRUCTING HOOK (V2.2) is the line that used to say "constructor patterns
        say nothing until measures exist".  Now they say one thing, and it is the
        modest one: reaching `| Cons(x, rest) =>` means the scrutinee IS `Cons(x,
        rest)`.  Not "its length is one more than rest's" — that is a consequence, and
        it arrives on its own, because the term is now in the hypotheses and
        VC.assumptions() instantiates `len` at every constructor term it finds.  The
        hook supplies a term; the equations are somebody else's job.
        """
        st = term_opt(e.scrutinee, env)
        sr = self.synth(e.scrutinee, env)
        seen: list[Formula] = []

        for pat, body in e.arms:
            inner = env
            for neg in seen:
                inner = inner.assume(Not(neg))

            match pat:
                case PLit(value=v) if st is not None and isinstance(v, bool):
                    f = Cmp("==", st, BoolLit(v))
                    inner = inner.assume(f)
                    seen.append(f)
                case PLit(value=v) if st is not None and isinstance(v, int):
                    f = Cmp("==", st, Num(v))
                    inner = inner.assume(f)
                    seen.append(f)
                case PVar(name=n):
                    inner = inner.bind(n, sr)
                case PCon(name=c, args=ps) if st is not None and \
                        c in self.con_owner and _con_arity(c, inner) == len(ps):
                    # Bind first: the equation's fields are the binders, and a binder
                    # with no sort is a term the logic will refuse to reason about.
                    inner = self._bind_pattern(pat, inner, sr)
                    ts: list[Term] = []
                    ok = True
                    for i, sp in enumerate(ps):
                        t2, inner = self._pat_term(
                            sp, inner, self._con_field_sort(c, i))
                        if t2 is None:
                            ok = False
                            break
                        ts.append(t2)
                    if ok:
                        # Assumed in THIS arm, and deliberately not added to `seen`.
                        # A literal pattern's negative information is free; a
                        # constructor's is not.  "The scrutinee was not `Cons(x,
                        # rest)`" mentions binders that exist only inside this arm,
                        # and the fact we actually want — "it was not a Cons at all" —
                        # needs constructor DISJOINTNESS, an axiom the logic does not
                        # have and that V2.2 does not need.  So we take the positive
                        # half and leave the negative half on the table.
                        inner = inner.assume(
                            Cmp("==", st, App(c, tuple(ts))))
                case _:
                    inner = self._bind_pattern(pat, inner, sr)

            if expect is None:
                self.synth(body, inner)
            else:
                t, where_ = expect
                self.check(body, t, inner, where_)

    def _bind_pattern(self, pat: Pat, env: Env, scrut: RType | None = None) -> Env:
        """Give a pattern's binders their types — by asking infer.py, not by
        working them out.  `infer_pat` instantiates the constructor's scheme and
        unifies the sub-patterns against its field types, so `| Buf(n) =>` really
        does deliver `n : Int`, and the arm can do arithmetic on it.

        A TUPLE pattern was V1's gap, and it is what V2.0 closes.  `infer_pat` can
        only give a tuple's binders FRESH type variables — the scrutinee's type is
        what determines them, and infer.py is not being re-run here — so they landed
        at sort OTHER and V1 could not see through `match f(x) with | (a, b) => ...`,
        the exact shape the affine borrow idiom needs.  The fix is not to infer harder
        but to stop inferring: the scrutinee has already been SYNTHESISED, so if it
        came back an RTuple, its components ARE the binders' refinement types, and
        every fact the callee's contract promised about them survives the destructuring.
        """
        if isinstance(pat, PTuple) and isinstance(scrut, RTuple) and \
                len(pat.elems) == len(scrut.comps):
            for sub, r in zip(pat.elems, scrut.comps):
                match sub:
                    case PVar(name=n):
                        env = env.bind(n, r)
                    case _:
                        env = self._bind_pattern(sub, env, r)
            return env

        # self.fresh, NOT a new ty.Fresh(): see the comment where it is seeded.  The
        # `except` stays — infer_pat may legitimately fail on a pattern this pass has
        # no business re-deriving — but it no longer papers over a bug, and it no
        # longer catches RecursionError, because there is no longer one to catch.
        try:
            _tp, _pt, local, _s = _infer.infer_pat(
                pat, self.fresh, dict(self.schemes))
        except FRONTEND_ERRORS:
            return env
        # V2.4b — pin polymorphic fields against the scrutinee's ACTUAL monotype.
        # infer_pat instantiated the constructor with fresh vars, so `Cons(x, _)`
        # gives `x` a fresh `a` (sort OTHER) with nothing to say `a == Int`.  The
        # scrutinee has already been synthesised and carries its monotype, so — the
        # ADT analog of the RTuple case above — unify the pattern's type against it
        # and `a` is Int.  Best-effort: a scrutinee with no monotype, or a genuinely
        # polymorphic one, leaves the field OTHER, which is the SOUND fallback.
        if isinstance(scrut, RBase) and scrut.mono is not None:
            try:
                s = ty.unify(_pt, scrut.mono)
                local = {k: ty.apply_scheme(s, sc) for k, sc in local.items()}
            except FRONTEND_ERRORS:
                pass
        for name, sc in local.items():
            env = env.bind(name, self._rtype_of_mono(sc.body))
        return env

    def _walk(self, e: Expr, env: Env) -> None:
        """Visit sub-expressions of a node we do not model, so their obligations
        (a division, a call to a builtin with a contract) are still collected."""
        match e:
            case TupleExpr(elems=elems):
                for x in elems:
                    self.synth(x, env)
            case Apply(fn=f, args=args):
                self.synth(f, env)
                for a in args:
                    self.synth(a, env)
            case BinOp(left=l, right=r):
                self.synth(l, env)
                self.synth(r, env)
            case UnaryOp(operand=x):
                self.synth(x, env)
            case Lambda(body=b):
                self.synth(b, env)
            case _:
                pass


def _refinable_base(t: Type) -> str | None:
    """The name of the base a predicate may be hung on, or None.

    Int and Bool the logic INTERPRETS; an ADT or a String it merely NAMES — but a
    name is all a predicate needs, since the only operations available on an
    OTHER-sorted value are equality and uninterpreted application.  A tuple and a
    function have no name to give, and are rejected."""
    match t:
        case TName(name=n):
            return n
        case TApply(name=n):
            return n
    return None


def _tycon_of(t: Type) -> tuple[str, tuple[Type, ...]] | None:
    """The head of a data type and its arguments: List(a) -> ("List", (a,))."""
    match t:
        case TName(name=n):
            return (n, ())
        case TApply(name=n, args=args):
            return (n, args)
    return None


def _syn_name(t: Type) -> str:
    match t:
        case TName(name=n):
            return n
        case TApply(name=n):
            return n
        case TUnit():
            return "()"
        case TTuple():
            return "tuple"
        case STFn():
            return "function"
        case TRefine():
            return "refinement"
    return "?"


# -- Builtin contracts ----------------------------------------------------------

def _builtin_contracts() -> dict[str, RType]:
    """Preconditions for the builtins that actually have them.

    These are the real Lark primitives, not toys — `string_index` is what the
    self-hosted lexer calls on every character — so proving a program's indices are
    in bounds is proving something about code that exists.

    `string_length` is uninterpreted, which is exactly enough: the checker cannot
    compute a string's length, but it can carry the SAME opaque length through the
    guard, the loop and the index, and see that they agree.
    """
    slen = lambda s: App("string_length", (PVarT(s),))     # noqa: E731
    return {
        "string_index": RFun(
            (("s", ROpaque()),
             ("i", RBase("Int", "v",
                         And(Cmp("<=", Num(0), PVarT("v")),
                             Cmp("<", PVarT("v"), slen("s")))))),
            rtrue("Int")),
        "string_slice": RFun(
            (("s", ROpaque()),
             ("a", RBase("Int", "v",
                         And(Cmp("<=", Num(0), PVarT("v")),
                             Cmp("<=", PVarT("v"), slen("s"))))),
             ("b", RBase("Int", "v",
                         And(Cmp("<=", PVarT("a"), PVarT("v")),
                             Cmp("<=", PVarT("v"), slen("s")))))),
            ROpaque()),
        "string_length": RFun(
            (("s", ROpaque()),),
            RBase("Int", "v", Cmp("==", PVarT("v"), slen("s")))),
        # `min`/`max` are UNINTERPRETED, exactly as `string_length` is: the checker
        # cannot compute the minimum, but it can carry the SAME opaque term `min(a, b)`
        # through the program and let its axioms (PRIMITIVE_AXIOMS, below) say the three
        # things that are true of it.  This entry is only the selfification — it names
        # the result, `{v | v == min(a, b)}`, so a call becomes that term in the logic;
        # the facts live in the axiom table where they can be audited.  (V2.4c step 1.)
        "min": RFun(
            (("a", rtrue("Int")), ("b", rtrue("Int"))),
            RBase("Int", "v", Cmp("==", PVarT("v"), App("min", (PVarT("a"), PVarT("b")))))),
        "max": RFun(
            (("a", rtrue("Int")), ("b", rtrue("Int"))),
            RBase("Int", "v", Cmp("==", PVarT("v"), App("max", (PVarT("a"), PVarT("b")))))),
    }


# -- Driver ---------------------------------------------------------------------

@dataclass
class Result:
    proved:   int
    failed:   list[VC]
    # The obligations the SOLVER ABANDONED — a budget ran out, and it stopped looking.
    # A subset of `failed`, because giving up counts as not proved and must: the sound
    # direction is the whole of V1′.  It is reported separately because it is a
    # different sentence.  "This does not follow from what you told me" is a fact about
    # the program; "I ran out of room" is a fact about the checker, and printing the
    # second in the words of the first is how a tool teaches its user to distrust it.
    gave_up:  list[VC] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.proved + len(self.failed)


# Every way the front end can legitimately reject a program.  A refinement checker
# runs *after* the type checker, so it must be able to say "this program does not
# typecheck" for EVERY reason the type checker has — including the ones that are
# easy to forget because they are rare.  `TraitBoundError`, `LexError` and `ty`'s
# `UnifyError` are exactly those: leaving them out does not make the checker wrong,
# it makes it crash with a Python traceback on a program the language itself has a
# perfectly good error message for.  Found by sweeping 07's own corpus (`make -C 08
# robust`), which is the point of sweeping it.
FRONTEND_ERRORS = (
    _lexer.LexError,
    _parser.ParseError,
    _infer.TypeError,
    _infer.AffineError,
    _infer.TraitBoundError,
    ty.UnifyError,
)

# The checker's own two ways of failing: a predicate outside the decidable fragment,
# or one the VC generator cannot model.  Distinct from FRONTEND_ERRORS on purpose —
# "your program is ill-typed" and "I cannot reason about this predicate" are
# different sentences and must not be printed as the same one.
REFINE_ERRORS = (RefineError, PredError)


class TooDeep(RefineError):
    """The program nests deeper than the checker can walk.

    Every pass here is recursive descent — the parser, the type checker, the VC
    generator, `pred.subst` — so a deeply enough nested expression exhausts the Python
    stack, and until this existed the result was a raw `RecursionError` traceback: a
    crash, at a checker, whose whole job is to tell you something true about a program.

    The rule it obeys is the fork's oldest, and it is what makes this an ERROR rather
    than a shrug: WHERE IT CANNOT SPEAK, IT SAYS NOTHING — and it must never let that
    silence read as approval.  A program the checker could not walk has not been
    checked, so it may not exit 0, may not print `ok`, and may not report zero
    obligations.  It says so, in words, and exits like any other malformed input.
    """


# The stack the checker actually gets.  CPython's default is ~1000 frames, and one
# level of `let … in` costs several of them across the four passes, so a perfectly
# ordinary generated program (a 1200-`let` chain; a 400-element list literal) hit the
# ceiling.  A worker thread with a big stack and a raised limit is the standard remedy,
# and it is confined to this module: 07's own interpreter keeps its own limits, which is
# what the conservative-extension differential requires.  The limit is a fence, not a
# cliff — whatever still overflows becomes `TooDeep`, above.
STACK_BYTES = 512 * 1024 * 1024
STACK_DEPTH = 200_000


def _with_big_stack(fn):
    """Run `fn` on a thread with a stack deep enough to walk a real program."""
    import threading
    out: list = []
    err: list = []

    def run() -> None:
        old = sys.getrecursionlimit()
        sys.setrecursionlimit(STACK_DEPTH)
        try:
            out.append(fn())
        except BaseException as e:                       # re-raised on the caller's thread
            err.append(e)
        finally:
            sys.setrecursionlimit(old)

    try:
        threading.stack_size(STACK_BYTES)
    except (ValueError, RuntimeError):
        pass                                             # take what the platform gives
    t = threading.Thread(target=run)
    t.start()
    t.join()
    if err:
        raise err[0]
    return out[0]


def check_program(path: str) -> Result:
    return _with_big_stack(lambda: _check_program(path))


def _check_program(path: str) -> Result:
    try:
        return _check_program_inner(path)
    except RecursionError:
        # NOT a Python bug to leak, and NOT an `ok`.  The one thing that must not happen
        # is for the checker to fall over and leave the program looking checked.
        raise TooDeep(
            f"{path}: nested too deeply for the checker to walk "
            f"(recursion limit {STACK_DEPTH})") from None


def _check_program_inner(path: str) -> Result:
    program = _parser.parse_file(path)
    tprog   = _infer.typecheck(program, source_file=path)
    vcs     = Refiner(program, tprog, path).run()

    proved = 0
    failed:  list[VC] = []
    gave_up: list[VC] = []
    for vc in vcs:
        hyps = vc.assumptions()
        # THE DOOR.  Everything upstream is careful to keep non-linear terms out of
        # the logic; this is where that care is CHECKED, on the last formulas before
        # they become the solver's problem.  A non-linear term past here is not a
        # wrong answer, it is an undefined one — the Omega test is a decision
        # procedure for linear arithmetic and for nothing else — so the checker must
        # not merely believe it never built one.  (It is a bug in the checker, not in
        # the program, hence the raise: it should be impossible, and if it happens we
        # want to be told, not to get an answer.)
        for f in (*hyps, vc.goal):
            if not pred.formula_linear(f):
                raise RefineError(
                    f"internal: non-linear term reached the solver: {pred.show(f)}")
        ok, quit_ = solver.decide(hyps, vc.goal, vc.sorts)
        if ok:
            proved += 1
        else:
            failed.append(vc)
            if quit_:
                gave_up.append(vc)
    return Result(proved, failed, gave_up)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: refine.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        res = check_program(path)
    except FRONTEND_ERRORS as e:
        print(f"type error: {e}", file=sys.stderr)
        sys.exit(2)
    except REFINE_ERRORS as e:
        print(f"refinement error: {e}", file=sys.stderr)
        sys.exit(2)

    quit_ = {id(vc) for vc in res.gave_up}
    for vc in res.failed:
        # Two different sentences, and the checker owes the user the right one.
        head = ("gave up (budget exhausted)" if id(vc) in quit_ else "cannot prove")
        print(f"{head}: {vc.where_}", file=sys.stderr)
        print(f"    goal: {pred.show(vc.goal)}", file=sys.stderr)
        if vc.hyps:
            print(f"    from: {pred.show(pred.conj(vc.hyps))}", file=sys.stderr)

    if res.failed:
        note = (f" ({len(res.gave_up)} abandoned on a budget)" if res.gave_up else "")
        print(f"{len(res.failed)} of {res.total} obligation(s) unproved{note}",
              file=sys.stderr)
        sys.exit(1)

    print(f"ok: {res.proved} obligation(s) proved")
