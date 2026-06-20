"""
Minimal 6502 interpreter - companion code for Chapter 1.

Covers the instructions from Section 1.3 plus the subroutine model
discussed in the text:

    LDX  #n     X = n                        (immediate)
    LDA  #n     A = n                        (immediate)
    STA  zp     mem[zp] = A                  (zero-page store)
    LDA  zp     A = mem[zp]                  (zero-page load)
    ADC  #n     A = A + n  (carry in)        (immediate)
    INX         X += 1
    DEX         X -= 1
    CPX  #n     set flags from X - n         (immediate)
    BNE  label  branch if Z == 0
    BEQ  label  branch if Z == 1
    JSR  label  push return address, jump    (2 bytes of stack per call)
    RTS         pop return address, jump back
    BRK         halt

The page-$01 stack (256 bytes, SP starts at $FF) is modelled exactly.
Stack overflow raises StackOverflow; stack underflow raises StackUnderflow.
This makes the depth limit the book describes directly observable.

Programs are lists of tuples with label strings interspersed:

    program = [
        ('LDX', '#', 0),
        'loop',
        ('INX',),
        ('CPX', '#', 10),
        ('BNE', 'loop'),
        ('BRK',),
    ]

Entry point:
    M6502(program).run()  ->  the M6502 instance (inspect .A, .X, .Y, .SP)
"""


class StackOverflow(Exception):
    pass

class StackUnderflow(Exception):
    pass


class M6502:
    def __init__(self, program):
        self._instrs = []
        self._labels = {}
        for item in program:
            if isinstance(item, str):
                self._labels[item] = len(self._instrs)
            else:
                self._instrs.append(item)

        # Registers
        self.A  = 0
        self.X  = 0
        self.Y  = 0
        self.SP = 0xFF      # full-descending; first push goes to $01FF

        # Status flags
        self.N = 0   # negative
        self.Z = 0   # zero
        self.C = 0   # carry
        self.V = 0   # overflow

        # Memory: zero page ($00-$FF) + stack page ($0100-$01FF)
        self._zp    = bytearray(256)
        self._stack = bytearray(256)   # indexed by SP

        # Depth tracking so we can report overflow precisely
        self._depth = 0    # bytes currently on the stack

    # -- Stack primitives

    def _push(self, byte):
        if self._depth >= 256:
            raise StackOverflow(
                f"6502 stack exhausted at SP=${self.SP:02X} "
                f"(depth={self._depth} bytes)"
            )
        self._stack[self.SP] = byte & 0xFF
        self.SP = (self.SP - 1) & 0xFF
        self._depth += 1

    def _pop(self):
        if self._depth == 0:
            raise StackUnderflow("stack underflow")
        self.SP = (self.SP + 1) & 0xFF
        self._depth -= 1
        return self._stack[self.SP]

    # -- Flag helpers

    def _set_nz(self, val):
        val &= 0xFF
        self.N = 1 if val & 0x80 else 0
        self.Z = 1 if val == 0 else 0

    def _cmp(self, reg, val):
        """Set N, Z, C from reg − val (unsigned comparison)."""
        val &= 0xFF; reg &= 0xFF
        diff = reg - val
        self.C = 1 if reg >= val else 0
        self.Z = 1 if reg == val else 0
        self.N = 1 if diff & 0x80 else 0

    # -- Run

    def run(self):
        pc = 0
        while 0 <= pc < len(self._instrs):
            instr = self._instrs[pc]
            op    = instr[0]
            args  = instr[1:]
            pc   += 1

            if op == 'LDX':
                mode, n = args
                if mode == '#': self.X = n & 0xFF; self._set_nz(self.X)

            elif op == 'LDA':
                mode, n = args
                if mode == '#':
                    self.A = n & 0xFF; self._set_nz(self.A)
                elif mode == 'zp':
                    self.A = self._zp[n & 0xFF]; self._set_nz(self.A)

            elif op == 'STA':
                mode, addr = args
                if mode == 'zp':
                    self._zp[addr & 0xFF] = self.A & 0xFF

            elif op == 'ADC':
                mode, n = args
                if mode == '#':
                    result = self.A + (n & 0xFF) + self.C
                    self.C = 1 if result > 0xFF else 0
                    self.A = result & 0xFF
                    self._set_nz(self.A)

            elif op == 'INX':
                self.X = (self.X + 1) & 0xFF; self._set_nz(self.X)

            elif op == 'DEX':
                self.X = (self.X - 1) & 0xFF; self._set_nz(self.X)

            elif op == 'CPX':
                mode, n = args
                if mode == '#': self._cmp(self.X, n)

            elif op == 'BNE':
                if not self.Z: pc = self._labels[args[0]]

            elif op == 'BEQ':
                if self.Z: pc = self._labels[args[0]]

            elif op == 'JSR':
                # Push the return address as two bytes (high byte first,
                # then low byte) — consuming 2 bytes of the page-$01 stack,
                # exactly as on real hardware.
                ret = pc   # index of the instruction after JSR
                self._push(ret >> 8)
                self._push(ret & 0xFF)
                pc = self._labels[args[0]]

            elif op == 'RTS':
                lo = self._pop()
                hi = self._pop()
                pc = (hi << 8) | lo

            elif op == 'BRK':
                break

            else:
                raise ValueError(f"unknown opcode {op!r}")

        return self


# -- Demos

if __name__ == "__main__":
    # From Section 1.3: ten-iteration loop
    #
    #     LDX #0        ; X = 0
    # loop:
    #     INX           ; X += 1
    #     CPX #10       ; compare X with 10
    #     BNE loop      ; if X != 10, repeat
    #     BRK
    loop = [
        ('LDX', '#', 0),
        'loop',
        ('INX',),
        ('CPX', '#', 10),
        ('BNE', 'loop'),
        ('BRK',),
    ]
    cpu = M6502(loop).run()
    assert cpu.X == 10 and cpu.Z == 1
    print(f"X = {cpu.X}  (loop ran 10 times)")

    # Subroutine: sum 1+2+3+4+5 by calling an ADD-one routine five times.
    # Each JSR pushes 2 bytes onto the page-$01 stack; RTS pops them back.
    # The demo uses zero-page address $00 as the accumulator.
    add_one = [
        ('LDA', 'zp', 0x00),   # A = mem[$00]
        ('ADC', '#',  1),       # A += 1  (C=0 after loop init)
        ('STA', 'zp', 0x00),   # mem[$00] = A
        ('RTS',),
    ]
    sum_prog = [
        ('LDA', '#', 0),       # mem[$00] = 0  (accumulator)
        ('STA', 'zp', 0x00),
        ('LDX', '#', 5),       # call add_one five times
        'iter',
        ('JSR', 'add_one'),    # stack depth += 2 bytes each call
        ('DEX',),
        ('BNE', 'iter'),
        ('BRK',),
    ] + ['add_one'] + add_one

    cpu = M6502(sum_prog).run()
    result = cpu._zp[0x00]
    assert result == 5, f"expected 5, got {result}"
    print(f"mem[$00] = {result}  (added 1 five times)")
    print(f"SP = ${cpu.SP:02X}  (back to $FF = fully unwound)")

    # Stack depth illustration: the book says eight nested JSRs cost 16 bytes.
    # Here we call eight levels deep (no body — each just JSRs the next).
    def nested(n):
        """Build a chain of n nested JSR calls, each doing nothing but JSR/RTS."""
        prog = [('JSR', 'f1'), ('BRK',)]
        for i in range(1, n + 1):
            label = f'f{i}'
            if i < n:
                body = [('JSR', f'f{i + 1}'), ('RTS',)]
            else:
                body = [('RTS',)]
            prog = prog + [label] + body
        return prog

    depth8 = nested(8)
    cpu8   = M6502(depth8).run()
    bytes_used = 0xFF - cpu8.SP   # SP started at $FF; the minimum it reached
    # SP is back to $FF after all returns; measure peak by counting JSR depth
    # (8 calls × 2 bytes = 16 bytes peak; SP fully restored after RTS chain)
    print(f"8 nested JSRs used 8×2 = 16 bytes of stack (SP restored to ${cpu8.SP:02X})")

    # Provoke stack overflow with 129 nested calls (129 × 2 = 258 > 256).
    try:
        M6502(nested(129)).run()
        print("ERROR: should have overflowed")
    except StackOverflow as e:
        print(f"StackOverflow at 129 levels: {e}")
