"""
Lark type representation — monotypes, polytypes, substitutions, unification.

Separate from tree.py (syntactic types) because the type checker uses a richer
internal representation: type variables are integers, not strings, and the occurs
check and unification are defined here.

Monotype grammar:
    τ ::= α           — type variable (TVar)
        | C           — nullary type constructor (TCon)
        | C(τ, …)     — applied type constructor (TApp)
        | τ → τ       — function type (TFn)
        | (τ, …)      — tuple type (TTup)

Polytype (type scheme):
    σ ::= ∀α₁…αₙ. τ  — quantified variables may carry Copy constraint

The only polymorphism in Lark is let-polymorphism (Hindley-Milner). Function
parameters are monomorphic at the call site; let bindings are generalised.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union


# -- Monotypes --

@dataclass(frozen=True)
class TVar:
    """Unification variable: α₁, α₂, …"""
    id: int

@dataclass(frozen=True)
class TCon:
    """Nullary type constructor: Int, Bool, String, Float, IO, ()"""
    name: str

@dataclass(frozen=True)
class TApp:
    """Applied type constructor: List(Int), Result(a, b), Maybe(a)"""
    head: str
    args: tuple[Mono, ...]

@dataclass(frozen=True)
class TFn:
    """Function type: τ₁ → τ₂"""
    param:  Mono
    result: Mono

@dataclass(frozen=True)
class TTup:
    """Tuple type: (τ₁, τ₂, …)"""
    elems: tuple[Mono, ...]

Mono = Union[TVar, TCon, TApp, TFn, TTup]


# -- Polytype (scheme) --

@dataclass(frozen=True)
class Scheme:
    """∀qs. body — quantified type variables, with optional Copy constraints.

    copy_vars: subset of qs that must implement Copy at instantiation.
    """
    qs:        tuple[int, ...]  # bound TVar ids
    body:      Mono
    copy_vars: frozenset[int] = field(default_factory=frozenset)

    def is_mono(self) -> bool:
        return len(self.qs) == 0


# -- Fresh variable supply --

class Fresh:
    """Monotonically increasing type variable counter."""
    def __init__(self) -> None:
        self._n = 0

    def var(self) -> TVar:
        v = TVar(self._n)
        self._n += 1
        return v

    def next_id(self) -> int:
        v = self._n
        self._n += 1
        return v


# -- Substitution --

Subst = dict[int, Mono]   # TVar.id → Mono


def apply(s: Subst, t: Mono) -> Mono:
    """Apply substitution s to monotype t."""
    match t:
        case TVar(id=i):
            if i in s:
                return apply(s, s[i])
            return t
        case TCon():
            return t
        case TApp(head=h, args=args):
            return TApp(h, tuple(apply(s, a) for a in args))
        case TFn(param=p, result=r):
            return TFn(apply(s, p), apply(s, r))
        case TTup(elems=elems):
            return TTup(tuple(apply(s, e) for e in elems))


def apply_scheme(s: Subst, sc: Scheme) -> Scheme:
    # Don't substitute bound variables
    s2 = {k: v for k, v in s.items() if k not in sc.qs}
    return Scheme(sc.qs, apply(s2, sc.body), sc.copy_vars)


def compose(s1: Subst, s2: Subst) -> Subst:
    """Return s1 ∘ s2 — apply s1 to the range of s2, then union."""
    result = {k: apply(s1, v) for k, v in s2.items()}
    result.update(s1)
    return result


def free_vars(t: Mono) -> set[int]:
    """Free type variable ids in monotype t."""
    match t:
        case TVar(id=i):
            return {i}
        case TCon():
            return set()
        case TApp(args=args):
            return set().union(*(free_vars(a) for a in args))
        case TFn(param=p, result=r):
            return free_vars(p) | free_vars(r)
        case TTup(elems=elems):
            return set().union(*(free_vars(e) for e in elems))


def free_vars_scheme(sc: Scheme) -> set[int]:
    return free_vars(sc.body) - set(sc.qs)


# -- Unification --

class UnifyError(Exception):
    def __init__(self, a: Mono, b: Mono, reason: str = "") -> None:
        self.a = a
        self.b = b
        msg = f"cannot unify {pretty(a)} with {pretty(b)}"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


def unify(a: Mono, b: Mono) -> Subst:
    """Most general unifier of a and b.  Raises UnifyError on failure."""
    a2 = a  # no lazy apply here; caller resolves vars before calling
    b2 = b
    match (a2, b2):
        case (TVar(id=i), TVar(id=j)) if i == j:
            return {}
        case (TVar(id=i), _):
            return _bind(i, b2)
        case (_, TVar(id=j)):
            return _bind(j, a2)
        case (TCon(name=n1), TCon(name=n2)) if n1 == n2:
            return {}
        case (TApp(head=h1, args=as1), TApp(head=h2, args=as2)) if h1 == h2:
            return _unify_seq(as1, as2, a2, b2)
        case (TFn(param=p1, result=r1), TFn(param=p2, result=r2)):
            s1 = unify(p1, p2)
            s2 = unify(apply(s1, r1), apply(s1, r2))
            return compose(s2, s1)
        case (TTup(elems=es1), TTup(elems=es2)):
            return _unify_seq(es1, es2, a2, b2)
        case _:
            raise UnifyError(a2, b2)


def _bind(i: int, t: Mono) -> Subst:
    if isinstance(t, TVar) and t.id == i:
        return {}
    if i in free_vars(t):
        raise UnifyError(TVar(i), t, "occurs check failed")
    return {i: t}


def _unify_seq(
    xs: tuple[Mono, ...], ys: tuple[Mono, ...], a: Mono, b: Mono
) -> Subst:
    if len(xs) != len(ys):
        raise UnifyError(a, b, f"arity mismatch ({len(xs)} vs {len(ys)})")
    s: Subst = {}
    for x, y in zip(xs, ys):
        s = compose(unify(apply(s, x), apply(s, y)), s)
    return s


# -- Pretty printer --

def pretty(t: Mono, *, paren: bool = False) -> str:
    result = _pretty_inner(t)
    if paren and isinstance(t, TFn):
        return f"({result})"
    return result


def _pretty_inner(t: Mono) -> str:
    match t:
        case TVar(id=i):
            # Display as Greek letter for small ids, α_N for large
            letters = "αβγδεζηθικλμνξοπρστυφχψω"
            return letters[i] if i < len(letters) else f"α{i}"
        case TCon(name=n):
            return n
        case TApp(head=h, args=args):
            if not args:
                return h
            return h + "(" + ", ".join(pretty(a) for a in args) + ")"
        case TFn(param=p, result=r):
            return pretty(p, paren=True) + " -> " + pretty(r)
        case TTup(elems=elems):
            return "(" + ", ".join(pretty(e) for e in elems) + ")"


# -- Built-in types --

T_INT    = TCon("Int")
T_FLOAT  = TCon("Float")
T_BOOL   = TCon("Bool")
T_STRING = TCon("String")
T_UNIT   = TCon("()")
T_IO     = TCon("IO")

def t_list(a: Mono) -> Mono:
    return TApp("List", (a,))

def t_result(a: Mono, b: Mono) -> Mono:
    return TApp("Result", (a, b))

def t_tuple(*elems: Mono) -> Mono:
    return TTup(elems)

def t_fn(*types: Mono) -> Mono:
    """Build a curried function type from two or more types."""
    assert len(types) >= 2
    result = types[-1]
    for t in reversed(types[:-1]):
        result = TFn(t, result)
    return result


# -- Copy-able types --
# A set of type constructor names whose values are freely copyable.
# User types can be added at type-check time when `impl Copy for T` is seen.

BUILTIN_COPY: frozenset[str] = frozenset({
    "Int", "Float", "Bool", "String", "()",
    # Tuples and List are Copy iff all their element types are Copy;
    # that structural rule is checked in the type checker, not here.
})
