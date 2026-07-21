"""
Lark AST — syntactic (untyped) tree produced by the parser.
The type checker will produce a separate typed tree from this.

All nodes are frozen dataclasses matching the CEK reference style.
Collections use tuple (immutable); optional fields use | None.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Union


# -- Types --

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

@dataclass(frozen=True)
class TRefine:
    """Refinement type: { v : Int | v >= 0 }   (PROVE.md, the 08/ fork)

    `base` is the underlying type, `var` the value binder, `pred` the predicate
    the value must satisfy.  The predicate is an ordinary Lark expression node —
    it is turned into the decidable predicate language by refine.py, which is the
    only module that reads this field.

    Refinements ERASE: syntype_to_mono maps TRefine(v, b, p) to the monotype of b
    and drops p, so the HM core and the affine checker never see a predicate.
    That erasure is what makes a predicate a *mention* and not a *use* — see the
    affine × refinement rule in refine.py's header.
    """
    var:  str
    base: Type
    pred: object          # tree.Expr — typed as object to avoid a forward cycle

Type = Union[TName, TApply, TFn, TUnit, TTuple, TRefine]


# -- Patterns --

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


# -- Expressions --

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


# -- Supporting structures --

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
    """ADT constructor declaration.

    payload is a tuple of field types:
      ()          — nullary:  | Nil
      (Float,)    — unary:    | Circle of Float
      (Float, Float) — binary curried: | Rect of Float, Float
    This lets the type checker build the correct curried constructor type.
    """
    name:    str
    payload: tuple[Type, ...]

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


# -- Declarations --

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


@dataclass(frozen=True)
class MeasureDecl:
    """A ghost measure  (PROVE.md V2.1, the 08/ fork):

        measure len(xs : List(a)) : Int =
          match xs with
          | Nil          => 0
          | Cons(_, rest) => 1 + len(rest)
          end

    It is NOT an `fn`, and it is deliberately NOT a member of `Decl`.  Three
    restrictions an ordinary function does not carry:

      GHOST       — it erases, as a refinement does, and the erasure is *by
                    construction*: measures live in `Program.measures`, never in
                    `Program.decls`, so infer.py and the CEK machine never see one.
                    A measure therefore has no runtime existence to erase, and —
                    the corollary that comes free — calling one from real code is
                    an unbound-name error from HM, not a special rule anyone wrote.
      STRUCTURAL  — one arm per constructor, recursion only on the fields of the
                    constructor matched.  This is a soundness side condition, not
                    style: a measure's arms become AXIOMS, and a non-terminating
                    axiom set proves everything.
      IN-FRAGMENT — an arm body must be a predicate-language expression, because
                    it becomes one.

    Were measures just functions we would owe the reader an account of why some
    `fn`s may appear in a predicate and others may not, and there is not a good one.
    refine.py checks all three (`Refiner._elab_measure`); the parser only shapes it.
    """
    name:        str
    params:      tuple[Param, ...]   # params[0] is the structural argument
    return_type: Type                # mandatory: the logic needs the sort
    body:        Expr                # a match on params[0]


# -- Program --

@dataclass(frozen=True)
class ImportDecl:
    module:   str
    exposing: tuple[str, ...] | None   # None = import whole module unqualified

@dataclass(frozen=True)
class Program:
    module:  str
    imports: tuple[ImportDecl, ...]
    decls:   tuple[Decl, ...]
    # Ghost declarations, kept OUT of `decls` on purpose — that is the erasure
    # (see MeasureDecl).  Defaulted, so every existing `Program(m, i, d)` in the
    # tree still builds the program it always built.
    measures: tuple[MeasureDecl, ...] = ()
