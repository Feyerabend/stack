
## Chapter 09 — Code Generation

Companion code for Chapter 9 of *The Language Stack: From Silicon to Semantics*.
Organised by section; each folder matches a §9.x heading in the book.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `02_instruction_selection/` | §9.2 Instruction Selection | `isel.py` — maximal-munch tree matching; folds `lw off(base)` and `addi` where a naive selector spends several instructions |
| `03_register_allocation/` | §9.3 Register Allocation | `regalloc.py` — linear scan *and* graph colouring on one IR, with spilling at `k=3` and a verifier (the chapter's centrepiece) |
| `04_riscv/` | §9.4 Targeting RISC-V | `01/` a concise RV32I (+M) manual with a small assembler, VM, and sample programs (`fact`, `fib`, `array`) — the direct assemble-and-run path; `02/` a fuller RISC-V toolchain (assembler, object files, linker, VM) — assemble, link, run |
| `05_the_6502/` | §9.5 The 6502 as Contrast | `codegen6502.py` — Chapter 1's `(a*b)+(c*d)` to the 6502 (13 memory accesses) vs RISC-V (0) |
| `06_tail_calls/` | §9.6 Tail-Call Elimination | `tail.py` and `general.py` — tail recursion and how it becomes iteration |

The Lark snapshot for this chapter is `lark/05/src/` — the compiler back end:
`regalloc.py` (linear-scan register allocation), `asm.py` (instruction selection,
frame layout, and the tail-call-to-loop transform), and `riscv_asm.py` (the
two-pass assembler). The runtime that links and flashes the result for a
Raspberry Pi Pico 2W is `lark/05/runtime/`.

*Supplementary:* `jit/` — a small JIT compiler (HotSpot-style). Just-in-time
(runtime) code generation is an alternative the chapter does not pursue; it is
kept here as a point of contrast to Lark's ahead-of-time compilation.

Every section §9.2–§9.6 now has a runnable companion (each folder has its own
README; the `.py` files run standalone with no arguments).
