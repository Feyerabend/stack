"""
Lark RISC-V assembler — RV32I + M extension.
Extended from ch05/sec5.9/riscv/02/asm.py.

Additions over the base assembler:
  call fn      → jal ra, fn            (4 bytes; near call, ±1 MB)
  la rd, lbl   → auipc rd, hi + addi   (8 bytes; full PC-relative address)
  li rd, imm   → addi (4) or lui+addi  (8; handles any 32-bit immediate)
  .word N      → 4-byte LE word
  .byte b,...  → N raw bytes
  .section .text / .rodata → section tracking; .text entry pads to 4-byte alignment
  .globl sym   → no-op

Runtime stubs: pre-registered labels at fixed addresses (EBREAK instructions).
  The VM intercepts those PC values and calls Python handlers instead of
  executing EBREAK.  The handler simulates a normal function call/return.

A bootstrap block is prepended that:
  1. Initialises sp to top-of-memory
  2. Calls __global_init__ (a default ret-only stub if none defined in source)
  3. Calls lark_main(a0=0)   (0 = unit IO token)
  4. ECALLs exit (syscall 10)
"""

from __future__ import annotations
import sys, os, struct
from dataclasses import dataclass


# ── Instruction encoding ──────────────────────────────────────────────────────

@dataclass
class Instruction:
    opcode: str
    rd: int = 0; rs1: int = 0; rs2: int = 0
    imm: int = 0; funct3: int = 0; funct7: int = 0

    def encode(self) -> int:
        op = self.opcode
        if op in ('ADD','SUB','AND','OR','XOR','SLL','SRL','SRA','SLT','SLTU',
                  'MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU'):
            return ((self.funct7<<25)|(self.rs2<<20)|(self.rs1<<15)|
                    (self.funct3<<12)|(self.rd<<7)|0b0110011)
        if op in ('ADDI','ANDI','ORI','XORI','SLTI','SLTIU'):
            return ((self.imm&0xFFF)<<20|(self.rs1<<15)|(self.funct3<<12)|
                    (self.rd<<7)|0b0010011)
        if op in ('SLLI','SRLI','SRAI'):
            shamt = self.imm & 0x1F
            upper = 0b0100000 if op=='SRAI' else 0
            return (((upper<<5)|shamt)<<20|(self.rs1<<15)|(self.funct3<<12)|
                    (self.rd<<7)|0b0010011)
        if op in ('LB','LH','LW','LBU','LHU'):
            return ((self.imm&0xFFF)<<20|(self.rs1<<15)|(self.funct3<<12)|
                    (self.rd<<7)|0b0000011)
        if op in ('SB','SH','SW'):
            i = self.imm & 0xFFF
            return (((i>>5)&0x7F)<<25|(self.rs2<<20)|(self.rs1<<15)|
                    (self.funct3<<12)|((i&0x1F)<<7)|0b0100011)
        if op in ('BEQ','BNE','BLT','BGE','BLTU','BGEU'):
            i = self.imm & 0x1FFF
            return (((i>>12)&1)<<31|(((i>>5)&0x3F)<<25)|(self.rs2<<20)|
                    (self.rs1<<15)|(self.funct3<<12)|(((i>>1)&0xF)<<8)|
                    (((i>>11)&1)<<7)|0b1100011)
        if op == 'JAL':
            i = self.imm & 0x1FFFFF
            return (((i>>20)&1)<<31|(((i>>1)&0x3FF)<<21)|(((i>>11)&1)<<20)|
                    (((i>>12)&0xFF)<<12)|(self.rd<<7)|0b1101111)
        if op == 'JALR':
            return ((self.imm&0xFFF)<<20|(self.rs1<<15)|(self.funct3<<12)|
                    (self.rd<<7)|0b1100111)
        if op == 'LUI':
            return ((self.imm&0xFFFFF)<<12|(self.rd<<7)|0b0110111)
        if op == 'AUIPC':
            return ((self.imm&0xFFFFF)<<12|(self.rd<<7)|0b0010111)
        if op == 'ECALL':  return 0x00000073
        if op == 'EBREAK': return 0x00100073
        raise ValueError(f"Cannot encode: {op}")


# ── Assembler ─────────────────────────────────────────────────────────────────

class LarkAssembler:
    """Two-pass RISC-V assembler extended for Lark-generated code."""

    REG_MAP = {
        'zero':0,'ra':1,'sp':2,'gp':3,'tp':4,
        't0':5,'t1':6,'t2':7,'s0':8,'fp':8,'s1':9,
        'a0':10,'a1':11,'a2':12,'a3':13,'a4':14,'a5':15,'a6':16,'a7':17,
        's2':18,'s3':19,'s4':20,'s5':21,'s6':22,'s7':23,
        's8':24,'s9':25,'s10':26,'s11':27,
        't3':28,'t4':29,'t5':30,'t6':31,
    }

    # These labels are pre-registered at stub addresses.
    # The VM intercepts execution at those addresses.
    RUNTIME_STUBS: list[str] = [
        '__heap_alloc', 'print', 'show', 'read',
        'int_to_float', 'float_to_int', 'int_to_string', 'float_to_string',
        '__lark_match_fail', '__str_concat',
        '__show_float',
        '__float_add', '__float_sub', '__float_mul', '__float_div',
        '__float_lt', '__float_le', '__float_gt', '__float_ge',
        '__show_bool',
        'string_length',
        'int_abs', 'float_abs', 'float_sqrt', 'float_floor', 'float_ceil',
    ]

    def __init__(self, mem_size: int = 65536) -> None:
        self.mem_size = mem_size
        self.labels: dict[str, int] = {}

    # ── Preamble generation ─────────────────────────────────────────────────

    def _preamble(self) -> str:
        """
        Generate the stub table and bootstrap.

        Layout:
          [0x00] stub for __heap_alloc  (ebreak, intercepted by VM)
          [0x04] stub for print
          ...
          [0x24] default __global_init__: ret  (overridden if user defines one)
          [0x28] __bootstrap: li sp, N; call __global_init__; li a0,0; call lark_main; exit
        """
        lines: list[str] = []
        for name in self.RUNTIME_STUBS:
            lines += [f"{name}:", "  ebreak"]
        # Default __global_init__: overridden if the source defines its own.
        lines += ["__global_init__:", "  ret"]
        # Bootstrap: set up stack, call __global_init__, then lark_main(io=0).
        lines += [
            "__bootstrap:",
            f"  li   sp, {self.mem_size - 16}",
            "  call __global_init__",
            "  li   a0, 0",
            "  call lark_main",
            "  li   a7, 10",
            "  ecall",
        ]
        return "\n".join(lines)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def parse_register(self, reg: str) -> int:
        reg = reg.strip().lower().rstrip(',')
        if reg in self.REG_MAP:
            return self.REG_MAP[reg]
        if reg.startswith('x'):
            return int(reg[1:])
        raise ValueError(f"Invalid register: {reg!r}")

    @staticmethod
    def sign_extend(val: int, bits: int) -> int:
        mask = 1 << (bits - 1)
        return val | (~((1 << bits) - 1)) if val & mask else val

    def _parse_int(self, s: str) -> int:
        s = s.strip().rstrip(',').split('#')[0].strip()
        if s.startswith('0x') or s.startswith('0X'):
            return int(s, 16)
        return int(s)

    def _parse_offset(self, operand: str) -> tuple[int, int]:
        """Parse 'off(reg)' → (offset, reg_index)."""
        operand = operand.strip().rstrip(',')
        if '(' in operand:
            off_s, rest = operand.split('(', 1)
            return self._parse_int(off_s or '0'), self.parse_register(rest.rstrip(')'))
        return 0, self.parse_register(operand)

    def _to_s32(self, imm: int) -> int:
        """Normalize to signed 32-bit."""
        imm = imm & 0xFFFFFFFF
        return imm - 0x100000000 if imm >= 0x80000000 else imm

    def _li_size(self, imm_str: str) -> int:
        """Return 4 (ADDI only) or 8 (LUI+ADDI) for a li immediate."""
        try:
            imm = self._to_s32(self._parse_int(imm_str))
            return 4 if -2048 <= imm <= 2047 else 8
        except (ValueError, IndexError):
            return 8

    def _instr_size(self, parts: list[str]) -> int:
        op = parts[0].upper() if parts else ''
        if op == 'LA':   return 8
        if op == 'LI' and len(parts) >= 3:
            return self._li_size(parts[2])
        return 4

    # ── Pass 1: collect labels ───────────────────────────────────────────────

    def _pass1(self, lines: list[str]) -> None:
        addr = 0
        section = '.text'

        for raw in lines:
            line = raw.split('#')[0].strip()
            if not line:
                continue

            # Label (handles .Lstr0: and lark_main: and __bootstrap:)
            if ':' in line:
                lbl, rest = line.split(':', 1)
                self.labels[lbl.strip()] = addr
                line = rest.strip()
                if not line:
                    continue

            # Directives
            if line.startswith('.section'):
                tok = line.split()
                new_sec = tok[1] if len(tok) > 1 else ''
                if new_sec == '.text' and section != '.text':
                    addr = (addr + 3) & ~3   # align to 4 bytes
                section = new_sec
                continue
            if line.startswith('.globl'):
                continue
            if line.startswith('.word'):
                addr += 4
                continue
            if line.startswith('.byte'):
                rest_b = line[len('.byte'):].strip()
                vals = [v.strip() for v in rest_b.split(',') if v.strip()]
                addr += len(vals)
                continue

            # Instruction
            parts = line.replace(',', ' ').split()
            if parts:
                addr += self._instr_size(parts)

    # ── Pass 2: emit binary ──────────────────────────────────────────────────

    def _pass2(self, lines: list[str]) -> bytes:
        binary = bytearray()
        addr = 0
        section = '.text'

        for raw in lines:
            line = raw.split('#')[0].strip()
            if not line:
                continue

            if ':' in line:
                _, rest = line.split(':', 1)
                line = rest.strip()
                if not line:
                    continue

            if line.startswith('.section'):
                tok = line.split()
                new_sec = tok[1] if len(tok) > 1 else ''
                if new_sec == '.text' and section != '.text':
                    pad = (4 - addr % 4) % 4
                    binary += bytes(pad)
                    addr += pad
                section = new_sec
                continue
            if line.startswith('.globl'):
                continue
            if line.startswith('.word'):
                rest_w = line[len('.word'):].strip().split('#')[0].strip()
                val = self._parse_int(rest_w)
                binary += struct.pack('<I', val & 0xFFFFFFFF)
                addr += 4
                continue
            if line.startswith('.byte'):
                rest_b = line[len('.byte'):].strip()
                for tok in rest_b.split(','):
                    tok = tok.strip().split('#')[0].strip()
                    if tok:
                        binary += struct.pack('B', self._parse_int(tok) & 0xFF)
                        addr += 1
                continue

            parts = line.replace(',', ' ').split()
            if not parts:
                continue

            encoded = self._encode(parts, addr)
            binary += encoded
            addr += len(encoded)

        return bytes(binary)

    # ── Instruction encoder ──────────────────────────────────────────────────

    def _encode(self, parts: list[str], addr: int) -> bytes:
        op = parts[0].upper()

        # ── Extended pseudo-instructions ─────────────────────────────────────
        if op == 'CALL':
            label = parts[1]
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label!r}")
            offset = self.labels[label] - addr
            return struct.pack('<I', Instruction('JAL', rd=1, imm=offset).encode())

        if op == 'LA':
            rd     = self.parse_register(parts[1])
            label  = parts[2].rstrip(',')
            if label not in self.labels:
                raise ValueError(f"Undefined label: {label!r}")
            delta  = self.labels[label] - addr
            lo12   = delta & 0xFFF
            if lo12 >= 0x800: lo12 -= 0x1000
            hi20   = (delta - lo12) >> 12
            auipc  = Instruction('AUIPC', rd=rd, imm=hi20 & 0xFFFFF)
            addi   = Instruction('ADDI',  rd=rd, rs1=rd, imm=lo12, funct3=0)
            return struct.pack('<II', auipc.encode(), addi.encode())

        if op == 'LI':
            rd  = self.parse_register(parts[1])
            imm = self._to_s32(self._parse_int(parts[2]))
            if -2048 <= imm <= 2047:
                return struct.pack('<I',
                    Instruction('ADDI', rd=rd, rs1=0, imm=imm, funct3=0).encode())
            lo12 = imm & 0xFFF
            if lo12 >= 0x800: lo12 -= 0x1000
            hi20 = (imm - lo12) >> 12
            lui  = Instruction('LUI',  rd=rd, imm=hi20 & 0xFFFFF)
            addi = Instruction('ADDI', rd=rd, rs1=rd, imm=lo12, funct3=0)
            return struct.pack('<II', lui.encode(), addi.encode())

        return struct.pack('<I', self._parse_instr(parts, addr).encode())

    def _parse_instr(self, parts: list[str], addr: int) -> Instruction:
        op = parts[0].upper()

        def reg(i: int) -> int: return self.parse_register(parts[i])
        def imm(i: int) -> int: return self._parse_int(parts[i])
        def sx(v: int, b: int) -> int: return self.sign_extend(v, b)
        def target(i: int) -> int:
            t = parts[i]
            return self.labels[t] - addr if t in self.labels else imm(i)

        # R-type ────────────────────────────────────────────────────────────
        if op == 'ADD':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b000,funct7=0b0000000)
        if op == 'SUB':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b000,funct7=0b0100000)
        if op == 'AND':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b111,funct7=0b0000000)
        if op == 'OR':    return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b110,funct7=0b0000000)
        if op == 'XOR':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b100,funct7=0b0000000)
        if op == 'SLL':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b001,funct7=0b0000000)
        if op == 'SRL':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b101,funct7=0b0000000)
        if op == 'SRA':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b101,funct7=0b0100000)
        if op == 'SLT':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b010,funct7=0b0000000)
        if op == 'SLTU':  return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b011,funct7=0b0000000)
        # M extension
        if op == 'MUL':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b000,funct7=0b0000001)
        if op == 'MULH':  return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b001,funct7=0b0000001)
        if op=='MULHSU':  return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b010,funct7=0b0000001)
        if op == 'MULHU': return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b011,funct7=0b0000001)
        if op == 'DIV':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b100,funct7=0b0000001)
        if op == 'DIVU':  return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b101,funct7=0b0000001)
        if op == 'REM':   return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b110,funct7=0b0000001)
        if op == 'REMU':  return Instruction(op,rd=reg(1),rs1=reg(2),rs2=reg(3),funct3=0b111,funct7=0b0000001)

        # I-type arithmetic ──────────────────────────────────────────────────
        if op == 'ADDI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=sx(imm(3),12),funct3=0b000)
        if op == 'ANDI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=sx(imm(3),12),funct3=0b111)
        if op == 'ORI':   return Instruction(op,rd=reg(1),rs1=reg(2),imm=sx(imm(3),12),funct3=0b110)
        if op == 'XORI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=sx(imm(3),12),funct3=0b100)
        if op == 'SLTI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=sx(imm(3),12),funct3=0b010)
        if op == 'SLTIU': return Instruction(op,rd=reg(1),rs1=reg(2),imm=sx(imm(3),12),funct3=0b011)

        # I-type shifts ──────────────────────────────────────────────────────
        if op == 'SLLI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=imm(3)&0x1F,funct3=0b001)
        if op == 'SRLI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=imm(3)&0x1F,funct3=0b101)
        if op == 'SRAI':  return Instruction(op,rd=reg(1),rs1=reg(2),imm=imm(3)&0x1F,funct3=0b101)

        # Loads ──────────────────────────────────────────────────────────────
        if op == 'LB':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rd=reg(1),rs1=base,imm=sx(off,12),funct3=0b000)
        if op == 'LH':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rd=reg(1),rs1=base,imm=sx(off,12),funct3=0b001)
        if op == 'LW':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rd=reg(1),rs1=base,imm=sx(off,12),funct3=0b010)
        if op == 'LBU':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rd=reg(1),rs1=base,imm=sx(off,12),funct3=0b100)
        if op == 'LHU':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rd=reg(1),rs1=base,imm=sx(off,12),funct3=0b101)

        # Stores ─────────────────────────────────────────────────────────────
        if op == 'SB':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rs1=base,rs2=reg(1),imm=sx(off,12),funct3=0b000)
        if op == 'SH':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rs1=base,rs2=reg(1),imm=sx(off,12),funct3=0b001)
        if op == 'SW':
            off,base = self._parse_offset(parts[2]); return Instruction(op,rs1=base,rs2=reg(1),imm=sx(off,12),funct3=0b010)

        # Branches ───────────────────────────────────────────────────────────
        if op == 'BEQ':   return Instruction(op,rs1=reg(1),rs2=reg(2),imm=target(3),funct3=0b000)
        if op == 'BNE':   return Instruction(op,rs1=reg(1),rs2=reg(2),imm=target(3),funct3=0b001)
        if op == 'BLT':   return Instruction(op,rs1=reg(1),rs2=reg(2),imm=target(3),funct3=0b100)
        if op == 'BGE':   return Instruction(op,rs1=reg(1),rs2=reg(2),imm=target(3),funct3=0b101)
        if op == 'BLTU':  return Instruction(op,rs1=reg(1),rs2=reg(2),imm=target(3),funct3=0b110)
        if op == 'BGEU':  return Instruction(op,rs1=reg(1),rs2=reg(2),imm=target(3),funct3=0b111)

        # JAL / JALR ─────────────────────────────────────────────────────────
        if op == 'JAL':
            if len(parts) > 2: return Instruction(op,rd=reg(1),imm=target(2))
            return Instruction(op,rd=1,imm=target(1))
        if op == 'JALR':
            rd_r = reg(1)
            if len(parts) > 2 and '(' in parts[2]:
                off,base = self._parse_offset(parts[2])
            else:
                off,base = 0, reg(2)
            return Instruction(op,rd=rd_r,rs1=base,imm=sx(off,12),funct3=0b000)

        # Upper immediate ─────────────────────────────────────────────────────
        if op == 'LUI':   return Instruction(op,rd=reg(1),imm=imm(2))
        if op == 'AUIPC': return Instruction(op,rd=reg(1),imm=imm(2))

        # System ──────────────────────────────────────────────────────────────
        if op == 'ECALL':  return Instruction(op)
        if op == 'EBREAK': return Instruction(op)

        # Pseudo-instructions ─────────────────────────────────────────────────
        if op == 'NOP':   return Instruction('ADDI',rd=0,rs1=0,imm=0,funct3=0)
        if op == 'MV':    return Instruction('ADDI',rd=reg(1),rs1=reg(2),imm=0,funct3=0)
        if op == 'RET':   return Instruction('JALR',rd=0,rs1=1,imm=0,funct3=0)
        if op == 'NEG':   return Instruction('SUB', rd=reg(1),rs1=0,rs2=reg(2),funct3=0,funct7=0b0100000)
        if op == 'NOT':   return Instruction('XORI',rd=reg(1),rs1=reg(2),imm=-1,funct3=0b100)
        if op == 'SEQZ':  return Instruction('SLTIU',rd=reg(1),rs1=reg(2),imm=1,funct3=0b011)
        if op == 'SNEZ':  return Instruction('SLTU', rd=reg(1),rs1=0,rs2=reg(2),funct3=0b011,funct7=0)
        if op == 'BNEZ':  return Instruction('BNE',rs1=reg(1),rs2=0,imm=target(2),funct3=0b001)
        if op == 'BEQZ':  return Instruction('BEQ',rs1=reg(1),rs2=0,imm=target(2),funct3=0b000)
        if op == 'J':     return Instruction('JAL',rd=0,imm=target(1))
        if op == 'BGT':   return Instruction('BLT',rs1=reg(2),rs2=reg(1),imm=target(3),funct3=0b100)
        if op == 'BLE':   return Instruction('BGE',rs1=reg(2),rs2=reg(1),imm=target(3),funct3=0b101)
        if op == 'BGTU':  return Instruction('BLTU',rs1=reg(2),rs2=reg(1),imm=target(3),funct3=0b110)
        if op == 'BLEU':  return Instruction('BGEU',rs1=reg(2),rs2=reg(1),imm=target(3),funct3=0b111)

        raise ValueError(f"Unknown instruction: {op!r}")

    # ── Entry point ──────────────────────────────────────────────────────────

    def assemble(self, source: str) -> bytes:
        """Prepend preamble and assemble to binary."""
        full = self._preamble() + "\n" + source
        lines = full.split('\n')
        self._pass1(lines)
        return self._pass2(lines)


# ── Public API ────────────────────────────────────────────────────────────────

def assemble_lark(source: str, mem_size: int = 65536) -> tuple[bytes, dict[str, int]]:
    """
    Assemble Lark-generated RV32I source.
    Returns (binary, label_map).

    label_map includes '__bootstrap' (VM entry point) and all runtime stub
    addresses so the VM can register Python intercept handlers.
    """
    asm = LarkAssembler(mem_size)
    binary = asm.assemble(source)
    return binary, dict(asm.labels)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    import parser as _parser
    import infer  as _infer
    from lower import lower
    from asm   import gen

    if len(sys.argv) < 2:
        print("usage: python3 src/riscv_asm.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)
    asm_text = gen(tac)

    binary, labels = assemble_lark(asm_text)
    print(f"Binary: {len(binary)} bytes", file=sys.stderr)
    for name in LarkAssembler.RUNTIME_STUBS + ['__global_init__', '__bootstrap', 'lark_main']:
        if name in labels:
            print(f"  {name}: 0x{labels[name]:04x}", file=sys.stderr)
