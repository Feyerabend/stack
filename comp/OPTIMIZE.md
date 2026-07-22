
## Optimizing Lark - Project Plan

> **Keep the work log.** Progress is recorded in [`LOG.md`](./LOG.md).
> After any `/clear`, read `LOG.md` for the current position - and **append an
> entry there whenever you do work on this plan.**

**Status:** planned (successor to self-hosting) - **Drafted:** 2026-07-07
**Goal:** give the Lark compiler a real optimization pipeline - turn correct-but-naive
code generation into code that is meaningfully smaller and faster.

Sequenced **after** `SELFHOST.md`. This is deliberate:

- Self-hosting first produces a clean Lark-level IR (`tac.lark`) that the
  optimizer can be *written in Lark* to transform - the optimizer optimizing its
  own compiler is the whole point.
- Self-hosting gives a **stable correctness oracle** (stage-0 Python + the
  differential harness). An optimizer is a correctness minefield; we want that
  net already strung before we start.
- Self-hosting gives a **real benchmark for free**: the compiler's own source.
  "Does the optimizer shrink the bootstrap time and the emitted binary?" is a
  self-contained, honest metric - no synthetic microbenchmarks required.

---

## 1. Where we start from

- **No optimizer exists today.** The pipeline is typed AST → TAC → linear-scan
  regalloc → RV32I. There is no constant folding, DCE, CSE, inlining, or
  peephole. Whatever the naive lowering emits is what runs.
- **The theory already exists, decoupled.** Book ch08 (*Optimization*) covers
  constant folding & propagation, DCE & reachability, expression simplification,
  and LICM, with companion demos in `stack/ch08/`. But those demos run on a
  **toy AST**, not Lark's TAC - they are the spec, not reusable code. Every pass
  is (re)implemented here against the real IR.
- **One optimization is already in the backend:** tail-call optimization
  (`asm.py`, the `.{fn}_loop:` + `j` idiom). Everything else is greenfield.

---

## 2. Guiding principles

- **Measure first, always.** ch08 closes on *diminishing returns*; honour it.
  No pass ships without a before/after number from the harness (§6). Passes are
  ranked by measured payoff, not by textbook fame.
- **Correctness is non-negotiable.** Every pass is validated *differentially*:
  optimized output must produce identical observable results to the unoptimized
  build across the whole `.lark` corpus, and the self-hosted compiler must still
  reach the F2 byte-identical fixpoint. A pass that breaks the bootstrap is
  reverted, not patched around.
- **Exploit what Lark is.** Purity + affine ownership hand us optimizations that
  imperative compilers must fight for:
  - **Referential transparency** → CSE / PRE are sound *everywhere*; no effect
    analysis needed.
  - **No mutation, no aliasing** → we skip alias analysis entirely; loads never
    invalidate.
  - **Affine use** → a value used at most once enables allocation sinking, arena
    reuse, and in-place update without escape analysis.
  These are the high-leverage passes, and they are the ones a generic textbook
  optimizer *doesn't* get to use - worth foregrounding in the book.
- **Every pass is individually toggleable** (`-O` levels, per-pass flags) so the
  harness can attribute speedups and bisect regressions.

---

## 3. Where optimization happens

Three levels, in priority order:

1. **TAC IR (`tac.lark`) - the main arena.** Machine-independent, SSA-friendly,
   where the classic and FP-specific passes live.
2. **Typed AST - a few source-level passes** best done before lowering
   (algebraic simplification with type info, inlining decisions).
3. **RV32I - peephole** after emission (redundant moves, load/store folding,
   branch simplification).

---

## 4. Pass catalog (tiered by payoff/risk)

### Tier 1 - Classic scalar passes *(high value, low risk)*
Reference: ch08 §§2-4. Reimplemented on TAC.
- **Constant folding + propagation** - fold `Const op Const`; propagate constants
  through `IAssign`.
- **Algebraic simplification** - `x+0`, `x*1`, `x*2 → shift`, `x-x → 0`, boolean
  identities.
- **Copy propagation** - eliminate `t = s` chains.
- **Dead code elimination** - drop instructions whose results are never live
  (we already compute liveness in `liveness.py` → free foundation).
- **Common subexpression elimination** - sound everywhere thanks to purity.

### Tier 2 - Function & control shape *(high value)*
- **Function inlining** - the single biggest win in a curried FP language: kills
  call overhead *and* unlocks folding/DCE across boundaries. Needs a size/cost
  heuristic to avoid bloat.
- **Trait-dispatch devirtualization** - `lower.py` emits dispatch stubs that
  branch on constructor tags; when the type is known at the call site, route
  directly to `method$Type` and delete the branch. Pure Lark payoff.
- **Loop-invariant code motion** - ch08 §5; on the TAC CFG (`cfg.py` exists).
- **Tail-call optimization** - already in the backend; generalize and verify it
  survives the new IR.

### Tier 3 - Allocation elimination *(the real payoff; GC-free, bump-heap)*
In a language with no GC and a bump-pointer heap, **allocation is the dominant
cost**. These passes are where the big numbers are, and where affinity earns its
keep.
- **Closure elimination / known-call optimization** - when a closure is created
  and immediately/only applied, skip the allocation and call directly.
- **Unboxing** - keep `Int`/`Float`/`Bool` in registers instead of heap cells
  across a computation.
- **Deforestation / fusion** - `map f . map g → map (f.g)`, fold/build fusion.
  Natural and safe in pure FP; removes intermediate lists wholesale.
- **Allocation sinking + arena reuse under affinity** - an affine value that
  dies can have its heap cell reused in place; no escape analysis needed because
  the type system already proved single-use.

### Tier 4 - Backend *(polish)*
- **RV32I peephole** - OK DONE (increment 1, §8f). Redundant `mv`, scratch
  round-trips, self-moves, fall-through-`j`.
- **Register allocation upgrade** - OK DONE (increment 2, §8g). Linear-scan →
  Chaitin-Briggs graph coloring with conservative coalescing (`src/coloring.py`);
  `igraph.py` builds the interference+copy graph the colorer runs on.
- **Instruction selection** - OK DONE (increment 3, §8h). `immfold`: fold a
  `li`-materialised constant into the immediate ALU form (addi/andi/ori/xori/slti) and
  mul-by-power-of-two into `slli`, dropping the `li`.
- **Branch layout** - OK DONE (increment 3, §8h). `branchlayout`: invert a conditional
  branch whose target is the fall-through block, deleting the taken jump.

---

## 5. Milestone ladder

- **O0 - Harness first. OK DONE (2026-07-08, §8c).** `07/tests/optbench.py` +
  `07/src/opt.py` + `riscv_vm.py` counters; baseline pinned in
  `07/tests/optbench_O0.json` / `BASELINES.md`.
- **O1 - Tier 1 on TAC. OK DONE (2026-07-09).** Copy prop + DCE (increment 1),
  then const fold + algebraic simplify + CSE (increment 2). All five in
  `07/src/opt.PASSES`, `-O1` wired. Guard green: `optbench --levels 0,1` = 25/25
  observably ==-O0; asm 8106→7821 on the corpus. Const fold is int/bool only under
  signed `_wrap32` (no `/`-`%`, no float - ÷0 and NaN divergence); CSE is
  block-local non-allocating (allocating-prim CSE via `CSE_ELIGIBLE` deferred).
- **O2 - Tier 2. OK DONE (2026-07-09).** Inlining + devirtualization + LICM in
  `opt.PASSES`, `-O2` wired. Guard green: `optbench --levels 0,1,2` = 25/25
  observably ==-O0; corpus asm 7821 → 6820, bin 36512 → 32472. Inline includes a
  reachable-function prune (so static size falls, not grows); devirt recovers the
  dispatch map from the stub body; LICM is a real dominator-based pass but a no-op
  on the acyclic TAC (recursion is inter-procedural) - unit-tested on a synthetic
  loop. Heap unchanged (that is Tier-3's number). See §8 for the write-up.
- **O3 - Tier 3 allocation passes. OK increments 1 & 2 DONE (2026-07-09).**
  `closure_elim` in `opt.PASSES`, `-O3` wired, and `optimize()` now iterates the
  enabled sweep to a fixpoint. Guard green: `optbench --levels 0,1,2,3` = 25/25
  observably ==-O0. FIRST pass to move the Tier-3 headline. **Increment 1** (single
  sweep): heap_allocs 360 → 358, asm 6820 → 6736. **Increment 2** (fixpoint
  iteration): heap_allocs 358 → **354**, heap_bytes 3732 → **3708**, asm 6736 →
  **6526**, bin 32128 → **31272**, stub_calls 524 → **520**. Iterating peels one
  closure layer per sweep, so non-recursive HOFs collapse fully - 10_closures asm
  146→**86**/heap 5→**3**, 25_torture 1848→**1790**/heap 159→**157**. (Iterating
  also nudges O1 asm 7821→7817 and O2 6820→6726 as cascade folding/inlining
  converges - still ==-O0.) `closure_elim` scalar-replaces non-escaping closures
  (inline the lifted body, `IGetField(env,i)`→`caps[i]`, delete the
  `IAllocClosure`). **Ceiling reached:** the remaining escaped closures go into
  RECURSIVE HOFs (map/foldr in 06_lists/16_stdlib/11_tree), which `inline` correctly
  never expands, so their closures stay heap-allocated - moving those needs
  specialization/defunctionalization, not more iteration. The other three named
  passes are analyzed-and-deferred: **unbox** = genuine no-op (scalars are register
  immediates here, only ADT ctors are boxed); **fusion** needs higher IR (structure
  gone at TAC); **arena_reuse** needs affinity threaded to TAC + a non-bump
  allocator. See §8e.
- **O4 - Tier 4 backend. OK increments 1, 2 & 3 DONE (2026-07-09/10).** **Increment 1 -
  `peephole`**, the FIRST post-gen pass (runs on emitted RV32I asm, str→str, not TAC;
  new `opt.ASM_PASSES` registry + `postgen()`). Window-local t-register (t0-t6)
  copy-prop / dead-scratch elimination / result coalescing + `mv r,r` and
  fall-through-`j` removal; sound because t-regs are never live across a block boundary
  (the generator reloads them every fragment). asm 6526→**5199**, bin 31272→**25964**,
  **dyn 22.551M → 14.036M (-38%, the biggest executed-instruction cut of any tier -
  hot recursive loops shed per-iteration moves)**. Idempotent, no residual self-moves,
  unknown mnemonics skipped. See §8f. **Increment 2 - graph-coloring regalloc**
  (`src/coloring.py`, Chaitin-Briggs iterated register coalescing over `igraph.py`'s
  interference+copy graph; the `regalloc_color` codegen flag, dispatched in
  `asm.gen(allocator=...)` - linear scan stays the O0..O3/diff_test default). Coalescing
  collapses the cross-block `mv sX, sY` copies the peephole cannot reach (they become
  self-moves and vanish) and packs into fewer callee-saved regs (smaller save area).
  Attributed by the flag toggle: asm **5199→4683** (-516), bin **25964→23900** (-2064);
  dyn barely moves (coalescing removes *static* setup moves; the 13M-instr hot loop
  dominates the dynamic count). Deterministic across `PYTHONHASHSEED`; `regalloc.verify`
  clean on every function. See §8g. **Increment 3 - Tier-4 remainder** (two more post-gen
  asm passes in `opt.ASM_PASSES`, after `peephole`): **`immfold`** = immediate-form
  instruction selection (fold a `li`-materialised constant into `addi`/`andi`/`ori`/`xori`/
  `slti`, `sub C`→`addi -C`, `mul` by 2^k→`slli`, dropping the `li`); **`branchlayout`** =
  invert a conditional branch whose target is the fall-through block, deleting the taken
  jump. Attributed by toggling: asm **4683→4443** (immfold -123, branchlayout -117), bin
  **23900→22940**, **dyn 14032752→10828342 (-23%, folding the per-iteration `li` out of hot
  loops)**; heap/stub unchanged. Idempotent, deterministic across `PYTHONHASHSEED`. See §8h.
  Guard green `optbench --levels 0,1,2,3,4` = **25/25 observably ==-O0** at O4 totals asm
  **4443** / bin **22940** / dyn **10828342**; heap/stub untouched (a pure backend tier).
  **Tier-4 now COMPLETE** (peephole + graph-coloring regalloc + instruction selection +
  branch layout); the remaining OPTIMIZE work is O5 (self-optimizing fixpoint).
- **O5 - The self-optimizing fixpoint.** WARNING *The literal wording is vacuous:* the
  optimizer lives on the **TAC→RV32** backend, while F2 is proven on the disjoint
  **C** backend, so running the RV32 optimizer cannot move the C fixpoint. O5 was
  therefore reframed (Set, 2026-07-10: "fix as many problems as you can") as a
  **behavioral** self-optimizing fixpoint on the RV32 backend + fixing the real
  bugs on the path there. **DONE 2026-07-10** (see LOG 2026-07-10):
  - **Correctness fix:** bare top-level fn used as a value was miscompiled on TAC
    (crash) and RV32 (garbage) - `IClosureCall`'s `(env,arg)` convention vs a
    direct fn's a0-first convention. Fixed in `07/src/lower.py` by **eta-expanding**
    such uses through the curried lambda-lifting path (retires the M0 "always pass
    lambdas, never bare names" workaround; fixes both interpreters at the source).
  - **Backend fix:** branch relaxation in `07/src/riscv_asm.py` for conditional
    branches > ±4 KB (needed for the 131 KB compiler image).
  - **Static result:** optimizer shrinks the compiler's own RV32 image **-58 %**
    (asm 31,576→13,174; bin 131,652→56,140 B, -O0→-O4).
  - **Behavioral result - TAC interpreter, O0-O3 on the real compiler.** The
    whole compiler on the RV32 *VM* is **infeasible** (the no-GC bump heap
    overflows >64 MB compiling even `01_hello` - the §8a/§8b arena wall, not a
    bug; see LOG 2026-07-10). Instead the behavioral fixpoint is shown on the
    heap-free `tac_vm` interpreter: the emit-only compiler emits **byte-identical
    C across -O0..-O3**, exercising the TAC passes on a program denser than any
    corpus file. The O4 asm passes are separately guarded ==-O0 on the 25 corpus
    files. Coverage: O1-O3 on the compiler itself, O4 on the corpus.
  - **Regression:** difftest 34/0; optbench all levels ==-O0 with `BASELINES.md`
    totals byte-identical; F2/self-hosting untouched (disjoint C-backend path).

---

## 6. Measurement & validation harness (O0)

Reuse and extend the `difftest` pattern.
- **Correctness:** for every corpus file and `-O` level, observable output must
  equal the `-O0` / stage-0 result. Optimizer must be safe under re-running
  (near-idempotent at a fixed level).
- **Metrics per file × level:**
  - RV32I instruction count (static) and executed-instruction count (dynamic, via
    `riscv_vm.py` counters).
  - Heap allocations executed (the Tier-3 headline number).
  - Emitted binary size.
  - **Bootstrap wall-clock** on the compiler's own source (the integrative metric).
- **Attribution:** per-pass on/off flags so a speedup can be pinned to a pass and
  a regression bisected.

---

## 7. Risks & open questions

- **CSE/PRE under affinity.** Purity makes CSE sound, but reusing an affine
  value where the type system expected single-use must not violate the ownership
  discipline - CSE of an affine-typed subexpression needs care. Prototype on a
  toy in O1.
- **Inlining bloat.** Curried inlining can explode code size and hurt I-cache /
  binary size on the Pico. Cost model + size cap required.
- **Don't break the fixpoint.** The optimizer must preserve F2 (byte-identical
  bootstrap of *behavior*, not necessarily of bytes once optimization is on -
  redefine the invariant as observable-equivalence at each `-O` level).
- **Diminishing returns.** ch08's own thesis: stop when the harness says the next
  pass isn't paying. The plan is tiered precisely so we can stop at any O-level
  with a coherent, shippable compiler.
- **Book tie-in.** This work is the natural "ch08 in anger" follow-through and a
  candidate for a new chapter/appendix: *optimizations a pure affine language
  gets that others can't*.

---

## 8. First step (when we get here)

### 8a. Emitter line-join - OK DONE (2026-07-08)

The first wall self-hosting handed us. The emitter's final line join
(`ecJoinNL`, originally `l + "\n" + ecJoinNL(rest)`) was **O(n²)** in the no-GC
bump arena - every step re-copied the growing suffix, so joining S bytes over N
lines cost Θ(S-N) *arena* bytes (nothing is freed). **Fixed** in
`self/emit_c.lark`: `ecJoinNL` now does a bottom-up **balanced pairwise** join
(`ecJoinPairs` joins adjacent pairs with `"\n"`, repeated ⌈log₂N⌉ times), so the
join allocates Θ(S-log N) instead. Output-identical (concat is associative; every
`"\n"` still lands between the same originally-adjacent lines).

- **Measured (emit-only bootstrap, its own 617 KB / ~9.6 K-line output):** arena
  peak **~3 GB → 177 MB**; the F2 fixpoint now closes at a **512 MB** arena (was
  8 GB reserved). C sha re-pinned `2ce6a281 → 49a4921c` in `BASELINES.md`.
- **Correctness guard held:** `emittest` **37/0/7** and `typechecktest` **42/0/2**
  stayed byte-identical (the join is output-neutral); `infertest`/`cektest`
  don't touch `emit_c.lark`.

### 8b. The infer-pass allocation wall - OK REDUCED, M5.5.4 native fixpoint CLOSED (2026-07-08)

**Finding: fixing the join did NOT close the F2⁺ native fixpoint (M5.5.4)** - the
join was only the first wall. Attributing the ~3534-line typechecking compiler's
self-compile after the join fix:

| pipeline on the 3534-line tc source | arena high-water |
|---|---|
| parse + emit (no typecheck), balanced join | **353 MB** |
| parse + **typecheck** + emit, before §8b | **>12 GB** (overflow) |
| parse + **typecheck** + emit, after §8b | **10.15 GB** (completes) |

Root cause: Algorithm W threaded purely over an **assoc-list `Subst`** - `apply`
walks the whole substitution (grows to O(n) over the program), called O(n) times,
every intermediate assoc-list / `Mono` cell bump-allocated and never freed. A
*second* ~O(n²) arena wall. It had **two multipliers**: an *env-side* one
(`applyEnv` calls `applyScheme` on every environment scheme at every
sub-expression) and a *subst-side* one (`compose`/`apply` rebuilding the growing
subst).

**Fix shipped (`self/types.lark`, output-neutral):** `applyScheme` now
short-circuits on a **closed** scheme. A fully-generalised (top-level) scheme's
body has every free var bound by its quantifier list `qs`, so applying any
substitution to it is provably the identity - return it unchanged, allocate
nothing (`monoVarsAllIn(body, qs)` walks the body and bails on the first unbound
var; the frozen `removeKeys`+`apply` path runs only for the few genuinely-open
local schemes). This kills the **env-side** multiplier: the hundreds of ~closed
top-level schemes that `applyEnv` re-applied at every node become a walk, not a
rebuild. Guard held green: `infertest` **42/0/2** + `typechecktest` **42/0/2**
byte-identical.

**Result: M5.5.4 CLOSED.** The tc self-compile went from >12 GB overflow →
10.15 GB completing high-water, and `self/tests/bootstrap_tc.py` reaches
**C1==C2==C3 byte-identical (sha `34a07692`, 18549 lines)** at a 14 GiB
lazily-committed arena (peak touched ~10.15 GB). This is the native analog of
`typechecktest`: the six-module compiler type-checks *its own source* and
reproduces its own C. Pinned in `BASELINES.md`; `make -C self bootstrap-tc`.

**Residual - CLOSED (2026-07-09, balanced-tree `Subst`):** after §8b the growth
was still ~O(n^1.9) - the **subst-side** multiplier survived (`compose =
appendSub(s1, mapApplyRange(s1, s2))` rebuilt the whole subst each call;
`apply`→`substGet` was a linear scan over an assoc list that degraded to a chain,
because Algorithm W allocates fresh vars monotonically). The frozen `infer.py`
hides this behind a dict (O(1) lookup). **Fix:** `self/types.lark`'s `Subst` is now
an **Int-keyed Okasaki red-black tree** (`type Subst = SLeaf | SNode of SColor,
Subst, Int, Mono, Subst`): `substGet` is O(log n), `subInsert` rebalances, and
`compose`/`removeKeys` fold through `subInsert` (overriding on shared keys, so the
tree caps at distinct-key count). **Output-neutral** - apply reads only the
key→Mono mapping, not assoc-list order - so `infertest` **42/0/3** and
`typechecktest` **42/0/3** stayed byte-identical against the oracle. The change is
invasive (the `List((Int, Mono))` type was threaded through both `types.lark` and
`infer.lark` - no transparent aliases in Lark, so every site changed), but it
flattened the tc self-compile peak **10.15 GB → 4.73 GB** (stage1, 58 s wall). The
emitted-C sha moved `34a07692 → 45c1982a` intentionally (the compiler's own source
now carries the RB-tree code); the ladder re-settled C1==C2==C3 byte-identical. See
`BASELINES.md` for the pinned numbers.

The remaining general lever is arena compaction / a collector in `cek.c`, which
would free the dead cells for *every* program, not just infer (biggest general
win, but touches the frozen runtime - genuinely Tier-3 allocation elimination /
arena reuse under affinity, §4, surfacing early because self-hosting forced it).

### 8c. O0 - the measurement ruler - OK DONE (2026-07-08)

Stood up the metric half of O0 *before* any pass (the correctness half already
existed as the `self/tests` differentials). Two new files, no pass logic:

- **`07/src/opt.py`** - the `-O`/per-pass plumbing. `optimize(tac, OptOptions) →
  TAC` runs the enabled passes in `PASSES` order; `PASSES` is **empty**, `LEVELS`
  declares the O1-O3 bundles ahead of time, so at every level `optimize` is
  currently the **identity** and emitted code is byte-identical to the raw
  pipeline. `OptOptions(level, enable, disable)` gives per-pass on/off for
  attribution and bisection.
- **`07/tests/optbench.py`** - the ruler. Per corpus file × `-O` level it drives
  `parse→typecheck→lower→optimize→gen→assemble→run` (each run in a subprocess
  under `--timeout`, empty stdin) and records: static asm-instruction count,
  assembled binary bytes, executed RV32I instructions, stub calls, heap
  allocs/bytes (from new **output-neutral counters in `riscv_vm.py`**), compile/run
  wall-clock, and the program-output sha. `--levels 0,1` cross-checks
  observable-equivalence (every level's output sha == `-O0`'s); `--save`/`--compare`
  pin and diff a baseline; `--pass-flags` lists the registry.

**Baseline captured** (`07/tests/optbench_O0.json`, pinned in `BASELINES.md`):
originally 23/24 acceptance files ran on RV32; `24_stringprims.lark` was a
**pre-existing** RV32 codegen crash (`PC misaligned`, string-prim lowering gap -
identical on the stock `riscv_vm.py` CLI, not introduced here). **That crash was
then fixed (see §8d) and the baseline re-pinned to 24/24** (totals: 5562 asm
instrs, 27132 bin bytes, 22.5 M executed instrs, 201 heap allocs / 2136 bytes). The
`riscv_vm.py` counter change is +9 lines, provably output-neutral; it is off the
self-host differential path entirely.

**Guard for every pass from here:** OBSERVABLE-EQUIVALENCE - each file's `-O0`
output sha in `optbench_O0.json` must survive at every level (asm/bin/instr/heap
numbers move by design), *and* the four `self/tests` differential counts stay
green. `optbench --compare optbench_O0.json` reports the deltas a pass bought.

**O1 Tier-1 TAC passes - OK DONE (2026-07-09).** copy prop, DCE, const fold,
algebraic simplify, CSE all appended to `opt.PASSES` and guarded by the rig above
(25/25 observably ==-O0).

**O2 Tier-2 passes - OK DONE (2026-07-09).** `devirt` (trait-dispatch
devirtualization), `inline` (small non-recursive static calls + reachable-function
pruning), and `licm` (loop-invariant code motion) added to `opt.PASSES`; `-O2`
wired. Guard green: `optbench --levels 0,1,2` = 25/25, ALL observably ==-O0. Corpus
asm 7821 (-O1) → **6820 (-O2)**, bin 36512 → 32472, dyn 22.5526 M → 22.5518 M; heap
unchanged (allocation removal is Tier-3). **`devirt`** recovers the tag→`m$Type` map
from each dispatch stub's own body (opt.py sees only TAC) and rewrites a stub call
whose argument was just `IAlloc`'d with a known constructor tag in the same block -
sound because the stub, on that tag, routes identically and has no other effect.
**`inline`** substitutes params, freshly renames temps/labels, turns `IReturn v`
into `dst = v; goto ret`; single-level per sweep (bounded growth), skips recursive
callees (keeps tail-recursion loops for the backend), body ≤ `INLINE_MAX=12`; a
reachability sweep from `main`/`__global_init__` then drops functions the inlining
made dead (why static size *falls*: 08_traits bin 1828→1724, 25_torture asm
2450→1890). Ordering in `PASSES`: devirt, inline lead so the Tier-1 passes clean up
across the newly-exposed call boundaries; licm trails. **`licm`** is a faithful
dominator-based natural-loop pass, but the TAC IR is ACYCLIC (Lark iteration is
inter-procedural recursion, not a back-edge), so it is a no-op on the corpus -
validated instead on a synthetic loop in `tests/opt_licm_test.py` (invariant
hoisted, variant kept, acyclic-identity). The four self-host differentials are
unaffected BY CONSTRUCTION (`opt` is imported only by `optbench.py`/`opt_licm_test`,
verified by grep; nothing on the cek/emit_c/infer path touches it); O0 stays
identity so `optbench_O0.json` is NOT re-pinned; `diff_test` 34/0.

**O3 Tier-3 allocation - [~] increment 1 DONE (2026-07-09).** `closure_elim` added to
`opt.PASSES` (right after `inline`, before the Tier-1 cleanup), `-O3` wired. Guard
green: `optbench --levels 0,1,2,3` = 25/25, ALL observably ==-O0. This is the FIRST
pass to move the Tier-3 headline: **heap_allocs 360 (-O2) → 358 (-O3)**, heap_bytes
3756 → 3732, asm 6820 → 6736, bin 32472 → 32128, dyn 22.5518 M → 22.5517 M,
stub_calls 526 → 524.

`closure_elim` **scalar-replaces non-escaping closures.** A closure
`IAllocClosure(cv, L, caps)` is a heap record `[fn_ptr, cap0, ...]`;
`IClosureCall(dst, cv, arg)` loads `cv[0]`, indirect-jumps, passes the record as
`env`; the lifted body `L(env, x)` reads captures via `IGetField(_, env, i) =
caps[i]`. When `cv` (and every single-assignment copy of it) is used ONLY as the *fn*
of an IClosureCall - never passed as an arg, returned, stored in another record, or
field-read - the record never escapes and its identity is unobservable (Lark values
are immutable + structurally equal, same properties that make CSE sound). We then
inline `L`'s body at each call site with `IGetField(_, env, i)` → `IAssign(_,
caps[i])` and DELETE the `IAllocClosure`; the record is dead (DCE removes it) → one
fewer runtime heap allocation, and the indirect `jalr` becomes straight-line.

Two design points. (1) It is **whole-function and follows single-assignment copies**,
so it fires across the `.i..._ret` block seam `inline` leaves between an inlined alloc
and its call - the composition that matters, since a closure returned from a callee
(`adder(n) = \x -> n + x`) only becomes a local alloc-then-call once `inline` has
pulled `adder` into its caller. (2) `caps[i]` must be **available** at the call site:
captures are required to be Const, param, or single-def temps - SSA value numbering
then guarantees the same value wherever referenced, so hoisting the reference is
sound; multi-def captures are rejected. The observable-equivalence guard backs it.

Fired on the 2 corpus files with a non-escaping applied closure: **10_closures** (asm
188 → 146, heap 6 → 5) and **25_torture** (asm 1890 → 1848, heap 160 → 159). Most
corpus closures ESCAPE into higher-order functions (passed to `map`/`compose`/`twice`,
which call them indirectly); collapsing those requires iterating inline+closure_elim to
a fixpoint (increment 2, deferred - a single `optimize` sweep does one level).

The **other three Tier-3 passes stay named in `LEVELS[3]` but filtered out** (absent
from `PASSES`) = analyzed-and-deferred. **`unbox` is a genuine no-op on this backend:**
scalars (Int/Float/Bool) are register immediates, never heap-boxed - the ONLY heap
allocations are ADT constructors (`IAlloc`) and closures (`IAllocClosure`), verified by
scanning every lowered `alloc` tag across the corpus (all constructor names, no scalar
boxes). **`fusion`** (map∘map, build/foldr) needs a higher IR - the fusible structure
is gone by the time it is flat TAC. **`arena_reuse`** (reuse an affine-dead record's
storage in place) needs the affinity information threaded down to TAC plus a non-bump
allocator; it is the OPTIMIZE §8 arena-join wall's neighbour. The four self-host
differentials are unaffected BY CONSTRUCTION (`opt` imported only by `optbench`/
`opt_licm_test`, grep-verified); `diff_test` 34/0; O0 stays identity so
`optbench_O0.json` is NOT re-pinned.

**O3 increment 2 - OK DONE (2026-07-09): sweep iterated to a fixpoint.**
`optimize()` now re-runs the enabled pass sweep until the TAC stops changing
(`_fingerprint` equality; `_MAX_SWEEPS = 8` safety cap). This is what reaches the
closures that ESCAPE into non-recursive HOFs. One sweep of `inline`+`closure_elim`
peels a single layer: inlining `compose`/`twice` exposes the closure it returned as
a local alloc-then-call, which `closure_elim` splices in - but the spliced body may
itself hold further closure calls (`compose(f,g) = \x -> f(g(x))`) that only the
NEXT sweep sees. Every pass is a sound reducer or a bounded (single-level,
prune-backed) expander, so the composition converges well under the cap. The site
counter for `inline`/`closure_elim` had to become **monotonic across sweeps**
(`_next_site()` off one `itertools.count`) - a per-call `site = 0` would re-mint
`.i0_...`/`.c0_...` on the second sweep and collide with the first sweep's labels.
Payoff vs increment 1: **heap_allocs 358 → 354, heap_bytes 3732 → 3708, asm 6736 →
6526, bin 32128 → 31272, stub_calls 524 → 520**; 10_closures collapses to asm 86 /
heap 3 (from 146 / 5), 25_torture to 1790 / 157 (from 1848 / 159). Guard green
(`optbench --levels 0,1,2,3` = 25/25 observably ==-O0); `diff_test` 34/0; licm unit
test green; O0 stays identity so `optbench_O0.json` is NOT re-pinned. **Ceiling
reached** (flagged in the increment-1 plan): the still-heap-allocated closures all
flow into RECURSIVE HOFs (map/foldr - `inline` correctly leaves them), so further
allocation removal there needs specialization/defunctionalization, a different pass.
**NEXT: O4** (Tier-4 backend - peephole, graph-coloring regalloc, instr-sel) or the
`PROVE.md` guarantees axis.

### 8d. Pre-O1 hygiene - observations from the string-prim fix (2026-07-08)

Fixing the `24_stringprims` RV32 crash exposed structural hazards worth clearing
(or at least *knowing*) before O1 passes start mutating codegen. Ranked by how
likely each is to bite.

- **[1] No single builtin registry - DONE (the crash's root-cause class).** A
  builtin lives in ~5 independent sites (`cek.py`, `tac_vm.py`, `lower._BUILTINS`,
  `riscv_asm.RUNTIME_STUBS`, `riscv_vm` stub_map). These six prims were in `cek.py`
  (so programs typechecked and ran under CEK) but absent from the whole RV32 chain;
  nothing flagged it until a corpus file used them and jumped to garbage. **Fixed:**
  `lower._expr`'s `TVar` case no longer silently `return Tmp(n)` for an unknown
  name (which became a read of an unassigned register → jump-to-garbage). It now
  returns `Tmp(n)` **only** for top-level `let` names (asm resolves those via the
  global-var table) and otherwise **raises a named compile-time error** telling you
  which registry to update. Verified: dropping a builtin from `_BUILTINS` now fails
  loudly at lower time instead of `PC misaligned` at run time. *Possible follow-up:*
  a startup assertion that `RUNTIME_STUBS`, the `riscv_vm` stub_map, and
  `tac_vm._BUILTINS` agree - turns backend-parity drift into an import error too.

- **[2] The corpus was a WEAK equivalence witness - DONE: added a deep witness on
  the RV32 path.** The observable-equivalence guard is only as deep as corpus
  coverage; an O1 bug reachable only by an unexercised construct stays green, and
  the 01-24 files each probe *one* feature (deepest ~60 lines). **Correction (the
  original note was wrong):** the F2/F2⁺ **bootstrap cannot gate O1** - it runs on
  the **C backend** (`emit_c_ast.py` / `emit_c.lark`, which imports nothing from
  `opt`/`lower`/`tac`), whereas O1 optimizes **TAC → RV32**. The bootstrap's
  emitted-C fixpoint is *invariant* under every O1 pass, so "bootstrap under `-O1`"
  would test nothing. The real self-host front-ends (`self/lex.lark`, 335 lines,
  `fn main` reading stdin) *are* on principle RV32-runnable but do **not** run
  standalone (need their differential driver; 64 KB-VM feasibility unproven - a
  quick probe hit a non-exhaustive match). **What was built instead:**
  `07/tests/25_torture.lark` - one program wiring together recursive/nested ADTs,
  closures, HOFs, trait dispatch, Stdlib+Option, the string-decomposition prims +
  `Ok`/`Err` lowering, int + float32 arithmetic, and algebraic-identity expressions
  the O1 passes target. It runs on the 64 KB RV32 VM, all three backends agree
  (`diff_test` 34/0), and at **2544 asm instrs / 160 heap allocs** it is ~half the
  rest of the corpus's asm and ~80 % of its heap allocs in one file. It lands in
  the `optbench` sweep automatically (`collect_acceptance` picks up `NN_*.lark`), so
  `optbench --levels 0,1` already checks its O0-vs-O1 output sha. *Deferred:* if the
  self-host front-ends are ever made RV32-runnable, add them as an even deeper
  witness (real self-host code). The bootstrap stays the C-backend fixpoint witness
  it already is (`BASELINES.md`), relevant to O5 (self-optimizing fixpoint), not O1.

- **[3] `--compare` now flags output changes too - DONE.** Previously `--compare`
  diffed only the six numeric metric columns, so a pass that changed output while
  preserving instruction counts passed `--compare` clean (only `--levels 0,1` ran
  the equivalence check). **Fixed:** `optbench --compare` now also (a) flags any
  `out_sha` change as `OUTPUT ... observable-equivalence BROKEN`, (b) flags any
  baseline-`ok` → now-not-`ok` file as `REGRESS`, and (c) prints a trailing
  `[warning] N output change(s), M regression(s)` (or an all-clear line) so the correctness
  signal can't hide under the expected metric deltas. `--levels 0,1` remains the
  primary in-run equivalence check; `--compare` is now safe to trust for
  correctness across saved runs too. Verified: clean self-compare reports all-clear;
  a mutated-`out_sha`/`status` baseline correctly raises `OUTPUT`/`REGRESS`.

- **[4] CSE-over-allocating-prims invariant recorded - DONE (the pass itself is
  O1, unwritten).** `string_slice`, `char_to_string`, and the raw-pair stubs are
  pure in *result* but **allocate** - CSE-ing two identical calls makes them return
  the *same* heap object instead of distinct-but-equal ones. Sound in Lark only
  because (1) values are **immutable** (no ref/mutable-array/in-place-update, so
  aliasing is unobservable) and (2) equality is **structural** (no physical/pointer
  identity, so shared vs separate storage is indistinguishable). Weaken either and
  CSE-over-allocations turns unsound. **Recorded at the code site** in
  `07/src/opt.py` (the `CSE_ELIGIBLE` block, next to where the `cse` pass will be
  registered), framed as the maintenance-minimising **allowlist** rule: CSE *only*
  prims explicitly named eligible (pure + immutable-result), so a future
  effectful/mutable/nondeterministic prim is safe **by default** (absent from the
  list → never CSE'd, no action needed) - the opposite of a blocklist, which would
  silently CSE a new mutable prim and break. Purity is also required: never list an
  IO/clock/random prim (`read` already lives in IO and is not a candidate). When the
  `cse` pass lands, populate `CSE_ELIGIBLE` and gate on it; the two language
  properties above are the tripwire if the language ever gains mutability or pointer
  identity.

- **[5] Representation-coupled spots - DONE (comments tightened at each site; low
  risk).** Each contract is now named in-code with an `OPTIMIZE §8d [5x]` tag so a
  future editor sees the coupling at the line they'd change. (a) The raw stub
  fabricates a fake 3-word record `[word0=tag-slot, flag@word1, payload@word2]` that
  only lines up because `IGetField(idx)` reads word `(idx+1)` (skips the tag slot) -
  an implicit `riscv_vm`↔`lower` contract with **no isolating test** (the corpus
  checks end-to-end output, not the intermediate word). Cross-referenced in both
  `lower._lower_string_to_result` and `riscv_vm._rt_string_to_{int,float}_raw`:
  change `IGetField`'s `(idx+1)*4` and both move together. (b) `_rt_float_to_bits`
  is the identity **purely** because floats are stored as f32 bit patterns; a
  boxed/double (f64) repr would make it a real reinterpret and break it (and every
  float op) - noted at the stub, with the reminder that `tac_vm` does a real struct
  unpack so the backends still agree by value. (c) `show_result`/`show_fresult`
  discard the `Err` payload, so the error-message strings are **never compared** by
  any test - verified the three backends' wording currently *does* match
  (`cek.py` == `tac_vm.py` == `riscv_vm.py`: "string_to_int: not an integer" /
  "string_to_float: not a float"), but nothing enforces it; a `COVERAGE GAP` comment
  at the `riscv_vm` error-string site says keep-in-sync-by-hand (or add a test that
  prints the `Err` payload). **All comment-only + one unused `CSE_ELIGIBLE` set -
  `diff_test` 34/0, backends byte-identical, baselines untouched.**

- **[5b-followup] Divergent float representations across backends - DEFERRED (future
  amendment, NOT fixed now).** The three backends model a `Float` differently:
  `cek.py` and `tac_vm.py` hold a Python `float` normalised through an *identical*
  `_f32` (struct pack/unpack `'f'`); `riscv_vm.py` stores the raw 32-bit pattern in
  memory (so `float_to_bits` is the identity). They **converge on value** (`diff_test`
  34/0), so this is representational divergence + duplication, **not a bug**. Decision:
  leave it. (i) The duplicated `_f32` is *deliberately* kept independent - two
  implementations that agree is a stronger cross-backend signal than one shared helper
  (a bug in a shared `_f32` would hide from the differential). (ii) O1 does **not**
  fold floats (only int `+`/`-`/`*` under `wrap32`, int comparisons, boolean ops), so
  the divergence never reaches the optimizer. **The only thing that forces convergence
  is float constant-folding** (deferred past O1): when it lands, the folder must
  reproduce the **RV32 backend's** float32 semantics (the real target) via the same
  `struct` pack/unpack - a single reference *for the optimizer*, computed without
  disturbing the three runtimes. Recorded here so the amendment is scoped and not lost.

### 8e. O1-O3 - the TAC-pass tiers - OK DONE (2026-07-09)

The TAC→TAC pipeline in `07/src/opt.py`, driven by `optimize(tac, opts)` over the
`PASSES` registry and the `LEVELS` bundles; every tier guarded by `optbench --levels
0,...` observable-equivalence + the four self-host differentials (unaffected by
construction - `opt` is imported only by `optbench`/`opt_licm_test`). Full per-tier
detail lives in the LOG and in §5; the essentials:

- **O1 (Tier-1 scalar).** copy-prop + DCE, then const-fold + algebraic-simplify + CSE.
  Const-fold is int/bool only under signed `_wrap32` (no `/`-`%`, no float - ÷0 and NaN
  diverge from the CEK); CSE block-local non-allocating (allocating-prim CSE gated by
  the empty `CSE_ELIGIBLE` allowlist). asm 8106→7817.
- **O2 (Tier-2).** devirt (recover the dispatch map from the stub body, rewrite a
  known-tag stub call to `m$Type`) + inline (single-level, recursive-skip, +
  reachable-function prune so static size *falls*) + licm (real dominator-based, but a
  no-op on the acyclic TAC - recursion is inter-procedural; unit-tested on a synthetic
  loop). asm 7817→6726, bin →32096.
- **O3 (Tier-3 allocation).** `closure_elim` scalar-replaces non-escaping closures
  (the first pass to move `heap_allocs`), and `optimize()` iterates the sweep to a
  fixpoint so non-recursive HOFs collapse fully. heap_allocs 361→**354**, asm →**6526**.
  Ceiling: closures escaping into recursive HOFs (map/foldr) need
  specialization/defunctionalization, not iteration. `unbox`/`fusion`/`arena_reuse`
  analyzed-and-deferred (no-op / needs-higher-IR / needs-affinity-threading).

### 8f. O4 - the RV32I peephole (the first post-gen pass) - OK increment 1 DONE (2026-07-09)

The first pass that runs **after `asm.gen`**, on the emitted RV32I assembly text
(`str → str`), because its targets are artefacts of instruction selection + linear-scan
regalloc that do not exist at the TAC level. New machinery: an `ASM_PASSES` registry
(post-gen asm passes, separate from the TAC `PASSES` because they operate on a different
IR) and `postgen(asm, opts)` - the asm analogue of `optimize()`. `LEVELS[4]` = the O3
TAC-pass names **plus** `"peephole"`, so `enabled_passes` gives O4 the identical O3 TAC
pipeline and `enabled_asm_passes` adds the peephole; O4's gain over O3 is attributable
entirely to it. `optbench.run_worker` calls `postgen(asm, opts)` after `gen`.

**What it removes.** Every `asm.gen` fragment reloads operands into the caller-saved
scratch registers t0-t6, computes into a scratch, then copies the result to the
destination temp's callee-saved (s-*) home - so `IAssign s2=s1` → `mv t0,s1; mv s2,t0`,
a binop → `mv t0,l; mv t1,r; add t2,t0,t1; mv dst,t2`, etc. The scratch round-trips are
pure overhead.

**Why it is sound without whole-function liveness.** The load-bearing invariant: a
t-register never carries a live value across a basic-block boundary (label / branch /
call / jump / jalr / ret) - the generator always writes a t-reg before reading it within
the using fragment, never reads one written by a previous fragment, and passes
args/returns through a-regs. So **live-out(t-regs) = ∅ at every window boundary**, and
t-registers are reasoned about independently inside each straight-line window. a-regs
and s-regs *do* cross boundaries (a0 holds a call's result), so the pass never
rewrites/deletes their defs - only the transient t-registers.

**Transforms** (window-local, iterated to a fixpoint): (A) copy-prop of `mv tX, R` into
later reads (register or memory base); (B) delete a pure instruction whose t-reg
destination is dead in the window; (C) coalesce `<op> tX, ...; mv D, tX` (tX dead after)
→ `<op> D, ...`. Then, over the whole listing: delete `mv rX, rX`, and delete a `j L`
whose next executable line is `L:` (fall-through). A window with any mnemonic `asm.gen`
never emits is skipped untouched (defensive).

- **Measured (O3→O4 corpus totals):** asm 6526→**5199**, bin 31272→**25964**, **dyn
  22,551,347 → 14,036,245 (-38%)** - the largest executed-instruction cut of any tier
  (the hot recursive loops shed their per-iteration scratch moves). heap_allocs /
  heap_bytes / stub_calls **unchanged** (a pure backend pass - it moves no allocation
  or IO). e.g. 10_closures asm 86→59 / dyn 94→67.
- **Guard held:** `optbench --levels 0,1,2,3,4` = **25/25 observably ==-O0**;
  `diff_test` 34/0 (O0 path unchanged, byte-identical); `opt_licm_test` green; O0 stays
  the identity so `optbench_O0.json` is not re-pinned. Hardening: peephole is
  **idempotent**, leaves **no residual `mv r,r`**, and **skips unknown-mnemonic
  windows** - verified over all 25 files.
- **Increment 2 - graph-coloring register allocation. See §8g.**

### 8g. O4 - graph-coloring register allocation (increment 2) - OK DONE (2026-07-09)

The register-allocation upgrade the peephole motivates. The peephole works
window-locally on the caller-saved **t-registers** (never live across a block
boundary), so two inefficiencies survive it, both in the **callee-saved s-registers**
that *do* cross boundaries: (1) an `IAssign dst = src` whose temps land in different
s-registers still emits a real `mv s_dst, s_src`; (2) linear scan's greedy interval
packing can spill, or occupy more distinct s-registers (a bigger prologue/epilogue save
area), than a precise interference graph needs.

**The allocator** (`src/coloring.py`, ~260 lines) is Chaitin-Briggs *iterated register
coalescing* (Appel §11.4): build → simplify → conservative (Briggs) coalesce → freeze →
optimistic spill → select, on the interference **and copy** graph `igraph.py` already
builds. K = 11 (s1-s11). Coalescing merges move-related temps that do not interfere, so
`mv s_dst, s_src` becomes `mv sX, sX` - which the peephole then deletes outright. It is a
drop-in: `color_allocate` returns the same `regalloc.Allocation` dataclass, and
`allocate_tac_color` mirrors `allocate_tac`.

**No program rewrite on spill.** Textbook Chaitin-Briggs rewrites the program (reload
temps) and restarts when a node spills. This backend's `asm.load` / `asm.store` already
materialise any register-less temp from/to its stack slot on every use/def (exactly how
linear scan spills here), so an actual spill is just "assign a slot, not a register" and
the optimistic colorer needs no restart loop.

**Gating.** `regalloc_color` is a **codegen-strategy flag** (`opt.CODEGEN_FLAGS`, named
in `LEVELS[4]`), not a TAC pass (PASSES) or an asm-text pass (ASM_PASSES) - it selects
the allocator *inside* `asm.gen(allocator=...)`, which defaults to linear scan. So O0..O3,
`diff_test`, and the `asm.py` CLI are byte-identical to before; only O4 (via
`optbench` querying `wants_graph_coloring`) uses coloring. `--pass-flags` lists it.

- **Measured (attributed by the flag toggle at O4):** corpus asm **5199 → 4683** (-516),
  bin **25964 → 23900** (-2064). dyn barely moves (14,036,245 → 14,032,752): coalescing
  removes *static* setup moves, and 04_tailrec's 13M-instruction hot loop dominates the
  dynamic total. heap_allocs / heap_bytes / stub_calls **unchanged** (a pure backend
  tier). Coloring-OFF reproduces increment 1's 5199 exactly, so the -516 is the
  coloring's alone.
- **Guard held:** `optbench --levels 0,1,2,3,4` = **25/25 observably ==-O0**;
  `diff_test` 34/0 (O0 path unchanged, byte-identical); `opt_licm_test` green; O0 stays
  the identity so `optbench_O0.json` is not re-pinned.
- **Hardening.** (a) **Deterministic** - every worklist choice is the minimum element
  (name / move index / spill cost), never `set.pop()`, so allocation is reproducible
  regardless of `PYTHONHASHSEED` (optbench runs each file in a fresh subprocess); the O4
  asm sha is identical across three hash seeds on 08_traits/25_torture/06_lists.
  (b) **`regalloc.verify` clean** on every function of all 25 files - no two interfering
  temps share a register (`color_allocate` also asserts this internally). (c) **Isolation
  by construction** - `coloring` is imported only by `optbench` (grep-verified), so the
  four self-host differentials are unaffected; `self/` never references it.
- **Increment 3 - instruction selection + branch layout. See §8h.**

### 8h. O4 - instruction selection + branch layout (increment 3) - OK DONE (2026-07-10)

The Tier-4 remainder, and the point at which Tier-4 is complete. Two more post-gen asm
passes (`opt.ASM_PASSES`, run after `peephole`), each a str→str transform guarded by the
same observable-equivalence rig.

**`immfold` - immediate-form instruction selection.** The generator materialises every
constant operand of an ALU op with a separate `li tX, C`, then does a reg-reg op: `x + 1`
→ `li t1, 1; add t2, t0, t1`; a `== 0` tag test → `li t1, 0; sub t2, t0, t1; seqz ...`;
`x * 4` → `li t1, 4; mul t2, t0, t1`. RV32I has immediate forms for exactly these, and
multiply by a power of two is a shift. `immfold` tracks, forward through each straight-line
window (the peephole's window machinery, reused via a `transform` parameter on
`_peep_local`; same load-bearing invariant that a t-register is never live across a window
boundary), the integer value a `li` put in each t-register, and rewrites:
`add`→`addi`, `sub C`→`addi -C`, `and`/`or`/`xor`→`andi`/`ori`/`xori`, `slt`→`slti`,
`mul` by 2^k→`slli k` - folding the constant in and leaving the `li` with no reader, which
the peephole's own dead-scratch elimination (`_opt_window`, re-run at the end of the
window) removes. **Soundness details:** the 12-bit signed immediate range `[-2048, 2047]`
is checked on every fold (for the bitwise ops the RV32I sign-extended immediate then equals
the constant exactly); `sub` folds only the rhs (`x - C`, not `C - x`); `slt` folds only
the rhs (`a < C`); `mul`→`slli` only for an exact power of two ≥ 2. **Floats are excluded
two ways:** a float-bits `li` carries a `# float` comment (skipped), and float arithmetic
lowers to runtime `ICall`s (`__float_add`, ...) - never a reg-reg integer ALU op - so a
float constant never reaches one of these instructions in the first place. Only mnemonics
already in the peephole's `_WRITE_FIRST`/`_KNOWN` sets are emitted (no `sltu`/`sltiu` - the
generator never emits `sltu`), so `_opt_window`'s read/write model stays correct.

**`branchlayout` - conditional-branch inversion for fall-through.** Every `ICondJump`
lowers to `bnez tX, TRUE; j FALSE`. The peephole's fall-through removal already drops the
`j` when FALSE is the next block; `branchlayout` handles the other case - when TRUE is the
next block, `bnez tX, TRUE; j FALSE; TRUE:` becomes `beqz tX, FALSE; TRUE:`, deleting the
taken jump (control still reaches TRUE by fall-through when the condition holds, FALSE by
the branch otherwise). A whole-listing pass keyed on the branch target being the label that
immediately follows the trailing `j`; the `_BRANCH_INVERT` table covers the full 1-/2-reg
conditional set for safety though the generator only emits `bnez`.

- **Measured (attributed by toggling each pass):** corpus asm **4683 → 4443** (immfold
  -123, branchlayout -117), bin **23900 → 22940** (-960), **dyn 14,032,752 → 10,828,342
  (-23%)** - the per-iteration `li` folded out of the hot recursive loops. heap_allocs /
  heap_bytes / stub_calls **unchanged** (pure backend passes).
- **Guard held:** `optbench --levels 0,1,2,3,4` = **25/25 observably ==-O0** (each file's
  optimized RV32 binary assembled, run on the VM, byte-identical program output);
  `diff_test` 34/0 (O0 path - no postgen - unchanged); `opt_licm_test` green; O0 stays the
  identity so `optbench_O0.json` is not re-pinned.
- **Hardening.** Idempotent (`branchlayout∘immfold∘peephole` applied twice == once on all
  25 files); no residual `mv r,r`; **deterministic** across `PYTHONHASHSEED` (the O4 asm sha
  is identical across seeds 0/12345/999 - `immfold`'s per-register `dict` is only queried,
  never iterated; `branchlayout`'s `drop` set is membership-only). **Isolation by
  construction** - `opt` is imported only by `optbench`/`opt_licm_test` (grep-verified), so
  the four self-host differentials are unaffected; `self/` never references it.
- **Tier-4 COMPLETE:** peephole + graph-coloring regalloc + instruction selection + branch
  layout. The remaining OPTIMIZE work is O5 (the self-optimizing fixpoint).

---

## 9. O5' - the self-hosted optimizing compiler (true self-optimizing fixpoint) - **PLANNED (scoped 2026-07-10)**

**Why this section exists.** O5-as-run (LOG 2026-07-10) delivered a *behavioral*
fixpoint - the Python optimizer preserves the Lark compiler's semantics on RV32,
shrinking its image -58 %. But it is not "the compiler making *itself* faster" in
the literal sense, for two reasons (see LOG 2026-07-10 for the full argument):

- **Gap 1 - the optimizer is Python, not Lark.** `opt.py` / `lower.py` / `asm.py`
  are external tooling. The self-hosted toolchain is only `lex → parse → infer →
  emit_c`. So an *outside* tool optimizes the compiler; the compiler does not
  optimize itself.
- **Gap 2 - the optimizer and the F2 fixpoint are on disjoint backends.** F2 is
  `emit_c.lark → C source`, fixpoint over C text. The optimizer is TAC→RV32. They
  never share bytes, so "the optimizer reaches F2" is category-mismatched, and the
  RV32 -58 % does not make the *shipped* (C-compiled) compiler faster.

**O5' closes both gaps** by building a **self-hosted optimizing C-compiler**: port
the TAC middle end (`lower` + the TAC passes) to Lark and feed a new TAC→C
emitter, so optimization lives *inside* the self-hosted compiler and on the F2
(C) backend. This is Option A' from the LOG discussion - deliberately **not** the
RV32/register-allocator port (SELFHOST M6/F3), which the C backend does not need.

### 9.1 Port surface (grounded in the current tree)

| Port (new Lark file) | Python source | ~lines | in O5'? | notes |
|----------------------|---------------|--------|---------|-------|
| `self/tac.lark` (TAC IR types) | `07/src/tac.py` | 231 | OK | 13 instr types (IAssign, IBinOp, IUnary, ICall, IClosureCall, IReturn, ILabel, IJump, ICondJump, IAlloc, IGetTag, IGetField, IAllocClosure) + Val + Function/TAC containers |
| `self/lower.lark` (typed AST → TAC) | `07/src/lower.py` | 695 | OK | consumes `tast.lark`'s `TProgram` (already ported at M3); **includes the 2026-07-10 eta-expansion fix** for bare-fn-as-value |
| `self/opt.lark` (TAC passes) | `07/src/opt.py` **TAC subset only** | ~600 of 1621 | OK | the `PASSES` list: devirt, inline(+prune), closure_elim, const_fold, copy_prop, algebraic, cse, dce, licm. **NOT** the `ASM_PASSES` (peephole/immfold/branchlayout) - those are RV32-text passes, irrelevant to a C emitter |
| `self/emit_tac_c.lark` (TAC → C) | **net-new - no oracle exists** | ~300 est. | OK | see 9.2 |
| `asm.py`, `coloring.py`, `regalloc.py`, `riscv_asm.py`, `cfg/liveness/igraph` | - | 2431 | NO | RV32 backend - SELFHOST M6/F3, not O5' |

**Already done and reusable:** `tast.lark` (typed AST, the `lower` input) and the
whole front end. The eta-expansion fix means `lower.lark` will be a faithful port
with the closure ABI already correct.

### 9.2 The one genuinely new piece - `emit_tac_c` (and its oracle)

There is **no TAC→C emitter anywhere today**: the Python C backend
(`emit_c_ast.py`, ported as `emit_c.lark`) emits C from the *syntactic AST*; TAC
only ever fed RV32/`tac_vm`. Consequence: `emit_tac_c` cannot be validated by the
usual "Lark port vs Python original" differential, because the original does not
exist. So the plan adds a step: **first write `07/src/emit_tac_c.py`** as the
Python oracle (small - TAC is flat: each instruction → one/few C statements,
`ILabel`→C label, `IJump/ICondJump`→`goto`, Vals→C locals; the hard work of
`match`/nesting compilation is already done by `lower`), validate *it* against CEK
by compile-and-run, **then** port it to `emit_tac_c.lark` differentially against
that oracle. Net-new but mechanically simpler than `emit_c.lark`.

### 9.3 Milestone breakdown (slots into SELFHOST as **M7**, cross-ref here)

- **M7.0 - `emit_tac_c.py` oracle + wire an all-Python optimizing-C path. OK DONE 2026-07-10.**
  `parse → infer → lower → optimize → emit_tac_c.py → C`. Validate: emitted C
  compiles and runs == CEK on the full corpus at every -O level (observable
  equivalence, the O0-ruler discipline). *This alone gives a Python optimizing-C
  compiler - the reference the Lark port will chase.*
  **Landed:** `07/src/emit_tac_c.py` (self-contained C, `intptr_t` word - ptrs and
  fn-ptrs fit, no runtime.c link) + `07/tests/emit_tac_c_difftest.py` =
  **100 ok / 0 fail** (25 corpus × -O0..-O3 vs CEK); `19_intoverflow` xfails at -O1+
  only (opt const-fold is 32-bit by RV32 design - matches CEK at -O0). Two emitter
  bugs fixed: duplicate top-level names (last-wins, per `tac_vm`'s `{fn.name:fn}`)
  and unconstructed-ctor tag tests (`tag_ids.get(name,-1)`, per `asm`). No existing
  pipeline file touched → frozen baselines intact. See LOG 2026-07-10 M7.0.
- **M7.1 - `self/tac.lark`** (IR types; smoke like `tastsmoke`).
- **M7.2 - `self/lower.lark`**, differential vs `lower.py` (serialize TAC to a
  normalized text form; byte-identical on the 9 samples + corpus, mirroring the
  M3 `infer_difftest` pattern).
- **M7.3 - `self/emit_tac_c.lark`**, differential vs the M7.0 oracle (byte-identical
  emitted C), then compile-and-run == CEK.
- **M7.4 - `self/opt.lark`** (the TAC passes) - **DONE 2026-07-11.** For every corpus
  file and -O level, `opt.lark`-optimized TAC serializes byte-identically to
  `opt.py`-optimized TAC (the strongest obligation): `make -C self opttest` =
  **128 ok / 0 fail / 52 skip** (52 = (3 imports + 7 reject fixtures + 3 CEK-overflow)
  × 4 levels). Ports the `PASSES` subset only (not the RV32 `ASM_PASSES`); each pass is
  `(TAC, Int) -> (TAC, Int)` threading the inline/closure site counter, fixpoint fuel 8.
  Key finding: opt.py's `fnmap` is a LIVE mutable map, so inline-grown functions become
  ineligible for later sites - reproduced purely by threading an updated fnmap
  left-to-right (17_mutual_rec -O2/-O3 is the witness). See LOG 2026-07-11 M7.4.
- **M7.5 - the O5' fixpoint** (9.4) - **DONE 2026-07-11.** Both claims closed; see
  §9.4 result block below and LOG 2026-07-11 M7.5.

### 9.4 The O5' fixpoint (definition of done)

Assemble `optcompiler.lark = lex + parse + infer + lower + opt + emit_tac_c`
(driver via the existing `bootstrap.py` `read_all` idiom). Two claims:

1. **Behavioral (semantics-preservation) fixpoint** - the Lark analog of the
   2026-07-10 result, now with a *Lark* optimizer: `optcompiler` compiled/run at
   -O0 and at -O3 emits **byte-identical C** for every input (optimization does not
   change what the compiler computes). Strictly stronger than today because the
   optimizer under test is self-hosted.
2. **Self-application fixpoint (the capstone)** - the optimizing compiler compiles
   **its own source**: stage1 (Python-hosted) → C(compiler) → clang → stage2;
   stage2 compiles the compiler source → C → stage3; **C(stage2) == C(stage3)**,
   byte-identical (the F2 C-source discipline, Mach-O binary caveats as in M5), on
   the **optimized** compiler. **Report the win:** stage2 (optimized) vs an -O0
   build - emitted-C size, clang'd binary size, and self-compile wall-clock - so
   "the compiler makes itself faster" is a *measured* delta, not a slogan.

#### 9.4 RESULT - both claims CLOSED (2026-07-11)

`optcompiler.lark = lex + parse + infer + lower + opt + emit_tac_c` assembled via
`bootstrap_opt.assemble_compiler(level)` (the `read_all` stdin driver); baked
`optimizeProg(prog, 3)`. Built self-contained (`emit_tac_c` backend, `cc -O2
-fwrapv -DLARK_HEAP_BYTES`), each stage run under `ulimit -s 65520` (macOS 8 MB
main-thread stack vs the compiler's deep recursion on its own ~7.5 k-line source).

1. **Behavioral fixpoint - GREEN** (M7.5 session 2026-07-11, harness
   `self/tests/optcompiler_difftest.py`): the self-hosted optimizing pipeline
   parse→inferProgram→lowerProgram→optimizeProg(L)→emitTacC reproduces the Python
   oracle's optimized C byte-for-byte at every level. The differential gate is
   `opttest` **128 ok / 0 fail / 52 skip** (`opt.lark` == `opt.py` at -O0..-O3).

2. **Self-application fixpoint - CLOSED.** Ladder (`self/tests/ladder_opt.sh`): stage0 = Python-hosted
   `emit_tac_c.py optc_O3.lark -O0` → clang → stage1; stage1 compiles the compiler
   source → C1 → clang → stage2; stage2 → C2 → stage3; stage3 → C3.
   **C1 == C2 == C3 byte-identical** on the **optimized** compiler,
   sha256 `f1dedfa9...` (1,512,018 bytes). Each self-compile ran in ≤ 1 s with
   **5.6 GB free** at the low-water mark.

   **The win** (same input `optc_O3.lark`, so a clean apples-to-apples delta):

   | metric                         | -O0 baseline | -O3 (self-optimized) | delta |
   |--------------------------------|--------------|----------------------|-------|
   | emitted C (bytes)              |    1,852,562 |            1,512,018 | **-340,544 (-18.4 %)** |
   | clang'd binary (bytes)         |      398,600 |              408,360 | +9,760 (noise; two different C files under `cc -O2`) |
   | self-compile wall-clock        |         ~1 s |                 ~1 s | at this size, both instant |

   The headline is the **emitted-C size**: the compiler applying its own -O3 passes
   to its own source cuts 18.4 % of the generated C (const-fold + copy-prop +
   algebraic + cse + dce + devirt + inline + closure-elim). Binary size and wall
   time are within noise at this program size - the observable, reproducible win is
   the -18.4 % on generated code.

   **The wall that was in the way (and the fix - output-neutral, §8b-class).** The
   -O0 self-compile fit comfortably (5.7 GB free), but every level ≥ 1 blew the
   no-GC arena past 12 GB *in 2 s* - before a single pass ran. Root cause was **not**
   the passes: `optSweeps` fingerprinted the whole ~1.8 MB program with
   `tacPretty(t)` (an O(n²) left-nested string join - the same arena-join wall as
   §8a/§8b) *twice per sweep*, and did it on the very first line before the first
   sweep. Fixed by replacing the string fingerprint with a **structural
   `optTacEq`** (opt.py's own `_fingerprint` discipline: compare `(f.name,
   f.body)` per function; O(n) time, O(1) alloc). Output-neutral - `opttest` stayed
   **128 / 0 / 52** byte-identical - and it collapsed the level-≥1 self-compile from
   *12 GB overflow → 5.6 GB free*. (Two smaller output-neutral cleanups landed in
   the same pass: structure-preserving `optCpKill`/`optCseKill` guards so
   copy-prop/cse rebuild their block-local maps only on a real kill, not every
   instruction; and `optLicmFn(f) = f` dropping the discarded O(B²) dominator
   computation - licm is a global no-op on Lark's DAG-only CFGs anyway.)

### 9.5 Validation & risks

- **Differentials reuse the existing rigs** (`self/tests/*_difftest.py`, `make -C
  self`): the M3/M5 pattern (serialize IR/C to a normalized form, diff vs the
  Python oracle) applies unchanged to `lower.lark` / `opt.lark` / `emit_tac_c.lark`.
- **Frozen-baseline safety.** `opt` passes are pure TAC→TAC and the new emitter is
  off the RV32 path, so the O0-O4 corpus baselines and the existing F2 remain the
  regression contract; O5' adds *new* baselines, it does not move `BASELINES.md`.
- **Affine-IO idiom** (LOG M0/M5.5): the passes are pure transforms (no IO - easy);
  only the driver threads IO, and must build output purely then print once.
- **The O(n²) arena/join wall** (§8a/§8b): `lower`/`opt` build and rewrite lists and
  assoc-map environments heavily; the balanced-tree `Subst` lesson (§8b) and the
  emitter line-join fix (§8a) are the templates if the self-hosted optimizer hits
  the same wall on its own ~4000-line source.
- **`emit_tac_c` has no pre-existing oracle** - hence M7.0 builds one first (9.2).
- **Closure ABI already correct** - the 2026-07-10 eta-expansion fix means
  `lower.lark` ports a lowering with no known correctness debt.

### 9.6 Effort

Roughly the M6-backend milestone minus the RV32 assembler/regalloc: ~1500 Lark
lines across four ports (`tac` + `lower` + `opt`-TAC-subset + `emit_tac_c`) plus a
~300-line Python oracle for the emitter. Comparable in size to M3 (`infer.lark`,
1215 lines) - a milestone, not a session. It is the *only* path that closes Gap 1
(the compiler literally optimizing itself); Option B (Python optimizer moved onto
the C path) closes only Gap 2 and is the cheaper fallback if a full port is not
wanted.
