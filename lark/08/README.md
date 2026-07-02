
## Lark — Phase 8 (rigor: exhaustiveness, totality, defined Int)

This snapshot extends Phase 7 with three rigor features. No new syntax is
required to use the language — but the type checker now proves more, and the
semantics has one less undefined corner:

1. **Static exhaustiveness checking.** A `match` that does not cover every
   value of its scrutinee type is a *compile-time* error, with a witness
   pattern naming a value no arm matches (Maranget's usefulness algorithm,
   `src/exhaust.py`). Through Phase 7 this failed at runtime.

2. **Opt-in totality.** `fn total f(...) = ...` asks the checker to prove f
   terminates on every input: recursive calls must descend structurally into
   a constructor of a parameter, and f may only call functions that are
   themselves known to terminate (`src/total.py`). Termination is *relative*:
   function-typed parameters are assumed total — the caller owes the proof.

3. **Defined Int semantics.** `Int` is a wrapping 32-bit two's-complement
   integer in *every* backend, with RISC-V division rules (`x/0 = -1`,
   `x%0 = x`, `INT_MIN / -1 = INT_MIN`). The former cross-backend overflow
   divergences (and their xfail bookkeeping) are gone: all backends agree on
   all programs, including overflowing ones.

These interact: wrapping Int is *why* the totality checker refuses `n - 1`
as a decreasing argument — counting down from a negative number never
reaches zero. Recurse on data, not on integers.

```
src/        the compiler + interpreters (lexer → parser → type checker →
            CEK interpreter, TAC IR, RV32 backend, C-CEK emitter)
            new in Phase 8: exhaust.py, total.py
tests/      acceptance tests (each carries its own "Expected output")
            new: 24_exhaustive, 25_total, errors/10–14
samples/    nine standalone example programs
runtime/    the C runtime + Pico build (see runtime/README.md)
docs/       grammar.ebnf, decisions.md, tac.md
```

Prebuilt Pico firmware images live in [`../07/firmware/`](../07/firmware/);
Phase 8 builds identically from source (below).

### Run on your computer

Everything here is driven by the `Makefile` (`make help` lists all targets). No
build needed for the Python interpreters:

```sh
make typecheck FILE=samples/03_primes.lark   # type-check one program
make tac_vm    FILE=samples/03_primes.lark   # run it (TAC virtual machine)
make repl                                    # interactive REPL (:type, :help, :reset)
make samples                                 # run all nine samples
make test                                    # full acceptance suite (all backends)
```

A native C version of the interpreter is also available:

```sh
make cekbuild FILE=samples/03_primes.lark    ## emit C, compile, and run via the C CEK
```

### Run on a Pico 2 / 2W

Lark compiles to RV32I and runs on the RP2350's RISC-V cores. You need the
Raspberry Pi Pico SDK 2.2.0 and the RISC-V toolchain installed under
`~/.pico-sdk` (the
[Pico VS Code extension](https://github.com/raspberrypi/pico-vscode) installs
exactly this layout). Then:

```sh
make pico  FILE=samples/03_primes.lark   ## Lark → RV32 → runtime/build/lark_pico.uf2
make flash FILE=samples/03_primes.lark   ## build + flash a board held in BOOTSEL
```

The build details, prerequisites, and how the runtime works are in
[`runtime/README.md`](runtime/README.md).

### The pipeline, stage by stage

`lexer.py` → `parser.py` → `infer.py` (Algorithm W + affine + traits, now
followed by the totality pass and the exhaustiveness pass) → `lower.py`
(TAC IR) → `asm.py` (RV32 assembly) → `runtime/` (links and runs on the
Pico). The same typed program can instead be run by `cek.py` (the reference
interpreter), `tac_vm.py` (the TAC VM / oracle), or `riscv_vm.py` (an RV32
emulator) — all four agree on output, which is how correctness is checked.
Phase 8 makes that agreement unconditional: with Int semantics defined, no
program is allowed to diverge across backends.
