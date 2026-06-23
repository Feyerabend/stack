"""
Chapter 2, Exercise 1 — solution code.

Add a MOD instruction (pop b, pop a, push a % b) to the stack VM. Give its
opcode number, the dispatch branch that implements it, and the entry it needs
in the assembler's WIDTHS table.

How to run:   python3 ex01_mod.py
Expected:     "17 % 5 = 2  (assembled, MOD width accounted for)"

The three additions are exactly:
  1. opcode number .... MOD = 15  (the next free value after RET = 14 in the
     base 15-instruction VM; the LOADK/JMPIND extensions in the chapter repo
     are separate VMs that happen to reuse 15/16, so a unified VM would renumber)
  2. dispatch branch ... see MODStackVM.run below
  3. WIDTHS entry ...... 15: 1   (MOD takes no operand byte, so width 1)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stack_vm import (  # noqa: E402
    StackVM, HALT, PUSH, ADD, SUB, MUL, DIV, EQ, LT, NOT,
    JMP, JMPZ, LOAD, STORE, CALL, RET,
)

MOD = 15   # opcode number — the answer to part 1


class MODStackVM(StackVM):
    """StackVM with one new branch: MOD (a % b)."""

    def run(self):
        code = self.code
        while True:
            op = code[self.pc]; self.pc += 1
            if op == MOD:                      # <-- the new dispatch branch
                b = self.stack.pop()
                self.stack[-1] %= b
            elif op == HALT:
                return self.stack[-1] if self.stack else None
            elif op == PUSH:
                self.stack.append(code[self.pc]); self.pc += 1
            elif op == ADD:
                b = self.stack.pop(); self.stack[-1] += b
            elif op == SUB:
                b = self.stack.pop(); self.stack[-1] -= b
            elif op == MUL:
                b = self.stack.pop(); self.stack[-1] *= b
            elif op == DIV:
                b = self.stack.pop(); self.stack[-1] //= b
            elif op == EQ:
                b = self.stack.pop(); self.stack[-1] = int(self.stack[-1] == b)
            elif op == LT:
                b = self.stack.pop(); self.stack[-1] = int(self.stack[-1] < b)
            elif op == NOT:
                self.stack[-1] = int(not self.stack[-1])
            elif op == JMP:
                self.pc = self._u16()
            elif op == JMPZ:
                target = self._u16()
                if not self.stack.pop(): self.pc = target
            elif op == LOAD:
                s = code[self.pc]; self.pc += 1; self.stack.append(self.locals[s])
            elif op == STORE:
                s = code[self.pc]; self.pc += 1; self.locals[s] = self.stack.pop()
            elif op == CALL:
                target = self._u16()
                self.frames.append((self.locals[:], self.pc))
                self.locals = [0] * 16
                self.pc = target
            elif op == RET:
                val = self.stack.pop()
                self.locals, self.pc = self.frames.pop()
                self.stack.append(val)
            else:
                raise ValueError(f"unknown opcode {op} at pc={self.pc - 1}")


# A small assembler with the MOD rows added, mirroring assembler.py. This is
# how the WIDTHS entry (part 3) is exercised: an instruction *after* the MOD
# must land at the right address, which only works if MOD's width is recorded.
def assemble_mod(program):
    OPCODE = {
        'HALT': 0, 'PUSH': 1, 'ADD': 2, 'SUB': 3, 'MUL': 4, 'DIV': 5,
        'EQ': 6, 'LT': 7, 'NOT': 8, 'JMP': 9, 'JMPZ': 10,
        'LOAD': 11, 'STORE': 12, 'CALL': 13, 'RET': 14,
        'MOD': 15,                       # <-- new OPCODE entry
    }
    WIDTHS = {
        0: 1, 1: 2, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1, 7: 1, 8: 1,
        9: 3, 10: 3, 11: 2, 12: 2, 13: 3, 14: 1,
        15: 1,                           # <-- new WIDTHS entry: MOD is 1 byte
    }
    labels, pos = {}, 0
    for item in program:
        if isinstance(item, str):
            labels[item.rstrip(':')] = pos
        else:
            pos += WIDTHS[OPCODE[item[0]]]
    code = []
    for item in program:
        if isinstance(item, str):
            continue
        op, *args = item
        code.append(OPCODE[op])
        for arg in args:
            if isinstance(arg, str):
                addr = labels[arg]
                code += [addr >> 8, addr & 0xFF]
            else:
                code.append(arg)
    return code


if __name__ == "__main__":
    # Direct dispatch-branch check: 17 % 5 = 2
    raw = [PUSH, 17, PUSH, 5, MOD, HALT]
    assert MODStackVM(raw).run() == 2

    # WIDTHS check: a JMP whose target is a label AFTER the MOD. If MOD's width
    # were missing or wrong, the 'done' address would be miscomputed and the
    # program would jump into the middle of an instruction.
    src = [
        ('PUSH', 17), ('PUSH', 5), ('MOD',),   # 2
        ('JMP', 'done'),
        ('PUSH', 99),                           # would overwrite if reached
        'done:',
        ('HALT',),
    ]
    code = assemble_mod(src)
    result = MODStackVM(code).run()
    assert result == 2, f"expected 2, got {result}"
    print(f"17 % 5 = {result}  (assembled, MOD width accounted for)")
