"""
Loop-invariant code motion (LICM) — Chapter 8, §8.5.

A self-contained demonstration over a tiny three-address IR. A computation
inside a loop whose operands do not change from one iteration to the next is
*invariant*; LICM moves it to a "preheader" that runs once before the loop, so
it is computed once instead of once per iteration.

The analysis is the one the chapter describes:

  1. Collect the variables defined inside the loop body.
  2. An instruction is invariant if every operand is a literal, or a variable
     defined outside the loop, or itself defined by an invariant instruction.
     (The last clause needs a fixed point: an instruction can become invariant
     only after the ones it depends on are known to be.)
  3. Hoist the invariant instructions, in order, into the preheader.

Simplifying assumptions, stated honestly: the loop body is a single block in
which every instruction runs each iteration and each destination is assigned
exactly once. Under those conditions hoisting a pure invariant computation is
sound. A real pass must also check that the instruction dominates every loop
exit; here, a single straight-line body makes that automatic.

Run:  python3 licm.py
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Instr:
    dst: str
    op: str            # 'add' | 'sub' | 'mul' | 'lt'
    a: object          # operand: a variable name (str) or an int literal
    b: object

    def __str__(self) -> str:
        sym = {"add": "+", "sub": "-", "mul": "*", "lt": "<"}[self.op]
        return f"{self.dst} = {self.a} {sym} {self.b}"


def _invariant_operand(x, loop_defs: set[str], invariant: set[str]) -> bool:
    """An operand is invariant if it is a literal, defined outside the loop,
    or defined inside the loop by an instruction already known invariant."""
    if isinstance(x, int):
        return True                      # a literal never changes
    if x not in loop_defs:
        return True                      # defined before the loop; live-in
    return x in invariant                # defined in-loop, but by an invariant


def find_invariant(body: list[Instr]) -> set[str]:
    """Return the set of destinations whose defining instruction is loop-invariant."""
    loop_defs = {i.dst for i in body}
    invariant: set[str] = set()
    changed = True
    while changed:                       # fixed point
        changed = False
        for i in body:
            if i.dst in invariant or i.op == "lt":
                continue                 # the loop test is the back-edge condition; it stays
            if (_invariant_operand(i.a, loop_defs, invariant)
                    and _invariant_operand(i.b, loop_defs, invariant)):
                invariant.add(i.dst)
                changed = True
    return invariant


def hoist(preheader: list[Instr], body: list[Instr]):
    """Move invariant instructions from the body into the preheader, in order."""
    invariant = find_invariant(body)
    moved   = [i for i in body if i.dst in invariant]
    stayed  = [i for i in body if i.dst not in invariant]
    return preheader + moved, stayed, moved


def show(title: str, preheader: list[Instr], body: list[Instr]) -> None:
    print(title)
    for i in preheader:
        print(f"    {i}")
    print("  loop:")
    for i in body:
        print(f"      {i}")
    print("      if c goto loop")
    print()


if __name__ == "__main__":
    # A loop summing s += (a*b + 1) over n iterations.
    # a, b, n are live-in (defined before the loop); i and s are the induction
    # variable and accumulator. t1 = a*b and t2 = t1+1 do not change across
    # iterations -- they are invariant. t2 becomes known invariant only after
    # t1 does, which is what the fixed point is for.
    preheader = [
        Instr("i", "add", 0, 0),         # i = 0
        Instr("s", "add", 0, 0),         # s = 0
    ]
    body = [
        Instr("t1", "mul", "a", "b"),    # invariant
        Instr("t2", "add", "t1", 1),     # invariant (depends on t1)
        Instr("u",  "add", "s", "t2"),   # variant (uses s)
        Instr("s",  "add", "u", 0),      # variant (s changes each iteration)
        Instr("i",  "add", "i", 1),      # variant (induction variable)
        Instr("c",  "lt",  "i", "n"),    # the loop test -- stays
    ]

    show("BEFORE  (a, b, n live-in):", preheader, body)
    new_pre, new_body, moved = hoist(preheader, body)
    show("AFTER  loop-invariant code motion:", new_pre, new_body)

    print("Hoisted out of the loop:", ", ".join(i.dst for i in moved) or "(nothing)")
    print(f"Work removed per iteration: {len(moved)} instruction(s) "
          f"-> over n iterations, {len(moved)}*n fewer operations.")
