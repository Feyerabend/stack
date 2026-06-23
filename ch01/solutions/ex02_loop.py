"""
Chapter 1, Exercise 2 — solution code.

Rewrite the ten-iteration loop (the 6502 `LDX #0 / INX / CPX #10 / BNE loop`
of Section 1.x) for a stack machine whose ONLY instructions are PUSH, ADD,
SUB, DUP, and BNZ (branch if the top of stack is non-zero, popping it).

How to run:   python3 ex02_loop.py
Expected:     "10 iterations, max stack depth = 2"

The exercise also asks for the greatest number of values on the stack at any
one moment. This program instruments the machine and reports it: the answer
is 2 (see solutions.md for the hand analysis).
"""

HALT = 0
PUSH = 1
ADD  = 2
SUB  = 3
DUP  = 5   # duplicate the top of stack
BNZ  = 6   # pop the top; if it was non-zero, jump to the operand address


def run(program):
    """Run a program, returning (result, iterations, max_depth)."""
    mem, stack, pc = list(program), [], 0
    iterations, max_depth = 0, 0
    while True:
        op = mem[pc]; pc += 1
        if   op == HALT:
            break
        elif op == PUSH:
            stack.append(mem[pc]); pc += 1
        elif op == ADD:
            b = stack.pop(); stack[-1] += b
        elif op == SUB:
            b = stack.pop(); stack[-1] -= b
        elif op == DUP:
            stack.append(stack[-1])
        elif op == BNZ:
            target = mem[pc]; pc += 1
            iterations += 1            # one full pass through the body reached here
            if stack.pop():            # non-zero: branch back
                pc = target
        max_depth = max(max_depth, len(stack))
    return (stack[-1] if stack else None), iterations, max_depth


# A counter that decrements from 10 to 0. Each pass through the body is one
# iteration; the loop exits when the counter reaches 0, exactly ten passes.
#
#   addr  instr            stack after        depth
#   0     PUSH 10          [10]               1
#   loop (addr 2):
#   2     PUSH 1           [c, 1]             2   <- peak
#   4     SUB              [c-1]              1
#   5     DUP              [c-1, c-1]         2   <- peak
#   6     BNZ loop         [c-1]  (or pops)   1
#   8     HALT
#
# The stack never holds more than two values, so the answer to the exercise's
# second question is 2.
PROGRAM = [
    PUSH, 10,        # 0: counter = 10
    # loop @ 2:
    PUSH, 1,         # 2
    SUB,             # 4: counter -= 1
    DUP,             # 5: copy counter to test it
    BNZ, 2,          # 6: if counter != 0, repeat (BNZ pops the copy)
    HALT,            # 8: counter (now 0) is the result
]


if __name__ == "__main__":
    result, iterations, max_depth = run(PROGRAM)
    assert iterations == 10, f"expected 10 iterations, got {iterations}"
    assert result == 0, f"expected final counter 0, got {result}"
    assert max_depth == 2, f"expected max depth 2, got {max_depth}"
    print(f"{iterations} iterations, max stack depth = {max_depth}")
