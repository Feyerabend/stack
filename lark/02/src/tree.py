"""
Lark AST — syntactic (untyped) tree produced by the parser.
The type checker will produce a separate typed tree from this.

All nodes are frozen dataclasses matching the CEK reference style.
Collections use tuple (immutable); optional fields use | None.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union


# ── Types ─────────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TName:
    """Type name or variable: Int, Bool, a, b"""
    name: str

@dataclass(frozen=True)
class TApply:
    """Applied type constructor: List(Int), Result(a, b)"""
    name: str
    args: tuple[Type, ...]

@dataclass(frozen=True)
class TFn:
    """Function type: a -> b  (right-associative)"""
    param:  Type
    result: Type

@dataclass(frozen=True)
class TUnit:
    """Unit type: ()"""

@dataclass(frozen=True)
class TTuple:
    """Tuple type: (a, b, c)"""
    elems: tuple[Type, ...]

Type = Union[TName, TApply, TFn, TUnit, TTuple]


# ── Patterns ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PWild:
    """Wildcard: _"""

@dataclass(frozen=True)
class PVar:
    """Variable pattern: x"""
    name: str

@dataclass(frozen=True)
class PLit:
    """Literal pattern: 42, "hello", true, ()"""
    value: object   # int | float | str | bool | None

@dataclass(frozen=True)
class PCon:
    """Constructor pattern: Circle(r), Nil, Cons(x, rest)"""
    name: str
    args: tuple[Pat, ...]

@dataclass(frozen=True)
class PTuple:
    """Tuple pattern: (a, b)"""
    elems: tuple[Pat, ...]

Pat = Union[PWild, PVar, PLit, PCon, PTuple]


# ── Expressions ───────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Lit:
    """Literal: 42, 3.14, "hi", true, false, ()"""
    value: object   # int | float | str | bool | None

@dataclass(frozen=True)
class Var:
    """Variable reference: x, foo"""
    name: str

@dataclass(frozen=True)
class Con:
    """Constructor reference: Circle, Nil, Ok"""
    name: str

@dataclass(frozen=True)
class TupleExpr:
    """Tuple expression: (a, b, c)"""
    elems: tuple[Expr, ...]

@dataclass(frozen=True)
class Apply:
    """Application: f(x, y), Circle(5.0)"""
    fn:   Expr
    args: tuple[Expr, ...]

@dataclass(frozen=True)
class BinOp:
    """Binary operation: a + b, x == y"""
    op:    str
    left:  Expr
    right: Expr

@dataclass(frozen=True)
class UnaryOp:
    """Unary operation: -x, not b"""
    op:      str
    operand: Expr

@dataclass(frozen=True)
class LetExpr:
    """Local binding: let x [: t] = e in body"""
    name:  str
    ann:   Type | None
    value: Expr
    body:  Expr

@dataclass(frozen=True)
class IfExpr:
    """Conditional: if c then t else e"""
    cond:  Expr
    then_: Expr
    else_: Expr

@dataclass(frozen=True)
class MatchExpr:
    """Pattern match: match e with | p => e ... end"""
    scrutinee: Expr
    arms:      tuple[tuple[Pat, Expr], ...]

@dataclass(frozen=True)
class Lambda:
    """Anonymous function: fn (params) => body"""
    params: tuple[Param, ...]
    body:   Expr

Expr = Union[Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
             LetExpr, IfExpr, MatchExpr, Lambda]


# ── Supporting structures ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class Param:
    """Function parameter with optional type annotation"""
    name: str
    ann:  Type | None

@dataclass(frozen=True)
class Bound:
    """Trait bound in a function signature: Copy a, Show b"""
    trait: str
    var:   str

@dataclass(frozen=True)
class Variant:
    """ADT constructor declaration: | Circle of Float"""
    name:    str
    payload: Type | None   # None = no payload; TTuple = multiple fields

@dataclass(frozen=True)
class TraitMethod:
    """Method signature in a trait body: fn name : type"""
    name: str
    typ:  Type

@dataclass(frozen=True)
class ImplMethod:
    """Method definition in an impl body: fn name (params) = body"""
    name:   str
    params: tuple[Param, ...]
    body:   Expr


# ── Declarations ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FnDecl:
    name:        str
    bounds:      tuple[Bound, ...]
    params:      tuple[Param, ...]
    return_type: Type | None
    body:        Expr
    exported:    bool

@dataclass(frozen=True)
class LetDecl:
    name:     str
    ann:      Type | None
    value:    Expr
    exported: bool

@dataclass(frozen=True)
class TypeDecl:
    name:     str
    params:   tuple[str, ...]
    body:     Type | tuple[Variant, ...]   # alias or ADT
    exported: bool

@dataclass(frozen=True)
class TraitDecl:
    name:     str
    params:   tuple[str, ...]
    methods:  tuple[TraitMethod, ...]
    exported: bool

@dataclass(frozen=True)
class ImplDecl:
    trait_name: str
    trait_args: tuple[Type, ...]
    for_type:   Type
    methods:    tuple[ImplMethod, ...]

Decl = Union[FnDecl, LetDecl, TypeDecl, TraitDecl, ImplDecl]


# ── Program ───────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ImportDecl:
    module:   str
    exposing: tuple[str, ...] | None   # None = import whole module unqualified

@dataclass(frozen=True)
class Program:
    module:  str
    imports: tuple[ImportDecl, ...]
    decls:   tuple[Decl, ...]
