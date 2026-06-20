"""
Control flow compilation - companion code for Chapter 2.

Shows how structured control flow compiles to the stack VM's jump
instructions.  Four patterns, in order of complexity:

  1. if/else       - JMPZ to else-branch, JMP over it
  2. while         - back-edge JMP + JMPZ exit
  3. switch chain  - O(n) sequential EQ tests, one JMPZ per case
  4. switch table  - O(1) arithmetic dispatch via a computed jump

The jump table needs one new instruction not in the base VM:

    JMPIND (opcode 16)   pop an address from the operand stack and
                         jump there.  A jump table is a block of JMP
                         instructions at consecutive addresses; the
                         dispatcher multiplies the switch value by the
                         instruction width (3 bytes) and adds the table
                         base, then JMPIND enters the right slot.

Programs 1-3 use the assembler from assembler.py.  Program 4 is written
as raw bytecode so the table layout is explicit.

All programs store the switch/input value in locals[0] and write their
result to locals[1]; the final LOAD 1 / HALT leaves the result on the
stack so run() returns it.
"""

from assembler import assemble
from stack_vm import (
    StackVM,
    HALT, PUSH, ADD, SUB, MUL, EQ, LT, NOT,
    JMP, JMPZ, LOAD, STORE,
)

JMPIND = 16   # pop address from stack, jump there


# -- Extended VM

class CFStackVM(StackVM):
    """StackVM with JMPIND for computed jumps."""

    def run(self):
        code = self.code
        while True:
            op = code[self.pc]; self.pc += 1

            if op == JMPIND:
                self.pc = self.stack.pop()
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
                s = code[self.pc]; self.pc += 1
                self.stack.append(self.locals[s])
            elif op == STORE:
                s = code[self.pc]; self.pc += 1
                self.locals[s] = self.stack.pop()
            else:
                raise ValueError(f"unknown opcode {op} at pc={self.pc - 1}")


def _run(code, x):
    """Assemble (or accept raw bytes), set locals[0]=x, return result."""
    vm = CFStackVM(code)
    vm.locals[0] = x
    return vm.run()


# -- Pattern 1: if/else
#
#   if x < 5:
#       result = 10
#   else:
#       result = 20
#
# Compiled form:
#   <x < 5>
#   JMPZ  else        ; false -> skip then-branch
#   PUSH  10
#   STORE 1
#   JMP   end
#  else:
#   PUSH  20
#   STORE 1
#  end:
#   LOAD  1
#   HALT

_if_else = assemble([
    ('LOAD',  0),
    ('PUSH',  5),
    ('LT',),
    ('JMPZ', 'else'),
    ('PUSH',  10),
    ('STORE', 1),
    ('JMP',  'end'),
    'else:',
    ('PUSH',  20),
    ('STORE', 1),
    'end:',
    ('LOAD',  1),
    ('HALT',),
])


# -- Pattern 2: while
#
#   while x > 0:
#       x = x - 1
#   result = x          # (always 0)
#
# Condition x > 0  ≡  0 < x  -> PUSH 0 / LOAD x / LT
#
# Compiled form:
#  loop:
#   PUSH  0
#   LOAD  0             ; x
#   LT                  ; 0 < x?
#   JMPZ  end           ; if x == 0, exit
#   LOAD  0
#   PUSH  1
#   SUB
#   STORE 0             ; x = x - 1
#   JMP   loop
#  end:
#   LOAD  0
#   HALT

_while = assemble([
    'loop:',
    ('PUSH',  0),
    ('LOAD',  0),
    ('LT',),
    ('JMPZ', 'end'),
    ('LOAD',  0),
    ('PUSH',  1),
    ('SUB',),
    ('STORE', 0),
    ('JMP',  'loop'),
    'end:',
    ('LOAD',  0),
    ('HALT',),
])


# -- Pattern 3: switch - if-else chain
#
#   switch x:
#     case 0:  result = 10
#     case 1:  result = 20
#     case 2:  result = 30
#     case 3:  result = 40
#     default: result = 99
#
# Each case: load x, push case_value, EQ, JMPZ next_case - O(n) comparisons.

_switch_chain = assemble([
    ('LOAD',  0), ('PUSH', 0), ('EQ',), ('JMPZ', 'c1'),
    ('PUSH',  10), ('STORE', 1), ('JMP', 'end'),
    'c1:',
    ('LOAD',  0), ('PUSH', 1), ('EQ',), ('JMPZ', 'c2'),
    ('PUSH',  20), ('STORE', 1), ('JMP', 'end'),
    'c2:',
    ('LOAD',  0), ('PUSH', 2), ('EQ',), ('JMPZ', 'c3'),
    ('PUSH',  30), ('STORE', 1), ('JMP', 'end'),
    'c3:',
    ('LOAD',  0), ('PUSH', 3), ('EQ',), ('JMPZ', 'dflt'),
    ('PUSH',  40), ('STORE', 1), ('JMP', 'end'),
    'dflt:',
    ('PUSH',  99), ('STORE', 1),
    'end:',
    ('LOAD',  1), ('HALT',),
])


# -- Pattern 4: switch - jump table
#
# Same switch, but dispatched in O(1):
#
#   1. Bounds-check: if x >= 4, jump default.
#   2. Multiply x by 3 (the byte width of each JMP instruction).
#   3. Add the table base address.
#   4. JMPIND - jump to the computed address.
#
# The jump table is a contiguous block of JMP instructions.  Entry k
# holds JMP to case k.  No comparisons are performed.
#
# Bytecode layout (addresses are list indices):
#
#   0   LOAD  0         push x
#   2   PUSH  4
#   4   LT              x < 4?
#   5   JMPZ  0  57     -> default if x >= 4
#   8   LOAD  0         push x
#  10   PUSH  3
#  12   MUL             x * 3
#  13   PUSH  17        table base
#  15   ADD             17 + x*3
#  16   JMPIND          jump there
#  -- jump table (addr 17, 4×3 = 12 bytes) --
#  17   JMP  0  29      case 0
#  20   JMP  0  36      case 1
#  23   JMP  0  43      case 2
#  26   JMP  0  50      case 3
#  -- case bodies (7 bytes each) --
#  29   PUSH 10  STORE 1  JMP 0 61    case 0
#  36   PUSH 20  STORE 1  JMP 0 61    case 1
#  43   PUSH 30  STORE 1  JMP 0 61    case 2
#  50   PUSH 40  STORE 1  JMP 0 61    case 3
#  -- default (addr 57) --
#  57   PUSH 99  STORE 1
#  -- end (addr 61) --
#  61   LOAD 1  HALT

_switch_table = [
    # bounds check
    LOAD,  0,
    PUSH,  4,
    LT,
    JMPZ,  0,  57,      # default at 57
    # compute 17 + x*3
    LOAD,  0,
    PUSH,  3,
    MUL,
    PUSH,  17,          # table base
    ADD,
    JMPIND,             # -> table entry
    # jump table (addr 17)
    JMP,  0,  29,       # case 0
    JMP,  0,  36,       # case 1
    JMP,  0,  43,       # case 2
    JMP,  0,  50,       # case 3
    # case 0 (addr 29)
    PUSH, 10, STORE, 1, JMP, 0, 61,
    # case 1 (addr 36)
    PUSH, 20, STORE, 1, JMP, 0, 61,
    # case 2 (addr 43)
    PUSH, 30, STORE, 1, JMP, 0, 61,
    # case 3 (addr 50)
    PUSH, 40, STORE, 1, JMP, 0, 61,
    # default (addr 57)
    PUSH, 99, STORE, 1,
    # end (addr 61)
    LOAD, 1, HALT,
]


# -- Demo

if __name__ == "__main__":
    # if/else
    assert _run(_if_else, 3)  == 10   # 3 < 5 -> then-branch
    assert _run(_if_else, 7)  == 20   # 7 >= 5 -> else-branch
    print("if/else:")
    print(f"  x=3 -> {_run(_if_else, 3)}  (3 < 5, then-branch)")
    print(f"  x=7 -> {_run(_if_else, 7)}  (7 ≥ 5, else-branch)")

    # while
    assert _run(_while, 5) == 0
    print("\nwhile x > 0: x -= 1")
    print(f"  x=5 -> {_run(_while, 5)}  (counted down to 0)")

    # switch chain vs. switch table - same results for all inputs
    EXPECTED = {0: 10, 1: 20, 2: 30, 3: 40, 5: 99, 9: 99}
    print("\nswitch chain vs. jump table:")
    print(f"  {'x':>3}  {'chain':>6}  {'table':>6}")
    for x, expected in EXPECTED.items():
        chain = _run(_switch_chain, x)
        table = _run(_switch_table, x)
        assert chain == expected, f"chain x={x}: {chain} != {expected}"
        assert table == expected, f"table x={x}: {table} != {expected}"
        print(f"  {x:>3}  {chain:>6}  {table:>6}")

    print(f"\nchain: {len(_switch_chain)} bytes, "
          f"4 cases -> up to 4 EQ comparisons per dispatch")
    print(f"table: {len(_switch_table)} bytes, "
          f"any number of cases -> 1 multiply + 1 add + 1 JMPIND")
