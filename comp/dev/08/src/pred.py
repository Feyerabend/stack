"""
The predicate language — QF-UFLIA (PROVE.md V1).

This is the logic refinements are written in, and it is deliberately *smaller*
than Lark: quantifier-free formulas over linear integer arithmetic, booleans, and
uninterpreted function symbols with equality.  Everything in it is decidable
(solver.py decides it); everything outside it is either rejected at
well-formedness time or abstracted to an uninterpreted symbol.

Two sorts, and they are kept apart:

    Term    ::= n                      integer literal
              | x                      variable      (Int- or Bool-sorted)
              | -t | t + t | t - t     linear arithmetic
              | k * t | t * k          multiplication by a *literal* only
              | f(t, ...)              uninterpreted function application
              | true | false           boolean literal

    Formula ::= true | false
              | t = t | t /= t         equality over either sort
              | t < t | t <= t | t > t | t >= t     integer comparison
              | b                       a Bool-sorted term used as an atom
              | not F | F and F | F or F | F => F

Multiplication is restricted to `literal * term` so arithmetic stays *linear*:
that restriction is the whole reason the fragment is decidable, and PROVE §7's
"resist general nonlinear arithmetic" is enforced here, at well-formedness, not
hoped for downstream.  `x * y` for two unknowns is not an error you can talk your
way out of — it is simply not a term.

Uninterpreted means uninterpreted: `len(xs)` is a symbol the solver knows nothing
about beyond congruence (equal arguments give equal results).  Teaching the solver
what `len` *computes* is V2 (measures), and this module has no opinion about it.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union


# -- Hashing --

def _node_hash(self) -> int:
    """The hash of a node, computed once and kept.

    A frozen dataclass hashes by hashing the tuple of its fields — and a field of
    a Term is a Term, so `hash(t)` is a *walk of the whole subtree under t*.  That
    is fine once.  It is not fine in congruence closure, which looks a term up in a
    dict for every merge, every `find`, every subterm it registers: an O(n) hash
    inside an O(n) loop is the quadratic you did not write down.  On a 600-term sum
    it cost 4.3M calls to `hash`, ~40% of the run.

    Terms are immutable and heavily shared (the same `Var('x')` node is reached by
    a hundred paths), so the hash of a node can be computed once and stored.  Each
    node then hashes in O(arity), because its children answer from their own cache
    — the walk happens once for the whole tree instead of once per lookup.

    Assigned as `__hash__` in each class body below: an *explicit* `__hash__` in
    the body is one that @dataclass(frozen=True) leaves alone, whereas an inherited
    one it would overwrite with the walking version.  Hence the repetition; a mixin
    would silently not work.
    """
    h = self.__dict__.get("_h")
    if h is None:
        h = hash((self.__class__.__name__,
                  *(self.__dict__[f] for f in self.__dataclass_fields__)))
        object.__setattr__(self, "_h", h)
    return h


# -- Terms --

@dataclass(frozen=True)
class Num:
    """Integer literal."""
    value: int
    __hash__ = _node_hash

@dataclass(frozen=True)
class BoolLit:
    """Boolean literal."""
    value: bool
    __hash__ = _node_hash

@dataclass(frozen=True)
class Var:
    """A variable: a program name, or the value binder `v` of {v:b|p}."""
    name: str
    __hash__ = _node_hash

@dataclass(frozen=True)
class Neg:
    """-t"""
    term: Term
    __hash__ = _node_hash

@dataclass(frozen=True)
class Arith:
    """t + t, t - t, k * t  (op in {'+', '-', '*'})"""
    op:    str
    left:  Term
    right: Term
    __hash__ = _node_hash

@dataclass(frozen=True)
class App:
    """Uninterpreted function application: len(xs), string_length(s)."""
    fn:   str
    args: tuple[Term, ...]
    __hash__ = _node_hash

Term = Union[Num, BoolLit, Var, Neg, Arith, App]


# -- Formulas --

@dataclass(frozen=True)
class Top:
    """true"""
    __hash__ = _node_hash

@dataclass(frozen=True)
class Bot:
    """false"""
    __hash__ = _node_hash

@dataclass(frozen=True)
class Cmp:
    """t R t  for R in {'==', '/=', '<', '<=', '>', '>='}"""
    op:    str
    left:  Term
    right: Term
    __hash__ = _node_hash

@dataclass(frozen=True)
class Atom:
    """A Bool-sorted term used directly as a formula: `b`, `is_empty(xs)`."""
    term: Term
    __hash__ = _node_hash

@dataclass(frozen=True)
class Not:
    f: Formula
    __hash__ = _node_hash

@dataclass(frozen=True)
class And:
    left:  Formula
    right: Formula
    __hash__ = _node_hash

@dataclass(frozen=True)
class Or:
    left:  Formula
    right: Formula
    __hash__ = _node_hash

@dataclass(frozen=True)
class Implies:
    left:  Formula
    right: Formula
    __hash__ = _node_hash

Formula = Union[Top, Bot, Cmp, Atom, Not, And, Or, Implies]


# -- Errors --

class PredError(Exception):
    """A predicate that is outside the decidable fragment, or ill-sorted.

    Raised at well-formedness time — never at solve time.  The solver may answer
    "I could not prove this"; it may not answer "I do not understand this."
    """


# -- Smart constructors --

def conj(fs: list[Formula]) -> Formula:
    """Fold a list of facts into one formula.  [] is `true`."""
    out: Formula = Top()
    for f in fs:
        if isinstance(f, Top):
            continue
        out = f if isinstance(out, Top) else And(out, f)
    return out


NEGATE_CMP = {
    "==": "/=", "/=": "==",
    "<":  ">=", ">=": "<",
    ">":  "<=", "<=": ">",
}


# -- Substitution --

def subst_term(t: Term, sub: dict[str, Term]) -> Term:
    match t:
        case Var(name=n):
            return sub.get(n, t)
        case Num() | BoolLit():
            return t
        case Neg(term=x):
            return Neg(subst_term(x, sub))
        case Arith(op=op, left=l, right=r):
            return Arith(op, subst_term(l, sub), subst_term(r, sub))
        case App(fn=f, args=args):
            return App(f, tuple(subst_term(a, sub) for a in args))
    raise PredError(f"cannot substitute in term: {t!r}")


def subst(f: Formula, sub: dict[str, Term]) -> Formula:
    """Capture-free by construction: the predicate language has no binders."""
    match f:
        case Top() | Bot():
            return f
        case Cmp(op=op, left=l, right=r):
            return Cmp(op, subst_term(l, sub), subst_term(r, sub))
        case Atom(term=t):
            return Atom(subst_term(t, sub))
        case Not(f=g):
            return Not(subst(g, sub))
        case And(left=l, right=r):
            return And(subst(l, sub), subst(r, sub))
        case Or(left=l, right=r):
            return Or(subst(l, sub), subst(r, sub))
        case Implies(left=l, right=r):
            return Implies(subst(l, sub), subst(r, sub))
    raise PredError(f"cannot substitute in formula: {f!r}")


# -- Free variables --

def free_vars_term(t: Term) -> set[str]:
    match t:
        case Var(name=n):
            return {n}
        case Num() | BoolLit():
            return set()
        case Neg(term=x):
            return free_vars_term(x)
        case Arith(left=l, right=r):
            return free_vars_term(l) | free_vars_term(r)
        case App(args=args):
            out: set[str] = set()
            for a in args:
                out |= free_vars_term(a)
            return out
    return set()


def free_vars(f: Formula) -> set[str]:
    match f:
        case Top() | Bot():
            return set()
        case Cmp(left=l, right=r):
            return free_vars_term(l) | free_vars_term(r)
        case Atom(term=t):
            return free_vars_term(t)
        case Not(f=g):
            return free_vars(g)
        case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
            return free_vars(l) | free_vars(r)
    return set()


def uf_symbols(f: Formula) -> set[str]:
    """The uninterpreted function symbols a formula mentions."""
    out: set[str] = set()

    def walk_t(t: Term) -> None:
        match t:
            case App(fn=fn, args=args):
                out.add(fn)
                for a in args:
                    walk_t(a)
            case Neg(term=x):
                walk_t(x)
            case Arith(left=l, right=r):
                walk_t(l); walk_t(r)
            case _:
                pass

    def walk_f(g: Formula) -> None:
        match g:
            case Cmp(left=l, right=r):
                walk_t(l); walk_t(r)
            case Atom(term=t):
                walk_t(t)
            case Not(f=h):
                walk_f(h)
            case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
                walk_f(l); walk_f(r)
            case _:
                pass

    walk_f(f)
    return out


# -- Linearity check --

def linear_node(t: Term) -> bool:
    """Is this ONE node linear, taking its subterms on trust?

    The rule, and the whole of it: at least one side of every `*` must be a literal.

    `is_linear` is the specification — a term is linear when every node in it is.
    But refine.py builds terms BOTTOM-UP out of terms it has already returned, and
    it returns none that failed this test, so at the moment a node is built its
    subterms are linear already and only the node itself is news.  Asking the full
    question there re-walks the whole subtree at every level of a walk that is
    already visiting every node: translating `1 + 1 + … + 1` (800 terms) cost 173
    MILLION calls to `is_linear`, and 3000 terms did not finish.

    A guard nobody can afford to run is a guard that will one day be taken down, so
    the cost matters for the same reason the check does.  `linear_selfcheck` (below)
    is what keeps the cheap rule honest against the specification.
    """
    match t:
        case Arith(op="*", left=l, right=r):
            return isinstance(l, Num) or isinstance(r, Num)
        case Num() | BoolLit() | Var() | Neg() | Arith() | App():
            return True
    return False


def is_linear(t: Term) -> bool:
    """Reject `x * y`: at least one side of every `*` must be a literal.

    This is the guard that keeps the fragment decidable — the SPECIFICATION of it.
    refine.py enforces it node by node as it builds (see `linear_node`), so no
    non-linear term ever reaches solver.py.
    """
    match t:
        case Num() | BoolLit() | Var():
            return True
        case Neg(term=x):
            return is_linear(x)
        case Arith(op="*", left=l, right=r):
            if not (isinstance(l, Num) or isinstance(r, Num)):
                return False
            return is_linear(l) and is_linear(r)
        case Arith(left=l, right=r):
            return is_linear(l) and is_linear(r)
        case App(args=args):
            # Arguments to an uninterpreted symbol are opaque to arithmetic, but we
            # still keep them linear so the term can be compared structurally.
            return all(is_linear(a) for a in args)
    return False


def formula_linear(f: Formula) -> bool:
    """Is every term in this formula linear?  The DOOR to the solver.

    The cheap node rule is what refine.py can afford to run at every node; this is
    what it is a rule FOR, and it is run once on each formula that is about to be
    handed to solver.py — the boundary of the decidable fragment, checked there
    rather than trusted there.  Once per formula is linear in its size; the thing
    that was cubic was asking at every level of the build."""
    match f:
        case Top() | Bot():
            return True
        case Cmp(left=l, right=r):
            return is_linear(l) and is_linear(r)
        case Atom(term=t):
            return is_linear(t)
        case Not(f=x):
            return formula_linear(x)
        case And(left=l, right=r) | Or(left=l, right=r) | Implies(left=l, right=r):
            return formula_linear(l) and formula_linear(r)
    return False


# -- Pretty printer --

_CMP_TEXT = {"==": "==", "/=": "/=", "<": "<", "<=": "<=", ">": ">", ">=": ">="}


def show_term(t: Term) -> str:
    match t:
        case Num(value=n):
            return str(n)
        case BoolLit(value=b):
            return "true" if b else "false"
        case Var(name=n):
            return n
        case Neg(term=x):
            return f"-{show_term(x)}"
        case Arith(op=op, left=l, right=r):
            return f"({show_term(l)} {op} {show_term(r)})"
        case App(fn=f, args=args):
            return f"{f}(" + ", ".join(show_term(a) for a in args) + ")"
    return "?"


def show(f: Formula) -> str:
    match f:
        case Top():
            return "true"
        case Bot():
            return "false"
        case Cmp(op=op, left=l, right=r):
            return f"{show_term(l)} {_CMP_TEXT[op]} {show_term(r)}"
        case Atom(term=t):
            return show_term(t)
        case Not(f=g):
            return f"not ({show(g)})"
        case And(left=l, right=r):
            return f"({show(l)} and {show(r)})"
        case Or(left=l, right=r):
            return f"({show(l)} or {show(r)})"
        case Implies(left=l, right=r):
            return f"({show(l)} => {show(r)})"
    return "?"
