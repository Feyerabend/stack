"""
Chapter 2, Exercise 2 — solution code.

The factorial passes its argument on the operand stack. Trace, value by value,
what sits on the operand stack at the moment of the deepest recursive CALL when
computing fact(3). Explain why each multiplicand is still present when its MUL
finally executes.

How to run:   python3 ex02_trace.py
Expected:     "deepest CALL operand stack: [3, 2, 1, 0]"

See solutions.md for the explanation. In short: each frame pushes its own n
(the first `LOAD 0` of the recursive case) BEFORE the recursive CALL, and the
MUL that consumes it runs only AFTER the call returns. Because CALL/RET preserve
the operand stack (the callee takes its argument off the top with STORE and RET
pushes the result back), every pending multiplicand survives untouched.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stack_vm import (  # noqa: E402
    StackVM, CALL,
    PUSH, HALT, STORE, LOAD, LT, NOT, JMPZ, SUB, MUL, RET,
)


class TracingStackVM(StackVM):
    """StackVM that records the operand stack each time CALL is dispatched."""

    def __init__(self, code):
        super().__init__(code)
        self.call_snapshots = []

    def run(self):
        code = self.code
        while True:
            if code[self.pc] == CALL:
                # snapshot the operand stack at the instant of the CALL
                self.call_snapshots.append(list(self.stack))
            # delegate one step by running the base loop for a single opcode
            op = code[self.pc]; self.pc += 1
            if op == HALT:
                return self.stack[-1] if self.stack else None
            elif op == PUSH:
                self.stack.append(code[self.pc]); self.pc += 1
            elif op == STORE:
                s = code[self.pc]; self.pc += 1; self.locals[s] = self.stack.pop()
            elif op == LOAD:
                s = code[self.pc]; self.pc += 1; self.stack.append(self.locals[s])
            elif op == LT:
                b = self.stack.pop(); self.stack[-1] = int(self.stack[-1] < b)
            elif op == NOT:
                self.stack[-1] = int(not self.stack[-1])
            elif op == JMPZ:
                target = self._u16()
                if not self.stack.pop(): self.pc = target
            elif op == SUB:
                b = self.stack.pop(); self.stack[-1] -= b
            elif op == MUL:
                b = self.stack.pop(); self.stack[-1] *= b
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


# fact compiled to bytecode (Section 2.4), bootstrapped with the argument 3.
# Layout identical to stack_vm.py's `fact`, but the bootstrap pushes 3.
fact = [
    PUSH, 3, CALL, 0, 6, HALT,
    STORE, 0, LOAD, 0, PUSH, 1, LT, NOT, JMPZ, 0, 29,
    LOAD, 0, LOAD, 0, PUSH, 1, SUB, CALL, 0, 6, MUL, RET,
    PUSH, 1, RET,
]


if __name__ == "__main__":
    vm = TracingStackVM(fact)
    result = vm.run()
    assert result == 6, f"fact(3) should be 6, got {result}"

    # snapshots[0] is the bootstrap CALL ([3]); the rest are the recursive ones.
    deepest = max(vm.call_snapshots, key=len)
    print("operand stack at each CALL (outermost first):")
    for snap in vm.call_snapshots:
        print(f"  {snap}")
    print(f"deepest CALL operand stack: {deepest}")

    assert deepest == [3, 2, 1, 0], f"expected [3, 2, 1, 0], got {deepest}"
