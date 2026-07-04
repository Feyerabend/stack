"""
Lark exhaustiveness checking — Maranget's pattern-matrix usefulness algorithm.

A match expression is exhaustive iff a wildcard row is NOT useful with respect
to the matrix formed by its arm patterns: every value is already covered by
some arm.  When the wildcard row IS useful, the recursion that establishes
usefulness doubles as a constructive proof — it builds a witness pattern
describing a value no arm matches, which becomes the error message.

Reference: Luc Maranget, "Warnings for pattern matching", JFP 17(3), 2007.

The check runs as a post-pass over the fully-substituted typed AST (the same
shape as the Show-bound check in infer.py), so every scrutinee carries its
final inferred type.  Column types drive the notion of a *complete signature*:

    Bool           — the two literals True and False
    ()             — the single literal ()
    (t1, …, tn)    — the single n-tuple constructor
    declared ADTs  — the constructor list from the type declaration
    Int, Float, String — no finite signature; only a wildcard/variable closes
    IO, functions, type variables — opaque; only a wildcard/variable closes

Entry points:
    ExhaustivenessError                — raised with a witness pattern
    check_texpr(expr, env, sigs, fresh) — walk one typed expression
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from ty import (
    Mono, TVar, TCon, TApp, TFn, TTup,
    apply, unify, UnifyError, Fresh,
    T_BOOL, T_UNIT,
)
from typed_tree import (
    TExpr, TLit, TVar as XVar, TCon as XCon, TTupleExpr, TApply as XApply,
    TBinOp, TUnaryOp, TLetExpr, TIfExpr, TMatchExpr, TLambda,
    TPat, TPWild, TPVar, TPLit, TPCon, TPTuple,
)

# Constructor signatures: type head name -> tuple of constructor names.
# Populated from type declarations in infer.typecheck; these are the builtins.
BUILTIN_SIGS: dict[str, tuple[str, ...]] = {
    "List":   ("Nil", "Cons"),
    "Result": ("Ok", "Err"),
}


class ExhaustivenessError(Exception):
    def __init__(self, witness: str) -> None:
        self.witness = witness
        super().__init__(f"non-exhaustive match: pattern {witness!r} not covered")


# -- Pattern heads --
#
# A head is a hashable key identifying the outermost constructor of a pattern,
# or None for a wildcard/variable.  Literal keys carry the value's type name
# so e.g. 1 and True can never collide.

def _head(p: TPat):
    match p:
        case TPWild() | TPVar():
            return None
        case TPLit(value=v):
            return ("lit", type(v).__name__, v)
        case TPCon(name=n, args=args):
            # True/False may be written as constructor patterns; normalise
            # them to Bool literals so both spellings count toward the
            # {True, False} signature.
            if n in ("True", "False") and not args:
                return ("lit", "bool", n == "True")
            return ("con", n)
        case TPTuple(elems=elems):
            return ("tup", len(elems))


def _sub_pats(p: TPat, arity: int) -> list[TPat]:
    """Sub-patterns of p when specialising by p's own head."""
    match p:
        case TPCon(args=args):
            return list(args)
        case TPTuple(elems=elems):
            return list(elems)
        case _:
            return []


# -- Column types --

def _ctor_field_types(
    cname: str, col_t: Mono, env: dict, fresh: Fresh,
) -> list[Mono]:
    """Field types of constructor cname when its result is col_t.

    Instantiates the constructor's scheme and unifies the result type with the
    column type, so e.g. Cons at column List(Int) yields [Int, List(Int)].
    """
    sc = env.get(cname)
    if sc is None:
        return []
    # Local import to avoid a cycle (infer imports this module).
    from infer import instantiate
    t = instantiate(fresh, sc)
    fields: list[Mono] = []
    while isinstance(t, TFn):
        fields.append(t.param)
        t = t.result
    try:
        s = unify(t, col_t)
    except UnifyError:
        s = {}
    return [apply(s, f) for f in fields]


def _complete_sig(
    col_t: Mono, sigs: dict[str, tuple[str, ...]],
) -> "list[tuple] | None":
    """The complete list of head keys for a column type, or None when the
    type has no finite signature (Int, String, IO, functions, type vars)."""
    match col_t:
        case TCon(name="Bool"):
            return [("lit", "bool", True), ("lit", "bool", False)]
        case TCon(name="()"):
            return [("lit", "NoneType", None)]
        case TCon(name=n) if n in sigs:
            return [("con", c) for c in sigs[n]]
        case TApp(head=h) if h in sigs:
            return [("con", c) for c in sigs[h]]
        case TTup(elems=elems):
            return [("tup", len(elems))]
        case _:
            return None


def _key_arity_fields(
    key, col_t: Mono, env: dict, fresh: Fresh,
) -> tuple[int, list[Mono]]:
    """Arity and column types introduced by specialising on head key."""
    match key:
        case ("con", n):
            fields = _ctor_field_types(n, col_t, env, fresh)
            return len(fields), fields
        case ("tup", k):
            if isinstance(col_t, TTup) and len(col_t.elems) == k:
                return k, list(col_t.elems)
            return k, [fresh.var() for _ in range(k)]
        case _:   # literal
            return 0, []


# -- The matrix recursion --

def _specialize(matrix: list[list[TPat]], key, arity: int) -> list[list[TPat]]:
    """Maranget's S(c, P): keep rows whose first pattern is head c (expanding
    its sub-patterns) or a wildcard (padding with wildcards); drop the rest."""
    out: list[list[TPat]] = []
    for row in matrix:
        h = _head(row[0])
        if h is None:
            out.append([TPWild(None)] * arity + row[1:])
        elif h == key:
            out.append(_sub_pats(row[0], arity) + row[1:])
    return out


def _default(matrix: list[list[TPat]]) -> list[list[TPat]]:
    """Maranget's D(P): rows whose first pattern is a wildcard, first column
    removed."""
    return [row[1:] for row in matrix if _head(row[0]) is None]


def _fmt_head(key, args: list[str]) -> str:
    match key:
        case ("con", n):
            return f"{n}({', '.join(args)})" if args else n
        case ("tup", _):
            return "(" + ", ".join(args) + ")"
        case ("lit", "bool", v):
            return "True" if v else "False"
        case ("lit", "NoneType", _):
            return "()"
        case ("lit", _, v):
            return repr(v) if isinstance(v, str) else str(v)


def _missing_witness(col_t, sig, present: set, matrix, env, fresh) -> str:
    """A pattern for the first column that no row's head covers."""
    if sig is not None:
        for key in sig:
            if key not in present:
                arity, _ = _key_arity_fields(key, col_t, env, fresh)
                return _fmt_head(key, ["_"] * arity)
    # No finite signature: pick a concrete unmatched Int when we can, else _.
    if isinstance(col_t, TCon) and col_t.name == "Int":
        used = {k[2] for k in present if isinstance(k, tuple) and k[0] == "lit"}
        n = 0
        while n in used:
            n += 1
        return str(n)
    return "_"


def _witness(
    matrix: list[list[TPat]],
    types: list[Mono],
    env: dict,
    sigs: dict[str, tuple[str, ...]],
    fresh: Fresh,
) -> "list[str] | None":
    """A vector of witness patterns matched by no row, or None if the matrix
    is exhaustive.  len(types) is the column count; rows must agree."""
    if not types:
        return None if matrix else []

    col_t = types[0]
    present = {h for h in (_head(row[0]) for row in matrix) if h is not None}
    sig = _complete_sig(col_t, sigs)

    if sig is not None and all(key in present for key in sig):
        # Complete signature: some constructor must expose a hole, if any.
        for key in sig:
            arity, fields = _key_arity_fields(key, col_t, env, fresh)
            sub = _specialize(matrix, key, arity)
            w = _witness(sub, fields + types[1:], env, sigs, fresh)
            if w is not None:
                return [_fmt_head(key, w[:arity])] + w[arity:]
        return None

    # Incomplete signature: a value with an unused head slips past every
    # constructor row, so only the wildcard rows matter.
    w = _witness(_default(matrix), types[1:], env, sigs, fresh)
    if w is None:
        return None
    return [_missing_witness(col_t, sig, present, matrix, env, fresh)] + w


def check_match(
    arm_pats: list[TPat], scrut_t: Mono,
    env: dict, sigs: dict[str, tuple[str, ...]], fresh: Fresh,
) -> None:
    """Raise ExhaustivenessError if the arms do not cover scrut_t."""
    w = _witness([[p] for p in arm_pats], [scrut_t], env, sigs, fresh)
    if w is not None:
        raise ExhaustivenessError(w[0])


# -- Typed-AST walk --

def check_texpr(
    expr: TExpr, env: dict, sigs: dict[str, tuple[str, ...]], fresh: Fresh,
) -> None:
    """Walk a substitution-applied typed expression and check every match."""
    match expr:
        case TMatchExpr(scrutinee=s, arms=arms):
            check_match([p for p, _ in arms], s.typ, env, sigs, fresh)
            check_texpr(s, env, sigs, fresh)
            for _, body in arms:
                check_texpr(body, env, sigs, fresh)
        case TTupleExpr(elems=elems):
            for e in elems:
                check_texpr(e, env, sigs, fresh)
        case XApply(fn=fn, args=args):
            check_texpr(fn, env, sigs, fresh)
            for a in args:
                check_texpr(a, env, sigs, fresh)
        case TBinOp(left=l, right=r):
            check_texpr(l, env, sigs, fresh)
            check_texpr(r, env, sigs, fresh)
        case TUnaryOp(operand=o):
            check_texpr(o, env, sigs, fresh)
        case TLetExpr(value=v, body=b):
            check_texpr(v, env, sigs, fresh)
            check_texpr(b, env, sigs, fresh)
        case TIfExpr(cond=c, then_=t, else_=e):
            check_texpr(c, env, sigs, fresh)
            check_texpr(t, env, sigs, fresh)
            check_texpr(e, env, sigs, fresh)
        case TLambda(body=b):
            check_texpr(b, env, sigs, fresh)
        case _:
            pass  # TLit, TVar, TCon — no sub-expressions
