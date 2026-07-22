
## Self-Hosting Lark - Project Plan

> **Keep the work log.** Progress is recorded in [`LOG.md`](./LOG.md).
> After any `/clear`, read `LOG.md` for the current position - and **append an
> entry there whenever you do work on this plan.** The plan is the map; the log
> is where you are on it.

**Status:** OK **M0-M7 COMPLETE** - F2⁺ frozen (2026-07-08), O5' optimizing fixpoint
closed (M7.5, 2026-07-11) - **Started:** 2026-07-07
**> ACTIVE: M6 / F3 - cross-compiling to bare metal** (re-scoped 2026-07-11; ladder
F3.1-F3.4 in §4). Was a "stretch"; it is now the nearest axis, because M7 already ported
most of its original list. Real surface = **`asm.py` + `regalloc.py`, ~822 lines**.
*(PROVE.md remains the deeper next axis, and is orthogonal - F3 costs it no rework.)*
**Goal:** rewrite the Lark toolchain *in Lark* and have it compile itself. - *Done:
the self-hosted compiler lexes, parses, **type-checks**, and emits C, reproduces its
own emitted C byte-identically (F2 fixpoint), and rejects ill-typed programs with the
oracle-identical diagnostic (F2⁺). One residual - the native binary fixpoint of the
larger typechecking compiler - is OPTIMIZE-gated by the O(n²) arena join; handed to
`OPTIMIZE.md` §8 as its motivated first win. Baselines pinned in
`self/tests/BASELINES.md`.*

This is the successor effort to the Phase 0-7 build (now complete; its notes are
archived in `../old/`). Where the original build asked *"can we build the
language?"*, this one asks *"is the language strong enough to build itself?"* -
the traditional coming-of-age test for a serious language.

---

## 1. Definition of done

Three fixpoints, in increasing strength. Each is a real, defensible milestone;
we stop wherever the payoff/effort trade stops being worth it.

- **F1 - Meta-circular interpreter.** A lexer + parser + typechecker + CEK
  evaluator, all written in Lark, that correctly runs the entire `.lark` test
  suite *including its own source*. First light: Lark interpreting Lark.
- **F2 - True self-hosting (the fixpoint).** The Lark-written compiler emits C
  (via the existing `emit_c_ast` path), which the C runtime compiles to a
  binary. Then:
  - stage-0: the Python compiler compiles `lark-in-lark` → **stage-1** binary.
  - stage-1: compiles its own source → **stage-2** binary.
  - **stage-1 and stage-2 are byte-identical.** That equality is the proof.
- **F3 - Pico self-hosting (stretch).** Self-host the TAC IR + RISC-V backend +
  register allocator too, so `lark-in-lark` targets RV32I and runs on the
  Pico 2W. The build closes on the metal.

We commit to **F1 and F2**. F3 is a stretch that turns the book's "silicon to
semantics" arc into a literal loop.

---

## 2. Feasibility summary

**Ready.** The language already has everything a compiler front/middle end
needs: parametric algebraic data types, exhaustive `match`, traits/`impl`,
recursion, curried functions, tuples, `String` + concatenation + `show`, and
linear `IO`. Pure affine FP is close to an ideal substrate for a compiler.
Proof of concept already in-tree: `07/samples/09_parser.lark` is a 261-line
recursive-descent parser written in Lark.

**The one real gap - string decomposition.** The runtime exposes only
`string_length`, `int_to_string`, `float_to_string`. There is **no way to read
the characters of a string**, so a lexer cannot be written in Lark today. This
is the critical path and the whole of Milestone M0. It is small and contained:
it is the only place we touch the Python/C runtime - everything after M0 is Lark.

**Affine wrinkle to settle in M0.** Source text is indexed thousands of times.
`String` must be usable non-linearly (an `impl Copy for String`, justified by
immutability) or every pass has to thread the source token by token. Decide this
in M0; it colours every later module.

---

## 3. What we are porting

The current toolchain is **~5,840 lines of Python** in `07/src/` (plus the C
runtime `cek.c`/`cek.h`/`larkrun.c`). Line counts drive the effort estimates
below - they are the Python source, and Lark tends to run 1.0-1.3× that.

| Python source | Lines | Role | Self-host module | Difficulty |
|---|--:|---|---|---|
| `lexer.py` | 394 | source → tokens | `lex.lark` | M1 - low (needs M0) |
| `parser.py` | 555 | tokens → AST | `parse.lark` | M2 - medium |
| `tree.py` | 241 | untyped AST types | `ast.lark` | M2 - low |
| `ty.py` | 265 | type representations | `types.lark` | M3 - medium |
| `typed_tree.py` | 172 | typed AST | `tast.lark` | M3 - low |
| `infer.py` | 950 | Algorithm W + affine + traits | `infer.lark` | M3 - **high** |
| `emit_c_ast.py` | 461 | typed AST → C | `emit_c.lark` | M5 - medium |
| `cek.py` | 706 | CEK evaluator | `cek.lark` | M4 - medium |
| `tac.py` + `lower.py` | 835 | IR + lowering | `tac.lark` | F3 - high |
| `cfg.py`/`liveness.py`/`igraph.py`/`regalloc.py` | 760 | backend analyses | `regalloc.lark` | F3 - high |
| `riscv_asm.py` | 499 | RV32I emission | `riscv.lark` | F3 - high |

`infer.py` is the mountain: union-find, substitution, generalization,
trait resolution, and affine-use checking - all in a language with no mutation.
Expect union-find as a persistent structure (map + path re-rooting) rather than
in-place. This is the intellectually hardest and most rewarding part.

---

## 4. Milestone ladder

### M0 - Unblock the lexer OK *(done 2026-07-07; runtime; the only non-Lark work)*
Add string primitives to **both** runtimes (`07/src/cek.c` **and** `07/src/cek.py`,
kept in lock-step) plus wire them through the lexer/typechecker's primitive
table. Proposed set:

- `string_index : String -> Int -> Int` - codepoint at index; O(1); defined
  bounds behaviour (return `-1` past end, or pair with a length guard).
- `string_slice : String -> Int -> Int -> String` - substring `[lo, hi)`; lets
  the lexer slice whole lexemes instead of `O(n²)` char-by-char concat.
- `char_to_string : Int -> String` - build a 1-char string from a codepoint.
- `string_to_int : String -> Option(Int)` - parse integer literals.

Character classification (`is_digit`, `is_alpha`, ...) needs **no** new prims -
it is codepoint range comparison in Lark. Also settle the `Copy for String`
question here.

**Done when:** each new prim has CEK-C and CEK-Python parity tests, and a throwaway
`lex_smoke.lark` can index/slice a source string end to end.

> **M0 outcome (2026-07-07):** all four prims landed in both CEK runtimes with
> byte-identical parity (`tests/24_stringprims.lark`, `make cektest` 31/31).
> `self/lex_smoke.lark` is a working cursor-based mini-lexer. Deviations from the
> proposal, both recorded in §7: `string_to_int` returns `Result` (not `Option`,
> which is user-level); `Copy for String` needed no work (already in
> `BUILTIN_COPY`). New language finding logged in §7 (affine-across-branches).

### M1 - `lex.lark` OK *(done 2026-07-07)*
Port `lexer.py`. The lexer walks an `Int` cursor over the (Copy) source string,
slicing lexemes. **Validation:** differential - token stream of `lex.lark` vs
`lexer.py` over all `.lark` files must match exactly.

> **M1 outcome (2026-07-07):** `self/lex.lark` is a faithful port of `lexer.py`
> (kinds, keywords, int/float/string/comment scanning, all operators, 1-based
> line/col). Cursor state is a single `Copy` value `Pos(pos,line,col)` threaded
> through `let` + accessor functions (Lark's `let` binds one name and cannot
> destructure). Differential harness `self/tests/lex_difftest.py` generates a
> driver per corpus file (embeds the source as a String literal, prints
> `dump(tokenize ...)`) and diffs it against a Python serialization of
> `lexer.py`'s tokens - **46/46 files identical, including `lex.lark` lexing its
> own 2776-token source.** Run: `make -C self lextest`.
>
> **Language finding (logged §7):** string `==` typechecks (Eq is polymorphic)
> but is **unimplemented in the CEK `binop`** - only string `+` is. Keyword
> lookup therefore uses `match` on string-literal patterns (which route through
> `_val_eq`, and do compare strings), not the `==` operator.

### M2 - `ast.lark` + `parse.lark` OK *(done 2026-07-07)*
Port `tree.py` (AST types) then `parser.py`, growing the `09_parser` sample into
the full grammar. **Validation:** pretty-printed AST of `parse.lark` vs
`parser.py` over the whole corpus.

> **M2 outcome (2026-07-07):** `self/parse.lark` is a faithful port of both
> `tree.py` (the full AST as ADTs) and `parser.py` (hand-written LL(1) recursive
> descent). The token cursor is a `List(Token)` threaded as a **Copy** value;
> every parse function returns `(Node, List(Token))` (node + remaining tokens),
> the functional analogue of `self.pos`. "Expect kind K" is a structural match on
> the head token (`Cons(Tok(KUpper, name, _, _), rest)` grabs text + tail in one
> step); guaranteed tokens are dropped with `advance`. The AST types carry
> `impl Copy` so a node can be reused across `match` arms (the precedence tails
> reuse `left` in every arm - the affine-across-branches wart, §7); Copy impls are
> name-only in infer, so this is free. Literals: INT/FLOAT keep the lexeme text
> (`str(int|float)` round-trips it - verified 0 mismatches over the corpus),
> STRING carries the escape-processed value to match `tok.value`.
>
> Combined AST-types + parser + an S-expression pretty-printer in **one file**
> (the tree.py/parser.py split isn't worth two Lark modules). Serialization is a
> canonical parenthesized S-expr, one line per top-level import/decl; the Python
> mirror lives in the harness. Differential harness `self/tests/parse_difftest.py`
> = **47/47 files byte-identical, including `parse.lark` parsing its own
> 139-declaration source** (and `Stdlib.lark`, all samples/tests). Strictness
> re-verified: a one-token serializer perturbation fails immediately. Run:
> `make -C self parsetest`.
>
> **Composition finding (logged §7):** parse.lark is written as a *component*
> that `import Lex`es the tokenizer, but the differential driver is built by
> **concatenation** (lex body + parse body + generated main, one module) - because
> the toolchain's *import* path re-type-checks the imported module WITHOUT infer's
> mutual-recursion pre-registration (Pass 1.5), so lex.lark's forward references
> (`read_name → keyword_kind`) fail on import though lex.lark type-checks
> standalone. Concatenation routes the whole program through the normal top-level
> typechecker, which pre-registers. A real toolchain gap, not a language one.

### M3 - the typechecker *(the hard core)* OK *(done 2026-07-08)*
Port `ty.py` → `types.lark`, `typed_tree.py` → `tast.lark`, then `infer.py` →
`infer.lark` (Algorithm W, persistent union-find, generalization, trait
resolution, affine-use checking). **Validation:** for every test file, the
inferred top-level types and the accept/reject verdict must match `infer.py`,
including the error-test suite (right programs rejected for the right reason).

> **M3 COMPLETE (2026-07-08).** All three slices done: `types.lark` (ty.py),
> `tast.lark` (typed_tree.py), and `infer.lark` (~1213 lines - Algorithm W +
> affine + trait bounds, threaded purely: `fresh`=Int, affine `tracked` as an
> assoc list, `env`/`Subst` as assoc lists, every failure an explicit result
> ADT). Passes mirror infer.py (Pass 1 registration → Pass 1.5 sig pre-register →
> Pass 2 check); entry `checkProgram` prints the normalised top-level signature
> block or `type error: <msg>`. Differential harness `self/tests/infer_difftest.py`
> (`make -C self infertest`) runs infer.py's `typecheck` **in-process** as oracle,
> serialises its TProgram to the *same* normalised block the port prints, and
> compares over the corpus: **42 ok / 0 fail / 2 skipped.** Every single-file test
> matches - 24 feature tests, `Stdlib.lark`, all 9 samples (incl. the self-hosted
> parser `09_parser.lark` type-checking itself), and the full error suite (6 real
> rejects match by message; `04_nonexhaustive`/`06_matchfail` correctly *accept* -
> infer.py checks no exhaustiveness). The 2 skips are exactly the two `import`
> files (the single-file port has no import path - same reason M4 inlines).
> **07/ oracle untouched.** lex+parse+infer+cek are now all differentially green.

### M4 - first light: meta-circular interpreter *(F1)*
Port `cek.py` → `cek.lark`. Now `lex → parse → infer → cek`, all in Lark, is a
complete interpreter. **Validation:** it runs all 9 samples + the acceptance
suite, then runs *its own source file* and reproduces the reference outputs.
**F1 reached.**

> **M4 evaluator FEATURE-COMPLETE for the slice (2026-07-07).** `self/cek.lark`
> is a faithful port of `cek.py`'s CEK machine. Differential harness
> `self/tests/cek_difftest.py` = **29 corpus + 4 read = 33 ok / 0 fail / 15
> skipped**; the 15 skips are all legitimate (oracle-rejected library files with
> no `main`, error-suite files, or corpus programs whose meta-circular evaluation
> exceeds the 90 s budget - a *performance* verdict, not correctness). Feature
> coverage: int/bool/string/list/tuple/ADT/recursion, **float arithmetic + non-
> arith float builtins**, **custom trait-method dispatch** (RDispatch + con→type
> map), **multi-module `import`** (resolved by the harness *inlining* each module's
> decls into the object source - the same flattening used for lex+parse+cek, since
> the toolchain's real import path skips Pass 1.5, §7), and **`read` (stdin)** -
> the IO token `RIO of String` carries the pending stdin, threaded by the
> program's own `io` sequencing, so `read` peels the next line exactly like the
> oracle (EOF → ""); validated by a dedicated echo-program differential
> (oracle piped stdin vs port embedded input). **07/ oracle untouched throughout.**
> What remains before F1 proper is not features but the interpretive tower's cubic
> cost (removed by a compiled bootstrap, F2); so the productive next step is M3's
> `infer.lark`, not more M4.

### M5 - true self-hosting *(F2)* - **fixpoint closed 2026-07-08**
Port `emit_c_ast.py` → `emit_c.lark`. Wire the full front+middle end to C
emission. Run the two-stage bootstrap and diff the emitted C across stages.
**F2 reached - the fixpoint closes: C1 == C2 == C3, byte-identical.**

- OK **`self/emit_c.lark`** (~445 lines) ports the emitter, driving off the
  **syntactic** `Prog` (the emitter never reads inferred types; the typed AST is a
  structural copy). Differential `self/tests/emit_c_difftest.py` (`make -C self
  emittest`) = **37 ok / 0 fail / 7 skip** - the emitted C is byte-identical to
  `emit_c_ast.py` on every self-containable corpus file, incl. `09_parser.lark`
  (851 C lines) AND both multi-module `import` programs. 7 skips = the 7
  oracle-rejected error-suite files (nothing else left in the port's control).
- OK **Import inlining** on the emit path - flattens a multi-module program to the
  decl stream the oracle's emitter core sees, reproducing the oracle's double-emit
  of imported decls (see the double-inline finding below).
- OK **The two-stage bootstrap - fixpoint closed.** `self/tests/bootstrap.py`
  (`make -C self bootstrap`) assembles lex+parse+emit_c into a stdin-driven
  compiler (`compiler.lark`, ~1844 lines; a new whole-stdin `read_all` prim lets
  it read its own source) and runs the ladder: the Python oracle builds `stage1`,
  then `stage1 < compiler.lark → C1 → stage2`, `stage2 → C2 → stage3`, `stage3 →
  C3`. **C1 == C2 == C3 byte-identical (sha `2ce6a281`)** - the self-hosted
  compiler reproduces its own emitted C. This is the F2 fixpoint proper; the text
  differential proved the emitter correct on the corpus, this proves the loop
  closes on the compiler itself.
- **Why the *C-source* fixpoint, not the binary.** The emitter is deterministic
  and reads only the syntactic AST, so C1==C2==C3 is build-environment
  independent - the strong, portable proof. Native binary equality is
  Mach-O-nondeterministic on macOS (per-link `LC_UUID`, embedded input/output
  paths); with `-Wl,-no_uuid` + identical paths held across links, `stage2 ==
  stage3` did go byte-identical too, but that equality is a property of the
  toolchain's build determinism, not of the self-host compiler, so it is not the
  asserted milestone.
- **Two frozen-oracle edits F2 required** (both kept in C/Python parity, no
  corpus regression - see LOG.md 2026-07-08): (1) a `read_all : IO -> (IO,
  String)` primitive (whole-stdin read) so a compiled compiler can read its own
  source; (2) the C CEK arena moved from a static array to a `malloc` so
  `LARK_ARENA_SIZE` can be raised to multi-GB - the emitter's final O(n²) string
  join over ~250 KB of output needs it (a performance wart, OPTIMIZE.md territory,
  not a correctness one).

### M5.5 - F2⁺: the *typechecking* self-hosted compiler - **near-future, planned 2026-07-08**
F2 as defined closes the loop with `lex → parse → emit` (the emitter drives off the
syntactic AST, so `infer.lark` was never on the bootstrap path). This milestone
makes the self-hosted compiler a *real compiler*: it type-checks, rejecting
ill-typed programs with the oracle-identical diagnostic before it emits. `infer.lark`
is already proven correct by the M3 differential - this wires it onto the compiler
driver. Enabling facts (all verified 2026-07-08): `Prog : Copy` (parse.lark:111) so
one parsed tree can be type-checked *and* emitted; `checkProgram : Prog -> String`
already runs `pass1 → pass15 → pass2`; the only cross-module function-name clash
across all six modules is `main`, which assembly strips.

- OK **M5.5.1 - Concat probe** *(2026-07-08)*. The six-module concat `lex + parse +
  types + tast + infer + emit_c` (3491 lines) + a trivial main runs through the
  oracle and prints `ok` - **no name collisions** between the infer-set and
  `emit_c` (their pairing had never been concatenated; the one real integration
  unknown). M5.5.2 is therefore pure wiring.
- OK **M5.5.2 - Typecheck gate** *(2026-07-08)*. Driver = the six modules + a
  `tcGate(prog) : Result(Bool, String)` (a `Result` re-expression of `checkProgram`'s
  `pass1→pass15→pass2`, `P2Err→Err`/`P2Ok→Ok`) + a main that parses once, gates, and
  prints. Smoke through the CEK: **accept** emits byte-identical C, **reject** prints
  the oracle-identical `type error:` message; `Prog : Copy` lets one tree be gated
  *and* emitted. **§7 finding:** the driver may not `print(io, ...)` in two match arms
  (the affine checker *sums* uses across arms → `io` used twice); build the output
  String purely and print `io` once - the M0 IO idiom now shapes the compiler driver.
- OK **M5.5.3 - Functional close (interpretive differential) - DONE *(2026-07-08)*.**
  `self/tests/typecheck_difftest.py` (`make -C self typechecktest`) drives the gated
  compiler over the corpus: **42 ok / 0 failed / 2 skipped**. Every accepted program
  emits byte-identical C (incl. `09_parser` 851 lines, `08_life` 519); the 5 genuinely
  ill-typed error-suite files reject with oracle-identical `type error:` messages
  (`04_nonexhaustive`/`06_matchfail` correctly *emit* - no exhaustiveness check); 2
  skips = the 2 `import` files. **Strictly stronger than `emittest` (37/7):** the 7
  error-suite files `emittest` can only skip are live acceptance tests here. **The
  self-hosted compiler is no longer a transpiler - it type-checks. Self-hosting is
  functionally complete at F2⁺.**
- OK **M5.5.4 - Native fixpoint attempt (was OPTIMIZE-gated) - CLOSED 2026-07-08.**
  Handed to OPTIMIZE as predicted; see `OPTIMIZE.md` §8b ("the infer-pass allocation
  wall - OK REDUCED, M5.5.4 native fixpoint CLOSED"). The arena wall was real and was
  fixed there (assoc-list `Subst`, env- and subst-side multipliers), not a failure.
  *(Checkbox was stale until 2026-07-11.)* Original scope: Try C1==C2==C3 on
  the bigger (~3700-line) typechecking compiler. Its emitted C roughly doubles, and
  the emitter's O(n²) arena join could push the peak past a laptop's RAM. **Either**
  the fixpoint closes and F2⁺ is complete natively, **or** the arena wall is recorded
  as the motivated hand-off to `OPTIMIZE.md` (O0/O1) - *not* a failure. The
  emit-only F2 fixpoint already stands regardless.

**When M5.5.3 lands, self-hosting is FROZEN at F2⁺** (M5.5.4 either closes here or is
owned by OPTIMIZE). See §5b "Freeze & hand-off".

### M6 - Pico self-hosting *(F3)* - **re-scoped 2026-07-11, ladder below**

> **What F3 is - and is not.** F3 is **cross-compilation**: the *self-hosted*
> (Lark-in-Lark) compiler, running on the host, emits RV32I; the emitted program
> runs on a Pico 2/2W. **The compiler does not run on the Pico.** It cannot: a
> self-compile needs ~5.6 GB of arena and an RP2350 has **520 KB** of RAM - a
> ~10 000× gap that no allocator fix closes (an on-device compiler would need a
> fundamentally different streaming design). The milestone name invites the wrong
> expectation; say "cross-compiling to bare metal", not "self-hosting on the Pico",
> in the prose too.

**Re-scope (2026-07-11): F3 is much closer than this section claimed.** The original
port list ("`tac.py`/`lower.py`, the backend analyses, and `riscv_asm.py`") was written
*before* M7 existed, and **M7 has already done most of it**:

| original M6 port item | actual status |
|-----------------------|---------------|
| `tac.py` | OK `self/tac.lark` (M7.1) |
| `lower.py` | OK `self/lower.lark` (M7.2) |
| "the backend analyses" | OK cfg / liveness / dominators already live in `self/opt.lark` (M7.4) - `optBuildCfg`, `optCfgPreds`, `optLiveFix`, `optDominators`, ... |
| `riscv_asm.py` | NO **not needed** - see below |

**The real port surface is 2 modules, ~822 lines.** Verified against the live tree:

- **`asm.py` (547 L)** - TAC → RV32I **assembly text**. Entry `gen(tac, allocator=None) -> str`.
- **`regalloc.py` (275 L)** - the default **linear-scan** allocator (`allocate_tac`).

Everything else stays **Python, as test infrastructure** - the same status `cek.py` has.
It is oracle, not product:

- **`riscv_asm.py` (617 L) + `riscv_vm.py` (726 L)** = the assembler + RV32 emulator. The
  **Pico path never touches them**: `make pico FILE=...` runs `asm.py FILE → runtime/program.S`
  and then the **real GNU RISC-V toolchain** (pico-sdk + cmake/ninja) assembles and links the
  `.uf2`. `riscv_asm`/`riscv_vm` exist only to *run RV32 in software for testing*
  (`assemble_lark(gen(tac))` → bytes → VM). **Do not port them.**
- **`coloring.py` (367 L) + `igraph.py` (162 L)** = the O4 graph-coloring allocator, swapped
  in via `gen`'s `allocator=` hook. An optimization increment, not on the critical path.

F3's core is therefore **smaller than `lower.lark` was**, and the recipe is the one already
executed eight times. **The seam is clean: F3 is a backend swap.** The self-hosted pipeline
`lex → parse → infer → lower → opt` is done and differentially green; F3 replaces exactly one
terminal stage, `emit_tac_c` (TAC→C) → `asm` (TAC→RV32), on the same TAC input.

#### The ladder

- OK **F3.1 - `self/regalloc.lark` + `self/asm.lark`; the 9th differential.** *(done 2026-07-13.)*
  Port linear-scan + the assembly generator. Harness `self/tests/asm_difftest.py`
  (`make -C self asmtest`): self-hosted `.S` **byte-identical** to `asm.py`'s over the
  corpus. Hardware-free. *This is the milestone; the rest is consequence.*
  **The finding: the compiler we were porting was not a function.** `regalloc.py` iterated
  `frozenset`s, so its output depended on `PYTHONHASHSEED` - there was no byte-identity for
  the differential to test *against* until the oracle was canonicalised. Also
  `self/tests/rv32c.py`: the ten Lark modules (**8,003 lines**) as a *native* stdin compiler,
  so the three programs the meta-circular harness can only skip (CPython's stack) are checked
  after all - **9/9**, `09_parser` included.
- OK **F3.2 - behavioral, in the emulator.** *(done 2026-07-13, with F3.1.)* Feed the
  self-hosted `.S` to the **Python** `riscv_asm.assemble_lark` → `riscv_vm`, and compare
  program output against the CEK oracle. Hardware-free, and it catches anything
  byte-identity can't (it didn't - but it's the honest check).
- OK **F3.3 - the capstone: real silicon. CLOSED 2026-07-13, all four claims green, 9/9 on a
  real Pico 2/2W.** Self-hosted compiler → `.S` → pico-sdk → `.uf2` → board.
  `self/tests/firmware_difftest.py --board`.

  **[warning] The original wording was unattainable, and the re-scope is strictly stronger.** This
  asked for the 9 prebuilt `07/firmware/*.uf2` to be reproduced **byte-identically** from the
  Lark compiler. They cannot be - **and not by `asm.py` either**: they predate F3.1's
  canonicalisation of `regalloc.py` (it iterated `frozenset`s, so register assignment was a
  function of `PYTHONHASHSEED`; `09_parser` gave *five distinct shas in five runs*). They are
  the output of one unrecoverable seed, and no `.S` was ever checked in to diff against. So
  the capstone is to **rebuild** the nine from the canonicalised pipeline and prove *the two
  compilers agree on every byte* - a claim about compilers, not about an artefact:
  - OK **claim 1 - assembly identity.** Self-hosted `.S` == `asm.py`'s `.S`, **9/9**.
  - OK **claim 1½ - behaviour in software.** That assembly, on the RV32 emulator, prints what
    `cek.py` prints, **9/9**. (Real gap: `make -C 07 difftest` sweeps `07/tests` only, so not
    one of the nine *flashable* programs had ever been run as RV32.)
  - OK **claim 2 - image identity.** The real GNU RISC-V toolchain turns it into **9 `.uf2`,
    byte-identical from both pipelines**. Staged in `build/firmware/` + `expected/<name>.txt`.
  - OK **claim 3 - silicon. 9/9 on a real Pico 2/2W (2026-07-13).** `--board` flashes each image
    with `picotool` and **diffs what the board prints over USB-CDC against `expected/`** -
    machine-checked, not eyeballed. Every program, `09_parser` included, prints on the Hazard3
    core exactly what the CEK interpreter prints. The register allocator, the frame layout and
    the tail-call loop survive contact with real silicon. `07/firmware/` re-pinned to the nine
    hardware-verified images (the bytes that were actually flashed).

    **§7 finding - the harness bug that looked like a hardware bug.** For a whole session the
    board was silent, and it was *ours*: opening the port asserts DTR, which releases the
    firmware's `while (!stdio_usb_connected())` wait, and it prints **immediately** -
    microseconds later. Python's `tty.setraw()` defaults to **`TCSAFLUSH`**: *apply, and
    **discard pending input***. The transcript arrived and the very next line threw it away; we
    then listened at a board that had already spoken and halted. `screen` never flushes on open,
    so it always worked - which made it look like silicon, or DTR, or macOS. **Set raw mode by
    hand with `TCSANOW`.** The discriminator that saved the day: flashing the *old,
    hardware-verified* image and finding it **equally silent** - a known-good artefact cannot be
    a compiler bug, so the fault had to be in the reader.
- **F3.4 - the graph-coloring allocator. RETIRED FROM THE PLAN; it is now an
  *exercise* (book ch11).** *Decided 2026-07-13.* Nothing depends on it: no fixpoint, no
  baseline, no chapter. The *reader* already has `coloring.py` + `igraph.py` in the oracle,
  so the book can teach graph colouring from the Python without the Lark port existing -
  and the port is a better exercise than it is a milestone, because it is the one piece of
  F3 where the answer is not already sitting in `07/` waiting to be diffed against.

  **If you (or a reader) attempt it:** port `igraph.py` + `coloring.py` → `allocate_tac_color`,
  swapped in at `gen`'s `allocator=` hook. `cfg`/`liveness` are **already ported** inside
  `opt.lark`, so this is ~529 lines of genuinely new code - a *purely threaded* interference
  graph + spilling. The differential is free: linear-scan and colouring must produce
  *different assembly* but *identical program output*, which is the first test in this whole
  project that is not byte-identity. Optionally also the post-gen RV32I peephole (`opt.py`'s
  `ASM_PASSES`, deliberately skipped in M7.4). The pre-registered §7 findings below still
  apply and are the hints.

#### Expected §7 findings (pre-registered, from the eight prior ports)

- **Mutable state in `asm.py`** (tag map, globals map, label counter) and **inherently
  stateful linear-scan** (active list, free-register pool, spill slots) → thread purely as
  folds / read-only `Ctx` + threaded state, the established M7.2/M7.3 idiom.
- **The occurs-gap redux.** A polymorphic accumulator-reverse tripped frozen `infer`'s
  monomorphic self-recursion in *both* `emit_c` (`ecRev`) and `emit_tac_c` (`etcRev`). Expect
  it a third time; fix by pinning the element type.
- **The arena wall.** Build the `.S` with a **balanced join from the start** (§8a `etcJoinNL`),
  never a left-nested `acc + line`, and intern any tables via a side-index - the two walls
  that cost the most time in M5.5 and M7.5.
- **Byte-identity is formatting-identity.** `tac.lark` already had to mirror Python's `repr`
  quote-selection; expect the same class of thing in `.S` text (immediate formatting, label
  naming, section directives, whitespace).

**F3 and PROVE are orthogonal** - F3 touches only the backend (TAC in), PROVE extends
Algorithm W in the front end. Doing F3 first creates **no rework** for PROVE.

### M7 - the self-hosted *optimizing* compiler (true O5') *(planned 2026-07-10)*
Port `tac.py` + `lower.py` + the **TAC subset** of `opt.py` to Lark and add a
net-new `emit_tac_c` (TAC → C), giving a self-hosted *optimizing C-compiler* - the
optimizer lives inside the compiler and on the F2 backend. Closes both gaps the
2026-07-10 behavioral O5 left open (Python optimizer; disjoint RV32 backend).
**This shares nothing with M6** (no RV32 assembler/regalloc port - the C backend
does not need it). Full breakdown (M7.0-M7.5, the O5' fixpoint, validation, ~1500
Lark lines): **OPTIMIZE.md §9**.

Progress: **M7.0 OK** (2026-07-10, `07/src/emit_tac_c.py` oracle, 100 ok/0 fail).
**M7.1 OK** (2026-07-10, `self/tac.lark` = the tac.py IR port + byte-faithful
pretty; `make -C self tacsmoke` is a true differential vs tac.py - builds the same
program both sides, pretty output byte-identical).
**M7.2 OK** (2026-07-10, `self/lower.lark` = lower.py port; `make -C self lowertest`
= 35/0/10, TAC byte-identical incl. 09_parser).
**M7.3 OK** (2026-07-10, `self/emit_tac_c.lark` = emit_tac_c.py port; `make -C self
emittactest` = 32/0/13, C byte-identical incl. 08_life 867 lines).
**M7.4 OK** (2026-07-11, `self/opt.lark` = opt.py TAC-passes port; `make -C self
opttest` = **128/0/52**, optimized TAC byte-identical vs opt.py at every -O0..-O3 -
the strongest M7 obligation).
**M7.5 OK - the O5' fixpoint, CLOSED 2026-07-11.** Both claims (OPTIMIZE.md §9.4):
(1) behavioral fixpoint - the self-hosted optimizing pipeline reproduces the oracle's
optimized C at every level (`opttest` 128/0/52); (2) **self-application fixpoint** -
the baked-`-O3` `optcompiler.lark` compiles its own ~7.5 k-line source to
**C1 == C2 == C3 byte-identical** (sha `f1dedfa9`, 1,512,018 bytes). The win: emitted
C **-18.4 %** (1,852,562 → 1,512,018) from the compiler applying its own -O3 passes.
The level-≥1 arena wall (O(n²) `tacPretty` fixpoint fingerprint) was replaced with a
structural `optTacEq` (output-neutral, 12 GB overflow → 5.6 GB free). See BASELINES.md
§ "O5' optimizing self-application fixpoint" and LOG 2026-07-11 M7.5.

**M7 COMPLETE - the self-hosted optimizing compiler is a true self-optimizing fixpoint.**

---

## 5. Bootstrap & validation strategy

- **Stage-0 is the oracle.** The Python toolchain in `07/src/` is frozen as the
  reference. Every self-host module is validated *differentially* against its
  Python twin before we trust it - reuse the existing `difftest` harness pattern.
- **Corpus.** The 158 `.lark` files (tests + samples) are the regression bed at
  every milestone. The compiler's own source joins the corpus once it parses.
- **Two-stage fixpoint (F2).** stage-1 = Python-built self-host compiler;
  stage-2 = stage-1 building its own source; require byte-identical output. A
  diff is a bug in the self-host compiler, caught mechanically.
- **No new language features.** Self-hosting must succeed on Lark *as it stands*.
  If a module feels impossible without a new construct, that is a finding about
  the language - record it in §7, don't silently extend the language.

---

## 5b. Freeze & hand-off to OPTIMIZE *(planned 2026-07-08)*

When M5.5.3 lands, self-hosting is **done**. How we freeze it and start the
optimization phase (my recommendation - *not* a directory copy):

- **Don't copy the docs.** `OPTIMIZE.md` already exists with a full O0-O5 ladder;
  it *is* the next active plan, not a copy of this one. This file (`SELFHOST.md`)
  gets marked COMPLETE and left as the frozen record. `LOG.md` is a *single running
  log across all phases* (its header already says "SELFHOST.md and OPTIMIZE.md") -
  it continues, it does not fork.
- **Freeze the artifact with a git tag, not a directory copy.** Tag the tree at F2⁺
  (e.g. `selfhost-f2`) so the proven fixpoint is reproducible forever. A `self-opt/`
  copy would fork maintenance; instead, optimization edits `emit_c.lark` / the arena
  *in place* on top of the tag.
- **The existing differentials already guard optimization.** Every self-host module
  is diffed against the frozen `07/src/` oracle. A correctness-preserving optimization
  (O(n) join, arena GC) must emit **byte-identical** C - so `emittest` and the
  `bootstrap` fixpoint are the regression net; no new safety scaffolding needed.
  Pin the golden output too: record the F2⁺ emitted-C sha as a fixture so "still
  emits the same C, now faster" is a one-line check.
- **The hand-off is *motivated*, not arbitrary.** The first optimization target is
  the concrete wall M5.5.4 may hit - the O(n²) arena join in `emit_c.lark`. That is
  where `OPTIMIZE.md` O0 (harness) → O1 should point first: it's the wall that gates
  the native fixpoint of the *typechecking* compiler, so fixing it *closes F2⁺
  natively* as its first win. Seed OPTIMIZE.md O0/O1 with this when we get there.

---

## 6. Proposed layout

```
lark/
  self/                 # the self-hosting sources (new)
    lex.lark
    ast.lark  parse.lark
    types.lark  tast.lark  infer.lark
    cek.lark            # F1
    emit_c.lark         # F2
    tac.lark  regalloc.lark  riscv.lark   # F3
    tests/             # differential harness vs 07/src
    Makefile           # test - interp - bootstrap - difftest
  07/                   # frozen stage-0 oracle (unchanged)
  formal/proof/         # unchanged
  SELFHOST.md           # this file
```

Keep `07/` frozen as the oracle; do the new work under `lark/self/`.

---

## 7. Risks & open questions

- **Affine union-find.** Persistent map with path re-rooting vs. threading an
  explicit store. Prototype both on a toy in M3 before committing.
- **String Copy semantics.** OK *Resolved in M0:* `String` is already in
  `BUILTIN_COPY`, so the source text can be indexed non-linearly for free - the
  lexer/parser need not thread it.
- **Affine values can't cross branches** *(known idiom, reconfirmed M0)*. The affine checker
  **sums** a variable's uses across `if` branches and `match` arms instead of
  treating them as mutually exclusive, so an affine value (notably `io`) cannot
  be threaded through branching control flow - even a `match`-based list printer
  is rejected. The corpus already sidesteps this: keep recursion **pure** and
  thread IO only sequentially at top level (build the output value, print once).
  This shapes the whole toolchain (lexer/parser/typechecker are pure String/AST
  transforms anyway), so it is not a blocker - but it is a real language wart
  worth the book's attention, and a candidate to fix (branch-local affine
  scopes) if a later module genuinely needs affine threading through a branch.
- **Perf of a pure compiler.** `O(n²)` traps in list/string handling; `slice`
  in M0 removes the worst. Acceptable if the bootstrap completes in seconds, not
  minutes.
- **Trait resolution ordering.** `infer.py`'s dictionary/instance search may lean
  on dict iteration order; make the Lark version's search order explicit.
- **String `==` unimplemented in the CEK** *(found M1, 2026-07-07)*. `==`/`!=`
  typecheck on `String` (Eq is polymorphic, `∀a. a → a → Bool`) and `_val_eq`
  compares strings - but `cek.binop` only implements `==` for `Int`/`Float`, and
  string `+` only for concat, so `s1 == s2` crashes at runtime (`cannot apply
  '==' to <str> and <str>`). Workaround in use: compare strings via
  **`match` on string-literal patterns**, which go through `_val_eq`. A clean
  fix (add `VStr`/`VBool` cases to `binop` in *both* runtimes) is a candidate M0
  follow-up if a later module needs dynamic string equality; keyword lookup does
  not. A first-class language finding for the book.
- **Import skips mutual-recursion pre-registration** *(found M2, 2026-07-07)*.
  A module type-checks standalone (top-level `typecheck` runs infer Pass 1.5,
  which pre-registers fully-annotated fn signatures so forward/mutual references
  resolve), but the same module fails to type-check when **imported**: the
  `_load_import` inner re-check (infer.py ~900-907) checks the imported module's
  FnDecls in source order *without* Pass 1.5, so any forward reference (e.g.
  lex.lark's `read_name → keyword_kind`) raises `unbound variable`. Workaround:
  the M2 differential driver **concatenates** lex+parse into one module rather
  than using `import`, so the whole program goes through the top-level checker.
  A clean fix (mirror Pass 1.5 inside `_load_import`) touches the frozen 07/
  oracle, so it's deferred; parse.lark still *reads* as a clean `import Lex`
  component for when the import path is fixed. Toolchain gap, not a language one.
  *(M4 follow-on, 2026-07-07:)* the same flatten-by-concatenation workaround now
  also covers the *object* programs the meta-circular evaluator runs - the CEK
  difftest **inlines** each imported module's decls into the object source before
  evaluation (visibility only hides names, so inlining a superset can't change an
  accept-test's output), so `16_stdlib` / `09_modules` run without the port
  needing any `import` mechanism of its own.
- **Occurs-check gap: a polymorphic fn that *builds* a `List(a)` from a
  polymorphic element loops the checker** *(found M4, 2026-07-07)*. `infer.py`'s
  `compose(s1, s2)` = "apply s1 through s2's range, then union s1's own bindings"
  can create a self-loop (`α ↦ β` and `β ↦ α` collapsing to `α ↦ α`) with **no
  occurs-check**, after which `apply` recurses forever → `RecursionError`. It is
  triggered narrowly: a generic function that unifies a user annotation var `a`
  against a *constructor's* fresh element var in a **value/return** position.
  Minimal reproducers: `fn f(x:a):List(a) = Cons(x, Nil)` and
  `fn f(x:a, xs:List(a)):List(a) = Cons(x, xs)` both hang; but `fn f(x:a):a = x`,
  `fn f(x:a):(a,a) = (x,x)`, and `fn f(xs:List(a)):Int = ...` (consuming, not
  building) all check fine. That is why parse.lark (never returns a `List(a)`
  built from a polymorphic element) and cek.lark's generic `ckLen`
  (`List(a)→Int`) are unaffected, while cek.lark's `ckSnoc` (a generic append,
  builds `List(a)`) crashed. **Workaround in use:** monomorphise the offending
  helper - `ckSnoc` is only ever called on `List(RVal)`, so it is specialised to
  that. A clean fix (an occurs-check in `bind`/`compose`) touches the frozen
  oracle, so deferred. A genuine *toolchain* soundness gap (the inferencer can
  build an infinite type), and a good book example of why occurs-checks exist.
- **Meta-circular eval is cubic** *(observed M4, 2026-07-07)*. cek.lark run
  through the difftest is Python-CEK > Lark-CEK > object program, so
  compute-heavy corpus files (e.g. `04_tailrec` = 1,000,000 iterations, `queens`,
  `life`) don't finish. This is a *performance* property of the differential
  harness, not a correctness gap: the port is byte-identical on the whole feature
  fragment incl. 6/9 samples. The M4 difftest therefore treats a per-file timeout
  as a *skip-with-reason*, not a failure. A compiled bootstrap (F1/F2/F3) removes
  the interpretive tower; until then, validate the evaluator on small inputs.
- **No `%` (modulo) operator** *(found M5, 2026-07-08)*. `%` is not a Lark lexer
  token - a source `%` raises `LexError: unexpected character '%'`. Any modular
  arithmetic must be written out: the emitter's hex-digit extraction uses
  `n - (n / 16) * 16` (integer `/` truncates). Minor language gap; a candidate
  lexer/parser addition, noted for the book. Not a blocker - the workaround is exact.
- **Float32 bit pattern needed a runtime prim** *(found M5, 2026-07-08)*. The C
  emitter writes float literals as `LIT_FLOAT` from the **IEEE-754 float32 bits**
  (`emit_c_ast.py._f32_bits`), and Lark had no way to reinterpret a `Float` as its
  bit pattern - the arithmetic prims all stay in `Float`/`Int` value space. Added
  **`float_to_bits : Float -> Int`** in **M0 lock-step** across all three runtimes:
  `cek.py` (`struct.unpack('I', struct.pack('f', f))`), `cek.c` (`(int32_t)` of a
  float32 reinterpret), `infer.py` (`Scheme((), TFn(T_FLOAT, T_INT))`); parity
  cases in `24_stringprims.lark`, `make cektest` = 31/31 C↔Python identical. Since
  float *literals* are non-negative, bit 31 is clear, so C's signed `int32_t` and
  Python's unsigned `'I'` agree without masking. This is the one prim M5 added to
  the frozen oracle - kept in lock-step with a parity test, per the M0 discipline.
- **Oracle bakes a nondeterministic `id()` into emitted C** *(found M5,
  2026-07-08)*. `infer.py` renames a wildcard param `_` → `_anon_{id(node)}`
  (lines 420, 573) using a CPython object address, and `emit_c_ast.py` writes that
  string into the closure's (never-referenced) param-name field. The output is
  therefore **not reproducible** run-to-run, and no port can match a specific
  `id()`; `emit_c.lark` keeps the deterministic wildcard `_`. The M5 differential
  **canonicalises `_anon_\d+` → `_` on both sides** before comparing - the token
  never occurs in the corpus (so it can't mask a real name) and the wildcard param
  name is semantically dead (never looked up). A *toolchain* determinism wart, not
  a language one; the honest fix (name wildcards `_` or by a deterministic counter)
  touches the frozen oracle, so deferred. Good book example: self-hosting surfaced
  a latent non-determinism in the reference compiler's output.
- **Oracle emits imported decls twice** *(found M5, 2026-07-08)*. `emit_c_ast.emit()`
  builds `all_decls = _load_imports(prog) + tprog.decls`, but `infer.typecheck`
  **already inlines** each imported module's typed decls into `tprog.decls`
  (Pass 0, infer.py:789 `typed_decls.extend(imp_decls)`). So `_load_imports`
  re-adds them and the emitted C carries every imported module's decls **twice**
  (distinct C symbols `_d0...` and `_d4...`, same `.name`; verified on `09_modules`).
  The generated program still compiles and runs (a later duplicate decl just
  shadows the earlier in the runtime's decl list), so the bug is latent - pure
  bloat, not a miscompile. It lives in the `emit()` *wrapper*, not the emitter
  core (which faithfully emits whatever decl stream it's handed). A frozen-oracle
  bug, so left as-is; the M5 differential mirrors it by inlining the imported
  bodies twice, so both `import` programs pass byte-identically. A clean fix would
  drop the `_load_imports` call (typecheck's inlining already suffices). Another
  book example of self-hosting flushing out a reference-compiler defect.
- **Feature gaps.** Any construct self-hosting *wants* but Lark lacks is a
  first-class finding for the book - log it here.

---

## 8. First step

**M0.** Design the four string primitives above, decide `Copy for String`, and
add them to `07/src/cek.c` and `07/src/cek.py` with parity tests. That single
step unblocks the entire Lark-only remainder of the project.
