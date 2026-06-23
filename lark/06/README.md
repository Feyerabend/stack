
## Lark — Phase 6 (hardening)

This snapshot is the *same compiler as [phase 5](../05/)* (the `src/` is
identical) with the testing turned up: the three execution paths are diffed
against each other and the type checker is stress-tested with generated programs.

Lark runs three ways — the **CEK interpreter**, the **TAC virtual machine**, and
the **RV32I emulator** — and phase 6 exists to prove they always agree before the
language is compiled to real RISC-V hardware.

```
src/                 the compiler (identical to phase 5)
tests/               acceptance tests + generators
runtime/             the C runtime + Pico build foundation (see ../07)
docs/decisions.md    per-decision design rationale
```

### Run it

```sh
make test       # acceptance suite across all backends
make difftest   # cross-backend diff: assert CEK == TAC VM == RV32 VM on every test
make proptest   # property-based tests (Hypothesis) for the type checker
make tac_vm FILE=tests/03_recursion.lark   # run a single program (TAC VM)
```

None of this needs hardware — the backends are all software.

### On a Pico

As with phase 5, the `runtime/` here is the foundation for the **Pico 2 / 2W
(RP2350, RISC-V)** build. For the complete build-and-flash workflow, the REPL, the
native C runtime, and prebuilt firmware, use the final snapshot
*[`../07/`](../07/)*.
