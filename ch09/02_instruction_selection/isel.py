"""
Instruction selection — Chapter 9, §9.2.

The principled technique is *tree matching*: the machine's instructions are tree
patterns ("tiles") with costs, and the selector covers the expression tree with
the cheapest tiles that fit. The greedy version -- at each node, take the largest
tile that matches, then recurse on its leaves -- is *maximal munch*.

This demo tiles small expression trees with a RISC-V-flavoured tile set. The
interesting tiles fold structure that a naive one-instruction-per-node selector
would spend several instructions on: an addition by a constant becomes `addi`,
and a load from base-plus-constant becomes a single `lw off(base)`.

Run:  python3 isel.py
"""

from __future__ import annotations
from dataclasses import dataclass
import itertools

_n = itertools.count()
def fresh() -> str:
    return f"t{next(_n)}"


# ── Expression trees ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Var:   name: str
@dataclass(frozen=True)
class Const: value: int
@dataclass(frozen=True)
class Add:   l: object; r: object
@dataclass(frozen=True)
class Mul:   l: object; r: object
@dataclass(frozen=True)
class Load:  addr: object        # load a word from a computed address


def render(e) -> str:
    if isinstance(e, Var):   return e.name
    if isinstance(e, Const): return str(e.value)
    if isinstance(e, Add):   return f"({render(e.l)} + {render(e.r)})"
    if isinstance(e, Mul):   return f"({render(e.l)} * {render(e.r)})"
    if isinstance(e, Load):  return f"mem[{render(e.addr)}]"


# ── Naive selection: one instruction per operator node ───────────────────────

def select_naive(e, out: list[str]) -> str:
    if isinstance(e, Var):
        return e.name
    if isinstance(e, Const):
        d = fresh(); out.append(f"li   {d}, {e.value}"); return d
    if isinstance(e, Add):
        a, b = select_naive(e.l, out), select_naive(e.r, out)
        d = fresh(); out.append(f"add  {d}, {a}, {b}"); return d
    if isinstance(e, Mul):
        a, b = select_naive(e.l, out), select_naive(e.r, out)
        d = fresh(); out.append(f"mul  {d}, {a}, {b}"); return d
    if isinstance(e, Load):
        a = select_naive(e.addr, out)
        d = fresh(); out.append(f"lw   {d}, 0({a})"); return d


# ── Maximal munch: take the largest matching tile at each node ───────────────

def select_munch(e, out: list[str]) -> str:
    # Tile: load of base + constant  ->  lw off(base)   (covers Load, Add, Const)
    if isinstance(e, Load) and isinstance(e.addr, Add) and isinstance(e.addr.r, Const):
        base = select_munch(e.addr.l, out)
        d = fresh(); out.append(f"lw   {d}, {e.addr.r.value}({base})"); return d
    # Tile: x + constant  ->  addi                       (covers Add, Const)
    if isinstance(e, Add) and isinstance(e.r, Const):
        a = select_munch(e.l, out)
        d = fresh(); out.append(f"addi {d}, {a}, {e.r.value}"); return d
    # Fall back to the small tiles, recursing on children.
    if isinstance(e, Var):
        return e.name
    if isinstance(e, Const):
        d = fresh(); out.append(f"li   {d}, {e.value}"); return d
    if isinstance(e, Add):
        a, b = select_munch(e.l, out), select_munch(e.r, out)
        d = fresh(); out.append(f"add  {d}, {a}, {b}"); return d
    if isinstance(e, Mul):
        a, b = select_munch(e.l, out), select_munch(e.r, out)
        d = fresh(); out.append(f"mul  {d}, {a}, {b}"); return d
    if isinstance(e, Load):
        a = select_munch(e.addr, out)
        d = fresh(); out.append(f"lw   {d}, 0({a})"); return d


if __name__ == "__main__":
    examples = [
        Load(Add(Var("a"), Const(8))),         # mem[a + 8]
        Add(Mul(Var("b"), Var("c")), Const(1)),# b*c + 1
        Add(Var("x"), Const(16)),              # x + 16
    ]
    for e in examples:
        print(f"expression: {render(e)}")
        naive: list[str] = []; select_naive(e, naive)
        munch: list[str] = []; select_munch(e, munch)
        print(f"  naive  ({len(naive)} instr):")
        for i in naive: print(f"      {i}")
        print(f"  maximal munch ({len(munch)} instr):")
        for i in munch: print(f"      {i}")
        print()
