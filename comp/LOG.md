
## Lark - Self-Hosting & Optimization Work Log

**This is the running record of work on `SELFHOST.md`, `OPTIMIZE.md`, `PROVE.md`,
and the book (`book/`).** The plans say *what to do*; this log says *what has been
done*. Keep them in sync.

## How to use this log

- Append an entry every working session, newest at the top of "Log entries" below.
- Record: date, milestone/rung, what changed (files), what was verified
  (tests/diffs), and what's next. Link commits if any.
- Write each story ONCE, in its dated entry. The pointers in "Current position"
  and "Recent sessions" point at those entries; they do not retell them. If a
  session is not worth a dated entry, it is not worth a pointer either.
- After a /clear: read "Current position", skim the newest dated entries, open the
  active plan's ledger (PROVE.md / SELFHOST.md / OPTIMIZE.md / book/PLAN.md), and
  remember to append here when you stop.

## Current position (2026-07-20)

Active axis: the book endgame. Wave E (mechanical book-scale hardening) is in
progress -- the tic budget is swept book-wide, checkpaths.py is hardened to scan the
now 0-stub book, and a whole-book index (137 keys, 172 locators) is in. What remains
of Wave E is the serial voice/flow readback (foreword-first), then figure polish and
the deferred comment-vs-code code pass.

The three engineering axes are complete and frozen:

- SELFHOST -> F2+ : the type-checking compiler reproduces its own emitted C
  byte-identically. See SELFHOST.md.
- OPTIMIZE -> O5' : the optimizer runs on the compiler itself. See OPTIMIZE.md.
- PROVE -> V3 summit + the three strands (denot, solver, vdeep), plus the affine
  and fixpoint rungs. See PROVE.md.

Book Parts I, II, III are written; Wave D (front/back matter) is done and the book
is 0-stub.

## Recent sessions (newest first)

Pointers into "Log entries" below -- the full story of each lives there.

- 2026-07-20  book: Wave E started -- tic sweep, checkpaths hardened, whole-book index
- 2026-07-20  repo: folder/README repair pass (slice 1) -- scrap/, hygiene, READMEs
- 2026-07-20  book: Wave D complete -- front/back matter written, book is 0-stub
- 2026-07-20  repo: folder reconciliation, steps 1-5 complete (dev/ + repo/ + root Makefile)
- 2026-07-20  book: Wave C -- ch08..ch12 + interlude2, Part II closed
- 2026-07-18  book: Waves A/B -- ch05-07, ch13-18, interludes; + STRAND-AFFINE, STRAND-FIXPOINT
- 2026-07-17  PROVE: V3 summit reached; DESCEND closed as a boundary; strands denot/solver/vdeep
- 2026-07-16  PROVE: V3 spine -> fundamental lemma -> sigma-fusion pile; RUNG(1)/(2)
- 2026-07-15  PROVE: V2.4 refinement work -- equality seam, float interlude, min/max fork planned
- 2026-07-14  PROVE: V1'/V2/V2.1/V2.2(x4)/V2.3, then H (hardening) and I (invariants)
- 2026-07-13  PROVE V1 + Step 0; RISC-V F3.1-F3.3; book ch01-04; the oracle ledger
- 2026-07-12  repo: the reader tree (repo/) split from the codebase
- 2026-07-11  M7.4; book/repo wired; oracle thaw #3
- 2026-07-10  M7.0-M7.3 self-hosted optimizing path; O5 self-optimizing fixpoint
- 2026-07-09  OPTIMIZE O1-O4 passes
- 2026-07-08  SELFHOST F2/F2+ fixpoint, hardening, M3/M5
- 2026-07-07  M0-M4 lexer/parser/types/evaluator ports; project kickoff

---

## Log entries (newest first)

### 2026-07-20 - book: Wave E started (mechanical book-scale hardening)

book, **Wave E started - the mechanical book-scale hardening passes.** Set
said "we go for wave E next." Wave E is the endgame (PLAN.md "Endgame"): mechanical passes first, the serial
voice/flow readback last. Done this slice: **(1) tic budget swept book-wide.** The forbidden set
(`exactly - precisely - honest - honestly - structural - the whole`) went 48 → 10 across all chapters,
concentrated in the earliest-written ch01-ch04 (ch04 alone was 16). Cut or varied ~38; the surviving 10 are
deliberate keeps, each load-bearing or term-of-art: "whole program" (the compilation term), affine "exactly
once" (×2), the fixpoint's `C1=C2=C3` "exactly the same way", literal "whole number(s)", the honesty-theme line
in ch01, and two rhetorical "what, exactly / that is the whole trade" emphases. Substitutions favoured
`entire/all/just/genuine/faithful/truthful/candid/conservative/to the bit/that very` per context; watched for
tic-for-tic swaps (caught one: "exactly"→"precisely" in ch01, refixed to "to the bit"). **(2) `checkpaths.py`
HARDENED - endgame step 1.** Dropped the stub exemption: the lint stripped `\begin{stub}...\end{stub}` before
scanning, on the theory that stubs are author notes citing our tree freely; the book is now 0-stub, so the
whole file is scanned and "no private path or phase-number reaches the public book" is machine-checked. A dev
path smuggled back inside a future stub now fails the build. Docstring + failure message + the `STUB` regex
removed accordingly. **(3) WHOLE-BOOK INDEX - Set asked "how about indexing the whole book? it is pretty
thick right now?" and chose "Comprehensive + subentries" (matching the sibling Language Stack book's ~265).**
The index was effectively dead past ch11 (only 26 keys, all in ch01-05/ch11); now it spans **every chapter,
front/back matter, and all four appendices**. Placed ~110 `\index{}` markers → **172 locators over 137 unique
keys** (`main.idx`). Covers: Part II optimization terms (three-address code, basic block, constant folding,
CSE, copy propagation, dead-code elimination, liveness, control-flow graph, inlining, devirtualization,
dispatch stub, closure elimination, LICM, back-edge, register allocation, linear-scan, graph colouring,
coalescing, spilling, live interval, peephole, lambda lifting, free variables, currying, tagged word, arena,
intermediate representation); Part III proof terms (Martin-Lof type theory, propositions as types, Pi/Sigma
type, bidirectional checking, NbE, de Bruijn, neutral value, trusted kernel/base, HoTT, univalence, identity
type, progress, preservation, type soundness, substitution lemma, call-by-value, well-typed by construction,
verified compiler, decision procedure, specification, refinement type + subentries, measure + subentries,
logical relation, false proof, adversarial testing, ...); plus front-matter locators (differential testing,
oracle, purely functional, affine types) and people (Thompson, Chaitin). Uses mkidx.py's full syntax:
**subentry families** (`measure!ghost`, `refinement type!precondition/postcondition/erasure`, `trait!bounds`),
**see-refs** (7: adversary→adversarial testing, IR→intermediate representation, TAC→three-address code,
HoTT→homotopy type theory, LICM→loop-invariant code motion, Curry-Howard→propositions as types,
ghost function→measure), and **multi-locator merges** (`affine types, 4, 21, 37, 157`; `CEK machine, 45, 93`).
**Verified:** `make book` green through the 3-pass mkidx pipeline; `main.ind` renders all 137 keys, 8 subitems,
7 see-refs; PDF 3.44 MB. **Verified:** `checkpaths` green (every citation resolves in repo/), `checkrefs` green
(211 \ref, no typed numerals), root `make check` green (repo in sync 310 files). The cover-into-main.pdf fold
(item 8 in the 12th entry below) was the first Wave E mechanical piece. **NEXT (Set to steer):** the serial
**voice/flow readback**, foreword-first, chapter by chapter (Set reading back between, per the per-session
protocol); then any figure/diagram polish. The deferred **comment-vs-code** code pass still stands after.

### 2026-07-20 - repo: folder/README repair pass (slice 1)

repo hygiene, **folder/README repair pass - SLICE 1.** Set asked to (a)
repair per-folder READMEs to describe each folder + what its code does, (b) park unused docs/code in a `scrap/`
folder rather than delete, and (c) noted a later comment-vs-code pass ("near time", NOT started). Done this
slice: **(1) `scrap/` created** with a `README.md` (what-and-why, everything here safe to delete, nothing
generates from it) + **`NOTE.md` parked there** (`git mv` - it was the original kickoff brainstorm, every goal
since done + written up in AIMS/STRUCTURE/PLAN, named only pre-move paths; its one live reference is a
historical LOG line, so nothing broke). **(2) `__pycache__` cleanup** - 8 stray dirs removed (2 had leaked into
`repo/*/oracle`, the artifact Set flagged); `.gitignore` gained `__pycache__/`, `*.pyc`, `.DS_Store` (none were
tracked - pure hygiene so they never leak into a commit). **(3) top-level `README.md` REWRITTEN** - it was
badly stale (described a `01/`-`07/` phase layout deleted in the reconciliation); now an honest map of the
working repo: `book/ repo/ dev/ tools/ scrap/ build/` + the plan/log docs, a `dev/` breakdown (07 frozen oracle,
08 refinement fork, self Lark port, prove 75 fixtures, formal/proof metatheory), a `repo/` = generated-reader-tree
note, and the root `make` targets. **(4) dev-tree README gaps filled:** wrote `dev/self/README.md` (was missing -
the self-hosted compiler modules front-end+optimizer, the one-rule differential-not-edit, tests/ + bootstrap,
`make` targets) and `dev/formal/README.md` (was missing - thin pointer into `proof/`). **(5) `dev/prove/README.md`
fixed:** its runnable command `make -C 08 prove` (broken by the dev/ move) → `make -C dev/08 prove`, and its
`../PROVE.md` link → `../../PROVE.md` (both broke when prove/ became dev/prove/). **Verified:** `make check`
green (repo in sync 310 files, both book lints pass); `make -C dev/08 prove` → 75 ok/0 fail (confirms
`SUITE=ROOT.parent/"prove"` still resolves, siblings moved together); every new/edited README relative link
resolves on disk. **(6) dev/07 + dev/08 README touch-up DONE (same session):** `dev/07/README.md` needed
nothing - it is a self-contained frozen snapshot, every link relative to its own subdirs (firmware/, runtime/),
no parent refs. `dev/08/README.md` had two move-breakages fixed: the header link `../PROVE.md` → `../../PROVE.md`,
and the whole "## The checks" command block `make -C 08 <t>` → `make -C dev/08 <t>` (all 11 targets verified to
exist in dev/08/Makefile; `make -C dev/08 prove` runs 75 ok). Left alone deliberately: the README's `07`/`08`
tree-name vocabulary in prose and in comments (`# 08/src == 07/src`), and the bare inline-code `PROVE.md §`
section pointers (not markdown links, so not broken). **(7) book/ + tools/ READMEs written (same session):**
both folders had NO README. `book/README.md` - what the book is (companion to no.4, PDF-only, cites repo/ only),
`make book/cover/all/clean` + the three-pass index, the layout (main.tex / 28 chapters / cover / references.bib /
PLAN.md / tools/), the two lints (checkpaths = prose cites reader paths only, checkrefs = \ref not numerals) +
mkidx, and 0-stub status. `tools/README.md` - the two-tree machinery: mkrepo.py (verbatim/rewrite/KEEP-repo-only
derivation + `--check` drift guard + pin/jargon checks) and oracle_drift.sh (frozen-oracle ledger vs pristine,
read against ORACLE.md), noting the book's own lints live in book/tools/ not here. All links verified on disk;
28-chapter and 13-harness/3-fixpoint claims sourced from mkrepo docstring + dev/08 README. **DECISION:** per-subfolder
READMEs inside the `repo/` strands are NOT needed - the strand READMEs (repo/self 200+ lines, optimize 123,
prove 143) already document `oracle/`/`lark/`/`harness/` with per-file tables; adding sub-READMEs would only
duplicate them. `make check` still green throughout. Nothing committed. **(8) cover folded into main.pdf (same session):**
`main.tex` now `\includepdf[pages=1,fitpaper=true]{cover.pdf}` right after `\begin{document}` (new `pdfpages`
package); `book/Makefile` makes `main.pdf` depend on `cover.pdf` so one `make book` builds the cover first and
emits a single 186-page main.pdf carrying it as page 1. No external PDF-merge tool - the join is inside tectonic,
and because only the static cover is `\includepdf`'d (the book compiles natively) the TOC/index/hyperlinks stay
live. Page-1 render confirmed = the cover; both lints green. `make cover` still builds the standalone cover.
**NEXT (Set to steer):** Book **Wave E** = serial readback (voice/flow). The deferred **comment-vs-code** pass
(the "near time" item) still stands after.

### 2026-07-20 - book: Wave D COMPLETE -- the book is 0-stub

book, **Wave D COMPLETE - the book is now 0-stub.** Wrote all six
front/back-matter pieces from scratch (appendix_oracle was already done): `foreword.tex` (names the companion
*The Language Stack* no.~4 as a bridge-not-gate, the three independent strands, the honest-AI-cooperation
paragraph, "working document, PDF only"); `introduction.tex` (the two-methods framing = differential then
adversarial co-billed up front; "Lark in two pages" showing `self/samples/03_primes.lark` whole and walking it;
the three orthogonal questions; how to use the companion repo); `conclusion.tex` (three answers, each fenced by
a named boundary - ℤ-vs-32bit, partial correctness, equality seam, trusted verifier "work goes next, has
begun"; + the Thompson trust question and diverse-double-compiling defense); `appendix_lark.tex` (language
reference: syntax EBNF, HM types + affine/Copy, full built-in table, "what Lark does not have" with reasons);
`appendix_method.tex` (the harness manual: per-stage differentials in `self/harness` + `optimize/harness`, the
three adversarial harnesses in `prove/harness`, watched-to-fail protocol, reading `N ok/M fail/K skip`,
BASELINES.md invariant-vs-environment split, `make bootstrap`/`make fixpoint` → hash `8f9596d9`); `appendix_repo.tex`
(map of the three trees + "deliberate duplication" = reader-over-byte-count). Grounded in REAL data (grammar.ebnf,
infer.py built-ins, the actual repo tree + Makefile targets, real BASELINES numbers) - the stale stub notes
(curation gap, 5-harness list, `08/tests`) were obsolete post-reconciliation and dropped. **DoD met:** reader-facing
paths only (checkpaths caught 3 false-positive slashes - operators `+ - * /`, remainder `n - n / d * d`, output
`N ok / M fail / K skip` - refiled as `\lstinline` = code, not paths); tics swept (fixed 11 across the 6 files,
kept only "whole program" as term-of-art); cross-refs via `\ref`. **`make book` green** (checkpaths + checkrefs
clean, main.pdf 551 KB). PLAN.md ledger flipped 6 lines STUB→DONE, status header → "0 stub blocks." Nothing
committed. **NEXT:** the folder/README repair pass Set named (per-folder README docs, more code comments; note
the `__pycache__` dirs leaking into `repo/*/oracle` as a mkrepo artifact) - then book Wave E (serial readback).

### 2026-07-20 - repo: folder reconciliation, steps 1-5 COMPLETE

Set flagged the ambiguous folder layout (repo/{self,optimize,prove} vs the
dev-tree self/ prove/ formal/proof/, plus 07/ 08/). Diagnosed as a designed
two-layer system and reconciled stepwise; analysis and target recorded in
STRUCTURE.md. The four sessions below, oldest step first:

**Step 1.**

repo structure, **folder reconciliation STEP 1 DONE (safe regen).**
Set flagged the ambiguous folders (`repo/{self,optimize,prove}` vs dev-tree `self/ prove/ formal/proof/`,
plus `07/ 08/`). Diagnosed as a designed **two-layer** system, not chaos: dev tree ("by history": `07/`
frozen oracle, `08/` refinement fork, `self/` Lark port, `prove/` 75 fixtures, `formal/proof/` lcore
metatheory) → **generated** reader tree `repo/{self,optimize,prove}/` via `tools/mkrepo.py` (`make repo`;
`--check` guards drift). Wrote the full analysis + agreed target to **`stack/lark/STRUCTURE.md`** (three
problems: (A) `repo/` stale, (B) prove strand HALF-BUILT - mkrepo ships only the metatheory, not the
`08/src` checker / 75 `prove/` fixtures / `08/tests` adversary, so ch16/17/18 have NO runnable reader code;
(C) top-level name collision). Decisions taken with Set: group the dev tangle under `dev/`; plan first,
execute stepwise. **STEP 1 executed now:** `python3 tools/mkrepo.py` regen - 7 drifted proof files fixed,
incl. **`lark-refine.lcore` (V3-FUND summit, 68 KB) that was MISSING from `repo/`** entirely. After:
`--check` clean (205 files, pins agree); `make paths` + `make refs` green (every prose citation resolves,
184 refs OK). Nothing committed. **NEXT (per STRUCTURE.md): step 2 = build out the prove strand in
`mkrepo.py` (biggest gap); step 3 = `git mv 07 08 self prove formal dev/` + rebase the ~4 hardcoded path
sites; step 4 = root Makefile; step 5 = verify.** Book work (Wave D) is unblocked and orthogonal.

**Step 2.**

repo structure, **folder reconciliation STEP 2 DONE - the prove
strand is built out.** Problem (B) from STRUCTURE.md was the real one: `mkrepo.py` shipped `repo/prove/`
the *metatheory only* (`lark-formal/`, `lcore/`) - ch16/17/18 are DONE in prose but the reader got **no
runnable refinement code**. Fixed by extending the generator: `repo/prove/` now also ships **`oracle/`**
(the `08/src` refinement checker - `refine.py`, `solver.py`, `pred.py` + the compiler it rides), **`fixtures/`**
(the 75 safe/unsafe `*.lark`, verdicts pinned), and **`harness/`** (`prove_difftest.py`, `adversary.py`,
`solver_fuzz.py`). New machinery in `tools/mkrepo.py`: `rewrite_prove()` path-rewrites (`08/src`→`oracle`,
`prove/`→`fixtures/`, `make -C 08`→`make`, drop the `# .../lark/08` ROOT-locator) with a guard that FAILS
the build on any surviving `07/`/`08/`; a `dejargon()` pass (per Set's "trim the version chatter" call)
that strips dev-milestone jargon (V-tags, PROVE.md refs, step/Part labels, `SELFHOST`/`OPTIMIZE`) from
copied prose - masking real `§` citations (Appel/Muchnick/Pierce) and solver.py's own section banners - and
raises if any survives; and a `_codeshape()` token guard proving **only comments/docstrings changed, never
code** (caught one real corruption mid-work: a version token that ate a sentence period + newline merged a
dataclass field into a comment - fixed by bounding the token + horizontal-only whitespace). Also rewrote the
two hand-written KEEP files (`repo/prove/README.md`, `Makefile`) from their stale "no code yet / chapters
13-16" state to describe all five folders + `make prove/adversary/solver/selftest/proofs/test`, with an
honest-boundaries section (compiler unverified, formal Lark is a model, checker trusted, partial correctness,
ℤ-vs-32bit). **Verified:** `mkrepo.py --check` clean (310 files, pins agree); in `repo/prove/`, `make prove`
→ **75 ok, 0 fail**, `make adversary` → clean, `make solver` → sound; book lints green (`make paths`/`make
refs`, 184 refs OK). Nothing committed. **NEXT (per STRUCTURE.md): step 3 = `git mv 07 08 self prove formal
dev/` + rebase the hardcoded path sites (mkrepo ROOT constants, `oracle_drift.sh` SRC=, `make -C` refs,
`checkpaths.py` bans); step 4 = root Makefile; step 5 = verify end-to-end.** Separate Wave-E follow-up: ch16/
17/18 prose still cites only `prove/lark-formal/` - can now cite the runnable `prove/{oracle,fixtures,harness}`.

**Step 3.**

repo structure, **folder reconciliation STEP 3 DONE - the dev tangle
is under `dev/`** (+ the step-2 chapter-citation follow-up). `git mv 07 08 self prove formal dev/`, so the
top level is now just `book/ repo/ dev/ tools/` (+ build/, docs). Rebased every hardcoded path: `mkrepo.py`
got `DEV = ROOT/"dev"` and all dev-tree *reads* moved onto it (the path-*rewrite* regex strings - `07/src`→
`oracle` etc. - left alone, they describe the reader tree, not disk); regen after the move is **byte-identical
(310 files, 0 updated)**, proving only source *location* changed. `oracle_drift.sh` now spans the rename
(both `stack/lark/07/src` and `stack/lark/dev/07/src` pathspecs, widened prefix-strip sed) - verified its
added/modified lists still print right. `checkpaths.py` kept its bans and added `08/`+`dev/` so the public
book can never name a dev path. No `make -C`/absolute refs inside the moved dev Makefiles (siblings moved
together → relative paths preserved), so the dev tree is self-contained. **Step-2 follow-up also done:** ch16
now cites `prove/oracle/` (the checker) + `prove/fixtures/` (the 75-program corpus), ch17 cites
`prove/harness/adversary.py` - the runnable code those chapters describe, which before this had no path at
all. `torture.py` stays a bare filename (deliberately not in the curated 3-file harness, so no slashed path
to resolve). **Verified end-to-end:** `mkrepo.py --check` clean; `make -C repo/prove prove` → 75 ok/0 fail;
`make -C dev/formal/proof check` → 5 files/0 errors; book `make` green (checkpaths + checkrefs + tectonic,
main.pdf written); new citations resolve in `repo/`; no new tics. Nothing committed. **NEXT (per STRUCTURE.md):
step 4 = root `Makefile` (`make repo`/`make check`/`make book`); step 5 = final end-to-end verify.**

**Steps 4 & 5.**

repo structure, **folder reconciliation COMPLETE - steps 4 & 5 done,
the whole plan is closed.** Step 4: wrote the top-level `stack/lark/Makefile` (`help` default). `make repo`
regenerates the reader tree; `make check` runs `mkrepo.py --check` + the two book lints and fails on any
drift / dead-path / typed numeral (verified exit 0 clean); `make drift` prints the informational frozen-oracle
audit; `make book` delegates to `book/` (which runs its own lints then tectonic); plus `make prove`
(→ 75 ok), `make formal` (→ 5 files/0 errors), `make test` (= check + prove + formal). Step 5 (final verify):
`make repo` byte-identical (310 files, 0 updated), `make check` green, book `make` green, `make -C
dev/formal/proof check` green, and the dangling-path grep is clean - every remaining `07/`/`08/` in tooling
is a rewrite-rule pattern, a GUARD string-literal that *detects* stray dev paths in generated output, the
rename-spanning drift sed, or a comment describing the rewrite; none is a live dev-tree read. **The top level
is now `book/ repo/ dev/ tools/` + the root Makefile + the plan/log docs; STRUCTURE.md status = COMPLETE.**
Nothing committed (root Makefile is untracked, awaiting Set's commit). **Folder reconciliation is DONE end to
end (steps 1-5).** The remaining Lark work is book Wave D/E (front/back matter + hardening), orthogonal to this.

### 2026-07-20 - book: interlude2 "The Quadratic Wall" DONE - **WAVE C COMPLETE, Part II closed.**

STUB (1 stub, 95 words) → DONE (0 stubs, 1355 words). The last piece of Part II. Written as the
book's engineering conscience per the stub's brief. **With this, Parts I, II, III are all done; only
Wave D (front/back matter) + Wave E (hardening) remain.**

CORRECTED the stub's framing (as flagged in the ch12 entry): the stub said "twice... interning string
literals" as the second instance. Reality is RICHER and I told it straight - the append-is-a-copy
quadratic bit THREE distinct subsystems, each authored knowing the last:
1. **§8a emitter line-join** - `l + "\n" + join(rest)` re-copies the growing tail; ~3 GB → <200 MB
   via balanced-pairs join. Output-neutral (concat is associative). "Building output strings."
2. **§8b infer substitution** - Algorithm W walked a growing assoc-list `Subst` once per node → two
   braided quadratics (env-side + subst-side); Python hides it behind a `dict`; port overflowed 12 GB;
   fixed by closed-scheme short-circuit + Int-keyed RB-tree Subst (10.15 → 4.73 GB). "Threading a
   substitution." This is the cleanest dict-vs-immutable + side-index story.
3. **M7.5 fixpoint fingerprint** - the sweep loop rendered the whole program to a string ×2/sweep to
   detect "changed?"; structural compare retired it (12 → 5.6 GB). The one ch12 tells.
Dropping "interning" as the named second instance keeps interlude2 consistent with ch12 (whose "second
time" is the fingerprint) and is more honest - the interning was one more face, not THE second.

Structure (interludes use `\section*`, no chapter number): open (the pattern bit >once) → **An append
that is a copy** (O(n) append → O(n²) loop; invisible because Python's list/dict hide it in the oracle)
→ **The three faces** (the three above, in prose) → **The constant that proves it** (leak grows with
LIVE set; quadratic work grows as output²; measured ratio heap÷output² ≈ **0.025** held across a **180×**
span → that constant IS the proof it's quadratic work not a leak; live set linear throughout) → **Does
Lark need a GC?** (NO - nothing leaked, the heap filled with provably-dead corpses; a tracing GC would
cost the determinism the language exists for; the affine discipline of ch:types already knows a value's
last use → deterministic reclamation / in-place reuse, arena reset at phase boundaries, Perceus-style;
"GC made unnecessary" → doorway into Part III).

Refs: `ch:selfopt` (the third face), `ch:types` (affine answer), `part:prove` (Part III doorway) - all
resolve. No dev paths / phase-numbers / internal-symbol names in prose (§8a/§8b/etcJoinNL/optSweeps
etc. stay out; described in plain English). DoD: `make` exit 0, 0 stubs, 0 tics (trimmed 4: `the
whole`×3, `exactly`×1). PLAN.md ledger interlude2 STUB→DONE; header rewritten (Parts I/II/III done,
Waves A/B/C complete), 68→67 stubs.

**NEXT: Wave D - front & back matter.** foreword, introduction (seed both from `../AIMS.md` per PLAN -
lift the thesis, don't re-invent), conclusion, appendix_lark, appendix_method, appendix_repo
(appendix_oracle already DONE). Written last on purpose. Then Wave E (whole-book hardening → public
move; see PLAN "Endgame"). After a /clear doing book work: read this, then `book/PLAN.md` Ledger + Wave.

### 2026-07-20 - book: ch12 "The Optimizer Optimizes Itself" DONE (Wave C, 5th of Part II).

STUB (4 stubs, 92 words) → DONE (0 stubs, 1351 words). The Part II capstone - the two fixpoint
claims of the self-optimizing compiler. Short by design; hands the "why" of the wall to interlude2.

CORRECTED a stale stub framing: the ch12 draft note + the interlude2 stub both said the wall was the
"interning fix" landing at `f1dedfa9`. Per the authoritative M7.5 CLOSE (LOG 2026-07-11), that was the
OLD WRONG GUESS - the real 12 GB blocker was `self/opt.lark`'s sweep loop fingerprinting the whole
~1.8 MB program via `tacPretty(t)` (O(n²) left-nested string join) TWICE per sweep to detect the
fixpoint, *before any pass ran*. Fix = structural `optTacEq` (compare `(f.name, f.body)` per fn, O(n)/
0-alloc); 12 GB → 5.6 GB; output-neutral (`opttest` stayed 128/0/52 byte-identical). Wrote the TRUE
story, not the stub's guess. **interlude2 (next) must be corrected the same way** - its stub still says
"interning string literals"; the real second-occurrence is the pretty-print-to-compare fingerprint.

Sections:
1. **Two claims, not one** - separated (a) the BEHAVIORAL claim (Lark-written optimizer == Python
   reference, byte-for-byte, every level; fails as a *diff* = a faithless pass) from (b) the SELF-
   APPLICATION claim (the optimizing compiler runs on its own 9 modules as a *fixpoint*; fails as a
   *crash / resource cliff*). "First can be green while second is nowhere near."
2. **The first claim, green** - the seam-closing test: earlier differentials fed each module an
   oracle-produced IR in isolation (the "cheat"); `optcompiler_difftest.py` assembles all 9 under one
   `module Selfhost`, runs end-to-end (inferProgram→lower→opt→emit, no Python in the loop), demands
   port==oracle byte-identical every file every level. Cited reader path
   `optimize/harness/optcompiler_difftest.py`. Green (pinned invariant / M7.5 COMPLETE; opttest
   128/0/52). Ran the harness to re-confirm - it's the heaviest meta-circular load, left running in bg.
3. **The second claim, and the wall** - ~7000-line compiler → ~1.5 MB / tens of thousands of lines of
   C; 3-stage ladder C1==C2==C3 byte-identical = the self-application fixpoint; **-18.4%** emitted C at
   the top level vs -O0 ("a fifth less code"). The wall (NOT a bug): 12 GB in ~2 s before any pass, in
   the fixpoint bookkeeping (pretty-print-the-whole-program-to-a-string ×2/sweep = the §8 arena-join
   quadratic). Fix = structural comparison, O(n)/0-alloc, 12 GB→5.6 GB, differential still green.
   Honest scale tail: 5.6 GB is a workstation number, the Pico has 520 KB - wall lowered not removed;
   "second time an append turned out to be a copy" → hands to interlude2.

No exercises (consistent with ch08/ch09/ch10, which have none; only ch11 does in Part II). All numbers
from the M7.5 CLOSE (pinned to `f1dedfa9`), no dev paths/phase-numbers/internal-symbol names in prose.
DoD: `make` exit 0, 0 stubs, 0 tics (trimmed 5: `the whole`×2, `exactly`×1, `precisely`×1). PLAN.md
ledger ch12 STUB→DONE, header 72→68 stubs.

**NEXT in Wave C: interlude2 "The Quadratic Wall" (STUB, 1) - the LAST piece of Part II.** Write it as
the book's engineering conscience (append is O(n) → append-in-a-loop O(n²); the Python oracle hid it
behind dict+mutable-list, the Lark port paid; the constant peak-heap ÷ emitted-bytes² across a 180×
span IS the proof it's quadratic work not a leak; fix = side-index + chunked build; ends on "does Lark
need a GC?" → no, affine types offer better). **CORRECT its second-instance framing** per this entry.
Then Part II is closed and Wave D (front/back matter) or Wave E remains.

### 2026-07-20 - book: ch11 "The Back End" DONE (Wave C, 4th of Part II).

Was POLISH (4 stubs, 1318 words) → DONE (0 stubs, 3123 words). The chapter that was already
strongest at the tail ("The last link" / the silicon-and-instrument sidebar + the four exercises,
all pre-written) got its three body sections and the intro stub written from real output.

Method: emitted verbatim material through a scratch program. `emit_tac_c.py FILE -O1` needs a full
module (`module Sq` header, `fn main(io:IO):IO`), so authored `sq(x)=x*x` + a `print(io,show(sq 6))`
main; `asm.py FILE out.S` produced the RISC-V for the same. Both pasted verbatim.

Sections written:
1. **Opener** - reframed to name the chapter's real spine up front: the string-vs-tag bug that lives
   in the gap between the two backends; "two ways down, the bug is the spine, the backends are the
   shoulders."
2. **TAC to C, again** - WHY a second C emitter beside ch06's. ch06's reads the *syntactic* tree +
   links a runtime; this one (`optimize/oracle/emit_tac_c.py` + port `optimize/lark/emit_tac_c.lark`)
   reads the *flat* optimized IR and is almost a transcription - one TAC instr → one line of C. Real
   `lk_sq` body shown incl. the DEAD second `return (lkw)0;` trap (same belt-and-braces as ch09's
   `__lark_match_fail`), and the `lkw` full-width-word / self-contained-C (no link step) departure.
   Sets up "two independent witnesses to the same meaning, from two intermediate forms."
3. **The real machine, briefly** - kept a SIDEBAR per the stub's own warning. Same `sq` as RISC-V:
   the honest 5-move sequence around one `mul` (`mv s11,a0; mv t0,s11; mv t1,s11; mul t2,t0,t1;
   mv s10,t2; mv a0,s10` - `x*x` reads `s11` twice), vs the human's `mul a0,a0,a0`. Linear scan
   (`optimize/oracle/regalloc.py`, Poletto-Sarkar, 11 callee-saved s-regs, spill-furthest-end) can't
   coalesce → copies survive. Graph colouring (`optimize/oracle/coloring.py`): interference graph, k-
   colour = k-register assignment, coalescing collapses `mv sX,sX` for the peephole to delete;
   Chaitin (NP-complete yet routine, non-adversarial graphs). Framed as the window into what clang
   does silently on the C path; ported in the exercises.
4. **A bug the fixpoint found** - the SPINE. Full story from LOG 2026-07-11 M7.5: `match`-on-ctor and
   string `==` both surface as `t == <const>` in TAC; the TAC→C emitter compiled BOTH as integer tag
   tests → `keyword_kind` in the lexer misclassified every keyword as a name → self-compiled parser
   recursed forever → SIGSEGV in generated `lk_pDecls`. Why differential-vs-interpreter MISSED it (CEK
   does string-eq right; native path only exercised under the optimizing SELF-compile, no corpus prog
   used dynamic string-eq in native code). Found with a C debugger on generated C. Fix = data-flow
   disambiguation: thread the per-fn set of IGetTag-dst temps; compared temp in that set → integer tag
   test, else → string-eq call; applied to BOTH oracle + port. Moral tied to the chapter's ceiling
   theme: differential testing is blind to a fault in a path neither witness travels; the fixpoint is
   the largest test - the one input that uses every construct the compiler is built from, and it was
   lying around free.

DoD: `make` exit 0 (checkpaths + checkrefs + tectonic all pass, main.pdf written); 0 stubs; tics 0
(trimmed 3 added `exactly` + 1 pre-existing `the whole book` in the ported-allocator exercise); all
cited paths resolve reader-facing (`optimize/oracle/{emit_tac_c,regalloc,coloring}.py`,
`optimize/lark/emit_tac_c.lark`). PLAN.md ledger flipped ch11 POLISH→DONE, header 76→72 stubs.

**NEXT in Wave C: ch12_selfopt (STUB, 4) then interlude2 (STUB, 1) - that CLOSES Part II.** Then
Wave D (front/back matter) or Wave E hardening. After a /clear doing book work: read LOG top pointer,
then `book/PLAN.md` Ledger + current Wave.

### 2026-07-20 - book: ch10 "The Passes" DONE (Wave C, 3rd of Part II - the longest chapter).

The TAC optimizer, eight sections, one pass (or pass-pair) each, every before/after verbatim from the oracle.
Method this session: no CLI in `opt.py`, so a throwaway scratch driver imported parser/infer/lower/tac/opt and
printed `tac.pretty(optimize(lower(typecheck(parse(f))), OptOptions(level=n | enable={pass})))`. Small fixtures
authored to isolate each pass; the canonical test-fixture corpus (`tests/08_traits.lark` etc.) used for devirt.

Sections + the real output each is built on:
1. **Constant folding** - `x + (2 + 3*4)`: `t0 = 3*4` → `t0 = 12`, the rest unchanged. Framed as the template
   pass (walk, find an improvable line, replace). HONEST LIMIT surfaced by testing: `2 + t0` does NOT fold -
   `const_fold` is instruction-local and Lark has NO constant propagation (read `copy_prop`: it propagates only
   `IAssign` whose src is a `Tmp`, never a `Const`). Stated plainly; "leaves the last few percent on the table."
2. **Copy prop + CSE** (the stub groups them) - the ch08 flagship `(x+1)*(x+1)` → at O1 `t0=x+1; t2=t0*t0`.
   Three passes separated in prose: cse finds the dup and emits `t1=t0`, copy_prop threads `t1→t0`, dce deletes
   the dead copy. Plus the CSE-over-allocating-prim soundness note (safe ONLY because values immutable +
   equality by-value; from opt.py's CSE_ELIGIBLE tripwire comment).
3. **Dead code elimination** - `let unused = x*x*x in x+1` → `t2 = x+1`. Introduces liveness + CFG "gently,
   needed nowhere else" (the stub's instruction): the one backward fixpoint over the graph; iterates (killing
   t1 exposes t0); guards = never drop a call or a global write.
4. **Inlining** - the enabling pass. `x + sq(4)` with `sq(n)=n*n`: inlined to `4*4`, THEN const-fold reaches in
   → `16`. Honest about the residue (a `dst=v` copy + jump-to-next-line per inline, left for ch11's peephole);
   INLINE_MAX 12, non-recursive only. Note: I tested inline-enables-CSE too (`sq(x)+sq(x)`) but block-local CSE
   can't cross the jump-fragmented blocks - so I chose the const-fold enabling demo, which fires cleanly.
5. **Devirt + closure elim** - `describe(Blue)` → `describe$Color` (devirt recovers the tag→impl map from the
   dispatch STUB's own `tag=='Red'/...` chain; fires because `Blue` is IAlloc'd in the same block). Closure elim:
   `let add = fn(y)=>y+x in add(10)` → `10 + x` scalar-replaced (non-escaping). Callback to ch09's lowering-time
   `show` routing = the static cousin of this runtime-dispatch removal.
6. **LICM - the honesty centrepiece.** Taught from scratch (loop-invariant, back-edge, hoist), then: it is a
   NO-OP on every Lark program. VERIFIED empirically - ran `pass:licm` vs raw on all 9 corpus samples, zero
   changed; confirmed by OPTIMIZE.md ("licm is a global no-op on Lark's DAG-only CFGs"). Reason: a functional
   language repeats via recursion = a call, not a graph cycle; every lowered CFG is acyclic. Kept because
   correct + validated on a synthetic loop. "A pass that is right and does nothing," said so plainly.
7. **Sweeping to a fixpoint** - `twice(inc, x)` (HOF) → at O3 collapses to `x+1+1`: no call to twice, no closure
   for inc, no indirect apply. Traced as one-layer-per-sweep peeling (inline twice → expose closure → elim →
   expose inc applies → inline), `_MAX_SWEEPS=8`, corpus settles in 2-3; the shrink-or-bounded-expand argument
   for why bounding is safe. Scaffolding again deferred to the backend.
8. **Levels** - O0-O4 table. O0 = the ruler (observable-equivalence baseline every level is checked against).
   Two honesties: O3's bundle NAMES unbox/fusion/arena_reuse but they are declared-not-written (in `LEVELS`,
   absent from `PASSES` - verified), so O3 = O2 + closure_elim today; and O4's real speed comes from the
   BACKEND (graph-colouring regalloc + peephole/immfold), not TAC.

**Opener rewritten - a genuine correction.** The stub's inherited claim "code two to ten times faster" is NOT
supported by the data. `harness/BASELINES.md`: O0→O3 static instrs 8106→6526 (~19%), code size 1.85M→1.52M
bytes (-18%); the big DYNAMIC wins are O4-only - regalloc 22.55M→14.04M (-38%), immfold -23%. So the chapter
now says plainly: these passes make code SMALLER (~a fifth), not much faster; the speed is ch11's backend. This
is the DoD "report not fiction / verbatim numbers" rule catching an overclaim before it shipped.

**Source used:** `repo/optimize/oracle/opt.py` (1621 L - read the driver/LEVELS/PASSES + const_fold, copy_prop,
dce, devirt/_extract_dispatch, inline, licm rationale, closure_elim, the CSE_ELIGIBLE tripwire, optimize()
fixpoint), `harness/BASELINES.md` (real numbers), `OPTIMIZE.md` (licm-no-op confirmation). Voice model: ch08/ch09
(immediate predecessors) + ch04 (longest technical). **DoD cleared:** 0 stubs, `make` green (lints + tectonic,
main.pdf 488 KiB), tics clean after a trim (10 hits → 0: exactly/precisely/honest/structural/the-whole varied),
all listings verbatim from real runs, reader-facing refs via `\ref` (ch:ir/ch:lowering/ch:backend), 3,430 words.
**Not committed** (Set commits). Ledger flipped in `book/PLAN.md` (ch10 DONE; header line → 76 stubs / ~28.2k words).

**Next:** finish **ch11 "The Backend"** (currently POLISH, 4 stubs - the RV32I `ASM_PASSES`: peephole, immfold,
branchlayout + graph-colouring regalloc, i.e. exactly the O4 items this chapter forward-referenced; source
`optimize/oracle/` asm.py/regalloc.py/coloring.py/peephole-in-opt.py). Then ch12 selfopt, interlude2.

### 2026-07-20 - book: ch09 "Lowering" DONE (Wave C, 2nd of Part II).

Second chapter of Wave C. ch08 built the flat language and argued for it; ch09 performs the translation
into it. Four sections, each anchored on verbatim TAC pulled from real lowerer runs (small fixtures
authored this session: opt/fl/gi/sh/lam):

1. **From typed tree to flat code.** The lowerer is one recursive walk; every node emits its instructions
   and returns the operand (temp or const) holding its value. Straight-line nodes (binop, literal, let) are
   dull by design - the frame that lets me say the interesting nodes are the value-becomes-control-flow ones.
   `if` was ch08's `abs`; here the sibling case is **pattern matching**, shown as a real lowered ladder for
   `Opt`/`unwrap`: `tag(o)` test → jump-or-fall-through per arm → `o[0]` GetField binds the payload → every
   arm writes the shared `r0` → `.match_end1` returns it. Two honesty beats: the trailing `call
   __lark_match_fail()` is a dead trap the exhaustiveness check already ruled out, emitted anyway
   (belt-and-braces); and `tag(o)` is read twice (`tag4`, `tag8`) - the visible redundancy ch08 promised,
   left for ch10 because the flat form makes it two comparable lines.

2. **Where the types go.** The pass reads the TYPED tree - the FIRST time in the book inference results are
   used for anything but rejection. `describe(n:Int, x:Float, b:Bool)` shows one `show` lowering to three
   runtime functions (`show`/`__show_float`/`__show_bool`) and `+` splitting to `__str_concat`; then `a+b`
   as `t0=a+b` (Int) vs `call __float_add(a,b)` (Float) - identical source, different code, decided by the
   type on the node. Named as **devirtualization**; the match ladder framed as the same economy (a fixed
   constructor set the type pinned).

3. **Lambda lifting.** `adder(n) = fn(x)=>x+n` → lifted `adder$lam0(env,x)` with `cap0=env[0]`, and
   `adder` returns `closure(adder$lam0; n)`. Free-var analysis (n free, x not), the uniform (env,param)
   convention whether or not anything is captured, multi-param currying.

4. **The port, and the bug it found.** The pass threads five things through one recursive call (expr, env,
   read-only tables, the Function being emitted into, the outliving LSt bookkeeping). Writing the Lark port,
   the binop case's natural `Cons(lv, Cons(rv, Nil))` tripped ch04's monomorphic-recursion wall a SECOND
   time; worked around by `lwPair` (operands pinned to concrete `Operand`), TAC byte-unchanged. Full
   diagnosis DEFERRED to ch04 (which already names lwPair as scar #2 of 3, understood only at the third);
   ch09 owns only the local scene - a general idea pinned to one type for no visible reason. Closes on the
   differential: `make lowertest` 35/0.

**Source used:** `repo/optimize/oracle/lower.py` (695 L, read in full), `repo/optimize/lark/lower.lark`
header + `lwPair` (for the five-state framing + the fix), LOG M7.2 entry (2026-07-10) for the port-bug story,
ch04 §monorec-fix for the shared diagnosis I must not re-tell. Voice model: ch08 (immediate predecessor) +
ch04 (long technical). **DoD cleared:** 0 stubs, `make` green (lints + tectonic, main.pdf written), tics
clean after a trim pass (8 hits → 0: whole/exactly/precisely/honest varied or cut), all listings verbatim,
reader-facing refs via `\ref`, 2,210 words. **Not committed** (Set commits). Ledger flipped in `book/PLAN.md`
(ch09 DONE; header measured line updated to 85 stubs / ~24.8k words).

**Next:** ch10 "Passes" (the optimization passes: CSE/const-fold/DCE reading the flat form - source
`optimize/opt.py`, `cfg.py`, `liveness.py`), then finish ch11 backend (POLISH, 4 stubs), ch12 selfopt,
interlude2.

### 2026-07-20 - **BOOK: ch08 "An In-Between Language" DONE - WAVE C STARTED (Part II opener, the IR).**

First chapter of Wave C (Part II, optimization). Part II's job is "the same meaning, faster," and ch08 is
its foundation: the intermediate representation the rest of the part reads, analyses, and rewrites. The
chapter's whole task (per its own stub) is to define *intermediate representation* and *lowering* for a
reader who has met neither word - so it stays a language chapter, not an optimization chapter (passes are
ch10, the full lowering is ch09; boundaries honored).

**Sections, and the real material behind each:**
- *Why a tree resists optimization.* Anchored on `(x+1)*(x+1)`: drew the AST (Mul over two Add nodes) and
  made the argument that the two `Add`s are structurally equal but distinct nodes, and nothing in a tree
  records that - so a tree-walking emitter emits `x+1` twice. Structure is the wrong question to ask a form
  whose questions are "used? already computed? still holds what it held?".
- *Three-address code.* Introduced TAC from nothing. Side-by-side source/TAC using **real lowered output**
  (`fn f(x): t0=x+1 / t1=x+1 / t2=t0*t1 / return t2`) - the redundancy that hid in the tree is now two lines
  with identical RHS, which is exactly why the CSE pass (ch10) is cheap to write. Named the cost honestly:
  TAC is longer and unreadable, "not for people," the disassembled-watch image.
- *Names, temporaries, and blocks.* The branch vocabulary, via **real abs() output** (t0=n<0; cond-jump to
  .then1/.else2; both arms write the SAME temp r4; .end3 returns it) - how an expression-shaped `if` (a
  value) survives flattening into control flow (not a value). Defined basic block. Listed the whole IR
  vocabulary (value kinds + ~13 instruction kinds) at a reader's altitude.
- *The IR is a language too.* It has a printer (every listing in the chapter is that printer's output), and
  it is differential-tested like every other stage - `make lowertest`, 35 ok / 0 fail across the corpus,
  Lark lowerer vs Python. Told the honest port snag: whole-compiler concatenation collided the IR's `Val`
  with the parser's `Val`, so the IR's became `Operand` (a real fact from `lark/tac.lark`'s header).

**Method:** all TAC listings are verbatim from `oracle/lower.py` (and `opt.py` for the CSE teaser, though
the teaser stayed out - it belongs to ch10). Drove them with a 6-line scratch harness (parse→typecheck→
lower→[optimize]→pretty). Source read: `oracle/tac.py` (231-line IR def + pretty-printer), `optimize/README.md`
(the reader-facing map), `harness/BASELINES.md` (the 35/0/10 lowertest count), `lark/tac.lark` (the Val→Operand
story). Voice model: ch06 (the sibling emit chapter).

**DoD cleared:** 0 stubs; 1,947 words; tic grep clean (trimmed 7 → 0: exactly×2, honest×2, the-whole×1, +2);
both lints green (`checkpaths` - every prose path resolves in `repo/`, no dev-tree tokens; `checkrefs` - 146
`\ref` all resolved, no typed numerals); `make` compiles 0 errors, no ch08 layout warnings. Ledger flipped
in `book/PLAN.md` (ch08 STUB→DONE; "measured" date bumped; stub tally 95→90). Not committed (Set commits).

**NEXT (Wave C, in order):** ch09 lowering (typed tree → TAC, node by node; where the types go; lambda
lifting; the port bug), ch10 passes (longest chapter - the 9 rewrites one at a time; CSE pays off here),
finish ch11 backend (POLISH, 4 stubs - real machine code / regalloc), ch12 selfopt (the two fixpoint
claims), interlude2 (the quadratic wall). Source tree: `optimize/`. Long-technical voice: ch04, ch07.

---

### 2026-07-18 - **BOOK: interlude3 "The Equality Seam" DONE → WAVE B COMPLETE (Part III fully written).**

Filled the interlude's one stub (kept its strong pre-written three-worlds opener). An interlude in interlude1's
`\paragraph{}` style, four beats, from the real 29-33 fixtures with verbatim artifacts: **(1) Float - an == that
exists and lies:** NaN breaks reflexivity, so a reflexive logic + a Float = ch17's first false-proof shape;
cure = Floats UNSPEAKABLE, enforced by TWO mechanisms by context - silence where a formula is optional (a Float
field flows untouched, 29_floatfield still catches its Int-divisor mutant), ERROR where mandatory (verbatim
`refinement error: not a predicate in the decidable fragment: (v > 0.0)` from 30_floatpred_reject; `refinement
error: measure 'bx', arm 'B': not expressible...: g` from 32_floatmeasure_reject). **(2) String/function - an ==
that does not exist and is believed:** logic grants `s == s` (must, or congruence is unsound), machine raises
`cannot apply '=='` before any branch → the `if s == s then 0 else div(100,d)` program proves (`ok: 2`) but the
else is dead code proving the division, and the crash preempts it - narrow promise KEPT, but "proved" in a
strictly weaker sense = the seam; function equality is undecidable, nothing to wire. **(3) The vetoed fix:**
routing runtime `==` through the value-eq helper made a function's dead branch live → the tenth false proof
(never shipped, ch17); priced and parked. **(4) The moral:** three worlds (types admit / logic reasons /
machine implements) are three different sets, `==` is where they part; the control (a string guarded through
`string_length` proves AND runs) shows the seam is one OPERATOR not one type; a language property shared with
the frozen oracle, documented not closed. **DoD cleared:** 0 stubs; `make` exits 0 (checkpaths + checkrefs
green: "every citation resolves", "137 \ref ... no typed numerals"); no tics; no dev paths (machine/type-system
named, not cek.py/infer.py); Part ref via `\ref{part:selfhost}`. Voice model interlude1 + ch16/ch17.

**> WAVE B COMPLETE: Part III (ch13-ch18 + interlude3) fully written, 0 stubs. Parts I + III done.**
**NEXT = WAVE C (Part II optimization): ch08 (ir), ch09 (lowering), ch10 (passes), finish ch11 (backend,
POLISH/4 stubs), ch12 (selfopt), interlude2. Source: the optimize work → `optimize/`.** Then Wave D
(front/back matter) + Wave E (hardening → public move). NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch18 "Measures and Trees" DONE + ch16's residual stub closed (Wave B, 5th).**

Polished ch18 to 0 stubs (was POLISH/6) and closed ch16's last stub (was POLISH/1 → DONE); only interlude3
remains in Wave B. **ch18** now runs the full measure arc, each rung from the real fixture and with verbatim
verdicts pulled from live `python3 src/refine.py` runs. Five stub sections filled (two sections -
"Taking the tree apart", "The horizon" - were already written and left intact): **(1) Ghost functions** - a
measure = structurally-recursive fn in the measure table, ghost/erased, a-mention-is-not-a-use as a fact about
where it may live; each equation → an axiom fired only at a known constructor; worked with `len` (10_measure_len,
verbatim `ok: 1`). **(2) A match inside a measure** - the two-deep match (`rdepth`), flatten-to-one-equation-per-
constructor-path firing at CONCRETE subfields, opaque fires nothing (sound silence); declared result `{v|v>=1}`
by nested induction lets a consumer divide by an opaque tree's depth (34_nestedmeasure, verbatim `ok: 6` +
the mutant's `1 of 6`, depth-0 lie caught). **(3) Building a search tree** - `maxv`/`minv`/`bst` as pure
ASSEMBLY (no checker change), builds-direction proved (35_bst, `ok: 1`), the opaque-`bst(t)` limit stated →
sets up the already-written destructing section. **(4) The cost of firing** - blunt all-pairs O(n²)
(29/121/497/2017 for n=3/7/15/31) vs demand-driven O(n log n) balanced (13/33/81/193), degenerate spine
intrinsically-quadratic-but-fast; third instance of the Algorithm-W / hash lesson, DIFFERENCE = profiled
BEFORE acceptance, not after a torture trip. **(5) What stays outside** - the four-boundary ledger
(unbounded-ints-vs-32-bit / partial-correctness / equality-seam / concrete-subfields-one-sidedness). **ch16**:
deleted the "Status of the material: built not designed" author-notes stub, trimmed 3×`exactly` + `whole
stack` (kept "whole numbers" idiom + one thematic "honest"). **DoD cleared both:** 0 stubs; `make` exits 0
(checkpaths + checkrefs green: "every citation resolves", "133 \ref ... no typed numerals"); ch18 tics clean.
**Two lint scars fixed mid-session:** (a) `\texttt{100 / d}` tripped checkpaths (slash read as a path) →
`\lstinline!100 / d!`; (b) `\vlabel`'s FIRST arg is a COLOUR (okgreen/failred), not a label - my
`\vlabel{measlen}{verdict}` → `Undefined color` → fixed to `\vlabel{okgreen}{verdict}` ×3. Voice model ch16.

**NEXT: interlude3 (Part III interlude - the equality seam; 1 stub) → WAVE B COMPLETE.** Then Wave C (Part II
optimization: ch08/09/10, finish ch11, ch12, interlude2). NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch17 "What a Verifier May Not Do" DONE (Wave B, 4th) - the adversary/torture chapter.**

The account of what it cost to make the refinement checker's verdicts mean something. ~1,850 words, all 6
stubs filled; a narrative-of-method chapter, but written from the real harvest and with verbatim verdicts
pulled from live runs of the checker on the regression fixtures. **The spine = the nine false proofs**, framed
up front by the two facts that matter (all nine in the checker's TRANSLATION layer, never the solver; and they
fall into three shapes - believing-what-was-not-established / speaking-about-a-name-that-changed-hands /
never-asking). Five sections after it: **(1) Run what you proved** - `adversary.py` generates random programs,
checks them, and RUNS the proved ones (the world is the court a second implementation can't stand in for);
4-by-hand-then-3-by-machine = the argument for building it early; watched-to-fail as the discipline against a
fuzzer that can't speak a construction. **(2) No answer at all** - `torture.py`, hostile-but-legal on a wall
clock; the budget-that-resets-is-not-a-budget fix; the crash-that-hid-a-cubic (raising the stack limit turned
a mercy-kill into a hang). **(3) The walk nobody writes** - the `hash` quadratic (a term's hash is a tree walk;
O(n) hash inside congruence closure's O(n) loop; 4.3M calls / 40% of a 600-term run; fix = one cached int per
node), tied to ch:types' Algorithm-W cost as the same pattern. **(4) Findings, and their ceiling** - the reframe
(all seven were LUCK; can't tell "none left" from "stopped looking" - the very distinction forced on the checker's
budgets), so `invariants.py` (coverage/asking/work, counting not timing); the EIGHTH false proof found on purpose
(58 unwalked nodes, all lambda bodies; `synth` returned opaque without looking; verbatim `1 of 1 unproved` from
22_lambda_unsafe). **(5) The language it can speak** - the NINTH (a lambda's parameter is a contract discharged
at the call; verbatim from 27_lambdapre_unsafe), the generator going to school on nested measures (→ ch:measures),
and the TENTH that never shipped (the equality-seam fix vetoed by its own nets - a method works when it may veto
the fix to its findings). **DoD cleared:** 0 stubs; reader-facing (scripts cited bare as `adversary.py`/
`torture.py`/`invariants.py` - no slash, so lint-clean and dev-path-free; no `08/`, no `.md`, no `make -C`);
cross-refs all `\ref`, no typed numerals; `make` exits 0 (checkpaths + checkrefs both green: "every citation
resolves", "128 \ref ... no typed numerals"); tics trimmed (the-whole×3 → entire, exactly×2, honestly×1 → clean).
Voice model ch16. Verbatim outputs verified against live `python3 src/refine.py` runs on the prove/ fixtures.

**NEXT: polish ch18 (measures, 6 stubs) + close ch16's residual stub, then interlude3 → Wave B complete.**
Then Wave C (Part II optimization). NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch13 "What ``Correct'' Could Mean" DONE (Wave B, 3rd) - Part III's framing chapter.**

The map for Part III (drawn after the payoff chapters ch14/ch15 were written, so it sizes the word "proved"
accurately). ~1,506 words, all 5 stubs filled; a philosophical/framing chapter, no code to report but built
from the real harvested specimens. Four sections: **(1) Tests, and their ceiling** - differential testing =
indistinguishability from a reference on the inputs tried, NOT correctness; carries the harvest specimen (the
fork's second, compiled runtime sat in no test target, so when the reference interpreter gained two builtins
the compiled one silently didn't - "byte-identical" all suites green because nothing drove those ops down
that path; told WITHOUT dev filenames cek.c/cek.py, as "two evaluators"). Lesson: "a runtime no target
exercises is not covered by the claim - it is hiding behind it." **(2) Three things one might prove** - type
soundness (cheap, language-wide, Lark has it) / verified compiler (meaning preservation, the CompCert-scale
mountain, Lark lacks it, C backend trusted) / program-meets-spec (per-program, refinement at the low end,
dependent types at the high end) - plus the FOURTH the project backed into: the verifier itself is sound,
which splits into three mountains (calculus / decision procedure / the code), only the first chapter-sized;
ch18 does the splitting. **(3) What we have** - type soundness in the strong form, floor-not-ceiling.
**(4) What we do not** - no verified compiler; the tense-fix recorded honestly (specs USED to be "out of
reach," no longer - refinement checker exists, both verdicts exercised); the surviving boundary = no verified
verifier, the handoff to ch17's torture-testing. Close: "A proof does not remove the last thing you must
trust. It moves the trust somewhere smaller, and asks you to look hard at where it went." **DoD cleared:**
0 stubs; reader-facing (no dev paths, no runtime filenames); ALL cross-refs via `\ref` incl. the four Part
refs that first FAILED the build as typed numerals ("Parts~I and~II", "Part~III"×3) → `\ref{part:selfhost}`
/`{part:optimize}`/`{part:prove}`; `make` exits 0; tics trimmed (honest×3, exactly×2 → clean). Voice model
ch16 + this chapter's own strong pre-existing opener.

**NEXT: ch17 adversary (Wave B, 4th) - "what it cost to make the verdicts mean something" (torture-testing
the refinement checker; adversary.py, false-proof hunts).** Then polish ch18 + close ch16 residual stub,
then interlude3. NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch15 "Proving the Language" DONE (Wave B, 2nd of Part III) - the honest metatheory.**

The Part III payoff chapter. Reports the base-language metatheory from the four reader-facing files at
`repo/prove/lark-formal/` (`prove/lark-formal/`): lark-typing / lark-subst / lark-step / lark-preservation,
~1,000 lcore lines. **~2,176 words, all 5 stubs filled.** The hard editorial call was HONESTY vs the bold
opener ("every program... will run without getting stuck. Every one."): the actual development does NOT
mechanise universal progress, so I kept the opener as the *claim under investigation* and made §1 tell the
real story. **Two load-bearing honesty points, straight from the source:**
- **Preservation is INTRINSIC - nothing to prove.** Expressions are encoded well-typed-by-construction
  (`Expr Γ τ` IS a typing derivation), and `Step : Π t. Expr empty t → Expr empty t → Type` carries the
  same `t` on both ends, so a type-changing step is unwritable. "Not a lemma that was proved; a sentence
  that could not be made false." (lark-preservation.lcore lines 18-22 say exactly this.)
- **Universal progress hits an lcore WALL** (matches the V3-DESCEND-WALL finding + lark-step.lcore:34-37):
  a general `indrec Expr` progress proof needs index refinement `g = empty` mid-proof, which lcore cannot
  do. So the development proves progress *constructively for values + each reduction rule* (the NotStuck
  witnesses) and the real general theorem `eval_produces_val : Eval t e v → IsVal t v` (evaluation
  soundness, by indrec Eval). Named the gap between "every term" and "values + rules + eval-soundness"
  rather than papering it.
Four sections: **(1) Progress & preservation** - intuition then the two honesty points above.
**(2) Formalising Lark** - the intrinsic encoding (Ty/Ctx de Bruijn/9 Expr forms 1:1 with inference cases)
and the THREE named seams: monomorphic (HM resolved *before* this layer, W not re-proved), no affine layer
here (separate proof), no ADT/match; step relation mirrors the ch05 CEK machine but IS a re-description,
fidelity argued via correspondence tables not proved. **(3) The proof, in lcore** - the spine: substitution
lemma first (the hard knot = ELam under a binder, resolved by generalising to open contexts + the trusted
kernel `weaken` de-Bruijn-shift primitive), then the 8-rule step relation (4 base + 4 congruence = the CBV
character), Steps closure, big-step Eval, `eval_produces_val` at the top. **(4) What is still trusted** -
the boundary as a 5-item list (model-is-a-fragment / fidelity-argued / runtime-unverified / checker-trusted
incl. the weaken hatch used here / universal-progress-argued-not-mechanised), then the harvest forward arc:
this metatheory is now LOAD-BEARING - the refinement-soundness logical relation (ch18 horizon) is built OVER
this chapter's Steps + Eval; "the strongest thing that can be said of a proof: something heavier was set on
top of it, and it held." **DoD cleared:** 0 stubs; paths reader-facing (`prove/lark-formal/` + bare
filenames); green-bar cited by NAME only (no `make -C`); cross-refs resolve; `make` exits 0; tics grepped
and trimmed HEAVY (10 hits - I leaned on honest/the-whole/exactly - all varied/cut, now clean). Voice
model ch16.

**PARKED IDEA (Set, this session):** lcore / MLTT / the proofs deserve their OWN small booklet - likely
living in or beside the `lcore` directory (a parent-ish home). That booklet is the right place for the deep
type-theory material, which is *why* ch14/ch15 could stay lean and send the curious reader onward rather
than swallow the book. Not started; captured so it survives.

**NEXT: ch13 correctness (Wave B, 3rd) - "What the Machine Can Promise" / well-typed-vs-correct setup**,
then ch17 adversary, polish ch18 + ch16 residual, interlude3. NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch14 "A Proof Checker in C" DONE (Wave B, 1st of Part III).**

First chapter of Wave B (Part III proving). ch14 is the trusted base the metatheory (ch15) will lean on -
and the stub's own warning was "this chapter could swallow the book," so it is deliberately the leanest of
the Part III chapters (~1,840 words, vs ch16's 2,531). **All 5 stubs filled**, written from the real
checker at `repo/prove/lcore/` (reader-facing `prove/lcore/`): term.h's `Term`/`Val` split, check.c's
`infer`/`check`/`conv` trio, the README's own "around 4 000 lines" framing. Four sections:
**(1) Propositions as types** - the identification from scratch (arrow = implies, pair = and, sum = or,
empty+abort = ex falso), no prior exposure assumed. **(2) Dependent types** - "the one idea the previous
book stopped short of": a type may mention a value; `Pi`/`Sigma` = for-all/there-exists; the cost is that
type equality may require *running* the values, which is why the checker needs an evaluator.
**(3) The checker, read** - bidirectional checking (infer vs check, everything else falls to infer+conv),
NbE (de Bruijn indices in `Term` / levels in `Val`, neutrals = stuck computations), the typing rules as one
`switch` in check.c, smallness = "readable in an afternoon, a price a doubter can actually pay"; **names the
two TRUSTED escape hatches** (general fixpoint + context weakening, marked trusted in the source) as the
honest boundary, echoing ch16's read-a-divisor admission. **(4) Why HoTT is here** - identity/J, univalence,
funext, truncation, the circle all present; the ch15 proof uses only Id+J, the nat/bool recursors, and
inductive families (+ universe polymorphism + implicits) and NEVER univalence/HITs - said plainly rather
than left to imply the proof uses all of it. **DoD cleared:** 0 stubs; reader-facing path only
(`prove/lcore/` via `\lstinline`, bare filenames elsewhere); cross-refs `\ref{ch:metatheory}`/`{ch:types}`;
`make` exits 0; tics grepped and trimmed (4× "the whole", 1× "honest" → varied/cut, now clean). Voice model
was ch16. **NEXT: ch15 metatheory (Wave B, 2nd) - the payoff: `fund` soundness-as-total-correctness, green
bar `make -C formal/proof check` but cite it by name only.** NOT committed (Set commits).

### 2026-07-18 - **BOOK: styling pass ported from the printed companion (headings - tables - listings).**

After Wave A, ported three typographic behaviours from the printed *The Language Stack* (Code Crafting no. 4)
so this PDF-only companion reads like it. **(1) Headings don't hyphenate:** new `\headnohyphen` macro
(`\raggedright\hyphenpenalty=10000\exhyphenpenalty=10000`) appended to the format group of the chapter /
section / subsection `\titleformat` in `main.tex`. **(2) Tables don't run into the margin:** converted the
fixed-`p{Ncm}` tables that were overrunning the ~11.5 cm text block to `tabularx` with an `X` (auto-flow)
column - ch01 (`>{\raggedright\arraybackslash}p{3.1cm} X`), ch03 (`p{3.6cm} X`), ch05 (two `lX`), and ch07's
stage ladder (`l l X`). Root cause named: a wide non-wrapping `l` column plus a fixed `p{}` exceeded
textwidth; `X` absorbs the slack. **(3) Listings fit the column with a clean break signal:** measured
capacity (temporarily `breaklines=false` to surface the pt-amount overflows the wrap hides) at ~60 mono
cols; reflowed ~19 source lines across ch02 / ch03 / ch04 to ≤58 cols (split long `match`/`if`/signature
lines, shortened over-long comments) so Part I listings no longer wrap at all. Kept `breaklines=true` and
the gray `$\hookrightarrow$` continuation arrow - per Set, the arrow "shows when it breaks and where to
adjust, and does nothing if everything is ok," so it stays as a where-to-shorten flag rather than being
suppressed. **Green:** `make` in `book/` exits 0; a breaklines-off measurement pass confirms 0 remaining
overfull listings in the DONE chapters (ch01-ch07 + interlude1). Residual overflows left for their own
waves: ch16 L231 (~85 pt), ch18 L147 (~1.3 pt), and the long `\texttt{}` paths inside the still-stubbed
ch08-ch11. NOT committed (Set commits).

### 2026-07-18 - **BOOK: interlude1 "What the Port Taught Us" DONE - WAVE A COMPLETE, Part I fully written.**

Last of Wave A. Turned the stub's five §7 self-hosting findings into short readable entries, each framed as
a design consequence + what one would change (not a bug list): (1) the affine checker SUMS uses across
`match` arms → `io` can't be threaded through a branch (fix: max over arms, not sum); (2) string `==`
missing in one runtime, compared piece-by-piece (fix: write the library fn - "the language is the language
plus its runtime"); (3) monomorphic self-recursion - a fn is one type inside its own body, no polymorphic
recursion (undecidable to infer; fix: allow an annotation to unlock it); (4) `fn` reserved + no
zero-argument function (fix: reserve fewer words, admit empty param list); (5) no `%` operator (fix: add
it). Closing beat: a spec review looks for intentions, the compiler didn't - it pressed every corner with
its weight until the loose ones gave. ~1035 words. Ledger flipped interlude1 STUB→DONE.
**DoD cleared:** `make` green; tic grep 0 (trimmed 4); 0 stubs; no dev paths (only `io`/`fn`/`%`/`match`
in prose, cross-refs to `ch:types`). NOT committed.

**Also this session, per Set's request: a Part-I review pass** - tic sweep + metaphor→explanation check
across the four new chapters (ch05/06/07 + interlude1), keeping the literary style. (Findings in the same
dated entry if any edits followed.)

**WAVE A DONE.** Part I (ch01-ch07 + interlude1) is fully written, 0 stubs. Per `book/PLAN.md` default
order the next wave is **B - Part III (proving): ch14, ch15, ch13, ch17, polish ch18 + ch16 residual,
interlude3** (source: `08/`→`prove/`, `formal/proof/`, ch16 is the voice model). NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch07 "The Ladder, and the Fixpoint" DONE (Wave A, 3rd of 4).** Part I climax - the loop closes.

Third Wave A chapter (`book/PLAN.md` Wave A = complete Part I). **All 5 stubs filled** (the chapter-open
draft-stub + 4 section stubs), ~2233 words, written from the two real harnesses, not invented. Ledger
flipped ch07 STUB→DONE. Sections:
- **Assembling the compiler** - the three built modules (`self/lark/lex.lark`, `parse.lark`, `emit_c.lark`)
  stripped of headers and concatenated under one module + a `read_all`/stdin `main` = **1,858 lines**
  (verified live; the stub's "1,844" was stale - corrected). Honest about the one place the frozen oracle
  was touched: `read_all` added identically on both sides (the compiler's *mouth*, not its logic; the
  differential it guards still holds). Named the real gap: this first loop lexes/parses/emits, does NOT
  type-check - the emitter drives off the syntactic AST, `infer.lark` is not on this path.
- **Stage 0,1,2,3** - the compiled-*by* vs compiled-*from* distinction drawn as a table; source constant
  at every rung, only the compiler varies. stage0 = Python oracle → stage1; stage1→C1→stage2; stage2→C2→
  stage3; stage3→C3. Three identical hashes `49a4921c53b2...`. Why stage 3 and not just stage 2 (first rung
  with no Python in its maker's ancestry).
- **What byte-identical proves** - and does NOT: source fixpoint yes; *binary* no (Mach-O UUID + build
  paths); reproducible-builds digression, stops at the C where the meaning lives.
- **Closing the last gap** - F2⁺: the six-module (`+types/tast/infer`) type-checking compiler behind a
  gate reaches its own fixpoint; **42 programs accepted-or-rejected as the oracle does**, accepts emitting
  byte-identical C, rejects printing the same `type error:` (`typechecktest` 42/0/3 baseline). Scar named:
  self-compiling six modules surfaced the O(n²) join + the arena climb past 12 GB (the ch06 "bill comes
  due" consequences arriving on schedule); both fixed, both verified **output-neutral** (corpus unchanged).
  Closes with the Thompson thread (first stage still trusted, not proved) → interlude.

**DoD cleared:** `make` green (main.pdf written; fixed 3 typed `Part~I`/`Part~II` → `\ref{part:selfhost}`/
`\ref{part:optimize}`); tic grep 0 hits (trimmed 10: exactly/the-whole/honestly varied or cut); 0 stubs;
reader-facing paths only (`self/lark/*.lark`, `self/harness/bootstrap.py`, `bootstrap_tc.py` - all resolve
in `repo/`). **NEXT: interlude1 (Wave A, 4th/last) - closes Wave A / Part I.** NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch06 "Emitting C" DONE (Wave A, 2nd of 4).** + front-matter companion note banked.

Second Wave A chapter, same session as ch05. **All 4 stubs filled**, written from the real emitter
(`self/lark/emit_c.lark` port of `self/oracle/emit_c_ast.py`), ~1491 words (shorter than its neighbours by
nature - the emitter is the simplest compiler stage). Sections: *Why C and not machine code* (C as portable
assembler; what you give up - control/directness - and the forward promise that Part~II emits real RISC-V);
*A tree walk that prints* (one fn per node kind; the no-mutation **threaded `Emit`** = 4 fresh-name counters
+ line buffer; the **byte-identical trick** = allocate the C name pre-order, emit the node's line post-order,
mirroring the Python emitter's order so temporaries match to the byte); *Representing Lark values in C*
(tagged words + the **allocate-and-never-free arena**, named as a decision whose bill comes due in
ch:selfopt); *Byte-identical C* (differential). Opening keeps the honest **syntactic-not-typed** point
(emitter reads the parser's tree, never inferred types - "an accident Part~II undoes").

**Verified.** `make` exit 0 (both lints); the pre-written opening already used `\ref{ch:fixpoint}` so no
ref-lint fixes needed. Tic grep clean (trimmed 6: honest/exactly/the-whole). 0 stubs. **Differential number,
candid again:** stub said "37 programs"; recorded baseline is **`emittest` 38/0/7** (re-pinned 2026-07-12,
was 37 - the pin predated `25_torture` joining the corpus). Prose cites 38 identical / 0 disagreement / 7
error-suite skips, AND keeps the one honest asterisk on "byte for byte": the oracle names wildcard params
from a nondeterministic `id()`, so that single token is canonicalised on both sides before compare (noise in
the reference, not signal in the port). Ledger flipped ch06 STUB→DONE.

**Also this session (Set's note on reading the draft): banked the companion connection into the front-matter
stubs.** The printed book is *The Language Stack* (Code Crafting no.\ 4, published, ISBN'd). Sharpened the
`foreword.tex` + `introduction.tex` stub author-notes (dated) to REQUIRE: name *The Language Stack*
explicitly and point the reader who wants the ground-up build to it; frame it as a **bridge, not a
prerequisite** (the intro's "Lark in two pages" must stand alone for a reader who never saw no.\ 4). Routed
to front matter = Wave D deliberately (framing, not body). Also scrapped the PRESERVE strand earlier today.

**NEXT: ch07 fixpoint (Wave A, 3rd - the loop closes), then interlude1.** NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch05 "The Evaluator, Written in Its Own Language" DONE (Wave A, 1st of 4).**

First chapter of the book's finishing pass (`book/PLAN.md` Wave A = complete Part I: ch05/06/07/interlude1),
picked up right after the AFFINE→FIXPOINT proof-frontier work landed. **All 5 stubs filled**, chapter
written from the real CEK source (`self/lark/cek.lark` port of `self/oracle/cek.py`), ~2327 words (Part I
range). Sections: *Why a machine and not a function* (the CEK idea for a newcomer - an operational
semantics you can hold, and why Part~III's proofs need a stack that is a value); *The three registers*
(C/E/K = control / assoc-list env / `List(Frame)` continuation, with the **hand-trace centrepiece** -
`1 + 2 * 3` walked over ten states, the frame stack growing then collapsing to `7`, faithful to
`stepEval`/`stepRet`); *Closures, traits, and the floating-point detour* (RClosure + currying, RDispatch
trait dispatch, and the honest `string_to_float` / monomorphisation friction); *Reading the world* (the one
effect - the threaded `RIO` token, ordering-as-consequence, the affine tie forward). Framing decision: the
evaluator is **not** on the compiler's fixpoint path - it supplies the *meaning* every later promise
(optimiser-preserves, checker-proves, metatheory-sound) is a promise about; made that its reason for being
in Part I.

**Verified.** `cd book && make` → exit 0 (runs `checkpaths.py` + `checkrefs.py` then tectonic); fixed one
ref-lint (`Part~III` → `Part~\ref{part:prove}`) and one path-lint pass. Tic grep clean (trimmed 6:
exactly/the-whole/honest cluster). 0 stubs. **Differential number handled candidly:** stub said "33"; the
recorded baseline is **`cektest` 35/0/14** (re-pinned 2026-07-13), and a fresh run under load this session
gave **34/0/15** - one more of the slowest programs timed out on the 90 s meta-circular budget. So the
prose does NOT pin a fixed pass count; it rests on the invariant (**0 disagreements, ever**; the compared
count drifts by one with load) and names the skips (error suite / no-`main` imports / slowest-recursive
timeouts). Ledger flipped ch05 STUB→DONE. **NEXT: ch06 emitter (Wave A, 2nd).** NOT committed (Set commits).

### 2026-07-18 - **STRAND-FIXPOINT OK RE-VERIFIED (`49a4921c`) + ARTICULATED: self-application is stable, and stability is not trust.**

Second rung of the AFFINE→FIXPOINT→BOOK sequence. An **exhibition** strand, not a proof - a different
epistemic kind from denot/solver/vdeep/affine (those are kernel-checked; this is **build-verified**). The
property already held; this session **re-ran it, confirmed it, and named its limit**.

**Re-verified green.** `python3 self/tests/bootstrap.py` (the F2 self-hosting ladder: stage0 = the Python
oracle compiles `compiler.lark` to C, then `stage1<compiler.lark→C1`, `stage2→C2`, `stage3→C3`) →
**`FIXPOINT REACHED - C1==C2==C3 byte-identical (49a4921c53b2)`**, 1858-line assembled compiler, ~3 GB
peak, a few minutes. The sha **matches the recorded F2 baseline `49a4921c`** - no drift. The self-hosted
compiler compiles its own source to the same C that a compiler built from that C emits: the ladder is at
its fixed point.

**The harness suffices (DoD 1) - checked before adding anything.** `bootstrap.py` prints the hash on every
run and `return 0 if ok else 1` with a loud `FIXPOINT BROKEN` on drift. It asserts the **fixpoint property**
(C1==C2==C3 self-consistency), NOT equality against a pinned baseline - and that is the right call, not a
gap: the project's standing rule is that an intentional `07/src` edit is *expected* to move the sha and gets
re-confirmed by a human against this LOG. A hard-coded pin would fight that workflow. No new `make fixpoint`
alias added - `make -C self bootstrap` already wraps `bootstrap.py` and is THE documented path (dev tree).
(`make fixpoint` exists only in the generated book repo `repo/optimize/Makefile`.)

**What it IS and is NOT (the whole point - book-ready in `strands/fixpoint/PLAN.md`).** The fixpoint is
**translation validation in the large**: not "the compiler is correct" but "the compiler is a *fixed point
of self-application*" - the build is stable and the binary is **reproducible** (rebuild clean → same bytes).
It does NOT say the binary is *trustworthy*. This is Thompson's *Reflections on Trusting Trust* (1984) made
concrete: a compiler carrying a self-reproducing backdoor is **also** a fixpoint of self-application -
byte-identity is exactly what such a backdoor preserves. So the fixpoint closes the **stability** question
and leaves **trust** wide open; the bootstrap C compiler beneath Lark stays in the TCB - the fixpoint does
not remove it, it *localizes* it. Its place in the book's trust taxonomy: *types say meaningful -
refinements say safe - the metatheory says the calculus is sound - the fixpoint says the build is stable -
and Thompson says stability is not trust.*

**Files touched:** `strands/fixpoint/PLAN.md` (status header → OK re-verified + articulated), `strands/
SUMMARY.md` (fixpoint row → OK), this entry. **No code changed; the main summit is untouched** - `make
-C formal/proof check` still `OK: 5 files, 0 errors`. **Remaining (done when the book reaches it):** feed
ch13/ch15/interlude the Thompson caveat (DoD 4). **NEXT per the sequence: resume the book at Wave A**
(`book/PLAN.md`); the two front-loaded proof-frontier strands (affine spine + fixpoint) are now both
landed. NOT committed (Set commits).

### 2026-07-18 - **STRAND-AFFINE OK M0-M2 SPINE LANDED: `affine_sound` proven, the A in "Lambda Affine Resource Kernel" mechanized.**

First rung of the AFFINE→FIXPOINT→BOOK sequence. New file `formal/proof/strands/affine/lark-affine.lcore`
+ `controls.lcore`; two green bars wired into `formal/proof/Makefile` (`make affine`, `make affine-controls`).
The main summit is **untouched** - `make check` still `OK: 5 files, 0 errors`.

**What landed (M0-M2, the structural spine):**
- **M0** - `Usage` (`avail t` / `spent t`), `LCtx` (de Bruijn spine of slots), `UseVar : LCtx→Ty→LCtx→Type`
  (a variable reference that CONSUMES: `uv_here` demands the front slot be `avail` and flips it `spent`).
- **M1** - `HasA : LCtx→Ty→LCtx→Type`, context-in/context-out: `AVar` consumes, `ALit` passes through,
  `AApp` THREADS left→right (gm between the two halves - a slot spent by the function is gone before the
  argument runs), `ALam` binds a fresh `avail` slot then drops it (final usage `u` may be avail OR spent =
  affine, not linear).
- **M2 - the spine** - `affine_sound : HasA g t g' → Consumed g g'` by `indrec HasA`. `Consumed` is the
  no-double-use invariant: same length, each slot related by `SlotLe` (avail↦avail/spent, spent↦spent, and
  **spent↦avail = Empty** - the one forbidden cell), a spent slot never resurrected. Every rule one line:
  AVar↦`usevar_consumed`, ALit↦`consumed_refl`, AApp↦`consumed_trans`, ALam↦`snd` of the body's consumption.

**Key design decision (ratified before writing, recorded in the file header):** `SlotLe`/`Consumed` are
**FUNCTIONAL recursive predicates** (`indrec ... : Type`, denot's TyD/DEnv house style), NOT inductive
relations - so refl/trans/tail are ordinary structural recursions with **no `Id`, no `J`, no inductive-family
inversion**. App uses **context threading** (subsumes the PLAN's `Split` - no partition relation needed).
The move that carried denot/vdeep - *recurse on structure, build in the target* - carries this too; it never
approaches the DESCEND wall.

**Teeth - 4/4 negative controls refused** (`make affine-controls` → `OK: 4/4`, exactly 8 error lines):
double-use (consume a spent slot), non-consuming var (output keeps avail), resurrection (Consumed spent→avail),
threaded-reuse (share one affine value across both halves of `f x`). **Watched-to-fail:** flipping ctl_double
from the lie (`spent` input) to the truth (`avail`, a legal single use) makes it type-check and drops the
count 8→6 - the refusal IS the affine violation, not incidental noise. Payoff smokes compute: `use_once`
(one var, avail→spent) and `apply_lin` (`f x`, two DISTINCT resources each spent once, threaded).

**One lcore lesson banked:** every `indrec` **case lambda** needs a full Π-annotation (atomic cases like
`Unit` don't); and `SlotLe (avail t) w` stays **stuck on an abstract `w`** (the kernel won't reduce an indrec
whose scrutinee is a variable) - needed a `slotle_avail` helper that cases `w` to hand out the witness. Each
`:let` must be ONE physical line (the Makefile pipe splits on newlines).

**Named boundaries (declared, not discovered):** (a) resource skeleton stands ALONE - not yet indexed by
`Expr Γ τ`; bridging LCtx↔the intrinsic Ctx/Expr (an erasure layer) is the next rung. (b) AFFINE not linear
(ALam doesn't require its binder consumed). (c) STRUCTURAL not operational - M2 proves the discipline
internally sound, not run-time no-reuse (that's M3/M4, needs `Step`, risks DESCEND). **Next: M3 (the IO token
`TIO` consumed once), or move to FIXPOINT per the sequence.** NOT committed (Set commits).

### 2026-07-18 - **BOOK: ch16 "Proving Programs" completed end-to-end (prose amend pass, showcase strand).**

Not a PROVE-axis entry - this is the reader-facing book strand ("Lark Builds Itself", `book/`),
following the ch16 showcase-gallery integration from the prior session. **The ask:** *"amend the book
with more text now that the code has been done."* ch16 had three conceptual stubs left after the gallery
went in; all three now written as real prose, so the chapter is complete from intro to close:
- **§"A type that says more"** - introduces refinement types with zero logic notation (the stub's own
  constraint): `{v: Int | v >= 0}` read aloud as "the integers where...", precondition/postcondition as one
  idea, the erases-at-runtime pitch vs. an assertion.
- **§"Why this and not full dependent types"** - decidability as the trade; the machine *finds* the proof
  (nobody writes one), set against Ch~\ref{ch:checker}'s hand-written proofs; why this is the pragmatic
  choice to make first (most shipped bugs live inside the decidable fragment).
- **§"How it fits"** - the extension bolts onto Ch~\ref{ch:types} inference as a second constraint-walk
  handing obligations to the solver; refinements erase so the type structure is untouched; **plus the
  honest cost note** - the 3000-term torture test exposed Algorithm~W's quadratic (substitution applied to
  the whole type env at every node), present since Ch4, unrelated to refinements, left unfixed *on purpose*
  because the measured compiler is frozen (a measurement that changes what you know without changing what
  you do). Frozen-oracle path NOT cited (lint-forbidden); reworded to keep the meaning.

**Verified:** built with `make` (NOT bare tectonic - bare tectonic bypasses the two lints). `make` exit 0,
`checkpaths.py` exit 0, `checkrefs.py` exit 0, **main.pdf = 123 pages**. Grepped for prose tics; trimmed a
4-way "the whole {appeal,design,point,apparatus}" cluster + one "precisely" I'd introduced (remaining
"whole numbers" hits are the integer idiom, not the tic). All citations reader-facing (`self/samples/`,
`prove/`), no dev-tree paths in prose. **NOT committed** (user commits their own work).
**Next (checked in with user first):** same amend pass for the other proof-arc stubs - ch17_adversary
(vivid: adversary.py, the 9-bug story), ch14_checker, ch15_metatheory; ch18_measures is polish-only.

**> SEQUENCE DECIDED WITH SET (2026-07-18): AFFINE → FIXPOINT → BOOK.** Before returning to the book,
two proof-frontier next-steps, both written up as strands under `formal/proof/strands/`:
  (1) **AFFINE** (`strands/affine/PLAN.md`) - OK **M0-M2 SPINE DONE 2026-07-18** (story in the dated
      entry ^ STRAND-AFFINE above): `affine_sound : HasA g t g' → Consumed g g'` proven by `indrec HasA`;
      functional `SlotLe`/`Consumed` predicates (no Id/J/inversion), threading subsumes Split; `make affine`
      + `make affine-controls` (4/4) green, summit untouched. Upgrades ch14/ch15 from "affine ownership =
      described" to "proven." **Remaining (optional): M3 the IO token `TIO` consumed once; the Expr/Ctx
      bridge; M4 operational reading (named boundary if it walls).**
  (2) **FIXPOINT** (`strands/fixpoint/PLAN.md`) - the self-hosting byte-identical fixpoint is ALREADY
      verified (`make -C self bootstrap`, `self/tests/bootstrap.py`; F2/F2⁺/O5' closed). So this is
      EXHIBITION not proof: name the property + its Trusting-Trust caveat (a backdoor is also a
      fixpoint → stability ≠ trust). Cheap; the bridge back into the book (ch13/ch15/interlude beat).
  `strands/SUMMARY.md` updated with both rows. THEN resume the book at Wave A.
  (3) ~~**PRESERVE** (semantic preservation)~~ - **SCRAPPED 2026-07-18 (Set).** Was parked as an optional
      post-book one-slice lcore proof; dropped entirely. The tractable form (`regalloc.verify` +
      differential oracle = translation validation) already lives in the book as ch13/ch17 prose, and a
      partial lcore slice risked making the un-proven rest read as *unfinished* rather than *consciously
      bounded* - undercutting ch13/ch17's own argument. `strands/preserve/` deleted; not a strand.

**> BOOK AXIS (queued behind affine+fixpoint) - plan at `book/PLAN.md`.** The user set the goal: finish the WHOLE book
(measured 2026-07-18: 95 stubs, ~20.7k words, only Part I + ch16 + appendix_oracle DONE; ~30-35k words
left), then migrate it to the public `github.com/Feyerabend/stack` repo's existing `lark/` subfolder under
reader names (`self/ optimize/ prove/`), NEVER the dev phase-numbers `07/ 08/` (which would collide
visually with the book's own `ch07`/`ch08`). Dev tree + logs stay private. **After a /clear doing book
work: read this pointer, then `book/PLAN.md` Ledger + current Wave, pick the next chapter.** Recommended
wave order: A = finish Part I (ch05/06/07/interlude1) → B = Part III proving (ch13/14/15/17 + polish
16/18/interlude3) → C = Part II optimization → D = matter → E = hardening + public move. One chapter per
session; Set reads back between. Definition-of-done + per-session protocol + lint rules all in PLAN.md.

### 2026-07-15 to 2026-07-17 - PROVE: the V3 summit, the three strands, and the V2.4 work

*Relocated from the old top pointer-block. These sessions were recorded only as
pointers and never got their own dated entries; the text is preserved here
(de-nested from the blockquote), newest sub-block first as it was written.*

**CURRENT POSITION (2026-07-17, V3 SUMMIT REACHED; DESCEND closed as a NAMED BOUNDARY; THREE STRANDS
opened past the summit - DENOT complete, VDEEP complete, SOLVER now proves BOTH QF-UFLIA halves
(interval LIA + congruence-closure UF); see STRAND-SOLVER-CC, STRAND-SOLVER, STRAND-VDEEP,
 STRAND-DENOT, V3-DESCEND-WALL below):** The upward V3 axis is DONE. The summit is **V3-FUND (∃-form), both
pitches green** - `fund : HasR → GoodEnv → Σk. SemE` proves refinement soundness as **total correctness**
for the whole judgment (Int/Bool/Var/App/If/Sub + Lam/Let). Green bar holds, SHARED FILE UNTOUCHED:
`make -C formal/proof check` → `OK: 5 files, 0 errors`. DESCEND (flip E to the ∀/safety form) was the
last candidate rung; this session took it seriously, hit a HARD KERNEL WALL, and - after reframing -
concluded it is BOTH unreachable in lcore AND not a higher truth for this language. It is now recorded
as a deliberate boundary alongside ℤ-vs-32bit / the equality seam. **THE TWO FINDINGS (story in
V3-DESCEND-WALL):**
  (1) **∀-form needs positive `Step` inversion, which lcore CANNOT express.** The App case must decompose
      a reduction of `EApp f x` - extract which rule fired + its sub-derivation. Stating even minimal
      `beta_det` fails at the MOTIVE: `inferred Expr empty b / expected Expr empty t1`. A well-typed
      inversion motive would have to reconstruct `body[arg]` from a generic source Expr, i.e. discriminate
      an `Expr` head and refine its `Ctx` index to `empty` inside `indrec Expr` - the exact operation the
      step file itself documents as impossible (lark-step.lcore:36-37, "general progress ... would require
      index refinement (g = empty) which lcore cannot perform"). Uniform motive = ill-typed; computed
      motive = unwritable. `step_not_val` works ONLY because it is the *negative*, uniform direction.
  (2) **The ∀-form is not a higher truth here anyway.** Lark is strongly normalizing (STLC, no recursion /
      fixpoint / recursive types). The ∀/safety form buys exactly *safety-under-divergence* - VACUOUS with
      no diverging terms. The ∃-form we already have green EXHIBITS a terminating reduction to a
      refinement-good value = **total correctness, the STRONGER statement**. It works in lcore precisely
      because it only ever *introduces* `StepsN` (builds it forward via `SN_cons`), never inverts it.
      Descending would trade a stronger theorem for a weaker one, in a form whose load-bearing index has
      nothing to bear, via machinery the kernel can't write. Not a summit above us - a wall beside us.
**CBV SIDE-FINDING (logged, fix deferred):** `StepBeta` lacks the `IsVal arg` guard its own header
documents (lark-step.lcore:39-43) → the encoded relation is non-deterministic, and the green ∃-proofs
actually lean on that (they fire β on unevaluated args, call-by-name-ish). Real latent defect; the fix
(add `IsVal a arg`, restoring determinism) would force reworking the ∃-form arrow to evaluate arguments
first - a separate optional "CBV-faithfulness" project, NOT a soundness gap for a pure total language.
**NEXT:** V3 upward axis is closed. Three STRANDS opened past the summit (`formal/proof/strands/`, agreed
order denot → solver → vdeep). Strand DENOT is COMPLETE; Strand VDEEP is COMPLETE (see STRAND-VDEEP);
Strand SOLVER now proves BOTH halves of QF-UFLIA's core - the interval LIA fragment ( STRAND-SOLVER) AND
congruence-closure soundness ( STRAND-SOLVER-CC). Solver's remaining deepenings are WIDTH not a missing
half (full multi-var Omega; CC completeness) - optional. Remaining older backlog is downward/optional
(V2 teeth gaps 4a/4b; the CBV-faithfulness project). Older frame (Pitch 2 / σ-fusion) below still holds.

**STRAND-VDEEP - COMPLETE: a VERIFIED ELABORATION `elab : HasR → MTm` of every Lark refinement
derivation into an intrinsically-typed MLTT term of the translated type, all 8 rules, no DESCEND wall
(2026-07-17).** `make vdeep` → 6/0; `make vdeep-controls` → 4/4 refused; main `make check` untouched 5/0.
Third strand
(order denot → solver → vdeep), the deepest: a VERIFIED ELABORATION of Lark refinement derivations into a
syntactic MLTT object theory living inside lcore (reification, not just a semantic model - that's denot).
File `strands/vdeep/lark-vdeep.lcore`. **KEY FINDING (matches the fundD prediction): C0 did NOT re-hit the
DESCEND wall in the introduction-only fragment.** `elab` recurses on the SOURCE `HasR` and only INTRODUCES
target `MTm` terms, so all 8 rules bar RT_Sub's SubFn are one-liners. **Block A - VERIFIED green this
session** (piped after meta+refine → 0 errors; `tyD`/`elabVar`/`elab_lam` inferred clean): an intrinsically
-typed theory `MTy`/`MCtx`/`MVar`/`MTm` (well-typing FUSED into the term index - no separate `HasMLTT`
needed, cleaner than the plan assumed), translations `tyD : RTy→MTy` / `ctxD : RCtx→MCtx`, `elabVar :
Var→MVar`, and the intro-only elab CASES `elab_int/bool/var/app/lam/let/if` (standalone at the `indrec
HasR` motive instances - even the λ-introduction `elab_lam`, C2's "real test", is wall-free). **Block B -
VERIFIED green:** intrinsic renaming `mweaken` via order-preserving embeddings (`OPE` keep/drop thinnings,
`headCtx`/`tailCtx`, `mvcase`, `ope_var`, `ope_id`, `ope_tm` going under the mlam/mlet binder via
`ope_keep`) - the McBride thinning technique. `mweaken : MTm g t → MTm (mcons s g) t` and `ope_tm` infer
their intended types, so **`indrec MTm` DOES go under a binder that changes the context index, in the
introduction direction** - vdeep does not re-hit the DESCEND wall even at the renaming crux. LANDING FIX
(banked lcore lesson): lcore's `indrec` INTERLEAVES each recursive argument's IH immediately after that
argument - the mapp/mif/mlet cases must bind `\x. \ihx.` per premise, NOT all IHs bunched at the end
(bunching → "IH type mismatch for arg N"). RESUME (C1/C2, not a risk anymore): (1) write `elabSub` by
`indrec Sub` (SubBase↦`msub_weaken`, SubFn↦η-coercion USING `mweaken` - weaken `f` under the fresh domain
binder, fire both variance IHs) + `elab_sub` + assemble `elab = indrec HasR` over all 8 cases. (2) add
Makefile `vdeep`/`vdeep-controls` + `controls.lcore` (≥4 forges) + README/PROVE/memory. Full detail:
`strands/vdeep/PLAN.md`. Fallback floor now moot (crux cleared).

**STRAND-SOLVER-CC - the UF half of QF-UFLIA is now PROVEN too: congruence-closure soundness in every
model (2026-07-17).** Extends the solver strand from its LIA floor ( STRAND-SOLVER) to the equational
(uninterpreted-function) half - the *other* half of the checker's from-scratch QF-UFLIA procedure. The
interval fragment proved the arithmetic verdict sound; this proves the congruence verdict sound, so BOTH
cores of the "solver is modelled, not proven" boundary are now discharged. **WHAT LANDED (appended to
`strands/solver/lark-solver.lcore`, all green):** `data Tm` - first-order terms (Nat-indexed atoms +
one binary `tapp`). `eval : Π(D)(val)(app). Tm → D` (`indrec Tm`) - interprets a term in ANY model; the
`Π D val app` quantification IS "in every model", which is the content of soundness. `data Ax` - the
hypothesis set handed to the solver, one concrete axiom `f a = a` (the classic congruence example). `data
Cong` - the congruence closure as an inductive derivation: reflexivity / symmetry / transitivity / the
congruence rule over application / axiom leaves = exactly the moves union-find+congruence make.
**`cc_sound : Π(D)(val)(app). (each axiom holds in the model) → Cong a b → Id D (eval a) (eval b)`** by
`indrec Cong` - cAx↦the hypothesis, cRefl↦`refl`, cSym↦`sym`, cTrans↦`trans`, cApp↦`ap2` on `app` (all
the equivalence+congruence machinery already lived in `lark-subst.lcore`). So the closure NEVER derives a
false equality: its verdict entails semantic truth in every model, same shape of teeth as `leB`. **Smoke:**
a genuine two-step run - congruence lifts `f a = a` under `f` to `f(f a) = f a`, transitivity with the
axiom gives `f(f a) = a`; `cc_smoke_sem` reifies it as "in every model of the axiom, `f(f a) = a`" and its
NORMAL FORM consumes the axiom hypothesis twice (verified via `:i` - not vacuous). **TEETH:** 4 new
controls (5)-(8) in `controls.lcore`, all refused - reflexivity forge (distinct atoms equated), congruence
forge (unequal head manufactured by `cApp`), axiom forge (the lone `axfa` reused to invent `Ax (tv0)(tv1)`),
transitivity gap (broken shared middle). **GREEN BARS:** `make solver` (6 files/0) + `make solver-controls`
now **8/8** (4 interval + 4 CC); `make check` untouched 5/0. **lcore note:** the `indrec Cong` IH
interleaving rule bit again - cTrans/cApp bind `\arg. \ih.` per recursive premise (same lesson banked in
STRAND-VDEEP). **STILL A FLOOR, just a wider one:** CC *soundness* not *completeness*, single concrete
axiom set; full multi-variable Omega + CC completeness remain OPTIONAL width in `strands/solver/PLAN.md`.
Both QF-UFLIA halves' cores are now proven - the seam is closed for both the arithmetic and equational
refinements a checker would face.

**STRAND-SOLVER - the refinement solver is PROVEN, not modelled, for the interval fragment; the real
`rge2 ⊆ rge1` seam is discharged by a decision procedure (2026-07-17).** Second of the three post-summit
strands (order denot → solver → vdeep). Everywhere in V3, `SubBase` (lark-refine.lcore:207) takes the
predicate implication `Π n. IsTrue(p n) → IsTrue(q n)` as a GIVEN - "if the solver says p ⊆ q, subtyping
is sound." This strand DISCHARGES that hypothesis for the fragment the spine actually uses: lower-bound
(interval) refinements `{n | n ≥ c}`. **WHAT LANDED (`strands/solver/lark-solver.lcore`, all green):**
`leB : Nat → Nat → Bool` - a real DECISION PROCEDURE (boolean ≤); crucially the spine's predicates ARE
this, `ge1 ≡ \n. leB 1 n` / `ge2 ≡ \n. leB 2 n` DEFINITIONALLY (both normalize to the same nested
natrec). `leB_sound` + `leB_complete` - the verdict reflects the inductive `Le` both ways (`leB a b=true ⇔
Le a b`); sound = verdict⇒truth is the heart of solver correctness; proved by double natrec (`abort` for
the false/Empty leaf) resp. `indrec Le`. `entail_ge` - interval entailment: to prove `{n≥c1} ⊆ {n≥c2}`
the solver DECIDES one comparison `c2 ≤ c1` then transports via the existing `le_trans` - this CONSTRUCTS
the `SubBase` premise from a decision. `sub_ge` - emits `Sub TInt (RInt{n≥c1}) (RInt{n≥c2})`. **THE
PAYOFF `sub_fixture` : `Sub TInt rge2 rge1`** - the exact certificate V3 took on faith - and
`sub_fixture_sem` FEEDS IT INTO the existing `sub_sound_v`, so the solver's verdict flows into the
operational soundness map (cross-strand tie). **S2:** `nmax`/`data NList`/`norm`/`sub_conj` - conjunctions
of lower bounds normalized to the tightest (`nmax`-fold), entailment reduced to comparing normalized
bounds (the solver handling constraint SETS; smoke `{n≥3,1,2} ⊆ {n≥1,2}`). **TEETH:** `controls.lcore`
4/4 refused - false-entailment forge (`{n≥1} ⊄ {n≥2}`, needs a witness of `leB 2 1 = Empty`), forged
soundness, reversed certificate, conjunction-weakening forge. The solver CANNOT emit a certificate for a
false entailment - that is the point. **GREEN BARS:** `make solver` (6 files/0) + `make solver-controls`
(4/4); `make check` untouched 5/0. **lcore lessons:** Empty is eliminated by the kernel's `abort A e`
(there is NO `indrec Empty` - "unknown family"); Nat has NO numeric literals (`succ`/`zero` only); every
natrec base/step must be a fully-annotated parenthesized atom, the STEP annotation covering the whole
`Π(arg).Π(ih).<motive succ>` type (not just the result). **FLOOR REACHED, not the whole solver:** this is
the single-variable interval slice of QF-UFLIA; congruence closure (the uninterpreted-function half) and
full multi-variable Omega (Farkas UNSAT witnesses) remain as OPTIONAL deepenings in `strands/solver/
PLAN.md` - but the seam is already closed for the refinements the spine inhabits.

**STRAND-DENOT - the denotational model climbs WALL-FREE past DESCEND; full fundamental lemma, both
λ-introductions in ONE LINE (2026-07-17).** After DESCEND walled, Set asked to try the three alternative
climbs suggested earlier as SEPARATE STRANDS, order denot → solver → vdeep (vdeep last, "the most
interesting to me"), keeping plans + code for later review even if the later two don't complete. Set up
`formal/proof/strands/` (README + one PLAN.md per strand) and BUILT the denotational strand end to end.
**THE IDEA:** interpret refinement types as lcore TYPES and prove soundness by recursion on the DERIVATION
(`indrec HasR`) - never eliminate the operational `Step` relation, so there is nothing to invert and the
DESCEND wall is structurally absent. **WHAT LANDED (`strands/denot/lark-denot.lcore`, all green):**
`TyD : Ty → Type` (Int↦Nat, Bool↦Bool, TFn↦lcore →, scalars↦Unit; large-elim, TFn IHs INTERLEAVED
`\a.\iha.\b.\ihb`); `RTyD : Πt. RTy t → Type` ({v:Int|p}↦the subset `Σ(n:Nat).IsTrue(p n)`, refined fn↦a
DEPENDENT map); `sub_denot : Sub t r r' → (RTyD t r → RTyD t r')` - subtyping soundness, SubFn = the
classic `f↦λx. ihc (f (ihd x))`, DRAMATICALLY cleaner than the operational `sub_sound_v` (no step index,
no SemEV, no EApp); `DEnv : Πg. RCtx g → Type` (telescope valued in RTyD) + `denot_lookup`; and the payoff
**`fundD : HasR g rg t r e → DEnv g rg → RTyD t r`** by `indrec HasR` over ALL 8 rules - every case ONE
LINE. The two rules that cost the operational proof its entire **Pitch 2** (the substitution lemma: lb,
fuse, lam_app_cert, let_cert, σ-fusion, a step budget) are here trivial: `RT_Lam ↦ \env.\x. ihbody
(x,env)`, `RT_Let ↦ \env. ihbody (ihval env, env)`, `RT_App ↦ \env. ihf env (ihx env)` (lcore's own λ /
application IS the model). Showcase `fundD_id`: the Lark identity on `{Int|ge2}` (built RT_Lam+RT_Var)
denotes the identity map on `Σ(n).IsTrue(ge2 n)`, RT_Lam a one-liner. **TEETH:** `controls.lcore`, 4/4
refused - payload forge (`\_.false` → IsTrue=Empty), variance forge ({ge2}→{ge2} is not {ge1}→{ge2}),
subtyping-direction forge (imp21 can't witness {ge1}⊆{ge2}), erasure/index forge (RInt at a TFn index).
**GREEN BARS:** new Makefile targets `denot` (OK: 6 files, 0 errors) + `denot-controls` (OK: 4/4 refused);
`make check` UNTOUCHED at 5/0. **THE NAMED BOUNDARY (honest cost):** this is soundness-OF-THE-MODEL, not
ADEQUACY - it does not yet bridge the denotation back to the CEK machine's actual output (the operational
V3 relation DOES, by running the machine; the two are complementary). The adequacy bridge is a
logical-relations argument whose FORWARD direction should stay clear of the DESCEND wall; untried, noted
in `strands/denot/PLAN.md`. **STRANDS solver + vdeep = PLAN.md only** (solver: prove the QF-UFLIA decision
procedure, discharging the `SubBase` implication hypothesis, CC-soundness first; vdeep: verified
elaboration into a `data MLTT` - the deepest, may re-hit the DESCEND wall from a new angle via nested
indexed induction, so its C0 is a one-session scouting probe with `fundD` as the guaranteed shallow floor).

**V3-DESCEND-WALL - the ∀/safety form is unreachable in lcore AND unnecessary here (2026-07-17).**
Followed the ratified plan (truncated `minus k-j` value-index; descend-spine-first staging) into
scratchpad probes, then hit the wall and turned back. **What landed green (scratchpad, kept as the record
of where the wall is, NOT in the shared file):** `probe_minus` - `minus` (recurse subtrahend, inner
natrec peels minuend: `minus a 0=a`/`minus 0 (S b)=0`/`minus (S k)(S j)=minus k j` definitional; `3 1→2`,
`2 2→0`, `1 3→0` to refl) + `apS` + `minus_plus : Le j k → plus j (minus k j)=k`; `probe_shape` - the
flipped `SemEV2/SemV2/SemE2` (∀-form, honest Kripke arrow, vacuous at k=0) elaborate well-formed;
`probe_inv` - `stepsN_inv_succ` (a `succ m` reduction splits into first `Step` + `m`-tail, via a
natrec-COMPUTED motive on the COUNT - this direction works because the count is `Ctx`-free);
`probe_notval` - `NV` (Expr head-discriminator → Unit on value heads / Empty else), `isval_nv` (a value
is value-headed), `step_not_val` (a stepping term is not a value - every Step source is a non-value head,
`isval_nv` discharges each case). **Where it stopped:** `step_det`/positive `Step` inversion - needed to
decompose `EApp f x` reductions for the fund App case - is inexpressible (finding (1) above; the
`beta_det` motive typecheck was the decisive experiment). **The reframe (finding (2)):** for an SN
calculus the ∃-form is total correctness = stronger, so there is nothing to descend TO. **Decision
(ratified with Set):** go back - V3-FUND (∃-form) IS the summit; record the ∀-form + the CBV non-
determinism defect as named boundaries; revert to the last green state (which was never left - all
DESCEND work stayed in scratchpad; shared file green throughout). One CBV dev-harness copy of the step
file with the `IsVal arg` guard (`scratchpad/cbv-step.lcore`) elaborated green, confirming the fix is
well-formed - kept only as evidence for the deferred CBV-faithfulness project.

**V3-FUND-P2 - RT_Lam & RT_Let PROVEN, PITCH 2 COMPLETE (2026-07-17, uncommitted).**
Added the two λ-introduction constructors to `data HasR` (`RT_Lam`, `RT_Let`) and their cases to the
`indrec HasR` in `fund` (`lark-refine.lcore`). Both cases bottom out at `fuse` (the σ-fusion capstone,
 V3-SIGMA-3g) exactly as designed. Seven new `:let` helpers before `fund`:
  - `lb` - the opened λ-body (weaken env under the binder, plug the bound var).
  - `lam_app_cert` - the applicative-clause certificate: one `StepBeta`, then `J`-transport the body IH's
    reduction along `sym (fuse ...)`. Budget = `succ` on both k and j (β costs one step); LeS.
  - `fund_lam_case` - RT_Lam: the λ is already a value, so j=0 (`SN_refl`, `ValLam`); the arrow clause
    `\w.\hw. lam_app_cert ... (ihbody (w,env) (hw,ge))` runs the body IH at the supplied argument+goodness.
  - `lift_let` - `StepsN` congruence through the let scrutinee (`indrec StepsN`, cons uses `StepLet`).
  - `semv_isval` - a `SemV` value is an `IsVal` (`indrec RTy`; Int/Bool J-transport along the pinning,
    Fn = `fst h`). Needed to fire `StepLetBeta` (which demands the bound value be a value).
  - `let_cert` - run the bound val to its value (`lift_let`), fire `StepLetBeta` (`semv_isval`), `J`-transport
    the body IH along `sym (fuse ...)`, `steps_append` the two legs, `le_plus_mono` the budgets.
  - `fund_let_case` - RT_Let: `(\hval. let_cert ... (ihbody (vv,env) (goodness,ge))) (ihval env ge)`, threading
    the bound val's own value `vv = fst(snd(snd(snd hval)))` and its `SemV` goodness into the body IH.
The def-eq chain that makes it go: `sub_ground g (TFn a b) (ELam g a b body) env ≡ ELam empty a b (lb...)`,
its contractum ≡ `fuse` LHS, and `sub_ground (ext a g) b body (w,env) ≡ fuse` RHS - so the body IH's
certificate transports across one `sym (fuse)` and `StepBeta`/`StepLetBeta` prepends the single step.
Method mirrored the App/If cases exactly (no solver, no src/ beyond refine). Built each artifact green
standalone against the full 5-file chain BEFORE splicing; `tools/parens.py` gated every single-line def
(caught one +1 imbalance and the `let_cert` -1). Controls (chain loaded, all REFUSED, honest probe
ACCEPTED): C1 λ-codomain widen rge2→rge1 - C2 λ-domain swap - C3 let-result-rider forge - C4 let-val-rider
forge. WATCHED-TO-FAIL note: the first control run was VACUOUS (zsh didn't word-split the file list, so the
chain never loaded and the forgeries "failed" only on undefined names) - caught and reran with the chain
genuinely loaded + an honest-accepts counter-probe, the real teeth. Green: `OK: 5 files, 0 errors`.
(was 2026-07-16, night):
the PROVE axis - V3. SPINE, V3-MONO, V3-TFN, V3-FUND (Pitch 1) are CLOSED AT 0;
`fund : HasR g rg t r e → GoodEnv g rg env → Σk. SemE t r k (e[env])` proves every
refined-typing derivation (Int/Bool/Var/App/If/Sub) lands in the relation. NOW: PITCH 2
(RT_Lam/RT_Let) is underway. Its ENABLING RUNG is DONE and GREEN - V3-WK0 below:
kernel `weaken` (opaque to induction on neutral terms, the thing that blocked the
substitution lemma) is RETIRED from the proof-critical path. `lark-subst.lcore` now
carries an lcore-native cutoff-indexed weakening `ins`/`shift`/`wk`/`wk0` that computes
one constructor-layer at a time (so it IS inductable); `weaken_semctx_d`/`sub_open` are
rebased onto `wk0`; agreement smokes hold. Five files pipe clean. UNCOMMITTED (Set commits).**
**NEXT - the σ-FUSION PILE (ratified with Set 2026-07-16, "bank wk0 rung, then grind"):
build the substitution lemma brick-by-brick, GREEN BAR AT EACH STEP. The Var/environment
layer ( V3-SIGMA-1) AND the big `indrec Expr` commutation `GenCancel` ( V3-SIGMA-2) are
BOTH DONE - landed in `lark-subst.lcore`, green at each step. Only the fusion assembly (3)
and RT_Lam/RT_Let remain. Bricks recorded:
  (1) OK `wk_lookup` - lookup commutes with env weakening: `sem_lookup_d (ext a d) g t v
      (weaken_semctx_d a d g env) = wk0 a d t (sem_lookup_d d g t v env)`. refl+IH, no J.
  (2a) OK `del` (delete env entry at de Bruijn depth n) + `sdl` - shift/del/lookup cancel:
      `sem_lookup_d d (ins a n g) t (shift a g t v n) env = sem_lookup_d d g t v (del a n g d env)`.
      This is the Var case of the coming weaken-subst commutation. refl+IH, no J.
  (2b) OK DONE ( V3-SIGMA-2 below) - `GenCancel`, the BIG `indrec Expr` weaken-subst
      commutation `sub_open (ins a n g) t (wk a g t e n) d env = sub_open g t e d (del a n g d env)`.
      Landed with the J-based congruence toolkit (`ap`/`trans`/`ap2`/`ap3`) and `del_wk`
      (`del` commutes with `weaken_semctx_d`, for the ELam/ELet binder cases). Var=`sdl`,
      literals=refl, App=`ap2`, If=`ap3`, ELam=`ap(ELam)∘trans∘del_wk`, ELet=`trans∘ap`.
      6 ground smokes cancel to `refl` (each branch fires). Green.
**V3-SIGMA-3a - DESIGN FORK RATIFIED WITH SET & LANDED GREEN (2026-07-16, continuing):
`sub_open` is now HOMOMORPHIC on ELet.** DISCOVERED grinding brick 3: the old `sub_open`
DELIBERATELY reduced lets during substitution (ELet case inlined `ih_bd d1 (ih_v d1 e1, e1)`;
the line-289 smoke's comment literally said "ELet reduces the inner let"). PROVEN empirically
(scratchpad probe_idsub) that this makes the substitution lemma FALSE for any let-containing term:
`sub_ground empty t X star = X` fails when X has a let (t2/t4 rejected) - and the RT_Lam/RT_Let
β-contractum fusion `C = D` bottoms out on exactly that identity, so Pitch 2 was IMPOSSIBLE under
the old design. FIX (proven first in probe_homo via a clone `sub_open2`, then Set chose it over two
alternatives via AskUserQuestion): the ELet case now emits an `ELet` node and weakens the env under
the binder EXACTLY like ELam - reducing a let stays operational (`StepLetBeta`), where it belongs.
Under homomorphic subst all 4 idsub probes pass. One downstream repair: `GenCancel`'s ELet case
(had assumed inlining) rewritten to `ap2(ELet) [ihv] [ELam-style trans∘del_wk body-leg]`.
Five files pipe clean - `OK: 5 files, 0 errors`. UNCOMMITTED (Set commits).**
**V3-SIGMA-3b - FOUR MORE σ-BRICKS BANKED GREEN (2026-07-16, continuing, uncommitted):**
Grinding brick 3, four self-contained lemmas landed in `lark-subst.lcore`, GREEN at each step:
  - `comp` / `comp_lookup` - composition of substitution ENVIRONMENTS (`comp d1 d2 env2 g env1
    : SemCtx_d d2 g`, maps each entry through `sub_open`) and the fact that lookup commutes with
    it (refl@here, IH@there, no J). The foundations of `sub_sub`.
  - `id_env` / `shift_zero` / `id_lookup` / `idsub` / `idsub_ground` - the IDENTITY substitution
    and `idsub : sub_open g t e g (id_env g) = e` (ground form `sub_ground empty t X star = X`).
    Turned out CLEAN: the binder case is DEFINITIONAL because `id_env (ext a g)` is byte-identical
    to the env `sub_open` builds under a binder - no exchange lemma. `id_lookup`'s there-case needed
    one tiny helper `shift_zero` (`shift a g t v 0 = there g t a v`, two refls) because `wk0` of an
    opaque var is stuck on `shift ... 0`. Uses only the existing `wk_lookup`.
  - `comp_weaken_cancel` - `comp (ext a empty) empty (w,star) g (weaken_semctx_d a empty g env) = env`,
    the env-equality (SECOND component) at the heart of the RT_Lam fusion. empty case = Unit-eta via
    `unitrec`; succ case = head through `GenCancel`@0 + `idsub_ground`, tail through the IH; `ap2` over
    the pair. (Banked lcore facts: lcore HAS definitional Σ-eta AND `unitrec` for Unit - so `env ≡
    (fst env, snd env)` and `star ≡`(opaque unit) are both reachable.)
REMAINING for the fusion (the hard core - a weaken-commutes-with-subst tower, mechanical, mirrors
the GenCancel family; realistically another session):
  (3a) `sub_weaken` (the "substitution commutes with weakening" lemma) via its cutoff-GENERALISED
       form `GSW` (indrec Expr over an insertion index n, EXACTLY like GenCancel/sdl/del carry n):
       Var case = `wk_lookup_n` [OK DONE, with `weaken_semctx_d_n` - see V3-SIGMA-3c], App/If =
       ap2/ap3, binder fires IH@(succ n) → `weaken_n_commute` → the LEAF `wk_wk` weaken/weaken exchange.
       WARNING The leaf is the two-cutoff de Bruijn EXCHANGE SWAMP (needs `ins_ins` ctx-exchange + `shift_shift`
       var-exchange, both under coercion) - details in V3-SIGMA-3c. Cutoff generalisation is REQUIRED
       - the plain n=0 IH is too weak (weakening happens at index 1 under the term's own binder).
  (3b) `comp_weaken` - env-induction, entry = `sub_weaken`@0. (comp commutes with weaken under a binder.)
  (3c) `sub_sub` - the GENERAL composition lemma (indrec Expr): Var=`comp_lookup`, App=ap2, If=ap3,
       binder=`comp_weaken`. Then THE FUSION `C = sub_sub-instance ; ap sub_open (first=w, second=
       comp_weaken_cancel) = D`.
  then RT_Lam/RT_Let in HasR + their fund cases (β-redex J-transported along the fusion eq).
PROBED 2026-07-16: cancellation holds by refl ONLY for literals; neutral `e` needs real
induction (probe_cancel.lcore) - hence the GenCancel machinery. Scratchpad probes:
probe_wklookup / probe_del / probe_sdl (all pass). After Pitch 2: DESCEND (flip E to
∀/safety; reworks all fund cases once; needs Step determinism / frame decomposition).**
Green bar = `make -C formal/proof check` (greps the transcript, fails loudly - lcore alone
exits 0 on a type error). V2 teeth gaps (4a)/(4b) remain optional backlog.
**V3-SIGMA-3c - GSW LAYER-1 BANKED + THE LEAF MAPPED SHARPLY (2026-07-16, continuing, uncommitted):**
Grinding the (3a) `GSW` tower. Two more self-contained bricks landed in `lark-subst.lcore`, GREEN:
  - `weaken_semctx_d_n` - cutoff-generalised env weakening (`SemCtx_d d g → SemCtx_d (ins a n d) g`,
    each entry `Y ↦ wk a d _ Y n`; `n=0` recovers `weaken_semctx_d`). Needed because GSW's binder
    fires the IH at `(succ n)` - the `n=0` form is too weak.
  - `wk_lookup_n` - lookup commutes with it (`sem_lookup_d (ins a n d) g t v (weaken_semctx_d_n ...) =
    wk a d t (sem_lookup_d d g t v env) n`). here=refl, there=IH; cutoff-generalised `wk_lookup`.
SHARPENED INTEL (hard-won, so the next session doesn't rediscover it): the tower's LEAF is NOT a
single-cutoff lemma. GSW's binder case needs `weaken_n_commute` (env-induction) whose per-entry
obligation is a weaken/weaken EXCHANGE `wk_wk`, and working its OWN binder case forces the general
TWO-CUTOFF form
    `wk a1 (ins a2 i d) s (wk a2 d s Y i)(succ(add i n)) = wk a2 (ins a1 (add i n) d) s (wk a1 d s Y (add i n)) i`
- and even the TYPE of that Id needs an `ins`/`ins` context-exchange coercion
(`ins a1 (succ(add i n))(ins a2 i d) = ins a2 i (ins a1 (add i n) d)`, STUCK on opaque `i`/`d`).
That is the classic de Bruijn exchange swamp: a fresh sub-tower = `ins_ins` ctx-exchange +
`shift_shift` var-exchange under coercion + `wk_wk` expr-exchange under coercion, THEN `weaken_n_commute`
→ `GSW` → `sub_weaken` → `comp_weaken` → `sub_sub` → the fusion → RT_Lam/RT_Let. Realistically its
own session. Stopped here at green (6 σ-bricks banked this session: comp/comp_lookup, id-tower,
comp_weaken_cancel, weaken_semctx_d_n, wk_lookup_n). Five files pipe clean - `OK: 5 files, 0 errors`.
**V3-SIGMA-3d - THE GSW LEAF, FIRST LEMMA `shift_shift` CLOSED AT 0 OK (2026-07-17, uncommitted):**
Entered the exchange swamp mapped in 3c. Landed the transport toolkit + the Var-level two-cutoff
exchange in `lark-subst.lcore`, GREEN at each step (`OK: 5 files, 0 errors`):
  - `sym` / `trC` - symmetry of Id and coercion-along-a-Ctx-path (`trC P c1 c2 q : P c1 → P c2`),
    both one-liners over `J`. `ins_ins` - the CTX-exchange: `ins a2 i (ins a1 (add i n) d) =
    ins a1 (succ(add i n)) (ins a2 i d)`, `natrec` on i + `indrec Ctx` on d, `ap(ext)` of the IH.
    Holds UNCONDITIONALLY (no in-range bound) because the `ins` junk case was ratified to a no-op,
    and a no-op commutes with everything. Plus `tr_here`/`tr_there` (transport of `here`/`there`
    across an `ext`-of-a-Ctx-path - the coercion peels one binder) and the `tr_*` Expr-constructor
    family. [These were the 12 microlemmas from the prior session, already banked.]
  - `shift_shift` - the LEAF's first lemma: `shift a1 (ins a2 i g) t (shift a2 g t v i)(succ(add i n))
    = trC ... (ins_ins ...) (shift a2 (ins a1 (add i n) g) t (shift a1 g t v (add i n)) i)` - the de Bruijn
    VAR exchange under the `ins_ins` context coercion. Proof: `natrec` on the lower cutoff i (outer) +
    `indrec Var` on v (inner, succ case only). BASE i=0 works uniformly for all v (`shift_zero` both
    sides + a definitional there-succ). SUCC/here = `sym tr_here`. SUCC/there = `ap(there -) ∘ IH ∘
    sym tr_there`, where IH = the natrec-IH at m applied to the sub-variable w. Built modularly
    (ss_base/ss_here/ss_there each typecheck standalone; the megaline wouldn't parse).
    lcore lesson banked: `indrec` CANNOT infer bare-lambda case bodies - cases must be FULLY-APPLIED
    terms. So the here-case eta-contracts to `(ss_here a1 a2 n m)`, and `ss_there` carries a trailing
    (ignored) `ihv` param so `(ss_there a1 a2 n m ih)` matches the there-case shape exactly. Two smokes
    (a `here`-var and a nested `there`-var) elaborate.
  - `wk_wk` - the LEAF's second (and final) lemma: the Expr-level two-cutoff exchange
    `wk A1 (ins A2 i g) t (wk A2 g t e i)(succ(add i N)) = trC ... (ins_ins A1 A2 N i g)
    (wk A2 (ins A1 (add i N) g) t (wk A1 g t e (add i N)) i)`. `indrec Expr` over e, motive carries
    `Π(i:Nat)`. Built as 10 fully-applied case helpers (`wkwk_litint`...`wkwk_if`), then the assembly
    (mirrors the `GenCancel` skeleton exactly). Cases: 5 literals = `sym tr_lit_*`; EVar = `ap(EVar -)
    ∘ shift_shift ∘ sym tr_evar`; EApp/EIf = `ap2`/`ap3` + `sym tr_app`/`sym tr_if`; ELam/ELet fire the
    IH@(succ i) and reconcile via `sym tr_lam`/`sym tr_let`. THE KEY that made the binder cases free:
    `ins_ins A1 A2 N (succ i)(ext a1 g) ≡ ap(ext a1)(ins_ins A1 A2 N i g)` DEFINITIONALLY (that's how
    ins_ins computes on an `ext`), and `ext a1 (ins A2 i g) ≡ ins A2 (succ i)(ext a1 g)`, and
    `add(succ i) N ≡ succ(add i N)` - so `ihbd (succ i)`'s coercion IS byte-for-byte the coercion
    `tr_lam` pushes under the binder, no transport surgery (unlike GenCancel's ELam, which needed
    `del_wk`). Probed the ELam case standalone FIRST (highest risk); it was green, then the full
    assembly went green on the first try. Lambda-over-lambda smoke elaborates. THE EXCHANGE SWAMP IS
    CLOSED. NEXT: `weaken_n_commute` (env-induction, per-entry = `wk_wk`@specific cutoffs) → `GSW`
    (indrec Expr, Var=`wk_lookup_n`, binders IH@succ ∘ `weaken_n_commute`) → `sub_weaken` (= GenCancel@0
    ∘ GSW@0) → `comp_weaken` → `sub_sub` → the fusion → RT_Lam/RT_Let. Then DESCEND.

**V3-SIGMA-3e - GSW LAYER-2 CLOSED: `weaken_n_commute` → `GSW` → `sub_weaken` OK (2026-07-17, uncommitted):**
Climbed back up the tower off the CLOSED exchange swamp. Three defs landed in `lark-subst.lcore` between
the `wk_wk` block and `IsVal`, GREEN (`OK: 5 files, 0 errors`):
  - `weaken_n_commute` - the two `SemCtx_d` env-weakenings COMMUTE: insert-at-0 (`weaken_semctx_d`) and
    insert-at-cutoff-`(succ n)` (`weaken_semctx_d_n`) applied in either order agree -
    `weaken_semctx_d_n a (ext a1 d)(succ n) g (weaken_semctx_d a1 d g env) =
    weaken_semctx_d a1 (ins a n d) g (weaken_semctx_d_n a d n g env)` (both live in
    `SemCtx_d (ins a (succ n)(ext a1 d)) g ≡ SemCtx_d (ext a1 (ins a n d)) g`). By env-induction
    (`indrec Ctx`): empty = `refl star`; ext-case head is the LEAF `wk_wk a a1 n d t (fst env) zero`
    ON THE NOSE - because `ins_ins a a1 n zero d` computes to `refl` (natrec base) so `wk_wk`'s residual
    `trC` coercion collapses to the identity, and `add 0 n ≡ n` / `ins a1 0 d ≡ ext a1 d` / `wk0 = wk _ 0`
    line the endpoints up - tail = the IH, joined by `ap2` on the SemCtx_d pair `\h.\tl.(h,tl)`.
  - `GSW` - substitution commutes with weakening the OUTPUT context, cutoff-generalised:
    `sub_open g t e (ins a n d)(weaken_semctx_d_n a d n g env) = wk a d t (sub_open g t e d env) n`.
    `indrec Expr` over e (mirrors the `GenCancel` skeleton): literals = `refl`; `EVar` = `wk_lookup_n`
    (the layer-1 lemma, exactly its shape); `EApp`/`EIf` = `ap2`/`ap3` over the IHs; `ELam`/`ELet` fire
    the IH@`(succ n, ext a1 d)` under the fresh `EVar` head and reconcile the two env transforms via
    `weaken_n_commute` (transported by `ap(\tl. sub_open ...(EVar, tl))` ∘ `sym`). The binder-case context
    lines up definitionally: `ins a (succ n)(ext a1 d) ≡ ext a1 (ins a n d)`, and `shift`-of-`here` under
    the nonzero cutoff computes the fresh head to `here (ins a n d) a1`, so ONLY the tail needs the
    commute. Probed the ELam case standalone (`gsw_lam`) FIRST - green - then the full 10-case assembly
    went green on the first try.
  - `sub_weaken` = `GSW`@0 - the clean cutoff-0 shape Pitch-2 fusion consumes:
    `sub_open g t e (ext a d)(weaken_semctx_d a d g env) = wk0 a d t (sub_open g t e d env)`.
  WATCHED-TO-FAIL (load-bearing): replacing the `weaken_n_commute` transport in GSW's ELam case with a
  bare `refl` is REFUSED (`type mismatch` / `indrec ... cannot infer type of case 6 ('ELam')`) - the two
  env tails genuinely differ; restored → green. NEXT: `comp_weaken` (= `sub_weaken`@empty target,
  env-induction) → `sub_sub` → the fusion → RT_Lam/RT_Let. Then DESCEND.

**V3-SIGMA-3g - THE FUSION: `fuse` OK (2026-07-17, uncommitted):** The capstone of the σ-pile.
One def landed in `lark-subst.lcore` between `:i sub_sub` and the `IsVal` section, GREEN
(`OK: 5 files, 0 errors`). This is the exact identity `RT_Lam`/`RT_Let` will consume: it says the
β/let contractum equals the semantic substitution.
  - `fuse` - `sub_open (ext a empty) b (sub_open (ext a g) b body (ext a empty)(EVar..., weaken... env)) empty (V,star)
    = sub_open (ext a g) b body empty (V, env)`. The LHS is EXACTLY the `Step` contractum: `StepBeta`/`StepLetBeta`
    both contract to `sub_ground (ext a empty) b BODY (V, star)` = `sub_open (ext a empty) b BODY empty (V, star)`
    where `BODY` is `body` already opened under the weakened env - i.e. the LHS above. The RHS is the honest
    one-shot substitution `body[V, env]`.
  - PROOF = `trans (sub_sub ...) (ap outer (ap inner (comp_weaken_cancel a V g env)))`. First `sub_sub` collapses
    the sub∘sub into a single `sub_open ... empty (comp (ext a empty) empty (V,star)(ext a g) env_ext)`; the
    composite's HEAD reduces definitionally to `V`, leaving `(V, comp-tail)`; then `comp_weaken_cancel` (already
    in the file, from the composition pile) rewrites `comp-tail ≡ env`, giving `(V, env)`. Two `ap`s carry the
    tail rewrite up through the pair and the `sub_open`.
  WATCHED-TO-FAIL (load-bearing): replacing `comp_weaken_cancel a V g env` with `refl env` (asserting the false
  defeq comp-tail ≡ env) is REFUSED (`type mismatch` / `definition of 'fuse' failed`); restored → green.
  The WHOLE σ-FUSION PILE is now CLOSED ( V3-SIGMA-1 Var layer → 2 `GenCancel` → 3a-3f homomorphic-let/GSW/
  composition → 3g fusion). NEXT: `RT_Lam`/`RT_Let` in `fund` (Pitch 2 completes) - new `HasR` constructors whose
  `fund` cases J-transport the β-redex certificate along `fuse` - then DESCEND. Per plan, /clear before that rung.

**V3-SIGMA-3f - THE COMPOSITION LEMMA: `comp_weaken` → `sub_sub` OK (2026-07-17, uncommitted):**
Substitution now provably COMPOSES. Two defs landed in `lark-subst.lcore` between `sub_weaken` and
`IsVal`, GREEN (`OK: 5 files, 0 errors`). The composition machinery (`comp`, `comp_lookup`) already
existed below them.
  - `comp_weaken` - `comp` commutes with weakening UNDER A BINDER:
    `comp (ext a d1)(ext a d2)(EVar..., weaken_semctx_d a d2 d1 env2) g (weaken_semctx_d a d1 g env1) =
    weaken_semctx_d a d2 g (comp d1 d2 env2 g env1)`. By env-induction (`indrec Ctx` over `g` with `env1`):
    empty = `refl star`; ext-case is `ap2` on the SemCtx_d pair, tail = IH, and the HEAD obligation is
    `trans (GenCancel a d1 t (fst env1) zero (ext a d2) env2L) (sub_weaken a d1 t (fst env1) d2 env2)` -
    i.e. weaken-then-substitute-under-the-extended-env goes through `del@0 ≡ snd` (GenCancel) and then
    `sub_weaken` closes the gap. THIS is why `sub_weaken` had to land first ( 3e): it is exactly the
    per-entry brick `comp_weaken` needs.
  - `sub_sub` - the composition lemma over FULL expressions:
    `sub_open d1 t (sub_open g t e d1 env1) d2 env2 = sub_open g t e d2 (comp d1 d2 env2 g env1)`
    (substitute-then-substitute = substitute-with-the-composed-env). `indrec Expr` over `e`: literals =
    `refl`; `EVar` = `comp_lookup` ON THE NOSE (its exact shape, the pre-existing Var brick); `EApp`/`EIf`
    = `ap2`/`ap3` over the IHs; `ELam`/`ELet` fire the IH@`(ext a1 d1, ext a1 d2, env1L, env2L)` under the
    fresh `EVar` head and reconcile the two env transforms via `comp_weaken`. Orientation REVERSES GSW's:
    here the IH comes FIRST, then the `comp_weaken` env-massaging (`ap(\tl. sub_open ...(EVar, tl)) ∘
    comp_weaken`), joined by `trans` - because `comp (ext...)(ext...) env2L (ext a1 g1) env1L` reduces
    definitionally to `(fst env2L, comp ... g1 (weaken ... env1))`, so only the tail differs.
  WATCHED-TO-FAIL (load-bearing): replacing BOTH `comp_weaken` invocations in `sub_sub`'s ELam/ELet
  body-paths with a bare `refl` (asserting the false defeq comp-tail ≡ weaken-tail) is REFUSED
  (`type mismatch` / `indrec ... cannot infer type of case 6 ('ELam')`); restored → green.
  lcore lesson re-banked: the REPL is LINE-BASED - a `:let` must be ONE physical line (a multi-line body
  parses as `unexpected char ' '`); collapse whitespace before piping. NEXT: the FUSION assembly (compose
  `sub_sub` + `comp_weaken_cancel` into the `sub_ground (weaken e) = e` shape RT_Lam/RT_Let consume) →
  RT_Lam/RT_Let in `fund` (Pitch 2 completes) → DESCEND.

**OPEN ITEMS / BACKLOG (not on the rung path; sorted by WHEN to address):**
**[DONE 2026-07-16] The green pile is COMMITTED** (`56c698e`, `c966b2a`); tree was clean.
**[OPTIONAL - low priority, only if fuzzing coverage is later judged thin] Two nested-measure teeth gaps,
both named in the RUNG (1) entry's KNOWN LIMITS.** Recommendation: LEAVE BOTH for now - they keep parity
with how the established measure hazard is exercised (volume-caught), and neither is a soundness hole.
  - (4a) Shape A's watched-to-fail RED is a `harden`-VOLUME property (~1/200), so `make adversary` (150)
    rarely hits it. A "focused-entry" generator mode (make `entry` trivially provable when a nested lie is
    planted) would raise the hit-rate so the teeth bite at default volume. Cost: breaks parity, adds a
    special case to the generator.
  - (4b) Shape B's watched-to-fail is STUB-witnessed (a forced proof over a disordered tree), not fuzzed
    under a checker regression - a `bst` proof has no clean one-line gate like the declared-result VC. A
    real bst regression (a `LARK_REGRESS_*` switch that lets a disordered tree prove) would fuzz it
    properly. Cost: a bespoke, more invasive injection than (4a).
**[NEW 2026-07-16 - BOOK-SIDE, blocks writing Part III] Curate the refinement strand into `repo/prove/`.**
`repo/prove/` holds only `lark-formal` + `lcore`; the checker fork (`08/src`), the 75 fixtures
(`prove/`), and the 8 harnesses (`08/tests/`) exist only in the working repo while book ch16-18 cite
them. The book's `checkpaths.py` already refuses prose cites of the missing paths (bit once this
session). Recorded in `book/chapters/appendix_repo.tex`.**

**V3-SIGMA-2 - the σ-FUSION PILE, WEAKEN-SUBST COMMUTATION `GenCancel`, CLOSED AT 0 OK
(2026-07-16, after V3-SIGMA-1; `formal/proof/lark/lark-subst.lcore` +6 defs; green;
uncommitted).** The big brick - the one piece that needs `indrec Expr`. Proves
`sub_open (ins a n g) t (wk a g t e n) d env = sub_open g t e d (del a n g d env)`:
substituting into a weakened term = substituting into the original under the env with the
inserted entry deleted. Landed three supporting pieces first, each probe-first in the
scratchpad then green in the file:
  - **`ap`/`trans`/`ap2`/`ap3`** - a generic J-based Id-congruence toolkit (lift an equality
    under a 1/2/3-ary function; compose two equalities). One-liners over `J`; compute to
    `refl` on `refl` inputs. First reusable congruence helpers in the lark files (previously
    only bespoke `coe_e`/`step_coe` in lark-refine). ap2/ap3 are `trans`+`ap` compositions.
  - **`del_wk`** - `del` commutes with `weaken_semctx_d`:
    `del a n g (ext a1 d) (weaken_semctx_d a1 d (ins a n g) env) = weaken_semctx_d a1 d g (del a n g d env)`.
    Needed because the ELam body weakens the env on BOTH sides of the goal, and I must
    reconcile "delete-then-weaken" with "weaken-then-delete". `natrec` on n + `indrec Ctx`
    on g: refl at zero and (succ,empty); `ap` of the natrec-IH under the pair at (succ,ext).
  - **`GenCancel`** - `indrec Expr` on e, 10 branches: literals = `refl`; **EVar = `sdl`**
    (V3-SIGMA-1, on the nose); **EApp = `ap2`** of the two sub-IHs under `EApp d a b`;
    **EIf = `ap3`**; **ELam** = `ap (ELam d a b)` of a `trans` chaining (body-IH at cutoff
    `succ n`, env = `(EVar here, weaken env)`) with (`ap` of `del_wk` swapping the env tail);
    **ELet** = `trans` of (body-IH at `succ n`, env head = the weakened value) with
    (`ap` of the value-IH `ihv` in the env head) - note sub_open INLINES let, so its case
    substitutes the value into the env rather than emitting an `ELet` node.
Load-bearing detail banked: for ELam, `del a (succ n)(ext a1 g1) d (h, W)` computes
DEFINITIONALLY to `(h, del a n g1 d W)` [del's succ/ext clause], so the body-IH's RHS lines
up without transport and only the env TAIL needs `del_wk`. WATCHED-TO-COMPUTE: 6 ground-closed
smokes (literal, id-λ, app of id, let, if, var at cutoff `succ zero`) all normalise to `refl`
- every branch actually fires and reduces, not just typechecks opaquely. natrec-scrutinee
lesson bit AGAIN (`del_wk` first failed "unbound variable 'n'" - the outer `natrec` had no
`\n.` binder; same shape as the `sdl` "unexpected char ':'" miss). Scratchpad: probe_ap /
probe_delwk / probe_gencancel / probe_gc_smokes (all pass). Green bar
`make -C formal/proof check` = OK 5 files, 0 errors. NEXT: brick (3) - instantiate GenCancel
at n=0, assemble the fusion equation, then RT_Lam/RT_Let in HasR + their `fund` cases.

**V3-SIGMA-1 - the σ-FUSION PILE, Var/ENVIRONMENT LAYER, CLOSED AT 0 OK
(2026-07-16, after V3-WK0; `formal/proof/lark/lark-subst.lcore` +3 lemmas; green at each
step; uncommitted).** With `wk0` inductable (V3-WK0), the substitution lemma is now a grind
up a stack of small commutation facts. Landed the whole Var/environment layer - the pieces
that do NOT need `indrec Expr` - each refl-in-base + IH-in-step, NO J:
  - **`wk_lookup`** - looking a variable up in a weakened environment = weakening the entry
    you'd have looked up: `sem_lookup_d (ext a d) g t v (weaken_semctx_d a d g env)
    = wk0 a d t (sem_lookup_d d g t v env)`. `indrec Var`: here-case both sides reduce to
    `wk0 a d t (fst env)` (refl); there-case is the IH at the tail on the nose. Key reason
    it's clean: `weaken_semctx_d` changes only the OUTPUT context (d→ext a d), so the source
    variable is looked up UNCHANGED - no index refinement.
  - **`del`** - delete the environment entry a front-inserted binder occupies at de Bruijn
    depth n: `SemCtx_d d (ins a n g) → SemCtx_d d g`. `natrec` on n (drop head at 0; keep-
    and-recurse in the tail at succ), succ case `indrec Ctx` on g - mirrors `ins`. Smokes:
    depth-0 drops the front binder, depth-1 the middle, both preserving the survivor entry.
  - **`sdl`** - shift/del/lookup cancellation, the Var case of the coming big induction:
    `sem_lookup_d d (ins a n g) t (shift a g t v n) env = sem_lookup_d d g t v (del a n g d env)`.
    `indrec Var` with an inner `natrec` on the cutoff: refl in both here sub-cases and the
    there/zero sub-case; the Var-IH at cutoff m in there/succ. (Bug caught + fixed: both
    natrecs were written without their scrutinee - `\n. natrec ... n`, not bare `natrec ...`;
    the parser reported "unexpected char ':'" at the ascription that followed.)
These three discharge every Var/env obligation of the eventual GenCancel. REMAINING is the
`indrec Expr` body (brick 2b) + fusion assembly (brick 3) - see NEXT. Scratchpad:
probe_wklookup / probe_del / probe_sdl.

**V3-WK0 - PITCH 2's ENABLING RUNG: kernel `weaken` RETIRED, weakening REBUILT
IN LCORE, CLOSED AT 0 OK (2026-07-16, night; `formal/proof/lark/lark-subst.lcore` +~55
lines - `ins`/`shift`/`wk`/`wk0` + rebase + agreement smokes; nothing else touched;
uncommitted).** Pitch 2's ratified first step was "probe what `weaken` gets stuck on in
eval.c - kernel equations vs. an induction over Expr." The probe answered decisively and
the fix followed.
  - **THE DIAGNOSIS (probe_weaken.lcore).** The kernel primitive `weaken a g t : Expr g t
    → Expr (ext a g) t` (eval.c `weaken_expr_val`) is fine on a fully-concrete tree and
    goes cleanly STUCK on a top-level neutral (SP_WEAKEN). But on a CONSTRUCTOR WITH
    NEUTRAL CHILDREN - exactly the shape an `indrec Expr` case hands you - it `exit(1)`s
    (`weaken_expr_val: expected Expr VL_INDCON`). So it can never be the subject of an
    induction: the substitution lemma was blocked at the primitive, not at the proof.
  - **THE FIX (probe_wk.lcore → the file).** Rebuilt weakening IN lcore with an explicit
    Nat cutoff, so the old blocker (ext-commutativity not definitional) dissolves:
    `ins a n g` inserts `a` at depth n and COMPUTES - `ins a zero g ≡ ext a g` on any g
    (even neutral), `ins a (succ m) (ext s g) ≡ ext s (ins a m g)` on neutral tail/m
    (the succ case rides the OUTER natrec ih, not the indrec Ctx one - that is what makes
    the second equation definitional). `shift` (de Bruijn shift by indrec Var, natrec on
    the cutoff) and `wk` (indrec Expr; ELam/ELet fire the IH at `succ n`, and
    `ins a (succ n) (ext a1 g) ≡ ext a1 (ins a n g)` lands the goal on the nose).
    `wk0 = \...wk ... zero` has the KERNEL primitive's exact type - a drop-in.
  - **THE REBASE.** `weaken_semctx_d` swapped `weaken a d t (fst e)` → `wk0 a d t (fst e)`
    (same arg order); `sub_open`'s ELam case reaches weakening only through
    `weaken_semctx_d`, so this one swap takes the whole `sub_ground` path off the kernel
    primitive. `sub_ground`, and thus StepBeta/StepLetBeta's contractum, now route through
    inductive weakening. TRUSTED BASE SHRINKS: `weaken` is no longer proof-critical.
  - **A LATENT KERNEL QUIRK surfaced.** The refl-agreement smoke passes on a payload-only
    tree (`wk0` ≡ `weaken`), but on the Var case they DIVERGE: front-insert must send
    index 0 → index 1, i.e. `here empty TBool ↦ there (ext TBool empty) TBool TInt (here...)`;
    `wk0`/`shift` give exactly that, while the kernel `weaken` prints a `there`-node
    carrying the WRONG sub-context (`empty`). `wk0` is the correct de Bruijn semantics;
    the smoke keeps `wk0`'s answer and checks its own typing rather than asserting a false
    agreement. (This never bit Pitch 1: `weaken_semctx_d` was defined but UNUSED - no fund
    case invoked it until Lam/Let, which don't exist yet.)
  - **VERIFIED:** `make -C formal/proof check` → OK: 5 files, 0 errors, before and after.
  - **WHY THIS IS ITS OWN RUNG (ratified with Set, "bank wk0 rung, then grind").** The
    rebase is the *precondition* that makes the substitution lemma provable AT ALL; the
    lemma itself (identity-subst → subst-weaken commutation → the two-substitution FUSION
    → RT_Lam/RT_Let) is the classic autosubst pile, large in raw lcore, and is the NEXT
    rung. Banking here gives a clean green checkpoint before that grind. See CURRENT
    POSITION for the brick order.**

**V3-FUND - THE FUNDAMENTAL LEMMA, PITCH 1 OF THE SUMMIT, CLOSED AT 0 OK
(2026-07-16, night; `formal/proof/lark/lark-refine.lcore` +~160 lines - budget arithmetic,
congruence lifts, refined contexts, `HasR`, `fund`, smokes; nothing else touched;
uncommitted).** The statement: `fund : HasR g rg t r e → Π env. GoodEnv g rg env →
Σk. SemE t r k (e[env])` - every refined-typing derivation lands in the semantic relation.
The existential budget is the inert-index decision carried through: fund PRODUCES the k.
  - **THE TWO-PITCH DECISION (ratified with Set before writing): Pitch 1 has NO RT_Lam
    and NO RT_Let.** Both bottom out at the SUBSTITUTION LEMMA - RT_Lam's β-redex needs
    `sub_ground (weaken e) (w, star) = e`, a fact about the kernel PRIMITIVE `weaken`
    (eval.c), stuck on neutral subterms, cutoff not exposed; RT_Let hits sub_open's
    CBN-at-substitution cousin. Three options were priced (carry the equation as a rule
    premise - dies at abstract env; closure-style SemV - moves the same equation to the
    App case; kernel equations for weaken - real work, its own rung). Named, priced,
    deferred - not fudged. Higher-order USE is still proven: functions enter through
    GoodEnv hypotheses, and RT_App eliminates them.
  - **The judgment: `HasR : Π(g)(rg : RCtx g)(t)(r : RTy t). Expr g t → Type`** - an
    extrinsic derivation riding the intrinsic Expr, exactly refine.py's second pass as a
    data type. RT_Int demands payload EVIDENCE `IsTrue (p n)` (selfification modeled the
    way SubBase models the solver); RT_Bool rides the new trivial `RBool` rider (RTy grew
    a third constructor; SemV pins the value to `ELitBool b` - exactly what RT_If needs);
    RT_Var's rider IS `rlookup g t v rg`, definitionally - no side relation, no Id;
    RT_App demands the argument's refinement EXACTLY (subsumption is a RULE, not
    implicit - control c3 checks this); RT_If takes both branches at the same r (NOT
    path-sensitive - named in scope note (d)); RT_Sub is the calculus's `Sub` as premise.
  - **Refined contexts by the telescope trick again:** `RCtx` puts an RTy rider on every
    Γ entry, `GoodEnv g rg env` says every env entry is SemV-good at its rider, and both
    lookups (`rlookup`, `glookup`) are FUNCTIONS whose fst/snd compute - glookup alone
    is the whole Var case.
  - **The technical meat: congruence lifts through the CBV frames.** indrec StepsN
    abstracts the stepping type t1, but the frames pin it (TFn a b / TBool) - solved by
    the le_inv computed-motive trick LIFTED FROM Nat TO Ty: motives quantify an
    `Id Ty t1 (TFn a b)` (resp. TBool) and coerce endpoints along it (`coe_e`/`step_coe`,
    J-based); at every use site the Id is refl and the coercions COMPUTE AWAY. lift_app2
    needs no coercion (its frame is parametric in the stepping type) but carries the
    function's IsVal - StepApp2 demands it, CBV order made visible. Budgets concatenate:
    `plus`, `le_plus_mono`, `steps_append`; the If case J-transports the goal along
    RBool's pinning and boolrec selects the branch certificate (StepIfTrue/False costs
    the one step: succ/LeS/SN_cons).
  - **The smokes COMPUTE.** `fund_lit` (literal 2 at {ge2}, empty context) normalizes to
    the canonical zero-step certificate. The showcase `f (if true then 2 else 3)` with
    `f : {ge2}→{ge2}` a GoodEnv hypothesis (idInt) fires EVERY rule - Var (rlookup
    computes the rider), Bool, Int (payload evidence by computation), If (J + boolrec),
    App (both lifts + the applicative clause + budget arithmetic), Sub (weakens the
    result to {ge1}) - and normalizes to the honest 2-step certificate: k=2, LeS LeS LeZ,
    `id (if true 2 3) → id 2 → 2`, payload good at the WEAKENED predicate.
  - **4/4 negative controls refused in LOADED pipes** (a sibling success visible in each
    transcript): c1 payload forge (`star` at `IsTrue (ge2 1)` → inferred Unit, expected
    Empty); c2 rider forge (RT_Var ascribed at a rider rlookup doesn't compute); c3
    no-implicit-subsumption (an {ge1} argument fed to RT_App demanding {ge2}); c4 SemV
    forge (the payload-evidence seam of the relation itself).
  - **Two transcription bugs caught before the checker saw them** (a full-width comma
    `,` and a misplaced paren in the App cert - found by a per-line paren-balance
    script, then a comma-depth trace; both mechanical, neither semantic).
  - Green bar: `make -C formal/proof check` → OK: 5 files, 0 errors. PROVE.md ledger
    flipped (V3-FUND line + NEXT rewritten); proof README table row updated.**

**V3-TFN - FUNCTION-TYPE REFINEMENTS, THE RELATION GOES RECURSIVE, CLOSED AT 0 OK
(2026-07-16, late night; `formal/proof/lark/lark-refine.lcore` rewritten in its relation
half - IsTrue/Le/StepsN and the whole Le arsenal verbatim; `08/src` and the solver
untouched; uncommitted).** The decided rung after V3-MONO: `{x:A|p} → {v:B|q}`.
  - **THE FORK, RATIFIED BEFORE WRITING (with Set, same day): the INDEX IS INERT INSIDE
    SemV AT THIS RUNG.** The plan's phrase "where the step index earns its keep"
    over-promised: with no recursion in the term language yet, NO discipline is
    load-bearing - and the spine's ∃-form SemE ("reaches a good value WITHIN k") actively
    fights a budgeted arrow clause: `Π j ≤ k` over the application is FALSE at j = 0 (β
    alone costs a step while the domain hypothesis is satisfiable at any index). So the
    arrow clause carries an EXISTENTIAL budget (Σ k'), SemV never consults k, and the
    spine's Le/SemE machinery survives verbatim. The index becomes load-bearing at the
    DESCEND rung, when general recursion forces SemV to recurse on k and E flips to the
    ∀/safety form - that rebuild is named in the file header, not smuggled. (The rejected
    alternative - flip to ∀/safety NOW - was priced: Step-INVERSION machinery for every
    concrete smoke, and the index still not truly earning its keep until descend.)
  - **ERASURE IS THE INDEX:** `RTy : Ty → Type` (`RInt : (Nat → Bool) → RTy TInt`;
    `RFn : RTy a → RTy b → RTy (TFn a b)`) - a refined type IS its erased type plus
    riders, V1's "a mention is not a use" as the shape of the encoding. `Sub t r r'`
    relates refinements of the SAME erasure definitionally: no transport anywhere, and
    mismatched erasures are ill-INDEXED before any predicate is consulted (control c4).
  - **THE RELATION GOES RECURSIVE:** `SemV` by `indrec RTy` - LARGE elimination on an
    indexed family (motive lands in Type; the SemCtx precedent held). `RInt` = the spine's
    payload triple; `RFn` = `IsVal f` × (good args → the application reaches, under Σ k',
    a value good at the codomain) - the IHs iha/ihb ARE the sub-relations. The knot is
    tied WITHOUT mutual recursion: `SemEV` (the E-wrapper, generic in the value relation)
    is defined first, and the RFn case applies it to the codomain IH.
  - **Sub GROWS SubFn** (domain premise FLIPPED: `Sub a ra' ra`), and `sub_sound_v`'s
    SubFn case is the variance flip made computational - the domain IH runs BACKWARD
    (fed to the clause's hypothesis), the codomain IH FORWARD (lifted through `sem_ev_imp`,
    the spine's sem_e_imp generalized). E-level `sub_sound` = one wrapper call.
    `sem_e_mono` restated generic in the value relation - covers arrows for free.
  - **PROBED FIRST (house rule, scratchpad clones, passed first run):** indrec large elim
    on an indexed family with IHs [ok]; definitional unfolding at constructors [ok]; and
    two-premise IH ordering = INTERLEAVED (`\sd. \ihd. \sc. \ihc.` - read off sub_open's
    EApp case before probing). One lexer landmine found: **`W` is a RESERVED TOKEN in
    lcore's parser** (parse.c:314, the W-type) - a bare parse error, not a type error;
    sem_ev_imp's second relation is named Q. **Fixed the DIAGNOSTIC same night** (`W`
    followed by anything but `(` is always an error in this grammar, so the branch now
    SAYS "'W' is reserved (the W-type binder...)" instead of the misdirecting bare
    expected-'(' - parse.c only, checker semantics untouched; kernel self-tests 339/339,
    check green; renaming the keyword was rejected: W-types are wired through
    term.h/eval.c/check.c and exercised by `:t`).
  - **SMOKES COMPUTE, NOT JUST TYPECHECK:** `idInt` at {ge2}→{ge2} - β fires via
    StepBeta, `sub_ground` computes the body (EVar here) to the NEUTRAL argument, the
    domain hypothesis is REUSED verbatim as the result witness (no J, no transport);
    `constTwo` at {ge1}→{ge2} carried across `SubFn imp21 imp21` to {ge2}→{ge1} - ONE
    implication exercising BOTH variances; `use_id`/`use_c2w` normalize to full canonical
    certificates (StepBeta visible, star at the rewritten payload); plus E-level carry and
    mono∘sub_sound composition at the arrow.
  - **WATCHED TO FAIL (4/4 refused, loaded pipe - imp22 checked first, so not vacuous;
    each at its own seam):** c1 domain-variance forged (inferred `Sub (RInt ge2) (RInt
    ge1)`, expected the FLIP - contravariance is load-bearing) - c2 IsVal forged for a
    non-value (ValLam pins its subject to an ELam; an EIf cannot borrow it) - c3 codomain
    promise forged (idInt at {ge1}→{ge2}: handing back the ge1-evidence where ge2 is
    demanded is refused) - c4 erasure seam (`Sub TInt rge2 rc12` ill-indexed: `RTy (TFn
    TInt TInt)` where `RTy TInt` expected).
  - **VERIFIED:** `make -C formal/proof check` → `OK: 5 files, 0 errors`.
  - **NEXT:** the fundamental lemma (the summit) - a refined typing judgment, and every
    checked term lands in the relation.

**V3-MONO - MONOTONICITY IN THE STEP BUDGET, CLOSED AT 0 OK (2026-07-16, night;
`formal/proof/` only - one section appended to `lark-refine.lcore`, README table row updated;
uncommitted).** The decided prerequisite rung, done: **`sem_e_mono : Le k k' → SemE k p e →
SemE k' p e`** - the index bookkeeping the TFn rung will lean on.
  - **THE DIRECTION, NAMED (the file header says it too):** for THIS relation (`SemE k` =
    "reaches a good value within k steps") monotonicity runs UPWARD - budget WIDENING - not the
    textbook "downward closure." Downward closure of the VALUE relation is trivial at the spine
    (`SemV` never mentions k) and becomes a real lemma only when TFn refinements give `SemV` its
    index. The seam is named so the TFn rung finds it prepared.
  - **THE REAL CONTENT IS `le_trans`, AND IT NEEDED REAL MACHINERY:** lcore's `indrec` does no
    dependent pattern matching, so inverting `Le (succ m) c` is not free. Technique (probed on a
    `PLe` clone in scratch BEFORE touching the file; passed first run): **a natrec-COMPUTED
    motive** - `LeInvT a b` unfolds by the shape of `a` (`zero → Unit`; `succ m → Σ k'.
    Id c (succ k') × Le m k'`), so each `indrec Le` case lands at its own already-computed type
    with no index refinement (the `IsTrue` boolrec trick, applied to an indexed family); the
    returned `Id` is then consumed by **`J`** (first use of lcore's J eliminator in the Lark
    proofs - motive inferred so it needs annotation; base is checked so a bare `\x. x` passes).
    `le_trans` = indrec on the FIRST derivation; LeS case: invert, step down (IH), rebuild with
    LeS, J-transport the endpoint back. Plus `le_refl` (natrec) as TFn ammunition.
  - **IT COMPUTES, NOT JUST TYPECHECKS:** `le_trans` on concrete derivations normalises to the
    canonical `LeS zero 2 (LeZ 2)`; the widened `seme_p_w` shows the REWRITTEN certificate
    `LeS zero 1 (LeZ 1) : Le 1 2` inline in the tuple; `sub_sound ∘ sem_e_mono` composes
    (widen budget 1→2, then cross ge2 <: ge1) with the full normal form visible.
  - **WATCHED TO FAIL (4/4 refused, each at the right seam):** budget NARROWING with a bogus
    certificate (demands `Le 2 1`) - `Le 2 1` forged directly (premise demands `Le 1 0`) -
    a FORGED INVERSION witness (the `Id` refuses to say `2 = succ zero`) - `le_trans` with
    endpoints swapped (demands `Le 3 1`). Caveat from the first attempt: the controls initially
    "failed" against an EMPTY pipe (zsh doesn't word-split `$FILES` - `cat` found nothing, so
    every control was refused as merely unbound); vacuous refusals, rerun against the loaded
    pipe before being counted.
  - **VERIFIED:** `make -C formal/proof check` → `OK: 5 files, 0 errors` (before and after the
    README row edit).

**V3 SPINE - SUBTYPING ⇒ SEMANTIC IMPLICATION, CLOSED AT 0 OK (2026-07-16, evening;
`formal/proof/` only - `08/src` and the solver untouched; uncommitted).** V3 as ratified in
`PROVE.md` §4 (calculus not solver/code; step-indexed over the existing metatheory; spine first).
  - **STEP ZERO WAS A PRECONDITION, NOT THE LEMMA:** `ELitInt` carried NO payload
    (`Π(g : Ctx). Expr g TInt` - one int literal in the whole encoding, while `ELitBool` carries its
    `b`). A refinement `{v:Int|p}` over that encoding predicates over a single token - every spine
    lemma would have closed VACUOUSLY. The false-spine trap, caught before writing a line. Fix:
    `ELitInt : Π(g : Ctx). Π(n : Nat). Expr g TInt`, threaded through all four closed files
    (`dummy_expr`, `sub_open`'s ELitInt case, `ValInt : Π(n : Nat). ...`, every smoke test - if-branch
    payloads now DISTINCT (then=1, else=2) so branch choice is visible in outputs). Kernel `weaken`
    needed NO change: `weaken_expr_val` dispatches by ctor name and copies non-context args through -
    the path `ELitBool` already exercises; verified by OBSERVATION (`:i wk1` → payload intact, context
    shifted). All four files re-closed at 0 before the spine was begun.
  - **THE SPINE (`lark-refine.lcore`, new):** `IsTrue` (Bool→Type via boolrec) - `Le` (budget order) -
    `StepsN` (step-COUNTED reduction - `Steps` with the count the index measures) - `SemV p v`
    (v pinned to `ELitInt n` by `Id`, payload satisfies p) - `SemE k p e` (reaches a SemV-good value
    in j ≤ k steps) - `Sub` (the CALCULUS object: derivations indexed by two `Nat → Bool` predicates;
    the `SubBase` leaf DEMANDS the implication evidence - the model of "the solver discharged p⇒q") -
    **`sub_sound : Sub p q → Π k e. SemE k p e → SemE k q e`** by `indrec Sub`, the index bookkeeping
    passing through untouched while the value predicate is rewritten at the payload. Smoke: ge2 <: ge1
    end-to-end on `if true then 2 else 1` (a term that STEPS), both `StepsN` and both `Le` ctors
    exercised; `:i seme_q` shows the lemma COMPUTED the ge1-witness (nested-natrec type → single-natrec
    type; full normal form visible). lcore facts that shaped the file: natrec's step arg is INFERRED
    (needs full annotation) while base/boolrec cases are CHECKED; function-typed data indices and
    Nat-indexed families both work (probed before writing).
  - **WATCHED TO FAIL (4/4 refused):** reversed subtyping (`SubBase ge1 ge2 imp21`) - a false
    implication (ge1⇒ge2 via `star`) - a lying value witness (payload 1 against ge2) - a BUDGET
    VIOLATION (the 1-step reduction offered at k=0) - the last is the proof the step index is
    load-bearing at the spine already, not decorative.
  - **NAMED SPINE SIMPLIFICATIONS (in the file header):** payloads are Nat not ℤ; predicates are
    SHALLOW (`Nat → Bool`, no syntactic predicate language - `imp` models the solver's verdict);
    one rule, one lemma. The V3 boundaries stand: this proves the RULES; `refine.py` is not mentioned.
  - **VERIFIED:** full five-file pipe → 0 errors; `formal/proof/README.md` table + run command updated.
  - **ADDENDUM (same evening) - GREEN BAR + THE ORDER DECIDED.** New `formal/proof/Makefile`:
    `make check` (all five files) / `make meta` (the four Phase-5b files) / `make repl`; builds lcore
    via sub-make. The point is the FAIL: lcore is a REPL that prints `type error: ...` and exits 0, so
    a bare pipe goes green on a broken proof - the target greps the transcript (`error|failed|cannot|
    not a function`) and exits 1 with the offending lines. Watched to fail: an ill-typed scratch file
    → FAIL with the exact `type error` lines, exit 2; real files → `OK: 5 files, 0 errors`. README run
    section now leads with `make check`. **NEXT (decided with Set): monotonicity/downward-closure in k
    FIRST (small, self-contained, a prerequisite), THEN TFn refinements; the fundamental lemma is the
    summit, after both.**

**RECORDS - THE DUPLICATION TRIMMED OK (2026-07-16; `PROVE.md` + `LOG.md` only, no code, no content
lost).** Set's observation: proofs and plans were hitting BOTH files and it was getting confusing -
merge? Decision: NO MERGE (LOG covers five axes; the plan's ladder/guardrails are consulted by topic,
not date) - the confusion was a DIVISION-OF-LABOR failure: `PROVE.md`'s Status block had grown into a
~190-line second log, and this file's top pointer RETOLD rungs instead of pointing. The trim, every cut
verified against its dated entry here first: `PROVE.md` status narrative → a one-line-per-milestone
LEDGER (1291→~1135 lines); this file's top pointer → CURRENT POSITION + NEXT in 7 lines; the rule
written into both headers (*a story is written ONCE - in its dated LOG entry; the plan flips a status
line; the pointer points*). Honesty fix caught mid-trim: V2 is NOT "complete" - its HEADLINE is reached
(boundary #3) while V2.5 (mergesort) was never picked up and V2.6 was never a discrete rung; the §4
ladder now says so per rung (V2.4 OK as foundation+b+c1-5; V2.5 [paused] not picked up, reopen deliberately or
not at all; V2.6 ongoing-by-nature). Reading order after /clear, now encoded: LOG top pointer first,
then the active plan's ledger (`PROVE.md` while this axis runs). *(Same session, earlier: book companion
framing fixed - see the bullet in the BOOK entry below.)*

**BOOK - PART III RESTRUCTURED + HARVEST + THE DESTRUCTING-BST SECTION DRAFTED OK (2026-07-16;
`book/` only, no code change; compiles green through checkpaths/checkrefs/tectonic).** At Set's ask
(pause; see what the finished code can already give the book), a whole-book review against current
code state, then:
  - **ch16 SPLIT INTO THREE.** `ch16_refinement` keeps the checker report (opening rewritten from
    proposal to report tense; suite count corrected 5 pairs → 75 fixtures). NEW `ch17_adversary`
    ("What a Verifier May Not Do") = the epistemology: false-proof count corrected 8 → NINE with the
    ninth's story (lambda's parameter contract discharged at the call; found the day the generator
    learned refined lambdas) + the never-shipped #10 (naive `==` reroute through `_val_eq`, vetoed on
    the bench); watched-to-fail named as a discipline; RUNG (1) receipt (nested-measure shapes, third
    semantic oracle, named limits). NEW `ch18_measures` ("Measures and Trees") = ghost functions →
    nested match (Part B) → building bst (step 4) → DESTRUCTING bst (boundary #3) → cost of firing
    (O(n²) blunt vs O(n log n) demand-driven) → boundary ledger → "The horizon" (moved from ch16,
    refs adjusted). NEW `interlude3` ("The Equality Seam": Float and String/fn as one seam at opposite
    polarities). `main.tex` wired; note print chapter numbers run one ahead of file numbers
    (Introduction is Chapter 1 - pre-existing).
  - **HARVEST PASS across the rest:** ch12's dead blocker removed (OPTIMIZE closed at `f1dedfa9`);
    ch13 tense fixed ("no program specifications" is no longer true) + a FOURTH provable row (the
    verifier itself; three mountains) + the `cek.c` parity lesson under "Tests, and their ceiling";
    ch15 gains the forward arc (V3's logical relation stands ON the metatheory - load-bearing, not a
    trophy); introduction + appendix_method now CO-BILL the second method (adversarial: run-what-you-
    proved, watched-to-fail, invariants) beside differential testing; appendix_repo records the
    curation gap (backlog above); conclusion thread (iii) updated (the "yet" arrived mid-book);
    hardcoded `Chapter~NN` mentions → `\ref`.
  - **"Taking the tree apart" DRAFTED as finished prose** (ch18's centrepiece, same register as The
    horizon, while the reasoning is fresh): the wrong framing (no universal bound invariant - the
    logic's refusal was the finding) → the reformulation (extra-param `lt`/`gt`, single unguarded
    match, order handed back out at opaque binders) → demand-driven firing (three head shapes, `b`
    fixed) → both-direction fixtures + the swap refused 1-of-4 → watched-for-VACUITY (the firing
    cannot lie; the watch proves it load-bearing) → the closing beat (what crossed the boundary was a
    reformulation, not a stronger solver).
  - **COMPANION FRAMING FIXED (same day, follow-up):** Set stole no. 4's tex style into `main.tex` and
    the printed book's identity came with it - title page said "The Language Stack / Second edition"
    with no. 4's BoD/ISBN imprint. Restored: title page + `pdftitle` back to "Lark Builds Itself:
    Self-Hosting, Optimization, and Proof" with "A companion to Code Crafting no. 4" over it; verso's
    print imprint replaced by one line POINTING AT no. 4 (its ISBN as a citation, not an identity) above
    Set's own "Not for print. PDF only." block. `cover.tex` rewritten from no. 4's print SPREAD
    (back|spine|band|front, bleed, missing barcode png - didn't even build) to a FLAT front cover,
    180×230mm = main.pdf's page size so it can be prepended as page 1; palette/typography kept,
    woodlark anchored at the bottom; rendered and eyeballed. `Makefile`: `all: book cover`, new
    `cover.pdf` target, `clean` removes it; full `make clean && make` green.
  - **NEXT (book):** curate `repo/prove/`, then Part III chapters are writable; a full read-back of
    ch16-18 with Set before drafting more. **NEXT (code): unchanged - no rung queued; V3 spine / tighten
    teeth / stop, decide with Set.**

**RUNG (2) - THE DESTRUCTING BINARY SEARCH TREE OK (2026-07-16, committed 56c698e/c966b2a). BOUNDARY #3 CROSSED.
`refine.py` `measure_axioms` (the ONE src/ change - solver untouched byte-for-byte) + fixtures + adversary.
prove 75/0; full `make harden` exit 0; invariants I1-I6 green.**
THE REFRAME (do not lose this): the pointer used to say "give `minv`/`maxv` DECLARED BOUND INVARIANTS." That
was WRONG - a declared measure result must hold of EVERY tree, and `minv(t) <= maxv(t)` is false of a
disordered one, so there is no universal bound invariant to declare. The real way past fire-at-concrete-
subfields: reformulate `bst` as a SINGLE match on the root and push "every value in the left child is below
the root" into an EXTRA-PARAMETER measure - `lt(t,b)` / `gt(t,b)` (every value below/above `b`), with
`bst(Node(l,x,r)) <=> lt(l,x) and gt(r,x) and bst(l) and bst(r)`. Now `bst`'s equation is UNGUARDED, so it
fires on `Node(l,x,r)` even when `l,x,r` are OPAQUE match binders, and HANDS OUT `bst(l)`, `bst(r)`,
`lt(l,x)`, `gt(r,x)` - the order facts a consumer reads back out. (Discovered in the spike: single-match
measures ALREADY destruct opaque trees - the nested two-deep `bst` of rung/35 was the specific blocker, not
destructing in general. A binder-name collision with the internal value binder `$v` was the pivotal
red herring; renaming binders fixed it.)
THE ONE NEW CHECKER CAPABILITY - DEMAND-DRIVEN FIRING (`measure_axioms`, fully rewritten): an extra-param
measure's equation is about an APPLICATION (`b` lives only there), so unlike a unary measure it can't fire on
the bare constructor. A demand `lt(c,b)` is discharged by the SHAPE of its first arg: (a) CONSTRUCTOR-HEADED
`lt(Node..,b)` → fire the arm, follow its own recursive demands `lt(l,b)`/`lt(r,b)` DOWN the structure with
`b` FIXED (never crossing one node's bound with another's - that is the O(n²) an all-pairs instantiation
suffers, avoided by following structure); (b) OPAQUE-HEADED `lt(lc,b)`, `lc` a binder → stays an ATOM, no
equation, sound silence (the reason a single-match bst comes apart); (c) VARIABLE-HEADED → bridge to
constructor terms by SORT (the congruence the unary walk gets free). Fixpoint worklist (`while work`). Cost
profiled: O(n log n) balanced (13/33/81/193 emitted for n=3/7/15/31) vs the blunt all-pairs prototype's O(n²)
(29/121/497/2017); degenerate right-spine is O(n²) but intrinsic and fast (n=63 ≈ 0.2s). **Set had asked to
confirm-by-profiling I hadn't just blown up tree volume by adding an extra param - the blunt version HAD
(O(n²)), which drove the demand-driven design.**
FIXTURES (`prove/36_bstdestruct_{safe,unsafe}.lark`): safe proves BOTH directions - `build` (constructed tree
is a bst, building, as 35) + `leftsub`/`descend` (from an OPAQUE `bst(t)`, the left child is a bst, read out
and recursed on), 6 obligations, runs → `3\n1`. Unsafe lies in the DESTRUCTING direction 35 could not attempt:
`swap` claims a bst for `Node(r,x,l)`, whose obligation needs `lt(r,x)` = the negation of the handed-out
`gt(r,x)` → 1 of 4 unproved. Registered in `prove_difftest.py` EXPECT + RUNS; 35's nested fixtures KEPT (they
document the building-only nested approach + the boundary now crossed).
ADVERSARY (`tests/adversary.py`): new `dbst_decls` single-match shape (mutually exclusive with the nested
`bst_decls` - both define `measure bst`/`type Tree`), an INDEPENDENT `eval_lt`/`eval_gt`/`eval_dbst`
transcription feeding ORACLE 3, and a `dconsume` reading `gt(r,x)` out as a `100/(rv-x)` divisor - RUN teeth
on the destructing direction (the tooth the nested bst, having no divisor, could not have). Genuine dbst
programs prove at scale (3-10 per 800 across seeds, on par with nested's 6-7); default `make adversary` (150)
rarely lands one (same volume property as Shape A's 4a gap). 0 false proofs.
WATCHED TO FAIL: the firing is SOUND by construction (it only emits true measure equations), and the unsafe
fixture supplies the false-CLAIM teeth; so the watch-to-fail here proves the firing is LOAD-BEARING, not
vacuous - disabling `fire_extra` (early `return`) took `36_safe` from 0→2 obligations failing (exactly the
two destructing ones) while `35_bst` stayed 0 (inert, no extra params). Restored byte-for-byte, clean.
ALSO THIS SESSION (a detour, at Set's ask): closed a `cek.c` PARITY GAP. The `08/` fork's `cek.py` had gained
`min`/`max` Int builtins (for the minmax fixtures) but `cek.c` (the C/native backend, byte-identical to
frozen `07/` until now, in NO test/harden target) had not - the two runtimes silently disagreed on those two
builtins. Added `min`/`max` to `cek.c` (`builtin_arity` + `apply_builtin_n` + top-env reg, mirroring `cek.py`),
verified the compiled path (emit_c_ast → cc → binary) now matches the interpreter on `25_minimum`→50,
`28_minmax`→20, and a hand-written `min`/`max` program. Rationale: the codebase is destined to be pedagogical,
so a dormant-but-diverging runtime shouldn't sit in the corner. `07/` left frozen; parity is within `08/`.
LIMITS (named, optional): dbst run teeth need a `rv==x` disordered tree wrongly proved to bite ORACLE 1 -
narrow; ORACLE 3 (semantic) is the primary net and catches every disordered-proved tree. Same volume caveat
as 4a: the teeth fire at 800 cases, not 150.**

**RUNG (1) - THE ADVERSARY NOW SPEAKS A NESTED MEASURE OK (2026-07-16, committed 56c698e/c966b2a). `tests/adversary.py`
ONLY - not one line of `src/` changed. The Part B / step-4 mechanism (flattened `Guard` chains,
cross-measure refs, 2-deep nested matches) was fixture-pinned but never FUZZED; now it is. prove still
73/0, invariants I1-I6 green.**
WHAT THE GENERATOR LEARNED: a `Tree` ADT emitted once (`_tree_type` + flag), then two shapes, each the
fixture-34/35 consumption pattern (a param contract + a CONCRETE generator-computed literal tree at the
call - NOT a companion `fn f(t):{v==m(t)}`, which recurses over an opaque subfield and the guard
declines: nested equations fire only at concrete subfields).
  - **SHAPE A - the run-oracle teeth.** `nested_measure_decls()` emits `rd` (right-spine depth, a nested
    `match r with Leaf | Node` measure) with a declared result WEIGHTED TOWARD A LIE (`{v>=1}`/`{v>0}`/
    `{v!=0}` while `cl`/`cd` can make the true depth `0`), consumed by `fn nuse(t:Tree, d:{v==rd(t)}):Int
    = 100/d`. `main` calls `nuse(<concrete tree>, <TRUE rd>)` - the call obligation `d==rd(t)` fires at
    the concrete subfields and holds; the only thing propping up `100/d` is `rd`'s declared result being
    honest. This mirrors measure_decls' V2.3 lie hazard, now over a NESTED measure.
  - **SHAPE B - the semantic-oracle teeth (no divisor).** `bst_decls()` emits `maxv`/`minv` (sentinel-Leaf
    arms) + the 2-deep `bst` Bool measure + `fn buse(t:{v:Tree|bst(v)}):Int`. `main` passes half genuine
    search trees (`ordered_struct`, checker should PROVE) and half random (mostly disordered, should
    REJECT). A proved program certifying a disordered tree crashes NOTHING - so a THIRD oracle was added
    to `main()`: the generator computes `eval_bst`/`eval_rd`/`eval_maxv`/`eval_minv` in Python (exact
    transcriptions of the arms), and a PROVED-but-model-false verdict is recorded as a false proof.
    Building-direction only, matching step 4's boundary.
  - **WATCHED TO FAIL - and it did.** Injected regression in `refine.py` (`_prove_measure_result`'s VC
    append gated behind `LARK_REGRESS_SKIP_MEASURE_RET`, `continue` = trust the declared result unproved).
    Un-regressed the hit rate is ~1/200 detonating-lie-that-fully-proves (the same volume-caught bar the
    established measure hazard sits at - both share entry's fate), so it takes volume: seed-5/**800** under
    regression → **[FAIL] 4 FALSE PROOFS, all `ZeroDivisionError`** (`nuse(Leaf, 0)`, `rd` declared nonzero,
    entry provable). `refine.py` restored byte-for-byte (`git checkout`); the SAME seed-5/800 un-regressed
    → **adversary clean**, proved 49→34 (the ~15 lie-dependent programs, the 4 detonators among them, now
    correctly UNPROVED). Shape B's semantic-oracle teeth were witnessed separately earlier (a stubbed-proof
    over a disordered tree → "false bst proof", exit 1) - a bst has no divisor, so only oracle-3 sees it.
  - **ALL GREEN** - full `make harden` exit 0 post-change (drift clean, conservative 45×2, prove 73/0 incl.
    34/35 both directions, robust 45/0/0, fuzz 3000 cases 0-unsound, adversary 150/11 clean, torture 14/14,
    invariants I1-I6 incl. I6 28 guards 0 out of scope). Three oracles now guard every proved program: run
    (no crash), erasure (refined ≡ stripped), semantic (model-true). No new false proof un-regressed - the
    nested mechanism holds.
  - **KNOWN LIMITS (do not over-trust the teeth):** (a) Shape A's watched-to-fail RED is a `harden`-VOLUME
    property, not a default-target one - the fully-provable detonating lie lands at ~1/200, so `make
    adversary` (150) will rarely hit the exact red (it took 800); the default run's value is the CONTINUOUS
    check that the honest checker false-proves NO nested-measure program, not a teeth demonstration. Same
    bar as the established measure hazard. (b) Shape B's watched-to-fail is STUB-witnessed, not fuzzed under
    a checker regression - a `bst` proof has no clean one-line gate like the declared-result VC, so oracle-3
    was shown live by forcing a proof by hand, not by a `LARK_REGRESS_*` switch. Asymmetry named, not a
    regression. Tightening either (a focused-entry generator mode for A; a real bst regression for B) is an
    OPTIONAL future item, deliberately not pursued to keep parity with the existing hazards.
  - **NEXT** - rung (2), the destructing / bound-invariant bst (BOUNDARY #3). Confirm scope with Set.**

**V2.4c STEP 4 - THE BINARY SEARCH TREE OK (2026-07-15, UNCOMMITTED). The invariant the whole
PROVE axis was pointed at, and it is PURE ASSEMBLY - NO new checker mechanism, NOT ONE line of
src/ changed. It is Part B's nested match (now TWO deep, on both children) + V2.4's Bool measure +
one thing Part B quietly already allowed: a measure body that MENTIONS ANOTHER measure. prove
71→73/0.**
`minv`/`maxv` (leftmost/rightmost value) are Part B measures with a SENTINEL Leaf arm (`0`) that is
never consulted, because `bst` only asks `maxv(l)`/`minv(r)` inside the arm where that child is
already a `Node`. `bst` is a Bool measure matching BOTH children (nested two deep) whose leaves
combine the ordering facts with the recursive calls - `maxv(l) < v and v < minv(r) and bst(l) and
bst(r)`. The cross-measure calls `maxv(l)`/`minv(r)` need no closure change: `l`/`r` are PHYSICAL
subterms of a built tree, so `measure_axioms`' single-pass walk reaches them for free (the same
reason Part B's `rdepth(Node(rl,rv,rr))` got its equation).
  - **PROVES THE BUILDING DIRECTION** - `prove/35_bst_{safe,unsafe}.lark`. Safe builds a six-node
    bst, `use` requires `{v:Tree|bst(v)}`, one obligation, all nested equations fire at the concrete
    subfields, runs → `3`. Mutant flips one inner value so the left subtree's max (9) exceeds the
    root (3); `bst`'s deepest arm asks `maxv(l)<v` = `9<3`, the whole `bst` resolves through the
    equivalences to false, the call owes a bst it cannot have → 1-of-1 unproved. (No detonation - a
    bst is a fact about ORDER, not a divisor - so the mutant is absent from RUNS; teeth = the build
    direction refuses to certify an out-of-order tree.)
  - **THE BOUNDARY, FOUND BY BUILDING IT** - the elegant DESTRUCTING teeth (23_boolmeasure's shape:
    a consumer READING order back out of an OPAQUE `bst(t)`) is BLOCKED by "fire at concrete
    subfields": over an opaque `Node(l,v,r)` the nested guards decline, so an abstract `bst(t)`
    yields NO usable order fact. To read order back out you need `minv`/`maxv` to carry declared
    LOWER/UPPER-BOUND invariants (`minv(t) <= root`, proved by induction) - a separate, larger rung.
    Documented in PROVE.md as a boundary beside ℤ-vs-32-bit, partial correctness, and the equality
    seam; NOT a regression. This is the honest edge of the concrete-subfields design.
  - **ALL GREEN** - harden exit 0: drift clean, conservative 90/0/0, solver 16/0, prove 73/0, robust
    45/0/0, fuzz 0-unsound over 3000 cases, adversary clean, torture 14/14 (incl. `mutual_measure`,
    which already exercised cross-measure recursion), invariants I1(4394 nodes, 0/0) I2(54/54)
    I3(2.00×) I4(18/0/0) I5(3/0) I6(28 nested guards, 0 out of scope).
  - **NEXT** - the destructing-direction bst (measure-invariant declared results) is the natural
    follow-on if wanted; and the adversary still cannot SPEAK a nested measure. Confirm with Set
    whether V2.4c is DONE here (step 3 A+B + step 4 all landed) or continues into the bound
    invariants.**

**V2.4c STEP 3 PART B - NESTED MATCH IN A MEASURE OK (2026-07-15, UNCOMMITTED). The move a
BST needs: a measure that looks at a CHILD's shape (a second `match`, on a FIELD of the one
already taken apart). `refine.py` only (checker; drift-EXTENDED); solver.py/pred.py/cek.py
UNTOUCHED - a measure is ghost, so it costs the runtime nothing. prove 69→71/0; new invariant I6.**
THE REPRESENTATION: a nested match FLATTENS to several `MArm`s sharing the outer `con`, each
carrying a chain of `Guard(var, con, binders, bsorts)` - one per inner step. `rdepth`'s three
equations become `rdepth(Leaf)==1`, `rdepth(Node(l,v,Leaf))==2` (guard r=Leaf),
`rdepth(Node(l,v,Node(rl,rv,rr)))==1+rdepth(Node(rl,rv,rr))` (guard r=Node). Six edits, all in
refine.py: a `Guard` dataclass + `guards` field on `MArm`; `_elab_measure` gutted into three
helpers (`_resolve_adt`, `_arm_binders`, `_elab_arms` with nested `do_match`/`do_body`/`emit_leaf`
that accumulate binders and guards along the path); `_instantiate` binds outer fields then walks
the guards, DECLINING (None) unless each `sub[g.var]` is a concrete App of `g.con`; `_prove_measure`
reconstructs the concrete-subfield target via `pred.subst_term` and threads `gsub` into the IH.
  - **FIRE AT CONCRETE SUBFIELDS** - the middle/last equations fire only where the right child is
    literally `Leaf`/`Node`; `rdepth(t)` for an OPAQUE `t` fires nothing, the same sound silence a
    flat measure keeps. No e-matching, no triggers, no quantifiers over inner fields - single-pass
    closure preserved because every fired RHS term (`rdepth(Node(rl,rv,rr))`) is a subterm the walk
    already descends into.
  - **STRUCTURAL CHECK NOW ACCUMULATES THE PATH** - recursion is legal on ANY binder taken apart on
    the way here (outer field OR inner field: all strict subterms); `emit_leaf` checks against the
    accumulated `fields`. Probed all five ways: non-total nested match → `has no arm for Node`;
    nested overlap → `has two arms`; nested match on an Int field → `not an algebraic data type`;
    recursion on the param `t` → `not structural - ... not a field taken apart on the way here`;
    recursion on an inner field `rr` → sound, proved. All the existing 11_measure_* checks reach
    through the nesting unchanged.
  - **THE DEMONSTRATOR, BOTH DIRECTIONS** - `prove/34_nestedmeasure_{safe,unsafe}.lark`. `rdepth`
    DECLARES `{v:Int|v>=1}`, proved by NESTED induction (the nested arm's target is the concrete
    subfield `Node(l,v,Node(rl,rv,rr))`, IH at `rdepth(Node(rl,rv,rr))`); that declared result is
    what lets `use(t, d:{v==rdepth(t)})` divide `100/d` over an OPAQUE tree (`d==rdepth(t)>=1>0`,
    the 21_result shape with nesting). The equations then fire at the BUILT trees in `main`
    (`2==rdepth(Node(Leaf,5,Leaf))`, `3==rdepth(Node(Leaf,1,Node(Leaf,2,Leaf)))`). 6 obligations,
    all proved, runs → `50\n33\n`. The mutant claims the first tree has depth 0; the nested Leaf
    equation fires and says 2, so `0==rdepth(Node(Leaf,5,Leaf))` is `0==2`, 1-of-6 unproved - and
    had it been admitted, `100/0` detonates (verified: prints 50 then ZeroDivisionError, exit 1),
    which is why it is absent from RUNS.
  - **I6 - GUARD SCOPING (the I-axis, not luck).** The NEW failure mode the flattening opens, that
    I1-I5 cannot see: a `Guard.var` that was never bound on the way in makes `sub.get(g.var)` None,
    so the arm NEVER FIRES for any term - the measure is silently PARTIAL along that path, which
    with a declared result is `11_measure_partial`'s unsoundness wearing a disguise TOTALITY CANNOT
    SEE (the arm is present; it is only unfireable). `tests/invariants.py` `guardscope` walks the
    flattened arms and asserts every guard names {param} ∪ {outer binders} ∪ {earlier guards'
    binders}. WATCHED to fail: injected `Guard(scrut_name+"_X", ...)` into refine.py → I6 flagged
    2+2 out-of-scope guards AND prove/34_safe fell 6→4 (the genuine call obligations became
    unprovable), then restored byte-for-byte. 4 nested guards over the corpus, 0 out of scope.
  - **ALL GREEN** - harden exit 0: drift clean, conservative 90/0/0, solver 16/0, prove 71/0,
    robust 45/0/0, fuzz 0-unsound over 3000 cases, adversary clean, torture 14/14, invariants
    I1(nodes 0 missed/0 revisited) I2(54/54) I3(2.00×) I4(16/0/0) I5(3/0) I6(4/0).
  - **NEXT = V2.4c STEP 4 (bst/sorted)** - the last, highest-risk piece. OPEN: the adversary cannot
    yet SPEAK a nested measure (a generator only finds bugs in the language it speaks); worth
    teaching before/with step 4. Confirm direction with Set.**

**THE EQUALITY SEAM OK (2026-07-15, UNCOMMITTED). Not a rung - the follow-up to the Float
interlude, answering Set's "any other types that need thinking? strings? other?". Answer: yes -
String and functions, and it is the MIRROR of Float. `refine.py`/`cek.py`/`solver.py` UNTOUCHED;
the whole thing is three fixtures + docs. prove 66→69/0.**
The seam is that three layers disagree about `==`, each correctly on its own terms: HM types it
`∀a. a → a → Bool` (fully polymorphic, `infer.py` `_binop_type`); the refinement logic treats a
String / closure / ADT / tuple as OTHER, where congruence makes `s == s` REFLEXIVELY VALID (as it
must); but the machine implements `==` for Int and Float ONLY (`cek.py` `binop`, else `raise
RuntimeError("cannot apply '==')`). So a checker proves the dead-`else` division of
`if s == s then 0 else div(100, d)` - `2 proved` - and the machine RAISES on `s == s` before any
branch. **NOT a false proof, NOT a bug:** the crash PREEMPTS the division, so no ZeroDivisionError,
the narrow promise is KEPT - but `proved` here is strictly weaker than every other proved row, and
that gap is the seam. Opposite polarity of Float: **Float's `==` EXISTS and lies** (NaN → a real
false proof → made unspeakable); **String's/function's `==` do NOT exist, and the logic believes in
them anyway.** For a closure the granted equality is not just unimplemented but UNDECIDABLE.
  - **Documented as a boundary, not closed** - a language property shared with 07/, a third
    deliberate gap beside ℤ-vs-32-bit and partial correctness (added to PROVE.md top block). Two
    real closing roads both scoped out: route runtime `==` through the existing `_val_eq` (a
    CEK-machine change, shared with 07 → String case would run, returning 0), or make String `==`
    untranslatable like Float (throws away the sound String congruence `33_eqseam_control` needs, to
    guard a case that cannot produce a false proof). **MEASURED (Set asked "would c fit now?"): the
    NAIVE reroute is UNSOUND - it produces false proof #10.** `_val_eq` (`cek.py:256`) handles the 5
    scalars then `case _: return False`, so for a CLOSURE (and VCon/VTuple) it silently returns False;
    rerouting `==` through it makes the checker-proved-dead `g == g` else go LIVE → `33_eqseam_fun`
    ran to `ZeroDivisionError` (`33_eqseam_string` ran fine → 0). So a SOUND (c) is its own rung, not
    a drop-in: make `_val_eq` total + reflexive-consistent - structural recursion for String/VCon/
    VTuple (sound: structural `==` IS a congruence in a pure language), physical identity for closures
    (reflexive for a bound name = all the logic uses; extensional fn-equality is undecidable - a
    DECISION to write down), with its own soundness note + invariant + an ADT/closure-`==`-speaking
    adversary. Parked; boundary stands.
  - **Three fixtures under number 33.** `33_eqseam_string` + `33_eqseam_fun` - both `proved` (2) and
    DELIBERATELY absent from RUNS (they raise `cannot apply '=='`); the suite's only proved-but-unrun
    rows, each with a long teaching comment on the three layers. `33_eqseam_control` - a String
    reasoned about SOUNDLY through `string_length` (its length is an Int, guard discharges the
    divisor by congruence on the one UF term), proved AND run → 33, so the seam reads as "one
    operator, `==`" and not "Strings are second-class".
  - **VERIFIED (2026-07-15):** prove 69/0 (control runs → 33; both seams crash `cannot apply '=='`
    as documented), invariants I1-I5 hold (the new `==` nodes walked once, I4 16/0, I5 3/0). The
    other suites (drift/conservative/robust/torture/fuzz/adversary) do not read `prove/` and no src
    changed, so they are unaffected. **Uncommitted:** `prove/33_eqseam_{control,string,fun}.lark`,
    `08/tests/prove_difftest.py`, this `LOG.md`, `PROVE.md`.
  - **NEXT = V2.4c step 3 Part B** (nested `match` in a measure), still the deferred rung; confirm
    with Set. Like the Float interlude, this touched no checker code.

**FLOAT INTERLUDE OK (2026-07-15, UNCOMMITTED). Not a rung - a demonstration that the ONE
fact V2.2' established (no term is ever built at sort FLOAT) is realised through DIFFERENT
machinery in different contexts, plus a pinning of the contexts the suite had left undriven.
No bug found: all four contexts were already sound. `refine.py`/`cek.py`/`solver.py` UNTOUCHED
- the whole interlude is fixtures + one adversary surface. prove 60→66/0.**
Set's steer was exactly right ("no easy solution because of different approaches in different
context for this Float - but you will see"). Probing the four ways a Float can reach the checker
showed there is no single "Float rule": the unspeakability principle surfaces as SILENCE where a
formula is optional (a program-position guard → `term_opt` returns None → the division goes
honestly unproved) and as an ERROR where a formula is mandatory (a refinement → the strict
`formula()` raises; a measure arm → the expressibility check raises). One principle, three code
paths - which is the fragility worth pinning, because every false proof in this fork's history
was a road correct in one path and missed in another.
  - **29_floatfield_{safe,unsafe} - THE FOURTH ROAD, and the only new soundness row.** A Float
    carried in a CONSTRUCTOR FIELD. Nothing in prove/ had a Float field before (V2.2' paved the
    param, the `float_sqrt` result, and the literal roads; a field was the unpaved fourth). The
    mutant reads the `f == f` guard off the Float field instead of the Int field beside it, the
    guard goes silent, the division is honestly unproved (1 of 2), and it DETONATES at run time
    (`B(0.0/0.0, 0)` → NaN → else → 100/0). Watched-to-fail: delete the FLOAT-silence guard in
    `term_opt` and it flips to `2 proved` - 13's false proof reached through a constructor.
  - **31_substitutivity_{safe,unsafe} - THE OTHER HALF OF THE LIE, and it BITES.** 13 is
    REFLEXIVITY (`x == x`, false for NaN); 31 is SUBSTITUTIVITY (`a == b` ⊢ `tag(a) == tag(b)`,
    false for `0.0`/`-0.0`). My first probe (`tag(z) == tag(0.0 - z)`) did NOT trigger - the args
    are distinct terms, congruence never fires. The proper shape is a float `==` GUARD
    (`if a == b then div(100, tag(a) - tag(b) + 1)`): under speakable Floats the guard asserts a
    term equality, congruence discharges the divisor, `2 proved`. So it flips under the same
    injection as 13 - genuine watched-to-fail, not decoration. The lesson in one row: reflexivity
    and substitutivity are the two axioms congruence closure IS, and a SINGLE guard (no Float term
    is built, so `a == b` over Floats is itself unreadable) shuts both doors.
  - **30_floatpred_reject / 32_floatmeasure_reject - the two REJECTIONS, kept for the demo.** A
    refinement over a Float (`{v : Float | ...}`, and even `{v : Float | v == v}` with no float
    literal - the binder alone is unspeakable) → "not a predicate in the decidable fragment"; a
    measure returning a Float field → "not expressible in the predicate language" (32 is the Float
    face of 11_measure_fragment; belt-and-suspenders - under injection it only trades one refusal
    for another, "not an integer", never a false proof). Neither bites under the `term_opt`
    injection because their guards are one path over - which is itself the point about the three
    roads.
  - **THE ADVERSARY LEARNED A FOURTH FLOAT POSITION.** It already spoke a Float literal/param in a
    guard; it could not speak a Float FIELD. New `has_floatbox` surface: declare `type FB = | FB
    of Float, Int`, and FORCE the body into a `match FB(<NaN factory>, k) with | FB(fld, k) => if
    fld == fld then 0 else (<body>) end` so the else - the real body, with its divisions - is the
    branch NaN actually takes. Under the speakable-Float injection the adversary now reports a
    FALSE PROOF through FB (`... else (... 6 / (0 * x) ...)`), so road 29 is FUZZED, not just fixture-
    pinned. "A generator only finds bugs in the language it can speak," a fourth time.
  - **VERIFIED (2026-07-15):** prove 66/0, drift 21/4/3/0 (refine.py already EXTENDED; cek.py
    UNTOUCHED - the interlude is checker-silent), conservative 90/0/0, robust 45/0/0, torture
    14/14, invariants I1-I5 (the new match/constructor nodes walked exactly once), adversary CLEAN
    seeds 3/11/4242 with the FB surface exercised, fuzz 0-unsound. **Uncommitted:**
    `prove/29_floatfield_{safe,unsafe}.lark`, `prove/30_floatpred_reject.lark`,
    `prove/31_substitutivity_{safe,unsafe}.lark`, `prove/32_floatmeasure_reject.lark`,
    `08/tests/{prove_difftest,adversary}.py`, this `LOG.md`, `PROVE.md`.
  - **NEXT = V2.4c step 3 Part B** (nested `match` in a measure), still the deferred rung; confirm
    with Set. The interlude touched no checker code, so it changes nothing about where Part B stands.

**V2.4c STEP 3 Part A OK (2026-07-15, UNCOMMITTED). The min/max-if-speaking adversary -
and it caught TWO on the way in: the NINTH false proof (a lambda's precondition) and a
step-1 min/max ROBUSTNESS hole. Two fixes in `refine.py`, tests-first, RED→green.**
Part A of step 3 was meant to be the low-risk half: teach the adversary to SPEAK `min`/`max`
(both as divisors and in CONTRACT position, the `minpos` shape) and refined lambdas, closing the
documented step-1/2 gap ("a generator only finds bugs in the language it can speak"). It spoke, and
immediately found two things two hand-audits had missed.
  - **THE NINTH FALSE PROOF - a lambda's PARAMETER is a contract, and a contract is discharged at the
    CALL.** 22 fixed the FIRST half of the lambda story (a body is code, so `synth` must WALK it). That
    left a hole one step along: the body is walked with the parameter bound to WHAT ITS ANNOTATION SAYS,
    so `fn (k : {v | v != 0}) => 100 / k` ASSUMES `k != 0` and proves the division - but `synth` returned
    `ROpaque()`, which carries no parameter contract, so the APPLICATION discharged nothing.
    `let g = fn (k : {v | v != 0}) => 100 / k in g(0)` was **`ok: 1 obligation(s) proved`**, exit 0, then
    ZeroDivisionError. The body's `k != 0` was proved from an assumption the call never had to earn.
    **FIX (the one 22's own comment pointed at without taking):** the `Lambda` case in `synth` now returns
    an `RFun` carrying the parameters' refinements, exactly as a top-level `fn` (`_fn_rtype`), so the
    EXISTING `_apply` raises the precondition obligation at the call - and the body may keep assuming the
    parameter BECAUSE the caller is now made to establish it. `prove/27_lambdapre_{safe,unsafe}.lark`
    pinned RED first (unsafe reported `1 proved`, the false proof in the flesh) then green at 3 / 1-of-2;
    `22_lambda_safe` legitimately moved 3→4 (its `quotient` calls `go(d)` through exactly this path, now
    honestly discharging `d != 0`), runs unchanged → 25/25.
  - **A step-1 min/max ROBUSTNESS hole (not soundness) - the adversary's FIRST catch once it could say
    min/max.** `min`/`max` carry a result axiom (`min(a,b) <= a`, ...) instantiated at each application an
    obligation mentions. A term-level `if` argument is untranslatable (step 2), so it is SKOLEMISED at
    sort OTHER, and the axiom read `min($k1, $k2) <= $k1` - an ORDER comparison on a non-integer term -
    which the solver RAISED on (`comparison on non-integer terms`). A legal, at-run-time-safe program
    became NO VERDICT, the one grade `torture` calls a failure. **FIX:** `result_axioms` now takes the
    sort context and DROPS any instantiation whose order-comparisons are not both integers (equalities are
    exempt - congruence decides them at any sort), checked against the SAME table the solver uses. It is
    `_instantiate`'s rule one table over: where the checker cannot speak it says NOTHING - `min`'s result
    stays opaque and the division goes honestly UNPROVED. `prove/28_minmax_untranslatable.lark` pinned
    RED (`error: comparison on non-integer terms`) → green (unproved 1/1, runs → 20). `25_minimum`
    unmoved (6 proved) - the guard only fires when an argument is genuinely unspeakable.
  - **VERIFIED.** prove 60/0, drift clean (refine.py already EXTENDED), conservative 90/0/0, solver sound,
    robust 45/0/0, invariants I1-I5, fuzz 0-unsound, torture 14/14, adversary CLEAN across seeds
    1/4/11/429/4242 with **0 refinement errors** (was 4 at seed 11 before the sort guard). cek.py
    untouched (both fixes are checker-only; the refinement stays ghost).
  - **OPEN → NEXT = V2.4c step 3 Part B** (the harder half, DEFERRED per the roadmap): nested `match` in a
    measure. Approach confirmed with Set: FLATTEN + fire at concrete subfields (a nested match flattens
    into constructor-path-guarded equations, each firing only when the mentioned target's subfield is a
    concrete constructor term - no discriminator predicate, no existential/injectivity; an opaque subfield
    ⇒ the equation does not fire = sound/under-complete). Then step 4 (full bst/sorted). Confirm with Set
    first.

**V2.4c STEP 2 OK (2026-07-15, UNCOMMITTED). `if` in PREDICATE position - one case in
`formula_opt`, no solver change, no false proof.**
Set asked (again) to write the tests first and confirm the plan before code; both held, and the plan
confirmed two calls - formula-position ONLY (a term-level `if` inside a comparison stays
untranslatable, which is sound), and I5 formalized as a FAITHFUL-TRANSLATION check rather than the
plan's literal "obligations its branches owe" (an `if`-predicate raises no obligation of its own - it
IS a formula - so that wording was about program-position `if`, already covered by I1+I2).
  - **THE STATE BEFORE.** An `if` in a predicate was UNSPEAKABLE: `formula_opt` had no `IfExpr` case, so
    `{v : Int | if c then p else q}` returned None and the STRICT `formula()` at the declaration site
    (`refine.py`, `_rtype_of_syn`) rejected the whole contract. Not a silent drop - a hard reject. So the
    rung is purely additive: it makes a shape the checker used to refuse into one it can translate.
  - **THE CHANGE - ONE CASE.** `formula_opt` now has `case IfExpr` → `And(Implies(cf, pf), Implies(Not(cf),
    qf))`, admitted ONLY when all three of c, p, q translate; the moment one is None the whole predicate is
    None again. That is V2.2''s law one level up from the solver and the same rule `_branch` already
    enforces for a PROGRAM-position `if`: where the checker cannot translate, it says NOTHING - never
    `or Top()`, never a negation. **No `solver.py`/`pred.py`/`cek.py` change** - `Implies`/`And`/`Not` were
    already decided, and the refinement is ghost. Drift ledger UNMOVED (refine.py was already EXTENDED).
  - **TEST-FIRST, RED then green.** `prove/26_ifpred_{safe,unsafe,drop}.lark` written and pinned to their
    TARGET verdicts first; the two feature fixtures failed RED (both `error: not a predicate ...`, rejected
    at declaration) while the sentinel already rejected - before any implementation. Predicted counts hit
    EXACTLY: `abs` safe **proved 3** (two body branch-VCs - the then owes `x==x`, the else owes
    `(0-x)==0-x` and `(0-x)>=0` - plus the caller's division, safe because the postcondition instantiated
    at `x=-4` takes the else disjunct and gives `a==4`), runs → **25**. `abs` needs the guard on BOTH sides
    and BOTH polarities: the body proves it (both branches), the caller reads it (guard-false at -4).
  - **THE MUTANT DETONATES.** `26_ifpred_unsafe` calls `abs(0)`: the guard `0>=0` is TRUE, `a==0`, the
    division `100/a` flips to **unproved 1/3**, and would divide 100 by 0 were it admitted. It indicts the
    if-translation directly - a collapsed else or a dropped guard would let the checker conclude `a!=0`
    from the wrong disjunct; it does not, because the guard at `x=0` selects the then-disjunct.
  - **THE SOUNDNESS SENTINEL** (25_minimum_redef's analog): `26_ifpred_drop` has an else branch
    `v == x*x*x` - NON-LINEAR, the ordinary way out of the fragment - so `q` is untranslatable, the whole
    `if`-predicate is None, and the contract is REJECTED at its declaration. It must stay rejected AFTER
    step 2, and that is exactly what an `or Top()` regression would break.
  - **I5 - FAITHFUL TRANSLATION, and it was WATCHED to fail.** New invariant (`08/tests/invariants.py`):
    for every `IfExpr` reaching `formula_opt` anywhere in the corpus, the result is either None or EXACTLY
    `And(Implies(a,p), Implies(Not(a),q))` with the SAME condition `a` on both sides and no branch `Top`/
    `Bot` unless the source branch was a literal `true`/`false`. Instruments the module-global `formula_opt`
    (its recursion resolves through the module, so nested `if`s are caught too). Per the standing rule -
    *an invariant you have not seen fail for a reason you understand is not yet evidence* - the `or Top()`
    bug (false proofs #2/#7, the exact shape) was INJECTED and BOTH sentinels bit: I5 named
    `26_ifpred_drop` mistranslated AND the prove difftest flipped it `error → 1 proved` (a false proof
    admitted). Restored byte-for-byte.
  - **All green (2026-07-15):** `make -C 08 harden` exit 0 - drift 21/4/3/0, conservative 90/0/0,
    solver clean, **prove 57/0**, robust 45/0/0, fuzz 3000/0-unsound, adversary 150/clean, torture 14/14,
    invariants I1 (4104 nodes/0/0), I2 (46/46), I3 (2.00×), I4 (16/0/0), **I5 (3 if-predicates / 0
    mistranslated)**. **Uncommitted:** `prove/26_ifpred_{safe,unsafe,drop}.lark`,
    `08/src/refine.py`, `08/tests/{prove_difftest,invariants}.py`, this `LOG.md`, `PROVE.md`.
  - **OPEN GAP (documented, sound-direction, same as step 1):** the adversary cannot yet SPEAK `if`-
    predicates, so it is not exercising this surface - a generator only finds bugs in the language it can
    speak. Step 2's soundness rests on the drop sentinel + I5, both tested; the adversary gap closes in
    step 3, which the plan sequences precisely so the min/if-speaking generator lands before nested match.
  - **NEXT = V2.4c step 3** (nested `match` in a measure) - and a NEW adversary generator that speaks
    `min`/`if`. Confirm with Set before starting, per the same discipline.

**V2.4c STEP 1 OK (2026-07-15, committed). `min`/`max` as UNINTERPRETED symbols with their
defining axioms - and the rung the LOG feared as "new decision-procedure surface" needed NONE.**
Set asked to write the tests first this time and be careful about the implementation, and both paid
off. **The finding that reframed the risk:** `min`/`max`-with-axioms-at-mentioned-terms is not new
solver surface - it maps EXACTLY onto the machinery `string_length` already uses, which V1'/V2.3 hardened.
`string_length` demonstrates the whole pattern: a `_builtin_contracts` entry that SELFIFIES the result
to its UF term (`{v | v == string_length(s)}`) plus a `PRIMITIVE_AXIOMS` entry for the fact
(`{v | v >= 0}`), instantiated at mentioned applications by `result_axioms`. `min`/`max` are the same
shape - selfify `{v | v == min(a,b)}`, axiom `{v | v <= a and v <= b and (v==a or v==b)}` - and the
DISJUNCTION is decided by DPLL(T) as-is. **No `solver.py`/`pred.py` change; no new theory.**
  - **TEST-FIRST (Set's ask).** `prove/25_minimum_{safe,unsafe}.lark` written and pinned RED first
    (`rejected: unbound variable 'min'`), then made green. Predicted counts (6 proved; 1-of-6) hit
    EXACTLY - no count surprise to investigate, which is the point of predicting them.
  - **FOUR edits, all localized:** `infer.py` HM schemes `min`/`max : Int,Int->Int`; `cek.py` runtime
    builtins (arity 2, two-arg dispatch, VBuiltin table); `refine.py` `_builtin_contracts()` selfify
    entries; `refine.py` `PRIMITIVE_AXIOMS` the three-fact axioms. The disjunction is load-bearing:
    `min_pos` proves `min(a,b) > 0` from `a>0 and b>0` ONLY because the result IS one of the two - the
    `<=` facts alone give an upper bound and no lower one. That obligation is the safe fixture's crux.
  - **FIRST PROVE RUNG TO TOUCH THE RUNTIME.** Every prior rung was ghost (erased before run time), so
    `cek.py` stayed byte-identical to the 07 oracle and the drift ledger never moved. `min`/`max` are
    REAL builtins the program calls, so `cek.py` genuinely changes - `drift.py` caught it, and `cek.py`
    is now registered EXTENDED with an honest description (and `infer.py`'s description updated: no
    longer "the ONE line"). A categorical first, flagged rather than buried.
  - **SOUNDNESS GUARD TESTED, not assumed.** Added a THIRD fixture beyond the plan,
    `prove/25_minimum_redef.lark` (`unproved 1/1`): a program that declares its own hostile `min` (the
    SUM) must NOT get the axiom - `16_axiom`'s rule, which the `rebound` intersection in
    `Refiner.__init__` already enforces. Verified it fails for the reason understood (axiom DROPPED,
    `min(a,b) <= a` unprovable, since `min(1,1)==2`). "An invariant you have not seen fail for a reason
    you understand is not yet evidence."
  - **All green (2026-07-15):** `make -C 08 harden` exit 0 - prove **54/0**, drift (cek.py now EXTENDED),
    conservative, solver, robust, fuzz 0-unsound, adversary clean, torture 14/14, invariants I1-I4
    (4068 nodes, 44 divisions/44 obligations, 2.00×, I4 16/0/0). **Uncommitted:**
    `prove/25_minimum_{safe,unsafe,redef}.lark`, `08/tests/{prove_difftest,drift}.py`, `08/src/{infer,cek,refine}.py`, this `LOG.md`.
  - **OPEN GAP (documented, sound-direction):** `08/tests/adversary.py` cannot yet SPEAK `min`/`max`, so
    it is not exercising this surface - the plan sequences a min-speaking adversary for a LATER step
    ("a generator only finds bugs in the language it can speak"). Step 1's soundness rests on the
    ResultAxiom path + the redef guard, both tested; the adversary gap is a completeness-of-search gap.
  - **NEXT = V2.4c step 2** (`if` in predicate position) - see §"V2.4c - the min/max fork" plan. Confirm
    with Set before starting, per the same discipline.

**V2.4 IN PROGRESS (2026-07-15). FOUNDATION OK (monomorphic path) and V2.4b OK (polymorphic
fields, P2 closed soundly) are BOTH LANDED and committed. V2.4c step 1 OK (uncommitted, above).
NEXT = V2.4c step 2, `if` in predicate position - see the staged plan. Do NOT start it without
reading §"V2.4c - the min/max fork" plan below and confirming with Set.** Update at the bottom of this banner (see
" V2.4 FOUNDATION, 2026-07-15") records what this session committed; the original find below stands.

**V2.4 - THE BOOL-ATOM CONGRUENCE BUG - FOUND AND FIXED; then a DESIGN
FORK, awaiting Set's call.** Started V2.4 (Bool-valued measures → `sorted`/`bst`) by exercising a
Bool measure end to end (`allpos`), and it did NOT prove. Two things were wrong, one deep:
**(1) THE SOLVER - `solver.py`, `Theory.consistent` - the real "the SORT" crux the V2.4 hint named.**
A Bool-valued measure reaches the solver as an ATOM (`sorted(xs)`), not as a term in an `==`. The
`Atom` case bridged it to `t == BoolLit(pos)` and fed that to congruence - CORRECT - but added only
`t` to the closure, never the `BoolLit`. So `true`/`false` were absent from `cc.terms` at the
distinct-literals pass, never asserted distinct, and a congruence that (rightly) collapsed
`sorted($v)==false` into `sorted(c)==true` when `$v==c` went **undetected**: the checker said
*cannot prove* where it should have proved. `sorted(c)` for a concrete `c` proved; `sorted($v)` with
`$v==c` in scope did not - congruence was not reaching the atoms. **The Int measures never hit this
because their result is a term in an `==`, so the value literal is added by the `Cmp` branch - which
is exactly why V2.2 could leave the solver byte-for-byte and V2.4 cannot.** Fix: add `BoolLit(pos)`
to the closure in the `Atom` branch, mirroring what the `Cmp` branch already does for both sides.
One line + comment; **soundness re-checked** (no bridge, no proof); all green - drift 22/3/3/0,
conservative 90/0/0, solver 16/0, prove 47/0, robust 45/0/0, fuzz 0-unsound, torture 14/14,
invariants clean (3954/0/0, 38/38, 2.00×). Bool measures now fire: `allpos`'s call-site VC, which
was unproved, proves.
**(2) A completeness gap for POLYMORPHIC list fields (open): `| Cons(x, rest) =>` over `List(Int)`
gives `x` sort OTHER, because `infer_pat` instantiates `Cons`'s scheme with a FRESH var and never
unifies against the scrutinee's `List(Int)`, and `_pat_term` computes the right `want=INT` sort but
discards it for a named `PVar` (only `PWild` uses it). So `allpos`'s division VC drops its equation on
the `other≠int` guard in `_instantiate`. It is the tuple bug V2.0 fixed wearing an ADT hat - the SOUND
direction (OTHER just drops a fact), so it is incompleteness, not a false proof. Monomorphic ADTs
(`Tree`, `Buf`) are unaffected: `infer_pat` gives their fields concrete types.**
**THE FORK (Set's call): min/max BST was SETTLED, but defining `minv`/`maxv` (or a list `minimum`)
needs `min`/`if`/a nested match, and the predicate fragment has NONE of these. So V2.4 needs a
direction - see the three options I'm putting to Set. Nothing past the solver fix is committed.**

**V2.4 FOUNDATION OK (2026-07-15). A Bool measure works end to end, WITHOUT the polymorphic-field
fix - because the demonstration was moved off the polymorphic path, not made to climb it.** Set's
caution was explicit: *"be careful with the tree climbing not to add too much special treatments,
that we have to correct."* The polymorphic-field gap (P2 above) tempts exactly that - threading the
scrutinee's monotype through `infer_pat`/`_pat_term` so `Cons(x, rest)` over `List(Int)` gives `x`
sort INT. Instead the whole V2.4 demonstration uses a **monomorphic** `Tree = Leaf | Node of Tree,
Int, Tree`: `infer_pat` already gives its fields concrete sorts, so the atom-bridge fix (the real
V2.4 crux) is exercised with **zero** new special-casing. The gap stays open, documented, sound-
direction; nobody had to climb the tree.
  - **Fixtures** - `prove/23_boolmeasure_safe.lark` (measure `pos` over `Tree`; `root` requires
    `{v : Tree | pos(v)}` and returns `{v : Int | v > 0}`; `main` builds `Node(Leaf, 5, Leaf)`;
    **checked AND run** → `20`; proves 4/4) and its one-character mutant
    `23_boolmeasure_unsafe.lark` (root value `0`; the call owes `pos(Node(Leaf, 0, Leaf))`, which is
    FALSE; proves 1/4, would detonate `100 / 0` if admitted). This pair exercises the atom-bridge in
    its true home - DESTRUCTURING a Bool-refined parameter and BUILDING the constructor at the call.
    Pinned in `prove_difftest.py`; **prove now 49/0**.
  - **I4, a new invariant** - `08/tests/invariants.py`: *a Bool measure is a proposition, never an
    integer.* Over all 94 files it walks every VC's assumptions and goal and asserts no Bool-measure
    application (`base == "Bool"` in `refiner.measures`) appears in an arithmetic operand or under an
    `==`/`≠` (only under a boolean connective or an ordering it must be an atom); its walker is unit-
    tested against `pos(t)`, `pos(t)==false` (both 0) vs `pos(t)+1`, `pos(t)<3`, `-pos(t)` (each 1).
    Reports *8 Bool-measure references, 0 in an integer position, 0 mis-sorted.* I4 exists because
    the atom-bridge bug was a SORT confusion, and I1-I3 could not have seen it - they count nodes and
    obligations, not the SORT a term carries into the solver.
  - **The adversary, refactored (Set's ask: "make it better")** - removed dead code (a `g2` erased-
    twin generator built and never used; the comment lied - erasure is tested via
    `strip_refinements`). Added `rand_tree(depth)` (literal `Tree`s, node values weighted toward `0`
    to seed a ZeroDivisionError) and `bool_measure_decls()` (the monomorphic `Tree`/`pos`/`root`);
    with prob 0.35 a program now grows a `let rt = root(<random tree>) in ...` and divides its body by
    `rt`, so proved programs that reach `root` must have discharged a real `pos(...)` obligation.
  - **The injection experiment (watching it fail, on purpose).** Discipline the file states about
    itself: *"an invariant you have not seen fail for a reason you understand is not yet evidence of
    anything."* Injected `_instantiate`'s Bool branch → `return a` (drop the equivalence; assert
    `pos` unconditionally). The result is the finding: **both** fixtures went 4/4 → 3/4, and the VC
    that broke was `fn root: return value`, NOT the call-site precondition. The measure's strength is
    load-bearing in BOTH directions - you cannot weaken `pos` enough to admit `Node(Leaf, 0, Leaf)`
    without simultaneously destroying `root`'s own proof that its result is `> 0` (root proves `x > 0`
    ONLY from `pos(t)` implying it). That is soundness working: there is no shallow injection into the
    measure's meaning that makes a false thing look true without also breaking the honest proof - which
    is why the ADVERSARY (it only flags proved-then-crashed) correctly stays clean under it, and why the
    sentinel that BITES is the **prove difftest** (`23_boolmeasure_safe` fails its pin, 4→1). Ran both
    ways, restored `refine.py` byte-for-byte (matches HEAD; the fix was already committed in `a1ca7e9`).
  - **All green (2026-07-15):** drift clean, conservative 90/0/0, solver 16/0, **prove 49/0**,
    robust 45/0/0, fuzz 0-unsound, adversary clean, torture 14/14, invariants I1-I4 (3986 nodes /
    0 / 0, 40/40 divisions, 2.00×, I4 8/0/0). Uncommitted: `prove/23_boolmeasure_{safe,unsafe}.lark`,
    `tests/{adversary,invariants,prove_difftest}.py`, this `LOG.md`.
  - **Still deferred, awaiting Set:** the min/max FORK (**V2.4c**: `if`/`min` in the predicate
    fragment for `bst`/`minimum`), which is new decision-procedure surface and the highest-risk change
    to land unsupervised.  (The polymorphic-field fix P2, once deferred here, is now **V2.4b** below.)

**V2.4b - POLYMORPHIC FIELDS OK (2026-07-15). The tree got climbed - soundly, by NOT inferring.**
P2 above: a field of a polymorphic constructor (`Cons of a`) reached the solver at sort OTHER, because
`infer_pat` instantiates the constructor scheme with a FRESH variable and never unifies it against the
scrutinee's concrete monotype - so `x` in `Cons(x, rest)` over `List(Int)` was neither INT nor even
equatable, and a Bool measure over a polymorphic list could not be discharged (sound-direction
incompleteness: honest proofs FAILED; no false proof was ever possible). The temptation was to teach
the tree-walker to read measure-declared sorts (`_con_field_sort`) - REJECTED: it is unsound under
mixed instantiations (the same `Cons` used at `List(Int)` and `List(Bool)` in one program would read
one declared sort for both). The V2.0 RTuple precedent is the real fix: *"the fix was not to infer
harder but to stop inferring."* `RBase` now carries the binder's HM monotype as `mono` (a
`compare=False` field - invisible to equality/hashing, so dropping it is always the sound fallback and
the field simply stays OTHER); `_bind_pattern` unifies the constructor's instantiated pattern type
against `scrut.mono` and applies the resulting substitution to the field schemes BEFORE binding them.
The sort now comes from the SCRUTINEE's actual type, never from a declaration the checker doesn't own.
  - **Five edits, `refine.py` only** - `RBase.mono` field; `rtype_of_mono` returns `RBase(n,...,mono=m)`
    for `TCon`/`TApp` ADT heads (was `rtrue`); `_rtype_of_syn`'s `TRefine` case infers and attaches the
    mono; the var-selfify site threads `r.mono`; and `_bind_pattern` does the `ty.unify(_pt, scrut.mono)`
    then `apply_scheme`. No change to `solver.py`, `pred.py`, or `infer.py` - the drift ledger is
    unmoved (`refine.py` is ADDED; the ONE infer.py line is untouched).
  - **Fixtures** - `prove/24_polylist_safe.lark` (polymorphic `List a`; `measure allpos(xs:List(Int))
    :Bool`; `head` requires `{v:List(Int)|allpos(v)}` returns `{v:Int|v>0}`; `main` builds
    `head(Cons(5,Cons(3,Nil)))`, **checked AND run** → `20`; pre-fix 3/4 with `fn head: return value`
    unproved, post-fix **4/4**) and its mutant `24_polylist_unsafe.lark` (`head(Cons(0,Nil))`, owes the
    FALSE `allpos(Cons(0,Nil))`; stays **1/4**, would detonate `100/0`). Pinned; **prove now 51/0**.
  - **Generic-function soundness check** - a program whose `head` is used at a genuinely polymorphic
    type still gets field sort OTHER (the mono unify fails or is absent → the `compare=False` fallback);
    it checks and runs → `7`. The fix specializes only where the scrutinee's monotype is concrete.
  - **The adversary learned to speak polymorphic lists** - `rand_intlist(depth)` (literal `List(Int)`,
    values weighted `[1,2,3,5,0,0,-1]`) and `poly_measure_decls` (polymorphic `List(a)` + `allpos` +
    a `phead` with a NAMED `Cons(x,rest)` head; declares `type List a` only when `measure_decls` didn't);
    30% of programs now grow `let ph = phead(<random int-list>) in ...` and divide the body by `ph`.
    **300 random programs, seed 11: 33 proved / 219 unproved (143 ran fine) / 36 front-end-rejected /
    0 refinement errors - clean; every proved program ran and erasure held.**
  - **All green (2026-07-15):** conservative 90/0/0 (unchanged - the fix is purely refinement-layer),
    **prove 51/0**, invariants I1-I4 (I4 16/0/0), adversary 300 clean. Uncommitted:
    `prove/24_polylist_{safe,unsafe}.lark`, `tests/{adversary,prove_difftest}.py`, this `LOG.md`,
    `PROVE.md`.

**V2.4c - THE MIN/MAX FORK (planned, NOT started, HIGHEST RISK). Read this before touching it.**
The goal is the classic pair - `minimum(xs)` returns `{v : Int | v <= every element}`, and `bst`/
`sorted` measures that need to compare a node's value against a whole subtree. Why it is the riskiest
rung yet: every rung so far reused the EXISTING decision procedure (congruence closure + Omega under
DPLL(T)); this one adds **new surface to the fragment itself** - `if`/`min`/`max` in predicate
position and nested `match` inside a measure. That is where a false proof is easiest to introduce,
because the checker must translate a construct it could previously refuse. The V2.2'/V2.2''' law binds
hardest here: *where the checker cannot translate a guard it must say NOTHING - never `true`, never a
negation* (a `min` it half-understands becoming `true` is exactly the shape of false proofs #2 and #7).
**Staged plan, smallest sound step first:**
  1. **`min`/`max` as UNINTERPRETED first, with their two defining axioms** - do NOT try to make the
     solver reason about `min` structurally. Introduce `min(a,b)` / `max(a,b)` as UF symbols and assert
     only `min(a,b) <= a ∧ min(a,b) <= b ∧ (min(a,b)==a ∨ min(a,b)==b)` (dually for max) at each term
     the program MENTIONS - the same quantifier-free instantiation-at-mentioned-terms discipline V2.2
     used for measures. This is the whole rung's soundness crux: axioms at mentioned terms, nothing
     more. Fixture: `minimum` over a small `List(Int)` returning `{v | v <= head}` (weaker than full
     "≤ every element" but HONEST and inside the fragment), plus its unsafe mutant.
  2. **`if` in predicate position** - a guarded predicate `if c then p else q` translates to
     `(c ⇒ p) ∧ (¬c ⇒ q)` ONLY when `c`, `p`, `q` all translate; if any does not, the whole predicate
     is untranslatable and the obligation is ASKED-anyway / the hypothesis DROPPED per polarity (never
     silently `true`). Add an I-invariant sibling to I2 that COUNTS `if`-predicates and asserts each
     raised exactly the obligations its branches owe - luck must not be the thing that finds the hole.
  3. **Nested `match` in a measure** - only after 1-2 are green under adversary + a NEW adversary
     generator that can SPEAK `min`/`if` (recall: "a generator only finds bugs in the language it can
     speak"; the current grammar cannot emit either, so it would stay falsely clean).
  4. **Full `bst`/`sorted`** - the real target - LAST, once the fragment additions are individually
     proven and fuzzed. Expect to need the induction machinery of V2.3 for the measure's own result.
**Before writing any code:** confirm with Set (this is the "V2.4c, highest-risk, not without direction"
item). First concrete action is `prove/25_minimum_{safe,unsafe}.lark` as the target fixture, RED, then
make it green by step 1 alone - resist doing `min` structurally.

### 2026-07-14 (latest) - **I: INVARIANTS. The rules, checked by a machine - and the eighth false proof.**

**The ask:** *"there have been many chance findings - a bit too many for my taste. So can we do better,
and start with more severe programming?"* It is the right complaint. Every bug in the PROVE axis so far
was a **finding**: a hostile program got lucky, or a careful read got lucky, or a profiler got lucky.
Seven times. **A method that finds bugs by being lucky cannot distinguish "there are none left" from "I
stopped looking"** - which is the exact distinction V1' and H spent their whole budget forcing the
*checker* to make about itself. Demanding it of the tool and not of the people building it is a poor
joke.

**So the rules stopped being prose.** `08/tests/invariants.py` (`make -C 08 invariants`, folded into
`harden`) checks three properties over all 92 corpus files, on every run. Each is a bug we actually
shipped, generalised to its shape:

- **I1 - COVERAGE.** Every expression node in a checked body is *visited*, exactly once. **Missed** is
  the shape of V2.2'''(7) (four sites *translated* a sub-expression instead of *walking* it, so every
  division in a Bool position raised nothing). **Revisited** is the shape of H's quadratic (a subtree
  re-walked at every level above it). One question - *how many times did you look at this node?* - and
  the only acceptable answer is once.
- **I2 - ASKING.** Every integer division the checker walks raises exactly one obligation. The shape of
  V2.2'''(5), and **coverage cannot see it**: the node WAS visited, and the checker still declined to ask,
  because it could not read the divisor. Obligations are matched by **provenance** (`where_`), not by
  goal shape - `d /= 0` is also what a *contract* asks, and counting those would let a missing division
  hide behind a contract that happened to say the same thing.
- **I3 - WORK.** The checker's own cost is linear in program size - checked by **COUNTING, not timing**.
  The counters are deterministic, so this is a regression test rather than a wall-clock coin flip.
  Measured: **2.00× per doubling** for `synth`, `term_opt`, `is_linear`, against a 2.5× budget (a
  quadratic would be 4×). The **solver** is deliberately held to a *different* bar - Omega on an n-term
  system is honestly superlinear, and is *fenced* (`MAX_WORK`), not fixed. Conflating the two would
  either excuse a quadratic in the checker or forbid an honest one in the solver.

**IT FOUND AN EIGHTH FALSE PROOF WITHIN MINUTES - THE FIRST ONE THIS PROJECT HAS EVER FOUND ON PURPOSE.**
I1 reported **58 nodes across 7 corpus files never walked**, and they were all one thing: **the body of a
lambda.** `check` walks a lambda's body, because it has an `RFun` to push into it. `synth` returned
`ROpaque()` **without looking inside** - and an unannotated `let h = fn (a) => ...` goes through `synth`:

    let h = fn (a : Int) => 100 / a in h(0)
      →  ok: 0 obligation(s) proved       exit 0
      →  then, at run time:               ZeroDivisionError

**This is V2.2'''(7) exactly - a piece of the program the checker never walked - wearing a hat nobody had
thought to look under.** One of the 58 was a live division inside `07/tests/25_torture.lark`
(`filter(fn(x) => (x - (x / 2) * 2) == 0, xs)`), never once examined in the fork's entire life, in a file
called *torture*. **THE RULE, GENERALISED, IS THE THING TO KEEP: "every sub-expression is walked exactly
once" is not a fact about EXPRESSIONS. It is a fact about EVERY PLACE CODE CAN HIDE - and a lambda is one
of them.**

**The fix** (`refine.py`, `synth`'s `Lambda` case): bind each parameter to what is **declared** about it -
an unannotated parameter is `ROpaque`, i.e. *the checker knows nothing*, which is the truth, since it does
not track the call sites - then **walk the body**. A division inside is therefore provable only if it holds
for **every** argument, and otherwise goes honestly unproved. Weaker than tracking call sites, and weak is
the correct direction. The synthesised *type* stays `ROpaque`: walking a body is about the obligations
inside it, not about learning what the function returns.

**AND THE GENERATOR'S OWN BLIND SPOT, FOR THE SECOND TIME.** `adversary.py`'s docstring has said *"a local
lambda's result"* since V2.2''' - and **the generator could not emit a lambda at all.** It knew the words and
not the grammar. Now it does. Per the standing rule (*never trust a fuzzer you have not seen fail*) the fix
was **disarmed** and both harnesses were watched to fail: the adversary with a false proof, I1 by naming the
exact unwalked nodes. **A generator only ever finds bugs in the language it can speak. Its grammar is a
claim about which programs exist, and an unexamined grammar is an unexamined claim.**

**Files:** `08/tests/invariants.py` (new), `08/tests/adversary.py` (lambdas), `08/src/refine.py` (the
Lambda case), `prove/22_lambda_safe.lark` + `22_lambda_unsafe.lark` (new pair), `08/tests/prove_difftest.py`
(pins + RUNS), `08/tests/robust_sweep.py` (`25_torture` 4 → 5 obligations; the new one proves),
`08/Makefile` (`invariants`, folded into `harden`).

**All green:** drift 22/3/3/0 - conservative 90/0/0 - solver 16/0 - **prove 47/0** - robust 45/0/0 -
fuzz 3000/0-unsound - adversary clean - torture 14/14 - **invariants: 3954 nodes, 0 never walked, 0 walked
twice; 38 divisions, 38 obligations; 2.00× growth per doubling.**

**What is still open, and it is worth stating as a limit of the method rather than a to-do:** I1/I2/I3 are
invariants about the SHAPE of the walk, not about the CONTENT of what is proved. They can make a whole class
of bug - *the checker did not look* - impossible to ship quietly. They cannot tell you that an axiom is
sound. The two remaining honest gaps are unchanged: the logic is ℤ while RV32/C are 32-bit, and contracts
are partial correctness. **NEXT = V2.4** (Bool-valued and parametrised measures: `sorted`, `bst`) - and per
the door-by-door argument in PROVE §7, expect a new rung to add a new door.

---

### 2026-07-14 - **H: HARDENING THE CODE THAT IS. Not a rung - a pass over what exists.**

**Not a new capability. The mandate was "harden, verify as much as you can, make it resilient,
robust" - the code that *is*, not the code that could be.** Every hunt before this one asked
whether the checker is RIGHT. This one asked whether it **ANSWERS**: the two failures a verifier
may not have are a wrong answer and no answer, and only the first had a suite pointing at it.

**New harness: `08/tests/torture.py` - `make -C 08 torture`, and `harden` now runs it.** Fourteen
hostile-but-legal programs, each in a subprocess on a wall clock: 3 000 terms in one expression,
a predicate that is a 300-way conjunction, a constructor term 400 deep, 1 200 nested lets, 40
disequalities (2⁴⁰ splits if anything enumerates them), 30 disjunctions, a measure at the wrong
arity, a `{v : Float | v == v}`, a mutually recursive measure pair. **The only failing grade is no
answer at all** - a traceback, or a prompt that never comes back. It opened at **5 failures of 15**
and closes at **0 of 14** (one probe turned out to be testing my own typo: it wrote `x` inside `x`'s
own refinement, where the binder is `v`, and the checker was right to reject it - *the harness needed
hardening before the code did*).

**What it found, and what was done:**

1. **Four raw `RecursionError`s** out of `parser.py`, `infer.py`, `refine.py`. The checker walks a
   program on the C stack; Python's limit is 1 000. Now the whole check runs on a thread with a real
   stack (`_with_big_stack`, 512 MB / 200 000 frames) and what is left over is classified as
   **`TooDeep`**: a stated limit, not a stack trace. `deep_lets`/`deep_con` now check; `deep_pred`
   reports unproved, cleanly.

2. **Every fence in `solver.py` was LOCAL, and every caller loops.** V1' fenced the *splits* - but
   `MAX_SPLITS` re-arms on each `_lia`, `_propagate` calls `_lia` quadratically, and DPLL calls
   `consistent` once per node, so **the total work in one `satisfiable()` had no bound at all.** A
   budget that resets is not a budget. Fixed with a **global work purse** - `MAX_WORK`, one
   `Exhausted` per query, which the callers are explicitly forbidden to swallow (`except Exhausted:
   raise`, above the `except Budget` that resolves toward *consistent*). And the sharper half: bound
   the **SIZE** of a linear system (`MAX_LINEAR`), not the number of them. **Fourier-Motzkin is
   quadratic per elimination, so counting calls bounds nothing** - `wide_conj` hung inside ONE
   `omega()` call on a 300-row system. Also `Congruence.pos`, an index replacing a linear `.index()`
   scan per int term per projection per DPLL node.

   **Both fences were set against measurement, not taste.** Peak honest theory work across the entire
   prove suite *and* all of 07's corpus: **131 units** (fence 2 000 000 - 15 000× headroom). Largest
   honest linear system in one `omega()`: **8 rows** (fence 256 - 32×). Nothing a real program does
   can reach them, and `prove` 45/0 + `conservative` 90/0/0 + `fuzz` 0-unsound are the evidence.

3. **"I stopped looking" is not "this does not follow".** The *provenance* of a give-up now survives
   into the report: `solver.decide` returns *(proved, gave-up)*, `Result.gave_up` carries the VCs, and
   the CLI prints **"gave up (budget exhausted)"** where it used to print "cannot prove", with
   `(N abandoned on a budget)` on the tail line. The first is a fact about the program; the second is
   a fact about the checker, **and printing the second in the words of the first is how a tool teaches
   its user to distrust it.**

4. **A crash was hiding a cost - the finding of the pass.** Once the stack was raised, `deep_expr`
   stopped crashing and started **hanging**: the overflow had been mercy-killing a **cubic** algorithm.
   Translating `1 + 1 + ... + 1` re-derived the linearity of the **whole subtree at every level** of a
   walk that already visits every node - **173 million `is_linear` calls on an 800-term sum**, and 3 000
   terms never returned. Two fixes:
   - **`pred.linear_node`.** The subterms of a term `_term_opt` returns have already passed the guard,
     so only the new node is news. The full `is_linear` survives as the **specification**, and is now
     run **once per formula at the solver's door** (`pred.formula_linear`) - the fragment's boundary
     checked *where the boundary is*, rather than re-derived at every node inside it.
   - **`Env.memo`.** `synth` walks each sub-expression exactly once (V2.2''''s rule), but at each node it
     asked for the term of *that node's whole subtree* - n nodes each re-translating their own subtree
     is n². Memo keyed by **AST identity within one `Env`**, because an Env is precisely the scope in
     which a node's translation is a pure function of the node; **a new binder makes a new Env and a new
     memo, which is what stops a shadowed name being answered out of the cache of the scope that did not
     have it.** (Value-keyed would have been self-defeating: hashing an `Expr` *is* a walk of the subtree.)

   **57s → 0.014s** on the checker's own share of that program. The rule this leaves behind: **a crash
   can be the symptom of a cost, and fixing the crash without measuring the cost only moves the failure
   somewhere the tests cannot see it.**

5. **`ResultAxiom` - the statement proved must be the statement asserted, and now it is BY CONSTRUCTION.**
   Found by poking at V2.3, not by a test. `result_axioms` substituted only the *value binder*, leaving a
   measure's own **parameter** free - in both the induction goal and the asserted axiom. That is a name the
   checker does not own: **V2.2'(c)/(d)'s shape exactly**, and sound today only by the accident that free
   variables in a validity query are universally quantified. One dataclass now owns the instantiation
   (`ResultAxiom.at`); the induction **proves `at(m(C(y...)))`** and every obligation **assumes `at(m(t))`** -
   the same door, so the two cannot drift apart by anyone's carelessness. It also turned a proof that had
   been passing by luck into one that passes for a reason (`selfref`: an inconsistent declaration is now
   rejected *at the term itself* - `len(Nil()) > len(Nil())` - rather than by quantifier accident).

**MEASURED AND LEFT ALONE: the residual quadratic is the ORACLE's, and we are not unfreezing it.** With
the checker's share gone, `deep_expr` is *still* O(n²) - in `infer.py`'s `_apply_env`, which rebuilds the
entire type environment at every node (textbook naive HM). **07 pays it too: 7.9s to typecheck the same
file before any refinement work happens.** It is *bounded, terminating* work: not a hang, not a crash, not
a hole. Fixing it properly means threading the substitution lazily through inference - a real change to the
type-checker, with real regression risk, made to the one file whose job is to be **indistinguishable from
the frozen oracle** (08's `infer.py` diff is **9 lines**: the single case that erases `{v:Int|p}`), in
exchange for speeding up an input no program writes. **The freeze is what gives 08 its meaning:** every
claim this fork makes is a claim *relative to something that cannot move*, and an oracle that may be edited
when it is inconvenient is a preference, not evidence. So: **not unfrozen, not patched - measured, and
written down.** (If it is ever fixed, it goes in **08's** copy, never 07's, and `conservative` 90/0/0 is
exactly the harness that would prove the fix changed nothing observable.)

**Verified - everything, after every fix:** drift **22/3/3/0** - conservative **90/0/0** - solver **16/0** -
prove **45/0** - robust **45/0/0** - fuzz **3 000 / 0 unsound** - adversary **clean** - torture **14/14**.
Note `solver.py` is no longer byte-identical to its V2.2 self - that claim was always about the *rungs*
(which added no theory), and this is not a rung; the fences it adds are pinned by the suites above.

**Files:** `08/src/refine.py` (`ResultAxiom`, `_with_big_stack`/`TooDeep`, `Env.memo`, `linear_node` at the
build site, `formula_linear` at the door, `_sort_of_term` no longer rebuilding `Sorts` per node,
give-up provenance in `Result`/CLI) - `08/src/solver.py` (`MAX_WORK`/`Exhausted` purse, `MAX_LINEAR`,
`Congruence.pos`, `decide`) - `08/src/pred.py` (`linear_node`, `formula_linear`) - `08/tests/torture.py`
(new) - `08/Makefile` (`torture`, folded into `harden`) - `08/README.md`, `PROVE.md`.

**Next:** V2.4 - Bool-valued and parametrised measures (`sorted`, `bst`), per `PROVE.md` §4. The naming
question is answered in `PROVE.md`'s "Naming, door by door" section: the *class* is closed at each door a
name enters the logic, and the two doors that remain open are named there rather than papered over.

### 2026-07-14 - **PROVE V2.3 OK - the axiom became a theorem. `NONNEG_UF` is deleted.**

**What the rung was for.** V1 shipped with a confession in its own comment: `refine.NONNEG_UF`, a
set literal asserting `string_length(t) >= 0`, was "something it strictly should not have to know."
It was load-bearing - without it, slicing the whole of a string is unprovable, because an
uninterpreted symbol may return -1 for all the logic knows - and it was the last thing in this
checker that was simply *believed*. V2.3 replaces belief with proof.

**The mechanism, and all of it is in `refine.py` (`solver.py`, `pred.py`, `parser.py`, `lexer.py`,
`infer.py`, `tree.py` byte-identical).** A measure may now declare its result refinement:

```
measure len(xs : List(Int)) : {v : Int | v >= 0} =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + len(rest)
  end
```

`_elab_measure` keeps each arm's body and environment, and `_prove_measure` turns them into
**one VC per constructor arm**: the goal is the declared predicate at `len(Cons($f1, $f2))` (a
fresh, sorted skolem per field), and the hypotheses are the arm's own equations plus - at each
**recursive occurrence** in the body - the declared predicate at that occurrence. That is the
**induction hypothesis**, and structural recursion is what entitles it: an arm may only recurse on
a *field*, so the fields are smaller, so the induction is well-founded. **V2.1's structural check,
written to keep the axioms consistent, is now also what makes the induction legal** - the second
time that check has paid for itself.

Once proved, the refinement is asserted at the applications a program *mentions* (`result_axioms`,
the same walk-the-obligation's-own-terms shape as V2.2's `measure_axioms`, no quantifier, no
trigger). **And that is the capability: `total / (len(xs) + 1)` proves for an *opaque* `xs` - a
list never taken apart, never built. It is the first universal claim this checker has been able to
earn**, and `NONNEG_UF` is gone, in favour of `PRIMITIVE_AXIOMS`: one line, one entry,
`string_length`, the one function whose body the checker cannot see. String is primitive; it has no
arms to induct on, so it stays an axiom - but a **named, declared** one, still withheld from any
name the program rebinds (`16_axiom`'s finding kept). *The complete list of what this checker takes
on faith is now readable in one place.*

**THE FINDING - an induction VC may not assume what it is proving.** `Refiner.run()` hands each VC
the results table it may assert from, and for `ind=True` VCs that table is `prim_results`:
**without** the measures' own declared refinements. Give the `Nil` arm the axiom it is trying to
prove and it discharges itself - the bogus declaration passes, and the checker has proved a division
by zero. It is one line, and it is the whole rung. **Assuming the conclusion is not a subtle bug; it
is the entire difference between an induction and a lie.**

**Done-when, met - and it detonates.** `prove/21_result_unsafe.lark` moves one character
(`{v : Int | v > 0}`) and is **rejected**: 1 of 5 unproved, at exactly the right place, the **`Nil`
arm**, whose goal `len(Nil) > 0` sits beside its own equation `len(Nil) == 0`. The `Cons` arm still
proves, from the IH - *a false claim about a recursive definition is usually false at the base case,
and the base case is where the checker catches it.* Not a style complaint: admit the declaration and
`avg`'s `total / len(xs)` is discharged, `ok`, exit 0 - then `main` passes `Nil` and the machine
divides 100 by 0. The safe half proves 5 obligations, runs, and prints `25`. And the induction is
**load-bearing**: delete the `>= 0` from the safe file and `avg` stops proving.

**THE STATEMENT PROVED MUST BE THE STATEMENT ASSERTED.** Caught by my own audit, before any test
saw it: for a measure with **extra parameters** (`drop(xs, i)`), the induction goal was built as
`drop(Nil())` - a term no program mentions - while `result_axioms` asserted the refinement at
`drop(xs, i)`, the terms programs actually write. A theorem about something else, standing in for
one nobody proved: **sound by luck, which is the state every false proof so far was found in.** The
extras now enter as **free variables**, and such a measure goes honestly *unproved* until V2.4 lets
its equations fire.

**And the adversary had to be re-aimed, which is its own finding.** With `_prove_measure` disarmed,
`08/tests/adversary.py` came back **clean** - not because the hole wasn't there, but because it
generated `x / size(xs)`, a **bare call**, whose postcondition never becomes a fact (V2.2'': *a fact
travels through a NAME*), so it was unprovable whatever the declaration claimed. The generator was
aimed one syntactic step to the left of the bug. Generating `let m = size(xs) in x / m` instead, the
disarmed checker produced a genuine false proof on seed 11 within seconds (`ok: 3 obligation(s)
proved`, exit 0, then `ZeroDivisionError`). **A fuzzer that cannot express the bug does not report
its absence - it reports its own blind spot.** The only defence is to disarm the fix and make the
machine find it; a green adversary means nothing until you have watched it go red.

**Files.** `08/src/refine.py` (`PRIMITIVE_AXIOMS`, `result_axioms`, `VC.results`/`VC.ind`,
`_prove_measure`, `run()`'s withholding); `prove/21_result_{safe,unsafe}.lark`; `08/tests/
prove_difftest.py` (pinned 5 / 1-of-5, safe file in `RUNS` → `25`); `08/tests/adversary.py` (now
generates a `List` ADT, a measure with a lie-weighted declared result, and a divisor bound through a
name); `08/README.md`, `prove/README.md`, `PROVE.md`.

**Verified.** `make -C 08 test`: drift **22/3/3/0**, conservative **90/0/0**, solver **16/0**,
prove **45/0** (43 → 45, one new pair). `make -C 08 harden`: robust **45/0/0 crashes, every verdict
where it was**, fuzz **3000 / 0 unsound**, adversary **clean** (seeds 11, 4242, 7). **Cost: nothing.**

**Left open, deliberately.** A measure's *termination* is structural **by syntax** (V2.1's check),
not proved by a well-founded order - and that check is what the induction stands on. **Next: V2.4**
- Bool-valued and parametrised measures (`sorted`, `bst`), where the min/max-measure design is
already settled, and where the "a fact travels through a name" gap will have to be paid.

### 2026-07-14 - **PROVE V2.2''' OK - the adversary. Three false proofs, and none of them found by a human.**

**Why this session exists.** V2.2'' closed the impl hole and the obvious next question was: *do we
fix the capability gap we left, or do we go hunting?* We went hunting - because the next rung adds
**hypotheses** to VCs, which is the mechanism of every false proof so far, and you want the hunter
built *before* the thing it is supposed to catch.

**The tool - `08/tests/adversary.py`.** Random **programs**, not random formulas. Check with
`refine.check_program`; then **RUN** on the CEK machine every program the checker proved. *If it
says `ok`, the program does not crash.* A crash after a proof is a false proof, and the offending
program is printed. A second oracle strips refinements textually and demands identical output
(erasure). The generator is aimed at what has drawn blood: non-linear divisors, unreadable guards,
Floats, local lambdas, shadowed `string_length`, impls with bodies. `make -C 08 adversary`;
`make harden` includes it.

`fuzz` tests the **solver** - and **the solver has never been the problem.** Every bug this project
has had was one level up, in the checker that *builds* the obligations, and all four of V2.2''s
were found by hand. This suite is the witness for that level, and it should have existed four false
proofs ago.

**FINDING 1 - `18_divisor`: a goal it could not read was never asked.** `100 / (x * y)` - merely
**non-linear**, so `term_opt` returned `None` - raised **no obligation at all**. Same for
`100 / h(x)` where `h` is a local lambda (V2.2'(c) made those unspeakable, so the divisor's type
came back opaque and the site declined to ask). Both: `ok`, exit 0, then `ZeroDivisionError`.

This is **V2.2'(b)'s own rule at the opposite polarity**, which is exactly why it slipped through -
the fix for "don't believe a guard you can't read" was quietly generalised into "don't ask about a
divisor you can't read":

> a **HYPOTHESIS** it cannot read must be **DROPPED**.
> a **GOAL** it cannot read must be **ASKED ANYWAY**, and then honestly go unproved.
>
> *Silence about what you may **assume** is modesty. Silence about what you must **prove** is a lie.*

The asking condition is now **HM's** - this is an integer division, therefore it owes a proof - and
the only excuse is *positively knowing* the division is a **Float's**. Note the polarity of that
escape: to **skip**, the checker must know FLOAT; if it *loses* a sort it merely over-asks (noisy,
sound). A divisor it cannot name gets a **skolem that inherits the divisor's own contract**, exactly
as an argument's does - so `100 / nz(x * y)` still proves, and `$k /= 0` with nothing said about
`$k` is unprovable, which is the truth. (The call rule was already right: `string_index(s, x * y)`
skolemizes and still asks. Only the one hard-coded site had the polarity backwards.)

**FINDING 2 - `19_floatlit`: the one road into a Float that nobody has to declare.** V2.2'(a) gave
FLOAT to a declared parameter and a declared return, and missed the **literal**. `0.0` synthesised
to an rtype with no sort → read as `OTHER` → an ordinary opaque value → **and an opaque value may be
EQUATED**. So `nan == nan` was believed, its negation was UNSAT, and the else branch - *the one NaN
actually takes* - became dead code in the logic, from which everything follows. One missing sort,
**two bugs pointing opposite ways**: a falsehood **believed**, and (the sort being lost through
arithmetic) an obligation **invented**, because `0.0 / 0.0` looked like an *integer* division. That
second one is what surfaced it: two `robust` files started failing, and the failure was the fix
pulling on a real hole. *Unspeakability is not a property of a literal; it is a property of every
value a Float can reach - so the sort must **survive the operations**.*

**FINDING 3 - `20_condition`: the worst hole this fork has had, and it is not a subtle one.** A
division inside **any Bool-valued position** was never visited *at all*:

```
fn entry(x : Int, y : Int) : Int =
  if ((x / y) < x) then 1 else ...        (* y = 0 *)
```
→ **`ok: 0 obligation(s) proved`**, exit 0, then `ZeroDivisionError`. **Zero.** The checker did not
fail to prove the division; it never **saw** it. The distinction the code had stopped making:

> **`formula_opt` and `term_opt` TRANSLATE. `synth` WALKS.**
> Only the walk raises obligations. Translation is pure: it asks for nothing.

Four sites translated a sub-expression **instead of** walking it - an `if`'s **condition**, a
**comparison**, a **`not`**, a **unary minus** - and every division inside any of them vanished. The
unary minus is the sharpest: it walked its operand only when `term_opt` **failed**, so *the better
the checker understood an expression, the less of it it checked.*

> **EVERY SUB-EXPRESSION IS WALKED EXACTLY ONCE**, whether or not it is also translated.
> What the checker declines to **understand**, it must still **look at**.

**And this was never a corner case.** 07's own primes sieve contains `fn divides(d, n) = n / d * d
== n` - a function whose entire body is a comparison - and it reported **zero obligations for the
whole life of this fork**. A trial-division sieve, and the checker had never once looked at the
division. `robust_sweep.py`'s verdict for `03_primes` has moved from `("proved", 0)` to
`("unproved", 1, 1)`, honestly: `d : Int` does not promise `d /= 0`, every caller passes `d >= 2`
but the **signature** is what a modular checker gets to read, and 07 is frozen. **The move is the
finding.**

**ALSO CLOSED - the language may not grow behind the checker's back.** `synth` ended in a silent
`return ROpaque()`, so a `BinOp` whose operator it had never heard of would fall straight through:
no obligation, no error, `ok`, exit 0. **That is the impl hole's shape exactly**, and `%` is the one
waiting to happen - the CEK already implements it (`l.n - int(l.n / r.n) * r.n`, which traps on
zero) and **only the lexer is keeping it out of the language.** An unknown operator now **raises**
and says what it owes. (Which is also the answer to *"should we add `%` now?"* - **no**: there is no
hole today, it is a front-end change touching the frozen oracle's shape, and the guard means the
next person to add it will meet an error before they meet a false proof.)

**Also fixed: a count that lied.** `synth`'s `IfExpr` synthesised each branch **twice** (once as a
walk, once for the join), duplicating every obligation inside an `if` in value position. Sound, but
this project pins its tests to counts.

**THE COST WAS NOTHING.** Every `_safe` file proves, runs, and prints its answer. Closing holes this
large normally spends capability; here there was none to spend, because the capability *was the
absence of a question*. `prove` **37 → 43** (`18_divisor`, `19_floatlit`, `20_condition`, each a
safe/unsafe pair, all three safe files RUN). drift 22/3/3/0 - conservative 90/0/0 - solver 16/0
(byte-identical yet again - **every one of these lived in `refine.py`**) - fuzz 3000/0 - robust
45/0/0 with **exactly one verdict moved, and that one on purpose.**

**WHAT THIS RUNG IS REALLY ABOUT.** I audited this checker twice, and it was still proving programs
that divide by zero. Not because the audits were sloppy, but because **an audit looks where a bug
would be interesting, and a random program does not know which positions are supposed to be
interesting.** Nobody writes `if (x / y) < x` on purpose. Nothing in a Bool position *looks*
partial. The generalisation, which is now the fork's first rule:

> **A checker's silence is a verdict, and a report must never let silence read as approval.**
> `ok: 0 obligation(s) proved` was sitting in that output the whole time, and it reads like success.

**NEXT.** V2.3 (a measure's own result refinement proved by structural induction; delete
`NONNEG_UF`) - and the capability rung still deferred: a call's postcondition should reach the logic
without needing a `let`-bound name (`total / weight(c)` is still unprovable where `let w = weight(c)
in total / w` proves). Keep running `adversary` at new seeds; seed 4242 is where `20_condition` came
from.

**Sweep after the fixes.** 10 seeds × 250 programs - 3, 11, 23, 101, 999, 4242, 7, 55, 1234,
31337 - **all clean**: every program the checker proved was then run on the CEK machine, and every
one of them ran. That is 2 500 programs, and it is only worth saying because the same generator was
finding false proofs at three of those seeds a few hours earlier. Suites: drift 22/3/3/0,
conservative 90/0/0, solver 16/0 (byte-identical - every bug lived in `refine.py`), prove 43/0,
robust 45/0/0, fuzz 3000/0.

### 2026-07-14 - **PROVE V2.2'' OK - the impl hole, closed. An impl body is a body.**

**Why this session exists.** V2.2' ended with one bug **found and deliberately not fixed**: the
checker never looked inside an `impl` block. It was written down at the top of this log, in
`PROVE.md`, and in `08/README.md` as the thing to do *before* V2.3, and this session did exactly
that and nothing else.

**The bug, stated once.** `refine.py` imported `ImplDecl` and never matched it - not in `run()`,
not anywhere. So for V1, V1', V2.0, V2.1 and V2.2, **the code inside an `impl` was never walked**.
Reproduced in four lines: a trait, an impl whose method body divides by zero, and a program that
never reads the trait. Verdict: **`ok: 2 obligation(s) proved`, exit 0** - the two obligations
belonging to the *other* functions. The division did not fail to be proved; it was never asked
about.

**It was sound, and sound only by luck.** The refinement on a trait method's signature was
*dropped* rather than trusted (`_register_trait_decl` returns an HM scheme; `_rtype_of_mono`
erases the predicate), so a lying impl could not discharge a caller's goal - no false proof. What
it was instead is the failure mode next door, and the one V2.2''s rule already condemns:
**silent under-verification. A weak answer is a result; a count that omits the obligation is a
wrong report.** A verifier may have the first and never the second.

**The fix is two halves of one decision.** `_check_impl` checks each `ImplMethod` exactly as
`_check_fn` checks an `fn`, against the contract in the **trait** (`_impl_rtype`): refinements
from the trait's signature, HM types from the `TFnDecl` `infer.py` had already built for that same
body, parameter *names* from the impl (so a dependent contract still binds what the author wrote).
**And because every impl is now held to that signature, a CALLER may read it** - `_rtype_of_sig`
installs the trait's refinement as the method's global contract, where before the predicate was
thrown away. The halves are not separable: **a contract the callers trust and nobody checks is
exactly the false proof V2.2' was about.** The reading is *earned* by the checking.

**TWO THINGS FELL OUT, both worth keeping.**
**(a) NOTHING NEEDS SUBSTITUTING, and that is a result rather than a shortcut.** The plan (and my
own note in this log) said "the impl's type substituted for the trait variable". It is not needed:
a refinement may only sit on a base **the logic can name**, and a trait variable is not one -
`_rtype_of_syn` rejects `{v : a | ...}` outright. So a trait signature contributes **predicates and
nothing about the type**, and the types come from HM, which checked them at the *concrete* type
already. The substitution would have been ceremony over an empty map.
**(b) A TRAIT NOT DECLARED HERE IS NOT AN EXCUSE TO SKIP THE BODY.** `Copy` and `Show` are
builtin: no `TraitDecl`, no signature to read. Every part then falls back to its HM type - **a
trivial contract is still a contract, and the body is walked all the same.** "I have no contract
for this" must never become "I need not look", which is V1''s rule wearing today's clothes.
And one small V2.2'(d) extension: `NONNEG_UF` is now withheld from names a **trait** declares too.
A trait method called `string_length` is the program's; the primitive's axiom is not about it.

**THE COUNTS ARE THE FINDING.** New pair `17_impl_{safe,unsafe}` (safe file **checked and run**).
Under the old checker **both halves had exactly ONE obligation** - `share`'s division, out in
ordinary code - and **both failed it**, because the contract that discharges it had been thrown
away. Now there are **four**: the safe file proves all four, and the mutant is caught **twice**,
once per hook - an arm returning `0` where the trait promised `{v : Int | v > 0}`, and a division
inside a body that nothing else reads. *Too weak outside, blind inside; one bug, and the count
says so.* `prove` **35 → 37 ok / 0 fail**.

**Everything else unmoved:** drift 22/3/3/0, conservative 90/0/0, solver **16/0 (byte-identical
again - `solver.py`, `pred.py`, `parser.py`, `lexer.py`, `tree.py`, `infer.py` all untouched; the
rung is entirely inside `refine.py`)**, robust **45/0/0 with every verdict on 07's corpus exactly
where it was** - its impl bodies divide by nothing, so the fix adds obligations only where there
is something to prove - fuzz 3000 / 0 unsound.

**KNOWN, AND LEFT (the weak direction, on purpose).** A call's postcondition still reaches the
logic **through a name**: `let w = weight(c) in total / w` proves; `total / weight(c)` does not,
because the division's VC assumes `env.facts` and a bare subexpression's *synthesised* refinement
is not one of them. `17_impl_safe` is written with the `let`, and says why in its header -
V2.2's own rule one rung down (**a NAME is what carries a fact out through a return**).
Materialising a synthesised refinement at its point of use is a **capability** rung, not a
soundness one, and it is not on the plan.

**NEXT = V2.3** (unchanged, and now unblocked): a measure's own result refinement proved by
structural induction, deleting `NONNEG_UF` - an axiom that becomes a theorem cannot be captured.

**Files:** `08/src/refine.py` (`_check_impl`, `_impl_rtype`, `_rtype_of_sig`, the `TraitDecl` arm
of the contract loop, `rebound`), `prove/17_impl_{safe,unsafe}.lark` (new),
`08/tests/prove_difftest.py` (EXPECT + RUNS), `PROVE.md` (V2.2''), `08/README.md`,
`prove/README.md`.

### 2026-07-14 - **PROVE V2.2' OK - I went looking for a false proof and found four.**

**Why this session exists.** V2.2 shipped green, and the honest question after a rung that adds
*power* to a verifier is not "did the tests pass" but **"can it now prove something false?"** I
had left one thing on the table in the V2.2 write-up - a note that Float equality reaches the
logic and a NaN might make an `else` branch assume `not (x == x)` - labelled *pre-existing, out
of scope*. Set asked for it to be repaired. It was real, it was reachable, and pulling on it
turned up a second bug underneath that is worse and has nothing to do with floats.

Then Set asked whether there were **more problems worth targeting**, so I kept going and found
two more - a different family, and in some ways a nastier one.

**Every probe: `ok: N obligation(s) proved`, then `ZeroDivisionError` on the very next line.**
These four are the only false proofs this project has produced. They fall into two families:
**believing something the checker had not established** (1, 2), and **speaking about a name that
no longer meant what the checker thought it meant** (3, 4).

**BUG 1 - a Float may not enter the logic.**

    fn f(x : Float, d : Int) : Int =
      if x == x then 0 else div(100, d)      -- div's contract: {v : Int | v != 0}

`x == x` is **valid** in the logic: equality is an equivalence relation, congruence closure makes
it reflexive, and it has to. It is **false at run time when x is NaN** - and Lark reaches NaN the
ordinary way, `0.0 / 0.0` (`cek.py:304`) and `float_sqrt` of a negative. So the checker assumed
`not (x == x)` in the else branch, found the hypotheses contradictory, and proved the branch
**vacuously** - while the machine ran it and divided by zero.

The second half of the same lie needs no NaN at all: **`0.0 == -0.0` is TRUE at run time and they
are DIFFERENT VALUES**, so congruence concludes `f(0.0) == f(-0.0)` for an `f` that can tell them
apart (`1.0 / x` is +inf for one, -inf for the other). **Reflexivity fails in one direction and
substitutivity in the other - and those two are the entirety of what a sort of `OTHER` grants.**
`OTHER` means *you may NAME me but not OPEN me*: correct for a String, a Buf, a List. **Too much
for a Float.** So a Float now has a sort of its own, `refine.FLOAT`, at which **no term is ever
built** - not opaque, **unspeakable** - guarded in `term_opt`, which refuses the term at the
moment of construction, so a constructor with a Float field is unnameable too (its *argument*
was) and a predicate over Floats is a refinement **error** instead of a silent lie.

*The bit worth remembering:* the first fix **looked right and did nothing.** The probe still said
"2 proved". The sort has to be set on **both roads into a binder's type** - `rtype_of_mono` for an
inferred one and **`_rtype_of_syn` for an ANNOTATED one**, and my probe's parameter was annotated,
so it went down the road I had not fixed. A default of "merely opaque" is the wrong default for a
Float, and it was sitting in a fall-through.

**BUG 2 - "I could not translate this" is not "this is true." And there is not a Float in it.**
Dumping the VCs to find out why bug 1 survived showed the hypothesis had become `not (true)`.
Both `if` sites read

    cf = formula_opt(c, env) or Top()

and `formula_opt` returns `None` for *I cannot express this condition*. That `or Top()` turned it
into **true** - so the else branch assumed `Not(Top())`, which is **FALSE**, and from false every
obligation in that branch follows. The guard in the fixture is `x * y > 0`: merely **non-linear**,
which is the ordinary, everyday way out of a linear-arithmetic fragment. Any unreadable guard
would have done - a Float compare, a String compare, a call through a local binding. This bug is
**older and wider than V2.2** and had been in the checker since V1.

The fix is `refine._branch`: a condition the logic cannot express **constrains nothing**, so
neither branch may learn anything from it - not the positive, and above all **not the negation**.
The `synth` join keeps what still survives (`pt or pe` - the value is one branch's or the other's,
which is the honest weakening of the conditional join).

**BUG 3 - a UF symbol is a global function, and only that.** The hunt for more had a thesis:
**the dangerous places are wherever the checker turns a name, or a "don't know", into a value.**
Bug 2 was the second kind. This is the first.

    fn size(b : Int) : Int = 0
    fn take(b : Int, k : {v : Int | v != size(b)}) : Int = div(100, k - size(b))

    fn bad(b : Int) : Int =
      let size = fn(x : Int) => 1 in          -- the shadow
      if 0 != size(b) then take(b, 0) else 0  -- proved.  size(9) is 0 at run time.

`take`'s contract is `05_buf`'s idiom - the oldest thing in the suite, a contract written with a
function the program itself defines, uninterpreted to the solver. The logic names its symbols by
their **source name**, so the guard and the contract both say `App("size", (b,))` - **and they
are two different functions.** Congruence closure did what congruence closure does and identified
them. The obligation `k != size(b)` (with `k = 0`) fell straight out of a guard about a lambda
that has nothing to do with it.

The fix is one condition in `term_opt`: refuse to build `App(f, ...)` when **`f ∈ env.vsorts`**.
`vsorts` holds the *value variables* - parameters, `let`s, match binders, global values - and
**never a global function**, so a name found there is not the symbol a contract could have meant.
**A locally bound function is unspeakable**: its applications are no term at all. Nothing sound is
lost, and that is the argument for the fix rather than a hope about it - a local function has no
contract to read off and no equations to instantiate, so all it ever had was **congruence**, and
congruence is exactly what was wrong.

**BUG 4 - an axiom is about a function, not about a name. And this one is worse, because nobody
has to CALL it for it to fire.**

    fn string_length(s : String) : Int = 0 - 4          -- a legal declaration
    fn safe(s : String) : Int = div(100, string_length(s) + 4)   -- "proved".  100 / 0.

`refine.NONNEG_UF` is V1's single hand-written belief: `string_length(t) >= 0`, instantiated at
every such term a VC mentions. It is **true of the primitive** - and a program may declare a
`string_length` of its own, which overrides the builtin *everywhere*, including in the CEK
machine. The axiom was then a flat lie about the program's own function, and it fired **without
the program doing anything at all** except mention the name.

Fix: `Refiner` intersects `NONNEG_UF` with the names the program **leaves alone**, and hands the
result to each VC (beside `cons`, and for the same reason - which axioms fire is a property of
the obligation). Note the shape it shares with bug 3: **`15_shadow` is a name captured by a
`let`, `16_axiom` is a name captured by an `fn`** - one steals a contract, the other steals an
axiom. And this fix is temporary in the good sense: **V2.3 deletes `NONNEG_UF` outright**, and a
theorem cannot be captured.

**THE RULE, and it is V1''s rule moved one level up.** V1' made every exhausted budget *inside
`solver.py`* resolve toward **"cannot prove"** - a budget can cost a proof that was deserved, it
can never manufacture one that was not. That rule now also binds the checker that **builds** the
obligations: **where it cannot speak, it must say NOTHING - never `true`, never a negation, and
never a claim about a name it does not own.** A verifier's silence is cheap. Its confidence is
not.

**Numbers.** `prove` **27 → 35 ok / 0 fail**: four new pairs - `13_float`, `14_guard`,
`15_shadow`, `16_axiom`, each `{safe,unsafe}`, each mutant pinned `unproved`. **Every safe file is
RUN**, and that is what shows the fix cost nothing a program was entitled to: same guard, same
obligation, still proved, still prints its answer (`15_shadow_safe` keeps `05_buf`'s idiom and
prints 25; `16_axiom_safe` is `16_axiom_unsafe` minus one declaration, and it still leans on the
axiom - `string_length("abc") + 4 = 7`, so it prints 14). Everything else unmoved: drift
**22/3/3/0**, conservative **90/0/0**, solver **16/0 and still byte-identical**, fuzz **3000 / 0
unsound**, and **robust 45/0/0 with every verdict exactly where it was.** That last one is the
tell: **the fix deleted no proof that was a proof.**

**Files:** `08/src/refine.py` only (`FLOAT`, `_sort_of_term`, the `term_opt` guards - Float *and*
the shadowed-name refusal, `_rtype_of_syn`'s Float case, `sort_of_rtype`/`sort_of_mono`, `_branch`,
`VC.nonneg` + `Refiner.nonneg` + `uf_axioms(fs, nonneg)`), `08/tests/prove_difftest.py` (eight pins
+ four RUNS), new `prove/1{3,4,5,6}_*.lark`; docs in `PROVE.md` §4 (the V2.2' rung), `08/README.md`,
`prove/README.md`. **`solver.py`, `pred.py`, `parser.py`, `lexer.py`, `tree.py`, `infer.py` are
untouched by the whole soundness pass** - every one of these was a bug in what the checker *said*,
not in what the solver *decided*.

**> THE NEXT THING TO FIX (found at the end of the session, not fixed): `impl` BODIES ARE NEVER
CHECKED.** `refine.py` imports `ImplDecl` and **never matches it**. Two halves, and only one of
them is comfortable:
- *The comfortable half.* A refinement on a **trait method's signature** is not believed either -
  the scheme comes from `_infer._register_trait_decl` and `_rtype_of_mono` erases it to a trivial
  predicate, so a call site learns `true` and proves nothing. A lying impl (`fn size(b) = 0`
  against `size : a -> {v : Int | v != 0}`) is therefore **not** a false proof. The contract is
  *dropped*, not *trusted* - the sound direction, by luck rather than by design.
- *The uncomfortable half.* **No obligation is raised inside an impl body at all.** Put
  `div(100, 0)` in one and the checker reports **`ok: 1 obligation(s) proved`, exit 0** - the
  division is simply not seen. That is not a lie in the logic; it is a lie in the **report**, and
  a reader takes "ok" to mean the program was verified. **Silent under-verification is the one
  failure mode a verifier may not have** - and `07/samples` use traits (`impl Copy for ...`), so
  this is not a corner.
- **Fix:** check each `ImplMethod` as an `fn` against the trait signature's rtype (with the impl's
  type substituted for the trait variable) - which also makes the refined trait method *mean*
  something, and is the right rung to put a `17_impl_{safe,unsafe}` pair on. Or, at minimum,
  **refuse to be silent**: a program with an unchecked impl body must not print `ok`.

**STILL OPEN, and now written down rather than shrugged at.** Three gaps beside the impl one,
none of them a false proof against the CEK machine, all real:
1. **The logic is ℤ; the RV32 and C backends are 32-bit.** Omega decides over unbounded integers,
   and the reference semantics is Python's bignum - so the checker is sound *for the machine it
   verifies against*. It is not sound for a 32-bit target: a refinement proved over ℤ need not
   survive `i32` wraparound (`19_intoverflow` is already a known optimizer xfail). Closing it means
   either wrapping arithmetic in the logic or an overflow obligation on every `+`/`*` - a real
   rung, not a patch, and it belongs on the plan before anyone claims a *verified* firmware.
2. **Contracts are partial correctness.** Checking a recursive body assumes the declared result
   type (as it must), so a function that never returns may carry any postcondition at all and the
   checker will believe it. Nothing bad *happens* - you never reach the division - but "proved"
   quietly means "**if it terminates**". Termination measures are the standard cure and are not on
   the plan.
3. **Trait method contracts are ignored** (see above) - sound, but it means `{v : Int | v != 0}`
   on a trait signature is decoration, and a reader cannot tell.

**And what was AUDITED and is fine** - worth recording, because the value of a hunt is also in
what it clears:
- **Mutually recursive measures.** `m1`'s arm calling `m2(xs)` on the scrutinee rather than a
  field would make the equation set inconsistent (`m1(c) = 2 + m1(c)`), and **the structural check
  already rejects it** - it constrains *every* measure application in an arm, not just self-calls.
  Verified with a probe, which errors as malformed.
- **The remaining `Top()` sites.** After `_branch`, the two left are the literal `true` and a
  fresh binder's trivial refinement - both are *no constraint*, which is the weak direction.
- **`_walk_match`'s `seen`** (the negation of earlier arms) only ever holds formulas that were
  actually translated.
- **`$div` and skolems.** `x / y` is an uninterpreted `$div(x, y)` with nothing asserted about it,
  and an unnameable argument gets a fresh constant that inherits only its own declared type.

The thesis that found bugs 3 and 4 - and the impl hole - is the one to carry into V2.3: **audit
every place the checker turns a NAME, or a "don't know", into a value; and every place it stays
silent while printing `ok`.**

### 2026-07-14 - **PROVE V2.2 OK - the equations reach the solver, and the solver never noticed.**

**The claim, and it held literally.** V2.2's whole point was a *negative*: the measure
equations must reach the solver **without changing the solver**. They did. `git status`
after the rung shows `08/src/solver.py` untouched - and `pred.py`, `parser.py`,
`lexer.py`, `tree.py`, `infer.py` with it. **The entire rung is inside `refine.py`.**

**What shipped.** One mechanism, fed from two places.

- **A constructor became a TERM.** `term_opt` now names `Cons(x, xs)` as the
  uninterpreted application `Cons(x, xs)`. That is the move the rung rests on, and it
  cost nothing, because the solver already decides equality and congruence at *any*
  sort. **A constructor needed no theory. It needed a name.** Congruence gives it
  exactly what it deserves - *equal fields build equal values* - and injectivity and
  disjointness are neither asserted nor needed.
- **`measure_axioms`** (in `VC.assumptions()`, right beside `uf_axioms`, same shape)
  walks the obligation's own terms and, at each constructor term, writes down the
  instantiated equation. **No schema, no trigger, no e-matching, and above all no
  quantifier** - `forall xs. len(Cons(x,xs)) == 1 + len(xs)` would leave QF-UFLIA and
  take the decision procedure with it. What goes in is that axiom's quantifier-free
  shadow: the equation at the terms that are actually there.
- **Building** (`Refiner._synth_con`): `Cons(a, Nil)` synthesises `{v | v == Cons(a, Nil)}`.
- **Destructing** (`_walk_match`): `| Cons(x, r) =>` assumes `xs == Cons(x, r)`. Note it
  says the *humbler* thing - **what the scrutinee is** - not `len(xs) == 1 + len(r)`. The
  equation follows on its own, because the term is now in the hypotheses and the walk
  finds it there. Two hooks, but only one place where an equation is ever written.
- `prove/07_affine_borrow.lark`: `fn size` → `measure size`. **A one-word diff.**
- `prove/12_measure_safe.lark` / `12_measure_unsafe.lark`: the new pair. Four
  obligations - build, destruct, and a fact carried *across a function boundary* - and a
  mutant that lies once per hook.

**Numbers.** `prove` **25 → 27 ok / 0 fail**; `07_affine_borrow` **1 of 3 → 3 of 3**;
`10_measure_len` **unproved → proved with no change to the file**; `12_measure_safe`
4 proved *and runs*; `12_measure_unsafe` 3 of 4 unproved. Output-neutral everywhere
else: drift **22/3/3/0**, conservative **90/0/0** (still the Step-0 number), solver
**16/0**, robust **45/0/0**, fuzz **3000 / 0 unsound**.

**It closes in a SINGLE PASS, and the reason is the good part.** The walk descends into
arguments; the subterms of a constructor term are constructor terms; and an arm may only
recurse on a **field**. So there is nothing to iterate to a fixpoint. **V2.1's structural
check - written to keep the axioms *consistent* - turns out to be what makes them
*terminate*.** One rule, two jobs, and the second was not designed.

**FINDING 1 - the time bomb was DETONATED, not asserted.** `11_measure_nonstructural.lark`
was written at V2.1 against this rung. I monkeypatched `refine._measure_calls` to return
`[]` - disarming V2.1's structural check and *nothing else* - and re-ran it. The checker
instantiates `bad(xs) == 1 + bad(xs)` at the `Cons` arm's own term, derives the
inconsistency, and **verifies that `absurd` returns a negative number when it plainly
returns `0`.** One false proof, ex falso. The `Nil` arm stays *honest*, because its
equation (`bad(Nil) == 0`) is consistent - so the poison reaches exactly the terms it is
instantiated at, which is as good an illustration of "instantiation at terms" as the
design could ask for. **The structural check is load-bearing for V2.2, and now that is
measured rather than argued.** With it in place the file is still rejected at
*declaration* time, before a single VC is built - the confirmation PROVE asked for.

**FINDING 2 - a latent bug of V1's, found because V2.2 needed the thing it broke.** The
first probe failed with `cannot prove: len($v) == 1 from (len(xs) == 2 and xs ==
Cons($f1, r))` - the returned `r` was never connected to `$v`. Two causes, one on top of
the other:

- An **ADT-typed binder was `ROpaque`**, so `synth(Var r)` could not *selfify* it and the
  hypothesis `$v == r` was never written down. `rtype_of_mono` now knows the program's
  ADTs. This is V2.0's own permission applied one level further - **a value the logic
  cannot OPEN it can still NAME** - and it costs nothing, since an OTHER-sorted binder
  can only be used in equality and UF application. So the sentence finally completes:
  **refined products let a fact TRAVEL; a measure CREATES one; a NAME is what carries it
  out through a return.**
- Underneath it, a **`RecursionError` that predates V2.2** (confirmed with `git stash`).
  `_bind_pattern` built a **new `ty.Fresh()` on every call**, whose counter restarts at 0
  and therefore collides with the type variables already inside the schemes;
  `infer.instantiate` built `sub = {0: TVar(0)}` and `ty.apply` chased `α₀ ↦ α₀` until the
  stack blew - where a bare **`except Exception` swallowed it and bound NOTHING.** So a
  constructor pattern over a *polymorphic* ADT gave its binders no types at all,
  silently, in **V1, V2.0 and V2.1**. A *monomorphic* one (`| Buf(n) =>`) was always fine,
  because `instantiate` returns early when there is nothing to quantify - which is
  precisely why the suite, `Buf`-shaped as it was, never noticed. Fixed: one `self.fresh`
  per `Refiner`, seeded above every tyvar id in any scheme; `except` narrowed to
  `FRONTEND_ERRORS`. **V1''s rule, one turn worse: a crash is never a verdict - and this
  one was a crash reported as a *proof attempt*.** (Side effect: `robust` got twice as
  fast, 0.6s → 0.3s. It had been building and discarding a stack overflow per pattern.)

**Left on the table, deliberately.** The **negative** half of a constructor pattern - "the
scrutinee was *not* `Cons(x, r)`" - is not assumed in later arms. It mentions binders that
exist only inside the arm it came from, and the fact one actually wants ("it was not a
`Cons` at all") needs constructor **disjointness**, which the logic does not have and
nothing yet needs. A literal pattern's negative information is free; a constructor's is
not - **V1's finding one level down: the mention is free, the guard is not.**

**Noted, not fixed (pre-existing, out of scope).** `Float` equality already reaches the
logic through `term_opt` at sort OTHER, so in principle a `NaN` could let an `else` branch
assume `not (x == x)`. It predates this rung; V2.2 neither introduced nor worsened it.

**Files:** `08/src/refine.py` (all of it), `08/tests/prove_difftest.py` (pins),
`prove/07_affine_borrow.lark` (one word), new `prove/12_measure_{safe,unsafe}.lark`;
docs in `PROVE.md` §4, `08/README.md`, `prove/README.md`.

**Next: V2.3** - the measure's own result refinement, **proved by structural induction over
its arms** rather than assumed, which deletes `NONNEG_UF` (the last hand-written axiom in
the checker). And it is where the wall is now: V2.2 proves things about lists the program
**built**, because it instantiates at terms. A claim about **every** list is universal, and
the only way to earn one is induction.

### 2026-07-14 - **PROVE V2.1 OK - the `measure` declaration. Erasure turns out to need no eraser, and the declaration buys something the plan did not know it was buying.**

**What shipped.** A ghost, structural, total top-level declaration:

    measure len(xs : List(Int)) : Int =
      match xs with
      | Nil           => 0
      | Cons(_, rest) => 1 + len(rest)
      end

- `tree.py` - `MeasureDecl`, and *pointedly not a member of `Decl`*.
- `parser.py` - `_parse_measure_decl`, with `measure` as a **contextual keyword**.
- `refine.py` - `Measure` / `MArm` (the elaborated equations) and
  `Refiner._elab_measure`, which is the well-formedness check: exactly one arm per
  constructor (exhaustive, non-overlapping), recursion **only on the fields of the
  constructor matched**, arm bodies translated **strictly** into the fragment, result
  sort `Int` or `Bool`, and - added on contact - **the name must belong to nothing else
  in the logic**. A measure that shares a name with an `fn` is one symbol with two
  definitions; the `fn`'s body was never checked against the equations, so asserting
  both proves that a list of three elements is empty (`prove/11_measure_clash.lark`).
- `prove/` - `10_measure_len.lark` (checked **and run**) + seven negatives
  `11_measure_*.lark`, each failing as **malformed**, never as *unproved*: a bug in the
  source is not a weak proof, and V1's distinction between the two is what makes the
  suite's counts readable.

**Numbers.** `prove` **17 → 25 ok / 0 fail**. Everything else output-neutral: drift
**22/3/3** (`tree.py` and `parser.py` were already EXTENDED, so only their *reasons*
grew - and `lexer.py` never moved), conservative **90/0/0**, solver **16/0**
byte-for-byte, `harden` robust **45/0/0** + fuzz **3000 / 0 unsound**. The V1' budget
did **not** bite, and could not have: no equation reaches the solver until V2.2, which
is exactly when to re-check it.

**FINDING (a) - erasure is by CONSTRUCTION, so there is no erasure.** A `MeasureDecl`
lives in `Program.measures` and **never in `Program.decls`**. The two halves of a
program - what runs, and what is only ever proved - are separated at the parser door
and never rejoined, so `infer.py` and the CEK machine *cannot* see a measure. There is
no ghost-elimination pass because there is nothing to eliminate. And the corollary is
free, and is the better half: **calling a measure from real code is an unbound-name
error from HM** - not a rule anybody wrote, not a check anybody maintains.
`prove/10_measure_len.lark` is checked and then *run* on the CEK machine to say so out
loud, exactly as `08_erasure.lark` does for refinements.

**FINDING (b) - the declaration is what lets the name into a contract AT ALL, which is
not what the plan thought it was buying.** Under V1, `len(v) > 0` in a contract was not
an unproved obligation - it was a **refinement error**. `len` had no declaration, so it
had no sort, so `_int_term`'s guard threw it out of the ordering; and rightly, because
an unsorted symbol has no business in an arithmetic comparison. Which means **the only
names a V1 predicate could apply were the program's own functions** - a rule that
sounds arbitrary the moment you say it out loud, and saying it out loud is what the
measure declaration removes. So V2.1's win is *smaller* than "measures work" and
*larger* than "it parses": the word now **means** something to the logic (an Int-sorted
symbol with one equation per constructor), and V2.2 is only the last step of showing
those equations to the solver. `10_measure_len.lark` is the thermometer - pinned at
**1 of 1 unproved**, and it goes to `("proved", 1)` with no change to the file.

**THE FIXTURE WITH TEETH IS A TIME BOMB ARMED FOR V2.2.** The arms of a measure become
**axioms**, which is the whole reason the well-formedness check is a soundness
condition and not hygiene. `prove/11_measure_nonstructural.lark` declares a measure
whose `Cons` arm calls `bad(xs)` where only `bad(rest)` is legal - asserting
`bad(xs) == 1 + bad(xs)`, which no integer satisfies. It is not a weak axiom; it is an
**inconsistent** one, and from an inconsistency every goal follows. The file's `absurd`
returns `0` under the contract `{v : Int | v < 0}`. Today the measure is rejected at
*declaration* time and no VC is ever built. The day V2.2 instantiates equations at the
terms an arm mentions, a checker that had admitted it would discharge `0 < 0` and
report a false program as verified - the one failure a verifier may not have.
**Termination is optional for a contract and mandatory for a measure.** Re-run that
file when V2.2 lands.

**Next: V2.2** - the equations reach the solver through two hooks and nothing else
(constructor application *builds* a refined type; a constructor pattern *assumes* the
equation), instantiated at the terms the program mentions - quantifier-free, no
triggers. The claim to test is that **`solver.py` does not change: 16/0,
byte-for-byte**. Two thermometers must both go green: `07_affine_borrow` 1 → 3 of 3,
and `10_measure_len` 0 → 1 of 1.

### 2026-07-14 - **PROVE V2 opened: the ladder is written, and V2.0 (refined products) OK CLOSED. The finding: products let a fact travel; only a measure can create one.**

**The V2 ladder is now in `PROVE.md` §4** - V2.0 products → V2.1 `measure` declarations →
V2.2 the build/destruct hooks → V2.3 the measure's own refinement *proved by induction* →
V2.4 `sorted`/`bst` → V2.5 mergesort → V2.6 regression. It replaces the three-line stub. Set
settled the one open fork: **min/max measures, not ghost parameters** - no quantifier enters
the logic, and ghosts stay unbuilt unless V2.5's permutation forces them.

One thing was **checked before the ladder was written**, because the whole shape of V2 turns
on it: `self.globals` holds every fn's contract and `_base_env` seeds from it, so inside
`_check_fn` a function's own name is in scope **with its contract** - a recursive call is
checked against it and may *assume* it. **Induction on programs is already there, for free.**
V2 is that same move applied to measures.

**V2.0 - refined products. OK** Entirely in `08/src/refine.py`; **the parser needed no change**,
which was the first surprise: `_parse_atom_type` already parses tuple elements with
`_parse_type` and `{` already begins an atom type, so `({v:Int | ...}, {v:Buf | ...})` parsed on
the first attempt. Three pieces:
- **`RTuple`, positional.** A component's predicate may mention any binder in scope *outside*
  the tuple - the argument it was computed from - but not a sibling, which has no name to be
  mentioned by. That is a decision, not a shortcut: a product's components are computed from a
  common input, not from each other, and nothing in Lark has ever wanted otherwise.
- **Refinements on non-Int/Bool bases** (`{v : Buf | size(v) == size(b)}`) - which the borrow
  idiom *requires* and V1 rejected outright. Far cheaper than it looks: the binder is sorted
  OTHER, `_int_term`'s guard keeps it out of arithmetic and ordering, and the only operations
  left are the two the solver already decides at any sort - equality and UF application.
  **Congruence closure does not care what a `Buf` is.** No new theory; just permission to name
  a value we cannot open.
- **`_bind_pattern` takes the scrutinee's already-synthesised `RType`.** V1's tuple binders came
  from `infer_pat`, which can only hand back fresh type variables at sort OTHER - so every fact
  a callee had promised died at the comma. The fix was not to infer harder but to **stop
  inferring**.

**THE FINDING - and it is a correction to the ladder's own definition of done, written three
hours earlier.** I had said V2.0 would flip `prove/07_affine_borrow.lark` (V1's *documented
failure*) to proved. It went **half** way - **1 of 3** - and the half it did not go is worth
more than the half it did:
- The **consumer** is discharged. `size_of`'s contract promises `n == size(b)` and
  `size(b2) == size(b)`; the tuple pattern now delivers both into the arm; the guard adds
  `n > 0`; `take(b2, 0)`'s bound follows. Checked *non-vacuous*: weaken the guard to `n >= 0`
  and the obligation fails, so the proof is really carried by the products.
- The **producer** cannot be discharged - not by a better product, not ever. `size_of`'s body
  needs `size(Buf(n)) == n`: that taking a buffer apart and putting it back does not change its
  size. `size` is uninterpreted and `Buf(n)` is an opaque constructor application, so **the two
  goals left standing are the two halves of one missing measure equation.**

> **Refined products let a fact TRAVEL; only a measure can CREATE one.**

That sentence is why V2.0 could not have been the last rung, and it was found by *building* it,
not by reasoning about it. `07_affine_borrow` is now the thermometer for V2.2: pinned at 1 of 3,
and it must read 3 of 3 the day constructor patterns learn to speak.

**Numbers.** New `prove/09_product_{safe,unsafe}.lark` gives V2.0 a green end-to-end case that
needs no measure at all - a pair of bounds for `string_slice`, a real builtin with a real
precondition; the mutant's right edge is one past the end and its helper declares that honestly,
so **no function is wrong, the interface between two of them is**. `prove` **15 → 17 ok / 0 fail**.
`07_affine_borrow` re-pinned `(unproved 1,1) → (unproved 2,3)`. Everything else **output-neutral**:
drift **22/3/3**, conservative **90/0/0**, solver **16/0 byte-for-byte** (V2.0 touched the VC
generator and *not* the decision procedure - as V2.2 must not either), `harden` robust **45/0/0**
+ fuzz **3000 / 0 unsound**.

**Next: V2.1** - the `measure` declaration. A new top-level decl, deliberately *not* an `fn`:
a measure is ghost, structural and total, and an `fn` is none of those three.

### 2026-07-14 - **PROVE V1' OK HARDENED - the fuzzer found a hang, and the hang taught the rule: a budget must give up in the sound direction.**

V1 was feature-complete and green. Green is not robust. Two harnesses were added that do
not ask *is the answer right* but *does it survive* - and both earned their keep.

**New: `08/tests/robust_sweep.py` (`make -C 08 robust`) - 45 ok / 0 fail / 0 crash (0.6 s).**
Every file of 07's real corpus through the refinement checker, in-process, verdict pinned
per file. The point is the third column: **a crash is never folded into a verdict.** "Cannot
prove" and "the checker fell over" must never leave the same footprint. It found three
frontend exceptions escaping the CLI as raw Python tracebacks - `TraitBoundError`, `LexError`,
`UnifyError` (fixed: `refine.FRONTEND_ERRORS` / `REFINE_ERRORS`, so the user sees
`type error: no Show instance for δ`). It also found **two true positives in Lark's own code**:
`| Div(a, b) => eval(a) / eval(b)` in `07/samples/05_expr.lark` and `09_parser.lark` is a
latent division by zero that has been running for the whole project. The checker is the first
thing to notice.

**New: `08/tests/solver_fuzz.py` (`make -C 08 fuzz`) - 3000 cases, seed 7, ~13 s: 2556 agreed,
135 SAT with no model in the box, 309 too big, 0 unsound.** Random QF-UFLIA decided twice -
once by `solver.py`, once by brute force over `[-3,3]` on the *occurring* symbols only, with
assignments that violate UF functional consistency discarded. Only the **fatal** direction
fails the run: a contradiction that isn't there, or a proof with a counterexample. The other
direction is *reported and never failed* - Omega is exact over ℤ, a small box is not, and a
harness that cannot tell the two apart would be worse than none.

**THE FINDING (book-grade). The solver could hang - and the hang lived on the boolean/arithmetic
seam.** `Theory.consistent` asserts that distinct integer literals are distinct (`3 ≠ 4`);
`_lia` decides `a ≠ b` by case-splitting it into `a < b` or `a > b`, at a cost of 2^k. Neither
is wrong. Together, a formula merely **mentioning** seven constants arrived at `_lia` with 21
disequalities and asked for 2²¹ calls to Omega - the profile showed the split entered 1,035,682
times, `omega` 517,825 times, for *one* random formula. Not a wrong answer: **no** answer, which
in a type checker is the worse failure. Fixed twice over - ground disequalities are settled by
looking at them and never reach the split (only a ground pair that is actually *equal* is a
contradiction worth recording), and the split is fenced by `MAX_DISEQ = 12` and
`MAX_SPLITS = 20000`.

**And the rule the fence taught, which is the part worth keeping: a budget must give up in the
sound direction.** A new `Budget` exception replaces the old `PredError`, and **every `except
Budget` in `solver.py` resolves towards *consistent*** - "I found no contradiction". That makes
`satisfiable` true, `valid` false, and `refine.py` answer **"cannot prove"**. An exhausted budget
can therefore cost you a proof you deserved; it can never manufacture one you didn't. Checked
directly: with a contradiction hidden behind an exhausted split, the solver **declines to prove
the goal even though it follows *ex falso***. It surrenders capability, not soundness. (The old
behaviour was worse than slow: exhaustion raised `PredError`, which the CLI prints as
`refinement error:` - a *resource limit* reported to the user as if their **program** were
malformed.) 91 disequalities that were 2⁹¹ splits now answer in 3 ms.

**Output-neutral, and that is the claim being made:** drift 22/3/3/0, conservative 90/0/0,
solver 16/0, prove 15/0 are byte-for-byte where V1 left them. New `make -C 08 harden` = `test`
+ `robust` + `fuzz`. `PROVE.md` gains a V1' section; `07/src` untouched (§0.1).

**Next: PROVE V2 - measures.** Unchanged by this pass.

### 2026-07-13 - **PROVE V1 OK COMPLETE - Lark proves programs. Refinement types, a from-scratch QF-UFLIA solver, and the affine × refinement rule settled.**

V1 of `PROVE.md`, end to end, in `08/src` - and `07/src` was not touched (§0.1).

**Three modules extended, and the third by one line.** `tree.TRefine` joins the syntactic
`Type` union; `parser._parse_refine_type` makes `{` begin a type (**the lexer needed no change
at all** - `{`, `}`, `|` were already tokens - and LL(1) survives, because `{` begins no other
type and a predicate is an expression, whose grammar has no `|`, so the predicate parse stops at
the closing brace by itself); and `infer.syntype_to_mono` gains **one case**, which *erases*
`TRefine` to its base type. That one line is the entire interface between the refinement layer
and the language: HM never sees a predicate, generalisation never sees one, and - decisively -
**the affine checker never sees one.**

**Three modules added, layered so each can be wrong without the one below it being wrong.**
- `pred.py` - the predicate language. QF-UFLIA: linear integer arithmetic, booleans,
  uninterpreted functions with equality. Multiplication is *literal × term* only, so `x * y` is
  **not a term you can write**: §7's "resist general nonlinear arithmetic" is enforced at
  well-formedness rather than hoped for downstream.
- `solver.py` (~780 lines) - the decision procedure, **from scratch**. Congruence closure
  (union-find + signature saturation to fixpoint); the **Omega test** (equality elimination,
  including the symmetric-modulus σ trick when |coef| > 1, then Fourier-Motzkin with **real
  shadow**, **dark shadow** and **splinters** - the splinters are what make it a *decision*
  procedure over ℤ rather than over ℚ); Nelson-Oppen in the small between the two (opaque int
  terms get one LIA column keyed on their congruence class; forced arithmetic equalities are
  merged back into CC); all under a DPLL(T) boolean search. **The `--smt`/Z3 escape hatch in the
  plan was never needed and was never built. Lark's verifier has no external dependency.**
- `refine.py` (~760 lines) - the VC generator. Bidirectional `synth`/`check`; **subtyping *is*
  entailment**; `Env` is immutable, so a path condition cannot leak out of the branch that
  assumed it; contracts are **dependent** - an argument's obligation is checked with the earlier
  arguments substituted in, which is what lets `string_slice`'s `b` say `a <= v`.

**Validated, not trusted.** The solver was fuzzed against brute force on **4000 random integer
systems** (three apparent mismatches turned out to be Omega being *right* and my search box being
too small - the witnesses were outside ±40; and one hand-written expectation of mine was simply
wrong). Two purpose-built grey-region systems - one SAT, one UNSAT, both decidable *only* by
enumerating splinters - are now permanent rows in `make -C 08 solver`, so the completeness path
is never dead code that nothing runs and nobody notices is broken.

**The suite (`prove/`, `make -C 08 prove` = 15/0).** Safe programs paired with mutants carrying
one real bug each, expected verdict pinned per file *as a count*, because an obligation that
quietly **disappears** is as suspicious as one that starts failing. Bounds on `string_index` -
the primitive the self-hosted lexer calls on every character - div-by-zero, non-negativity,
`string_slice` totality, and a contract written with a function the program itself defines.
`08_erasure.lark` is checked **and then run**: every obligation discharged, then it executes on
the ordinary CEK machine and prints what it promises, because the predicate is gone before the
runtime sees a type.

**THE FINDING (§7 asked for it early; both halves are book-grade).**
1. **A mention is not a use.** Naming an affine binding in a predicate does not consume it -
   *by construction*, since erasure happens before inference traverses anything. Sound because
   **affinity in Lark restricts USE, not TRUTH**: the language is pure, so consuming a value
   *moves* it rather than mutating it, and a fact proved about an affine binding stays true for
   its whole scope. **In a language with mutation this rule is unsound.** The permission is paid
   for by purity, and by nothing else. The corollary that keeps it honest: a predicate may only
   *apply* functions (uninterpreted), never *evaluate* Lark code - so it cannot force or observe
   an affine value, only name it.
2. **The guard is not free even though the predicate is.** `if size(b) > 0 then take(b, 0)` is
   rejected by the affine checker: evaluating the guard is a real use of `b`, so you cannot check
   a precondition about an affine value and still pass the value on. The standard borrow idiom
   (`size_of(b) : (Int, Buf)`) fixes the affine error and typechecks - and V1 *still* cannot
   discharge the resulting VC, because it has no refined tuple components. So the two features
   are individually fine and **jointly blocked for non-Copy types**, and **refined products
   become a V2 requirement that was derived rather than guessed.** (`prove/07_affine_guard.lark`,
   `prove/07_affine_borrow.lark`.)

**Two smaller findings.**
- **An uninterpreted length can be negative.** `string_slice(s, 0, string_length(s))` - slicing
  the whole of a string, which cannot fail - was *unprovable*, because nothing in the logic rules
  out a length of -1. Fixed with `refine.NONNEG_UF`, an axiom **instantiated on the terms an
  obligation mentions** (so the fragment stays quantifier-free), and it is the one-symbol
  stand-in for what V2 makes a real measure signature. The suite caught this, on a *safe* file.
- **`conservative` went red for a moment, and it was noise - of a kind worth knowing about.**
  The reject fixtures die with an uncaught Python exception, so their stderr is a *traceback*,
  and a traceback carries the line numbers of `infer.py` itself. Adding nine lines shifted every
  number below them without changing a single thing Lark decided. Canonicalised - and the first
  attempt at the canonicalisation matched *nothing*, because Python 3.14 colourises tracebacks
  and the digits sit inside an ANSI escape. A canonicalisation that silently matches nothing
  looks exactly like one that works.

**Baselines (`make -C 08 test`, all green):** drift **22 identical / 3 extended / 3 added / 0
missing** - conservative **90 ok / 0 fail / 0 skip** - *unchanged from the Step-0 baseline, so
refinements are a conservative extension of Lark, demonstrated rather than asserted* - solver
**16 ok / 0 fail** - prove **15 ok / 0 fail**.

**NEXT: V2 - measures** (lift `len`/`elems`/`sorted`/`bst` into the logic), then refined products
(finding 2), then re-verify Lark's own samples: `01_mergesort` returns a sorted permutation,
`02_bst` maintains ordering. The corpus proving itself *correct*, not just safe.

*(Uncommitted - Set commits.)*

### 2026-07-13 - **PROVE Step 0 OK - THE ORACLE IS FORKED. `08/` exists, and the conservative-extension baseline is green *before* the first refinement.**

PROVE §8 Step 0, done exactly as written: `07/src` → `08/src` (25 files, `rsync` minus
`__pycache__`), plus the two checks that make the fork mean something. **No file in `07/`
was touched** - the three fixpoints (`49a4921c`, `829410dc`, `f1dedfa9`) and both
`BASELINES.md` are untouched by construction (§0.1).

**New: `08/` (`make -C 08 test` runs both).**

| target | result | what it holds |
|---|---|---|
| `make -C 08 drift` (`08/tests/drift.py`) | **25 identical / 0 extended / 0 added / 0 missing** | every file in `08/src` is byte-identical to its `07/src` twin unless declared |
| `make -C 08 conservative` (`08/tests/conservative_difftest.py`) | **90 ok / 0 fail / 0 skip** (~75 s) | 07's whole 45-file corpus answers *identically* through `08/` - through `infer.py` **and** `cek.py` |

- **`drift.py` carries two tables, `EXTENDED` (modules this axis changed) and `ADDED`
  (`refine.py`, `solver.py`, ...), each entry with a reason. They are empty today, and they are
  the honest running measure of how large the extension has grown** - a module that drifts
  without appearing in one of them is a bug, not a feature. It also fails on a *stale* entry
  (listed EXTENDED but identical), so the tables cannot rot into decoration.
- **`conservative` compares `cek` as well as `infer` on purpose.** Refinements erase at
  runtime; a refinement that changes what a program *prints* is not a refinement. The evaluator
  row is where that would show up.

**The one wrinkle, and it was worth the 20 minutes: the first run came back 86/4, on a
byte-identical copy.** Neither red was divergence, and neither was harmless to leave in:

1. **The oracle is nondeterministic across runs - `06_lists` and `25_torture` [infer].**
   `infer.py:420,588` renames a wildcard param `_` to `_anon_{id(node)}`, baking a CPython
   object address into the typed AST it prints. Two runs of **`07/src` alone** differ
   (`_anon_4462712208` vs `_anon_4430665104`). This is the *same* §7 finding M5 hit and
   canonicalised in `self/tests/emit_c_difftest.py`; the new harness now applies the identical
   `_anon_\d+ → _` rule, and cites it. **A pre-registered hazard that fires on day one of a new
   harness is the argument for building the harness before the feature.**
2. **My own canonicaliser was the other two** (`Stdlib`, `09_modules/shapes` [cek]) - it
   rewrote the *tree* path, so the oracle's `(no main in ...)` message got scrubbed on the 07 side
   and not on the 08 side. Now only the interpreter's own `src` path is canonicalised. The rule
   the fix restores: **canonicalise the thing that differs for a reason you can name, and
   nothing else.**

**NEXT: PROVE V1 steps 1-3, in Python, in `08/src`** - `{v:b|p}` surface syntax + predicate AST,
VC generation at the subtyping points (application, return, `let`, `if` path conditions), then
the QF-UFLIA decision procedure (congruence closure + linear integer arithmetic; Z3 behind
`--smt` only to unblock, never as the resting state). **Settle affine × refinement early** (§7):
a predicate that mentions an affine binding must not *consume* it - refinements are erased and
must be use-neutral. That is the book-grade finding on this axis, and it wants deciding before
the VC generator hard-codes an answer to it.

**One open naming question for Set:** PROVE §6 puts the safe/unsafe verification suite at
top-level `lark/prove/`, but `repo/prove/` already exists as the generated *proof strand* of the
book. Two different things one word apart. I would put the suite at **`08/prove/`** (it is the
fork's fixture set, and it travels with it) and leave `prove/` to mean the book strand - but the
plan says otherwise, so it is Set's call, not mine.

*(Set committed the fork mid-session as `7abd47b`; that commit caught `conservative_difftest.py`
before fix (2) above, so the working tree's version is the right one.)*

### 2026-07-13 - **the axis handed over to PROVE. F3.4 retired into an exercise; vendoring buried; ch11 written.**

Closing session after the silicon result. No code changed; the tree was tidied and the
next axis was chosen. **The next session starts at PROVE §8 Step 0 (fork `07/src` → `08/src`).**

**Audit before the handover** - asked "is anything forgotten?", and checked rather than
remembered. `make -C self drift` clean (204 files, pins agree). Working tree carries the nine
hardware-verified `.uf2` + this session's edits, uncommitted (Set's). One [ ] remained on either
plan, and it is now gone:

- **F3.4 (graph-colouring allocator) - RETIRED FROM THE PLAN → book ch11 Exercise 11.3.**
  Nothing depended on it: no fixpoint, no baseline, no chapter. The *reader* already has
  `coloring.py` + `igraph.py` in the oracle, so the book teaches colouring from the Python
  without the Lark port existing. **And it is a better exercise than a milestone**, for a reason
  worth keeping: a correctly-ported colouring allocator **cannot** be checked by byte-identity -
  it must emit *different assembly with identical behaviour* than linear scan. It is the first
  test in this whole project that is not byte-identity, which makes it the right place to ask the
  reader what byte-identity was ever a proxy *for*. SELFHOST's F3.4 entry keeps the ~529-line
  scope and the pre-registered §7 findings as hints.

- **VENDORING: BURIED.** `self/vendor/` and `self/VENDORING.md` are gone from the tree (the
  "DEAD END, DO NOT RE-DERIVE" block below is the record). Removed the last **forward-looking**
  reference, in PROVE §0.1, which told a future session to reuse `check_drift.sh` - a file that
  no longer exists. The `08/`↔`07/` drift check is now specified as a plain `diff -r` plus an
  **explicit allow-list of the modules this axis has deliberately extended** (the allow-list *is*
  the honest statement of how large the extension has grown - a better design than the one it
  replaced). Mentions in this log, in `BASELINES.md`, and in the lex/parse difftest comments are
  **kept on purpose**: they explain why `corpus()` is an explicit list and not an `rglob`. Do not
  "restore" anything on their account.

**Book (ch11 + ch01).** Wrote ch11 §*The last link* - the chapter that pays for the board. Its
argument, and it is the one the whole method was owed: **agreement between two implementations is
evidence about their relationship, not about the world.** The port and the oracle are not
independent witnesses - one was written from the other - so they share their misunderstandings as
reliably as they share their logic, and a differential is blind to any error *both* sides make.
Hence the last link in the chain has to be physical. The day's serial-port bug appears as one
clause (the cause is "a default argument in a standard library and of no interest to anyone"); its
two *general* lessons are the section: **a test that has never passed is not evidence about the
system under test, it is evidence about itself** (a new harness is an uncalibrated instrument, and
its first reading is a claim about two things at once), and **run a new instrument against a
known-good specimen before trusting what it says about an unknown one**. Added the matching
**third consequence** to ch01's differential-testing section, where two were already listed - the
limit of the method, forward-referencing ch11. Four exercises added to ch11 (first use of the
`exercise` environment, which `main.tex` had defined but nobody had used). `make -C book paths`
green, book builds.

---

### 2026-07-13 - **F3.3 CLOSED: 9/9 ON SILICON. And the bug was a default argument in the standard library.**

**THE CAPSTONE IS CLOSED. `make`-free, one command, nine images, a real Pico 2/2W: 9 ok / 0 fail.**
Every program prints on the Hazard3 core exactly what `cek.py` prints - `09_parser` included, which is
**Lark's own parser running on a microcontroller, compiled by a compiler written in Lark**. No BOOTSEL
press was needed for any of the nine (`picotool -f` resets the board itself). `07/firmware/` now holds
the nine **hardware-verified** images: the exact bytes that were flashed, shas unchanged from claim 2.
SELFHOST F3 is done but for the optional F3.4.

**THE BUG WAS OURS, AND IT WAS `tty.setraw()`.** For most of the session the board was silent and it
looked like hardware. It was Python's standard library:

> `tty.setraw(fd)` defaults to **`TCSAFLUSH`** - *apply these settings, and **discard any pending
> input***.

Opening the port asserts DTR. DTR releases the firmware's `while (!stdio_usb_connected())` wait. The
board prints **immediately** - microseconds later. And our *very next line* flushed the transcript into
the bin. We then listened for 25 s at a board that had already said its piece and halted. `screen` does
not flush on open, so `screen` always worked - which is exactly what made it look like DTR, or macOS's
CDC driver, or the soft-reboot USB session, or the silicon. **Fix: set raw mode by hand with `TCSANOW`,
which never discards.** (`a[0]=a[1]=a[3]=0`, `CS8|CLOCAL|CREAD`, `VMIN=VTIME=0`.)

**THE MOVE THAT CRACKED IT - flash a known-good artefact.** Half a session of host-side theories
(call-in vs call-out node, `CLOCAL`, blocking opens, explicit `TIOCMBIS` DTR, open delays of 1/3/6 s,
close-and-reopen) all failed *identically*, which should have been the clue. What settled it was
flashing **the OLD `07/firmware/01_mergesort.uf2` - the image Set had verified on this very board months
ago - and finding it EQUALLY SILENT.** A known-good artefact cannot be a compiler bug: the fault had to
be in the reader. From there the decisive question was cheap - *does `screen` still print if we do not
replug?* Set: **"no it does not print."** That one word killed the last wrong theory (that our opens
never reached the chip) and proved the opposite: our open **had** woken the firmware, it **had** printed,
and we had **thrown the bytes away**. The fix was four lines.

**Two lessons worth keeping** (both are for the book): a test harness that has never once passed is
**not evidence about the system under test** - it is evidence about itself; and when a known-good
artefact fails your new test, **stop debugging the artefact.**

**The earlier hypothesis in this log - "picotool's soft reboot leaves a stale USB session" - was WRONG**,
and is struck. Soft reboot re-enumerates fine; `--board` now flashes all nine through it without a
button press. The 0.3 s port reappearance was real and irrelevant.

---

**Everything below was written before the board was in hand, and its diagnosis is superseded** (kept
for the record of how the harness was built, and because the pseudo-terminal tests it describes are
still what guards the capture loop).

### 2026-07-13 - **the board arrived, and the silence was OURS.** *(diagnosis superseded - see above; it was `TCSAFLUSH`, not the soft-reboot session)*

Set ran `--board` and got a wall of nothing, then: *"the script is confusing... it is unclear if it is
running, if the Pico is connected or not."* Both complaints were fair, and the second one was a bug.

**WHAT THE BOARD SAYS.** The nine images are **not** implicated. The chain of experiments, in order,
each one killing a hypothesis:
1. `--board` flashed fine, port came back as `/dev/cu.usbmodem1101` - **and 180 s of silence.**
2. **DTR was not the cause.** A plain `os.open` on macOS already shows `DTR=Y RTS=Y` (`TIOCMGET`);
   asserting it explicitly changed nothing.
3. **Not a race.** Rebooting the app and grabbing the port 0.3 s later: still silent.
4. **THE DISCRIMINATOR.** Flashed the **OLD `07/firmware/01_mergesort.uf2` - the image Set verified on
   this very board months ago** - and read it with the same reader: **also silent.** A known-good
   artefact cannot be a compiler bug, so the fault was ours, not F3's.
5. **Set ran `screen` by hand after a physical replug: it printed `1 2 3 4 5 6 7 8 9`.** The board, the
   firmware and the old image are all *fine*. Our reader is the thing that fails.
6. Swept the reader: `cu.*` vs `tty.*`, `CLOCAL` on/off, blocking/non-blocking, explicit DTR, opens at
   1/3/6 s, close-and-reopen - **every combination silent, each on a fresh reboot** (the firmware
   prints once per boot, so a stale board invalidates a probe; that flaw voided our first `tty.*` test).

**THE LEADING HYPOTHESIS - AND IT WAS WRONG.** ~~Every failure of ours followed a
**picotool soft reboot / flash**; the one success followed a **physical replug**. After `picotool`, the
port reappears in **~0.3 s - far too fast for a real USB re-enumeration**, which smells like macOS
reusing a stale CDC session, in which case `SET_CONTROL_LINE_STATE` never reaches the chip and the
firmware sits in `while (!stdio_usb_connected())` forever. **NEXT SESSION, FIRST THING:** ask Set to
unplug/replug (no BOOTSEL, no `screen`), then run
`python3 self/tests/firmware_difftest.py --board --only 01_mergesort --no-flash`. If it prints, the
diagnosis is confirmed and the fix is in the flash-then-connect path (force a real re-enumeration, or
prompt for a replug between images) - **not in the reader, and not in the compiler.**~~
**STRUCK.** The replug test came back **silent too**, killing this. It *was* the reader: `tty.setraw()`
flushing the transcript on open (`TCSAFLUSH`). Soft reboot was never the problem.

**THE HARNESS NOW SAYS WHAT IS HAPPENING** (the first complaint, and it is what made the second one so
opaque). `--board` gained: a **preflight** that names what is on the USB bus (`FOUND, running - USB-CDC
on /dev/cu.usbmodem1101` / `FOUND, in BOOTSEL` / `NOT FOUND`, and it stops instead of flashing into the
void); **live per-step narration** with the elapsed second (`flashing 99 KB...`, `waiting for the board to
come back on USB... 3s`, `reading 12/36 lines... 8s`), throttled when piped; a **25 s first-byte deadline**
instead of sitting mute for 180; and a **failure message that teaches** - it now prints the replug
diagnosis above rather than the old, wrong guess about a stray `screen`. New **`--no-flash`** reads the
image already on the board, which is what a replug-based flow needs.

**Left as it stands:** the board holds the OLD `01_mergesort` (the control). `07/runtime/platform_pico.c`
is **untouched** - a bounded-wait diagnostic build was written (`$CLAUDE_JOB_DIR/tmp/hw/bounded_probe.py`,
in the transcript) but never run; it is the fallback if the replug test *fails*, since it times the first
byte and so proves whether DTR ever reaches the chip. Only `self/tests/firmware_difftest.py` is modified.
**Manual `screen` remains a perfectly good way to close claim 3** if the automation stays stubborn - it
demonstrably works, and nine images by hand is an hour, not a week.

### 2026-07-13 - **claim 3 is now a test, not a ritual. The harness was written before the board arrived.**

Set: *"verify F3.3 on the pico"* - then, mid-run: *"well there will be some hours before i can get
my hand on the Pico."* So the board test could not be run. What could be done was to stop claim 3
from being the one hand-checked link in a chain that is otherwise machine-checked end to end.

**The state, re-verified before touching anything.** All nine staged `.uf2` still hash to the shas
pinned in the entry below (`9bb1dc6b1897` ... `c80e9260d60a`), and `--asm-only` re-run is **9/9
assembly-identical + 9/9 emulator-behavioural**. Claims 1, 1½, 2 are green and reproducible.

**`firmware_difftest.py --board`** (new) makes claim 3 machine-checkable. It flashes each image with
`picotool`, captures what the board prints over USB-CDC, and diffs it against `expected/<name>.txt`.
The old `--hardware` runbook (flash → `screen` → eyeball → `diff`, nine times) stays as the fallback.
Three things made it possible, and each was already true - nobody had used them:
- **`platform_pico.c` blocks on `stdio_usb_connected()` before its first line.** So there is no race
  between flashing and reading: open the port and the board starts printing *to us*. The wait that
  exists to make `screen` usable is exactly what makes the capture exact.
- **`pico_enable_stdio_usb` puts the SDK's reset-via-vendor-interface in the firmware**, so
  `picotool -f` reboots a *running* board into BOOTSEL. **The BOOTSEL button is needed at most once**,
  not once per image - otherwise nine flash cycles is a chore nobody re-runs.
- **stdlib only** (`termios`+`select`; no pyserial - it is not installed and this must not need it).

**The subtle part is when to stop reading, and the obvious answer is wrong.** Silence does not mean
"done": `08_life` and `09_parser` think for seconds *between* lines, so any idle timeout short enough
to be pleasant is short enough to truncate them - and a truncated capture reads as **a failed claim
about the compiler** when it is a bug in the harness. So `capture()` **stops on match** (it knows
what to expect), and keeps the idle timeout only as the give-up path. After a match it still waits a
grace second, so trailing garbage cannot hide behind the early return.

**Tested without the board, because "I'll find out when the hardware arrives" is how you waste the
hardware.** A pseudo-terminal impersonates the Pico's CDC endpoint and plays a real `expected/`
transcript out of the master end: (a) a program that pauses **4 s mid-transcript** - captured whole,
where a naive idle timeout truncates it; (b) one burst - captured whole; (c) `PANIC: heap` **after** a
full match - **caught**, not hidden. Plus the no-board path: it fails with *"hold BOOTSEL and replug"*,
not a stack trace. The one deliberate tolerance: `normalise()` strips **trailing** blank lines from
both sides (the wire is CRLF; a final newline is not a claim about the program). Everything else is
compared exactly.

**Also**: the F3.1/F3.2 checkboxes in SELFHOST §4 were still [ ] though yesterday closed them; ticked,
and F3.3 rewritten there to carry the re-scope and its four claims (3 green, 1 pending silicon).

**FOR SET, WHEN THE BOARD IS IN HAND - one command:**

    python3 self/tests/firmware_difftest.py --board     # hold BOOTSEL for the first flash

Green ⇒ `--install` re-pins `07/firmware/` and **F3.3 is closed**. A FAIL is the first bug hardware
has caught: it stops on the spot (does not flash over the evidence), saves `<name>.got.txt` next to
the `.S` and the `.uf2`, and prints the diff. The one to watch is **`09_parser`: Lark's own parser,
on a microcontroller, compiled by a compiler written in Lark.**

### 2026-07-13 - **F3.1 + F3.2 closed: the RISC-V backend is self-hosted. And the compiler we were about to port was not a function.**

Set said: *"continue F3.1."* It closed, and F3.2 with it, and the machine-checkable half of F3.3.
But the day's real finding came before any of that.

**THE ORACLE WAS NOT A FUNCTION.** Before porting `asm.py` I checked the thing a differential
silently assumes: that the oracle, given the same input, gives the same output. It did not.
`regalloc.py::_compute_intervals` iterated **frozensets** (`live_in`, `live_out`, `defs`, `uses`).
Set iteration order in CPython depends on `PYTHONHASHSEED`; the interval table's insertion order is
the **tiebreak of the stable sort** in `_linear_scan`; so *which `Tmp` won which register* - and
therefore every register name in the emitted assembly - **varied from run to run**. Ten of the 45
corpus files differed across seeds, with different byte lengths. `09_parser` produced **five distinct
shas in five runs**. **There was no byte-identity for F3.1's differential to test against**, and there
never had been. It was invisible because nothing downstream of `asm.py` ever compared two runs of it -
`make -C 07 difftest` compares *behaviour* across backends, and behaviour was never in doubt.

The fix is four `sorted()` calls in `07/src/regalloc.py`. What it cost to *trust* the fix is the
part worth remembering: an edit to `07/src` re-opens every frozen fixpoint, so - even though `self/`
never imports `regalloc`/`asm` and the edit is provably off the compiler path - all three were re-run
and re-confirmed: `bootstrap` `49a4921c`, `bootstrap-tc` `829410dc`, the O5' ladder `f1dedfa9`. Plus
`make -C 07 difftest` **34 passed**, which matters more than it sounds: the RV32 **emulator executes
the re-allocated code** and still agrees with CEK, so the new allocation is *correct*, not merely
*stable*.

**THE PORT (F3.1).** `self/regalloc.lark` (~360 L) + `self/asm.lark` (~600 L), and two new
differentials - the 9th and 10th in the tree:

| target | result |
|---|---|
| `make -C self regalloctest` | **32 ok / 0 fail / 13 skip** - every register and spill slot identical |
| `make -C self asmtest` | **32 ok / 0 fail / 13 skip** - byte-identical `.S`, incl. 08_life at 1,645 lines |

Both green **on the first run**. The 13 skips are `emittactest`'s exact shape (3 imports + 7 reject
fixtures + 3 CEK-overflow on deep serialised TAC). Pinned in `tests/BASELINES.md`, wired into
`make test`, and `repo/` regenerated - `make drift` caught that the canonicalisation had not reached
`repo/optimize/oracle/regalloc.py`, which is the drift checker earning its keep.

Two things made this the smallest port yet (~950 lines against `lower.lark`'s ~630 + `emit_tac_c`'s
~680): **`regalloc.lark` reuses `opt.lark`'s CFG and liveness** rather than re-porting them, and the
sizing was checked first - max 90 tmps / 142 instrs per function across 246 functions, so plain assoc
lists suffice and the arena wall never comes near. Of the four pre-registered §7 hazards, **none
bit**: the purity threading (read-only `AsCtx`, `List(String)` string-literal interning in first-seen
order, `(lines, table)` returns) was by now routine.

**THE NATIVE COMPILER (F3.2), and why it exists.** `asmtest` runs the port meta-circularly, on
CPython's stack, so the three deepest programs are skipped - and two of them (`05_expr`, `09_parser`)
are among the nine with firmware. `self/tests/rv32c.py` assembles the ten Lark modules
(`lex...opt+regalloc+asm`, **8,003 lines**) into a stdin compiler and builds it through the O5' ladder's
stage0 path into a **native binary**. `--check` = **9 ok / 0 fail**: identical `.S` to `asm.py` on
every sample, `09_parser` included (3,180 lines of RV32I). The skips were a fact about the harness,
and this is how you cash them in. It also fixes an honesty problem: **firmware built by a Python
compiler tests Python.**

**THE CAPSTONE (F3.3) - re-scoped, because the old wording was unattainable.** SELFHOST asked for the
nine committed `07/firmware/*.uf2` to be **reproduced byte-identically** from the Lark compiler. They
cannot be - **not by the Lark compiler and not by `asm.py` either**: they were built from one
unrecoverable hash seed, and no `.S` was ever checked in to diff against. So the capstone becomes
*rebuild and prove the two compilers agree on every byte*, which is strictly stronger than matching an
artefact. `self/tests/firmware_difftest.py`, all three machine-checkable claims green:

- **claim 1 - assembly identity**: self-hosted vs `asm.py`, **9/9 byte-identical**.
- **claim 1½ - behaviour in software**: that assembly, run on the RV32 emulator, prints exactly what
  `cek.py` prints, **9/9**. This gap was real: `make -C 07 difftest` sweeps `07/tests` only, so **not
  one of the nine flashable programs had ever been executed as RV32**.
- **claim 2 - image identity**: the real GNU RISC-V toolchain (the pico-sdk *is* installed, under
  `~/.pico-sdk` - cmake, ninja, toolchain, picotool, just not on `PATH`) turns it into **nine `.uf2`,
  byte-identical from both pipelines**. Staged in `build/firmware/` with `expected/<name>.txt`.
- **claim 3 - silicon**: needs the board. Set has a Pico 2/2W, not with him today; he asked to keep it
  as *his* verification step. `firmware_difftest.py --hardware` prints the runbook; `--install`
  replaces `07/firmware/` **only after claim 3 passes**.

The one to watch on the board is `09_parser`: **Lark's own parser, running on a microcontroller,
compiled by a compiler written in Lark.**

**Still to do:** F3.4 (`coloring.py` + `igraph.py` - the graph-coloring allocator behind `gen`'s
`allocator=` hook) is optional. Then **PROVE.md**.

### 2026-07-13 - **the oracle was wrong, and we fixed it. ch02/03/04 written. The freeze was a story we were telling ourselves; now there is a ledger.**

Started as "write ch04". Ended somewhere better, because Set asked two questions I did not
have good answers to.

**ch02, ch03, ch04 written** (commits `2e5570b`, `948cc04`, `76470da`), plus
`book/tools/checkrefs.py` (`1ece9df`) - cross-references are now `\ref`/`\label` and the build
refuses a typed numeral. That caught a real rot: the Introduction is a *numbered* chapter, so
every hardcoded "Chapter~N" in the prose was **off by one** and LaTeX had no complaint to make.

**Then Set asked: "any reason not to repair the bug?"** - the monomorphic-recursion finding
that ch04 is built around. The honest answer was no. So:

**C3 - the type-checker repair (`07/src/{infer,ty}.py` + `self/{infer,types}.lark`).**
`check_fn_decl` bound a function's recursive occurrence to a bare monotype var, *throwing away
the type Pass 1.5 had already computed from its signature*. A fully annotated polymorphic
function that recurses on its own result could not be typed - and because `compose` ran no
occurs check while `apply` chases var chains, the symptom was a **hang**, not a rejection
(`compose` splices `a5|->a16` and `a16|->a5` into `a5|->a5`; `apply` follows it forever).
Fix = a full signature licenses polymorphic recursion (bind the **generalised** annotated
scheme). Guard = `compose`/`subComposeRange` drops a composed `k|->k` (sound and total - it
*is* the identity map). `rev(xs, acc)` now type-checks as `List(a) -> List(a) -> List(a)`.

**THE REDUCTION - and this is the part worth remembering.** ch04's diagnosis named *three*
co-equal causes. Fix B **alone** killed the bug; the other two are untouched. So there was one
defect (the compiler was handed the answer and discarded it) and two *aggravating conditions*
(which decided that the symptom was a hang rather than a diagnosis). That distinction is
invisible from the traceback and only visible from the repair. **Repairing a bug is how you
find out what it was.** New §"The repair, and what the repair taught" in ch04 carries it.

**Validated - output-neutral with BOTH implementations changed** (the one manoeuvre the method
forbids, so the evidence has to be that neither *moved*): all seven differentials back on their
pins - `infertest` 42/0/3 - `typechecktest` 42/0/3 - `cektest` 35/0/14 - `emittest` 38/0/7 -
`lowertest` 35/0/10 - `emittactest` 32/0/13 - `opttest` 128/0/52. `typechecktest` is the witness:
every accepted program still emits byte-identical C, every rejected one still gives a
byte-identical `type error:`. **O5' ladder re-run: C1==C2==C3 byte-identical, sha
`f1dedfa9 → 8f9596d9`** (7,688 lines, 1,519,608 bytes). The sha *must* move - `infer.lark` and
`types.lark` **are** compiler source. **The invariant is the closure, not the sha.** Re-pinned in
both `BASELINES.md` (drift-checked; `check_pins` caught that my re-pin had reached one tree only -
the tooling works).

**`24_stringprims` was never failing.** `make -C 07 test` had reported `1 failed` for weeks. The
expected output is embedded in the test as a comment; someone added three `float_to_bits` prints
and never grew the comment. First 13 lines always matched. Fixed the comment → **81 passed, 0
failed**, green for the first time on this branch. (Set asked whether to delete the test - no: it
is the *only* test of the eight primitives self-hosting rests on, and dropping it would move every
pinned count.)

**Then Set's second question, which is the real find: "compare the *original* 07 with what is in
07 now."** Done, and it is worse than we said. Since self-hosting began (`a12ad34a`, the parent of
the first `self/` commit) the "frozen" oracle has taken **3,393 insertions across 13 files**.
ch01 was telling readers the freeze had been broken **three times**. New:

- **`ORACLE.md`** - the ledger. Class A (new files: `opt.py`, `emit_tac_c.py`, `coloring.py` - a
  second axis, nothing pre-existing changed). Class B (**growth**: eight primitives added *because
  the port demanded them* - Lark could not index a string when the port began. "Lark can express
  its own compiler" is true *of a Lark that grew eight primitives in order to*, and that price is
  paid in the language, not the compiler, and is almost never quoted). Class C (**corrections**:
  C1 UTF-8 byte columns, C2 the C arena, C3 today's, C4 the stale expectation).
- **`tools/oracle_drift.sh`** - regenerates the ledger **from git**, not from memory. A ledger you
  maintain by remembering is a ledger about your memory.
- **`book/chapters/appendix_oracle.tex`** (`\label{app:oracle}`) - the reader's copy of the
  argument. ch01's "broken three times" passage rewritten to be true and to `\ref` it.

The oracle is not a fixed point. It is a **tracked** point - which is the most that was ever
actually on offer, and is fine *so long as the tracking exists*. What was not fine is believing in
the freeze while quietly editing the thing that was frozen. **This is a precondition for PROVE:**
it is why refinement types get prototyped in an `08/src` fork and not in `07/src`. A guarantees
axis that also drifts the reference proves things about a moving target.

**Next:** ch05 (the evaluator). ~90 stubs left across Parts I-III.

### 2026-07-13 (later) - **the writing starts. PROVE.md fixed; ch01 written; the shipping layout settled.**

Three things, in order. The axis has turned: the code is frozen and green, and the work is now
the **book**.

**1. `PROVE.md` no longer says to thaw the oracle.** It had told a future session to prototype
`refine.py` / `solver.py` *in `07/src`*, calling that "the frozen-oracle convention every other
module follows." That inverts the convention: every module was **ported from** the oracle, never
**added to** it. Adding a file to `07/src` re-opens three pinned fixpoints (`49a4921c`,
`829410dc`, `f1dedfa9`) and every count in both `BASELINES.md`. New **§0.1**: the plan **forks**
the oracle into `08/src/`, untouched modules byte-identical and drift-checked (reuse
`self/vendor/check_drift.sh`), and **Step 0** is now *fork + establish the conservative-extension
baseline* - every program that checks through `07/` must check identically through `08/` unless
it carries a refinement. Commit `83cb982`.

**2. `book/chapters/ch01_bootstrap.tex` is written** - first chapter out of stub. Five stubs
replaced with prose. Shape: Thompson's "Trusting Trust" as the opener but explicitly *deferred*
(the trust question is the conclusion's, and the chapter says so); the **three senses of
self-hosting** (source is in the language / the compiler compiles it / **the fixpoint**), with
only the third a claim about correctness, and the honest note that a **uniformly wrong** compiler
satisfies the fixpoint anyway - which is why Chapters 2-6 exist; **the oracle** and why frozen
("an oracle that moves is not an oracle; it is a mirror"), with **all three thaws** named - the
stub said *two*, `BASELINES.md` records **three**, and the third (UTF-8 / byte columns) is the
best story in the chapter because **neither the fixpoint nor the differential could have caught
it**: all three ladder stages corrupted string literals identically, and both implementations
were wrong in the same place; **differential testing** with a real worked example (`let x = 1 in
x + 2` → the nine-line token dump, taken from the actual oracle, not invented); and **a map of
the port** as a table (ch → Lark file → what it must reproduce). The stub's word "milestone" is
gone - the reader has no plan documents.

Verified: `make -C book paths` green, `make book` builds, both `\cite` keys resolve
(`thompson1984trust`, `mckeeman1998differential` - note the book loads **no natbib**, so it is
`\cite`, not `\citep`).

**3. The shipping layout is settled, and the prose is already immune to it.** Set: the companion
ships from `github.com/Feyerabend/stack`, in a folder of its own (`ext/` or similar) holding the
book **and** the three strands side by side. This costs **zero chapter edits**, by construction:
**prose never names the directory that contains the strands** - it cites *inside* one
(`self/oracle/lexer.py`) or a command typed *from* one (`make lextest`). The one rule the book
depends on, now written into `book/PATHS.md`:

> the three strand directories keep their names - `self`, `optimize`, `prove` - and stay
> **siblings at the reader's root**.

Nesting them (`ext/code/self/`) or renaming one breaks every citation at once; putting the PDF
beside them breaks nothing. Exactly **three** constants move with the folder, and `PATHS.md` now
tables them: the output dir in `tools/mkrepo.py`, `REPO` in `book/tools/checkpaths.py`,
`\codeurl` in `main.tex`.

**Next: the book, Parts I-III.** ch01 done; ch02 (lexer) is next. 24 files, ~98 stubs left.
Writing rules that are now mechanical, not remembered: cite the **reader's** paths only
(`make -C book paths` fails the build otherwise - stub blocks are exempt), and never hand-edit
`repo/` (`make -C self drift`).

### 2026-07-13 - **the full suite, run against both trees. Zero failures; one pin was lying.**

Set: *"run the full test suite to be sure"* - ten targets in the dev tree, three strands in
`repo/`. Everything is green in the sense that matters (**0 failed**, everywhere), and the run
paid for itself twice over: it found dangling pointers in the reader's tree, and it found a pin
that had quietly stopped being a claim.

**`emittest` re-pinned 37/0/7 → 38/0/7.** 37 + 7 = 44, but the corpus is 45 files. The pin was
set before `25_torture` joined the corpus and was never updated, so it accounted for every file
but that one - and the 45th has been passing the whole time. Nothing about the compiler changed.
This is the same drift `cektest` suffered (and the same file caused it), and it is worth naming
as a class: **a pinned count that no longer adds up to the corpus has stopped being a claim about
the corpus.** The corpus grows; a pin that does not is a number, not a test. Both copies of the
row (`self/tests/BASELINES.md` and `repo/self/harness/BASELINES.md`) now say 38/0/7 - they must,
because `check_pins()` in `mkrepo.py` cross-checks them and fails the build if they disagree.

**The dangling pointers** (found only by *running* the reader's tree, which is the point of
running it): module headers in `repo/` said `make -C self X` - how you invoke a target from the
dev tree's root, not from inside a strand, where the reader is standing. `tast.lark` and
`tac.lark` told the reader to run smoke harnesses that were never shipped. `opt.lark` cited
`make optsmoke`, a target that has never existed in *either* tree. And the `optimize` strand
shipped `lex`/`parse`/`infer` - it has to, it lowers a *typed* AST - while shipping none of the
differentials their headers tell you to run. Fixed by shipping the harnesses, adding the real
targets, and rewriting the invocations in the generator; then made mechanical, so it cannot come
back: every `make X` cited in `repo/` must be a real target, and every `harness/*.py` cited must
actually ship.

Numbers, dev tree: `infertest` 42/0/3 - `cektest` 35/0/14 - `emittest` **38/0/7** -
`typechecktest` 42/0/3 - `lowertest` 35/0/10 - `emittactest` 32/0/13 - `opttest` 128/0/52 -
`optcompilertest` 140/0/40. Reader tree: `prove` 339 passed / 0 failed plus the four soundness
proofs check; `self` and `optimize` run their whole chains clean. `cektest` gained a file
(34→35 ok, one fewer skip): a skip going green is an improvement, not a regression - which is
why the **invariant is `0 failed`**, and the ok/skip split is a report about the machine, not
about the compiler.

**The contention finding - and how nearly it became a false one.** Dev `lextest`/`parsetest` came
in at 55/0/2 and 56/0/1 against a 57/0/0 pin. I put the skips down to CPU contention, then re-ran
to confirm it - and got *the same* 55/0/2, which looked like a refutation: the skips reproduced on
an idle box, so they must be real timeouts, and the pin must be stale in the way `emittest`'s was.
It was not a refutation. The box was not idle. I had regenerated `repo/` and run the drift check
**on the same machine, while that very run was inside `lextest`** - the exact interference I
believed I was ruling out. A third run, which actually waits for everything else to exit
(`while pgrep -f suite2.sh; do sleep 60; done`), reports **57 ok / 0 fail / 0 skip**. The pin holds.
There were never two skipped files to name.

Worth keeping, because it is a trap this whole method is shaped to fall into: **a timeout-skip and
a stale pin look identical in a summary line and are nothing alike underneath.** A skip is a report
about the machine and evaporates when the machine goes quiet; a stale pin is a claim about the
corpus that has stopped being true and will never evaporate on its own. Both show up as
`n ok / 0 fail / k skip` with an `n` below the pin. The suite can only tell them apart if the
machine is quiet *while you ask* - and every harness here is a Python interpreter running a Lark
interpreter, so it is slow enough that anything else you do on the box is contention. Two of my
three runs were polluted by my own concurrent work, and the second one's agreement with the first
was the most misleading evidence in the whole session: **a reproduced number is not an independent
one if you reproduced the interference along with it.** Quiesce first, then measure; and when a
re-run agrees with a run, check that it disagreed about something.

**`cektest` re-pinned 34/0/15 → 35/0/14 - and this one is the *other* case.** Set asked for it, and
the point of the paragraph above is that you cannot grant that request by looking at the number.
`emittest`'s old pin failed arithmetic: 37 + 7 = 44 against a 45-file corpus, which no amount of
hardware explains. `cektest`'s did **not**: 34 + 15 = 35 + 14 = 49 (45 corpus files + 4 `read`
cases). Its pin still covered every file. So what moved was a **skip going green** - and a skip that
went green because the box happened to be fast is exactly what you must *not* pin, or the pin starts
lying on a slower box. The way to tell is to stop reading the summary line and look at the skip
*list*: two idle runs, back to back, both **35/0/14 with a file-for-file identical skip list**, and
the two earlier contended runs said 35/0/14 as well. Four observations, two load conditions, same
files. That is what earns a pin; `lextest` never had it.

The 14 skips, now enumerated in the row rather than waved at as *"legit (timeouts/imports)"* -
because that phrase is what let the rot sit:

- **11 structural** (`oracle exit 1`): the 9-file error suite, plus `09_modules/shapes.lark` and
  `Stdlib.lark`, which are import fragments with no `main` of their own. **No machine, however
  fast, turns these green** - the oracle itself declines to produce a reference stdout.
- **3 timing**: `04_tailrec`, `15_tailrec2`, `04_queens` exceed the meta-circular eval budget.

So the skip column is **not one thing**, and the old prose in `BASELINES.md` said it was: it claimed
all 15 skips were files "this machine could not finish in 90 s", when 11 of them are structural and
would skip on any hardware ever built. Read that sentence and you would tune the budget forever
waiting for a corpus that cannot move. Two-thirds of a skip column that looks environmental is not.
(Also fixed: both `AUDIT.md` copies documented the budget as **300 s**; `cek_difftest.py` has been
defaulting `LARK_TIMEOUT` to **90** - the harness prints the real figure in every skip line, which
is how it surfaced. Documentation drifts away from a constant the moment the constant is written
down twice.)

### 2026-07-12 (later still, iii) - **the milestone vocabulary is gone from `repo/`. The readback found it hiding in the two file classes the substitution never touched.** (commit `806e26e`)

Set: *"cut the milestone jargon from the reader's tree"* - `M7.4`, `SELFHOST §7`, `OPTIMIZE §8b`,
`F2⁺`, `O5'`. Every one of them indexes a plan document (`SELFHOST.md`, `OPTIMIZE.md`, `LOG.md`)
that is **ours and is not in `repo/`**. A label pointing at a document the reader cannot open is
worse than no label: it reads like a reference and resolves to nothing.

The dev tree **keeps** its milestones (this log depends on them). `tools/mkrepo.py` strips them on
the way out - `_JARGON` (~100 rules) + `dejargon()` + a guard that **fails generation** if one
survives, so they cannot creep back. Substitutions name the part of the compiler meant: "a known
wart of the language" for §7, "the optimizing pipeline" for M7, `-O1` for the plan's increments.

**Then Set asked for a readback - and it earned its keep.** `dejargon()` was wired into `rewrite()`
(harnesses) and `rewrite_lark()` (modules) and **nowhere else**, so two whole file classes still
carried dead references:

- **The oracle.** Copied from `07/src` with only its *paths* fixed. `opt.py` cited five
  `OPTIMIZE.md` sections, `riscv_vm.py` three; and `opt.py`'s header still said
  `[populated in milestone O1] / [later milestones]` - by now not merely dead but **false**:
  every level is populated.
- **The corpus.** Copied byte-for-byte from `07/tests`. `24_stringprims` and `25_torture` head
  themselves with the milestone they unblocked.

`07/src` is **frozen and was not touched** - the rewrite happens on the copy. To keep that honest,
`rewrite_oracle()` now tokenizes before and after and **refuses to emit a file whose CODE moved**;
only comments and docstrings may differ from the reference. Verified: **10 oracle files differ in
prose, 0 in code**; all 29 compile.

**Two things that LOOK like jargon and are not.** Worth writing down, because a de-jargoning pass
is a search-and-destroy pass and its characteristic failure is destroying the wrong thing:

1. `-O0`..`-O4`, and prose like "an `O1` pass" - **real optimization levels** the reader passes on
   the command line. Only the plan's *increment* numbering (`O4 increment 2`) is dead. Guard
   excludes them.
2. `Appel §11.1` / `§11.4` in `coloring.py` / `igraph.py` - a citation to **a book the reader can
   actually open**. One of the §-catch-alls would have eaten `§11.4` and silently destroyed a real
   reference. Literature cites are now **masked before the rules run** (`_LITERATURE`). *If you add
   a rule, add its exception first.*

Also: the word **"milestone"** itself is now banned in both guards (generated *and* hand-written
KEEP files), which caught `self/Makefile`'s "This is the milestone" and `emit_c.lark`'s "alongside
this milestone", and `AUDIT.md` citing `LOG.md` at the reader.

Verified: `mkrepo --check` clean - drift green - 29 oracle modules compile - the two edited corpus
files give **byte-identical CEK output** across dev/`self`/`optimize` - reader's `lextest`
**52 ok / 0 fail / 0 skip**, on its pin.

### 2026-07-12 (later still, ii) - **the corpus was eating its own scratch. `lextest`/`parsetest` swept 104 files, not 57.**

Found by accident: a dev `lextest` died with `FileNotFoundError: self/tests/_driver.lark`. The
harness had put its **own transient driver in its own corpus**, and then unlinked it.

`corpus()` in `lex_difftest.py` and `parse_difftest.py` did `rglob("*.lark")` over `SELF` - i.e.
over *everything below* `self/`. Since `self/vendor/` landed (2026-07-11, staged-not-wired) that
meant:

| | files |
|---|---|
| `07/tests` + `07/samples` - the actual corpus | 45 |
| `self/*.lark` - the compiler's own source (right, and the point) | 12 |
| **`self/vendor/**` - a byte-faithful SECOND COPY of the same corpus** | **45** |
| **`self/tests/_*.lark` - the harnesses' own scratch drivers** | **2** |
| | **104** |

So every run since the vendor staging lexed the corpus **twice** and lexed the drivers as if they
were source. Nothing went red (the duplicates agree with themselves, and a driver is valid Lark),
which is the whole problem: **the bug was invisible precisely because it could only ever pass.**
The crash only surfaced because two runs overlapped and one deleted the other's `_driver.lark`
mid-sweep. Fix: glob `SELF` **non-recursively** and skip `_`-prefixed names, in both harnesses -
`57 files` (45 + 12), and the two corpora now provably match each other.

Two things fall out. **The dev `BASELINES.md` had no `lextest`/`parsetest` rows at all** - they had
been running unwatched, which is the exact condition that let `optcompilertest` sit on 25 silent
failures. Pinned now. And the reader's strands were never affected: their `SELF` is `lark/`, which
holds nothing but modules - the `self` strand computes 45 + 7 = **52**, which is what its pin
already said. Also added `stack/lark/.gitignore` for the scratch drivers; the reader's tree had
been ignoring them all along, and the dev tree had not.

### 2026-07-12 (later still) - **the three strands are cut apart. `repo/` is an illustration, not a codebase.**

Set settled the framing: `repo/` exists to *show* self-hosting, optimization and proof, not to be
the base anyone develops Lark from. That turns the thing I had been treating as a cost into the
design. Each strand is a complete, readable, runnable artifact; the same lexer living in two trees
is the price of a reader being able to `cd optimize && make test` without ever opening `self/`.

Checked, and it was already true *in code* - no file in any strand imports or reads from another
(`self/` 75 files, `optimize/` 85, `prove/` 46, each with its own `oracle/ lark/ harness/ tests/
samples/`). But it was **not true in prose**, and prose is what a reader follows:

- `optimize/Makefile:9` and `optimize/README.md:114` both said *"Expected numbers: `../self/harness/
  BASELINES.md`"* - the optimize strand had **no baselines of its own**. Written now:
  `optimize/harness/BASELINES.md`, pinning its four differentials (`lowertest` 35/0/10,
  `emittactest` 32/0/13, `opttest` 128/0/52, `optcompilertest` 140/0/40), the O5' self-application
  fixpoint (`f1dedfa9`, 1,512,018 bytes, **-18.4 %** against `-O0`), and the RV32I ruler.
- `prove/README.md:78` cited `self/lark/` - a path that does not exist inside `prove/`.

`mkrepo.py` grew accordingly: `KEEP` (the hand-written, repo-only files) now carries
`optimize/harness/BASELINES.md`, and `check_pins()` walks **every** strand's pin file rather than
just `self/`'s - a strand that cannot say what its own tests should print is not standing on its own.
`make -C self drift` → *196 generated files, pins agree*.

### 2026-07-12 (later) - **`repo/` stops being a second repository and becomes a generated one.**

Set's question was "we really don't want two repositories - where should PROVE work happen?"
The premise turned out to be the thing to fix.

**What was actually true.** `repo/` was a hand-made copy of the dev tree, and the copies had
drifted - *all thirteen* harnesses, not one. Worse, the drift ran the wrong way: `repo/`'s
harnesses were **better than ours**, because fixes landed in whichever copy happened to be the
one being run and never came back. Concretely, `repo/` had a `LARK_TIMEOUT` budget and
timeout→skip handling that dev lacked, and dev's `lex_difftest.py` printed a `PORT_TIMEOUT` it
never defined, with no `TimeoutExpired` handler at all - on a slow machine it would not have
skipped, it would have **crashed**. And the two `BASELINES.md` had come to disagree about
`cektest`: dev said 33 ok, `repo/` said 34, and `repo/` was right.

**Nothing here was a compiler bug. Again.** Same lesson as the morning: the apparatus rots faster
than the thing it measures, and a duplicated file is edited in one place.

**What was done.**

1. **Backported every real improvement upstream**, so dev is now the good copy: `LARK_TIMEOUT` +
   timeout→skip across all 13 harnesses. Dev is canonical; its `07/src` references are *correct
   there*.
2. **`tools/mkrepo.py`** - generates all **196 files** of `repo/`. Modules, oracle, corpus,
   samples, proof kernel copied verbatim; the **13 harnesses rewritten** (root-finding header,
   `07/src`→`oracle`, `07/tests`→`tests`, `self/tests/x.py`→`harness/x.py`,
   `self/x.lark`→`lark/x.lark`). The rewrite *fails loudly* if it leaves a dev path behind.
3. **`make -C self repo` / `make -C self drift`.** Drift = regenerate and diff. It caught the
   stale `cektest` pin on its first run.
4. **The 22 dead `07/src` signposts are gone by construction** - including inside the `.lark`
   module headers, whose smoke lines now read `python3 oracle/cek.py lark/lex.lark`. **Zero**
   dev-tree paths remain anywhere in `repo/`.
5. **The pins may not disagree.** `BASELINES.md` is hand-written in both trees (different
   audiences, different prose) - so `mkrepo --check` parses the ok/fail/skip rows and the shas out
   of both and fails if they differ. **Except `lextest`/`parsetest`**, which lex the *compiler's own
   source* and so legitimately see different corpora (12 modules in `self/`, 7 in the `self`
   strand, 9 in `optimize`). Their counts are *supposed* to differ and are excluded, with the
   reason written down.
6. **`repo/` stops assuming our machine.** New "What you need" section: which targets are heavy
   (`bootstrap-tc` ~10 GB, `fixpoint` ~6 GB), that the arena is *reserved, not used*, that on
   overflow you want **less** not more - and `ARENA_MB` exposed on `bootstrap-tc` so that advice
   is actually followable (it took `--arena-mb` but the Makefile never passed it).

**§7 finding - a decision that fell out of the survey.** The dev tree holds a great deal the book
must never ship (fuzz, optbench, RISC-V, firmware, old plans). That is not a mess to clean up
before the book: **it is what a working tree is for.** The manifest in `mkrepo.py` *selects*, so
anything not named there simply never reaches a reader. One repository, one curated view of it -
which is the thing Set actually wanted, without having to choose between them.

### 2026-07-12 - **the book repo (`repo/`) got its first full run. Nothing was wrong with the compiler; three things were wrong with the scaffolding.**

First end-to-end run of every target in all three strands (`repo/self`, `repo/optimize`,
`repo/prove`). **Final: zero failures anywhere** - ten differentials, three fixpoints, the
proofs. But getting there surfaced three defects, and *not one of them was in the compiler*.
All three were in the apparatus that is supposed to be watching the compiler.

**1. `optcompilertest` - 115 ok / 25 fail / 40 skip → 140 / 0 / 40.**
The strongest differential in the tree (all 9 modules concatenated; the whole optimizing
pipeline must reproduce the oracle's optimized C at every `-O` level). It had **no baseline
row and, in the dev tree, no `make` target at all** - the file existed and nothing ran it.
Run at last, it held 25 failures. All 25 were harness bugs, and *both had already been fixed
in sibling harnesses that this one never inherited*:

- **`opt._SITE` is a module-level `itertools.count()`.** The oracle's inline/closure passes
  stamp rewrite-site ids from it, so it climbed across corpus files; the port is a fresh
  subprocess per file and always starts at zero. From the second file on, the two sides wrote
  different site ids into otherwise identical C. This was the whole -O2/-O3 cluster (23 of the
  25) and it wore the costume of a real bug: **`08_traits -O2` passed alone and failed inside
  the sweep.** `oracle_at` now resets it, as `opt_difftest.py` already did - which also makes
  the verdict independent of how the run is grouped (alone, per-level, or full sweep).
- **`_anon_<id()>`** - `infer.py` names a wildcard param from a CPython `id()` (a memory
  address) and bakes it into the emitted C. Canonicalised on both sides, as
  `emit_c_difftest.py` already did.

**2. `make fixpoint` invoked a ladder that had never closed.**
`optimize/oracle/` was missing `emit_c_ast.py`, `cek.c`, `cek.h`, `larkrun.c` - stage 0 could
not emit, stage 1 could not link. With those restored it *still* died: **"lark: arena overflow"
at a 15 GB arena, on a 16 GB machine.** Cause: `bootstrap_opt.py` built stage 1 from
`emit_c_ast.py`, whose C runs on the **CEK interpreter** and allocates into a CEK arena. The
ladder that actually produced the pinned sha (`ladder.sh`, M7.5) went through **`emit_tac_c.py`
at `-O0`**, whose C is self-contained (own `main`, bump heap) and peaks near 6 GB. **The
documented -18.4 % result came from a hand-rolled script; the harness left behind in the tree
took the other route and was never run end to end.** A reader typing `make fixpoint` would have
hit an arena overflow and concluded the compiler could not compile itself. Both ladders now
close: **C1 == C2 == C3, sha `f1dedfa9`, 1,512,018 bytes, 49,290 C lines** - the pinned
invariant, reproduced.
(Also: raising the child stack must be **best-effort** - macOS rejects `setrlimit` against the
very hard limit it reports. A stage that would have fit in 8 MB must not fail because we tried
to give it 64.)

**3. `bootstrap-tc`'s pin had rotted: `45c1982a` → `829410dc`.**
Not a regression. `self/infer.lark` changed on 2026-07-11, *after* the pin was taken, and the
compiler's own source is an input to its self-compile - so the sha of the C it emits for itself
moves. Output-neutral (`infertest`/`typechecktest` stayed byte-identical against the unchanged
Python oracle). Nobody had re-pinned it. Re-pinned, with the rule written down: **editing any
module the self-compile assembles counts as intentionally altering emitted C - re-run the
target rather than assuming.**

**§7 finding - the shape of all three.** `optcompilertest` had a number nobody wrote down;
`bootstrap-tc` had a number written down and left to rot; `fixpoint` had a command nobody ever
typed. **They fail identically, and the last two are worse than the first, because they still
look like guarantees.** The 25_torture entry below says "the differential caught a bug in the
differential"; this session says the same thing three times, and adds: *an unrun target is not
a weaker guarantee than a failing one, it is a fictional one.* Everything in `repo/` is now
pinned in `BASELINES.md` **and** verified by running it.

**Final numbers (all pinned):** lextest 52/0/0 - parsetest 52/0/0 - infertest 42/0/3 -
cektest 35/0/14 - emittest 38/0/7 - typechecktest 42/0/3 - lowertest 35/0/10 -
emittactest 32/0/13 - opttest 128/0/52 - **optcompilertest 140/0/40** - prove 339/0 + 4 proofs -
bootstrap `49a4921c` - bootstrap-tc `829410dc` - **fixpoint `f1dedfa9`**.

**Also this session:** Makefiles for all three `repo/` strands + a top-level one (they had
none); timeout-as-skip made consistent across every harness (a timeout is a fact about the
machine, not the compiler - `lex`/`parse` were reporting it as FAIL); `BASELINES.md` split into
*invariant* (`0 failed`) vs *environment-dependent* (the ok/skip split).

**Commits** (branch `worktree-book-repo-stubs`, for Set to merge): `ddc1651` cek_difftest
import fix - `bf21ce1` Makefiles - `53b9418` timeout semantics + BASELINES split - `ef85232`
optcompilertest + missing oracle files + pins - `49a761b` the fixpoint ladder.

**NEXT:** `repo/` is a *reader's* tree, not a builder's, and it is still shaped like ours -
see the open question at the top of this log.

### 2026-07-11 - `25_torture` bisected: **the harness was wrong, not the port**. cektest 33/1/15 → **34/0/15**

**The one red** left by the previous session (`cek.lark` printing `()` where `cek.py`
printed `10`) is closed, and `cek.lark` had **no** bug. The fault was in
`cek_difftest.py`'s `inline_imports` - i.e. in the *measuring instrument*.

**What it was.** The port has no `import`, so the harness flattens a multi-module
program by inlining the module wholesale. It ignored `exposing (...)` entirely, on a
reasoning it had written down above itself: hiding a name can only *remove* bindings,
so inlining a superset "changes nothing." That is false when a hidden name
**collides**. `25_torture.lark` defines `fn length(xs : List(Int))` and imports
`Stdlib` *without* exposing `length` - but `Stdlib.lark:62` has
`export fn length(s : String) = string_length(s)`. Both `length`s landed in one flat
scope, the inlined one came last and won, and `length(xs)` became `string_length`
applied to a list → `()`.

**Minimal repro: 19 lines, one declaration toggles it** (in
`repo/self/harness/BASELINES.md`, *Closed:* section - a module exporting a
`length : String -> Int` that the importing file does not expose, plus that file's own
`length : List(Int) -> Int`; oracle `3`, port `()`; delete the module's line and the
port matches).

**The fix.** Keep inlining the module whole - its exported functions call each other
(`spaces` calls `repeat_str`), so filtering the body to the `exposing` list would
break them - but **α-rename** any module top-level name that is not exposed to this
file *and* collides with one of the file's own top-level names (`length` →
`stdlib__length`). Driven off the lexer's token stream, so comments and string
literals are untouched; case-preserving, because Lark reads a leading capital as a
constructor (my first attempt emitted `Stdlib__length`, which parsed as a constructor
and hung the tower).

**Patched:** `self/tests/cek_difftest.py` + `repo/self/harness/cek_difftest.py`
(identical code). **Deliberately NOT** `emit_c_difftest.py`: it inlines the same way
but compares *emitted C*, where the oracle spells imported decls out under their
original names - renaming there would break a green baseline to fix nothing.

**Verified.** Full sweep at the pinned default budget: **34 ok / 0 fail / 15 skip**
(was 33/1/15; the 15 skips are unchanged and all legitimate). BASELINES.md re-pinned.

**§7 finding (for the book).** This one is worth keeping: the differential caught a
bug *in the differential*. The oracle and the port disagreed, and the honest reading -
which took a bisect to reach - was that neither implementation was wrong; the harness
was feeding them **different programs**. A flattening step that "preserves semantics"
only does so up to name capture. It is the same lesson as the blind-spot argument one
level up: the instrument needs its own witness.

### 2026-07-11 - BOOK/REPO: `book/` + `repo/` wired up; **oracle thaw #3 - a String is bytes** (a real bug the fixpoint could not see)

**Goal.** Two things: (a) make `repo/`'s three strands actually *run* from inside
themselves; (b) the book+repo stubs (see `NOTE.md`).

**(a) Rewiring - done.** All 13 harnesses in `repo/*/harness/` now resolve their
own strand and reach outside it for nothing:

```python
HERE = <strand>/harness ;  ROOT = <strand>/
SELF = ROOT/"lark"       # the compiler, in Lark
SRC  = ROOT/"oracle"     # the Python reference
```

Corpus paths `07/tests` → `tests`, `07/samples` → `samples`. Per-file budget is
now `LARK_TIMEOUT` (default 120 s) and **a timeout is a reported failure, not a
traceback** - the old code let `subprocess.TimeoutExpired` escape and kill the
run mid-corpus. `repo/README.md` documents the commands.

WARNING **Do not raise `LARK_TIMEOUT` for `cek_difftest`**: 15 of its skips *are*
timeout skips by design, so a big budget makes each grind for the full budget
instead of skipping. Raise it only for `lex_difftest` (the corpus now includes
`opt.lark`, 1 770 lines).

**(b) The finding - oracle thaw #3.** Running the rewired `lex_difftest` red-flagged
3 files (`cek.lark`, `emit_c.lark`, `emit_tac_c.lark`, `types.lark`). Not a
rewiring artifact: it **reproduces in the untouched tree**. The oracle contradicted
itself -

- `cek.py string_index` returned a **codepoint** (`ord`), but
- `cek.py char_to_string` truncated to a **byte** (`chr(n & 0xFF)`), to stay in
  lock-step with `cek.c`, which is byte-oriented throughout (`strlen`,
  `(unsigned char)s[i]`).

So the two primitives stopped being inverses above U+007F: `-` (U+2014) came back
as `\x14`. **This is on the compiler path** - `parse.lark:134,143` (`strValFrom`)
rebuilds every string-literal *value* one char at a time, so the self-hosted
parser silently corrupted every non-ASCII string literal.

**Why nothing caught it.** The corpus is ASCII (byte == codepoint), and the F2
fixpoint compares three *Lark* stages that corrupt **identically** - C1==C2==C3
still held. A compiler comparing itself to itself is blind here; only the
differential against a *different* implementation could see it, and did.

**Decision (Set): make Python match C.** A Lark `String` **is a sequence of UTF-8
bytes**, and a **column is a byte offset**. The port was right; the reference was
wrong. Changes, all in the frozen oracle:

- `cek.py` - `VStr` payload is now the byte-per-char (latin-1) view of the UTF-8
  bytes. Text crosses the boundary at exactly three places: `_lit_val` (in),
  `read`/`read_all` (in), `print` (out, writes raw bytes as `puts` does).
  `string_index` / `string_length` / `string_slice` / `char_to_string` then need
  **no special cases** - they are byte ops, and mutually inverse, by construction.
- `lexer.py` - `_advance` bumps `col` by `len(ch.encode("utf-8"))`. One line.
- `cek.c` - comment only; the C was already correct.

**Verified.** `lextest` **52 ok / 0 fail / 0 skip** (was 49/3; the "46/46" baseline
was stale - it was pinned at M1 when `self/` held one module, and the corpus grows
with the compiler). Blast radius is exactly one harness: the AST carries **no**
positions, so parse/infer/emit/typecheck cannot see a column. Round-trip smoke:
`char_to_string(string_index(s,i))` over `"a - b - α"` now reproduces it exactly,
14 bytes.

Thaws are now catalogued in `repo/self/harness/BASELINES.md` (§ *Oracle thaws*).
This is the only one where **the port won the argument**.

**Regression sweep (all against the pinned baselines).**

| harness | result | vs baseline |
|---|---|---|
| `lextest` | **52 ok / 0 fail / 0 skip** | was 49/3/0 before the fix; baseline re-pinned (the "46" was stale) |
| `cektest` | 33 ok / **1 fail** / 15 skip | 1 **pre-existing** red - see below |
| `emittest` | **38 ok** / 0 fail / 7 skip | one *better* than the pinned 37 (corpus grew) |
| `infertest` | 42 ok / 0 fail / 3 skip | on baseline |
| `typechecktest` | 42 ok / 0 fail / 3 skip | on baseline |

**WARNING Pre-existing red found: `cektest` / `25_torture.lark`** (`oracle='10'`,
`port='()'` on the 2nd line). **Not ours** - verified by running the *pristine*
harness against the *pristine* oracle in the untouched tree, where it fails
identically. Cause: `25_torture.lark` was added **2026-07-09**, one day *after*
the cektest baseline was pinned, so `cek.lark` has never passed it and nobody
re-ran the evaluator differential. **Open** - bisect it to a minimal repro (see
`repo/self/harness/BASELINES.md` § *Known red*).

**A rewiring bug I made and fixed** (worth recording, it is a good trap): I gave
`run_port` its own `except subprocess.TimeoutExpired` returning exit 124. But 8 of
the 13 harnesses **already** caught `TimeoutExpired` at the call site and counted
it as a *skip* ("meta-circular eval too slow"). My inner handler masked theirs, so
4 legitimate skips silently became "port crash" FAILs - a harness reporting
failures that are really skips is worse than one that crashes. Inner handler
removed from those 8; kept only in `lex`/`parse`, which had no guard at all and
previously died mid-corpus with a traceback.

**Next.** Book chapters are stubs (`make todo` in `book/` counts them). Ch. 7 gains
this story; ch. 12 can now be finished (M7.5 closed).

### 2026-07-11 - M7.4 (O5' leg 5): `self/opt.lark`, the opt.py TAC-passes port, optimized TAC byte-identical at every -O level
**Goal.** SELFHOST M7 slice 4 (`OPTIMIZE.md §9.3`): port `07/src/opt.py`'s TAC-subset passes to
Lark and differential-test the optimized IR byte-for-byte against the oracle - at *every*
optimization level, the strongest M7 obligation (the port reproduces the oracle's optimized IR
pass for pass, sweep for sweep). Scope = the `PASSES` list only (devirt, inline [+ prune],
closure_elim, const_fold, copy_prop, algebraic_simplify, cse, dce, licm); NOT the RV32
`ASM_PASSES` (peephole/immfold/branchlayout rewrite asm text, irrelevant to a C backend).

**What landed.**
- `self/opt.lark` (~1770 lines, `module Opt`). opt.py leans on three things a pure port can't use
  directly, all threaded here:
  - **Mutation + a module-global site counter (`_SITE`).** Every pass is
    `(TAC, Int) -> (TAC, Int)`: the Int is the shared inline/closure_elim site counter (only those
    two passes mint sites; the rest thread it untouched). `optimizeProg` starts it at 0 and threads
    it across every pass AND every sweep. The inline/closure renames are a pure function of
    `(site, name)` (`_i{site}_{name}` / `.i{site}_{label}`), so no memo dict is needed.
  - **cfg.py / liveness.py helpers**, ported inline: `optBuildCfg` (an `OptBlock` type, `impl
    Copy`), `optLiveness` (Jacobi backward-dataflow fixpoint), `optDefs`/`optUses`. Only `dce`
    needs the full CFG + liveness; `copy_prop`/`cse` need only block boundaries (detected inline at
    labels / after terminators - opt.py's `_blocks`); `licm` needs dominators (`optDominators`,
    no-op on the acyclic corpus).
  - **The optimize fixpoint**: `optSweeps` runs the level's passes to a structural-fingerprint
    fixpoint, fuel = `_MAX_SWEEPS` = 8. `optPassesForLevel` returns the passes in `PASSES` order
    filtered by the level bundle (O1 scalar; O2 += devirt/inline/licm; O3 += closure_elim).
- `self/tests/opt_difftest.py` (`make -C self opttest`) + Makefile `opttest` target + `.PHONY`/help.
  For every corpus file × level -O0..-O3: the oracle re-lowers a fresh TAC (passes mutate in place),
  optimizes at that level, pretty-prints; the port serialises the SAME unoptimized lowering and runs
  lex+parse+tac+opt + `tacPretty(optimizeProg(<TAC>, level))`. Byte-identical demanded. Two
  determinism points: the harness RESETS `opt._SITE` per oracle call (both start a file+level at site
  0) and re-lowers per level.

**Verified.** `make -C self opttest` = **128 ok / 0 fail / 52 skip** - every accepted single-file
program's optimized TAC matches the oracle at all four levels. 52 skips = (3 imports + 7 reject
fixtures + 3 CEK-overflow on deep serialised TAC [24_stringprims, samples/05_expr, samples/09_parser]
- a capacity verdict; the optimizer walks far more list structure than the emitter) × 4 levels. No
regression across the suite: infertest 42/0/3 - cektest 33/0/15 - emittest 37/0/7 - typechecktest
42/0/3 - lowertest 35/0/10 - emittactest 32/0/13 - **opttest 128/0/52**. BASELINES.md pins the new
row.

**§7 findings.**
- **The live-mutable `fnmap` is load-bearing - a frozen snapshot is a real bug.** opt.py's `inline`
  and `closure_elim` build `fnmap = {f.name: f for f in tac.functions}` holding LIVE references and
  set `fn.body = new_body` in place. A function that GROWS past `INLINE_MAX` (=12) from an earlier
  inline becomes **ineligible** for call sites processed later in the same pass, and its grown body
  is what later sites splice. **Witness: 17_mutual_rec at -O2/-O3.** is_even inlines is_odd → its
  body exceeds 12 → is_odd is no longer inlined at its other site and gets pruned as unreachable. My
  first port used a frozen snapshot, inlined everything, is_odd survived - TAC diverged (this was the
  only corpus failure, 126/2/52, until fixed). **Fix: thread an updated fnmap left-to-right** via
  index walks (`optInlineWalk` / `optClosureElimWalk`, with `optNthFn` / `optReplaceFn`), rebuilding
  each function against the already-updated list - the pure restatement of opt.py's in-place mutation.
- **No `%` operator** - const_fold's 32-bit wrap uses a floor-mod built from `/` (truncates toward
  zero), `*`, `-` (`optFloorMod` / `optWrap32`). It folds int +,-,* under wrap32 + comparisons + bool
  &&/||, and NEVER `/` or `%` (matches opt.py, which leaves division to runtime). No occurs-gap this
  port - the recursive block/set helpers are already concrete-typed.
- **`fn` reserved as a binder** (redux) - every `ICall(_, fn, _)` / `IAllocClosure(_, fn, _)` binder
  renamed `fnm`; and a `match`-in-`let` needs its `end` before the `in` (two silent parse errors).

**Next.** M7.5: the F2-style fixpoint on the *optimizing* self-hosted compiler (assemble
lex+parse+lower+tac+opt+emit_tac_c into a stdin compiler with opt ON the path, check C1==C2==C3), and
flip the emittactest oracle to optimize-before-emit so that differential runs on optimized IR too.
Per `OPTIMIZE.md §9.3`. (Do not commit - the user handles commits.)

### 2026-07-10 - M7.3 (O5' leg 4): `self/emit_tac_c.lark`, the emit_tac_c.py port, C byte-identical to the oracle
**Goal.** SELFHOST M7 slice 3 (`OPTIMIZE.md §9.3`): port `07/src/emit_tac_c.py` (550 lines,
the TAC → C emitter on the OPTIMIZING backend path) to Lark, differential-tested byte-for-byte
against the oracle. `self/emit_c.lark` (M5) is the structural template; the difference is that
emit_tac_c consumes TAC (not the syntactic AST) and emits a self-contained C program (bump heap
+ inlined builtins, `intptr_t` word).

**What landed.**
- `self/emit_tac_c.lark` (~680 lines, `module EmitTacC`). CEmitter's mutable `strlits` interning
  table → a threaded `List(String)` (first-seen order = C string-array index) via
  `etcIntern`/`etcIndexOf`; read-only tables (tag→id assoc, defined-fn names, globals) ride in a
  `Ctx` record (`impl Copy for Ctx`). Ports `_mang`→`etcMang` (non-alnum byte → `_<hex>_`),
  `_cstr`→`etcCStr`/`etcOct3` (OCTAL `\NNN` escaping - distinct from emit_c's hex `ecCStr`), the
  13-arm `emit_instr`→`etcInstr`, `_binop`, `_emit_fn`, locals/proto/body assembly, `_functions`
  last-wins-by-name-first-position dedup (`dfUpsert`/`dfBuild`), tag-id gathering from IAlloc
  (sorted, `()` excluded), and `emit()`'s exact parts order in `emitTacC`. Float consts via
  `string_to_float`+`float_to_bits` (M5 idiom). The 7838-byte C `_PREAMBLE` is carried verbatim
  as one `etcPreambleRaw` string constant (byte-injected, trailing `\n` preserved).
- `self/tests/emit_tac_c_difftest.py` (~290 lines) + Makefile `emittactest`. Serialises the
  oracle's TAC into tac.lark ctors (`s_operand`/`s_const`/`s_instr`/`s_function`/`s_tac`),
  concatenates lex+parse+tac+emit_tac_c (no types/tast - the emitter never reads a typed node),
  runs `emitTacC(<TAC>)` through cek.py, byte-compares against `CEmitter(tac).emit() + "\n"`.
  The oracle lowers with **NO optimization** (opt.lark is M7.4, not yet ported), so both sides
  emit from the identical lowered TAC - isolating the emitter.

**Verified.** `make -C self emittactest` = **32 ok / 0 fail / 13 skip**. Every accepted single-file
program produced byte-identical C: 08_life 867 lines, 06_rle 647, Stdlib 584, 01_mergesort 576,
02_bst 534, plus the error-suite acceptances 04_nonexhaustive/06_matchfail (which correctly EMIT,
no exhaustiveness check). 13 skips = 3 imports (multi-module, no import mechanism) + 7 reject
fixtures (infer raises, nothing to lower) + 3 CEK-overflow on a deep serialised TAC
(24_stringprims, samples/05_expr, samples/09_parser - a capacity verdict, same class as
lowertest's overflow skip). All differentials still green: infertest 42/0/2 - cektest 33/0/15 -
emittest 37/0/7 - typechecktest 42/0/2 - lowertest 35/0/10 - **emittactest 32/0/13**.

**§7 findings.** (1) Occurs-gap redux: a polymorphic `etcRev(List(a))` accumulator-reverse tripped
the frozen infer's monomorphic self-recursion (RecursionError in ty.py `apply`, same gap that made
emit_c.lark's ecRev/ecApp String-monomorphic); fixed by pinning it to `List(String)` - the sole
code fix during the port. `etcLen(List(a)) : Int` stayed polymorphic and typechecks fine, so it is
specifically the reverse/append pattern (result-var cons'd back into the accumulator) that
diverges. (2) When M7.4's opt.lark joins the path, flip the harness `oracle()` to optimize before
emit (currently `_lower.lower(tprog)` with no opt) so both sides run identical passes. (3) The C
`_PREAMBLE` byte-injection idiom (read + escape `\`/`"` + `@@PREAMBLE@@` substitution) reproduced
emit()'s `parts[0]` exactly incl. trailing `\n`; reuse verbatim for any raw-C-blob port.

**NEXT.** M7.4 `self/opt.lark` (TAC optimization passes, vs frozen `07/src/opt.py`) → M7.5 the
F2-style fixpoint on the *optimized* self-hosted compiler (`OPTIMIZE.md §9.3`).

### 2026-07-10 - M7.2 (O5' leg 3): `self/lower.lark`, the lower.py port, TAC byte-identical to the oracle
**Goal.** SELFHOST M7 slice 2 (`OPTIMIZE.md §9.3`): port `07/src/lower.py` (695 lines,
the typed-AST → TAC lowerer) to Lark. lower.py is a mutable `Lowerer` class; the port
threads that state purely.

**What landed.**
- `self/lower.lark` (~630 lines): read-only program tables as an `LCtx` record
  (type_tags / trait_impls / global_lets / show_impls / global_arity, built once by
  `buildCtx`); the mutable lowerer state as a threaded `LSt` record (globalFns / lambdaCtr
  / lifted-closure-fns, most-recent-first); the per-Function instruction stream + fresh/label
  counter as tac.lark's `Function`. Every lowering is
  `(..., ctx : LCtx, fnc : Function, st : LSt) -> (Operand, Function, LSt)` - `fnc` and `st`
  threaded SEPARATELY so the lambda case can swap the Function while sharing st. Both `LCtx`
  and `LSt` are `impl Copy`. Full port: expr/if/match/apply/lambda lowering, closure
  conversion (free-var capture, `<fn>$lam<n>` lifting, eta-expansion of bare global fns used
  as values), pattern check/bind, dispatch-stub synthesis, `__global_init__`, and the exact
  function-ordering + counter-increment discipline lower.py+tac.py need for byte-identical output.
- `self/tests/lower_difftest.py` + `make -C self lowertest`: serializer differential - the
  oracle typechecks (infer.py) + lowers (lower.py) + `tac.pretty`; the port concatenates
  lex+parse+types+tast+tac+lower + a driver that runs
  `tacPretty(lowerProgram(<serialised TProgram>))`, comparing byte-for-byte. Isolates
  lower.lark (no infer.lark surgery). **35 ok / 0 fail / 10 skip** - every single-file corpus
  program matches, incl. 09_parser (851-line self-hosted parser lowering ITSELF); 10 skips =
  3 imports + 7 reject fixtures (infer raises).
- Makefile `lowertest` target added.

**Two real bugs found + fixed along the way (see NEXT block for the durable lessons):**
1. **Monomorphic-recursion type blowup.** In lowerExpr's TBinOp case, `Cons(lv, Cons(rv, Nil))`
   over two self-call results unifies their element types and ties the list-element type back
   through lowerExpr's own rec-var → an infinitely-growing type (non-terminating `apply`, still
   diverges at a 200k recursion limit). Root-caused by bisecting cases, then the exact construct,
   then confirming empty affine `tracked` + the divergence lives in `apply`/`compose` expansion.
   **Fixed** by routing the pair through an annotated helper
   `fn lwPair(a : Operand, b : Operand) : List(Operand)` - the annotations pin each operand to
   concrete `Operand`, so the two result-vars never unify. Runtime value identical → TAC unchanged.
2. **tac.lark `tacReprStr` (an M7.1 defect).** Python `repr(str)` uses `"`-delimiters when the
   string contains `'` and no `"`; 09_parser's `expected ')'` reprs as `"expected ')'"`. The M7.1
   port always single-quoted + escaped. **Fixed** to reproduce Python's quote-selection
   (`tacContainsChar` + an `escSingle` flag); tacsmoke still green (19 lines).

**Also:** the threaded Function param is named `fnc` (`fn` is a reserved keyword - a param named
`fn` is a ParseError; and `fn f()` zero-arg decls are unparseable, `()` being one UNIT token, so
`_BUILTINS` is a top-level `let`). tac.lark's `pretty` was renamed `tacPretty` (permanent) so the
6-module concat can also include types.lark's Mono `pretty`.

**Regression:** infertest 42/0/2 - cektest 33/0/15 - emittest 37/0/7 - typechecktest 42/0/2 -
lowertest 35/0/10 - tacsmoke green. lower.lark is off every prior path (only tacsmoke + lowertest
touch tac.lark), so the tac.lark repr fix affects nothing else.

**Next:** M7.3 `self/emit_tac_c.lark` (differential vs the M7.0 `emit_tac_c.py` oracle;
`self/emit_c.lark` is the structural template). Not committed - Set commits.

### 2026-07-10 - M7.1 (O5' leg 2): `self/tac.lark`, the tac.py IR port, pretty byte-identical to the oracle
**Goal.** SELFHOST M7 slice 1 (`OPTIMIZE.md §9.3`): port `07/src/tac.py` (231 lines
- the three-address-code IR) to Lark. Pure data + pretty-printer + the Function
counter helpers; no lowering yet (that is M7.2). The structural template is
`tast.lark` (the M3 typed-AST port): typed ADTs + a printer + Copy impls, validated
by a smoke.

**What landed (2 new files + 3 additive edits, NO existing pipeline file touched →
frozen baselines intact).**
- **`self/tac.lark`** (~300 lines). The IR vocabulary:
  - `type Tmp = | Tmp of String`; `type ConstVal` (`CInt`/`CFloat`/`CStr`/`CBool`/
    `CUnit`) modelling tac.py's raw `int|float|bool|str|None` union; `type Operand
    = OTmp | OConst` - **tac.py's value union `Val` RENAMED to `Operand`** because
    parse.lark already owns `type Val` (VInt/...), and the M7 pipeline concatenates
    lex+parse+...+tac (SELFHOST §7 naming discipline, same as types.lark's M-prefix
    and tast.lark's TApply→TApp). Constructor names `Tmp`/`Const`... don't clash
    (parse's are V-prefixed) - verified by grep over lex+parse.
  - `type Instr` = the 13 constructors (IAssign/IBinOp/IUnary/ICall/IClosureCall/
    IReturn/ILabel/IJump/ICondJump/IAlloc/IGetTag/IGetField/IAllocClosure), field
    order following the dataclasses. `dst` is a `Tmp`; other value positions are
    `Operand`. ICall dst = `Maybe(Tmp)`, IReturn val = `Maybe(Operand)` (parse's Maybe).
  - `type Function` (name, params, body, ctr) and `type TAC` (functions, global names).
  - `impl Copy` on all six (lower/opt reuse subtrees across arms - free, name-only).
  - **byte-faithful `pretty`/`showInstr`** - a direct port of tac.py `pretty` /
    `_instr_str` (incl. empty-vs-non-empty `alloc`/`closure`, `Maybe` dst/val,
    the per-function trailing "" that yields the blank line between functions +
    one final `\n`). String Consts render via `tacReprStr` = Python-`repr`-style
    single-quoting (backslash/quote/nl/tab/cr escaped; operates on code points via
    `string_index`/`char_to_string` like lex.lark's `escape`).
  - pure `tacFresh`/`tacLabel`/`tacEmit` (tac.py's mutable methods, threaded).
- **`self/tests/tac_smoke.py`** + Makefile `tacsmoke`. Unlike tastsmoke, tac.lark
  HAS a Python twin, so this is a **true differential**: the harness builds the
  *same* program in tac.py (`golden()`) AND in tac.lark's smoke main, runs the
  latter through the CEK (concat lex+parse+tac; parse supplies Maybe), and demands
  the emitted bytes == `tac.py pretty() + "\n"` (the CEK's `print` adds the newline).
  The smoke program exercises every Instr shape, both Operand cases, every ConstVal,
  empty/non-empty field+capture lists, and fresh/emit. **Green: 19 lines, byte-identical.**

**§7 findings / notes for M7.2.**
- **Float repr is the one deferred canonicalisation.** ints/floats are carried as
  SOURCE STRINGS (like parse's VInt/VFloat), so int pretty is passthrough, but
  Python `repr(float)` ≠ the raw lexeme in general (e.g. `1e10`→`10000000000.0`).
  No smoke float diverges; handle in the M7.2 lower differential if a corpus float
  hits it (same class as the M5 float_to_bits lesson).
- **`CStr` deliberately covers BOTH string literals AND constructor-tag names** -
  tac.py's `Const(str)` makes no distinction, disambiguating by context at an `==`
  tag test (lower.py/emit_tac_c.py). Preserving that ambiguity keeps the port
  faithful downstream; do NOT split it.
- **`tacEmit` appends (O(n) snoc).** Fine for the tiny smoke, but lower.lark should
  reverse-accumulate its body and reverse once, to dodge the O(n²) wall (§9.5).

**Next.** M7.2 `self/lower.lark` (695-line `lower.py` port): typed AST (`TProgram`
from tast.lark) → TAC. Differential = serialize the produced TAC via tac.lark's
`pretty` and diff byte-for-byte vs `lower.py` on the 9 samples + corpus (the M3
`infer_difftest` pattern). The eta-expansion fix (2026-07-10 O5 entry) is already
in `lower.py`, so the port carries no known closure-ABI debt.

### 2026-07-10 - M7.0 (O5' leg 1): `emit_tac_c.py`, a CEK-validated TAC→C emitter on the optimizing path
**Goal.** O5' / SELFHOST M7 (`OPTIMIZE.md §9`) closes the two gaps behavioral O5
left: put the optimizer and a C fixpoint on the *same* backend, in Lark. `emit_c`
already emits C but from the *syntactic* AST (feeding the CEK C backend, disjoint
from the optimizer). The missing piece is a **TAC→C** emitter - it consumes the
*optimized* TAC, so an optimized program can be compiled to native via a portable C
target instead of the RV32 assembler. `emit_tac_c` has no prior oracle, so M7.0
builds the Python reference first, validates it against CEK by compile-and-run, and
only then (M7.1) ports it to Lark differentially.

**What landed.**
- **`07/src/emit_tac_c.py`** (~430 lines) - TAC→C. Pipeline entry mirrors `tac_vm`
  (`parse_file → typecheck → lower`) plus `optimize(tac, OptOptions.O(level))`, so
  the full path is `parse→infer→lower→optimize→emit_tac_c→C`. CLI:
  `emit_tac_c.py FILE [-O0..-O3]` → C on stdout.
- **Self-contained C.** Output compiles with a bare `clang -O2 -fwrapv out.c` - the
  bump heap and *every* builtin are emitted inline (adapted from `runtime.c` +
  `platform_posix.c` + the VM string-prim stubs). Deliberate departure from
  `runtime.c`: the machine word is **`intptr_t` (`lkw`)**, not `uint32_t`, because a
  heap word must hold both boxed pointers AND a raw function pointer (closure record
  word 0) - a 32-bit slot truncates a 64-bit code address under ASLR. A full-width
  word also makes Int arbitrary-precision *to 64 bits*, so this backend matches the
  CEK oracle where RV32's 32-bit wrap diverges (04_tailrec, 19_intoverflow at -O0).
- **Semantics matched to CEK, confirmed by reading the reference code**, not guessed:
  Const encodings (`None/False`→0, `True`→1, Int as-is, Float as its f32 *bits*, Str
  interned), `&&`/`||` as bitwise on 0/1, `/`-`%` truncate-toward-zero (C native),
  int compares signed, IClosureCall = call through `record[0]` cast to
  `lkw(*)(lkw,lkw)` with env = the record. Compiled with `-fwrapv` so signed Int
  overflow wraps two's-complement (matches the VM).

**Two real emitter bugs found and fixed while getting to green:**
1. **Duplicate top-level names → C redefinition.** 25_torture binds `length` twice
   (imported Stdlib `fn length(s)=string_length(s)` shadowed by local
   `fn length(xs)`), so the TAC has two `Function`s named `length`. `tac_vm`
   resolves calls via `{fn.name: fn}` = **last-wins**, and CEK agrees. Fix:
   `_functions()` dedups by name keeping the last body, so calls bind exactly as the
   VMs do and the C has one definition per name.
2. **Unconstructed-constructor tag test → segfault.** In 08_traits, `describe` matches
   `Green`, but `Green` is never *constructed*, so it is absent from the
   allocation-derived tag set. My first cut fell back to `strcmp` on a str-Const RHS
   - but the LHS there is an *integer* tag (from `IGetTag`), so `lark_str_data` on a
   small int dereferenced near-null (SIGSEGV). Fix: mirror `asm._instr` exactly - a
   str-Const RHS of `==`/`!=` is *always* a constructor-tag test, `tag_ids.get(name,
   -1)`, so an unconstructed ctor maps to the impossible id -1 and its arm is
   correctly unreachable. (No corpus program matches genuine string *literals* or
   uses string `==`; the whole TAC→native pipeline treats a str-Const RHS as a tag.)

**Validation - `07/tests/emit_tac_c_difftest.py` (new).** For each corpus file × each
-O level: emit C → `clang -O2 -fwrapv` → run (empty stdin, like `diff_test.py`) →
diff stdout vs `cek.py`. **100 ok / 0 fail / 0 skip** (25 files × 4 levels). The one
expected divergence, `19_intoverflow`, xfails **only at -O1+**: there `opt`'s
constant-folder evaluates `100000*100001` with `_wrap32` (32-bit, its RV32 target)
and bakes `1410165408` into the TAC as a Const, which the emitter faithfully emits;
CEK is arbitrary-precision. At -O0 (no folding) the 64-bit runtime matches CEK. This
is the same class as `diff_test.py`'s RV32 XFAIL for the file - recorded, not a bug.

**Integrity note.** Only two *new* files were added (`emit_tac_c.py`, its difftest);
no existing pipeline file (`lower`/`opt`/`asm`/runtime) was touched, so the frozen F2⁺
baselines (`self/tests/BASELINES.md`) are unaffected. Not committed (Set commits).

**Next (M7.1):** port `emit_tac_c.py` → `self/emit_tac_c.lark`, differentially checked
against this oracle (the `self/emit_c.lark` port is the structural template). Then
M7.2-M7.5 per `OPTIMIZE.md §9`.

### 2026-07-10 - O5 (self-optimizing fixpoint): fixed the bare-fn-as-value miscompile, then ran the optimizer on the compiler itself
**Context.** O5 as literally worded ("optimizer reaches F2 byte-identical") is
*vacuous* - the optimizer lives on the TAC→RV32 backend, F2 is proven on the
disjoint C backend, so running the RV32 optimizer cannot change the C fixpoint.
Set's directive was therefore **"fix as many problems as you can"** and then
demonstrate the optimizer on the self-hosted compiler as a program. Two real
backend bugs were on the path to running the whole compiler on RV32; both fixed.

**Fix 1 - bare top-level function used as a value miscompiled (correctness).**
The M0 log entry (2026-07-07) already flagged this as a "closure-stub
calling-convention path" and worked around it by *always passing lambdas, never
bare top-level names*. Root cause, now pinned: `IClosureCall` uses the `(env,
arg)` convention (a0=env record, a1=arg), but a top-level `f(x)` compiled by
`ICall` expects its first arg in a0. `lower.py` turned `f`-as-a-value into
`IAllocClosure(dst, f, ())` pointing the record straight at `f`'s own label, so
an indirect call fed `f` the **record** instead of the argument.
- **Minimal repro** (`apply(twice, 21)`, none in the corpus - every HOF test
  passes a `fn(...)` lambda): CEK **42** (correct); TAC **IndexError crash**;
  RV32 **920** (garbage). A real cross-backend correctness bug the corpus never
  exercised.
- **Fix** (`07/src/lower.py`): record each user fn/impl-method arity
  (`_global_arity`); when a bare global fn of arity *k* is used as a value,
  **eta-expand** it - lower `f` as `fn(a0..a{k-1}) => f(a0..a{k-1})` through the
  existing (already-correct, curried) lambda-lifting path. This produces proper
  `(env,arg)` adapters ending in a static `ICall` to `f`, fixing **TAC and RV32
  uniformly with zero interpreter special-casing**. Builtins / trait stubs
  (unknown arity) keep the legacy direct wrap, so their behavior is byte-for-byte
  unchanged.
- **Verified:** `apply(twice,21)` → CEK/TAC/RV32 all **42**; a multi-arg curried
  case (`apply2(add,30,12)` + `map(inc, ...)`) → all three **51**. This retires the
  M0 "always use lambdas" workaround: bare top-level names as HOF arguments now
  work.

**Fix 2 - branch relaxation for conditional branches > ±4 KB (backend).**
RV32I B-type encodes a 13-bit signed offset (±4 KB); the 131 KB self-hosted
compiler has conditional branches far past that. `07/src/riscv_asm.py` silently
truncated the offset (`imm & 0x1FFF`). Added a convergent relaxation pass
(`_relax_branches`, ≤64 iterations): rewrite an out-of-range `b<cc> ops, FAR`
into `b<!cc> ops, .Lrlx; j FAR; .Lrlx:` (inverted condition + trampoline JAL,
±1 MB); plus defensive range asserts in `target()` for both B-type and JAL. It
only fires on branches that overflow, so the corpus is untouched.

**Regression - all frozen baselines preserved, exactly.**
- `make difftest` = **34 passed, 0 failed** (CEK/TAC/RV32 three-way).
- `make optbench --levels 0,1,2,3` and `0,4`: **all levels observably
  equivalent to -O0**; corpus totals match `BASELINES.md` to the byte -
  **-O0 asm 8106 / bin 37656 / dyn 22,553,695**, **-O4 asm 4443 / bin 22940 /
  dyn 10,828,342**. So both the eta-expansion (`lower.py`) and the relaxation
  (`riscv_asm.py`) are transparent to the existing corpus.
- `lower.py` is only imported by the TAC/RV32 backend (cfg/asm/coloring/...), **not**
  by `emit_c_ast.py` or `cek.py` → the **F2 bootstrap and self-hosting
  differentials are untouched by construction** (infertest 42/0/2, cektest
  33/0/15, emittest 37/0/7, typechecktest 42/0/2; F2 sha `49a4921c`, tc sha
  `45c1982a` all still valid - no rerun needed, path is disjoint).

**O5 static result - the optimizer shrinks the compiler's own image ~58%.**
Compiled the emit-only self-hosted compiler (lex+parse+emit_c, 1856-line driver
embedding `01_hello`) through the TAC→RV32 pipeline:
- **-O0: asm 31,576 instrs, bin 131,652 B**
- **-O4: asm 13,174 instrs, bin  56,140 B**  → **-58.3 % asm, -57.4 % bin.**
(Note: -O0 grew 80 instrs vs the pre-fix build - the self-hosted compiler *does*
pass a bare fn as a value, so the pre-fix RV32 build was miscompiling it; F2 was
safe only because it rides the C backend. Fix 1 makes the RV32 build correct.)

**O5 behavioral result - where it's verified, and the RV32 wall.**
CEK ground-truth emitted C for the driver = 15 lines, sha `a073b974d032`.
- **Whole compiler on the RV32 VM: INFEASIBLE - hit the no-GC arena wall.** Ran
  the emit-only compiler on `riscv_vm.py` at -O0 with a 64 MB heap; after ~14 min
  of Python-interpreted RV32 it died with **`RuntimeError: Heap overflow`**. Root
  cause is the §8a/§8b arena wall, not a bug: the VM's bump heap never frees, so
  compiling even `01_hello` through the full lex+parse+emit pipeline (every
  `List`/`String` op allocates, plus the O(n²) emit join) exhausts >64 MB. A
  bigger heap only defers it and multiplies the already-infeasible wall-clock.
  `o5_static.py`'s own docstring called this out up front. **So the RV32 backend
  cannot run the full self-hosted compiler to completion** - the behavioral
  fixpoint is not established there. (The *fixes* are still verified on RV32 via
  the standalone tests + full corpus below; it's only the whole-compiler RV32
  *run* that's walled.)
- **Behavioral fixpoint that IS established - TAC interpreter, O0-O3 on the real
  compiler.** `tac_vm.py` is a pure Python-object interpreter (no fixed heap), so
  it runs the full compiler. With the eta fix in place, `o5_behavior.py` runs the
  emit-only compiler under the TAC interpreter at -O0/-O1/-O2/-O3 and checks the
  emitted C is byte-identical across levels - **RESULT: all four levels emit 15
  lines, sha `a073b974d032`, == -O0 AND == the CEK oracle.** So the TAC optimizer
  provably preserves the full compiler's output, and the compiled compiler emits
  exactly what the reference interpreter does. This exercises the TAC-level passes
  (fold/dce/inline/devirt/cse/licm/closure_elim) on a program far denser than any
  corpus file. The O4 asm passes are RV32-text passes; they're separately guarded
  observably-==-O0 on all 25 corpus files (optbench). Coverage is therefore
  honest: **O1-O3 verified on the compiler itself; O4 verified on the corpus.**
  (This run also *re-confirms the eta fix on a real program*: pre-fix,
  `o5_behavior.py` crashed with the bare-fn `IndexError` - the self-hosted
  compiler does use a bare fn as a value.)

**O5 status - closed in the *behavioral* sense; "true" O5 scoped separately.** The
optimizer provably preserves the self-hosted compiler's semantics (TAC O0-O3 on the
compiler == CEK oracle; O4 ==-O0 on the corpus) and shrinks its RV32 image -58 %.
But this is *not* the compiler literally optimizing itself: the optimizer is Python
(not Lark) and lives on the RV32 backend, disjoint from the F2/C fixpoint. Set asked
what "true" O5 needs; scoped as **O5' / SELFHOST M7 - see OPTIMIZE.md §9** (port
`tac`+`lower`+TAC-`opt` to Lark + a net-new `emit_tac_c` = a self-hosted *optimizing
C-compiler*; ~1500 Lark lines, M3-scale; the one net-new piece has no Python oracle,
so M7.0 builds one first). `tac_vm` no longer needs a separate closure-ABI patch -
the eta-expansion fixes it at the source (lowering), not per-interpreter.

**Files touched this session:** `07/src/lower.py` (eta-expansion), `07/src/riscv_asm.py`
(branch relaxation); docs `LOG.md`, `OPTIMIZE.md` (§5 + new §9), `SELFHOST.md` (M7 pointer).

**Not committed** (Set commits own work). No `BASELINES.md` change - corpus baselines
byte-identical.

### 2026-07-09 - O4 increment 2 DONE: graph-coloring regalloc, asm 5199→4683 via coalescing
The register-allocation upgrade the peephole motivates. The peephole (increment 1) works
window-locally on the caller-saved **t-registers** (never live across a block boundary);
two inefficiencies survive it, both in the callee-saved **s-registers** that DO cross
boundaries: (1) an `IAssign dst = src` in two different s-regs still emits a real
`mv s_dst, s_src`; (2) linear scan can spill / occupy more distinct s-regs (bigger save
area) than a precise interference graph needs. Graph coloring + coalescing attacks both.

**The allocator** (`07/src/coloring.py`, ~260 lines): Chaitin-Briggs iterated register
coalescing (Appel §11.4) - build → simplify → conservative (Briggs) coalesce → freeze →
optimistic spill → select - run on the interference **and copy** graph that `igraph.py`
already builds (it records copy edges from every `IAssign dst=src_tmp`). K=11 (s1-s11).
Coalescing merges move-related temps that don't interfere → `mv s_dst, s_src` becomes
`mv sX, sX`, which the peephole then deletes. Drop-in: `color_allocate` returns the same
`regalloc.Allocation` dataclass; `allocate_tac_color` mirrors `allocate_tac`.

**No program rewrite on spill.** Textbook Chaitin-Briggs inserts reload temps and restarts
when a node spills. Not needed here: `asm.load`/`asm.store` already load/store any
register-less temp from/to its stack slot on every use/def (this is how linear scan spills
on this backend), so an actual spill is just "assign a slot, not a register" - the
optimistic colorer's `select` phase marks the node spilled and moves on, no restart loop.

**Gating (keeps O0..O3 byte-identical).** `regalloc_color` is a **codegen-strategy flag**
(new `opt.CODEGEN_FLAGS`, named in `LEVELS[4]`), NOT a TAC pass (`PASSES`) or asm-text
pass (`ASM_PASSES`). `asm.gen(tac, allocator=None)` now takes the allocator; it defaults
to `regalloc.allocate_tac` (linear scan). `optbench.run_worker` calls
`opt.wants_graph_coloring(opts)` and passes `coloring.allocate_tac_color` only when the
flag is in the bundle. So `diff_test`, the `asm.py` CLI, and O0..O3 are unchanged;
`--pass-flags` lists the new flag under "codegen-strategy flags".

**Guard green.** `optbench --levels 0,1,2,3,4` = **25/25 ALL observably ==-O0**. Movers,
attributed by toggling the flag at O4 (coloring OFF vs ON, both with the peephole):
corpus asm **5199→4683** (-516), bin **25964→23900** (-2064). dyn 14,036,245→14,032,752
(-3493, barely) - coalescing removes STATIC setup moves, and 04_tailrec's ~13M-instruction
hot loop dominates the dynamic count. heap_allocs/heap_bytes/stub_calls UNCHANGED
(354/3708/520 - a pure backend tier, moves no allocation or IO). Coloring-OFF reproduces
increment 1's 5199 exactly, so the -516/-2064 is attributable to the coloring alone. Tight
packing visible per file, e.g. 08_traits `area$Shape` = 16 temps into only s1-s4.

**Hardening.** (a) **Deterministic** - every worklist choice is `min(...)` (name / move
index / spill-cost), never `set.pop()`, so allocation is reproducible regardless of
`PYTHONHASHSEED` (optbench forks a subprocess per file); verified the O4 asm sha is
identical across `PYTHONHASHSEED=0/12345/999` on 08_traits/25_torture/06_lists. (b)
**`regalloc.verify` clean** on every function of all 25 corpus files (no two interfering
temps share a register); `color_allocate` also asserts this internally before returning.
(c) **Isolation by construction** - `grep` confirms `coloring` is imported only by
`optbench`; `self/` never references it, so the four self-host differentials are
unaffected. `diff_test` **34/0** (O0 path, linear scan, byte-identical), `opt_licm_test`
green. O0 stays the identity (totals 8106/37656/22553695/527/361/3760 unchanged) so
`optbench_O0.json` is NOT re-pinned. Updated `self/tests/BASELINES.md` O0→O4 table,
`OPTIMIZE.md` §5 O4 line + Tier-4 checklist + new §8g. NEXT = the Tier-4 remainder
(instruction selection - fold address arithmetic, `IMAC` mul/div; branch layout) or
`PROVE.md`.

### 2026-07-09 - O4 increment 1 DONE: RV32I peephole (the first post-gen pass), dyn -38%
Tier-4, the backend tier. The first pass that runs AFTER `asm.gen`, on the emitted
RV32I assembly text (str→str) rather than on TAC - because the redundancies it targets
are artefacts of instruction selection + linear-scan regalloc that don't exist at the
TAC level.

**What the generator leaves.** Every `asm.gen` fragment is self-contained: it reloads
its operands into the caller-saved scratch registers t0-t6, computes into a scratch,
then copies the result to the destination temp's allocated (callee-saved s-*) home. So
`IAssign s2 = s1` → `mv t0, s1; mv s2, t0`; a binop → `mv t0,l; mv t1,r; add t2,t0,t1;
mv dst,t2`; a field read → `mv t0,base; lw t1,k(t0); mv dst,t1`. The scratch round-trips
are pure overhead.

**The load-bearing invariant** (makes it sound WITHOUT whole-function register liveness):
a t-register never carries a live value across a basic-block boundary (label / branch /
call / jump / jalr / ret). The generator always writes a t-reg before reading it within
the using fragment, never reads a t-reg written by a previous fragment, and passes
args/returns through a-regs - so no t-reg is ever live into a call/branch/return. Hence
**live-out(t-regs) = ∅ at every window boundary**, and t-registers can be reasoned about
independently inside each straight-line window. a-regs and s-regs DO cross boundaries
(a0 holds a call's result), so the pass never rewrites/deletes THEIR defs - only the
transient t-registers.

**Three window-local transforms + two structural** (`07/src/opt.py`, ~230 lines):
(A) copy-prop - `mv tX, R` lets later reads of tX (register or memory base) be rewritten
to R; (B) dead-scratch elimination - a pure instr whose t-reg dst is never read again in
the window is deleted; (C) result coalescing - `<op> tX, ...` immediately followed by
`mv D, tX` (tX dead after) is retargeted to `<op> D, ...`, dropping the copy. Iterated to
a fixpoint per window. Then over the whole listing: delete `mv rX, rX`, and delete a
`j L` whose next executable line is `L:` (fall-through). A window containing any
mnemonic `asm.gen` never emits is skipped untouched (defensive - an unmodelled instr
could read/write a t-reg the analysis doesn't account for).

**Wiring.** New `ASM_PASSES` registry (post-gen asm passes, separate from the TAC
`PASSES` because they operate on a different IR) + `postgen(asm, opts)` = the asm
analogue of `optimize()`. `LEVELS[4]` = the O3 TAC-pass names PLUS `"peephole"`, so
`enabled_passes` (TAC) gives O4 the identical O3 TAC pipeline and `enabled_asm_passes`
adds the peephole - O4's improvement over O3 is attributable entirely to the peephole.
`optbench.run_worker` now calls `asm = postgen(asm, opts)` after `gen`. `--pass-flags`
lists both registries.

**Guard green.** `optbench --levels 0,1,2,3,4` = **25/25 ALL observably ==-O0** (every
file's program-output sha identical). Movers (O3→O4 corpus totals): asm 6526→**5199**,
bin 31272→**25964**, **dyn 22,551,347 → 14,036,245 (-38%)** - the biggest executed-
instruction cut of any tier, because the hot recursive loops (04_tailrec's ~21M-instr
sum_to) shed their per-iteration scratch moves. heap_allocs/heap_bytes/stub_calls
UNCHANGED from O3 (354/3708/520) - a pure backend pass, it moves no allocation or IO.
Per file e.g. 10_closures asm 86→59 / dyn 94→67; peephole alone on un-TAC-optimized asm
is 8106→6518.

**Hardening (same session).** A scratch script over all 25 files confirmed: peephole is
**idempotent** (`peephole∘peephole == peephole` on every file - the fixpoint is real),
leaves **no residual `mv r,r`**, and **skips unknown-mnemonic windows** untouched. ALL
CLEAN.

**Isolation.** Only `07/src/opt.py` + `07/tests/optbench.py` touched. `diff_test`
**34/0** (runs the O0 path - no `optimize`/`postgen` call - so CEK==TAC==RV32 stays
byte-identical), `opt_licm_test` green. O0 stays the identity (totals 8106/37656/
22553695/527/361/3760 unchanged) so `optbench_O0.json` is NOT re-pinned. The 4
self-host differentials are unaffected BY CONSTRUCTION (`opt` imported only by
`optbench`/`opt_licm_test`, grep-verified). `self/tests/BASELINES.md` gains the O0→O4
progression table as the regression contract. NEXT = **O4 increment 2** (graph-coloring
regalloc via the existing `igraph.py`, instruction selection, branch layout - the
s-register pressure / spill-reload the peephole can't reach) or **`PROVE.md`**.

### 2026-07-09 - O3 increment 2 DONE: optimize() iterated to a fixpoint, closures collapse fully
The deferred alt from increment 1. A single `optimize()` sweep peels only ONE closure
layer (`inline` exposes a returned closure as a local alloc-then-call, `closure_elim`
splices its body in - but that body may hold *further* closure calls only the next
sweep can see). Increment 2 re-runs the whole enabled pass sweep until the TAC stops
changing.

**Change (`07/src/opt.py`, ~30 lines).** (1) `optimize()` now loops the enabled passes
up to `_MAX_SWEEPS = 8`, breaking when `_fingerprint(tac)` (a tuple of every function's
`(name, tuple(body))`; Instr are frozen dataclasses ⇒ value-comparable) is unchanged
across a sweep. At -O0 `passes` is empty → early return, still the identity. (2) The
site counter for `inline` and `closure_elim` became **monotonic across sweeps**: a
shared module-level `itertools.count` via `_next_site()`, replacing each pass's
per-call `site = 0`. **This was load-bearing** - iterating meant `inline` on sweep 2
would otherwise re-mint `.i0_ret` / `_i0_x` (and `closure_elim` `.c0_...`) and COLLIDE
with the labels/temps sweep 1 already emitted into the same function. Names only need
per-function uniqueness, but the never-reset counter guarantees it across sweeps for
free (one process per file under optbench).

**Why it converges.** Every pass is a sound reducer (const_fold/copy_prop/algebraic/
cse/dce shrink or simplify, never add names) or a bounded expander (`inline` is
single-level per sweep + prune-backed; `closure_elim` deletes an alloc). The inlining
depth of a non-recursive call graph is finite, so the sweep reaches a true fixpoint
(all names included, since the counter only advances when inline/closure_elim actually
fire) well under the cap; the cap only ever leaves optimization on the table, never
breaks equivalence.

**Guard green.** `optbench --levels 0,1,2,3` = **25/25 ALL observably ==-O0**. Movers
vs increment 1 (O3 totals): heap_allocs 358→**354**, heap_bytes 3732→**3708**, asm
6736→**6526**, bin 32128→**31272**, stub_calls 524→**520**, dyn ~22.5517M→22.551347M.
Per file: **10_closures** asm 146→**86** / heap 5→**3** (a non-recursive HOF chain,
now fully collapsed), **25_torture** 1848→**1790** / heap 159→**157**. Iterating the
sweep also nudged the lower levels as cascade folding/inlining converges: **O1** asm
7821→7817, **O2** 6820→6726 (heap unchanged at both - allocation removal is O3's job).

**Ceiling reached** (flagged when increment 1 deferred this). The closures still on the
heap all escape into RECURSIVE HOFs - `map`/`foldr` in 06_lists, 16_stdlib, 11_tree -
which `inline` correctly never expands (would not terminate / leaves the self-call for
the backend's loop lowering). So those closures never become a local alloc-then-call
and `closure_elim` can't reach them. Removing them is a *different* pass
(specialization / defunctionalization / a worker-wrapper), not more iteration -
recorded, not attempted.

**Isolation.** Only `07/src/opt.py` touched. `diff_test` **34/0** (runs at -O0, no
`optimize` call), `opt_licm_test` green (uses `opt` directly), O0 totals unchanged
(8106 asm / 361 heap → still identity, `optbench_O0.json` NOT re-pinned). The 4
self-host differentials unaffected BY CONSTRUCTION (`opt` imported only by
`optbench`/`opt_licm_test`, grep-verified).

**Hardening/verification (fixpoint-specific, done same session).** A one-off script
built each corpus file's TAC and, at -O3: (1) counted sweeps to convergence -
**max = 3** across all 25 files (cap is 8, so ample headroom; the 3-sweep files are
exactly 08_traits/10_closures/25_torture, the closure-heavy multi-layer ones),
confirming no file relies on the cap; (2) checked **idempotence** - a second full
`optimize()` on the converged TAC changed nothing for all 25 (the fixpoint is real);
(3) checked **label uniqueness** - zero duplicate `ILabel` names per function after
iterating (the monotonic `_next_site()` fix does prevent cross-sweep `.i0_...`/`.c0_...`
collisions). ALL CLEAN. Script left in scratchpad (not committed); it's the
verification any future change to the iteration/counter should re-run. NEXT = **O4**
(Tier-4 backend: RV32I peephole, graph-coloring regalloc, instr-sel) or **`PROVE.md`**
(guarantees axis).

### 2026-07-09 - OPTIMIZE §8b residual CLOSED: balanced-tree `Subst`, tc peak 10.15 GB → 4.73 GB
The last arena-wall residual. Algorithm W's `Subst` was an assoc list
`List((Int, Mono))`; `substGet`/`apply` scanned it linearly and - because fresh vars
are allocated monotonically - it degraded to a chain on exactly the keys unification
looks up hardest (the ~O(n^1.9) subst-side multiplier left after §8b's `applyScheme`
env-side fix).

**Change (`self/types.lark` + `self/infer.lark`).** `Subst` is now an Int-keyed
Okasaki red-black tree: `type SColor = SRed | SBlack` + `type Subst = SLeaf | SNode
of SColor, Subst, Int, Mono, Subst`. `substGet` is O(log n); `subIns`/`balance`
rebalance on insert (`subInsert` recolours the root black); `compose` folds s2's
range under s1 then unions s1 over it (`subComposeRange`/`subUnionInto`); `removeKeys`
folds through `subInsert`. Because compose OVERRIDES on shared keys, the tree caps at
distinct-key count - the assoc list instead PREPENDED duplicates that never collapsed
and got re-scanned/re-copied on every compose (the memory blowup). `bind`/`unify`/
`freshSubst` build via `subInsert`/`SLeaf` (were `Cons`/`Nil`). Lark has no type
alias, so all 41 `List((Int, Mono))` signature sites (15 in types.lark + 26 in
infer.lark) became `Subst`, and every value-level empty-subst `Nil` → `SLeaf` /
`Cons((k,v), s)` → `subInsert(s, k, v)`. De-risked the toolchain first (5-tuple match
+ deep nested patterns + the four balance rotations) on a standalone RB probe run
through `07/src/cek.py`, then typechecked the whole concatenated `Selfhost` module
with the oracle to catch every missed subst-`Nil`.

**Output-neutral - guards byte-identical.** `apply` reads only the key→Mono mapping,
never traversal order, and compose preserves the exact override semantics the assoc
list had. `make -C self infertest` = **42 ok / 0 fail / 3 skip** and `typechecktest`
= **42 ok / 0 fail / 3 skip**, every accept byte-identical vs the (unchanged Python)
oracle, every reject oracle-identical. (Skip 2→3 is unrelated to this change:
`25_torture.lark`, added during O0, is a 3rd `import` file, and infer/typecheck
differentials skip all imports; the 42 ok are unchanged. BASELINES re-pinned
42/0/2 → 42/0/3, skips named.)

**Payoff - M5.5.4 native fixpoint re-measured.** `make -C self bootstrap-tc` still
reaches **C1==C2==C3 byte-identical** (F2⁺), at new sha `45c1982a` (18877 lines; was
`34a07692` / 18549 - the sha moved because the compiler's OWN source now carries the
RB-tree code, exactly like the §8a join re-pin; the oracle differentials staying
byte-identical is what proves output-neutrality, since they compare against the
unchanged Python `infer.py`, not the self-compile). **Stage1 peak RSS 10.15 GB →
4.73 GB** (5,079,072,768 B; 58 s wall; `/usr/bin/time -l ./stage1 < tc_compiler.lark`)
- a 2.15× / -53 % cut. Re-pinned in `self/tests/BASELINES.md` (bootstrap-tc sha,
residual-CLOSED + re-pin notes, invariant #2, the two differential counts).

**Isolation.** Only `self/types.lark` + `self/infer.lark` touched (the shared
front-end that the differentials and the bootstrap all run through); the 07/ Python
oracle is untouched. cek/emit differentials unaffected by construction (neither runs
the inferencer). NEXT = O3 increment 2 (iterate inline+closure_elim to a fixpoint to
collapse escaping-into-HOF closures - the deferred alt from O3 increment 1) OR
`PROVE.md`. The arena-wall work (§8a join + §8b env-side + this subst-side residual)
is now fully closed.

### 2026-07-09 - O3 increment 1 DONE: closure_elim, first pass to move heap_allocs
Tier-3, the allocation tier - the milestone where `heap_allocs` finally MOVES. One
new pass in `07/src/opt.py`: `closure_elim`, `-O3` wired (`LEVELS[3]` already named it).

**What it does.** Scalar-replacement of NON-ESCAPING closures. A closure
`IAllocClosure(cv, L, caps)` is a heap record `[fn_ptr, cap0, cap1, ...]`;
`IClosureCall(dst, cv, arg)` loads `cv[0]`, indirect-jumps, passes the record as `env`;
the lifted body `L(env, x)` reads captures via `IGetField(_, env, i)` = `caps[i]`. If
`cv` (and every single-assignment copy of it) is used ONLY as the *fn* of an
IClosureCall - never passed as an arg, returned, stored in another record, or
field-read - the record never escapes and its identity is unobservable. Then at each
call site we inline `L`'s body with `IGetField(_, env, i)` → `IAssign(_, caps[i])` and
DELETE the `IAllocClosure`. The record is now dead (DCE removes it): a real
`heap_allocs` decrement + the indirect jalr becomes straight-line.

**Design.** Whole-function (not block-local) so it fires ACROSS the `.i..._ret` block
seam `inline` leaves between an inlined alloc and its call; follows single-assignment
copies (root/alias map). Placed right after `inline` (which exposes local closures by
inlining the callee that returns them - e.g. `adder(n)=\x->n+x`) and before the Tier-1
cleanup (which sweeps the copies it leaves). Availability of `caps[i]` at the call
site: captures must be Const/param/single-def (SSA value ⇒ same everywhere ⇒ hoisting
the reference is sound); multi-def caps rejected. Lifted body must read `env` ONLY via
IGetField, be non-recursive, ≤ CLOSURE_INLINE_MAX=24.

**Guard green.** `optbench --levels 0,1,2,3` = 25/25 ALL observably ==-O0. Movers:
heap_allocs 360(-O2)→358(-O3), heap_bytes 3756→3732, asm 6820→6736, bin 32472→32128,
dyn 22.5518M→22.5517M, stub_calls 526→524. Fired on the 2 corpus files with a
non-escaping applied closure: **10_closures** asm 188→146 heap 6→5, **25_torture** asm
1890→1848 heap 160→159. Most corpus closures ESCAPE into HOFs (map/compose/twice) -
collapsing those needs iterating inline+closure_elim to a fixpoint (O3 increment 2,
deferred; single sweep does one level).

**Other three Tier-3 passes = analyzed-and-deferred**, still named in `LEVELS[3]` but
FILTERED OUT (not in PASSES): `unbox` is a genuine no-op - scalars (Int/Float/Bool) are
register immediates on this backend, never heap-boxed; only ADT constructors IAlloc
(verified by scanning every lowered `alloc` tag in the corpus). `fusion` needs higher
IR (the `map∘map` structure is gone by TAC). `arena_reuse` needs affinity info threaded
to TAC + a non-bump allocator.

**Isolation.** `opt` imported ONLY by `optbench` + `opt_licm_test` (grep-verified), so
the 4 self-host differentials are unaffected BY CONSTRUCTION; `diff_test` 34/0; licm
unit test green. O0 stays identity → `optbench_O0.json` NOT re-pinned.

### 2026-07-09 - O2 DONE: devirt + inline (+ prune) + licm, guard green
Tier-2. Three passes in `07/src/opt.py`, `-O2` wired via `LEVELS[2]` (which already
declared the bundle). `PASSES` order set to `devirt, inline, const_fold, copy_prop,
algebraic, cse, dce, licm` - devirt/inline lead so the Tier-1 passes clean up across
the newly-exposed call boundaries, licm trails. The O1 subset keeps its exact
relative order, so **O1 is unaffected** (corpus O1 total still 7821).
- **`devirt` - trait-dispatch devirtualization.** `lower.py` emits a dispatch STUB
  fn `m` that reads the arg's constructor tag and branches to `m$Type(x)`. opt.py
  sees only TAC, so `_extract_dispatch` RECOVERS the `tag → m$Type` map from the
  stub's own body (trace each `tag == "Con"`/`ICondJump` to its arm label, read the
  arm's `m$Type(x)` call). A call `ICall(dst, m, (a,))` where `a` was just
  `IAlloc`'d with a known tag in the same straight-line block (block-local tag
  tracking, reset on every label/terminator; IAssign-copy propagates the tag) is
  rewritten to call `m$Type` directly. **Sound**: the stub, on that tag, computes
  exactly this route and has no other effect → observably identical; the tag chain
  + stub-call vanish.
- **`inline` - small non-recursive static calls.** Substitutes params by the arg
  Vals, freshly renames the callee's temps (`_i{site}_...`, globals kept) and labels
  (`.i{site}_...`), turns each `IReturn v` into `dst = v; goto .i{site}_ret`.
  **Single-level per sweep** (only ORIGINAL-body calls expand → growth bounded by
  sites × callee size); **skips recursive callees** (leaves the self-call, and keeps
  tail-recursion as a loop for the backend); body ≤ `INLINE_MAX=12`; never `main`/
  `__global_init__`; bails if the callee defines a param name (would break subst).
  Then **`_prune_unreachable`** drops functions no longer reachable from
  `main`/`__global_init__` via `ICall.fn` + `IAllocClosure.fn_name` (closure calls
  flow through the value an `IAllocClosure` produced, so its fn_name already marks
  the target reachable). That prune is why static size FALLS: a callee inlined at
  its only site becomes dead. (08_traits bin 1828→1724; 25_torture asm 2450→1890.)
- **`licm` - loop-invariant code motion.** Faithful: dominators → back-edges
  (`n→h` with `h` dom `n`) → natural loops; hoists a pure non-allocating header
  instruction whose operands are Const/defined-outside and whose single dst is
  defined once in the loop, into the sole non-back-edge predecessor (preheader).
  **BUT the TAC CFG is ACYCLIC** - Lark has no loop form; iteration is
  inter-procedural recursion (an `ICall`, not a back-edge), and if/match/dispatch
  emit only forward branches. So licm finds no back-edges and is a **no-op on the
  corpus**. Validated instead on a synthetic loop: `07/tests/opt_licm_test.py`
  (invariant `a+b` hoisted to preheader; variant `i+inv` kept; acyclic fn = identity).
  It activates the moment a back-edge exists (a future loop construct or a
  recursion→loop transform).
- **Guard GREEN** (`python3 tests/optbench.py --levels 0,1,2`): **25/25 ok, ALL
  observably ==-O0** (every output sha identical at O1 and O2). Corpus totals:
  asm **8106(-O0) / 7821(-O1) / 6820(-O2)**, bin 37656/36512/**32472**, dyn
  22.55370M/22.55261M/**22.55180M**, heap 361/360/**360** (unchanged - Tier-3 moves
  it). Biggest movers: 25_torture asm 2544→1890 dyn 13493→12582; 16_stdlib asm
  999→683; 08_traits asm 394→358 dyn 549→490; 17_mutual_rec dyn 682→358. (Aggregate
  dyn barely moves because 04_tailrec's 21M-instr recursive loop dominates and is
  correctly NOT inlined.)
- **Four self-host differentials unaffected BY CONSTRUCTION** - `grep` confirms
  `opt` is imported only by `tests/optbench.py` and the new `tests/opt_licm_test.py`;
  nothing on the cek/emit_c/infer/typecheck path touches it. **O0 still identity** so
  `optbench_O0.json` NOT re-pinned. **`diff_test` 34/0** (CEK==TAC==RV32 at O0, no
  `optimize` call).
- **NEXT: O3** - Tier-3 allocation passes (closure elimination, unboxing, fusion,
  affine arena reuse). The FP-specific headline, and the first passes that move the
  heap-alloc number (`LEVELS[3]` already declares the bundle).

### 2026-07-09 - O1 increment 1 DONE: copy_prop + dce landed, guard green
First real O1 passes. Split O1 into two increments; this one ships the two
**clearly-sound, no-arithmetic-semantics** passes, where the actual instruction
shrink lives. Both in `07/src/opt.py`, registered in `PASSES` (`copy_prop`, `dce`);
`optimize()` at `-O1` now transforms (was identity).
- **`copy_prop` (block-local, Tmp→Tmp only).** Within a straight-line block, an
  `IAssign(dst, srcTmp)` rewrites later uses of `dst` to `srcTmp`. **Block-local
  because TAC is NOT globally SSA** - the `if`/`match` result temp (`r*`) is assigned
  once *per arm* in different blocks (`lower.py:388,393,421`), so a copy is only valid
  inside the block that set it. Restricted to Tmp→Tmp (const propagation deferred to
  increment 2, where the backend paths for Const-in-cond etc. get checked). New helper
  `_map_uses(instr,f)` rewrites every use position of an instr, leaving defs/ops/labels
  alone.
- **`dce` (global liveness, iterated to fixpoint).** Drops any PURE value-def
  (`IAssign/IBinOp/IUnary/IAlloc/IGetTag/IGetField/IAllocClosure`) whose result is
  dead. Two guards: never drop a call (`ICall`/`IClosureCall` may have IO effects), and
  **never drop an assignment to a `tac.global_names` name** - a global is written in the
  init fn but read from OTHER functions, so intra-function liveness wrongly sees it dead.
  Reuses `cfg.build_cfg` + `liveness.analyse`/`defs`/`uses`.
- **Guard GREEN** (`python3 tests/optbench.py --levels 0,1`): **all 25 files ok,
  all observably equivalent to -O0** (every output sha identical). Shrink O0→O1:
  **asm 8106→7831 (-275, -3.4 %)**, bin 37656→36556, exec 22.553 M→22.552 M,
  **heap allocs 361→360 (DCE removed a dead allocation)**. `25_torture`: asm
  2544→2454, dyn 13493→12782.
- **Four self-host differentials unaffected BY CONSTRUCTION** - `opt.py` is imported
  only by `optbench`/the RV32 CLI; the oracles (`infer.py`/`cek.py`/`emit_c_ast.py`)
  never import it. `diff_test` (cross-backend) runs at -O0 (no `optimize` call), also
  unaffected. **O0 baseline `optbench_O0.json` still valid** (optimize is still identity
  at O0) - not re-pinned.
- **Float question (Set) answered → DEFERRED.** The three backends' divergent float
  representations (cek/tac `_f32` Python-float vs riscv raw f32 bits) are value-equivalent
  (`diff_test` 34/0), not a bug; the duplicated `_f32` is *deliberately* independent
  (stronger differential). O1 doesn't fold floats, so it's a non-issue for the optimizer.
  Recorded as a scoped future amendment tied to float constant-folding in
  **OPTIMIZE.md §8d [5b-followup]**.
- **NEXT: O1 increment 2** - `const_fold` (int `+`/`-`/`*` under **`wrap32`** to match
  RV32 32-bit; **skip `/`,`%`** [div-by-zero: cek raises vs RV32 spec -1/dividend] and
  **skip all float folding**; int comparisons + bool `and`/`or`/`not` ok), `algebraic`
  (int-const-gated `x+0`/`x*1`/`x*0`/`x-0`, bool identities; skip `x-x` & float - type
  not on IBinOp), `cse` (block-local, pure non-allocating first via `CSE_ELIGIBLE`).
  Same guard: `optbench --levels 0,1` equivalence + the four differentials.

### 2026-07-09 - Pre-O1 item [5] DONE: representation-coupled spots documented in-code (ALL of §8d done)
Tightened comments at the three representation-coupled sites, each tagged
`OPTIMIZE §8d [5x]` so a future editor meets the coupling at the line they'd touch:
(a) the raw `string_to_{int,float}` stub fabricates a fake 3-word record
`[word0=tag-slot, flag@word1, payload@word2]` that only lines up because
`IGetField(idx)` reads word `(idx+1)` (skips the tag slot) - cross-referenced in
both `lower._lower_string_to_result` and `riscv_vm._rt_string_to_{int,float}_raw`;
no test isolates it (corpus checks end-to-end output, not the middle word). (b)
`_rt_float_to_bits` is the identity ONLY because floats are stored as f32 bit
patterns - a boxed/f64 repr would break it and every float op; `tac_vm` does a real
struct unpack so backends still agree by value. (c) `show_result`/`show_fresult`
discard the `Err` payload, so the parse-error strings are never compared by any test
- VERIFIED the three backends' wording currently matches (`cek.py`==`tac_vm.py`==
`riscv_vm.py`) but nothing enforces it; left a `COVERAGE GAP` comment at the
`riscv_vm` error-string site. All comment-only edits + one unused `CSE_ELIGIBLE`
frozenset; `diff_test` **34/0** (CEK==TAC==RV32 byte-identical), baselines untouched.
**§8d Pre-O1 hygiene is now COMPLETE ([1]-[5]).** NEXT axis = **O1 Tier-1 TAC passes**
(const-fold/prop, algebraic-simplify, copy-prop, DCE, CSE → append to `opt.PASSES`,
wire `-O1`, guard by `optbench --levels 0,1` + `--compare` [now output-aware] + the 4
differentials; write CSE as an allowlist per `opt.CSE_ELIGIBLE`).

### 2026-07-09 - Pre-O1 item [4] DONE: CSE immutability invariant recorded at the code site
CSE over allocating pure prims (`string_slice`, `char_to_string`, the
`__string_to_{int,float}_raw` stubs) makes two distinct-but-equal heap objects
become one shared object - sound in Lark ONLY because values are immutable (no
ref/mutable-array/in-place-update) AND equality is structural (no pointer identity).
Recorded this where whoever writes the pass will see it: a `CSE_ELIGIBLE` block +
invariant comment in `07/src/opt.py`, next to the `("cse", cse)` placeholder.
Framed as an **allowlist** (CSE only prims explicitly listed eligible) rather than a
blocklist, so the rule is self-enforcing: a future mutable/effectful/nondeterministic
prim is safe by default (absent from the list → never CSE'd, no action needed),
instead of being silently CSE'd and breaking. Purity also required - never list an
IO/clock/random prim. The pass itself is O1 and unwritten, so this is a recorded
reminder, not a live transform; `CSE_ELIGIBLE` is empty until `cse` lands. Verified
`opt.py` still imports and `optimize()` is still the identity at O0. Output-neutral -
no corpus/backend/self-host artifact touched. §8d item [4] marked DONE. NEXT (paused
for review): item [5] - the three representation-coupled spots (hardening/doc).

### 2026-07-09 - Pre-O1 item [3] DONE: `optbench --compare` now catches output changes
`--compare` used to diff only the six numeric metric columns, so a pass that changed
program output while keeping instruction counts constant would slip through clean
(only `--levels 0,1` ran the equivalence check). Closed that gap in
`07/tests/optbench.py`: the compare block now flags any `out_sha` change as
`OUTPUT ... observable-equivalence BROKEN`, flags any baseline-`ok` → now-not-`ok`
file as `REGRESS`, and prints a trailing `[warning] N output change(s), M regression(s)` (or
an all-clear line). Verified two ways: a clean self-compare against
`optbench_O0.json` reports all-clear (metric deltas zero), and a baseline with one
`out_sha` mutated + one `status` flipped correctly raises `OUTPUT`/`REGRESS`.
Output-neutral tooling change - no corpus, backend, or self-host artifact touched;
all baselines unchanged. §8d item [3] marked DONE. NEXT (paused for review): items
[4] (document the CSE immutability invariant - the pass doesn't exist yet, so this is
a recorded reminder) and [5] (the three representation-coupled spots - hardening/doc).

### 2026-07-09 - Pre-O1 item [2] DONE: deep equivalence witness (+ wording correction)
The §8d item [2] note was **wrong** as written ("gate O1 on the F2/F2⁺ bootstrap"):
the bootstrap runs on the **C backend** (`emit_c_ast.py`/`emit_c.lark`, off the
`opt`/`lower`/`tac` path), while O1 optimizes **TAC→RV32** - so the bootstrap's C
fixpoint is *invariant* under every O1 pass and would test nothing. Verified the two
backends are disjoint (emit_c imports none of opt/lower/tac/asm). The real self-host
front-ends (`self/lex.lark`, 335 L, has `fn main`+stdin) are RV32-runnable in
principle but **don't** run standalone (need their differential driver; a probe hit a
non-exhaustive match; 64 KB-VM feasibility unproven) - logged as a deferred
"even-deeper witness." **Built instead (option B):** `07/tests/25_torture.lark` - one
program wiring recursive/nested ADTs, closures, HOF map/fold/filter, trait dispatch,
Stdlib+Option, the string-decomp prims + `Ok`/`Err` lowering, int+float32 arithmetic,
and algebraic-identity expressions the O1 passes target. All three backends agree
byte-identically (`diff_test` **34/0**); it runs on the 64 KB RV32 VM in 13 ms; at
**2544 asm instrs / 160 heap allocs** it is ~half the rest of the corpus's asm and
~80 % of its heap allocs in a single file - a far sharper O0-vs-O1 guard than any
feature test. It lands in the `optbench` sweep automatically (`collect_acceptance`
picks up `NN_*.lark`), so `optbench --levels 0,1` already checks its O0-vs-O1 sha
(demonstrated: "all levels observably equivalent to -O0"). Baseline re-pinned to
**25/25 ok** (`optbench_O0.json` + BASELINES.md O0 table: 8106 asm / 37656 bin / 361
heap allocs). §8d item [2] rewritten with the correction; the bootstrap stays the
C-backend fixpoint witness it already is (relevant to O5, not O1).

### 2026-07-08 - RV32 string-prim crash FIXED (self-contained, pre-O1)
`24_stringprims.lark` was the one corpus file that crashed on RV32 (`PC misaligned:
0x00100072`). Root cause: six self-host string-decomposition prims (`string_index`,
`string_slice`, `char_to_string`, `float_to_bits`, `string_to_int`, `string_to_float`)
were absent from `lower._BUILTINS`, so each was mis-lowered as an `IClosureCall` through
an unallocated fn-pointer → `jalr` to garbage. **Fix** (backend-only; nothing on the
self-host path, so the 4 frozen differentials are untouched):
- `lower.py`: added all six to `_BUILTINS`. The four scalar ones lower to a plain
  `ICall` → runtime stub. `string_to_int`/`string_to_float` return a `Result`, which a
  dumb VM stub *can't* build (tag ids are per-program via `asm._collect_tags`), so they
  route through new `_lower_string_to_result`: a raw stub `__<name>_raw` parses and
  returns a heap `[flag,payload]` pair, then lowered TAC does `IGetField`×2 + `ICondJump`
  + `IAlloc Ok`/`IAlloc Err` - so the `Ok`/`Err` tags are numbered in lock-step with any
  user-written `Ok`/`Err`.
- `riscv_asm.py`: six new `RUNTIME_STUBS` labels (`ebreak` intercepts).
- `riscv_vm.py`: six `_rt_*` handlers + strict `_parse_int`/`_parse_float` mirrors of
  `cek.py` (byte-based; ASCII corpus ⇒ byte == codepoint). `float_to_bits` is the
  identity (a float is *already* stored as its f32 bit pattern in the backend). The two
  raw stubs build the `[flag,payload]` pair on the heap; float payload = f32 bits.
- `tac_vm.py` (the 3rd backend the differential checks): same six as native-Python
  builtins + the two raw-pair stubs (float payload = real Python float there).

Result: `diff_test.py` **33 passed / 0 failed** - CEK == TAC interpreter == RV32
byte-identical on `24_stringprims` (and all others). `optbench` now **24/24 ok** at -O0.
Baseline re-pinned (`optbench_O0.json` + BASELINES.md O0 table: 5562 asm / 27132 bin /
201 heap allocs) - the only cross-corpus delta is `bin_bytes +24` on every file (six new
4-byte `ebreak` stub-table entries in the shared preamble); program output unchanged
everywhere. Kept separate from the O1 pass work as requested.

**Root-cause guard added (pre-O1 hygiene item [1], see OPTIMIZE §8d):** `lower._expr`'s
`TVar` case used to silently `return Tmp(n)` for an unknown name - a read of an
unassigned register that became the jump-to-garbage. It now returns `Tmp(n)` **only**
for top-level `let` names (asm resolves those via the global-var table) and otherwise
**raises a named compile-time error** ("register it in lower._BUILTINS AND the RV32
backend..."). Verified: dropping a builtin from `_BUILTINS` now fails loudly at lower time
instead of `PC misaligned` at run time. **OPTIMIZE §8d records the full pre-O1 checklist**
(items [2]-[5]: corpus is a weak equivalence witness → gate O1 on the F2/F2⁺ bootstrap
too; use `optbench --levels 0,1` not `--compare` for correctness; CSE-over-allocating-
pure-prims is sound only via value immutability; three representation-coupled spots).

### 2026-07-08 - OPTIMIZE O0 DONE: the measurement ruler (§8c), baseline pinned
Built the *metric* half of O0 before writing any pass ("ruler first"), as directed.
The *correctness* half already exists (the `self/tests` differentials + `BASELINES.md`);
this session adds the measurement rig and the `-O`/per-pass plumbing, and baselines
the current un-optimized RV32I code generator. **No pass logic written** - by design.
- **`07/src/opt.py` (new)** - the optimizer plumbing. `optimize(tac, OptOptions) →
  TAC` runs the enabled passes in `PASSES` order. `PASSES` is **empty** and `LEVELS`
  declares the O1/O2/O3 bundles ahead of the passes they'll hold, so at *every* level
  `optimize` is the **identity** right now → emitted code byte-identical to the raw
  `lower→gen` pipeline (this is what makes it a ruler, not yet a transform).
  `OptOptions(level, enable, disable)` = per-pass on/off for attribution/bisection.
- **`07/src/riscv_vm.py` (+9 lines, output-neutral)** - added profiling counters
  read after `run()`: `dyn_instrs` (retired RV32I instrs), `stub_calls`,
  `heap_allocs`, `heap_bytes` (every `_heap_alloc`). Pure increments; behaviour
  unchanged (verified: `24_stringprims` crashes *identically* on the stock CLI).
  This file is **off** the self-host differential path (infer/cek/emit_c/typecheck
  never import `riscv_vm`), so those baselines can't be touched by it.
- **`07/tests/optbench.py` (new)** - the rig (OPTIMIZE §6). Per corpus file × `-O`
  level it drives `parse→typecheck→lower→optimize→gen→assemble→run` (each run in a
  **subprocess under `--timeout`**, empty stdin, so a runaway VM - e.g. 04_tailrec's
  1M-iter sum, ~34 s - never wedges the sweep) and records: static asm-instr count,
  assembled binary bytes, `dyn_instrs`, `stub_calls`, `heap_allocs`/`heap_bytes`,
  compile/run wall-clock, and the program-output sha. `--levels 0,1` cross-checks
  **observable-equivalence** (every level's output sha == `-O0`'s); `--save`/`--compare`
  pin & diff a baseline; `--pass-flags` lists the registry.
- **Baseline captured & pinned** → `07/tests/optbench_O0.json` + a new O0 section +
  invariant #4 in `self/tests/BASELINES.md`. Corpus totals at the current generator:
  **23/24 ok - 4997 asm instrs - 23980 bin bytes - 22.5 M executed instrs - 285 stub
  calls - 165 heap allocs / 1680 bytes.** `24_stringprims.lark` = **pre-existing**
  RV32 codegen crash (`PC misaligned 0x00100072`, string-prim lowering gap; same on
  stock `riscv_vm.py` - NOT a regression, reported `crash`).
- **Guard from here (both halves):** each file's `-O0` output sha in
  `optbench_O0.json` must survive at every level (asm/bin/instr/heap numbers move by
  design), AND the four differentials stay green (`infertest 42/0/2 - cektest 33/0/15
  - emittest 37/0/7 - typechecktest 42/0/2`). My edits touch only the RV32 path +
  two new files, so the four are unaffected by construction; **`infertest` re-run =
  42/0/2 confirmed green.** **07/ oracle otherwise untouched; no commit/tag.**
- **Hardening pass on the rig (same session):** (a) the observable-equivalence check
  now also flags a level that turns a clean `-O{base}` run into a **crash/timeout/fail**
  (previously it only compared `out_sha` when *both* levels were ok - an ok→crash
  regression would have slipped through); (b) a handled worker crash now exits 0 with
  a clean `{status:crash, detail}` record so the parent shows the reason (e.g.
  `crash RuntimeError: PC misaligned`) instead of raw JSON. Reporting-only - metric
  values and the saved baseline are unchanged. Verified crash-row formatting,
  equivalence happy-path, and `--compare` roundtrip.
- **NEXT: O1 Tier-1 TAC passes** - const fold/prop, algebraic simplify, copy prop,
  DCE (liveness.py exists), CSE (sound via purity) - each appended to `opt.PASSES`,
  wired to `-O1`, guarded by the rig. Observable-equivalence + differentials are the
  contract; `optbench --compare optbench_O0.json` reports each pass's payoff.

### 2026-07-08 - §8b DONE: infer wall reduced, M5.5.4 native fixpoint CLOSED
Closed the one residual left open at freeze. The §8a join fix was only the first
wall; the `infer` pass was the second - Algorithm W threaded over an assoc-list
`Subst`, applied O(n) times and never freed in the no-GC bump arena, overflowed
**>12 GB** compiling the 3534-line typechecking compiler's own source. Diagnosed
two multipliers: an **env-side** one (`applyEnv` → `applyScheme` on every scheme at
every sub-expression) and a **subst-side** one (`compose`/`apply` rebuilding the
growing subst).

**Fix (`self/types.lark`, one function, output-neutral):** `applyScheme` now
short-circuits when the scheme is *closed* - `monoVarsAllIn(body, qs)` walks the
body and returns true iff every type var is bound by the quantifier list `qs`
(allocation-free, bails on the first free var). A fully-generalised (top-level)
scheme is closed, so applying any substitution to it is provably the identity →
return `sc` unchanged, allocate nothing. The frozen `Scheme(qs, apply(removeKeys(
s,qs), body), cv)` path now runs only for the few genuinely-open *local* schemes.
This removes the env-side O(env × |s|) multiplier `applyEnv` paid at every node:
the hundreds of ~closed top-level schemes become a walk, not a rebuild.

**Verified (correctness, the hard gate):** `make -C self infertest` = **42 ok / 0
fail / 2 skip** and `make -C self typechecktest` = **42 ok / 0 fail / 2 skip**,
both byte-identical to the oracle - the change is output-neutral. All four
BASELINES counts stay green.

**Result - M5.5.4 CLOSED:** the tc self-compile went **>12 GB overflow → 10.15 GB
completing high-water**, and `self/tests/bootstrap_tc.py` reaches **C1==C2==C3
byte-identical (sha `34a07692`, 18549 lines C)** - the six-module typechecking
compiler (lex+parse+types+tast+infer+emit_c + tcGate) type-checks *its own source*
and reproduces its own emitted C across three native stages. Ran at a 14 GiB
lazily-committed arena (peak touched ~10.15 GB); made that the `bootstrap_tc.py`
default and un-blocked the `bootstrap-tc` Make target. Pinned new sha `34a07692`
in `BASELINES.md`, marked §8b DONE in `OPTIMIZE.md`.

**Residual (deferred, not a blocker):** growth is still ~O(n^1.9) - the subst-side
multiplier survives (`compose = appendSub(s1, mapApplyRange(s1, s2))` rebuilds the
whole subst each call; `apply`→`substGet` is a linear assoc-list scan; the frozen
`infer.py` hides this behind a dict). The principled next reduction is a
**balanced-tree `Subst`** (Int-keyed, O(log n) lookup, output-neutral since apply
depends only on the mapping not list order), or arena compaction / a collector in
`cek.c` (frees dead cells for every program). Both are invasive/touch-frozen-runtime
and unnecessary now the fixpoint closes at a laptop-feasible arena.

**Files:** `self/types.lark` (`applyScheme` + `monoVarsAllIn`/`monoListVarsAllIn`),
`self/tests/bootstrap_tc.py` (default arena 2048→14336 MiB, header), `self/Makefile`
(`bootstrap-tc` comment + help), `self/tests/BASELINES.md` (tc-fixpoint sha pinned),
`OPTIMIZE.md` §8b (DONE). **NEXT:** OPTIMIZE O1 (Tier-1 TAC passes) or the
tree-`Subst`/collector reduction.

### 2026-07-08 - OPTIMIZE activated: §8a emitter-join fixed; §8b infer wall found
First OPTIMIZE session. Followed OPTIMIZE.md's "measure first" and reused the
`self/tests` differentials as the correctness half of O0 (no new correctness rig
needed - they already are it).
- **Baseline (O0).** Reproduced the arena-join wall cheaply: the emit-only
  bootstrap compiler **overflows a 256 MB arena** compiling its own source (LOG'd
  as needing ~8 GB). Confirmed the mechanism in `cek.c`: every string `+` is
  `str_cat`, which bump-allocates `la+lb+1` and never frees, so the right-fold
  `ecJoinNL` (`l + "\n" + ecJoinNL(rest)`) re-copies the growing suffix at each of
  N steps ⇒ Θ(S-N) arena bytes for S bytes of output.
- **§8a FIX - balanced join (DONE, output-neutral).** Rewrote `self/emit_c.lark`
  `ecJoinNL` as a bottom-up **pairwise** join: new `ecJoinPairs` joins adjacent
  pairs with `"\n"`, and `ecJoinNL` applies it ⌈log₂N⌉ times. Associativity ⇒
  byte-identical output; allocation drops Θ(S-N) → Θ(S-log N).
  - **Measured (instrumented `cek.c` high-water):** emit-only self-compile
    **~3 GB → 177.5 MB** peak; F2 fixpoint **closes at a 512 MB arena** (full
    ladder C1==C2==C3, new sha `49a4921c`; was 8 GB reserved). C sha changed
    *intentionally* - the compiler's own source now contains the new code
    (BASELINES invariant #2, re-pinned with reason).
  - **Correctness held:** `make -C self emittest` = **37/0/7** and
    `typechecktest` = **42/0/2**, both byte-identical (incl. reject diagnostics +
    09_parser 851 lines). `infertest`/`cektest` don't concat `emit_c.lark`, so
    they're unaffected by construction (unchanged 42/0/2 - 33/0/15).
- **§8b FINDING - the join was NOT the only wall; M5.5.4 still not closed.** Wrote
  `self/tests/bootstrap_tc.py` (the native tc-fixpoint harness: 6 modules +
  `tcGate` + a `read_all` stdin main, the native analog of `typecheck_difftest`'s
  gated driver). stage0 (oracle) type-checks + emits the 3534-line tc compiler
  fine, but **stage1 overflows even a 12 GB arena** on its own source. Attributed
  it: parse+emit of that source (join fixed, no typecheck) = **353 MB**, but
  adding the `infer` gate blows past 12 GB - so **>11.6 GB is the `infer` pass**.
  Root cause: Algorithm W threaded purely over an **assoc-list `Subst`** - `apply`
  walks the O(n)-sized subst, called O(n) times, every cell bump-allocated and
  never freed ⇒ a *second* ~O(n²) arena wall. (Growth measured across inputs:
  25→261 source lines gave 5.9→130 MB, ~O(n^1.3-2).) Corrected OPTIMIZE.md §8's
  premise (join alone ⇏ native fixpoint) and re-scoped §8 into 8a (done) + 8b
  (reduce infer allocation - arena compaction in `cek.c`, or a non-quadratic
  `Subst`; guard `infertest` 42/0/2 + `typechecktest` 42/0/2 + `bootstrap_tc`).
- **Files touched:** `self/emit_c.lark` (the fix), `self/tests/bootstrap_tc.py`
  (new harness), `self/tests/BASELINES.md` (re-pin + reason), `OPTIMIZE.md` §8
  (re-scoped), this LOG. **07/ oracle untouched** (the join is a Lark-port-only
  optimization; the oracle's `"\n".join` was already O(n)). No commit/tag (Set
  does those). **NEXT: §8b.**

### 2026-07-08 - OK SELF-HOSTING FROZEN at F2⁺ (Set's call)
M5.5.3 landed (typechecktest **42/0/2**, byte-identical accepts incl. 09_parser
851 lines, oracle-identical rejects incl. the whole error suite) → self-hosting is
functionally complete. Set chose *freeze now* over attempting the native fixpoint.
Freeze executed: **SELFHOST.md** status → COMPLETE (frozen at F2⁺); new
**`self/tests/BASELINES.md`** pins the golden numbers (four differential counts +
F2 C sha `2ce6a281` + binary sha `c4c622df`) as OPTIMIZE's regression contract;
**OPTIMIZE.md §8** now leads with the O(n²) arena-join wall as the motivated first
win (fixing it, output-neutral, closes the M5.5.4 native fixpoint); this **LOG**
Current position → COMPLETE. No heavy run in this session - the freeze is
bookkeeping over the already-green M5.5.3 result. Residual M5.5.4 explicitly handed
to OPTIMIZE. Hand-off: Set tags `git tag selfhost-f2` after committing (I don't
commit/tag). **Next axis when Set resumes: activate OPTIMIZE.md (O0 reuses the
existing differentials).**

### 2026-07-08 - M5.5 / F2⁺ started: the *typechecking* self-hosted compiler
Closing the one gap: the F2 bootstrap compiler was `lex→parse→emit` only (emitter
drives off the syntactic AST), so it did not type-check. Putting `infer.lark` on
the compiler path so it rejects ill-typed programs. See SELFHOST.md M5.5.
- OK **M5.5.1 - Concat probe.** Assembled the six-module concat
  `lex+parse+types+tast+infer+emit_c` (3491 lines, 134 KB) + a trivial main and ran
  it through the oracle (`07/src/cek.py`) → prints `ok`. **No name collisions**
  between the infer-set and `emit_c` (their pairing had never been concatenated -
  the one real integration unknown). So M5.5.2 is pure wiring.
- OK **M5.5.2 - Typecheck gate works end-to-end.** Driver = six modules + a
  `tcGate(prog) : Result(Bool, String)` (a Result-returning re-expression of
  `checkProgram`'s `pass1→pass15→pass2`, `P2Err→Err` / `P2Ok→Ok`) + a main that
  parses once, gates, and prints. Smoke through `cek.py`: **accept** (`02_arithmetic`)
  → emits **byte-identical C** vs `emit_c_ast.py` (67 lines); **reject**
  (`errors/09_lambda_mono`) → prints **exactly** `type error: cannot unify Bool with
  Int` (the oracle message). `Prog : Copy` lets the same parsed tree be gated *and*
  emitted.
  - **§7 finding (affine idiom shapes the driver).** First cut used `print(io, ...)`
    in *both* match arms → `infer.AffineError: affine variable 'io' used more than
    once`: the affine checker **sums** a variable's uses across match arms, so `io`
    counted twice. Fix = the M0 IO idiom: build the output String purely in the
    `match`, `print(io, out)` exactly once. The affine-across-arms wart now dictates
    compiler-driver structure, not just the toy printers.
- OK **M5.5.3 - corpus differential DONE = 42 ok / 0 failed / 2 skipped.** New
  `self/tests/typecheck_difftest.py` (`make -C self typechecktest`) drives the gated
  compiler over the corpus: accept→oracle-identical C, reject→oracle-identical
  `type error:`. Reuses `infer_difftest.oracle`/`_canon_reject` (verdict+message) and
  `emit_c_difftest.run_oracle`/`canon` (accepted C + `_anon` canon); own temp driver
  `_tcdriver.lark`; imports skipped. Every accept emits byte-identical C (incl.
  09_parser 851 lines, 08_life 519); the 5 ill-typed error-suite files reject with
  oracle-identical messages (04_nonexhaustive/06_matchfail correctly EMIT - no
  exhaustiveness check); 2 skips = the 2 import files. **Strictly stronger than
  emittest (37/7): the 7 error-suite skips became live tests.** THE SELF-HOSTED
  COMPILER TYPE-CHECKS - self-hosting is functionally COMPLETE at F2⁺.
- **Next after M5.5.3 green:** M5.5.4 native-fixpoint attempt on the typechecking
  compiler (may hit the O(n²) arena wall → OPTIMIZE), then FREEZE self-hosting
  (git-tag `selfhost-f2` + golden-C sha; SELFHOST §5b) and activate OPTIMIZE.md.

### 2026-07-08 - F2 FIXPOINT CLOSED: true self-hosting (the compiler reproduces itself)
- **The bootstrap compiler.** Assembled `compiler.lark` (~1844 lines) = `module
  Selfhost` + the bodies of `self/lex.lark` + `self/parse.lark` + `self/emit_c.lark`
  (each split at its `main` marker, module/import lines stripped - the same
  concatenation the M5 emit differential uses) + a `read_all`/stdin `main`:
  `match read_all(io) with | (io2, src) => print(io2, emitProgram("compiler",
  parseProgram(tokenize(src, string_length(src), P(0,1,1)))))`. `infer.lark` is
  **not** on this path (the emitter drives off the syntactic `Prog`).
- **The ladder.** `stage0` = the Python oracle `emit_c_ast.py` compiles
  `compiler.lark` → `c0.c`, linked against `cek.c`+`larkrun.c` → the `stage1`
  binary. Then `stage1 < compiler.lark → C1 → stage2`, `stage2 → C2 → stage3`,
  `stage3 → C3`. **Result: C1 == C2 == C3 byte-identical (sha `2ce6a281`)** - the
  fixpoint. (C0 differs from C1 only in 2 cosmetic lines - header basename +
  trailing newline; all 9558 code lines identical.)
- **Why the C-source fixpoint is the milestone, not the binary.** The emitter is
  deterministic and reads only the syntactic AST, so C1==C2==C3 is build-env
  independent - portable, strong. Native binaries are Mach-O-nondeterministic on
  macOS: per-link random `LC_UUID`, plus embedded input/output **paths** baked in.
  With `-Wl,-no_uuid` + holding the input path (`prog.c`) and output path
  identical across links, `stage2 == stage3` DID go byte-identical (sha
  `c4c622df`) - but that equality is a property of the toolchain's build
  determinism, not of the self-host compiler, so it is not the asserted fixpoint.
- **Two edits to the frozen oracle** (kept in strict C/Python parity, mirrored in
  the `.lark` ports; regression-checked, no corpus change):
  1. **`read_all : IO -> (IO, String)`** - whole-stdin read, so a compiled
     compiler can read its own source. Added to `07/src/cek.py` (`sys.stdin.read()`),
     `07/src/cek.c` (growing `fread` buffer, verbatim, arena-copied), `07/src/infer.py`
     (scheme), and both ports `self/cek.lark` + `self/infer.lark`.
  2. **C CEK arena static→`malloc`** in `07/src/cek.c` - replaced the fixed
     `static char _arena_buf[LARK_ARENA_SIZE]` with a `malloc(LARK_ARENA_SIZE)` in
     `cek_run`, so `-DLARK_ARENA_SIZE` can be raised to multi-GB. Default 512 KB
     behaviour unchanged (no corpus impact). The emitter's final `ecJoinNL` is
     O(n²) in the no-GC bump arena → compiling the ~250 KB of output needs ~8 GB
     reserved / ~3 GB peak. **Performance wart, not correctness** - OPTIMIZE.md.
  - Also needed big compile-time limits for the 1844-line concat:
    `-DLARK_KONT_MAX=1048576 -DLARK_TOP_MAX=8192 -DLARK_CON_MAX=4096
    -DLARK_DISPATCH_MAX=2048` (266 constructors, deep emitter recursion; runs fine
    unbounded under `cek.py`).
- **Packaged repeatably.** `self/tests/bootstrap.py` (`make -C self bootstrap`)
  assembles the compiler from the three live modules (so it tracks their changes),
  runs the ladder, and asserts C1==C2==C3 (`--stages 2` for the cheaper C1==C2,
  `--keep DIR` to retain artifacts). Verified the assembler reproduces the proven
  1844-line `compiler.lark` **byte-identical** (body identical, stdin main matches).
- **WARNING Harness discipline reconfirmed:** the fuzz/infer/emit/cek differentials share
  fixed temp-driver filenames (`_idriver.lark` etc.) - run only ONE at a time. Hit
  a real collision this session (two `infertest` runs clobbering `_idriver.lark`);
  killed both and re-ran serialized.
- **Next:** F2 is the committed endpoint of self-hosting. Queued big-ticket is
  `PROVE.md` (refinement/dependent types → prove programs). F3 (Pico self-hosting)
  stays a stretch.

### 2026-07-08 - HARDENING PASS (1): fuzz/property harness + skip/canon audit
- **New property differential** attacking the corpus-coverage blind spot (the 5
  differentials only prove `port == oracle` on constructs the ~44 fixed files
  exercise). Two files under `self/tests/`:
  - **`fuzz_gen.py`** - a deterministic (seeded) generator of random **well-typed**
    Lark programs by *type-directed synthesis* over the four Copy scalars
    {Int, Float, Bool, String}: every term is built for a target type, so each
    program type-checks by construction and reaches the emit stage. Covers every
    binary op (`+ - * /`, six comparisons, `and`/`or`), unary `not`/`-`,
    `if/then/else`, `let ... in`, `match` on Int with literal + wildcard/var arms,
    top-level `fn`(1-3 params)/`let`, mutual reference, calls, and all scalar
    built-ins - recombined/nested in shapes the corpus never wrote. (Out of scope,
    left for a later extension: ADTs/constructor patterns, traits, tuples, lists,
    Result, import, intentionally-rejected programs.)
  - **`fuzz_difftest.py`** - pushes each generated program through
    **lex → parse → infer → emit**, demanding `port == oracle` at every stage. It
    *reuses* the four sibling harnesses' own driver assembly / port runners /
    oracles, so a fuzz program travels the exact same port pipeline the corpus
    differentials use; only the input distribution is new. `make -C self fuzz`
    (full pipeline, small batch) / `fuzzfast` (front-end only, large batch).
- **Findings (this is why we fuzz):**
  - **A [REAL PORT DEFECT - FIXED]:** `float_to_bits : Float -> Int` was in the
    oracle's env (`infer.py`, added in the M0 runtime lock-step) but **missing from
    `self/infer.lark`** (had the other three float conversions) - so the port
    *rejected* any program calling `float_to_bits` while the oracle accepted it.
    The evaluator port **`self/cek.lark`** had the same gap (present in `cek.py`,
    absent from `cek.lark`): the M0 lock-step reached the Python/C runtimes but
    never the `.lark` ports. **Fixed both** (`infer.lark` builtin env + `cek.lark`
    dispatch arm & registration). Verified: `float_to_bits(2.5)` now type-checks in
    infer.lark and evaluates to `1075838976` in cek.lark, byte-identical to the
    oracle. (emit_c.lark already used the prim internally, so emit was unaffected.)
  - **B [BENIGN → canonicalised]:** parsed-AST float representation differs - port
    keeps the raw lexeme text (`VFloat of String`), oracle stores `float(text)`, so
    `33.90` renders differently from `33.9`. Proven benign: infer ignores the value,
    emit routes floats through the IEEE-754 **float32 bit pattern** (byte-identical),
    eval compares by value - verified `emit=ok` on trailing-zero-float programs.
    Canonicalised in the fuzz parse comparison only.
  - **C [ORACLE ROBUSTNESS - catalogued]:** `ty.apply` is not stack-safe - a long
    variable-substitution chain (`v1↦v2↦...↦Int`) overflows CPython recursion before
    a verdict, so such programs are *skipped* (no oracle answer to compare). Same
    family as the known occurs-check gap. Left byte-faithful to the frozen oracle.
- **Audit deliverable - `self/tests/AUDIT.md`:** every skip category across all 5
  differentials confirmed *out-of-port-control* (structural import / oracle gave no
  verdict / meta-circular perf - argued slow-not-wedged: the tower is cubic-not-
  divergent, and the fuzzer runs the same port assembly on tiny inputs that finish);
  every canonicalisation (infer greek-var renaming, emit `_anon_id()`, emit import
  double-emit, fuzz float rendering) shown to erase only value-equivalent
  differences; and the oracle bugs the port deliberately mirrors catalogued.
- **Results:** `fuzzfast` = **80/80 ok** over 40 programs (lex+parse). Full
  four-stage `fuzz` (seeds 2000-2011) = all `lex/parse/infer/emit = ok` (after the
  float_to_bits fix). WARNING Harness note: the reused sibling `run_port` helpers write
  **fixed** temp-driver names, so **do not run two fuzz/infer/emit/cek harnesses
  concurrently** - they clobber each other mid-write (I hit one spurious cross-seed
  "FAIL" doing exactly that; re-run alone = green). Our own object temp file is now
  PID-unique. **NEXT: hardening (2) is essentially folded in here; remaining before
  F2 = optionally extend the generator (ADTs/traits/reject path), then the F2
  two-stage binary bootstrap.**

### 2026-07-08 - M5 text differential COMPLETE: `emit_c.lark` (the C emitter, in Lark)
- **Ported `07/src/emit_c_ast.py` → `self/emit_c.lark`** (~445 lines) - the
  typed-AST → C-source emitter that feeds the `cek.c` runtime. Emits **from the
  syntactic `Prog`** (`parse.lark`), not the typed AST: verified the emitter reads
  only structure / names / literal values (never a node's inferred type) and the
  typed AST is a 1:1 structural copy - so this path skips `infer.lark` entirely.
- **State model:** one record `type Emit = | Emit of Int,Int,Int,Int,List(String)`
  = the four C-node counters (`_e` expr / `_p` pat / `_d` decl / `_a` arr) + the
  emitted lines newest-first, threaded purely (every emit fn returns `(result, Emit)`).
  Node names are allocated at function **entry** (pre-order) and lines emitted
  **after** children (post-order) - matches the oracle's counter/line interleave.
  Both multi-param desugar shapes reproduced: `ecWrap` (fn-decl / impl-method =
  nested single-param lambdas, each numbered before its body) and `ecLamInner`
  (source lambda = `reversed(params[1:])`, body numbered before the wrappers).
- **`impl Copy for Emit = {}`** - the affine checker sums a var's uses across match
  arms (SELFHOST §7), and `Emit` is matched-and-rebuilt in every arm of every emit
  fn; Copy is name-only in infer so this is free (mirrors `parse.lark`'s AST types).
- **Differential:** `self/tests/emit_c_difftest.py` (`make -C self emittest`)
  concatenates lex+parse+emit_c into one module (same assembly as `cek_difftest`;
  the `import` path skips infer Pass 1.5), embeds each corpus file as a String
  literal, runs the port through `cek.py`, and compares the emitted C line-for-line
  vs `emit_c_ast.py`: **37 ok / 0 fail / 7 skipped** over 44 files. Byte-identical
  on every self-containable file - incl. `09_parser.lark` (851 C lines, the
  self-hosted parser emitted to C), `08_life` (519), `05_expr` (341), `06_rle`
  (321). The 7 remaining skips are exactly the error-suite files the oracle rejects.
- **Import inlining (both multi-module programs now pass).** The port has no
  `import`; the harness flattens a multi-module program to one decl stream matching
  what the oracle's emitter core sees. Subtlety uncovered: `emit_c_ast.emit()`
  builds `all_decls = _load_imports(prog) + tprog.decls`, but `typecheck` **already
  inlines** imported decls into `tprog.decls` (infer.py:789) - so the oracle emits
  every imported module's decls **twice** (a real bug; see §7). The flattener
  reproduces that stream (deduped imported bodies, concatenated **twice**, then the
  main body) so `09_modules/main` (152 lines) and `16_stdlib` (634) match exactly.
- **End-to-end build+run proof (not just text).** Took emit_c.lark's emitted C for
  several programs, compiled it with the real runtime (`cc cek.c larkrun.c
  port_prog.c -o bin -lm`), ran the binary, and diffed stdout vs `cek.py`:
  `05_adt`, `13_floatops` (LIT_FLOAT bit inits), `16_stdlib` (import - the doubled
  decls compile & run fine, later dup just shadows), and `02_bst` (recursive tree)
  all **compile clean and produce identical output**. So the self-hosted emitter
  yields valid, working native executables across the feature space - the text
  differential's byte-identity is backed by real object-code behaviour.
- **Agreed next (2026-07-08): a HARDENING pass before F2.** (1) fuzz/property
  harness (random well-formed Lark programs, assert `port == oracle` end-to-end -
  targets the corpus-coverage blind spot); (2) audit the skips (timeouts truly
  slow, not wedged) and the canonicalisations (`_anon`→`_`, greek error vars - do
  they mask any real diff?), and catalogue the known oracle bugs the port mirrors.
  Then F2 (two-stage binary bootstrap).
- **Finding - no `%` operator:** `%` is not a Lark lexer token (`LexError`). The
  oracle's `_c_hex` mod arithmetic is done as `n - (n / 16) * 16`.
- **Finding - float32 bit pattern needed a prim:** float literal inits emit
  `LIT_FLOAT` from the IEEE-754 float32 **bits**, which Lark had no way to compute.
  Added `float_to_bits : Float -> Int` in **M0 lock-step** - `cek.py` (`struct`
  unpack), `cek.c` (`(int32_t)` reinterpret), `infer.py` (`Scheme((), TFn(T_FLOAT,
  T_INT))`); `24_stringprims.lark` got parity cases, `make cektest` = **31/31**
  (C↔Python identical). Non-negative literals ⇒ bit 31 clear ⇒ signed C == unsigned
  Python, so the two agree without extra masking.
- **Finding - oracle nondeterminism (canonicalised):** `infer.py` renames a
  wildcard param `_` → `_anon_{id(node)}` (a CPython object id) and the emitter
  bakes that address into the C as the closure's (never-referenced) param name.
  No port can reproduce a specific `id()`; the port keeps the deterministic `_`.
  The harness canonicalises `_anon_\d+` → `_` on **both** sides - the token never
  appears in the corpus, so it can't mask a real name, and the wildcard name is
  semantically irrelevant (never looked up).
- **07/ oracle stays the reference;** only the new `float_to_bits` prim touched it,
  in lock-step across all three runtimes + a parity test.
- **Next:** the **F2 two-stage bootstrap** (emit the toolchain itself to C, build
  stage-1 & stage-2 binaries, byte-diff them) and import inlining on the emit path
  (the 2 remaining skips). Remaining cost is interpretive-tower perf, not features.

### 2026-07-08 - M3 COMPLETE: `infer.lark` (the type checker, in Lark) + corpus differential
- **Ported `07/src/infer.py` → `self/infer.lark`** (~1213 lines) - Algorithm W
  (Hindley-Milner) + affine (linear) use-tracking + trait-bound (`Show`)
  resolution, the whole front-end's hardest slice ("the mountain"). Everything
  is threaded **purely** (no mutation, no exceptions): `fresh`=Int; the affine
  `tracked` map=`List((String,Int))`; `env`=`List((String,Scheme))`; `Subst`=
  assoc `List((Int,Mono))`; every fallible step returns an explicit result ADT
  (`IResult`/`PatR`/`FnDeclR`/`Pass2R`/... , each with an `impl Copy`). Passes
  mirror infer.py exactly: Pass 1 (types/traits/Copy/Show registration) → Pass
  1.5 (pre-register annotated fn/let sigs for mutual recursion) → Pass 2 (check
  values + impl methods). Reuses `types.lark` (unify/apply/generalise/pretty)
  and `tast.lark` (typed AST); assembled by **concatenation** lex+parse+types+
  tast+infer under one module (not `import` - the import path skips Pass 1.5,
  SELFHOST §7). Entry point `checkProgram(prog) : String` prints the normalised
  top-level signature block, or `"type error: <msg>"` on reject.
- **Lark constraints re-hit & worked around** while writing it: reserved words
  (`fn`/`module`/...) can't be binders (renamed `fn`→`fnx`, `module`→`modName`);
  identifiers can't start with `_` (bare `_` for unused); no nullary fns (`()`
  is one UNIT token - `initialEnv(dummy:Int)`); `let` binds one name (destructure
  tuples via `match`); list-*building* generics hang the occurs check, so those
  helpers are monomorphic. Type-var normalisation uses a dedicated first-occurrence
  printer (`collectVars`/`pnInner`/`pnP`), never `apply()` (which would loop).
- **Differential harness `self/tests/infer_difftest.py`** (`make -C self infertest`):
  runs `infer.py`'s `typecheck` **in-process** as oracle, serialises its TProgram
  to the *same* normalised block `checkProgram` prints (greek table byte-identical
  to `types.lark`), and runs the port via the concatenated driver over the corpus.
  ACCEPT files compared line-for-line; REJECT files compared on the `type error:`
  message with greek type-vars canonicalised (the two Fresh counters number vars
  differently, but the error kind + concrete types must agree).
- **Result: 42 ok / 0 fail / 2 skipped.** Every single-file test matches infer.py:
  all 24 feature tests, `Stdlib.lark` (27 sigs), all 9 samples - including
  `07/samples/09_parser.lark` (**the self-hosted parser type-checking itself**,
  21 sigs) - and the whole error suite (`errors/01...09`): the 6 real type/affine/
  trait rejects match by message, and `04_nonexhaustive`/`06_matchfail` correctly
  **accept** (infer.py performs no exhaustiveness check - a runtime concern). The
  2 skips are exactly the two `import` files (`09_modules/main`, `16_stdlib`); the
  single-file port deliberately has no import mechanism.
- **Makefile:** added `infersmoke` + `infertest`; `infertest` now part of `test:`.
- **07/ oracle untouched.** With M1 (lex), M2 (parse), M3 (infer) and M4 (cek) all
  differentially green, the entire front-end + evaluator is self-hosted.
- **Next:** M5/M6 - bootstrap & fixpoints (F1-F3). The open problem is interpretive-
  tower perf (cubic meta-circular cost), which a compiled bootstrap removes; it is
  no longer a feature gap.

### 2026-07-07 - M3 slice 2 complete: `tast.lark` (the typed AST, in Lark)
- **Ported `07/src/typed_tree.py` → `self/tast.lark`.** The typed AST the checker
  produces from a syntactic `Prog`: typed exprs (`TLit`/`TVar`/`TCon`/`TTupleExpr`/
  `TApp`/`TBinOp`/`TUnaryOp`/`TLetExpr`/`TIfExpr`/`TMatchExpr`/`TLambda`), each
  node's **last field a `Mono`**; typed patterns (`TPWild`/`TPVar`/`TPLit`/`TPCon`/
  `TPTuple`); typed decls (`TFnDecl`/`TLetDecl`/`TTypeDecl`/`TImplDecl`) carrying a
  generalised `Scheme`; `TVariant`; `TProgram`. Literal payloads reuse parse.lark's
  `Val`; a type-alias `TTypeDecl` uses `Maybe(List(TVariant))` (`Nothing` = alias),
  mirroring typed_tree.py's `variants | None`.
- **One renamed ctor: `TApply` → `TApp`.** parse.lark's *syntactic* type ADT
  already owns `TApply` (`TApply of String, List(Ty)`), and the M3 pipeline is one
  concatenated module (SELFHOST §7), so the two vocabularies share a namespace -
  same reasoning that M-prefixes types.lark's monotypes. `TApp` also matches
  ty.py's own abbreviation. Verified this is the **only** real collision: I
  grepped all 22 typed ctor names + 3 union names against parse+types+cek; the
  other apparent hits (`TVar`/`TCon` in types.lark, `TImplDecl` in cek.lark) are
  **comments only**, not declarations. Every typed type gets `impl Copy = {}`
  (infer.lark reuses subtrees across arms; Copy is name-only ⇒ free).
- **`tDeclSig` / `showTProgram`.** Not throwaway: this is exactly the M3
  differential's serialization - one line per top-level decl (`name : <type>` for
  fn/let via a small `prettyScheme` over types.lark's `pretty`; `type N` /
  `impl T for U` for the rest). The quantifier-prefix rendering (`forall ...`) is a
  placeholder to be format-matched against infer.py in slice 3.
- **Validation - `make -C self tastsmoke`** (`self/tests/tast_smoke.py`): no Python
  twin exists to diff (the typed AST's observable differential is *inferred types*,
  which needs infer.lark), so this is a concatenation smoke like `typesmoke`. It
  **concatenates lex+parse+types+tast** (lex is needed because parse.lark builds on
  its `Token` type + `Copy for List(Token)` - omitting it tripped an affine error
  on the token cursor `ts`), runs tast.lark's hand-built typed program
  (`type Color`, `id : ∀. α→α`, `answer : Int`, `impl Show for Color`), and checks
  the 5 output lines exactly. Strictness re-verified (a one-token printer
  perturbation fails immediately). All new work under `self/`; 07/ untouched.
- **Gotcha logged:** `trait` is a keyword - can't be a `match`-arm variable name
  (first draft used `TImplDecl(trait, ...)` → parse error); renamed to `tr`.
- **Next:** M3 slice 3 - `infer.py` → `infer.lark`, the mountain (Algorithm W,
  `infer`/`infer_pat`/`check_*_decl`/`typecheck` + Pass 1.5, `generalise`/
  `instantiate`, trait resolution, affine checking; `Fresh` threaded as an `Int`
  like the lexer's `Pos`). Differential = inferred top-level types + accept/reject
  vs infer.py, driven by **concatenation** (lex+parse+types+tast+infer), since the
  import path still skips Pass 1.5 (SELFHOST §7).

### 2026-07-07 - M4: `read` (stdin) + import-skip lifted (multi-module programs run)
- **Two M4 gaps closed; corpus difftest now 29 corpus + 4 read = 33 ok / 0 fail /
  15 skip** (all skips legitimate: oracle-rejected library files, too-slow
  meta-circular loops). Only `self/cek.lark` + `self/tests/cek_difftest.py`
  touched - **07/ oracle untouched**, so C/Python runtime parity is unaffected.
- **import-skip lifted by INLINING** (not by fixing the toolchain's import path,
  which touches frozen 07/ - §7). The harness resolves each `import M exposing
  (...)` the same way cek.py's `load_import` does (`<dir>/<m.lower()>.lark` then
  `<dir>/<M>.lark`), strips the module's own `module`/`import` lines, removes the
  object file's `import` statements (a balanced-paren scan handles the multi-line
  `exposing ( ... )` form), and appends the module decls to the object source.
  The result is a self-contained program the port evaluates directly - exactly
  the flattening already used for lex+parse+cek. The oracle still runs the
  ORIGINAL file with real imports; outputs must agree. `export` prefixes and decl
  order don't matter (the port's parser accepts `export`; globals resolve
  mutually); visibility only ever HIDES names, so inlining (a superset) can't
  change an accept-test's runtime output. **Result: `09_modules/main` (import
  Shapes) and `16_stdlib` (import Stdlib) both pass byte-identically.**
- **Float builtins wired into the port** (were a documented gap): `16_stdlib`
  exercises `abs_float`/`sqrt_float`/`floor_float`/`ceil_float`, so `cek.lark`'s
  `builtin` dispatcher + `initialEnv` gained `int_to_float`/`float_to_int`/
  `float_abs`/`float_sqrt`/`float_floor`/`float_ceil` - each calls the host prim
  on a real `Float`, so the oracle's `_f32` truncation applies byte-identically.
- **Also fixed a latent 24_stringprims FAIL:** that file was extended (previous
  session, uncommitted) to call `string_to_float(...)` *directly as a builtin*,
  but the port only used it internally in `litVal`. Added `string_to_float` to
  the port's `builtin` dispatcher + `initialEnv` (mirrors `string_to_int`,
  returns `Result`). 24_stringprims now byte-identical again.
- **`read` (stdin) now genuinely supported** (was "returns empty line"). Clean
  design: the IO token `RIO` becomes **`RIO of String`** carrying the *pending
  stdin*, threaded by the program's own `io` sequencing - NOT a new machine-State
  field (that would churn all 67 SEval/SRet sites) and NOT an output-channel hack.
  `read(RIO(pending))` splits off the next line via `readLine` (first '\n' =
  codepoint 10 dropped; whole string if unterminated; "" if pending empty - the
  oracle's `sys.stdin.readline().rstrip("\n")`, incl. its EOF-returns-"" quirk)
  and returns `(RIO(rest), RStr(line))`. `print` returns the io value unchanged,
  so pending stdin flows through untouched; `out` stays PURE output (no separator
  trickery, extraction unchanged). Only ~6 sites changed: RVal ctor, showVal,
  the `read` builtin, `applyMain`/`runProgram` (gained an `input` param), + the
  new `RLine` carrier & `firstNL`/`readLine` helpers.
- **`read` validated by a dedicated differential check** (`read_checks` in the
  difftest, since no corpus file reads): an echo program run through the oracle
  (bytes piped to real stdin) vs the port (same bytes embedded as a String
  literal via `make_driver`'s new `input`), over 4 cases - two full lines, an
  unterminated last line, a short read that hits EOF, and empty stdin - **4/4
  byte-identical**. Distinct io names (io1/io2/...) sidestep the affine checker's
  dislike of a shadowed `io`; `read`'s `(IO,String)` is consumed via `match`
  (Lark `let` binds one name - no tuple destructuring).
- **Next in M4/M3:** M4's evaluator is now feature-complete for the slice
  (floats, traits, imports, read all done). Resume **M3's `infer.lark`** (the
  mountain: Algorithm W, Pass 1.5, traits+affine) - slice 1 (`types.lark`) is
  done; slices 2 (`typed_tree.py`→typed AST) and 3 (`infer.py`) remain.

### 2026-07-07 - M4: cek.c `string_to_float` (full runtime parity for floats)
- **Closed the pending parity gap** from the float-arithmetic entry below: the
  float work added `string_to_float` to `07/src/cek.py` + `07/src/infer.py` but
  left the **C runtime** without it, so a compiled program (the eventual F2
  bootstrap path) would reject float literals the Python CEK accepts.
- **Ported `_parse_float` → `parse_float_c`** in `07/src/cek.c`: same strict
  lexer FLOAT shape (optional sign, digits, `.`, digits - no exponent/prefix/
  whitespace), validates then stores `f32_bits(strtof(s, NULL))` (C stores f32
  bits like every float literal via `LIT_FLOAT`; Python stores the raw double and
  truncates at show/binop - both display through `%.7g` + `.0`, so identical).
  Added the `string_to_float` builtin case (mirrors `string_to_int`: `Ok(f)` /
  `Err("string_to_float: not a float")`) and registered it in `top_set`.
- **Validated:** extended `07/tests/24_stringprims.lark` with four
  `string_to_float` cases - `"3.14"→Ok: 3.14`, `"-0.5"→Ok: -0.5`, `"abc"→Err`,
  and `"42"→Err` (int-shaped rejected: the strict FLOAT shape requires a `.`).
  `python3 src/cek.py tests/24_stringprims.lark` matches the expected block, and
  **`make cektest` = 31/31 C↔Python byte-identical** (incl. 24_stringprims). No
  regressions. The M0 lock-step discipline (every prim in *both* runtimes) is
  restored; SELFHOST §7's implicit "cek.c parity pending" for floats is cleared.
- **Note:** this does NOT change the M4 differential (`cek.lark` runs on the
  *Python* host; unchanged at 28 ok / 16 skipped). It's about the compiled
  runtime that F2 will use. Still out of C scope (no corpus file needs them):
  `int_to_float`/`float_*` are already in C, but the port's `builtin` dispatcher
  in `cek.lark` still lacks the non-arith float prims (unchanged this entry).
- **Next in M4:** `read` (stdin), then lift the import/Stdlib skip.

### 2026-07-07 - M4: custom trait-method dispatch (RDispatch + con→type map)
- **Goal:** dispatch user-defined trait methods (`impl Area for Shape`,
  `impl Describe for Color`) so **08_traits** passes - the last non-import,
  non-timeout skip. The port already did nothing with `ImplDecl`; `apply`'s
  catch-all returned `RUnit`, so `area(x)` yielded `()`.
- **Ported cek.py's mechanism** (VDispatch + `m.dispatch` + `runtime_type` +
  eval_program's `TImplDecl` case) into the *pure* port:
  - added **`RDispatch of String`** to `RVal` (the method name);
  - **`runtimeType(v, g) : String`** mirrors `runtime_type` (RInt→"Int",
    RFloat→"Float", RBool→"Bool", RStr→"String", RUnit→"()", RCon→con→type map);
  - the dispatch table + con→type map live **inside the threaded globals `g`**
    under mangled keys - `"<meth>#<type>"` for impls and `"#type#<Tag>"` for
    con→type. `#` can't appear in a Lark identifier, so these never collide with
    real names (no new State field / no extra threaded param needed);
  - **`apply` now takes `g`** (was the one architectural change - its 3 call
    sites in `stepRet`/`applyMain` updated) so the `RDispatch` case can look up
    `g[meth#runtimeType(arg)]` and re-`apply` the impl closure;
  - **`addImplMethods`** (called from `addDecls`' new `ImplDecl` arm) registers
    each `IMethod` closure under `meth#type`, rebinds the method name to
    `RDispatch`, and - on the first impl that shadows a builtin (e.g. `show`) -
    **`seedPrim`** seeds Int/Float/Bool/String/() → the original builtin, exactly
    as cek.py does, so `show(42)` still routes to the builtin printer;
  - **`addVariants`** now also emits `"#type#<Tag>"→<TypeName>` entries; the
    built-in List/Result tags are seeded in `initialEnv` (matching cek.py's
    `con_to_type` for Nil/Cons/Ok/Err).
- **Impl closures capture `Nil`** (like top-level fns) and resolve constructors /
  other globals / top-level `let`s (e.g. `pi` in `area(Circle(r))`) via `g` at
  apply time - so registering them in Pass 1 before `addLets` is fine.
- **Two keyword/syntax gotchas hit & fixed:** (1) `impl` is a reserved keyword -
  can't be a pattern variable (`RSome(impl)` → renamed `fnv2`); (2) off-by-one in
  `initialEnv`'s trailing-paren count after adding the 4 con→type entries.
- **Verified:** `08_traits` now byte-identical (`the color is red / ... blue /
  areas: 12.0 and 78.53975`); `23_show_impl` (built-in Show impl) still passes.
  Full corpus **28 ok / 0 failed / 16 skipped** - up from 26; removed 08_traits
  from the harness `EXPLICIT_SKIP` (now empty of feature-gaps). No regressions.
- **Next in M4:** `read` (stdin), then lift the import/Stdlib skip; cek.c
  `string_to_float` for full runtime parity. Then resume M3's `infer.lark`.

### 2026-07-07 - M4: float arithmetic (RFloat = real `Float`, `string_to_float` prim)
- **Motivation:** the 4 float files were skipped as a *gap*, not excluded - so
  "add float arithmetic next" removes the skip. Root cause: parse.lark hands
  float literals to the evaluator as **lexeme Strings** (`VFloat of String`), and
  the port had no way to turn `"3.14"` into a `Float` (the mirror of how ints use
  `string_to_int`). No `string_to_float` existed in the runtime.
- **Added `string_to_float`** to `07/src/cek.py` (+ `_parse_float`: strict
  optional-sign / digits / `.` / digits, exactly the lexer's FLOAT shape, no
  exponent - so a future C runtime can match byte-for-byte; returns
  `Result(Float, String)` like `string_to_int`) and its type scheme to
  `07/src/infer.py` (`String → Result(Float, String)`). Registered in
  `initial_env`. **cek.c parity is still pending** (deferred, noted below).
- **`cek.lark`:** `RFloat of String` → **`RFloat of Float`**; `litVal` converts
  float literals via `string_to_float` (Err → `0.0`); new `floatBin` handles
  `+ - * /` and all six comparisons; `binop` gets the `(RFloat, RFloat)` case;
  `unaryop` gets float negation; `valEq` uses `==`; `showVal` uses the real
  `float_to_string` builtin. **Byte-parity by construction:** the port's float
  ops run on real `Float` values through the *host* cek.py, so the oracle's
  `_f32` 32-bit truncation is applied identically; literals are stored raw
  (truncation only in binop), matching how the oracle lifts a literal.
- **Result: 05_adt, 13_floatops, 20_floatprec now pass** (verified directly);
  **23_show_impl still passes** (regression check - `show(3.14)` via the new
  `float_to_string` path is byte-identical to the old lexeme path).
- **08_traits still skipped - but for a *different* reason.** Floats were only
  one of its two out-of-scope features; with floats fixed the port now prints
  `areas: () and ()` because `area(x)` (a **user-defined trait method**, `impl
  Area for Shape`) dispatches to nothing. The port implements only built-in
  `Show` dispatch, not custom trait methods - so 08_traits is re-labeled in
  `EXPLICIT_SKIP` as a trait-dispatch skip. This is the next M4 target.
- **Not wired (honest scope):** the port's `builtin` dispatcher still lacks
  `int_to_float`/`float_to_int`/`float_abs`/`float_sqrt`/`float_floor`/
  `float_ceil` (no slice-1 corpus file uses them); header comment updated.

### 2026-07-07 - M4 started: `cek.lark` (the `cek.py` evaluator port - slice 1)
- **Ported `07/src/cek.py` → `self/cek.lark`** (~555 lines): the small-step CEK
  machine that *evaluates* parse.lark's `Expr`. Contents: `RVal` runtime-value
  ADT (`RInt/RFloat`[lexeme String]`/RBool/RStr/RUnit/RTuple/RCon/RPartCon/
  RClosure/RBuiltin/RPrintIO/RIO`), `Frame` ADT, `State` = `SEval(Expr,env,kont,
  out) | SRet(RVal,kont,out)`, `stepEval`/`stepRet`/`step`, `run`/`runToVal`,
  `apply`, `builtin`/`builtinMulti` (string prims from M0, arity-tracked),
  `binop`/`unaryop`, `matchPat`, `initialEnv`, and program driver
  `runProgram`/`addDecls` (mutual recursion via a threaded globals env, no
  cek.py mutable-closure backpatch).
- **Naming under concatenation:** runtime ctors **R-prefixed** (`RInt`...) so they
  don't collide with parse.lark's syntactic `Val` (`VInt`...); reserved words `fn`
  avoided as identifiers (used `fv`/`fe`). Output is **accumulated** into a
  String threaded in `State` and printed once by the driver (the §7 pure-IO
  idiom) - pure Lark can't side-effect mid-eval.
- **Differential harness `self/tests/cek_difftest.py`** (adapted from
  parse_difftest): for each corpus file, oracle = `cek.py file` stdout; port =
  concat(lex+parse+cek) + a generated `main` that lexes/parses/evaluates the
  file's source *as a String literal*, run through cek.py; compare line-for-line.
- **Result: 23 ok / 0 unexpected fail / 21 skipped (44 files).** Passing incl.
  01_hello, 02_arith, 03/21 recursion, 06_lists, 07_result, 10_closures, 11_tree,
  12_tuples, 14_stringops, 17_mutual_rec, 18_litpat, 19_intoverflow, 22_io_seq,
  **23_show_impl** (user `impl Show` dispatch works), 24_stringprims, and
  **6/9 samples** (mergesort, bst, primes, expr, rle, hanoi[16 lines], parser).
- **Skips (all documented, none a correctness gap):** `import`/Stdlib (slice 1);
  **float arithmetic** - 4 files in `EXPLICIT_SKIP` (`05_adt`, `08_traits`,
  `13_floatops`, `20_floatprec`): the port has no float binop / `string_to_float`
  so `pi*r*r` etc. → unit; float *literals* + `show(3.14)` DO work, so the skip
  is by-file not "any FLOAT token"; **meta-circular too slow** - 6 files exceed
  the 90 s budget (`04_tailrec`=1e6 iters, `15_tailrec2`, `queens`, `life`, ...);
  harness now treats a port timeout as skip-with-reason, not FAIL.
- **WARNING Finding logged (SELFHOST §7): `infer.py` occurs-check gap.** A generic fn
  that *builds* `List(a)` from a polymorphic element (`Cons(x, ...)` with `x:a`)
  makes `compose` create `α↦α` with no occurs-check → `apply` loops forever
  (`RecursionError`). Narrowly triggered (value/return position, constructor
  element var vs annotation var); `id`, `(a,a)`, and `List(a)→Int` are all fine,
  which is why parse.lark and generic `ckLen` are unaffected. **Fix used:**
  monomorphise `ckSnoc` to `List(RVal)` (its only call type). Also logged the
  cubic meta-circular perf as a harness (not correctness) property.
- **Next M4:** float arithmetic (`string_to_float` prim + float `binop`), then
  full trait/`impl` dispatch (Show already works), then `read`; then lift the
  import/Stdlib skip so real multi-module programs run.

### 2026-07-07 - M3 started: `types.lark` (the `ty.py` port - M3 slice 1/3)
- **Ported `07/src/ty.py` → `self/types.lark`** (~330 lines): the internal type
  representation the checker stands on. Contents: the `Mono` ADT, `Scheme`,
  substitution as an assoc list, `apply`/`applyScheme`/`compose`, `freeVars`/
  `freeVarsScheme`, `unify` (+ `unifySeq`/`bind`), the `isCopy` check, and the
  `pretty` printer (Greek var display incl. ty.py's ς-skip table + `α<N>` after 23),
  plus `tList`/`tResult` helpers.
- **Key design decisions (also relevant to the rest of M3):**
  - **M-prefixed monotype constructors** `MVar/MCon/MApp/MFn/MTup` (not ty.py's
    TVar/TCon/TApp/TFn/TTup). Why: parse.lark's *syntactic* type ADT already owns
    `TFn`/`TName`/`TApply`/`TUnit`/`TTuple`, and the M3 pipeline is assembled by
    **concatenation** (the import path skips Pass 1.5 - SELFHOST §7), so the two
    type vocabularies share one namespace and must not collide. `infer.lark` will
    consume parse.lark's `Ty` (surface) and emit `Mono` - both present at once.
  - **Substitution = `List((Int, Mono))`** (assoc list, raw tuples - no newtype).
    This is the persistent-map answer to the union-find risk (§7): `substGet` is
    a linear scan; `compose s1 s2` = `appendSub s1 (mapApplyRange s1 s2)` so s1's
    entries sit in front and win lookups (immutable `dict.update`).
  - **`unify : Mono -> Mono -> Result(Subst, String)`** - no exceptions in Lark,
    so the Result is threaded by every caller (nested `match Ok/Err`). `unifySeq`
    is the accumulator fold from `ty._unify_seq` (apply-then-recurse-then-compose).
  - **Dynamic string equality is char-by-char** (`strEq` via `string_index` +
    Int `==`), NOT operator `==` - string `==` still crashes in `cek.binop`
    (M1 finding, §7). Constructor-name comparison in `unify`/`isCopy` uses it.
  - **`Mono`/`Scheme` get `impl Copy`** so values reuse across match arms/lets
    (same affine-across-branches wart as M2, §7). A small local `Opt` ADT
    (`ONone`/`OSome`) stands in for `substGet`'s result (avoids a Maybe import).
- **Fidelity check:** ran the same monotypes through **both** `types.lark` (via
  `cek.py`) and `ty.py` directly - identical on pretty(fn/tuple/nested/α25),
  `unify`+`apply` results, the `cannot unify Int with String` message, and the
  full `cannot unify α with List(α): occurs check failed` message (matched after
  wrapping `bind`'s occurs error like `ty.UnifyError` does, not a bare reason).
- **Validation:** `make -C self typesmoke` - 11 smoke assertions, all correct.
  No corpus-wide differential yet: at M3 the differential is *inferred top-level
  types*, which needs `infer.lark`; `types.lark` alone has no Python-callable
  twin to diff, so it's smoke + oracle cross-check for now.
- **Next:** M3 slice 2 = `typed_tree.py` → typed AST ADTs (low; mirrors the
  `TExpr`/`TPat`/`TDecl`/`TProgram` shapes, each node carrying a `Mono`). Then
  slice 3 = `infer.py` → `infer.lark` (the mountain). `Fresh` becomes an `Int`
  threaded like the lexer's `Pos`; `instantiate`/`generalise` live in infer, not
  here. Watch: `_load_import` re-check still skips Pass 1.5 (§7), so the M3
  differential driver must **concatenate** lex+parse+types+tast+infer, not import.

### 2026-07-07 - M2 complete: `parse.lark` (AST + parser, in Lark)
- **Ported `07/src/tree.py` + `07/src/parser.py` → `self/parse.lark`** (~900 lines,
  one file - the AST/parser split isn't worth two Lark modules). Full AST as ADTs
  (Ty/Val/Pat/Expr/Decl/... mirroring tree.py), the complete LL(1) recursive-descent
  grammar (module/imports/decls, fn/let/type/trait/impl, full precedence chain,
  types, patterns), and a canonical S-expression pretty-printer.
- **Idiom - token cursor as a Copy value.** The token stream is a `List(Token)`
  (Copy, imported from Lex) threaded through every parse function; each returns
  `(Node, List(Token))` = node + remaining tokens (the functional `self.pos`).
  "Expect kind K" is a *structural match on the head token*
  (`Cons(Tok(KUpper, name, _, _), rest)` grabs text + tail at once); guaranteed
  tokens are dropped with `advance`. Fallback `_` arms return placeholders (never
  fire on the valid corpus - parser.py raises there).
- **Copy for AST nodes.** Every AST type gets `impl Copy = {}` so a node can be
  reused across `match` arms - the precedence tails reuse `left` in every arm,
  which the affine-across-branches checker (§7) would otherwise reject. Copy impls
  are name-only in infer (no field check), so this is free.
- **Literals.** INT/FLOAT keep the lexeme text (verified: `str(int|float)`
  round-trips it with 0 mismatches over the corpus's 354 ints / 49 floats), so
  serialization matches Python's `str(value)`. STRING carries the escape-processed
  value (mirrors `lexer._read_string`) to match parser.py's `tok.value`.
- **WARNING Composition finding (logged SELFHOST §7):** parse.lark *reads* as a clean
  `import Lex` component, but the differential driver is built by **concatenation**
  (lex body + parse body + generated main, one `module Selfhost`). Reason: the
  toolchain's *import* path re-type-checks the imported module WITHOUT infer's
  Pass 1.5 mutual-recursion pre-registration, so lex.lark's forward references
  (`read_name → keyword_kind`) raise `unbound variable` on import though lex.lark
  checks fine standalone. Concatenation routes everything through the top-level
  typechecker (which pre-registers). Toolchain gap, not a language one; clean fix
  touches frozen 07/ so deferred.
- **Differential harness:** `self/tests/parse_difftest.py`. Per corpus file it
  serializes `parser.py`'s Program to the canonical S-expr (Python mirror of the
  Lark `sX` functions; bool-before-int for VBool/VInt; `_` for None), builds the
  concatenated driver embedding the source as a String literal, runs it through
  `cek.py`, and diffs line-lists. Corpus = 07/tests + 07/samples + self/ (excl.
  `_*` temp drivers).
- **Validation:** `make -C self parsetest` = **47 ok, 0 failed, 0 skipped** -
  including `self/parse.lark` parsing its own 139-declaration source, `Stdlib.lark`,
  and every sample/test. Strictness re-verified: a one-token serializer
  perturbation (`(BinOp` → `(BinOpX`) fails the diff immediately.
- **Also:** `self/Makefile` gains `parsetest` (and `test` now runs lex+parse).
  Both CEK runtimes untouched; all new work under `self/`.
- **Next:** M3 - the typechecker (ty.py/typed_tree.py/infer.py → Lark): the hard
  core (Algorithm W, persistent union-find, generalization, trait resolution,
  affine checking). Validate inferred types + accept/reject vs infer.py.

### 2026-07-07 - M1 complete: `lex.lark` (the lexer, in Lark)
- **Ported `07/src/lexer.py` → `self/lex.lark`** (~330 lines). Faithful: same
  token kinds (names mirror the `TK` enum), keyword table, int/float scanning
  (float only when `.` is digit-followed), string literals with escape-skipping,
  nested block comments, all operators/punctuation, and 1-based line/col.
- **Key idiom - single-value state threading.** Lark's `let` binds *one* name and
  cannot destructure a tuple, so multi-value returns are carried as one `Copy`
  ADT value `Pos(pos,line,col)` and read back with accessor functions
  (`pos_of`/`line_of`/`col_of`). `Copy` makes reuse across branches free (Int is
  Copy). Readers return `Lexed(Token, Pos)`; only the token loop `match`es.
- **WARNING Language finding (logged SELFHOST §7):** string `==` **typechecks** (Eq is
  polymorphic) but is **unimplemented in `cek.binop`** - it crashes at runtime
  (`cannot apply '==' to <str> and <str>`; only string `+` is implemented).
  `_val_eq` *does* compare strings, so **literal patterns in `match` work** -
  keyword lookup uses `match text with | "and" => ... | _ => KName end`. Clean fix
  (add `VStr`/`VBool` to `binop` in both runtimes) is a candidate follow-up.
- **Differential harness:** `self/tests/lex_difftest.py`. Per corpus file it
  serializes `lexer.py`'s tokens to canonical lines (`KIND line col esc(text)`),
  generates a driver by stripping lex.lark's smoke `main` and appending one that
  embeds the source as an (escaped) String literal + prints `dump(tokenize ...)`,
  runs it through `cek.py`, and compares line-lists (splitlines dodges trailing
  `\n`). Escaping mirrors lex.lark's `escape` (\\ n t r). Corpus = 07/tests +
  07/samples + self/ (incl. lex.lark itself).
- **Validation:** `make -C self lextest` = **46 ok, 0 failed, 0 skipped** -
  including `self/lex.lark` lexing its own 2776-token source byte-identically,
  and the escape path (07_hanoi/08_life string escapes). Verified strict: a
  deliberate `kind_name` perturbation fails the harness immediately.
- **Also added:** `self/Makefile` (`lexsmoke`, `lextest`, `test`). Both CEK
  runtimes untouched (07/ stays the frozen oracle); all new work under `self/`.
- **Next:** M2 - `ast.lark` (port `tree.py`) then `parse.lark` (grow
  `09_parser` to the full grammar), differential on pretty-printed AST.

### 2026-07-07 - M0 complete: string-decomposition prims
- **Added four runtime prims** to *both* CEK runtimes in lock-step:
  - `string_index : String -> Int -> Int` - codepoint at index, `-1` if OOB.
  - `string_slice : String -> Int -> Int -> String` - `[lo,hi)`, bounds clamped.
  - `char_to_string : Int -> String` - 1-byte string from a codepoint (`&0xFF`).
  - `string_to_int : String -> Result(Int, String)` - strict signed-decimal parse.
- **Files:** `07/src/infer.py` (type schemes), `07/src/cek.py` (Python CEK),
  `07/src/cek.h` + `07/src/cek.c` (C CEK). Multi-arg builtins needed a
  partial-application mechanism: Python `VBuiltin` gained an `args` tuple +
  `BUILTIN_ARITY`; C gained a `V_BUILTIN_PART` value kind + `LkPartBuiltin`
  struct, mirroring `LkPartCon`.
- **Decisions (see SELFHOST §7):**
  - *`Copy for String` - already settled:* `String ∈ BUILTIN_COPY`, so source
    text is freely indexable. No change needed.
  - *Option → Result:* plan said `string_to_int : ... -> Option`, but `Option`
    is user-level (Stdlib), not a built-in constructor; used built-in `Ok`/`Err`
    (`Result`) so the prim needs no stdlib import and stays in C/Python parity.
  - *ASCII/byte semantics:* Python indexes codepoints, C indexes bytes; they
    agree on the ASCII self-host corpus (same convention as `string_length`).
- **Validation:** new `tests/24_stringprims.lark` exercises all four prims;
  `make cektest` = **31 passed, 0 failed** (C vs Python byte-identical). Full
  `run_tests.py` = **78 passed, 0 failed** (24 marked CEK-only via
  TAC_VM_SKIP/RV32_SKIP - the TAC/RV32 backends get these prims at M6/F3).
  `self/lex_smoke.lark` (a real cursor-based mini-lexer) produces identical
  output on both runtimes.
- **WARNING Language constraint (reconfirmed; SELFHOST §7):** the affine checker
  **sums** a variable's uses across `if` branches *and* `match` arms rather than
  treating them as mutually exclusive - so an affine value (`io`) cannot be
  threaded through any branching control flow (even the canonical `match`-based
  list printer fails). This is the *known* "affine IO idiom" already noted in
  Phase 7 samples (project_lark.md): keep recursion **pure**, thread IO only
  sequentially at top level, build the output value and print once. Flagged here
  because it directly shapes how the self-host lexer/printer must be written.
- **Reviewed `07/samples/09_parser.lark`** (M2 scouting): a pure LL(1) arithmetic
  parser (5 mutually-recursive rules + `pand`/`por` combinators, `List(Token)` →
  `Result((Expr, List(Token)), String)`). Proves recursive descent + combinators
  + mutual recursion work in Lark - but it is **monomorphic and tiny** (one AST,
  arithmetic only); M2 must scale it to the full grammar / `tree.py` AST, it is a
  shape proof not a skeleton. Gotcha flagged in the sample: pass parsers as
  **lambdas, not bare top-level names**, to avoid a closure-stub calling-convention
  path (appears backend-specific - `lex_smoke` passes bare `is_alnum`/`is_digit`
  to `scan_while` and runs fine on both CEK runtimes; watch this at M6/F3).
- **Next:** M1 - `self/lex.lark`, validated differentially against `lexer.py`.

### 2026-07-07 - Project kickoff & planning
- Chose the next big build: **self-host Lark in Lark** (biggest challenge, in Lark itself).
- Surveyed the current toolchain: ~5,840 lines Python in `07/src/`; confirmed the
  language is capable (ADTs, match, traits, `09_parser.lark` = a parser in Lark).
- **Key finding:** no string-decomposition primitives in the runtime → a lexer
  can't be written in Lark yet. This is M0 and the critical path.
- Confirmed **no optimizer exists** in the pipeline (only backend TCO); ch08
  theory/demos exist but run on a toy AST, decoupled from real TAC.
- Wrote `SELFHOST.md` (M0-M6, fixpoints F1/F2/F3) and `OPTIMIZE.md` (O0-O5,
  deferred to after self-hosting).
- Archived old build notes → `../old/` (`build.md`, `lark-build.md`), banner-marked.
- Updated memory (`project_lark.md`, `MEMORY.md`): corrected path `lang/lark`→`stack/lark`,
  recorded the new effort and this log.
- **Next:** SELFHOST **M0** - design the four string primitives, settle
  `Copy for String`, add to `07/src/cek.c` + `07/src/cek.py` with parity tests.
