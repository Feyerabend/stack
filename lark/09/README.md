
## Lark — Phase 9 (Track C: generate, then fuzz)

This snapshot extends Phase 8 with the first step of Track C — *verification
and testing deepening*. No new language features: the deliverable is a tool
that manufactures test programs, and the first bug it caught.

1. **A well-typed program generator** (`tests/gen_prog.py`). Where the
   Phase 6 property tests instantiate a handful of fixed templates, the
   generator builds whole random programs by *inverting the typing rules*
   (Palka et al. 2011): pick a goal type, pick a rule whose conclusion
   produces it, recurse into the premises. Programs are well typed by
   construction — including the affine discipline (IO threaded linearly,
   non-Copy ADTs consumed at most once) — and terminate by construction
   (helper call graphs are DAGs). Hypothesis drives the choices, so any
   failing program shrinks to a minimal counterexample.

2. **Differential fuzzing with a built-in oracle** (`make fuzz`). Every
   generated program runs on all three backends — CEK, TAC VM, RV32 VM —
   and their outputs must be byte-identical (the Phase 6 diff_test oracle,
   now fed by a generator instead of a fixed corpus). Two properties join
   the suite: P6, every generated program typechecks; P7, every generated
   program runs identically everywhere.

3. **Frontend robustness as a property** (`tests/fuzz_frontend.py`).
   P8: *no input ever produces a Python traceback* — random unicode,
   token soup, mutated programs, and pathological nesting all get a
   positioned diagnostic or a typed program. Fuzzing found and fixed
   three violations: unbounded recursion on deep input (now a
   per-declaration node budget in the parser), and two lexer holes
   around unicode digits and giant literals.

4. **Sanitizers as a standing target** (`make santest`). The C CEK
   corpus builds and runs under ASan + UBSan with zero findings — the
   Phase 8 uint32_t arithmetic is UB-free by construction. The harness
   is validated with planted UB before its silence is trusted.

5. **The hardening pass.** A systematic review with the new tools in
   hand closed a second affine soundness hole: a closure capturing an
   affine variable (`let g = fn(x) => io in (g(1), g(2))`) duplicated
   the resource without the name ever appearing twice — closures are
   Copy, so capture of affine values is now rejected outright (error
   test 16). All five CLI runners now share one diagnostics contract
   (`infer.DIAGNOSTICS`): a one-line error and exit 1, never a
   traceback — the same tuple the P8 fuzzer accepts, so the CLI surface
   and the fuzzed property cannot drift apart.

6. **Certified register allocation** (`src/regcheck.py`). Every
   compilation independently validates the allocator's output — its own
   liveness, its own successor map, sharing only the instruction set —
   and `asm.gen()` refuses to emit code that fails the certificate.
   Validated by mutation in both directions: planted allocator bugs are
   caught with named clobber sites; a semantically safe off-by-one is
   correctly left alone.

7. **The first catch: the ambiguous-operator hole.** Fuzzing immediately
   found `let f = (fn(x) => x + x) in f("uh oh")`: `+` is ad-hoc
   polymorphic, and inside the generalised lambda its operand type is still
   a type variable. The interpreters dispatch on the runtime value (string
   concat), but the RV32 backend commits to integer arithmetic at compile
   time — and added the string *pointers*, printing garbage memory. The
   checker now rejects any operator whose operand type is not concrete when
   the enclosing declaration is generalised (error test 15) — a
   monomorphism restriction on operators, so no backend ever sees a program
   it would miscompile.

The generator earns its keep twice over: it also *discovered the checker's
own conservatism* — `show` on a never-constrained lambda parameter is
rejected ("no Show instance for α"), so the generator tracks groundedness
the same way it tracks affine use. Inverting the real rules, not the rules
you assumed, is the point of P6.

```
src/        the compiler + interpreters (lexer → parser → type checker →
            CEK interpreter, TAC IR, RV32 backend, C-CEK emitter)
            changed in Phase 9: infer.py (ambiguous-operator restriction,
            affine-capture rule), parser.py (node budget), lexer.py
            (literal diagnostics); new: regcheck.py (certifying regalloc)
tests/      acceptance tests (each carries its own "Expected output")
            new: gen_prog.py (the generator + P6/P7), fuzz_frontend.py
            (P8 no-traceback), errors/15_ambig_op
samples/    nine standalone example programs
runtime/    the C runtime + Pico build (see runtime/README.md)
docs/       grammar.ebnf, decisions.md, tac.md
```

### Run on your computer

Everything here is driven by the `Makefile` (`make help` lists all targets). No
build needed for the Python interpreters:

```sh
make test                 # full acceptance suite (all backends)
make proptest             # property-based tests, incl. P6/P7/P8
make fuzz N=500           # differential fuzzing: 500 fresh random programs
make santest              # C CEK corpus under ASan + UBSan
python3 tests/gen_prog.py show 5     # eyeball five generated programs
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

`lexer.py` → `parser.py` → `infer.py` (Algorithm W + affine + traits +
totality + exhaustiveness, now closed against ambiguous operators) →
`lower.py` (TAC IR) → `asm.py` (RV32 assembly) → `runtime/` (links and runs
on the Pico). The same typed program can instead be run by `cek.py` (the
reference interpreter), `tac_vm.py` (the TAC VM / oracle), or `riscv_vm.py`
(an RV32 emulator) — all four agree on output, which is how correctness is
checked. Phase 8 made that agreement unconditional; Phase 9 makes it
*enforced by search*: random well-typed programs now hunt for divergence
continuously instead of waiting for a hand-written test to stumble on one.
