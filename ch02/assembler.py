"""
Two-pass assembler for the stack VM — companion code for Chapter 2.

Input:  a list of items, each either a label string ("fact:") or an
        instruction tuple ("PUSH", 5) / ("CALL", "fact") / ("HALT",).
Output: a flat list of integer bytes, ready for StackVM(code).run().

Label resolution uses two passes:
  1. Walk the program computing byte addresses for each label.
  2. Walk again emitting bytes, substituting label addresses as big-endian
     16-bit pairs wherever a string argument appears.
"""

from stack_vm import (
    StackVM,
    HALT, PUSH, ADD, SUB, MUL, DIV, EQ, LT, NOT,
    JMP, JMPZ, LOAD, STORE, CALL, RET,
)


def assemble(program):
    """program: list of label strings or (op, *args) tuples"""
    OPCODE = {
        'HALT': 0,  'PUSH': 1,   'ADD': 2,   'SUB': 3,
        'MUL':  4,  'DIV':  5,   'EQ':  6,   'LT':  7,
        'NOT':  8,  'JMP':  9,   'JMPZ': 10,
        'LOAD': 11, 'STORE': 12, 'CALL': 13, 'RET': 14,
    }
    WIDTHS = {          # opcode value -> total byte width of instruction
        0: 1,   # HALT
        1: 2,   # PUSH  + 1-byte operand
        2: 1,   # ADD
        3: 1,   # SUB
        4: 1,   # MUL
        5: 1,   # DIV
        6: 1,   # EQ
        7: 1,   # LT
        8: 1,   # NOT
        9: 3,   # JMP   + 2-byte address
        10: 3,  # JMPZ  + 2-byte address
        11: 2,  # LOAD  + 1-byte slot
        12: 2,  # STORE + 1-byte slot
        13: 3,  # CALL  + 2-byte address
        14: 1,  # RET
    }

    # First pass: record the byte address of each label.
    labels = {}
    pos = 0
    for item in program:
        if isinstance(item, str):
            labels[item.rstrip(':')] = pos
        else:
            pos += WIDTHS[OPCODE[item[0]]]

    # Second pass: emit bytes, resolving label references to addresses.
    code = []
    for item in program:
        if isinstance(item, str):
            continue
        op, *args = item
        code.append(OPCODE[op])
        for arg in args:
            if isinstance(arg, str):        # label reference -> big-endian u16
                addr = labels[arg]
                code += [addr >> 8, addr & 0xFF]
            else:
                code.append(arg)
    return code


# ── Demo ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Factorial in assembler source (from the book, Section 2.5).
    # The assembler resolves 'fact' and 'base' to their byte addresses.
    factorial_src = [
        ('PUSH',  5),         # bootstrap: push the argument
        ('CALL', 'fact'),
        ('HALT',),            # result is left on the operand stack
        'fact:',
        ('STORE', 0),         # pop the argument into local slot 0
        ('LOAD',  0),
        ('PUSH',  1),
        ('LT',),
        ('NOT',),
        ('JMPZ', 'base'),
        ('LOAD',  0),         # keep n on stack across recursive call
        ('LOAD',  0),
        ('PUSH',  1),
        ('SUB',),
        ('CALL', 'fact'),
        ('MUL',),
        ('RET',),
        'base:',
        ('PUSH',  1),
        ('RET',),
    ]

    code = assemble(factorial_src)
    result = StackVM(code).run()
    assert result == 120, f"expected 120, got {result}"
    print(f"factorial(5) = {result}  (assembled)")
    print(f"bytecode ({len(code)} bytes): {code}")
