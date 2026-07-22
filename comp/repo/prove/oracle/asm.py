"""
Lark assembler — TAC → RV32I assembly (linear-scan register allocation).

Tmps are assigned to callee-saved registers s1-s11 by linear scan; only
Tmps that spill go to stack slots.  The output links against
runtime/runtime.c for heap allocation, strings, and I/O.

Calling convention
------------------
All top-level Lark functions use the standard RV32I ABI:
  args  a0-a7, callee returns in a0, caller-saved t0-t6 / a0-a7.
The Lark `main` function is emitted as `lark_main` to avoid clashing
with the C runtime's `int main()`.

Frame layout  (s0 = fp = sp + fs)
----------------------------------
  -4(s0)                      : saved ra
  -8(s0)                      : saved s0
  -12(s0)                     : saved regs_used[0]   (first s-reg used)
  -(8 + k*4)(s0)              : saved regs_used[k-1]
  -(save_area + 4)(s0)        : spill slot 0
  -(save_area + (n+1)*4)(s0)  : spill slot n

  save_area = 8 + 4 * len(regs_used)
  fs        = (save_area + 4 * num_spills + 15) & ~15   (16-byte aligned)

Heap objects
------------
ADT/tuple   [tag_id, field0, field1, ...]   (tag_id is a 32-bit int)
Closure     [fn_ptr, cap0, cap1, ...]        (first word is the fn pointer)
String      [len, ...bytes]                   (managed by runtime)

IClosureCall dst = f(arg)
    t0 = f[0]           # fn_ptr
    a0 = f              # env (the whole closure record is the env pointer)
    a1 = arg
    jalr ra, 0(t0)
    dst = a0

IAlloc dst = tag(fields...)
    a0 = n_words        # 1 (tag) + len(fields)
    call __heap_alloc
    [a0+0] = tag_id
    [a0+4] = field0
    ...
    dst = a0

IAllocClosure dst = closure(fn; caps...)
    a0 = n_words        # 1 (fn_ptr) + len(caps)
    call __heap_alloc
    [a0+0] = &fn
    [a0+4] = cap0
    ...
    dst = a0
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tac import (
    TAC, Function, Val, Tmp, Const,
    IAssign, IBinOp, IUnary, ICall, IClosureCall,
    IReturn, ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
    Instr,
)
from regalloc import Allocation, allocate_tac


# -- Tag map ---

def _collect_tags(tac: TAC) -> dict[str, int]:
    """Assign a unique integer id to each constructor tag seen in the TAC."""
    tags: set[str] = set()
    for fn in tac.functions:
        for instr in fn.body:
            if isinstance(instr, IAlloc) and instr.tag not in ("()",):
                tags.add(instr.tag)
    return {t: i for i, t in enumerate(sorted(tags))}


def _collect_globals(tac: TAC) -> dict[str, str]:
    """
    Return {var_name: asm_label} for each top-level let binding.

    Only names in tac.global_names (set by the lowerer) get a .data slot.
    Temporary names generated inside __global_init__ are excluded — they are
    local to that function and must not be treated as globals in other
    functions where the same fresh name happens to appear.
    """
    labels: dict[str, str] = {}
    for name in sorted(tac.global_names):   # sorted for deterministic label order
        labels[name] = f".Lgvar{len(labels)}"
    return labels


# -- Tail-call detection --

def _find_tail_return(
    body: list, start: int, live: str,
    labels_map: dict[str, int],
) -> bool:
    """
    Return True if the tmp named `live` (result of a call) flows directly
    through assigns/jumps to an IReturn, with no other uses in between.
    """
    i = start
    visited: set[int] = set()
    while i < len(body):
        if i in visited:
            return False
        visited.add(i)
        instr = body[i]
        if isinstance(instr, ILabel):
            i += 1; continue
        if isinstance(instr, IJump):
            target = instr.label
            if target in labels_map:
                i = labels_map[target] + 1; continue
            return False
        if isinstance(instr, IAssign):
            if isinstance(instr.src, Tmp) and instr.src.name == live:
                live = instr.dst.name; i += 1; continue
            return False
        if isinstance(instr, IReturn):
            return (instr.val is not None
                    and isinstance(instr.val, Tmp)
                    and instr.val.name == live)
        return False
    return False


# -- Code generator --

_ARG_REGS = ["a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7"]

_BINOP_INT: dict[str, str] = {
    "+":  "add",
    "-":  "sub",
    "*":  "mul",
    "/":  "div",
    "%":  "rem",
    "&&": "and",
    "||": "or",
}


class AsmGen:
    def __init__(self, tag_ids: dict[str, int],
                 global_vars: dict[str, str] | None = None) -> None:
        self._tag_ids      = tag_ids
        self._globals      = global_vars or {}
        self._str_literals: dict[str, str] = {}
        self._str_ctr: int = 0

    def _str_label(self, s: str) -> str:
        if s not in self._str_literals:
            self._str_literals[s] = f".Lstr{self._str_ctr}"
            self._str_ctr += 1
        return self._str_literals[s]

    def gen_fn(self, fn: Function, alloc: Allocation) -> list[str]:
        regs_used = alloc.regs_used            # callee-saved regs actually used
        save_area = 8 + len(regs_used) * 4    # ra(4) + s0(4) + s-regs
        fs        = (save_area + alloc.num_slots * 4 + 15) & ~15
        ra_off    = fs - 4                     # from sp
        s0_off    = fs - 8                     # from sp

        def spill_off(k: int) -> int:
            """Byte offset from s0 for spill slot index k (0-based)."""
            return -(save_area + (k + 1) * 4)

        out: list[str] = []

        asm_name = "lark_main" if fn.name == "main" else fn.name
        out += [f".globl {asm_name}", f"{asm_name}:"]

        # Prologue: allocate frame, save ra + s0, save used callee-saved regs.
        out += [
            f"  addi sp, sp, -{fs}",
            f"  sw   ra, {ra_off}(sp)",
            f"  sw   s0, {s0_off}(sp)",
            f"  addi s0, sp, {fs}",
        ]
        for k, r in enumerate(regs_used):
            out.append(f"  sw   {r}, {-(12 + k * 4)}(s0)")

        # Move incoming parameters (a0-a7) to their allocated locations.
        for i, p in enumerate(fn.params):
            if i >= len(_ARG_REGS):
                break
            ar = _ARG_REGS[i]
            if alloc.is_reg(p):
                out.append(f"  mv   {alloc.reg[p]}, {ar}")
            elif alloc.is_spill(p):
                out.append(f"  sw   {ar}, {spill_off(alloc.slot[p])}(s0)")
            # else: unused parameter — drop it

        # Tail-call detection.
        loop_label = f".{fn.name}_loop"
        labels_map = {
            instr.name: i
            for i, instr in enumerate(fn.body)
            if isinstance(instr, ILabel)
        }
        tail_calls: set[int] = set()
        for i, instr in enumerate(fn.body):
            if (isinstance(instr, ICall) and instr.fn == fn.name
                    and instr.dst is not None
                    and _find_tail_return(fn.body, i + 1,
                                         instr.dst.name, labels_map)):
                tail_calls.add(i)

        if tail_calls:
            out.append(f"{loop_label}:")

        # Instruction selection — each call returns a fragment appended to out.
        for i, instr in enumerate(fn.body):
            out += self._instr(instr, fn, alloc, spill_off,
                               ra_off, s0_off, fs, regs_used,
                               i, tail_calls, loop_label)
        return out

    # -- Instruction selection --
    #
    # IMPORTANT: load(), store(), epilogue() are defined as closures over
    # _instr's local `out` list.  All emitted instructions — whether from
    # the helpers or from explicit out.append() calls — go to the same list
    # and therefore appear in the correct order.

    def _instr(
        self,
        instr: Instr,
        fn: Function,
        alloc: Allocation,
        spill_off,          # callable: int → int
        ra_off: int,
        s0_off: int,
        fs: int,
        regs_used: list[str],
        instr_idx: int,
        tail_calls: set,
        loop_label: str,
    ) -> list[str]:
        out: list[str] = []   # ← all helpers close over THIS list

        def load(val: Val, reg: str) -> None:
            match val:
                case Const(value=None):
                    out.append(f"  li   {reg}, 0")
                case Const(value=True):
                    out.append(f"  li   {reg}, 1")
                case Const(value=False):
                    out.append(f"  li   {reg}, 0")
                case Const(value=v) if isinstance(v, int):
                    out.append(f"  li   {reg}, {v}")
                case Const(value=v) if isinstance(v, float):
                    import struct
                    bits = struct.unpack("I", struct.pack("f", v))[0]
                    out.append(f"  li   {reg}, {bits}  # float {v}")
                case Const(value=v) if isinstance(v, str):
                    out.append(f"  la   {reg}, {self._str_label(v)}")
                case Tmp(name=n):
                    # Globals (top-level lets) always live in .data — load via la/lw.
                    # global_names excludes fresh temps, so no false positives here.
                    if n in self._globals:
                        out.append(f"  la   {reg}, {self._globals[n]}")
                        out.append(f"  lw   {reg}, 0({reg})")
                    elif alloc.is_reg(n):
                        r = alloc.reg[n]
                        if r != reg:
                            out.append(f"  mv   {reg}, {r}")
                    elif alloc.is_spill(n):
                        out.append(f"  lw   {reg}, {spill_off(alloc.slot[n])}(s0)")
                    else:
                        out.append(f"  # unallocated tmp: {n}")

        def store(reg: str, dst: Tmp) -> None:
            # Globals always written to .data; local temps use registers/spill slots.
            if dst.name in self._globals:
                out.append(f"  la   t5, {self._globals[dst.name]}")
                out.append(f"  sw   {reg}, 0(t5)")
            elif alloc.is_reg(dst.name):
                r = alloc.reg[dst.name]
                if r != reg:
                    out.append(f"  mv   {r}, {reg}")
            elif alloc.is_spill(dst.name):
                out.append(f"  sw   {reg}, {spill_off(alloc.slot[dst.name])}(s0)")
            else:
                out.append(f"  # unallocated dst: {dst.name}")

        def epilogue() -> None:
            for k, r in enumerate(regs_used):
                out.append(f"  lw   {r}, {-(12 + k * 4)}(s0)")
            out.extend([
                f"  lw   ra, {ra_off}(sp)",
                f"  lw   s0, {s0_off}(sp)",
                f"  addi sp, sp, {fs}",
                f"  ret",
            ])

        def local(lbl: str) -> str:
            return f".{fn.name}_{lbl[1:]}" if lbl.startswith('.') else lbl

        match instr:

            case ILabel(name=lbl):
                out.append(f"{local(lbl)}:")

            case IJump(label=lbl):
                out.append(f"  j    {local(lbl)}")

            case ICondJump(cond=c, true_label=t, false_label=f):
                load(c, "t0")
                out.append(f"  bnez t0, {local(t)}")
                out.append(f"  j    {local(f)}")

            case IAssign(dst=dst, src=src):
                load(src, "t0")
                store("t0", dst)

            case IBinOp(dst=dst, op=op, l=l, r=r):
                if op in _BINOP_INT:
                    load(l, "t0"); load(r, "t1")
                    out.append(f"  {_BINOP_INT[op]:<4} t2, t0, t1")
                    store("t2", dst)
                elif op == "==":
                    if isinstance(r, Const) and isinstance(r.value, str):
                        tag_id = self._tag_ids.get(r.value, -1)
                        load(l, "t0")
                        out.append(f"  li   t1, {tag_id}  # tag '{r.value}'")
                    else:
                        load(l, "t0"); load(r, "t1")
                    out.append(f"  sub  t2, t0, t1")
                    out.append(f"  seqz t2, t2")
                    store("t2", dst)
                elif op == "!=":
                    load(l, "t0"); load(r, "t1")
                    out.append(f"  sub  t2, t0, t1")
                    out.append(f"  snez t2, t2")
                    store("t2", dst)
                elif op == "<":
                    load(l, "t0"); load(r, "t1")
                    out.append(f"  slt  t2, t0, t1")
                    store("t2", dst)
                elif op == ">":
                    load(l, "t0"); load(r, "t1")
                    out.append(f"  slt  t2, t1, t0")
                    store("t2", dst)
                elif op == "<=":
                    load(l, "t0"); load(r, "t1")
                    out.append(f"  slt  t2, t1, t0")
                    out.append(f"  xori t2, t2, 1")
                    store("t2", dst)
                elif op == ">=":
                    load(l, "t0"); load(r, "t1")
                    out.append(f"  slt  t2, t0, t1")
                    out.append(f"  xori t2, t2, 1")
                    store("t2", dst)
                else:
                    load(l, "a0"); load(r, "a1")
                    out.append(f"  call __lark_{op}_str")
                    store("a0", dst)

            case IUnary(dst=dst, op=op, src=src):
                load(src, "t0")
                if op == "-":
                    out.append(f"  neg  t2, t0")
                elif op == "not":
                    out.append(f"  xori t2, t0, 1")
                else:
                    out.append(f"  # unary {op} — not handled")
                    out.append(f"  mv   t2, t0")
                store("t2", dst)

            case ICall(dst=dst, fn=callee, args=args):
                if tail_calls and instr_idx in tail_calls:
                    # Stage new arg values through a-regs before writing params
                    # to avoid clobbering param locations mid-setup.
                    for j, a in enumerate(args):
                        if j < len(_ARG_REGS):
                            load(a, _ARG_REGS[j])
                    for j, p in enumerate(fn.params):
                        if j >= len(_ARG_REGS):
                            break
                        ar = _ARG_REGS[j]
                        if alloc.is_reg(p):
                            r = alloc.reg[p]
                            if r != ar:
                                out.append(f"  mv   {r}, {ar}")
                        elif alloc.is_spill(p):
                            out.append(f"  sw   {ar}, "
                                       f"{spill_off(alloc.slot[p])}(s0)")
                    out.append(f"  j    {loop_label}")
                else:
                    for i, a in enumerate(args):
                        if i < len(_ARG_REGS):
                            load(a, _ARG_REGS[i])
                        else:
                            raise NotImplementedError("more than 8 args")
                    callee_name = "lark_main" if callee == "main" else callee
                    out.append(f"  call {callee_name}")
                    if dst is not None:
                        store("a0", dst)

            case IClosureCall(dst=dst, fn=fn_val, arg=arg):
                load(fn_val, "t0")
                out.append(f"  lw   t1, 0(t0)")   # fn_ptr = closure[0]
                out.append(f"  mv   a0, t0")       # env = closure record
                load(arg, "a1")
                out.append(f"  jalr ra, 0(t1)")
                store("a0", dst)

            case IReturn(val=val):
                if val is not None:
                    load(val, "a0")
                else:
                    out.append(f"  li   a0, 0")
                epilogue()

            case IAlloc(dst=dst, tag=tag, fields=fields):
                n = 1 + len(fields)
                out.append(f"  li   a0, {n}")
                out.append(f"  call __heap_alloc")
                out.append(f"  mv   t3, a0")
                tag_id = 0 if tag == "()" else self._tag_ids.get(tag, 0)
                out.append(f"  li   t0, {tag_id}  # {tag}")
                out.append(f"  sw   t0, 0(t3)")
                for i, fld in enumerate(fields):
                    load(fld, "t0")
                    out.append(f"  sw   t0, {(i + 1) * 4}(t3)")
                store("t3", dst)

            case IGetTag(dst=dst, src=src):
                load(src, "t0")
                out.append(f"  lw   t1, 0(t0)")
                store("t1", dst)

            case IGetField(dst=dst, src=src, idx=idx):
                load(src, "t0")
                out.append(f"  lw   t1, {(idx + 1) * 4}(t0)")
                store("t1", dst)

            case IAllocClosure(dst=dst, fn_name=callee, captured=caps):
                n = 1 + len(caps)
                out.append(f"  li   a0, {n}")
                out.append(f"  call __heap_alloc")
                out.append(f"  mv   t3, a0")
                name = "lark_main" if callee == "main" else callee
                out.append(f"  la   t0, {name}")
                out.append(f"  sw   t0, 0(t3)")
                for i, cap in enumerate(caps):
                    load(cap, "t0")
                    out.append(f"  sw   t0, {(i + 1) * 4}(t3)")
                store("t3", dst)

            case _:
                out.append(f"  # unhandled: {instr!r}")

        return out


def _data_section(global_vars: dict[str, str],
                  str_literals: dict[str, str]) -> list[str]:
    out: list[str] = []
    if global_vars:
        out.append(".section .data")
        out.append("  .p2align 2")
        for name, lbl in global_vars.items():
            out.append(f"{lbl}:")
            out.append(f"  .word 0")
    if str_literals:
        out.append(".section .rodata")
        for s, lbl in str_literals.items():
            encoded = s.encode("utf-8")
            n = len(encoded)
            byte_list = ", ".join(str(b) for b in encoded)
            # Each string is [.word len, ...bytes, 0].  The variable-length byte
            # run leaves the cursor at an arbitrary offset, so re-align to 4 bytes
            # before the next record: otherwise its .word length header is loaded
            # with a misaligned `lw`, which the Python VM tolerates but real RISC-V
            # (the Pico's Hazard3 core) traps on.
            out.append("  .p2align 2")
            out.append(f"{lbl}:")
            out.append(f"  .word {n}")
            out.append(f"  .byte {byte_list}, 0" if byte_list else "  .byte 0")
    return out


# -- Entry point --

def gen(tac: TAC, allocator=None) -> str:
    """Lower a full TAC program to a RV32I assembly string.

    `allocator` is the register-allocation strategy: a callable
    `TAC -> list[Allocation]`. It defaults to `regalloc.allocate_tac` (linear
    scan) — the O0..O3 and diff_test path, kept byte-identical. optbench passes
    `coloring.allocate_tac_color` when the O4 `regalloc_color` flag is enabled.
    The `Allocation` shape is identical either way,
    so nothing else in the generator changes."""
    if allocator is None:
        allocator = allocate_tac
    tag_ids     = _collect_tags(tac)
    global_vars = _collect_globals(tac)
    cg          = AsmGen(tag_ids, global_vars)
    allocs      = allocator(tac)

    fn_sections: list[list[str]] = []
    for fn, alloc in zip(tac.functions, allocs):
        fn_sections.append(cg.gen_fn(fn, alloc))

    lines: list[str] = []
    lines += _data_section(global_vars, cg._str_literals)
    lines.append("")
    lines.append(".section .text")
    for sec in fn_sections:
        lines += sec
        lines.append("")

    return "\n".join(lines)


# -- CLI --

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: asm.py <file.lark> [output.S]", file=sys.stderr)
        sys.exit(1)

    import parser as _parser
    import infer  as _infer
    from lower import lower
    import os

    src_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) >= 3 else os.path.splitext(src_path)[0] + ".S"

    prog  = _parser.parse_file(src_path)
    tprog = _infer.typecheck(prog, source_file=src_path)
    tac   = lower(tprog)
    asm   = gen(tac)

    with open(out_path, "w") as f:
        f.write(asm)
        f.write("\n")
    print(f"wrote {out_path}", file=sys.stderr)
