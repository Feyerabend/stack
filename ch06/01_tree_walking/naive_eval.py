"""
Naive tree-walking evaluator — Chapter 6, §6.1 "Tree-Walking Evaluation".

This is the design anyone would write first: one recursive function that walks
the typed AST and returns a value for each node. It is correct, short, and --
for a purely functional language -- fatally incomplete. A tail-recursive loop
nests one Python frame per Lark call and overflows the host stack long before
it finishes (the flaw §6.4 fixes by making control explicit).

It is *illustrative -- NOT Lark's actual interpreter*. Lark evaluates with the
CEK machine in `lark/04/src/cek.py`, which carries "what to do next" as data
and so gets proper tail calls for free. Run this file to watch the naive
evaluator succeed on a small program and then blow up on a deep tail recursion:

    python3 naive_eval.py

Self-contained: standard library only, no Lark import (the typed AST below is a
minimal hand-built subset of `lark`'s `typed_tree`, enough for §6.1's listing).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Union


# --- Typed AST: a minimal subset of Lark's typed tree -----------------------
# Each node mirrors one form of the language. Types have already been checked
# (Chapter 5); here they are irrelevant, so annotations are dropped.

@dataclass
class TLit:
    value: object                       # an int or a bool literal

@dataclass
class TVar:
    name: str

@dataclass
class TBinOp:
    op: str
    left: "TExpr"
    right: "TExpr"

@dataclass
class TIfExpr:
    cond: "TExpr"
    then_: "TExpr"
    else_: "TExpr"

@dataclass
class TLetExpr:
    name: str
    value: "TExpr"
    body: "TExpr"

@dataclass
class TLambda:
    params: tuple                       # ((name, type), ...); here single-param
    body: "TExpr"
    rec_name: str | None = None         # set for a self-recursive definition

@dataclass
class TApply:
    fn: "TExpr"
    args: tuple                         # single argument; multi-arg is curried

TExpr = Union[TLit, TVar, TBinOp, TIfExpr, TLetExpr, TLambda, TApply]


# --- Values: what expressions evaluate *to* ---------------------------------

@dataclass
class VInt:
    n: int

@dataclass
class VBool:
    b: bool

@dataclass
class VClosure:                         # a function value: code + captured env
    param: str
    body: "TExpr"
    env: dict
    rec_name: str | None = None

Value = Union[VInt, VBool, VClosure]


def _lit_val(v: object) -> Value:
    if isinstance(v, bool):             # bool before int: bool is a subclass
        return VBool(v)
    if isinstance(v, int):
        return VInt(v)
    raise TypeError(f"unsupported literal: {v!r}")


def binop(op: str, x: Value, y: Value) -> Value:
    if op == "+":
        return VInt(x.n + y.n)
    if op == "-":
        return VInt(x.n - y.n)
    if op == "*":
        return VInt(x.n * y.n)
    if op == "==":
        return VBool(x.n == y.n)
    raise ValueError(f"unknown operator: {op!r}")


# --- The naive evaluator (§6.1) ---------------------------------------------
# One recursive function. Each case mirrors one node of the typed tree, and the
# recursion mirrors the tree's structure exactly. Where Chapter 5's `infer`
# returned a type for each node, `eval` returns a value: the codomain changed,
# the shape did not.

def eval(e: TExpr, env: dict) -> Value:
    match e:
        case TLit(value=v):
            return _lit_val(v)
        case TVar(name=n):
            return env[n]
        case TBinOp(op=op, left=l, right=r):
            return binop(op, eval(l, env), eval(r, env))
        case TIfExpr(cond=c, then_=t, else_=f):
            return eval(t, env) if eval(c, env).b else eval(f, env)
        case TLetExpr(name=n, value=v, body=b):
            return eval(b, {**env, n: eval(v, env)})
        case TLambda(params=((p, _),), body=b, rec_name=rn):
            return VClosure(p, b, dict(env), rn)
        case TApply(fn=fn, args=(arg,)):
            f = eval(fn, env)
            a = eval(arg, env)
            call_env = {**f.env, f.param: a}
            if f.rec_name:                       # rebind self for recursion (§6.2)
                call_env[f.rec_name] = f
            return eval(f.body, call_env)        # <- fatal: one host frame per call
    raise NotImplementedError(type(e).__name__)


# --- Demo -------------------------------------------------------------------

def make_countdown(n: int) -> TExpr:
    """let countdown = fn(n) => if n == 0 then 0 else countdown(n - 1)
       in countdown(n)  -- a tail-recursive loop."""
    body = TIfExpr(
        TBinOp("==", TVar("n"), TLit(0)),
        TLit(0),
        TApply(TVar("countdown"), (TBinOp("-", TVar("n"), TLit(1)),)),
    )
    lam = TLambda((("n", None),), body, rec_name="countdown")
    return TLetExpr("countdown", lam, TApply(TVar("countdown"), (TLit(n),)))


if __name__ == "__main__":
    import sys

    # 1. Correct on a small program: let x = 2 + 3 in x * x  =>  25
    prog = TLetExpr("x",
                    TBinOp("+", TLit(2), TLit(3)),
                    TBinOp("*", TVar("x"), TVar("x")))
    print("let x = 2 + 3 in x * x   =>", eval(prog, {}))

    # 2. Correct on a shallow tail recursion.
    print("countdown(50)            =>", eval(make_countdown(50), {}))

    # 3. The fatal line. A tail call should run in constant stack, but the naive
    #    evaluator nests one Python frame per Lark call, so a deep loop overflows
    #    the host stack -- the failure that forces the CEK machine in §6.4.
    n = 100_000
    print(f"countdown({n})        =>", end=" ")
    try:
        print(eval(make_countdown(n), {}))
    except RecursionError:
        print(f"RecursionError (host limit {sys.getrecursionlimit()})")
        print("    A tail call, yet every Lark call became a Python call. Control was")
        print("    delegated to the host stack, and the host stack is finite.")
        print("    lark/04/src/cek.py runs the same loop in bounded continuation space.")
