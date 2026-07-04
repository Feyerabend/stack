"""
Lark RISC-V VM — RV32I + M extension with soft runtime.
Extended from ch05/sec5.9/riscv/02/vm.py.

Additions:
  • Soft runtime: Python callbacks intercept execution at stub addresses
    (set by riscv_asm.py), replacing the need for a C runtime library.
  • Bump-pointer heap allocator inside the VM's memory bytearray.
  • sp initialised to top-of-memory; heap grows up from end of binary.
  • Entry point: labels['__bootstrap'].
  • Strings are heap objects: [4-byte length][UTF-8 bytes][null byte][pad].

Runtime functions handled:
  __heap_alloc(n_words: Int) → ptr
  print(io: IO, str_ptr) → io
  show(val: Int) → str_ptr         (integer only; float/ADT not yet typed)
  read(io: IO) → tuple_ptr         (returns heap pair (io, str))
  int_to_float(n: Int) → bits      (IEEE-754 float as uint32)
  float_to_int(bits) → n           (truncate toward zero)
  int_to_string(n: Int) → str_ptr
  float_to_string(bits) → str_ptr
  __lark_match_fail()              (halt with error message)
"""

from __future__ import annotations
import sys, os, struct
from dataclasses import dataclass


# -- Instruction (for decode) --

@dataclass
class Instruction:
    opcode: str
    rd: int = 0; rs1: int = 0; rs2: int = 0
    imm: int = 0; funct3: int = 0; funct7: int = 0


# -- VM core --

class LarkVM:
    """RV32I + M emulator with Lark soft runtime."""

    MAX_CYCLES = 50_000_000

    def __init__(self, mem_size: int = 65536) -> None:
        self.mem_size = mem_size
        self.regs     = [0] * 32
        self.pc       = 0
        self.memory   = bytearray(mem_size)
        self.running  = True
        self.failed   = False    # set by _rt_match_fail; caller checks for exit code
        self.heap_ptr = 0        # bump pointer; set after program load
        self._stubs: dict[int, object] = {}   # addr → handler callable

    # -- Loading --

    def load(self, binary: bytes, labels: dict[str, int]) -> None:
        """Load binary and wire up runtime stubs from the label map."""
        if len(binary) > self.mem_size:
            raise ValueError("Program too large for VM memory")
        self.memory[: len(binary)] = binary
        # Heap starts right after the binary (4-byte aligned)
        self.heap_ptr = (len(binary) + 3) & ~3

        # Register Python handlers for each runtime stub address.
        stub_map = {
            '__heap_alloc':    self._rt_heap_alloc,
            'print':           self._rt_print,
            'show':            self._rt_show,
            'read':            self._rt_read,
            'int_to_float':    self._rt_int_to_float,
            'float_to_int':    self._rt_float_to_int,
            'int_to_string':   self._rt_int_to_string,
            'float_to_string': self._rt_float_to_string,
            '__lark_match_fail': self._rt_match_fail,
            '__str_concat':    self._rt_str_concat,
            '__show_float':    self._rt_show_float,
            '__float_add':     self._rt_float_add,
            '__float_sub':     self._rt_float_sub,
            '__float_mul':     self._rt_float_mul,
            '__float_div':     self._rt_float_div,
            '__float_lt':      self._rt_float_lt,
            '__float_le':      self._rt_float_le,
            '__float_gt':      self._rt_float_gt,
            '__float_ge':      self._rt_float_ge,
            '__show_bool':     self._rt_show_bool,
            'string_length':   self._rt_string_length,
            'int_abs':         self._rt_int_abs,
            'float_abs':       self._rt_float_abs,
            'float_sqrt':      self._rt_float_sqrt,
            'float_floor':     self._rt_float_floor,
            'float_ceil':      self._rt_float_ceil,
        }
        for name, handler in stub_map.items():
            if name in labels:
                self._stubs[labels[name]] = handler

        # Entry point: __bootstrap initialises sp then calls lark_main.
        if '__bootstrap' not in labels:
            raise ValueError("No __bootstrap label in binary")
        self.pc = labels['__bootstrap']
        # Stack pointer: top of memory, 16-byte aligned.
        self.regs[2] = self.mem_size - 16

    # -- Helpers --

    def signed(self, val: int) -> int:
        val &= 0xFFFFFFFF
        return val - 0x100000000 if val & 0x80000000 else val

    def unsigned(self, val: int) -> int:
        return val & 0xFFFFFFFF

    def _sign_extend(self, val: int, bits: int) -> int:
        mask = 1 << (bits - 1)
        return val | (~((1 << bits) - 1)) if val & mask else val

    def _read_mem(self, addr: int, size: int, signed: bool = False) -> int:
        addr &= 0xFFFFFFFF
        if addr + size > len(self.memory):
            raise RuntimeError(f"Memory read out of bounds: 0x{addr:08x}")
        if size == 1:
            v = self.memory[addr]
            return self._sign_extend(v, 8) if signed else v
        if size == 2:
            v = struct.unpack_from('<H', self.memory, addr)[0]
            return self._sign_extend(v, 16) if signed else v
        return struct.unpack_from('<I', self.memory, addr)[0]

    def _write_mem(self, addr: int, val: int, size: int) -> None:
        addr &= 0xFFFFFFFF
        if addr + size > len(self.memory):
            raise RuntimeError(f"Memory write out of bounds: 0x{addr:08x}")
        if size == 1:   self.memory[addr] = val & 0xFF
        elif size == 2: struct.pack_into('<H', self.memory, addr, val & 0xFFFF)
        else:           struct.pack_into('<I', self.memory, addr, val & 0xFFFFFFFF)

    def _heap_alloc(self, n_bytes: int) -> int:
        """Bump-pointer allocator; returns start address."""
        n_bytes = (n_bytes + 3) & ~3   # align to 4 bytes
        addr = self.heap_ptr
        self.heap_ptr += n_bytes
        if self.heap_ptr > self.mem_size - 1024:   # leave 1 KB for stack
            raise RuntimeError("Heap overflow")
        return addr

    def _alloc_string(self, text: str) -> int:
        """Allocate a Lark string [length][bytes][null][pad] on the heap."""
        encoded = text.encode('utf-8')
        n = len(encoded)
        total = 4 + n + 1                   # length word + chars + null
        addr  = self._heap_alloc(total)
        struct.pack_into('<I', self.memory, addr, n)
        self.memory[addr+4 : addr+4+n] = encoded
        self.memory[addr+4+n] = 0
        return addr

    def _read_string(self, str_addr: int) -> str:
        """Read a Lark heap string back to Python str."""
        n = self._read_mem(str_addr, 4)
        return bytes(self.memory[str_addr+4 : str_addr+4+n]).decode('utf-8', errors='replace')

    # -- Runtime handlers --
    # Each handler reads args from self.regs, writes result to self.regs[10],
    # then sets self.pc = self.regs[1] (ra) to simulate a normal return.

    def _rt_heap_alloc(self) -> None:
        """__heap_alloc(a0=n_words) → a0=ptr"""
        n = max(1, self.signed(self.regs[10]))
        self.regs[10] = self._heap_alloc(n * 4)
        self.pc = self.regs[1]

    def _rt_print(self) -> None:
        """print(a0=io, a1=str_ptr) → a0=io"""
        str_addr = self.regs[11]
        text = self._read_string(str_addr)
        print(text)
        # a0 (io token) passes through unchanged
        self.pc = self.regs[1]

    def _rt_show(self) -> None:
        """show(a0=value) → a0=str_ptr  (integer representation)"""
        val  = self.signed(self.regs[10])
        self.regs[10] = self._alloc_string(str(val))
        self.pc = self.regs[1]

    def _rt_read(self) -> None:
        """read(a0=io) → a0=tuple_ptr  where tuple = (io, str_ptr)"""
        io_tok  = self.regs[10]
        line    = input()
        str_ptr = self._alloc_string(line)
        # Allocate 2-tuple: [tag_word=0, io, str_ptr]  (3 words)
        tup = self._heap_alloc(12)
        struct.pack_into('<III', self.memory, tup, 0, io_tok, str_ptr)
        self.regs[10] = tup
        self.pc = self.regs[1]

    def _rt_int_to_float(self) -> None:
        """int_to_float(a0=int) → a0=float_bits"""
        n    = self.signed(self.regs[10])
        bits = struct.unpack('I', struct.pack('f', float(n)))[0]
        self.regs[10] = bits
        self.pc = self.regs[1]

    def _rt_float_to_int(self) -> None:
        """float_to_int(a0=float_bits) → a0=int"""
        bits = self.regs[10] & 0xFFFFFFFF
        f    = struct.unpack('f', struct.pack('I', bits))[0]
        self.regs[10] = int(f) & 0xFFFFFFFF
        self.pc = self.regs[1]

    def _rt_int_to_string(self) -> None:
        val = self.signed(self.regs[10])
        self.regs[10] = self._alloc_string(str(val))
        self.pc = self.regs[1]

    def _rt_float_to_string(self) -> None:
        bits = self.regs[10] & 0xFFFFFFFF
        f    = struct.unpack('f', struct.pack('I', bits))[0]
        s = f"{f:.7g}"
        if '.' not in s and 'e' not in s:
            s += '.0'
        self.regs[10] = self._alloc_string(s)
        self.pc = self.regs[1]

    def _rt_str_concat(self) -> None:
        """__str_concat(a0=str_ptr1, a1=str_ptr2) → a0=result_ptr"""
        s1 = self._read_string(self.regs[10])
        s2 = self._read_string(self.regs[11])
        self.regs[10] = self._alloc_string(s1 + s2)
        self.pc = self.regs[1]

    def _f32(self, bits: int) -> float:
        return struct.unpack('f', struct.pack('I', bits & 0xFFFFFFFF))[0]

    def _f32_bits(self, f: float) -> int:
        return struct.unpack('I', struct.pack('f', f))[0]

    def _rt_show_float(self) -> None:
        """__show_float(a0=float32_bits) → a0=str_ptr (7 sig-fig display for float32)"""
        f = self._f32(self.regs[10])
        s = f"{f:.7g}"
        if '.' not in s and 'e' not in s:
            s += '.0'
        self.regs[10] = self._alloc_string(s)
        self.pc = self.regs[1]

    def _rt_float_add(self) -> None:
        self.regs[10] = self._f32_bits(self._f32(self.regs[10]) + self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_float_sub(self) -> None:
        self.regs[10] = self._f32_bits(self._f32(self.regs[10]) - self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_float_mul(self) -> None:
        self.regs[10] = self._f32_bits(self._f32(self.regs[10]) * self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_float_div(self) -> None:
        b = self._f32(self.regs[11])
        self.regs[10] = self._f32_bits(self._f32(self.regs[10]) / b if b else float('nan'))
        self.pc = self.regs[1]

    def _rt_show_bool(self) -> None:
        """__show_bool(a0=0/1) → a0=str_ptr"""
        self.regs[10] = self._alloc_string("true" if self.regs[10] else "false")
        self.pc = self.regs[1]

    def _rt_float_lt(self) -> None:
        self.regs[10] = int(self._f32(self.regs[10]) < self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_float_le(self) -> None:
        self.regs[10] = int(self._f32(self.regs[10]) <= self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_float_gt(self) -> None:
        self.regs[10] = int(self._f32(self.regs[10]) > self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_float_ge(self) -> None:
        self.regs[10] = int(self._f32(self.regs[10]) >= self._f32(self.regs[11]))
        self.pc = self.regs[1]

    def _rt_string_length(self) -> None:
        """string_length(a0=str_ptr) → a0=length_in_chars"""
        s = self._read_string(self.regs[10])
        self.regs[10] = len(s)
        self.pc = self.regs[1]

    def _rt_int_abs(self) -> None:
        """int_abs(a0=int) → a0=|int|"""
        n = self.signed(self.regs[10])
        self.regs[10] = abs(n) & 0xFFFFFFFF
        self.pc = self.regs[1]

    def _rt_float_abs(self) -> None:
        """float_abs(a0=float32_bits) → a0=|f|_bits"""
        self.regs[10] = self.regs[10] & 0x7FFFFFFF  # clear sign bit
        self.pc = self.regs[1]

    def _rt_float_sqrt(self) -> None:
        """float_sqrt(a0=float32_bits) → a0=sqrt(f)_bits"""
        import math
        f = self._f32(self.regs[10])
        result = math.sqrt(f) if f >= 0.0 else float('nan')
        self.regs[10] = self._f32_bits(result)
        self.pc = self.regs[1]

    def _rt_float_floor(self) -> None:
        """float_floor(a0=float32_bits) → a0=floor(f)_bits"""
        import math
        self.regs[10] = self._f32_bits(math.floor(self._f32(self.regs[10])))
        self.pc = self.regs[1]

    def _rt_float_ceil(self) -> None:
        """float_ceil(a0=float32_bits) → a0=ceil(f)_bits"""
        import math
        self.regs[10] = self._f32_bits(math.ceil(self._f32(self.regs[10])))
        self.pc = self.regs[1]

    def _rt_match_fail(self) -> None:
        print("ERROR: non-exhaustive pattern match", file=sys.stderr)
        self.failed  = True
        self.running = False

    # -- ECALL (exit) --

    def _handle_ecall(self) -> None:
        syscall = self.regs[17]   # a7
        if syscall == 10:         # exit
            self.running = False
        elif syscall == 1:        # print int (fallback)
            print(self.signed(self.regs[10]))
        elif syscall == 4:        # print cstring (fallback)
            addr = self.regs[10]
            chars = []
            while self.memory[addr]:
                chars.append(chr(self.memory[addr]))
                addr += 1
            print(''.join(chars), end='')
        elif syscall == 11:       # print char (fallback)
            print(chr(self.regs[10] & 0xFF), end='')

    # -- Decoder --

    def _decode(self, word: int) -> Instruction:
        opcode = word & 0x7F
        rd     = (word >>  7) & 0x1F
        funct3 = (word >> 12) & 0x7
        rs1    = (word >> 15) & 0x1F
        rs2    = (word >> 20) & 0x1F
        funct7 = (word >> 25) & 0x7F

        if opcode == 0b0110011:   # R-type
            m = {(0b0000000,0b000):'ADD',(0b0100000,0b000):'SUB',
                 (0b0000000,0b111):'AND',(0b0000000,0b110):'OR',
                 (0b0000000,0b100):'XOR',(0b0000000,0b001):'SLL',
                 (0b0000000,0b101):'SRL',(0b0100000,0b101):'SRA',
                 (0b0000000,0b010):'SLT',(0b0000000,0b011):'SLTU',
                 (0b0000001,0b000):'MUL',(0b0000001,0b001):'MULH',
                 (0b0000001,0b010):'MULHSU',(0b0000001,0b011):'MULHU',
                 (0b0000001,0b100):'DIV',(0b0000001,0b101):'DIVU',
                 (0b0000001,0b110):'REM',(0b0000001,0b111):'REMU'}
            op = m.get((funct7,funct3))
            if op is None: raise ValueError(f"Unknown R-type f7={funct7:07b} f3={funct3:03b}")
            return Instruction(op,rd=rd,rs1=rs1,rs2=rs2,funct3=funct3,funct7=funct7)

        if opcode == 0b0010011:   # I-type arith/shift
            imm = self._sign_extend(word >> 20, 12)
            ops = {0b000:'ADDI',0b100:'XORI',0b110:'ORI',0b111:'ANDI',
                   0b010:'SLTI',0b011:'SLTIU'}
            if funct3 == 0b001: return Instruction('SLLI',rd=rd,rs1=rs1,imm=imm&0x1F,funct3=funct3)
            if funct3 == 0b101:
                op = 'SRAI' if (word>>25)&0x7F==0b0100000 else 'SRLI'
                return Instruction(op,rd=rd,rs1=rs1,imm=imm&0x1F,funct3=funct3)
            return Instruction(ops[funct3],rd=rd,rs1=rs1,imm=imm,funct3=funct3)

        if opcode == 0b0000011:   # Loads
            imm = self._sign_extend(word >> 20, 12)
            ops = {0b000:'LB',0b001:'LH',0b010:'LW',0b100:'LBU',0b101:'LHU'}
            return Instruction(ops[funct3],rd=rd,rs1=rs1,imm=imm,funct3=funct3)

        if opcode == 0b0100011:   # Stores
            imm = self._sign_extend(((word>>25)&0x7F)<<5|((word>>7)&0x1F), 12)
            ops = {0b000:'SB',0b001:'SH',0b010:'SW'}
            return Instruction(ops[funct3],rs1=rs1,rs2=rs2,imm=imm,funct3=funct3)

        if opcode == 0b1100011:   # Branches
            imm = self._sign_extend(
                ((word>>31)&1)<<12|((word>>7)&1)<<11|
                ((word>>25)&0x3F)<<5|((word>>8)&0xF)<<1, 13)
            ops = {0b000:'BEQ',0b001:'BNE',0b100:'BLT',
                   0b101:'BGE',0b110:'BLTU',0b111:'BGEU'}
            return Instruction(ops[funct3],rs1=rs1,rs2=rs2,imm=imm,funct3=funct3)

        if opcode == 0b1101111:   # JAL
            imm = self._sign_extend(
                ((word>>31)&1)<<20|((word>>12)&0xFF)<<12|
                ((word>>20)&1)<<11|((word>>21)&0x3FF)<<1, 21)
            return Instruction('JAL',rd=rd,imm=imm)

        if opcode == 0b1100111:   # JALR
            imm = self._sign_extend(word>>20, 12)
            return Instruction('JALR',rd=rd,rs1=rs1,imm=imm,funct3=0)

        if opcode == 0b0110111:   # LUI
            return Instruction('LUI',rd=rd,imm=(word>>12)&0xFFFFF)

        if opcode == 0b0010111:   # AUIPC
            return Instruction('AUIPC',rd=rd,imm=(word>>12)&0xFFFFF)

        if opcode == 0b1110011:   # SYSTEM
            imm12 = word >> 20
            if imm12 == 0: return Instruction('ECALL')
            if imm12 == 1: return Instruction('EBREAK')
            raise ValueError(f"Unknown system imm {imm12}")

        raise ValueError(f"Unknown opcode: {bin(opcode)}")

    # -- Execute --

    def _step(self, instr: Instruction) -> None:
        op = instr.opcode
        r  = self.regs

        # R-type ALU --
        if op == 'ADD':   r[instr.rd]=(r[instr.rs1]+r[instr.rs2])&0xFFFFFFFF; self.pc+=4
        elif op=='SUB':   r[instr.rd]=(r[instr.rs1]-r[instr.rs2])&0xFFFFFFFF; self.pc+=4
        elif op=='AND':   r[instr.rd]=(r[instr.rs1]&r[instr.rs2])&0xFFFFFFFF; self.pc+=4
        elif op=='OR':    r[instr.rd]=(r[instr.rs1]|r[instr.rs2])&0xFFFFFFFF; self.pc+=4
        elif op=='XOR':   r[instr.rd]=(r[instr.rs1]^r[instr.rs2])&0xFFFFFFFF; self.pc+=4
        elif op=='SLL':   r[instr.rd]=(r[instr.rs1]<<(r[instr.rs2]&0x1F))&0xFFFFFFFF; self.pc+=4
        elif op=='SRL':   r[instr.rd]=(self.unsigned(r[instr.rs1])>>(r[instr.rs2]&0x1F))&0xFFFFFFFF; self.pc+=4
        elif op=='SRA':   r[instr.rd]=(self.signed(r[instr.rs1])>>(r[instr.rs2]&0x1F))&0xFFFFFFFF; self.pc+=4
        elif op=='SLT':   r[instr.rd]=1 if self.signed(r[instr.rs1])<self.signed(r[instr.rs2]) else 0; self.pc+=4
        elif op=='SLTU':  r[instr.rd]=1 if self.unsigned(r[instr.rs1])<self.unsigned(r[instr.rs2]) else 0; self.pc+=4
        # M extension
        elif op=='MUL':
            r[instr.rd]=(self.signed(r[instr.rs1])*self.signed(r[instr.rs2]))&0xFFFFFFFF; self.pc+=4
        elif op=='MULH':
            r[instr.rd]=((self.signed(r[instr.rs1])*self.signed(r[instr.rs2]))>>32)&0xFFFFFFFF; self.pc+=4
        elif op=='MULHSU':
            r[instr.rd]=((self.signed(r[instr.rs1])*self.unsigned(r[instr.rs2]))>>32)&0xFFFFFFFF; self.pc+=4
        elif op=='MULHU':
            r[instr.rd]=((self.unsigned(r[instr.rs1])*self.unsigned(r[instr.rs2]))>>32)&0xFFFFFFFF; self.pc+=4
        elif op=='DIV':
            a,b=self.signed(r[instr.rs1]),self.signed(r[instr.rs2])
            if b==0: r[instr.rd]=0xFFFFFFFF
            elif a==-0x80000000 and b==-1: r[instr.rd]=0x80000000
            else: r[instr.rd]=(int(a/b))&0xFFFFFFFF    # truncate-toward-zero
            self.pc+=4
        elif op=='DIVU':
            a,b=self.unsigned(r[instr.rs1]),self.unsigned(r[instr.rs2])
            r[instr.rd]=(a//b if b else 0xFFFFFFFF)&0xFFFFFFFF; self.pc+=4
        elif op=='REM':
            a,b=self.signed(r[instr.rs1]),self.signed(r[instr.rs2])
            if b==0: r[instr.rd]=r[instr.rs1]&0xFFFFFFFF
            elif a==-0x80000000 and b==-1: r[instr.rd]=0
            else: r[instr.rd]=(a-int(a/b)*b)&0xFFFFFFFF   # truncate-toward-zero remainder
            self.pc+=4
        elif op=='REMU':
            a,b=self.unsigned(r[instr.rs1]),self.unsigned(r[instr.rs2])
            r[instr.rd]=(a%b if b else a)&0xFFFFFFFF; self.pc+=4

        # I-type ALU --
        elif op=='ADDI':  r[instr.rd]=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; self.pc+=4
        elif op=='ANDI':  r[instr.rd]=(r[instr.rs1]&instr.imm)&0xFFFFFFFF; self.pc+=4
        elif op=='ORI':   r[instr.rd]=(r[instr.rs1]|instr.imm)&0xFFFFFFFF; self.pc+=4
        elif op=='XORI':  r[instr.rd]=(r[instr.rs1]^instr.imm)&0xFFFFFFFF; self.pc+=4
        elif op=='SLTI':  r[instr.rd]=1 if self.signed(r[instr.rs1])<self.signed(instr.imm) else 0; self.pc+=4
        elif op=='SLTIU': r[instr.rd]=1 if self.unsigned(r[instr.rs1])<self.unsigned(instr.imm) else 0; self.pc+=4
        elif op=='SLLI':  r[instr.rd]=(r[instr.rs1]<<instr.imm)&0xFFFFFFFF; self.pc+=4
        elif op=='SRLI':  r[instr.rd]=(self.unsigned(r[instr.rs1])>>instr.imm)&0xFFFFFFFF; self.pc+=4
        elif op=='SRAI':  r[instr.rd]=(self.signed(r[instr.rs1])>>instr.imm)&0xFFFFFFFF; self.pc+=4

        # Loads --
        elif op=='LB':   addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; r[instr.rd]=self._read_mem(addr,1,True)&0xFFFFFFFF; self.pc+=4
        elif op=='LH':   addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; r[instr.rd]=self._read_mem(addr,2,True)&0xFFFFFFFF; self.pc+=4
        elif op=='LW':   addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; r[instr.rd]=self._read_mem(addr,4)&0xFFFFFFFF; self.pc+=4
        elif op=='LBU':  addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; r[instr.rd]=self._read_mem(addr,1)&0xFFFFFFFF; self.pc+=4
        elif op=='LHU':  addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; r[instr.rd]=self._read_mem(addr,2)&0xFFFFFFFF; self.pc+=4

        # Stores --
        elif op=='SB':  addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; self._write_mem(addr,r[instr.rs2],1); self.pc+=4
        elif op=='SH':  addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; self._write_mem(addr,r[instr.rs2],2); self.pc+=4
        elif op=='SW':  addr=(r[instr.rs1]+instr.imm)&0xFFFFFFFF; self._write_mem(addr,r[instr.rs2],4); self.pc+=4

        # Branches --
        elif op=='BEQ':  self.pc=(self.pc+instr.imm)&0xFFFFFFFF if r[instr.rs1]==r[instr.rs2] else self.pc+4
        elif op=='BNE':  self.pc=(self.pc+instr.imm)&0xFFFFFFFF if r[instr.rs1]!=r[instr.rs2] else self.pc+4
        elif op=='BLT':  self.pc=(self.pc+instr.imm)&0xFFFFFFFF if self.signed(r[instr.rs1])<self.signed(r[instr.rs2]) else self.pc+4
        elif op=='BGE':  self.pc=(self.pc+instr.imm)&0xFFFFFFFF if self.signed(r[instr.rs1])>=self.signed(r[instr.rs2]) else self.pc+4
        elif op=='BLTU': self.pc=(self.pc+instr.imm)&0xFFFFFFFF if self.unsigned(r[instr.rs1])<self.unsigned(r[instr.rs2]) else self.pc+4
        elif op=='BGEU': self.pc=(self.pc+instr.imm)&0xFFFFFFFF if self.unsigned(r[instr.rs1])>=self.unsigned(r[instr.rs2]) else self.pc+4

        # Jumps --
        elif op=='JAL':  r[instr.rd]=(self.pc+4)&0xFFFFFFFF; self.pc=(self.pc+instr.imm)&0xFFFFFFFF
        elif op=='JALR': tmp=(self.pc+4)&0xFFFFFFFF; self.pc=(r[instr.rs1]+instr.imm)&0xFFFFFFFE; r[instr.rd]=tmp

        # Upper immediate --
        elif op=='LUI':   r[instr.rd]=(instr.imm<<12)&0xFFFFFFFF; self.pc+=4
        elif op=='AUIPC': r[instr.rd]=(self.pc+(instr.imm<<12))&0xFFFFFFFF; self.pc+=4

        # System --
        elif op=='ECALL':  self._handle_ecall(); self.pc+=4
        elif op=='EBREAK': print(f"EBREAK at pc=0x{self.pc:04x}", file=sys.stderr); self.running=False

        else: raise ValueError(f"Unknown opcode: {op!r}")

        r[0] = 0   # x0 hardwired to 0

    def run(self, debug: bool = False) -> None:
        """Execute until halt or MAX_CYCLES."""
        cycles = 0
        while self.running and cycles < self.MAX_CYCLES:
            if self.pc % 4 != 0:
                raise RuntimeError(f"PC misaligned: 0x{self.pc:08x}")
            if self.pc >= len(self.memory):
                raise RuntimeError(f"PC out of bounds: 0x{self.pc:08x}")

            # Intercept runtime stubs before fetching any instruction.
            if self.pc in self._stubs:
                self._stubs[self.pc]()
                self.regs[0] = 0
                cycles += 1
                continue

            word  = struct.unpack_from('<I', self.memory, self.pc)[0]
            instr = self._decode(word)
            if debug:
                print(f"  pc=0x{self.pc:04x}  {instr.opcode:6s}  "
                      f"rd={instr.rd} rs1={instr.rs1} rs2={instr.rs2} imm={instr.imm}", file=sys.stderr)
            self._step(instr)
            cycles += 1

        if cycles >= self.MAX_CYCLES:
            print(f"Warning: hit {self.MAX_CYCLES} cycle limit", file=sys.stderr)


# -- Public API --

def run_lark(binary: bytes, labels: dict[str, int],
             mem_size: int = 65536, debug: bool = False) -> bool:
    """Load and run a Lark binary produced by assemble_lark(). Returns True on failure."""
    vm = LarkVM(mem_size)
    vm.load(binary, labels)
    vm.run(debug=debug)
    return vm.failed


# -- CLI --

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))

    debug_flag = '-d' in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith('-')]

    if not args:
        print("usage: python3 src/riscv_vm.py <file.lark> [-d]", file=sys.stderr)
        sys.exit(1)

    import parser as _parser
    import infer  as _infer
    from lower     import lower
    from asm       import gen
    from riscv_asm import assemble_lark

    path = args[0]
    try:
        prog  = _parser.parse_file(path)
        tprog = _infer.typecheck(prog, source_file=path)
    except (*_infer.DIAGNOSTICS, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    tac      = lower(tprog)
    asm_text = gen(tac)

    if debug_flag:
        print("=== Assembly ===", file=sys.stderr)
        print(asm_text, file=sys.stderr)
        print("================", file=sys.stderr)

    binary, labels = assemble_lark(asm_text)
    failed = run_lark(binary, labels, debug=debug_flag)
    if failed:
        sys.exit(1)
