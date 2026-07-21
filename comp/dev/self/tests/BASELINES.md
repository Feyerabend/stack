
## Frozen baselines — self-hosting at F2⁺

Pinned reference values for the self-hosted Lark toolchain at the freeze point.
Any OPTIMIZE (or later) change must keep every differential green and every
*output-neutral* artifact byte-identical. If a number here moves, either a real
regression happened or the change is genuinely output-changing (then update this
file in the same commit, with the reason).

Regenerate all with `make -C self <target>`; each is meta-circular (slow), so run
__one at a time__ (siblings share fixed temp-driver filenames).

### Differential test counts

| target          | result           | what it proves                                              |
|-----------------|------------------|-------------------------------------------------------------|
| `lextest`       | __57 ok / 0 fail / 0 skip__ | `lex.lark` == `lexer.py` (token streams, incl. line/col). Pinned 2026-07-12 at `LARK_TIMEOUT=900` — before that these two had __no row here at all__ and had been running unwatched. The corpus is 45 (`07/tests` + `07/samples`) + 12 (the compiler's own source), so it __grows with the compiler__. It swept 104 files until 2026-07-12: `corpus()` used `rglob` over `self/`, which pulled in `self/vendor/`'s byte-identical *second copy* of the corpus and the harnesses' own scratch drivers. `opt.lark` alone is 1,770 lines — the whole run is tens of minutes. |
| `parsetest`     | __57 ok / 0 fail / 0 skip__ | `parse.lark` == `parser.py` (syntax trees, serialised). Same corpus, same 2026-07-12 pin, same `rglob` bug and fix. |
| `infertest`     | __42 ok / 0 fail / 3 skip__ | `infer.lark` == `infer.py` (Algorithm W + affine + traits); 3 skips = the 3 `import` files (`09_modules/main`, `16_stdlib`, `25_torture`) |
| `cektest`       | __35 ok / 0 fail / 14 skip__ | `cek.lark` == `cek.py` (evaluator). Re-pinned 2026-07-13 (was 34/0/15). The 14 skips are __11 structural__ — `oracle exit 1`: the 9-file error suite, plus `09_modules/shapes.lark` and `Stdlib.lark`, which are import fragments with no `main` — and __3 timing__: `04_tailrec`, `15_tailrec2`, `04_queens` exceed the meta-circular eval budget (`LARK_TIMEOUT`, default __90 s__). Held at 35/0/14 across four runs in two load conditions (two contended, two idle) with a file-for-file identical skip list. Earlier: 33/0/15, then 33/1/15 once `25_torture` (added after the pin) was actually run; the red was the *harness's* import-inlining, not the port, and fixing it made `25_torture` the 34th green. |
| `emittest`      | __38 ok / 0 fail / 7 skip__ | `emit_c.lark` == `emit_c_ast.py` (C from syntactic AST); 7 skips = error suite (no C to compare). Re-pinned 2026-07-12: was 37/0/7, which accounted for only 44 of the 45 corpus files — the pin predates `25_torture` joining the corpus. The 45th file has been passing all along; the pin, not the port, was stale. (Same class of drift as the `cektest` re-pin above: a pin that stops covering the corpus stops being a claim about it.) |
| `typechecktest` | __42 ok / 0 fail / 3 skip__ | the __typechecking__ compiler (F2⁺): accept→oracle-identical C, reject→oracle-identical `type error:`; strictly stronger than emittest (the 7 error-suite skips become live tests); 3 skips = the 3 `import` files |

`typechecktest` dominates `emittest`: same acceptance C __plus__ the reject
diagnostics. It is the load-bearing freeze witness.

#### O5′/M7 self-hosting the *optimizing* backend

These port the optimizing-path oracles (`lower.py`, `emit_tac_c.py`) and are
differential-tested by feeding the __same__ oracle-produced TAC to both sides
(the front end + lowerer are trusted; only the ported module runs in Lark).
`lowertest`/`emittactest` feed the __unoptimized__ TAC to both sides (isolating the
lowerer/emitter); `opttest` (M7.4, landed 2026-07-11) is the pass that puts the
optimizer itself on the differential — both sides run `opt.optimize` at every level
before the comparison.

| target        | result           | what it proves                                              |
|---------------|------------------|-------------------------------------------------------------|
| `lowertest`   | __35 ok / 0 fail / 10 skip__ | `lower.lark` == `lower.py` (typed AST → TAC); TAC byte-identical incl. 09_parser; 10 skips = 3 imports + 7 reject fixtures |
| `emittactest` | __32 ok / 0 fail / 13 skip__ | `emit_tac_c.lark` == `emit_tac_c.py` (TAC → C, optimizing backend path); C byte-identical incl. 08_life 867 lines; 13 skips = 3 imports + 7 reject fixtures + 3 CEK-overflow on deep serialised TAC (24_stringprims, 05_expr, 09_parser) |
| `opttest`     | __128 ok / 0 fail / 52 skip__ | `opt.lark` == `opt.py` (TAC → TAC passes) — optimized TAC byte-identical at __every__ level -O0..-O3, incl. 17_mutual_rec's live-fnmap inline eligibility; 52 skips = (3 imports + 7 reject fixtures + 3 CEK-overflow [24_stringprims, 05_expr, 09_parser]) × 4 levels |
| `optcompilertest` | __140 ok / 0 fail / 40 skip__ (35/0/10 per level) | the __whole optimizing pipeline__, self-hosted: all 9 modules concatenated (`lex`→`emit_tac_c`) compile each file and must reproduce the oracle's optimized C byte-for-byte at __every__ level -O0..-O3. Strictly stronger than `lowertest`/`emittactest`/`opttest`, which each isolate one stage. 40 skips = (3 imports + 7 reject fixtures) × 4 levels — __no timeout skips__ |

#### F3 self-hosting the *RISC-V* backend

The same TAC, a second backend. `lex → parse → infer → lower → opt` is unchanged;
where `emit_tac_c.lark` writes C, `asm.lark` writes RV32I for the RP2350. Both
harnesses feed the oracle's __unoptimized__ TAC to both sides, isolating the stage
under test, exactly as `lowertest`/`emittactest` do.

| target         | result           | what it proves                                              |
|----------------|------------------|-------------------------------------------------------------|
| `regalloctest` | __32 ok / 0 fail / 13 skip__ | `regalloc.lark` == `regalloc.py` (linear scan, Poletto & Sarkar) — every register and spill slot identical, incl. 09_parser; reuses `opt.lark`'s CFG + liveness rather than re-porting them. 13 skips = the `emittactest` shape (3 imports + 7 reject fixtures + 3 CEK-overflow on deep serialised TAC) |
| `asmtest`      | __32 ok / 0 fail / 13 skip__ | `asm.lark` == `asm.py` (TAC → RV32I assembly text) — byte-identical `.S`, every immediate, label, section directive and column of mnemonic padding, incl. 08_life 1,645 lines. Same 13 skips |

__The oracle was not a function, and had to be made one first.__ `regalloc.py`'s
`_compute_intervals` iterated __frozensets__ (`live_in`, `live_out`, `defs`, `uses`),
so the interval table's insertion order — which is the tiebreak of the *stable* sort
in the scan, hence which `Tmp` wins which register — was a function of
`PYTHONHASHSEED`. __`asm.py` emitted different assembly on every run__: 10 of the 45
corpus files varied, and `09_parser` produced 5 distinct outputs in 5 runs. There was
no byte-identity for either row above to be a claim *about*. All four iterations are
now `sorted()`; the port mirrors that with `raSortedNames`. `make -C 07 difftest`
(34 passed — CEK ≡ TAC-C ≡ RV32 emulator) confirms the re-allocated code still *runs*
correctly, and all three frozen fixpoints re-confirmed unchanged. __If either row
starts flapping, suspect a reintroduced set iteration before suspecting the port.__

A differential that has never been run cannot flap either — which is how this sat
undetected: nothing downstream of `asm.py` compared two runs of it.

#### The native RV32 cross-compiler (`self/tests/rv32c.py`)

`asmtest` runs the port meta-circularly, so the three deepest programs overflow
CPython's stack and are skipped — and two of them (`05_expr`, `09_parser`) are among
the nine with prebuilt firmware. Compiled to a __native binary__ (the ten Lark modules
`lex…opt+regalloc+asm`, 8,003 lines, built through the O5′ ladder's stage0 path), the
same compiler runs them without complaint:

| check                                  | result | what it proves |
|----------------------------------------|--------|----------------|
| `rv32c.py --check`                     | __9 ok / 0 fail__ | the self-hosted compiler's `.S` == `asm.py`'s on all nine samples, incl. `09_parser` (3,180 lines of RV32I) — the three `asmtest` skips, cashed in |
| `firmware_difftest.py` claim 1½        | __9/9__ | that assembly, executed on the RV32 emulator, prints what `cek.py` prints. `make -C 07 difftest` sweeps `07/tests` only, so __not one of the nine flashable programs had ever been run as RV32__ |
| `firmware_difftest.py` claim 2         | __9/9__ | the GNU RISC-V toolchain (pico-sdk) turns it into nine `.uf2`; both pipelines yield byte-identical images |
| `firmware_difftest.py --board` claim 3 | __9 ok / 0 fail__ | __REAL SILICON, 2026-07-13.__ Flashed to a Pico 2/2W, each image prints over USB-CDC exactly what `cek.py` prints — `09_parser` included. The register allocator, frame layout and tail-call loop survive a real Hazard3 core |

__Claim 3 is closed, and `07/firmware/` now holds the nine hardware-verified images__ — the
exact bytes that were flashed. sha256 (first 12): `01_mergesort 9bb1dc6b1897` ·
`02_bst a32ae55267be` · `03_primes 43c482e98ca0` · `04_queens 5f5fda9487cc` ·
`05_expr 22520abb5c98` · `06_rle 250455d6210e` · `07_hanoi 5354233ce529` ·
`08_life 9f93c28bb7a9` · `09_parser c80e9260d60a`. The __previous__ nine could not be
matched — they predate the canonicalisation above and are the output of one unrecoverable
hash seed. They are replaced, not reproduced.

⚠ __Re-running `--board` requires a board, and its capture loop has one trap, paid for in a
whole debugging session (2026-07-13):__ opening the port asserts DTR, which releases the
firmware's `while (!stdio_usb_connected())` wait, and it prints *microseconds later*.
Python's `tty.setraw()` defaults to __`TCSAFLUSH` — discard pending input__ — so the
transcript arrives and is thrown away by the next line, and the board looks dead. Set raw
mode by hand with __`TCSANOW`__. (`screen` never flushes on open, which is why it always
worked and made this look like a hardware fault.)

__Newly pinned, 2026-07-12 — and a warning about what its absence cost.__
`optcompilertest` is the strongest differential in the tree. Until today it had __no row
here and no `make` target__: `tests/optcompiler_difftest.py` existed, and nothing ran it.
When it was finally run end-to-end it came back __115 ok / 25 fail / 40 skip__ — 25
failures that had been sitting in it, unnoticed, for as long as it had existed. A
differential with nothing pinned is not a test; it is a script that prints a number
nobody reads.

All 25 were defects in the __harness__, not the compiler — the same lesson as
`25_torture`, learned twice in one week:

- __`opt._SITE` is a global counter.__ `opt.py`'s inline and closure passes stamp an id
  on each rewrite site from a module-level `itertools.count()`, so it kept climbing from
  one corpus file to the next, while the port (a fresh subprocess per file) always starts
  at zero. From roughly the second file onward the two sides wrote different site ids into
  otherwise identical C. This produced the whole -O2/-O3 cluster (23 of the 25) and wore
  the costume of a real bug: `08_traits -O2` __passed when run alone and failed inside the
  sweep__. `oracle_at` now resets `_SITE` per call, as `opt_difftest.py` already did — which
  also makes the verdict independent of how the run is grouped.
- __`_anon_<id()>`.__ For a wildcard parameter `_`, `infer.py` invents a name from a CPython
  `id()` — a memory address — and bakes it into the emitted C. No port can reproduce an
  address; the port keeps `_`. Both sides are now canonicalised, as `emit_c_difftest.py`
  already did.

Both had already been solved in sibling harnesses. This one never inherited the fixes,
because nothing was checking it.

### F2 emit-only fixpoint (the bootstrap)

`make -C self bootstrap` — the emit-only compiler (`lex + parse + emit_c`,
1858 lines) reproduces its own emitted C.

| artifact                     | sha (first 8) | note                                              |
|------------------------------|---------------|---------------------------------------------------|
| C1 == C2 == C3               | `49a4921c`    | emitted-C fixpoint, byte-identical across 3 stages |
| stage2 binary == stage3      | *(not pinned)* | Mach-O `LC_UUID` + embedded paths are nondeterministic; only the C-source fixpoint is asserted |

__Re-pin note (2026-07-08, OPTIMIZE §8 join fix):__ the C sha moved
`2ce6a281 → 49a4921c` *intentionally* (BASELINES invariant #2). `self/emit_c.lark`'s
`ecJoinNL` was changed from an O(n²) right-fold to a balanced bottom-up pairwise
join (`ecJoinPairs`) — output-identical (string concat is associative), verified
by `emittest` 37/0/7 and `typechecktest` 42/0/2 staying byte-identical. But the
compiler's *own source* now contains that new code, so the C it emits for itself
differs, and the ladder settles at a new fixpoint. The __arena requirement
collapsed__: the emit-only self-compile peaks at __177 MB__ (was ~3 GB) and the
fixpoint closes at a __512 MB__ arena (was 8 GB reserved). `bootstrap.py` still
defaults to a large arena; pass `LARK_ARENA_SIZE` to run it small.

### F2⁺ native fixpoint of the *typechecking* compiler (M5.5.4)

`make -C self bootstrap-tc` (`self/tests/bootstrap_tc.py`) — the full six-module
typechecking compiler (`lex + parse + types + tast + infer + emit_c` + `tcGate`,
3562 lines) type-checks __its own source__ and reproduces its own emitted C.

| artifact        | sha (first 8) | note                                                      |
|-----------------|---------------|-----------------------------------------------------------|
| C1 == C2 == C3  | `829410dc`    | emitted-C fixpoint (19415 lines), byte-identical across 3 native stages |

__Re-pin note (stale pin — found by actually running the target):__ the sha
moved `45c1982a → 829410dc` (18877 → 19415 C lines; assembled source 3562 → 3718 lines)
because `self/infer.lark` changed on 2026-07-11 (commit `1badfd5`), *after* the previous
pin was taken. Ordinary consequence, already described by the re-pin notes below: the
compiler's __own source__ is an input to the self-compile, so changing it moves the sha of
the C it emits for itself. Not a regression — the oracle-based differentials (`infertest`
__42/0/3__, `typechecktest` __42/0/3__, which compare against the unchanged Python
`infer.py` and not against the self-compile) stayed byte-identical. The fixpoint still
closes: C1 == C2 == C3.

The lesson mirrors `optcompilertest`'s above. That number was never written down; this one
was written down and left to rot for three days while the source moved underneath it. __A
pin that is never re-checked is indistinguishable from a pin that is wrong__ — and costs
more, because it still looks like a guarantee. Re-run `make bootstrap-tc` whenever any of
the six modules it assembles changes.

__How it closed (OPTIMIZE §8b):__ the join fix (§8a) was only the
first wall. With it, parse+emit of the 3534-line source is 353 MB, but adding the
`infer` pass (the gated `tcGate`) overflowed the no-GC arena past __12 GB__ —
Algorithm W's assoc-list `Subst` applied O(n) times and never freed. __Fix:__
`self/types.lark` `applyScheme` now short-circuits when the scheme is *closed*
(`monoVarsAllIn(body, qs)` — every var bound by the quantifier list), returning it
unchanged instead of `apply(removeKeys(s,qs), body)`. Applying a substitution to a
closed (fully-generalised, top-level) scheme is provably the identity, so this is
__output-neutral__ — `infertest` __42/0/2__ and `typechecktest` __42/0/2__ stayed
byte-identical. It removed the env-side O(env × |s|) multiplier that `applyEnv`
paid at every sub-expression: the tc self-compile went from __>12 GB overflow →
10.15 GB completing high-water__, closing the fixpoint (ran at a 14 GiB
lazily-committed arena for headroom; peak touched ~10.15 GB).

__Residual CLOSED (balanced-tree `Subst`):__ the §8b fix left a
subst-side multiplier — `substGet`/`apply` scanned the assoc-list `Subst` linearly,
and Algorithm W allocates fresh vars monotonically, so the list degraded to a chain
on exactly the keys unification looks up hardest (~O(n^1.9)). `self/types.lark`'s
`Subst` is now an __Int-keyed Okasaki red-black tree__ (`type Subst = SLeaf | SNode
of SColor, Subst, Int, Mono, Subst`): `substGet` is O(log n), `subInsert` rebalances,
and `compose`/`removeKeys` fold through `subInsert` (overriding on shared keys, so the
tree caps at distinct-key count instead of accumulating duplicate assoc entries).
__Output-neutral__ — apply reads only the key→Mono mapping, so `infertest` __42/0/3__
and `typechecktest` __42/0/3__ stayed byte-identical against the oracle. Effect: the
tc self-compile peak dropped __10.15 GB → 4.73 GB__ (stage1, 58 s wall; measured
`/usr/bin/time -l ./stage1 < tc_compiler.lark`).

__Re-pin note (balanced-tree `Subst`):__ the bootstrap-tc emitted-C sha
moved `34a07692 → 45c1982a` (18549 → 18877 lines) *intentionally*, exactly as the
§8a join fix did: the compiler's __own source__ now contains the red-black-tree code,
so the C it emits for itself differs and the ladder settles at a new fixpoint
(C1==C2==C3 byte-identical). Not a regression — the oracle-based differentials
(`infertest`/`typechecktest`, which compare against the unchanged Python `infer.py`,
not the self-compile) stayed byte-identical, proving the change is output-neutral.

### O5′ optimizing self-application fixpoint (M7.5 / OPTIMIZE §9.4)

`self/tests/ladder_opt.sh` — the __optimizing__ compiler
(`optcompiler.lark = lex + parse + infer + lower + opt + emit_tac_c`, assembled by
`self/tests/bootstrap_opt.assemble_compiler(3)`, ~7.5 k lines, baked
`optimizeProg(prog, 3)`) compiles __its own source__ to a fixpoint. Built
self-contained (`emit_tac_c` backend, `cc -O2 -fwrapv -DLARK_HEAP_BYTES=12G`), each
stage under `ulimit -s 65520`.

| artifact       | sha (first 8) | note                  |
|----------------|---------------|-----------------------|
| C1 == C2 == C3 | `8f9596d9`    | -O3-optimized emitted C, 1,519,608 bytes, 7,688 lines of Lark, byte-identical across 3 self-compiling stages |

__Re-pin note (2026-07-13, polymorphic-recursion repair — BASELINES invariant #2).__
The sha moved `f1dedfa9 → 8f9596d9` *intentionally*, and the C grew 1,512,018 →
1,519,608 bytes. `infer.lark` and `types.lark` __are compiler source__: they are two
of the six modules `assemble_compiler` concatenates, so any edit to them necessarily
changes the C the compiler emits for itself. __The invariant is not the sha — it is
the closure.__ `C1 == C2 == C3` still holds byte-identically, which is the claim.

The change: `check_fn_decl` was binding a function's recursive occurrence to a bare
monotype var, *discarding the type Pass 1.5 had already computed from its
signature* — so a fully annotated polymorphic function that recurses on its own
result could not be typed. And because `compose` ran no occurs check while `apply`
chases var chains, the symptom was a __hang__, not a rejection (`compose` spliced
`a5 |-> a16` and `a16 |-> a5` into the self-binding `a5 |-> a5`). Fixed in
`07/src/{infer,ty}.py` __and__ `self/{infer,types}.lark` together:

- a full signature now licenses polymorphic recursion (bind the *generalised*
  annotated scheme) — __the fix__;
- `compose` / `subComposeRange` drops a composed binding `k |-> k` — sound and total
  (it *is* the identity map), and it is why the symptom was a loop — __the guard__.

__Output-neutral on the corpus, with both implementations changed__ — which is the
only reason it is allowed at all. All seven differentials returned to their pinned
values: `infertest` 42/0/3 · `typechecktest` 42/0/3 · `cektest` 35/0/14 · `emittest`
38/0/7 · `lowertest` 35/0/10 · `emittactest` 32/0/13 · `opttest` 128/0/52. Every
accepted program still emits byte-identical C and every rejected one still produces
a byte-identical `type error:` (that is `typechecktest`, and it is the load-bearing
witness). `make -C 07 test` also went __81 passed / 0 failed__ — the long-standing
`24_stringprims` red was a stale *embedded expectation* (3 missing `float_to_bits`
lines), never a compiler fault.

The three monomorphic workarounds this bug forced — `ecRev`, `etcRev`, `lwPair` —
were __deliberately left in place__: they are compiler source, un-pinning them would
move this sha again for no benefit, and they are the evidence. See `ORACLE.md`
(class C3) for the full ledger of what has been done to the "frozen" oracle.

__The win__ (same input, `optc_O3.lark`): emitted C __1,852,562 (-O0) → 1,512,018
(-O3)__ bytes = __−18.4 %__; clang'd binary 398,600 → 408,360 (noise); self-compile
~1 s either way. The reproducible headline is the −18.4 % on generated code.

__How it closed (structural fixpoint fingerprint — output-neutral).__ Level-≥1
self-compile blew the no-GC arena past 12 GB in 2 s — *before any pass ran*.
`self/opt.lark`'s `optSweeps` fingerprinted the whole ~1.8 MB program with
`tacPretty(t)` (O(n²) join, the §8a/§8b arena wall) twice per sweep. __Fix:__
replaced it with a structural `optTacEq` mirroring opt.py's `_fingerprint`
(compare `(f.name, f.body)` per function; O(n)/O(1)-alloc). Level-≥1 self-compile
went __12 GB overflow → 5.6 GB free__. Output-neutral: `opttest` stayed
__128 / 0 / 52__ byte-identical vs the `opt.py` oracle. (Same pass: structure-
preserving `optCpKill`/`optCseKill` guards + `optLicmFn(f)=f`, both also
output-neutral — licm is a no-op on Lark's DAG-only CFGs.)

### O0 RV32I metric baseline (the OPTIMIZE ruler)

`python3 07/tests/optbench.py --levels 0 --save 07/tests/optbench_O0.json` — the
measurement rig (OPTIMIZE.md §6). Per corpus file × `-O` level it records static
asm-instruction count, assembled binary bytes, executed RV32I instructions, stub
calls, and heap allocs/bytes (via `riscv_vm.py` counters), plus compile/run
wall-clock and the program-output sha. Full per-file numbers live in
`07/tests/optbench_O0.json`; the corpus totals at the current (un-optimized) code
generator:

| level | files ok | asm_instrs | bin_bytes | dyn_instrs | stub_calls | heap_allocs | heap_bytes |
|-------|----------|------------|-----------|------------|------------|-------------|------------|
| `-O0` | 25       | 8106       | 37656     | 22553695   | 527        | 361         | 3760       |

#### Optimization-level progression (corpus totals — the OPTIMIZE regression contract)

Each `-O`n reproduces every file's `-O0` program-output sha (checked by
`optbench.py --levels 0,1,2,3,4`); only the metric numbers move. `-O0` stays the
identity, so `optbench_O0.json` is *not* re-pinned. Achieved totals (2026-07-09):

| level | asm_instrs | bin_bytes | dyn_instrs | stub_calls | heap_allocs | heap_bytes | headline |
|-------|------------|-----------|------------|------------|-------------|------------|----------|
| `-O0` | 8106       | 37656     | 22553695   | 527        | 361         | 3760       | ruler (identity) |
| `-O1` | 7817       | 36496     | 22552605   | 526        | 360         | 3756       | Tier-1 scalar |
| `-O2` | 6726       | 32096     | 22551647   | 526        | 360         | 3756       | devirt+inline |
| `-O3` | 6526       | 31272     | 22551347   | 520        | 354         | 3708       | closure_elim (heap) |
| `-O4` | 4443       | 22940     | 10828342   | 520        | 354         | 3708       | peephole + coloring + immfold + branchlayout |

O4 has four backend items, all observably ==-O0 across all 25 files:

__Increment 1 — post-gen `peephole`__ (opt.ASM_PASSES): windowed t-register copy-prop
/ dead-scratch elimination / result coalescing on the emitted asm, plus self-move and
fall-through-jump removal. It removes the scratch round-trips instruction selection
leaves in every fragment — the largest __executed-instruction__ cut of any tier
(22.55M → 14.04M, −38%; the hot recursive loops shed their per-iteration moves).
Peephole-only totals (regalloc_color OFF): asm __5199__, bin __25964__, dyn 14036245.

__Increment 2 — graph-coloring register allocation__ (`src/coloring.py`, Chaitin-Briggs
iterated register coalescing; the `regalloc_color` codegen flag in `LEVELS[4]`, selected
in `asm.gen(allocator=…)` — linear scan stays the O0..O3/diff_test default). It coalesces
move-related temps (so cross-block `mv sX, sY` copies the peephole can't reach collapse
to self-moves and vanish) and packs into fewer callee-saved registers (smaller
prologue/epilogue save area). Attributed by toggling the flag: corpus asm __5199 → 4683__
(−516), bin __25964 → 23900__ (−2064); dyn barely moves (14036245 → 14032752 — coalescing
removes *static* setup moves, and 04_tailrec's 13M-instr hot loop dominates the dynamic
count). Allocation is __deterministic__ across `PYTHONHASHSEED` (min-element worklist
selection) and passes `regalloc.verify` on every function (no interfering temps share a
register). heap/stub unchanged (a pure backend tier). Peephole+coloring totals: asm
__4683__, bin __23900__, dyn 14032752.

__Increment 3 — Tier-4 remainder__ (two post-gen asm passes in `opt.ASM_PASSES`, run after
`peephole`): __`immfold`__ = immediate-form instruction selection — a constant the
generator materialises with a separate `li tX, C` feeding a reg-reg ALU op is folded into
the immediate form (`add`→`addi`, `sub C`→`addi -C`, `and`/`or`/`xor`→`andi`/`ori`/`xori`,
`slt`→`slti`, `mul` by 2^k→`slli k`), removing the `li` (the dead-scratch cleanup reuses
`_opt_window`); floats are excluded (a float-bits `li` is comment-tagged and float
arithmetic lowers to runtime calls, never a reg-reg ALU op). __`branchlayout`__ = invert a
conditional branch whose target is the fall-through block — `bnez tX, TRUE; j FALSE;
TRUE:` becomes `beqz tX, FALSE; TRUE:`, deleting the taken jump (complements the peephole's
fall-through-jump removal, which handles the FALSE-is-fall-through case). Attributed by
toggling: asm __4683 → 4443__ (immfold −123, branchlayout −117); bin __23900 → 22940__;
dyn __14032752 → 10828342__ (−23% — folding the per-iteration `li` out of hot loops).
heap/stub unchanged. Idempotent, deterministic across `PYTHONHASHSEED`, no residual
self-moves.

- The __program-output sha per file__ is the observable-equivalence contract:
  every future `-O`n build must reproduce each file's `-O0` sha (asm/bin/instr
  counts change by design; *output* must not). `optbench.py --levels 0,1` checks
  this automatically.
- __25/25__ acceptance files run on RV32. `24_stringprims.lark` was previously a
  codegen crash (`PC misaligned` — six string-decomposition prims missing from the
  RV32 backend); __fixed 2026-07-08__ (self-contained, *before* any optimization
  pass): `string_index`/`string_slice`/`char_to_string`/`float_to_bits` lower to
  plain runtime stubs, and `string_to_int`/`string_to_float` lower to a raw-parse
  stub returning a `[flag, payload]` pair that `lower._lower_string_to_result`
  wraps in `Ok`/`Err` (so tag ids come from `asm._collect_tags` in lock-step with
  user `Ok`/`Err`). All three backends (CEK, TAC interpreter, RV32) agree
  byte-identically — `diff_test.py` __33/0__ at the time. The `+24` bin_bytes on
  every file vs the pre-fix baseline is the six new `ebreak` stub-table entries
  (6 × 4 B) in the shared preamble; program output is unchanged.
- `25_torture.lark` (added 2026-07-09, OPTIMIZE §8d item [2]) is the __deep
  equivalence witness__ for O1: one program wiring together recursive/nested ADTs,
  closures, higher-order map/fold/filter, trait dispatch, Stdlib+Option, the
  string-decomposition prims + `Ok`/`Err` lowering, int + float32 arithmetic, and
  algebraic-identity-shaped expressions. At __2544 asm instrs / 160 heap allocs__
  it is ~half the rest of the corpus's asm and ~80 % of its heap allocs in a single
  file — a much sharper O0-vs-O1 guard than any single feature test. All three
  backends agree byte-identically (`diff_test` now __34/0__).
- `04_tailrec` (sum_to 1M) dominates run-time (~34 s of pure-Python VM); the rig
  drives each file in a subprocess under `--timeout` so a runaway never wedges the
  sweep.

### Invariants for OPTIMIZE

1. All five differential counts above stay exactly as written (or improve skips→ok).
2. `bootstrap` emitted-C sha stays `49a4921c` and `bootstrap-tc` stays `829410dc`
   __unless__ the change intentionally alters emitted C — in which case re-pin here
   with the new sha and the reason. Note that editing *any* of the modules the
   self-compile assembles counts as intentionally altering emitted C: the compiler's
   own source is one of its inputs. Re-run the target rather than assuming.
3. The reject diagnostics stay oracle-identical (that is what makes it a compiler).
4. Every corpus file's RV32 __program-output sha__ (in `optbench_O0.json`) is
   preserved at every `-O` level (observable-equivalence, OPTIMIZE §2/§6). The
   asm/binary/instruction/heap numbers are *expected* to move — that is the point;
   re-run `optbench --compare optbench_O0.json` to see the deltas a pass bought.
5. The O5′ optimizing self-application fixpoint sha stays `8f9596d9` (C1==C2==C3 on
   the baked-`-O3` `optcompiler.lark`) __unless__ a change intentionally alters the
   compiler's own emitted C — then re-pin here with the new sha and the reason (the
   §8a/§8b re-pin discipline: the compiler's own source changed, so its self-emit
   settles at a new fixpoint; oracle differentials must stay byte-identical).
