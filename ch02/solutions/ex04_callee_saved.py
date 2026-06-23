"""
Chapter 2, Exercise 4 — solution code.

The register VM's RCALL (in the book's listing) zeroes every register. Modify
RCALL and RRET to implement a caller-saved/callee-saved split: r2-r7 may be
clobbered by the callee, while r8-r15 must be preserved across the call. Which
registers does each instruction now copy, and where does the saved copy live?

How to run:   python3 ex04_callee_saved.py
Expected:     two lines, both ending in OK.

Answers:
  - RCALL copies ONLY the callee-saved registers r8-r15 (eight values) into the
    new frame, alongside the return pc. It does not touch r2-r7.
  - RRET restores those eight r8-r15 values from the frame, writes the return
    value into r1, and restores the pc. It leaves r2-r7 holding whatever the
    callee left in them.
  - The saved copy lives in the frame on `self.frames` (the call stack), exactly
    where the full-file copy lived before — only now it is a slice, not all 16.

Consequence (demonstrated below): a value that must survive a call has to be
kept in a callee-saved register. The corrected recursive factorial therefore
holds n in r8 (not r6 as in reg_vm.py, which only worked because that VM saved
the *entire* file).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reg_vm import (  # noqa: E402
    RegVM, _THREE_REG,
    RHALT, RMOVI, RMOV, RADD, RSUB, RMUL, RDIV, REQ, RLT, RNOT,
    RJMP, RJMPZ, RCALL, RRET,
)


class RegVMSplit(RegVM):
    """Register VM with a caller-saved (r2-r7) / callee-saved (r8-r15) split."""

    def run(self):
        code = self.code
        r = self.regs
        while True:
            op = code[self.pc]; self.pc += 1
            r[0] = 0
            if op == RHALT:
                return r[1]
            elif op == RMOVI:
                rd = code[self.pc]; self.pc += 1
                r[rd] = code[self.pc]; self.pc += 1
            elif op == RMOV:
                rd = code[self.pc]; rs = code[self.pc + 1]; self.pc += 2
                r[rd] = r[rs]
            elif op in _THREE_REG:
                rd = code[self.pc]; rs1 = code[self.pc + 1]; rs2 = code[self.pc + 2]
                self.pc += 3
                if   op == RADD: r[rd] = r[rs1] + r[rs2]
                elif op == RSUB: r[rd] = r[rs1] - r[rs2]
                elif op == RMUL: r[rd] = r[rs1] * r[rs2]
                elif op == RDIV: r[rd] = r[rs1] // r[rs2]
                elif op == REQ:  r[rd] = int(r[rs1] == r[rs2])
                elif op == RLT:  r[rd] = int(r[rs1] < r[rs2])
            elif op == RNOT:
                rd = code[self.pc]; rs = code[self.pc + 1]; self.pc += 2
                r[rd] = int(not r[rs])
            elif op == RJMP:
                self.pc = self._u16()
            elif op == RJMPZ:
                rs = code[self.pc]; self.pc += 1
                target = self._u16()
                if not r[rs]: self.pc = target
            elif op == RCALL:
                target = self._u16()
                # CHANGED: save only the callee-saved registers r8-r15.
                self.frames.append((r[8:16], self.pc))
                self.pc = target
            elif op == RRET:
                rs = code[self.pc]; self.pc += 1
                val = r[rs]
                saved, self.pc = self.frames.pop()
                # CHANGED: restore only r8-r15; r2-r7 keep the callee's values.
                r[8:16] = saved
                r[1] = val
            else:
                raise ValueError(f"unknown opcode {op} at pc={self.pc - 1}")


# ── Demo 1: the split itself ──────────────────────────────────────────────────
# Caller sets r2 = 100 (caller-saved) and r8 = 200 (callee-saved), then calls a
# callee that overwrites both. After the call, r2 must be clobbered (= 7) and
# r8 must be preserved (= 200).
def demo_split():
    prog = [
        RMOVI, 2, 100,        # r2 = 100   (caller-saved)
        RMOVI, 8, 200,        # r8 = 200   (callee-saved)
        RCALL, 0, 10,         # call clobber @ 10
        RHALT,                # @ 9
        # clobber @ 10:
        RMOVI, 2, 7,          # r2 = 7   (will survive the return)
        RMOVI, 8, 9,          # r8 = 9   (will be undone by RRET)
        RRET, 1,
    ]
    vm = RegVMSplit(prog)
    vm.run()
    return vm.regs[2], vm.regs[8]


# ── Demo 2: recursive factorial that respects the convention ─────────────────
# n is held in r8 (callee-saved) so it survives the recursive RCALL.
def demo_factorial():
    fact = [
        RMOVI, 2, 5,          # r2 = 5
        RCALL, 0, 7,          # call fact
        RHALT,
        # fact @ 7:
        RMOVI, 3, 1,          # r3 = 1
        RLT,   4, 2, 3,       # r4 = (n < 1)
        RNOT,  4, 4,          # r4 = not r4
        RJMPZ, 4, 0, 40,      # if n == 0 -> base @ 40
        RMOV,  8, 2,          # r8 = n   (callee-saved: survives the call)
        RSUB,  5, 2, 3,       # r5 = n - 1
        RMOV,  2, 5,          # r2 = n - 1  (argument; caller-saved, fine)
        RCALL, 0, 7,          # fact(n-1)
        RMUL,  1, 1, 8,       # r1 = fact(n-1) * n      (r8 restored to n)
        RRET,  1,
        # base @ 40:
        RMOVI, 1, 1,
        RRET,  1,
    ]
    return RegVMSplit(fact).run()


if __name__ == "__main__":
    r2, r8 = demo_split()
    assert r2 == 7, f"caller-saved r2 should be clobbered to 7, got {r2}"
    assert r8 == 200, f"callee-saved r8 should be preserved at 200, got {r8}"
    print(f"split: after call  r2={r2} (clobbered)  r8={r8} (preserved)  OK")

    fact5 = demo_factorial()
    assert fact5 == 120, f"expected 120, got {fact5}"
    print(f"factorial(5) with n in callee-saved r8 = {fact5}  OK")
