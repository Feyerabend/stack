# §9.5 — The 6502 as Contrast

`codegen6502.py` — Chapter 1's expression `(a * b) + (c * d)` compiled two ways:
for the 6502 (one accumulator, intermediates shuttled through the zero page) and
for RISC-V (every intermediate in a register).

    python3 codegen6502.py

The 6502 version spends **13 memory accesses**; the RISC-V version spends **0**.
With one usable arithmetic register, every intermediate must live in memory; with
thirty-two, none need to. (The 6502 also has no multiply instruction, so each
`*` is a subroutine call — a further reminder that the instruction set, not the
compiler, sets the floor.) This is the concrete form of the live-value question
Chapter 1 asked.
