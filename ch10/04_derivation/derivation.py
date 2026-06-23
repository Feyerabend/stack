"""
From small-step semantics to the CEK machine — Chapter 10, §10.4.

The chapter claims the CEK machine is the operational semantics, derivable from
the small-step rules by *reifying the evaluation context as a continuation*.
This demo carries out that derivation on one small call-by-value language and
shows the two run the same program to the same answer.

  Stage 1 -- reduction semantics.  To take a step, DECOMPOSE the whole term into
  an evaluation context E and a redex, CONTRACT the redex, and PLUG the result
  back into E. Repeat. The context is rediscovered by re-traversing the term on
  every step.

  Stage 2 -- the CEK machine.  Carry the evaluation context as an explicit stack
  of frames (the continuation) instead of rediscovering it. Each *kind* of
  evaluation context becomes one *kind* of frame:

      context  [] e        <->  frame  AppFn(e)
      context  v  []        <->  frame  AppArg(v)
      context  [] + e       <->  frame  AddL(e)
      context  v  + []      <->  frame  AddR(v)

That table is the whole derivation. The machine does not approximate the
semantics; it is the same definition with the context turned into data.

Run:  python3 derivation.py
"""

from __future__ import annotations
from dataclasses import dataclass


# ── A small call-by-value language ────────────────────────────────────────────

@dataclass(frozen=True)
class Lit: n: int
@dataclass(frozen=True)
class Var: x: str
@dataclass(frozen=True)
class Lam: x: str; body: object
@dataclass(frozen=True)
class App: f: object; a: object
@dataclass(frozen=True)
class Add: l: object; r: object


def is_value(e) -> bool:
    return isinstance(e, (Lit, Lam))


def render(e) -> str:
    if isinstance(e, Lit): return str(e.n)
    if isinstance(e, Var): return e.x
    if isinstance(e, Lam): return f"(λ{e.x}. {render(e.body)})"
    if isinstance(e, App): return f"({render(e.f)} {render(e.a)})"
    if isinstance(e, Add): return f"({render(e.l)} + {render(e.r)})"


def subst(e, x, v):
    """Capture-avoiding only by convention: the demo uses distinct bound names."""
    if isinstance(e, Lit): return e
    if isinstance(e, Var): return v if e.x == x else e
    if isinstance(e, Lam): return e if e.x == x else Lam(e.x, subst(e.body, x, v))
    if isinstance(e, App): return App(subst(e.f, x, v), subst(e.a, x, v))
    if isinstance(e, Add): return Add(subst(e.l, x, v), subst(e.r, x, v))


def contract(redex):
    """The two reduction rules: beta and addition."""
    if isinstance(redex, App):                 # (\x. body) v  ->  body[x:=v]
        return subst(redex.f.body, redex.f.x, redex.a)
    if isinstance(redex, Add):                 # n1 + n2  ->  n
        return Lit(redex.l.n + redex.r.n)


# ── Stage 1: reduction semantics (decompose / contract / plug) ───────────────

def decompose(e):
    """Find the leftmost-outermost redex under call-by-value, left to right.
    Return (context, redex), where context is a function hole->term that plugs
    the result back, or (None, e) when e is already a value."""
    if is_value(e):
        return None, e
    if isinstance(e, App):
        if not is_value(e.f):
            ctx, redex = decompose(e.f)
            return (lambda h: App(ctx(h), e.a)), redex      # context  [] a
        if not is_value(e.a):
            ctx, redex = decompose(e.a)
            return (lambda h: App(e.f, ctx(h))), redex      # context  v  []
        return (lambda h: h), e                              # App(Lam, v): a redex
    if isinstance(e, Add):
        if not is_value(e.l):
            ctx, redex = decompose(e.l)
            return (lambda h: Add(ctx(h), e.r)), redex      # context  [] + r
        if not is_value(e.r):
            ctx, redex = decompose(e.r)
            return (lambda h: Add(e.l, ctx(h))), redex      # context  v  + []
        return (lambda h: h), e                              # Add(n, n): a redex
    raise ValueError(f"free variable or stuck term: {render(e)}")


def eval_reduction(e, trace):
    steps = 0
    while True:
        ctx, redex = decompose(e)
        if ctx is None:
            trace.append(f"  {render(e)}   (value)")
            return e, steps
        trace.append(f"  {render(e)}")
        e = ctx(contract(redex))
        steps += 1


# ── Stage 2: the CEK machine (context reified as a continuation) ─────────────

@dataclass(frozen=True)
class AppFn:  a: object        # context  [] a
@dataclass(frozen=True)
class AppArg: v: object        # context  v  []
@dataclass(frozen=True)
class AddL:   r: object        # context  [] + r
@dataclass(frozen=True)
class AddR:   v: object        # context  v  + []


def eval_cek(e, trace):
    state = ("eval", e, [])
    steps = 0
    while True:
        kind = state[0]
        if kind == "eval":
            _, ex, k = state
            trace.append(f"  eval   {render(ex):<14} {_kont(k)}")
            if is_value(ex):
                state = ("ret", ex, k)
            elif isinstance(ex, App):
                state = ("eval", ex.f, [AppFn(ex.a)] + k)
            elif isinstance(ex, Add):
                state = ("eval", ex.l, [AddL(ex.r)] + k)
            else:
                raise ValueError(f"stuck: {render(ex)}")
        else:  # ret
            _, v, k = state
            trace.append(f"  ret    {render(v):<14} {_kont(k)}")
            if not k:
                return v, steps
            top, rest = k[0], k[1:]
            if isinstance(top, AppFn):
                state = ("eval", top.a, [AppArg(v)] + rest)
            elif isinstance(top, AppArg):                    # top.v is the function
                state = ("eval", subst(top.v.body, top.v.x, v), rest)   # beta
            elif isinstance(top, AddL):
                state = ("eval", top.r, [AddR(v)] + rest)
            elif isinstance(top, AddR):
                state = ("ret", Lit(top.v.n + v.n), rest)    # addition
        steps += 1


def _kont(k) -> str:
    names = {AppFn: "[] a", AppArg: "v []", AddL: "[]+r", AddR: "v+[]"}
    return "k=[" + ", ".join(names[type(f)] for f in k) + "]"


if __name__ == "__main__":
    # ((\x. x + x) (1 + 2))
    expr = App(Lam("x", Add(Var("x"), Var("x"))), Add(Lit(1), Lit(2)))
    print(f"expression: {render(expr)}\n")

    t1 = []
    v1, s1 = eval_reduction(expr, t1)
    print(f"Stage 1 -- reduction semantics ({s1} steps, re-decomposing each time):")
    print("\n".join(t1))

    print()
    t2 = []
    v2, s2 = eval_cek(expr, t2)
    print(f"Stage 2 -- CEK machine ({s2} steps, context carried as continuation):")
    print("\n".join(t2))

    print(f"\nSame answer: {render(v1)} == {render(v2)}  ->  {render(v1) == render(v2)}")
    print("Each evaluation context of Stage 1 is one frame of the continuation in")
    print("Stage 2: [] a -> AppFn,  v [] -> AppArg,  []+r -> AddL,  v+[] -> AddR.")
