"""
Stack VM - companion code for Chapter 2.

A fifteen-instruction stack machine.  Argument convention: caller pushes
arguments onto the operand stack before CALL; callee stores them into local
slots; return value is left on the operand stack at RET.

Entry point:
    StackVM(code).run()  ->  value at top of stack, or None
"""

# -- Opcodes

HALT  = 0   # stop; top of stack is the return value
PUSH  = 1   # push the next byte as an integer literal
ADD   = 2   # pop b, pop a; push a + b
SUB   = 3   # pop b, pop a; push a - b
MUL   = 4   # pop b, pop a; push a * b
DIV   = 5   # pop b, pop a; push a // b
EQ    = 6   # pop b, pop a; push 1 if a == b, else 0
LT    = 7   # pop b, pop a; push 1 if a < b, else 0
NOT   = 8   # pop a; push 0 if a is nonzero, else 1
JMP   = 9   # next two bytes: target address; jump
JMPZ  = 10  # next two bytes: target; jump if stack top zero
LOAD  = 11  # next byte: slot index; push locals[slot]
STORE = 12  # next byte: slot index; pop into locals[slot]
CALL  = 13  # next two bytes: target; save frame, jump
RET   = 14  # pop return value, restore frame, push it


# -- Core VM

class StackVM:
    def __init__(self, code):
        self.code   = code
        self.stack  = []        # operand stack
        self.frames = []        # saved frames: (locals, return_pc)
        self.locals = [0] * 16  # current frame's 16 local slots
        self.pc     = 0

    def _u16(self):             # read a big-endian 16-bit operand
        hi = self.code[self.pc]
        lo = self.code[self.pc + 1]
        self.pc += 2
        return (hi << 8) | lo

    def run(self):
        code = self.code
        while True:
            op = code[self.pc]; self.pc += 1

            if op == HALT:
                return self.stack[-1] if self.stack else None
            elif op == PUSH:
                self.stack.append(code[self.pc])
                self.pc += 1
            elif op == ADD:
                b = self.stack.pop(); self.stack[-1] += b
            elif op == SUB:
                b = self.stack.pop(); self.stack[-1] -= b
            elif op == MUL:
                b = self.stack.pop(); self.stack[-1] *= b
            elif op == DIV:
                b = self.stack.pop(); self.stack[-1] //= b
            elif op == EQ:
                b = self.stack.pop()
                self.stack[-1] = int(self.stack[-1] == b)
            elif op == LT:
                b = self.stack.pop()
                self.stack[-1] = int(self.stack[-1] < b)
            elif op == NOT:
                self.stack[-1] = int(not self.stack[-1])
            elif op == JMP:
                self.pc = self._u16()
            elif op == JMPZ:
                target = self._u16()
                if not self.stack.pop():
                    self.pc = target
            elif op == LOAD:
                s = code[self.pc]; self.pc += 1
                self.stack.append(self.locals[s])
            elif op == STORE:
                s = code[self.pc]; self.pc += 1
                self.locals[s] = self.stack.pop()
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


# -- Constant pool extension
# The book presents this as a sketch showing the one new branch to add.
# Here it is as a complete runnable class.

LOADK = 15  # next byte: index into constant pool

class StackVMWithPool(StackVM):
    """StackVM with a constant pool for values that do not fit in one byte."""

    def __init__(self, code, constants):
        super().__init__(code)
        self.constants = constants  # list of int, float, or str

    def run(self):
        code = self.code
        while True:
            op = code[self.pc]; self.pc += 1

            if op == LOADK:
                idx = code[self.pc]; self.pc += 1
                self.stack.append(self.constants[idx])
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


# -- Demo

if __name__ == "__main__":
    # 3 * (4 + 5) = 27
    prog = [
        PUSH, 3,
        PUSH, 4,
        PUSH, 5,
        ADD,
        MUL,
        HALT,
    ]
    result = StackVM(prog).run()
    assert result == 27
    print(f"3 * (4 + 5) = {result}")

    # factorial(5) = 120
    #
    # Address layout:
    #   0  PUSH 5       bootstrap: push argument
    #   2  CALL [6]     call fact
    #   5  HALT
    #   6  STORE 0      fact: n -> locals[0]
    #   8  LOAD  0      push n
    #  10  PUSH  1
    #  12  LT           n < 1?
    #  13  NOT          flip: 1 if n >= 1
    #  14  JMPZ [29]    if n == 0, go to base case
    #  17  LOAD  0      push n  (stays on stack across recursive call)
    #  19  LOAD  0      push n again
    #  21  PUSH  1
    #  23  SUB          n - 1
    #  24  CALL  [6]    fact(n-1); result replaces n-1 on stack
    #  27  MUL          n * fact(n-1)
    #  28  RET
    #  29  PUSH  1      base: return 1
    #  31  RET
    fact = [
        PUSH, 5, CALL, 0, 6, HALT,
        STORE, 0, LOAD, 0, PUSH, 1, LT, NOT, JMPZ, 0, 29,
        LOAD, 0, LOAD, 0, PUSH, 1, SUB, CALL, 0, 6, MUL, RET,
        PUSH, 1, RET,
    ]
    result = StackVM(fact).run()
    assert result == 120
    print(f"factorial(5) = {result}")

    # Constant pool: load a value wider than one byte
    constants = [1000]
    pool_prog = [
        LOADK, 0,   # push constants[0] = 1000
        LOADK, 0,   # push 1000 again
        ADD,        # 2000
        HALT,
    ]
    result = StackVMWithPool(pool_prog, constants).run()
    assert result == 2000
    print(f"1000 + 1000 (via constant pool) = {result}")
