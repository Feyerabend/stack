"""
Lark typed AST — produced by the type checker from the syntactic AST (tree.py).

Every expression node carries a monotype. The tree is otherwise isomorphic to
the syntactic tree; node names match for easy comparison.

The type checker takes a Program (tree.py) and produces a TProgram (typed_tree.py).
The CEK machine will evaluate the typed tree directly.

Naming: type-level objects (TVar, TCon, etc.) live in ty.py and are accessed via
the `ty` module alias to avoid name clashes with the expression-level nodes here.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass
from typing import Union
import ty


# ── Typed expressions ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TLit:
    value: object   # int | float | str | bool | None
    typ:   ty.Mono

@dataclass(frozen=True)
class TVar:
    """Typed variable reference."""
    name: str
    typ:  ty.Mono

@dataclass(frozen=True)
class TCon:
    """Typed constructor reference."""
    name: str
    typ:  ty.Mono

@dataclass(frozen=True)
class TTupleExpr:
    elems: tuple[TExpr, ...]
    typ:   ty.Mono

@dataclass(frozen=True)
class TApply:
    fn:   TExpr
    args: tuple[TExpr, ...]
    typ:  ty.Mono

@dataclass(frozen=True)
class TBinOp:
    op:    str
    left:  TExpr
    right: TExpr
    typ:   ty.Mono

@dataclass(frozen=True)
class TUnaryOp:
    op:      str
    operand: TExpr
    typ:     ty.Mono

@dataclass(frozen=True)
class TLetExpr:
    name:   str
    value:  TExpr
    body:   TExpr
    typ:    ty.Mono

@dataclass(frozen=True)
class TIfExpr:
    cond:  TExpr
    then_: TExpr
    else_: TExpr
    typ:   ty.Mono

@dataclass(frozen=True)
class TMatchExpr:
    scrutinee: TExpr
    arms:      tuple[tuple[TPat, TExpr], ...]
    typ:       ty.Mono

@dataclass(frozen=True)
class TLambda:
    params: tuple[tuple[str, ty.Mono], ...]  # (name, type) pairs
    body:   TExpr
    typ:    ty.Mono   # overall TFn type (curried)

TExpr = Union[
    TLit, TVar, TCon, TTupleExpr, TApply, TBinOp, TUnaryOp,
    TLetExpr, TIfExpr, TMatchExpr, TLambda,
]


# ── Typed patterns ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TPWild:
    typ: ty.Mono

@dataclass(frozen=True)
class TPVar:
    name: str
    typ:  ty.Mono

@dataclass(frozen=True)
class TPLit:
    value: object
    typ:   ty.Mono

@dataclass(frozen=True)
class TPCon:
    name: str
    args: tuple[TPat, ...]
    typ:  ty.Mono

@dataclass(frozen=True)
class TPTuple:
    elems: tuple[TPat, ...]
    typ:   ty.Mono

TPat = Union[TPWild, TPVar, TPLit, TPCon, TPTuple]


# ── Typed declarations ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TFnDecl:
    name:     str
    params:   tuple[tuple[str, ty.Mono], ...]
    body:     TExpr
    scheme:   ty.Scheme    # generalised type of the function
    exported: bool

@dataclass(frozen=True)
class TLetDecl:
    name:     str
    value:    TExpr
    scheme:   ty.Scheme
    exported: bool

@dataclass(frozen=True)
class TVariant:
    name:    str
    payload: tuple[ty.Mono, ...]   # field types (empty = nullary constructor)

@dataclass(frozen=True)
class TTypeDecl:
    name:     str
    params:   tuple[str, ...]
    variants: tuple[TVariant, ...] | None   # None = type alias
    exported: bool

TDecl = Union[TFnDecl, TLetDecl, TTypeDecl]


# ── Typed program ─────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TProgram:
    module: str
    decls:  tuple[TDecl, ...]
