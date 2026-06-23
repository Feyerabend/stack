
## Lark — Phase 5 (the compiler)

This snapshot adds the *compiler* to the language built in phases 0–4 (lexer,
parser, type checker, CEK interpreter). A type-checked Lark program is lowered to a
three-address IR and then to *RISC-V (RV32I)* through a real backend.

Lark is *not* RISC-V-only: the same program can be run three ways, and the test
suite checks that all three agree.

```
src/
  lexer/parser/infer/...   the front end (phases 0–3)
  cek.py                   the CEK interpreter (the default way to run Lark)
  tac.py / lower.py        the three-address IR and lowering
  tac_vm.py                a TAC virtual machine (software; the correctness oracle)
  cfg/liveness/igraph/regalloc.py   analysis + linear-scan register allocation
  asm.py / riscv_asm.py    RV32I assembly emission + an assembler
  riscv_vm.py              an RV32I emulator (run compiled code with no hardware)
runtime/                   the C runtime + Pico build foundation (see ../07)
tests/                     acceptance tests (each carries its "Expected output")
docs/decisions.md          per-decision design rationale
```

### Run it

```sh
make typecheck FILE=tests/03_recursion.lark   # type-check one program
make tac_vm    FILE=tests/03_recursion.lark   # run it (TAC virtual machine)
make asm       FILE=tests/03_recursion.lark   # emit RISC-V assembly
make test                                     # full suite: CEK, TAC VM, and RV32 VM agree
```

So you can run Lark with no hardware at all (the CEK interpreter and the TAC/RV32
VMs are pure software).

### Where this goes

Next, **[`../06/`](../06/)** is the hardening phase: it keeps this same compiler
and adds cross-backend differential testing and property tests to prove the CEK,
TAC, and RV32 backends always agree.

### On a Pico

This phase already contains the `runtime/` that links compiled programs for the
**Raspberry Pi Pico 2 / 2W (RP2350, RISC-V)**. For the polished build-and-flash
workflow (`make pico` / `make flash`), the interactive REPL, the native C runtime,
and prebuilt firmware, use the final snapshot **[`../07/`](../07/)** — the same
language with the tooling completed. See the top-level [`../README.md`](../README.md)
for the whole phase-by-phase map.
