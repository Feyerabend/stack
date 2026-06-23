"""
The 6502 as contrast — Chapter 9, §9.5.

The same expression compiled two ways: for RISC-V, where thirty-two registers
hold every intermediate, and for the 6502, where the single accumulator forces
every intermediate out to the zero page (the fast first 256 bytes of memory)
and back. The demo compiles the expression Chapter 1 used to count live values,
(a * b) + (c * d), and counts the memory accesses each target pays.

The 6502 has no multiply instruction, so a multiply is a subroutine call -- a
further reminder that an instruction set, not the compiler, sets the floor on
what code generation can achieve.

Run:  python3 codegen6502.py
"""

from __future__ import annotations
from dataclasses import dataclass
import itertools


@dataclass(frozen=True)
class Var: name: str
@dataclass(frozen=True)
class Add: l: object; r: object
@dataclass(frozen=True)
class Mul: l: object; r: object


def render(e) -> str:
    if isinstance(e, Var): return e.name
    op = "+" if isinstance(e, Add) else "*"
    return f"({render(e.l)} {op} {render(e.r)})"


# ── 6502: accumulator + zero-page temporaries ────────────────────────────────

class Gen6502:
    def __init__(self):
        self.out: list[str] = []
        self.mem = 0                       # memory accesses (zero-page loads/stores)
        self._t = itertools.count()

    def temp(self) -> str:
        return f"zp_t{next(self._t)}"

    def gen(self, e) -> str:
        if isinstance(e, Var):
            return e.name                  # already a zero-page location
        lx, ly = self.gen(e.l), self.gen(e.r)
        t = self.temp()
        if isinstance(e, Add):
            self.out += [f"LDA {lx}", "CLC", f"ADC {ly}", f"STA {t}"]
            self.mem += 3                  # LDA, ADC operand, STA all touch memory
        else:  # Mul -> subroutine (no hardware multiply)
            self.out += [f"LDA {lx}", "STA mula", f"LDA {ly}", "STA mulb",
                         "JSR mul", f"STA {t}"]
            self.mem += 5                  # 4 loads/stores + the result store
        return t


# ── RISC-V: registers only ───────────────────────────────────────────────────

class GenRV:
    def __init__(self):
        self.out: list[str] = []
        self.mem = 0
        self._r = itertools.count()

    def reg(self) -> str:
        return f"t{next(self._r)}"

    def gen(self, e) -> str:
        if isinstance(e, Var):
            return e.name                  # already in a register
        a, b = self.gen(e.l), self.gen(e.r)
        d = self.reg()
        op = "add" if isinstance(e, Add) else "mul"
        self.out.append(f"{op:<4} {d}, {a}, {b}")
        return d                           # no memory touched


if __name__ == "__main__":
    expr = Add(Mul(Var("a"), Var("b")), Mul(Var("c"), Var("d")))
    print(f"expression: {render(expr)}   (Chapter 1's live-value example)\n")

    g6 = Gen6502(); g6.gen(expr)
    print(f"6502  (accumulator + zero page) -- {g6.mem} memory accesses:")
    for i in g6.out: print(f"      {i}")

    grv = GenRV(); grv.gen(expr)
    print(f"\nRISC-V  (registers only) -- {grv.mem} memory accesses:")
    for i in grv.out: print(f"      {i}")

    print(f"\nThe 6502 spends {g6.mem} memory accesses where RISC-V spends "
          f"{grv.mem}. With one")
    print("usable arithmetic register, every intermediate must live in memory;")
    print("with thirty-two, none need to. The instruction set sets the floor.")
