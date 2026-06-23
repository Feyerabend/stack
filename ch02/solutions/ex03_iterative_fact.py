"""
Chapter 2, Exercise 3 — solution code.

Rewrite the stack-VM factorial iteratively, with a loop and no recursion. Does
your version use the call stack (frames) at all? What is the maximum operand-
stack depth it reaches, and how does that compare with the recursive version?

How to run:   python3 ex03_iterative_fact.py
Expected:     "fact(5) = 120  | frames used: 0  | max operand depth: 2"

Answers:
  - The call stack (frames) is NEVER used: there is no CALL or RET, so `frames`
    stays empty the whole run.
  - Maximum operand-stack depth is 2 (constant, independent of n).
  - The recursive version (Exercise 2) grows BOTH stacks with n: the operand
    stack holds one kept multiplicand per active frame (depth ~ n+1, e.g.
    [5,4,3,2,1,0] for fact(5)) and `frames` holds one entry per active call.
    Iteration trades that O(n) space for O(1) — the classic reason to convert
    tail-shaped recursion into a loop.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stack_vm import (  # noqa: E402
    StackVM, HALT, PUSH, MUL, SUB, LT, JMPZ, JMP, LOAD, STORE,
)


class InstrumentedStackVM(StackVM):
    """StackVM that tracks peak operand-stack depth and peak frames depth."""

    def __init__(self, code):
        super().__init__(code)
        self.max_stack_depth = 0
        self.max_frames_depth = 0

    def run(self):
        code = self.code
        while True:
            self.max_stack_depth = max(self.max_stack_depth, len(self.stack))
            self.max_frames_depth = max(self.max_frames_depth, len(self.frames))
            op = code[self.pc]; self.pc += 1
            if op == HALT:
                return self.stack[-1] if self.stack else None
            elif op == PUSH:
                self.stack.append(code[self.pc]); self.pc += 1
            elif op == MUL:
                b = self.stack.pop(); self.stack[-1] *= b
            elif op == SUB:
                b = self.stack.pop(); self.stack[-1] -= b
            elif op == LT:
                b = self.stack.pop(); self.stack[-1] = int(self.stack[-1] < b)
            elif op == JMPZ:
                target = self._u16()
                if not self.stack.pop(): self.pc = target
            elif op == JMP:
                self.pc = self._u16()
            elif op == LOAD:
                s = code[self.pc]; self.pc += 1; self.stack.append(self.locals[s])
            elif op == STORE:
                s = code[self.pc]; self.pc += 1; self.locals[s] = self.stack.pop()
            else:
                raise ValueError(f"unknown opcode {op} at pc={self.pc - 1}")


# Iterative factorial:
#
#   n   = locals[0]   (counter, starts at the input)
#   acc = locals[1]   (accumulator, starts at 1)
#   while 0 < n:
#       acc = acc * n
#       n   = n - 1
#   return acc
#
# No CALL / RET anywhere, so the frames stack is untouched.
def iterative_fact(n):
    src_bytes = [
        # init: n = <n>, acc = 1
        PUSH, n, STORE, 0,
        PUSH, 1, STORE, 1,
        # loop @ 8: while 0 < n
        PUSH, 0, LOAD, 0, LT,        # 0 < n ?   (addrs 8-12)
        JMPZ, 0, 33,                 # if n == 0 -> end (addr 33)   (13-15)
        LOAD, 1, LOAD, 0, MUL, STORE, 1,   # acc = acc * n          (16-22)
        LOAD, 0, PUSH, 1, SUB, STORE, 0,   # n = n - 1              (23-29)
        JMP, 0, 8,                   # back to loop                 (30-32)
        # end @ 33
        LOAD, 1, HALT,               # leave acc on the stack       (33-35)
    ]
    vm = InstrumentedStackVM(src_bytes)
    result = vm.run()
    return result, vm.max_frames_depth, vm.max_stack_depth


if __name__ == "__main__":
    result, frames_used, max_depth = iterative_fact(5)
    assert result == 120, f"expected 120, got {result}"
    assert frames_used == 0, f"expected 0 frames, got {frames_used}"
    assert max_depth == 2, f"expected max operand depth 2, got {max_depth}"
    print(f"fact(5) = {result}  | frames used: {frames_used}  "
          f"| max operand depth: {max_depth}")
