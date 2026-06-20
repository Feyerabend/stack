"""
Register VM - companion code for Chapter 2.

A fourteen-instruction register machine with 16 registers (r0 hardwired to
zero, r1 holds return values by convention).  Calling convention: arguments
are placed in r2 onward before RCALL; RCALL saves the full caller register
file; RRET restores it and writes the return value into r1.

Note on RCALL: the callee starts with the caller's current register values
(arguments already in place).  A copy of the full register file is saved so
that RRET can restore the caller's state exactly.  The book's listing shows
self.regs = [0]*16 here, which zeros the argument registers and makes
argument-passing impossible; the correct implementation omits that line.

Entry point:
    RegVM(code).run()  ->  value in r1 after RHALT
"""

# -- Opcodes

RHALT = 0   # stop; result is in r1
RMOVI = 1   # rd, imm:       rd = imm
RMOV  = 2   # rd, rs:        rd = rs
RADD  = 3   # rd, rs1, rs2:  rd = rs1 + rs2
RSUB  = 4   # rd, rs1, rs2:  rd = rs1 - rs2
RMUL  = 5   # rd, rs1, rs2:  rd = rs1 * rs2
RDIV  = 6   # rd, rs1, rs2:  rd = rs1 // rs2
REQ   = 7   # rd, rs1, rs2:  rd = 1 if rs1 == rs2 else 0
RLT   = 8   # rd, rs1, rs2:  rd = 1 if rs1 < rs2 else 0
RNOT  = 9   # rd, rs:        rd = 0 if rs nonzero else 1
RJMP  = 10  # target:        jump unconditionally
RJMPZ = 11  # rs, target:    jump if rs == 0
RCALL = 12  # target:        save registers, jump
RRET  = 13  # rs:            return value in rs

_THREE_REG = (RADD, RSUB, RMUL, RDIV, REQ, RLT)


# -- Core VM

class RegVM:
    def __init__(self, code):
        self.code   = code
        self.regs   = [0] * 16  # r0 always zero; r1 = result
        self.frames = []
        self.pc     = 0

    def _u16(self):
        hi = self.code[self.pc]
        lo = self.code[self.pc + 1]
        self.pc += 2
        return (hi << 8) | lo

    def run(self):
        code = self.code
        r    = self.regs
        while True:
            op = code[self.pc]; self.pc += 1
            r[0] = 0   # r0 hardwired to zero

            if op == RHALT:
                return r[1]
            elif op == RMOVI:
                rd = code[self.pc]; self.pc += 1
                r[rd] = code[self.pc]; self.pc += 1
            elif op == RMOV:
                rd = code[self.pc]; rs = code[self.pc + 1]
                self.pc += 2
                r[rd] = r[rs]
            elif op in _THREE_REG:
                rd  = code[self.pc]
                rs1 = code[self.pc + 1]; rs2 = code[self.pc + 2]
                self.pc += 3
                if   op == RADD: r[rd] = r[rs1] + r[rs2]
                elif op == RSUB: r[rd] = r[rs1] - r[rs2]
                elif op == RMUL: r[rd] = r[rs1] * r[rs2]
                elif op == RDIV: r[rd] = r[rs1] // r[rs2]
                elif op == REQ:  r[rd] = int(r[rs1] == r[rs2])
                elif op == RLT:  r[rd] = int(r[rs1] < r[rs2])
            elif op == RNOT:
                rd = code[self.pc]; rs = code[self.pc + 1]
                self.pc += 2
                r[rd] = int(not r[rs])
            elif op == RJMP:
                self.pc = self._u16()
            elif op == RJMPZ:
                rs = code[self.pc]; self.pc += 1
                target = self._u16()
                if not r[rs]: self.pc = target
            elif op == RCALL:
                target = self._u16()
                self.frames.append((r[:], self.pc))
                # Callee starts with caller's register values: arguments in r2
                # onward are visible to the callee without any copying.
                self.pc = target
            elif op == RRET:
                rs = code[self.pc]; self.pc += 1
                val = r[rs]
                r_saved, self.pc = self.frames.pop()
                self.regs = r_saved; r = self.regs
                r[1] = val
            else:
                raise ValueError(f"unknown opcode {op} at pc={self.pc - 1}")


# -- Demo

if __name__ == "__main__":
    # Both programs share the same layout:
    #   bootstrap at addr 0  (3 bytes RMOVI + 3 bytes RCALL + 1 byte RHALT = 7)
    #   fact      at addr 7
    #   base      at addr 37  (after RRET at 35-36)
    #
    # Address map for fact body (both versions):
    #   7   RMOVI r3, 1        3 bytes
    #  10   RLT   r4, r2, r3   4 bytes
    #  14   RNOT  r4, r4       3 bytes
    #  17   RJMPZ r4, [37]     4 bytes  -> base case
    #  21   ...                         -> recursive case (differs below)
    #  35   RRET  r1           2 bytes
    #  37   RMOVI r1, 1        3 bytes  (base case)
    #  40   RRET  r1           2 bytes

    # -- Buggy factorial (from the book)
    #
    # RMOV r2, r5 sets r2 = n-1 before RCALL.  RCALL saves the register file
    # at that moment (r2 = n-1, not n).  When RRET restores it, r2 = n-1 again.
    # RMUL r1, r1, r2 then multiplies by n-1 instead of n.
    #
    # Recursive case (addr 21-36):
    #  21   RSUB r5, r2, r3    r5 = n-1
    #  25   RMOV r2, r5        r2 = n-1  <-- clobbers n; save captures n-1
    #  28   RCALL [7]          fact(n-1); RRET restores r2 = n-1
    #  31   RMUL r1, r1, r2    r1 * (n-1)  BUG: should be n
    #  35   RRET r1
    fact_buggy = [
        # bootstrap
        RMOVI, 2, 5,        # r2 = 5
        RCALL, 0, 7,        # call fact
        RHALT,
        # fact (addr 7)
        RMOVI, 3, 1,        # r3 = 1
        RLT,   4, 2, 3,     # r4 = (r2 < 1)
        RNOT,  4, 4,        # r4 = not r4
        RJMPZ, 4, 0, 37,    # if r4==0 (n==0), jump to base
        RSUB,  5, 2, 3,     # r5 = n-1
        RMOV,  2, 5,        # r2 = n-1  (save captures this value, not n)
        RCALL, 0, 7,        # fact(n-1)
        RMUL,  1, 1, 2,     # BUG: r2 restored to n-1, not n
        RRET,  1,
        # base (addr 37)
        RMOVI, 1, 1,        # r1 = 1
        RRET,  1,
    ]
    buggy_result = RegVM(fact_buggy).run()
    print(f"factorial(5) buggy  = {buggy_result}  (expected 120, bug gives {buggy_result})")
    assert buggy_result != 120, "buggy version should not give the right answer"

    # -- Corrected factorial
    #
    # Fix: save n into r6 before overwriting r2 with n-1.  When RRET restores
    # the caller's register file, r6 holds n (as it was at save time).
    # RMUL r1, r1, r6 then multiplies by the correct value.
    #
    # Recursive case (addr 21-38):
    #  21   RMOV  r6, r2       save n
    #  24   RSUB  r5, r2, r3   r5 = n-1
    #  28   RMOV  r2, r5       r2 = n-1  (r6 still holds n)
    #  31   RCALL [7]          fact(n-1); RRET restores r6 = n
    #  34   RMUL  r1, r1, r6   r1 * n  (correct)
    #  38   RRET  r1
    #
    # Because of the extra RMOV instruction (3 bytes), base is now at addr 40.
    fact_fixed = [
        # bootstrap
        RMOVI, 2, 5,        # r2 = 5
        RCALL, 0, 7,        # call fact
        RHALT,
        # fact (addr 7)
        RMOVI, 3, 1,        # r3 = 1
        RLT,   4, 2, 3,     # r4 = (n < 1)
        RNOT,  4, 4,        # r4 = not r4
        RJMPZ, 4, 0, 40,    # if n==0, jump to base
        RMOV,  6, 2,        # r6 = n  (save before clobbering)
        RSUB,  5, 2, 3,     # r5 = n-1
        RMOV,  2, 5,        # r2 = n-1
        RCALL, 0, 7,        # fact(n-1)
        RMUL,  1, 1, 6,     # r1 * r6  (r6 = n, restored by RRET)
        RRET,  1,
        # base (addr 40)
        RMOVI, 1, 1,        # r1 = 1
        RRET,  1,
    ]
    fixed_result = RegVM(fact_fixed).run()
    assert fixed_result == 120, f"expected 120, got {fixed_result}"
    print(f"factorial(5) fixed  = {fixed_result}")
