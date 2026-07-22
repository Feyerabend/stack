# Frozen baselines — the optimizing back end

These are the numbers this strand is supposed to print. If a run disagrees with a
count here, either the code changed or the harness did; find out which before you
change this file.

This strand stands alone: it has its own compiler (`lark/`), its own Python
reference (`oracle/`), its own corpus, and its own harnesses. It shares no files
with the self-hosting strand, and these baselines are its own.

## ⚠ Which of these numbers are about the compiler, and which about the machine

Read this before treating any count below as a contract. The numbers are of two
kinds, and only one kind is a claim about Lark.

**Invariant — true on any machine.** These are the actual results:

- **`0 failed`, everywhere.** A *failure* means the Lark implementation and the
  Python reference disagreed about a program they both finished. That is a fact
  about the compiler and holds on a Raspberry Pi.
- The **accept/reject verdicts** in the error suite.
- The **fixpoint shas** (`8f9596d9`; C1 == C2 == C3) — the emitted C is
  deterministic, so a different machine reproduces the same bytes. (The *binary*
  is not: Mach-O carries a UUID and paths. That is noted where it appears.)

**Environment-dependent — true of *this* machine, on the day it was pinned.**
These are budgets, and the numbers that fall out of budgets:

- **`LARK_TIMEOUT`** is wall clock. The port is an interpreter running an
  interpreter, so a per-file budget is unavoidable — but it measures the box, not
  the compiler.
- **Therefore the `ok`/`skip` split moves with the box.** `emittactest`'s 13 skips
  include 3 files whose serialised TAC is too deep for this machine's CEK stack. A
  faster or roomier box turns skips into `ok`; a slower one does the reverse. The
  count is a report, not a promise. What *is* promised is that of the files that
  ran, none disagreed.
- **Arena sizes** (12–15 GB, lazily committed) and the `ulimit -s` bump for
  macOS's 8 MB stack.

Consequently: **a moved `ok`/`skip` boundary is not a regression — a `fail` is.**
Every harness now reports a timeout as a *skip with a reason*, never as a failure,
so that a slow machine cannot masquerade as a disagreement. This is not a nicety:
a harness that scores its own impatience as a compiler bug will send you hunting a
defect that is not there.

If you are re-pinning on new hardware: raise `LARK_TIMEOUT` until the skip count
stops falling, and expect these counts to be *at least* as green as the table.


## Differential test counts

### The seven differentials

These port the optimizing-path oracles (`lower.py`, `emit_tac_c.py`) and are
differential-tested by feeding the **same** oracle-produced TAC to both sides
(the front end + lowerer are trusted; only the ported module runs in Lark).
`lowertest`/`emittactest` feed the **unoptimized** TAC to both sides (isolating the
lowerer/emitter); `opttest` is the pass that puts the
optimizer itself on the differential — both sides run `opt.optimize` at every level
before the comparison.

`lextest`, `parsetest` and `infertest` are the odd ones out and belong here anyway: the
optimizer lowers a *typed* AST, so the whole front end is on this strand's path. They are
the same differentials the `self` strand runs, against the same oracle — deliberately
duplicated, because a strand you can only half-check is not self-contained.

| target        | result           | what it proves                                              |
|---------------|------------------|-------------------------------------------------------------|
| `lextest`     | **54 ok / 0 fail / 0 skip** | `lex.lark` == `lexer.py` (token streams, incl. line/col). The corpus is every `.lark` in `tests/`, `samples/` **and this strand's own nine modules**, so the count is 54 here and 52 in the `self` strand — the two are not comparable, and are not compared. Slow: `LARK_TIMEOUT` defaults to 900 for this target, because `opt.lark` alone is 1,770 lines |
| `parsetest`   | **54 ok / 0 fail / 0 skip** | `parse.lark` == `parser.py` (syntax trees). Same corpus, same budget. Pinned 2026-07-13, when these two shipped as targets: until then the strand *ran* them with no row here, and a target with no row is a target nobody is watching — which is precisely how a `parsetest` timeout once sat unnoticed in the other tree |
| `infertest`   | **42 ok / 0 fail / 3 skip** | `infer.lark` == `infer.py` (Algorithm W + affine + traits) — the types the optimizer relies on are the types the reference infers; 3 skips = the 3 `import` files |
| `lowertest`   | **35 ok / 0 fail / 10 skip** | `lower.lark` == `lower.py` (typed AST → TAC); TAC byte-identical incl. 09_parser; 10 skips = 3 imports + 7 reject fixtures |
| `emittactest` | **32 ok / 0 fail / 13 skip** | `emit_tac_c.lark` == `emit_tac_c.py` (TAC → C, optimizing backend path); C byte-identical incl. 08_life 867 lines; 13 skips = 3 imports + 7 reject fixtures + 3 CEK-overflow on deep serialised TAC (24_stringprims, 05_expr, 09_parser) |
| `opttest`     | **128 ok / 0 fail / 52 skip** | `opt.lark` == `opt.py` (TAC → TAC passes) — optimized TAC byte-identical at **every** level -O0..-O3, incl. 17_mutual_rec's live-fnmap inline eligibility; 52 skips = (3 imports + 7 reject fixtures + 3 CEK-overflow [24_stringprims, 05_expr, 09_parser]) × 4 levels |
| `optcompilertest` | **140 ok / 0 fail / 40 skip** (35/0/10 per level) | the **whole optimizing pipeline**, self-hosted: all 9 modules concatenated (`lex`→`emit_tac_c`) compile each file and must reproduce the oracle's optimized C byte-for-byte at **every** level -O0..-O3. Strictly stronger than `lowertest`/`emittactest`/`opttest`, which each isolate one stage. 40 skips = (3 imports + 7 reject fixtures) × 4 levels — **no timeout skips** |

**Newly pinned, 2026-07-12 — and a warning about what its absence cost.**
`optcompilertest` is the strongest differential in the tree, and until today it had
**no row here at all**. It was written last, never got a baseline, and so had no
expected numbers for anyone to disagree with. When it was finally run end-to-end it
came back **115 ok / 25 fail / 40 skip** — 25 failures that had been sitting in it,
unnoticed, for as long as it had existed. A differential with nothing pinned is not a
test; it is a script that prints a number nobody reads.

All 25 turned out to be defects in the **harness**, not the compiler — the same
lesson as `25_torture` below, learned twice in one week:

- **`opt._SITE` is a global counter.** `opt.py`'s inline and closure passes stamp an
  id on each rewrite site from a module-level `itertools.count()`, so it kept climbing
  from one corpus file to the next. The port is a fresh subprocess per file and always
  starts at zero, so from roughly the second file onward the two sides wrote different
  site ids into otherwise identical C. This produced the whole -O2/-O3 cluster (23 of
  the 25) and had the signature of a real bug: `08_traits -O2` **passed when run alone
  and failed inside the sweep**. `oracle_at` now resets `_SITE` per call, as
  `opt_difftest.py` already did. The fix also makes the result independent of how the
  run is grouped — a file now gets the same answer alone, in a level-chunk, or in the
  full four-level sweep.
- **`_anon_<id()>`.** For a wildcard parameter `_`, `infer.py` invents a name from a
  CPython `id()` — a memory address — and bakes it into the emitted C as a parameter
  nothing ever refers to. No port can reproduce an address; the port keeps `_`. Both
  sides are now canonicalised, as `emit_c_difftest.py` already did.

Neither is a fact about the compiler. Both had already been solved in sibling
harnesses; this one simply never inherited the fixes, because nothing was checking it.


## The optimizing compiler optimizes itself to a fixed point

`make fixpoint` (`harness/bootstrap_opt.py`). The whole optimizing pipeline — nine
modules, `lex` through `emit_tac_c`, about 7,500 lines of Lark — is assembled into a
compiler with `-O3` baked in, and pointed at **its own source**.

| artifact | value | note |
|---|---|---|
| C1 == C2 == C3 | `8f9596d9` | emitted-C fixpoint, byte-identical across three stages |
| size | 1,519,608 bytes | 49,536 lines of C |
| stage2 binary == stage3 | *(not pinned)* | Mach-O carries an `LC_UUID` and embedded paths; only the C-source fixpoint is asserted |

**Re-pin (2026-07-13):** the sha moved `f1dedfa9 → 8f9596d9` *intentionally*, when the
type checker was repaired to let a full signature license polymorphic recursion. The
type checker **is** compiler source — `infer` and `types` are two of the six modules
assembled here — so any edit to it necessarily changes the C the compiler emits for
itself. **The invariant is the closure, not the sha:** `C1 == C2 == C3` still holds
byte-identically. A pin that forbids the compiler's own source from ever changing is
not a correctness property; it is a freeze on the project.

**The headline, and the reason the strand exists.** The same compiler, on the same
input, emits **1,852,562 bytes at `-O0` and 1,519,608 at `-O3` — 18% less code**.
It optimizes itself, and the result still reproduces itself exactly.

This is the *strongest* claim in the strand and the cheapest to check: a fixpoint
cannot be faked by a bug the three stages happen to share only if the bytes agree,
and they do. It runs in ~6 GB; see the README for what the heavy targets need.

**Do not treat a moved sha as noise.** The compiler's own source is one of its
inputs, so editing *any* of the nine modules changes the emitted C by definition.
Re-run the target and re-pin deliberately, with the reason.

## The RV32I metric baseline (the optimizer's ruler — 2026-07-08)

`optbench.py --levels 0 --save optbench_O0.json` — the
measurement rig. Per corpus file × `-O` level it records static
asm-instruction count, assembled binary bytes, executed RV32I instructions, stub
calls, and heap allocs/bytes (via `riscv_vm.py` counters), plus compile/run
wall-clock and the program-output sha. Full per-file numbers live in
`optbench_O0.json`. (The benchmark rig is development tooling and is not shipped
here; the numbers are quoted because they are what the optimizer is judged
against.) The corpus totals at the current (un-optimized) code
generator:

| level | files ok | asm_instrs | bin_bytes | dyn_instrs | stub_calls | heap_allocs | heap_bytes |
|-------|----------|------------|-----------|------------|------------|-------------|------------|
| `-O0` | 25       | 8106       | 37656     | 22553695   | 527        | 361         | 3760       |

### Optimization-level progression (corpus totals — the regression contract)

Each `-O`n reproduces every file's `-O0` program-output sha (checked by
`optbench.py --levels 0,1,2,3,4`); only the metric numbers move. `-O0` stays the
identity, so `optbench_O0.json` is *not* re-pinned. Achieved totals (2026-07-09):

| level | asm_instrs | bin_bytes | dyn_instrs | stub_calls | heap_allocs | heap_bytes | headline |
|-------|-----------|-----------|-----------|-----------|-------------|-----------|----------|
| `-O0` | 8106      | 37656     | 22553695  | 527       | 361         | 3760      | ruler (identity) |
| `-O1` | 7817      | 36496     | 22552605  | 526       | 360         | 3756      | Tier-1 scalar |
| `-O2` | 6726      | 32096     | 22551647  | 526       | 360         | 3756      | devirt+inline |
| `-O3` | 6526      | 31272     | 22551347  | 520       | 354         | 3708      | closure_elim (heap) |
| `-O4` | 4443      | 22940     | 10828342  | 520       | 354         | 3708      | peephole + coloring + immfold + branchlayout |

O4 has four backend items, all observably ==-O0 across all 25 files:

**Increment 1 — post-gen `peephole`** (opt.ASM_PASSES): windowed t-register copy-prop
/ dead-scratch elimination / result coalescing on the emitted asm, plus self-move and
fall-through-jump removal. It removes the scratch round-trips instruction selection
leaves in every fragment — the largest **executed-instruction** cut of any tier
(22.55M → 14.04M, −38%; the hot recursive loops shed their per-iteration moves).
Peephole-only totals (regalloc_color OFF): asm **5199**, bin **25964**, dyn 14036245.

**Increment 2 — graph-coloring register allocation** (`src/coloring.py`, Chaitin-Briggs
iterated register coalescing; the `regalloc_color` codegen flag in `LEVELS[4]`, selected
in `asm.gen(allocator=…)` — linear scan stays the O0..O3/diff_test default). It coalesces
move-related temps (so cross-block `mv sX, sY` copies the peephole can't reach collapse
to self-moves and vanish) and packs into fewer callee-saved registers (smaller
prologue/epilogue save area). Attributed by toggling the flag: corpus asm **5199 → 4683**
(−516), bin **25964 → 23900** (−2064); dyn barely moves (14036245 → 14032752 — coalescing
removes *static* setup moves, and 04_tailrec's 13M-instr hot loop dominates the dynamic
count). Allocation is **deterministic** across `PYTHONHASHSEED` (min-element worklist
selection) and passes `regalloc.verify` on every function (no interfering temps share a
register). heap/stub unchanged (a pure backend tier). Peephole+coloring totals: asm
**4683**, bin **23900**, dyn 14032752.

**Increment 3 — Tier-4 remainder** (two post-gen asm passes in `opt.ASM_PASSES`, run after
`peephole`): **`immfold`** = immediate-form instruction selection — a constant the
generator materialises with a separate `li tX, C` feeding a reg-reg ALU op is folded into
the immediate form (`add`→`addi`, `sub C`→`addi -C`, `and`/`or`/`xor`→`andi`/`ori`/`xori`,
`slt`→`slti`, `mul` by 2^k→`slli k`), removing the `li` (the dead-scratch cleanup reuses
`_opt_window`); floats are excluded (a float-bits `li` is comment-tagged and float
arithmetic lowers to runtime calls, never a reg-reg ALU op). **`branchlayout`** = invert a
conditional branch whose target is the fall-through block — `bnez tX, TRUE; j FALSE;
TRUE:` becomes `beqz tX, FALSE; TRUE:`, deleting the taken jump (complements the peephole's
fall-through-jump removal, which handles the FALSE-is-fall-through case). Attributed by
toggling: asm **4683 → 4443** (immfold −123, branchlayout −117); bin **23900 → 22940**;
dyn **14032752 → 10828342** (−23% — folding the per-iteration `li` out of hot loops).
heap/stub unchanged. Idempotent, deterministic across `PYTHONHASHSEED`, no residual
self-moves.

- The **program-output sha per file** is the observable-equivalence contract:
  every future `-O`n build must reproduce each file's `-O0` sha (asm/bin/instr
  counts change by design; *output* must not). `optbench.py --levels 0,1` checks
  this automatically.
- **25/25** acceptance files run on RV32. `24_stringprims.lark` was previously a
  codegen crash (`PC misaligned` — six string-decomposition prims missing from the
  RV32 backend); **fixed 2026-07-08** (self-contained, *before* any optimization
  pass): `string_index`/`string_slice`/`char_to_string`/`float_to_bits` lower to
  plain runtime stubs, and `string_to_int`/`string_to_float` lower to a raw-parse
  stub returning a `[flag, payload]` pair that `lower._lower_string_to_result`
  wraps in `Ok`/`Err` (so tag ids come from `asm._collect_tags` in lock-step with
  user `Ok`/`Err`). All three backends (CEK, TAC interpreter, RV32) agree
  byte-identically — `diff_test.py` **33/0** at the time. The `+24` bin_bytes on
  every file vs the pre-fix baseline is the six new `ebreak` stub-table entries
  (6 × 4 B) in the shared preamble; program output is unchanged.
- `25_torture.lark` (added 2026-07-09) is the **deep
  equivalence witness** for O1: one program wiring together recursive/nested ADTs,
  closures, higher-order map/fold/filter, trait dispatch, Stdlib+Option, the
  string-decomposition prims + `Ok`/`Err` lowering, int + float32 arithmetic, and
  algebraic-identity-shaped expressions. At **2544 asm instrs / 160 heap allocs**
  it is ~half the rest of the corpus's asm and ~80 % of its heap allocs in a single
  file — a much sharper O0-vs-O1 guard than any single feature test. All three
  backends agree byte-identically (`diff_test` now **34/0**).
- `04_tailrec` (sum_to 1M) dominates run-time (~34 s of pure-Python VM); the rig
  drives each file in a subprocess under `--timeout` so a runaway never wedges the
  sweep.


## Invariants for this strand

1. **All four differential counts above stay as written** (skips may become oks on a
   faster machine; a `fail` may never appear).
2. **The self-optimizing fixpoint sha stays `8f9596d9`** unless a change intentionally alters
   emitted code — in which case re-pin it here, with the reason.
3. **Every corpus file's program-output sha is preserved at every `-O` level.** This
   is the whole contract of an optimizer: the asm, binary, instruction and heap
   numbers are *expected* to move — that is the point — but what the program *prints*
   may not. An optimization that changes an output is not an optimization; it is a
   bug.
4. **The reject diagnostics stay oracle-identical.** A compiler is judged by what it
   refuses, not only by what it accepts.
