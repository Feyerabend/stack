"""
Minimal RV32I interpreter - companion code for Chapter 1.

Covers the instructions shown in Section 1.4:
    li   rd, imm        load immediate (pseudo: ADDI rd, x0, imm)
    addi rd, rs1, imm   add immediate
    add  rd, rs1, rs2   add registers
    bne  rs1, rs2, lbl  branch if not equal
    ret                 return (pseudo: JALR x0, ra, 0 - halts here)

Programs are written as lists of tuples; labels are bare strings placed
between instructions, just as they appear in assembly source.

All values are kept as signed Python ints (no truncation to 32 bits) so
the demos stay readable.  A real emulator would mask to 32 bits on every
write.

Entry point:
    RV(program).run()  ->  dict of {abi_name: value} register file
"""

# -- ABI register aliases

_ABI = {
    'zero': 0, 'ra':  1, 'sp':  2, 'gp':  3, 'tp': 4,
    't0':   5, 't1':  6, 't2':  7,
    's0':   8, 's1':  9,
    'a0':  10, 'a1': 11, 'a2': 12, 'a3': 13,
    'a4':  14, 'a5': 15, 'a6': 16, 'a7': 17,
    's2':  18, 's3': 19, 's4': 20, 's5': 21,
    's6':  22, 's7': 23, 's8': 24, 's9': 25,
    's10': 26, 's11': 27,
    't3':  28, 't4': 29, 't5': 30, 't6': 31,
}
for _i in range(32):
    _ABI[f'x{_i}'] = _i


class RV:
    def __init__(self, program):
        # Separate instructions from labels; build label-to-PC map.
        self._instrs = []
        self._labels = {}
        for item in program:
            if isinstance(item, str):
                self._labels[item] = len(self._instrs)
            else:
                self._instrs.append(item)

    def run(self):
        regs = [0] * 32
        pc   = 0

        def R(name):
            return regs[_ABI[name]]

        def W(name, val):
            idx = _ABI[name]
            if idx != 0:   # x0/zero hardwired to 0
                regs[idx] = val

        while 0 <= pc < len(self._instrs):
            op, *args = self._instrs[pc]
            pc += 1

            if   op == 'li':
                rd, imm = args
                W(rd, imm)
            elif op == 'addi':
                rd, rs1, imm = args
                W(rd, R(rs1) + imm)
            elif op == 'add':
                rd, rs1, rs2 = args
                W(rd, R(rs1) + R(rs2))
            elif op == 'sub':
                rd, rs1, rs2 = args
                W(rd, R(rs1) - R(rs2))
            elif op == 'bne':
                rs1, rs2, label = args
                if R(rs1) != R(rs2):
                    pc = self._labels[label]
            elif op == 'beq':
                rs1, rs2, label = args
                if R(rs1) == R(rs2):
                    pc = self._labels[label]
            elif op == 'ret':
                break
            else:
                raise ValueError(f"unknown opcode {op!r}")

        # Return register file as {abi_name: value} for easy inspection.
        return {name: regs[idx] for name, idx in _ABI.items()}


# -- Demos

if __name__ == "__main__":
    # From Section 1.2: adding on a register machine
    #
    #     li   t0, 3        ; t0 = 3
    #     li   t1, 4        ; t1 = 4
    #     add  t2, t0, t1   ; t2 = t0 + t1 = 7
    add_prog = [
        ('li',  't0', 3),
        ('li',  't1', 4),
        ('add', 't2', 't0', 't1'),
    ]
    regs = RV(add_prog).run()
    assert regs['t2'] == 7
    print(f"t2 = {regs['t2']}  (3 + 4)")

    # From Section 1.4: ten-iteration loop
    #
    #     li   t0, 0        ; t0 = 0
    #     li   t1, 10       ; t1 = 10 (loop bound, loaded once)
    # loop:
    #     addi t0, t0, 1    ; t0 += 1
    #     bne  t0, t1, loop ; if t0 != 10, repeat
    loop_prog = [
        ('li',   't0', 0),
        ('li',   't1', 10),
        'loop',
        ('addi', 't0', 't0', 1),
        ('bne',  't0', 't1', 'loop'),
    ]
    regs = RV(loop_prog).run()
    assert regs['t0'] == 10
    assert regs['t1'] == 10
    print(f"t0 = {regs['t0']}  (loop ran 10 times, t0 now equals t1)")
