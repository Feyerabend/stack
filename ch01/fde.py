"""
Fetch-decode-execute loop - companion code for Chapter 1.

The listing from the book is reproduced verbatim below, then wrapped in a
small class so the extended version can share the same dispatch table without
repeating the loop.
"""

# -- Book listing (Section 1.1)

HALT = 0
PUSH = 1
ADD  = 2

memory = [
    PUSH, 3,   # push the literal 3
    PUSH, 4,   # push the literal 4
    ADD,       # pop two values, push their sum
    HALT,
]

pc    = 0
stack = []

while True:
    opcode = memory[pc]; pc += 1
    if opcode == HALT:
        break
    elif opcode == PUSH:
        stack.append(memory[pc]); pc += 1
    elif opcode == ADD:
        b = stack.pop()
        a = stack.pop()
        stack.append(a + b)

assert stack[-1] == 7
print(stack[-1])   # 7


# -- Extended machine (Exercise 1: add SUB and JMP)
#
# SUB pops two values and pushes their difference (a - b).
# JMP reads a one-byte target address from the next memory cell and jumps.
# Together they are enough to write counted loops.

SUB = 3
JMP = 4

class FDE:
    """Minimal fetch-decode-execute machine: PUSH, ADD, SUB, JMP, HALT."""

    def __init__(self, program):
        self.mem   = list(program)
        self.stack = []
        self.pc    = 0

    def run(self):
        while True:
            op = self.mem[self.pc]; self.pc += 1
            if   op == HALT: break
            elif op == PUSH: self.stack.append(self.mem[self.pc]); self.pc += 1
            elif op == ADD:  b = self.stack.pop(); self.stack[-1] += b
            elif op == SUB:  b = self.stack.pop(); self.stack[-1] -= b
            elif op == JMP:  self.pc = self.mem[self.pc]
        return self.stack[-1] if self.stack else None


if __name__ == "__main__":
    # 3 + 4 = 7  (book example)
    result = FDE([PUSH, 3, PUSH, 4, ADD, HALT]).run()
    assert result == 7
    print(f"3 + 4 = {result}")

    # Sum 1+2+3+4+5 = 15.
    #
    # This tiny ISA has no conditional branch (Exercise 1 adds only SUB and an
    # unconditional JMP), so a counted loop would spin forever. We therefore
    # show the sum as straight-line code, and demonstrate JMP separately below.
    straight = [
        PUSH, 1, PUSH, 2, ADD,
        PUSH, 3, ADD,
        PUSH, 4, ADD,
        PUSH, 5, ADD,
        HALT,
    ]
    result = FDE(straight).run()
    assert result == 15
    print(f"1+2+3+4+5 = {result}")

    # JMP demo: jump over a PUSH that would otherwise add 100
    # Memory layout: 0=PUSH 1=3 2=PUSH 3=4 4=ADD 5=JMP 6=9 7=PUSH 8=100 9=HALT
    jump_prog = [
        PUSH, 3,
        PUSH, 4,
        ADD,          # stack: [7]
        JMP, 9,       # jump to addr 9, skipping PUSH 100
        PUSH, 100,    # addr 7-8 - skipped
        HALT,         # addr 9
    ]
    result = FDE(jump_prog).run()
    assert result == 7
    print(f"3+4 (JMP skips PUSH 100) = {result}")
