
## Lark — Phase 7 (the complete language)

This is the final, self-contained snapshot of **Lark** (Lambda Affine Resource
Kernel): a small, purely functional language with Hindley–Milner type inference,
affine ownership, and traits. Phase 7 adds a native C runtime, an interactive
REPL, and a set of standalone sample programs — and it compiles all the way down
to a **Raspberry Pi Pico 2 / 2W (RP2350, RISC-V)**.

If you just want to *run a Lark program on a Pico without installing anything*,
skip to [Run on a Pico](#run-on-a-pico-2--2w) and use the prebuilt firmware in
[`firmware/`](firmware/).

```
src/        the compiler + interpreters (lexer → parser → type checker →
            CEK interpreter, TAC IR, RV32 backend, C-CEK emitter)
tests/      acceptance tests (each carries its own "Expected output")
samples/    nine standalone example programs
runtime/    the C runtime + Pico build (see runtime/README.md)
firmware/   prebuilt .uf2 images for the samples (flash and run, no toolchain)
docs/       grammar.ebnf, decisions.md, tac.md
```

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

Lark compiles to RV32I and runs on the RP2350's RISC-V cores.

**Option A — prebuilt (no toolchain).** Hold **BOOTSEL**, plug the board in, and
copy any `firmware/*.uf2` onto the `RP2350` USB drive. See
[`firmware/README.md`](firmware/README.md) for what each one prints and how to
read the output.

**Option B — build it yourself.** You need the Raspberry Pi Pico SDK 2.2.0 and the
RISC-V toolchain installed under `~/.pico-sdk` (the
[Pico VS Code extension](https://github.com/raspberrypi/pico-vscode) installs
exactly this layout). Then:

```sh
make pico  FILE=samples/03_primes.lark   ## Lark → RV32 → runtime/build/lark_pico.uf2
make flash FILE=samples/03_primes.lark   ## build + flash a board held in BOOTSEL
```

The build details, prerequisites, and how the runtime works are in
[`runtime/README.md`](runtime/README.md).

### The pipeline, stage by stage

`lexer.py` → `parser.py` → `infer.py` (Algorithm W + affine + traits) →
`lower.py` (TAC IR) → `asm.py` (RV32 assembly) → `runtime/` (links and runs on
the Pico). The same typed program can instead be run by `cek.py` (the reference
interpreter), `tac_vm.py` (the TAC VM / oracle), or `riscv_vm.py` (an RV32
emulator) — all four agree on output, which is how correctness is checked.
