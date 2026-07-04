
## Lark - Lambda Affine Resource Kernel

Lark is a small, serious, purely functional language. It is built in this
repository phase by phase, with each phase as a sealed snapshot you can run
independently. The build is the book.

*Language properties*

- Hindley-Milner type inference
- Affine ownership as a resource discipline (no GC, no mutation)
- Traits for structured polymorphism
- CEK machine as the interpreter target
- RV32I (RISC-V 32-bit) as the compilation target, running on Raspberry Pi Pico 2W

Nearest existing language: OCaml without the imperative surface, with affine
ownership and traits added. Research precedent: Alms (Tov & Pucella, 2011).


### Folder layout

```
lark/
  01/       Phase 0 - Language design: grammar, acceptance tests, lexer
  02/       Phase 2 - Frontend: LL(1) recursive-descent parser, AST
  03/       Phase 3 - Type checker: Algorithm W, affine tracking, traits
  04/       Phase 4 - CEK interpreter: iterative machine, pattern matching, IO
  05/       Phase 5 - Compiler: TAC IR, RV32I backend, Pico 2W runtime
  06/       Phase 6 - Hardening: differential tests, Hypothesis, formal spec
  07/       Phase 7 - C CEK native runtime, REPL, nine sample programs
  08/       Phase 8 - Rigour: exhaustiveness checking, opt-in totality,
                      defined (wrapping i32) Int semantics
  09/       Phase 9 - Track C: well-typed program generator, differential
                      fuzzing, ambiguous-operator restriction

  formal/proof/   MLTT kernel (lcore + llang) and the type-soundness proof -
                  the verification side of Phase 5; not a numbered snapshot
```

Each numbered folder is self-contained and runnable. `formal/proof/` is the
specification-and-verification artifact; the proof does not change as the
language is built. The specification (`lark-formal.tex`) travels with it:
Phase 8 added a clearly-marked Part III addendum (defined Int, exhaustiveness,
totality) rather than rewriting the Phase 5-6 parts.


### Phase summary

| Folder          | Phase | What                                                        | Book ch. |
|-----------------|-------|-------------------------------------------------------------|----------|
| `01/`           | 0     | Language design: EBNF grammar, acceptance tests, lexer      | 3        |
| `02/`           | 2     | Frontend: hand-written LL(1) parser, AST dataclasses        | 4        |
| `03/`           | 3     | Type checker: Algorithm W + affine tracking + traits        | 5        |
| `04/`           | 4     | CEK interpreter: iterative, pattern matching, IO            | 6        |
| `05/`           | 5     | Compiler: TAC IR, RV32I backend, Pico 2W runtime            | 7, 9     |
| `06/`           | 6     | Hardening: differential tests, property tests, formal spec  | 8, 11    |
| `07/`           | 7     | C CEK native runtime, REPL, nine standalone samples         | 10       |
| `08/`           | 8     | Rigour: static exhaustiveness, `fn total`, wrapping i32 Int | ??       |
| `09/`           | 9     | Track C: typed-term generator, differential fuzzing         | ??       |
| `formal/proof/` | 5     | Type soundness proof in MLTT (lcore kernel)                 | 11       |

Phase numbers skip from 0 to 2 because Phase 1 was originally planned as a
formal specification before any code, then reordered: see
[Development notes](#development-notes) below.

*Test counts (07/):* 76/76 run\_tests * 31/31 difftest * 25/25 proptest *
29/29 cektest * 31/31 repltest * 9/9 samples

*Test counts (08/):* 90/90 run\_tests * 40/40 difftest * 29/29 proptest *
40/40 cektest * 31/31 repltest * 9/9 samples - no xfails, no skips: with
Int semantics defined, every backend agrees on every program (counts
include the Phase 9 ambiguous-operator fix, backported)

*Test counts (09/):* 91/91 run\_tests * 41/41 difftest * 35/35 proptest *
41/41 cektest * 41/41 santest * 31/31 repltest * 9/9 samples - and
`make fuzz` generates fresh well-typed programs on demand, so the
differential corpus is no longer bounded by what anyone thought to write
down


### Quick start

Every phase has a `Makefile`. From any numbered folder:

```sh
make test                           # run acceptance tests + error tests
make run FILE=tests/01_hello.lark   # run one program (CEK backend)
```

Phase 5+ add compiler targets:

```sh
make tac FILE=tests/02_arithmetic.lark   # TAC VM backend
make riscv FILE=tests/03_recursion.lark  # RV32I VM backend
make difftest                            # cross-backend diff (Phase 6+)
make proptest                            # Hypothesis property tests (Phase 6+)
make cektest                             # C CEK tests (Phase 7)
make repl                                # interactive REPL (Phase 7)
make samples                             # nine standalone programs (Phase 7)
```

The Phase 7 REPL accepts Lark declarations and expressions interactively,
with `:type`, `:reset`, and `:help` commands.


### Run on a Raspberry Pi Pico 2 / 2W

Lark compiles to RV32I and runs on the RP2350's RISC-V cores. The quickest way is
the *prebuilt firmware* in [`07/firmware/`](07/) - hold BOOTSEL, plug in, and
drop a `.uf2` onto the `RP2350` drive (no toolchain needed). To build it yourself:

```sh
cd 07
make pico  FILE=samples/03_primes.lark   # Lark -> RV32 -> .uf2
make flash FILE=samples/03_primes.lark   # build + flash a board in BOOTSEL
```

This needs the Pico SDK 2.2.0 + RISC-V toolchain under `~/.pico-sdk`. See
[`07/README.md`](07/) and [`07/runtime/README.md`](07/runtime/) for the full setup
and how the runtime works.


### Each phase in one line

*Phase 0* (`01/`): the design is settled on paper. `grammar.ebnf` is the
ground truth. The lexer is a single-pass state machine; every subsequent phase
carries it forward unchanged in architecture.

*Phase 2* (`02/`): one Python function per grammar rule, no backtracking.
The AST is frozen dataclasses. This is the grammar that all later phases
consume.

*Phase 3* (`03/`): Algorithm W threads substitutions; the affine context
(`tracked` set) is checked alongside. A bidirectional layer lets type
annotations on parameters and return types meet the inferred type.

*Phase 4* (`04/`): an iterative CEK machine in Python - one `while` loop,
no Python stack frames per Lark call. `sum_to(1_000_000)` runs without stack
overflow. Trait dispatch, IO, and pattern matching are all handled here.

*Phase 5* (`05/`): the full compiler pipeline. TAC IR -> control-flow graph
-> liveness analysis -> interference graph -> linear-scan register allocator ->
RV32I instruction selection. Programs run on Pico 2W hardware over USB CDC.

*Phase 6* (`06/`): three backends (CEK, TAC VM, RV32 VM) run every test and
diff outputs. Hypothesis generates random Lark programs to stress-test affine
tracking and Copy transparency. `lark-formal.tex` extends the proof-phase
specification to the full language surface.

*Phase 7* (`07/`): `cek.c` is a C port of the Python CEK machine. A single
`larkrun` binary runs the full pipeline natively without Python. The REPL
accumulates session state and re-typechecks incrementally. Nine sample programs
demonstrate idiomatic Lark.

*Phase 8* (`08/`): three rigour features. Non-exhaustive matches become
compile-time errors with a witness pattern (Maranget's usefulness algorithm).
`fn total` opts a function into a structural termination check. And `Int` is
defined as a wrapping i32 with RISC-V division rules in every backend, which
deletes all cross-backend xfail bookkeeping - agreement is now unconditional.

*Phase 9* (`09/`): the differential corpus stops being hand-written.
`tests/gen_prog.py` generates random well-typed programs by inverting the
typing rules (affine discipline included) and runs each on all three
backends, which must agree byte-for-byte (`make fuzz`). Its first catch was
real: the RV32 backend miscompiled polymorphic `+` inside a generalised
lambda (integer `add` on string pointers); the checker now rejects operators
whose operand type is not concrete at generalisation time. The frontend
gained a fuzzed no-traceback guarantee (any input gets a positioned
diagnostic, never a Python stack trace), and `make santest` runs the C CEK
corpus under ASan + UBSan - zero findings.


### Development notes

These are the moments from the build that were surprising, non-obvious, or
illuminate how the language works. Per-decision rationale is in each phase's
`docs/decisions.md`.



#### Why Phase 1 was reordered

The original plan placed a machine-checked formal specification *before* any
implementation - proof as design ground truth. In practice, the type rules were
designed and documented through building: `notes.md`, `decisions.md`, and
working tests were the real record. When `formal/proof/` encoding began (after
Phase 4), it became a *verification* exercise, not a design exercise.

This changes the epistemology: the implementation is not derived from the proof;
the proof checks the implementation. Encoding Lark's type judgment in lcore
after the fact surfaced one genuine discrepancy (the `weaken` issue below) and
confirmed everything else.

*Consequence:* the phase numbering skips from 0 to 2. Phase 1 became
Phase 5 and lives in `formal/proof/`.



#### The `weaken` primitive in the type soundness proof

The type soundness proof (`formal/proof/lark/lark-*.lcore`) encodes the typing
judgment intrinsically: `Expr Γ τ` is simultaneously a well-typed expression
*and* a typing derivation.

The substitution lemma required a `weaken` operation: moving an expression from
context `Γ` to an extended context `Γ, a`. A pure lcore encoding via
`indrec Expr` is blocked because `ext a (ext a' Γ)` and `ext a' (ext a Γ)` are
not definitionally equal in MLTT - context commutativity is a propositional, not
definitional, equation.

The fix: `weaken` was added as a C primitive to the lcore kernel
(`TM_WEAKEN` in `eval.c`). Every other proof step is encoded purely. This is
documented in `formal/proof/README.md` and is the only discrepancy between the
specification and what lcore can verify automatically.

*Lesson:* intrinsic encodings hit definitional equality limits sooner than
extrinsic ones. For a first machine-checked proof, this is an acceptable
trade-off; fixing it would require either congruence closure or an extrinsic
encoding.



#### The affine IO idiom

Lark's IO token is an affine value. A function that needs to print inside a
recursive call can't pass the IO token into both branches of an `if` - the
type checker rejects it as a use-twice violation.

The canonical idiom is: build output as a pure `String` using recursion, then
call `print` exactly once at the end.

```
fn lines(n : Int, acc : String) : String =
  if n == 0 then acc
  else lines(n - 1, acc + show(n) + "\n")
in
print(lines(10, "")) io
```

All nine sample programs in `07/samples/` follow this pattern. It is not a
workaround - it is the structurally correct shape for IO in an affine language.



#### Float semantics across three backends

IEEE 754 negative-value ordering is reversed under signed integer comparison:
`-1.0` as a bit pattern is a large unsigned integer. The RV32I `slt` instruction
would give the wrong result for negative float comparisons. Float comparison uses
runtime stubs (`__float_lt`, `__float_le`, etc.) across all three backends.

Consistency also required uniform f32 rounding: Python's `float` is 64-bit, but
the RISC-V backend uses 32-bit registers. Every float operation and display
function in every backend now applies `:.7g` formatting with a `.0` suffix
guarantee. This was the last category of CEK/TAC/RV32 output divergence.



#### The CPython id reuse bug in `emit_c_ast.py`

`emit_c_ast.py` (Phase 7) converts the Python typed AST to static `const` C
structs, memoising shared subtrees by Python object id. The compiler generates
synthetic `TLambda` wrappers to handle multi-argument application. When those
wrappers were not kept alive - only referenced by local variables in the
desugaring loop - CPython's garbage collector freed them. Their ids were then
reused by other objects. Two separate syntactic forms (`compose` and `twice`)
ended up with the same memoised id and therefore the same C struct body.

Fix: `Emitter._synthetic` is a list that holds all synthetic nodes alive for
the duration of the emit pass.

*Lesson:* Python object id is not a stable identity across GC boundaries.
Any memoisation that stores `id(obj)` as a key must also keep `obj` alive.



#### 32-bit integer overflow (xfail through Phase 7, defined in Phase 8)

Through Phase 7, `sum_to(1_000_000)` gave the wrong result in the RV32I VM
because RV32I arithmetic is 32-bit and Python's integers are arbitrary
precision. The test was marked `xfail` because fixing it would have required
64-bit integers or bignums.

Phase 8 resolves it the other way around: instead of making the RV32 backend
match Python, the *semantics* is defined as what the hardware does. `Int` is a
wrapping 32-bit two's-complement integer with RISC-V division rules in every
backend (the Python VMs mask to i32; the C CEK computes in `uint32_t`). The
xfail is deleted - all backends agree on all programs, including overflowing
ones. A pleasant side effect: the totality checker can honestly refuse `n - 1`
as a decreasing argument, because under wrapping semantics it genuinely isn't.


### Further reading

- `0N/docs/decisions.md` - per-decision design rationale for each phase;
  these become the "Design Decision" sidebars in the book
- `formal/proof/README.md` - the lcore MLTT kernel and the type soundness proof
- `07/samples/` - nine standalone Lark programs with comments


### License

To the extent possible under law, Set Lonnert has waived all copyright and
related or neighboring rights to Lark. The work is dedicated to the public
domain under the Creative Commons CC0 1.0 Universal dedication; see the
`LICENSE` file or <https://creativecommons.org/publicdomain/zero/1.0/>.
