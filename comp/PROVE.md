
## Proving Programs — Refinement & Dependent Types for Lark (Project Plan)

> **📓 The rule of record.** A rung's story is written ONCE — in its dated entry
> in [`LOG.md`](./LOG.md). This file is the MAP: the ledger below flips one line
> per milestone, §4 holds the ladder, §5–§7 the guardrails and boundaries.
> After any `/clear`: read `LOG.md`'s top pointer for the current position,
> then come here when working this axis — and append to the LOG when you stop.

**Status: ACTIVE — V2's HEADLINE fully reached (2026-07-16; V2.5/V2.6 not picked up); V3 STARTED same day: the SPINE IS CLOSED at 0.**
**Drafted:** 2026-07-07.

The ledger (one line per milestone; each story is in `LOG.md` under its date):

- **Step 0 OK 2026-07-13** — the oracle forked: `08/` exists; conservative-extension baseline green *before* the first refinement.
- **V1 OK 2026-07-13** — `{v:Int|p}` parses and *erases*; `refine.py` generates VCs bidirectionally; `solver.py` decides QF-UFLIA from scratch (congruence closure + the Omega test under DPLL(T)) — no Z3, the `--smt` hatch unneeded; affine × refinement settled (§7).
- **V1′ OK 2026-07-14** — fuzz-hardening; the rule: a budget must give up in the sound direction.
- **V2.0 OK 2026-07-14** — refined products: a fact travels through a tuple; only a measure can create one.
- **V2.1 OK 2026-07-14** — `measure` declared and checked well-formed: ghost, structural, total.
- **V2.2 OK 2026-07-14** — measure equations reach the solver, instantiated at the constructor terms a program *mentions* and nowhere else; `solver.py` unchanged byte for byte.
- **V2.2′ OK 2026-07-14** — the FIRST FOUR FALSE PROOFS, found and closed: Float reflexivity; an untranslatable `if` condition read as `true`; a UF symbol captured by a shadowing local; a captured non-negativity axiom.
- **V2.2″ OK 2026-07-14** — the impl hole closed: an `impl` body is a body.
- **V2.2‴ OK 2026-07-14** — `08/tests/adversary.py` (run what you proved): FALSE PROOFS FIVE–SEVEN, including divisions that were never visited at all (`ok: 0 obligation(s) proved`, exit 0, then a crash).
- **V2.3 OK 2026-07-14** — a measure's declared result proved by structural induction; `NONNEG_UF` deleted; faith reduced to one named line (`PRIMITIVE_AXIOMS`).
- **H OK 2026-07-14** — the *no-answer* failure: `08/tests/torture.py`; global budgets (every fence was local, every caller loops); the cubic a stack overflow had been mercy-killing; `ResultAxiom`.
- **I OK 2026-07-14** — the rules became a program: `08/tests/invariants.py` (coverage / asking / work) — and the EIGHTH FALSE PROOF, the first found on purpose (`synth` never walked a lambda's body).
- **V2.4 + V2.4b OK 2026-07-15** — Bool measures as propositions (the Bool-atom congruence bridge); polymorphic fields via the binder's HM monotype, never inferred from a measure.
- **V2.4c steps 1–2 OK 2026-07-15** — `min`/`max` as UF symbols with their defining axioms; `if` in predicate position (+ invariant I5, faithful translation).
- **V2.4c step 3 OK 2026-07-15** — Part A: the adversary speaks min/max + refined lambdas → the NINTH FALSE PROOF (a lambda parameter's contract assumed in the body, never discharged at the call) + a min/max robustness hole. Part B: NESTED MATCH in a measure — flatten to guarded arms, fire at concrete subfields (+ invariant I6, guard scoping).
- **V2.4c step 4 OK 2026-07-15** — the binary search tree, BUILDING direction: pure assembly, not one line of `src/` changed.
- **Float interlude + the equality seam OK 2026-07-15** — not rungs. The one Float fact realised through different machinery per context, fixture-pinned and fuzzed; `==` as one operator in three worlds, documented as the third deliberate boundary — and the would-be TENTH false proof (`_val_eq` reroute) vetoed on the bench.
- **RUNG (1) OK 2026-07-16** — the adversary speaks nested measures (two shapes) + a THIRD, semantic oracle; watched to fail at volume (a planted regression → 4 false proofs at seed-5/800; restored, clean).
- **RUNG (2) = V2.4c step 5 OK 2026-07-16 — BOUNDARY #3 CROSSED** — the DESTRUCTING bst: not bound invariants (that framing was wrong) but `bst` as a SINGLE match over extra-parameter measures `lt(t,b)`/`gt(t,b)`, whose unguarded equation fires at opaque binders and hands the order facts back out; extra-param equations fire DEMAND-DRIVEN (`refine.py` `measure_axioms` rewritten — the one `src/` change; solver untouched). *(Same session: `cek.c` min/max parity gap closed.)*
- **V3-SPINE OK 2026-07-16** — `formal/proof/lark/lark-refine.lcore` closes at 0: `sub_sound` (base-Int refinement subtyping ⇒ semantic implication) by `indrec Sub` over a step-indexed relation (`SemV`/`SemE`/`StepsN`/`Le`) standing on `Step`/`IsVal`; precondition: `ELitInt` given its `Nat` payload across all four metatheory files (else every refinement is vacuous), re-closed at 0; 4 negative controls refused, incl. a budget violation (the index is load-bearing).
- **V3-MONO OK 2026-07-16** — monotonicity in the step budget: `sem_e_mono` (`Le k k' → SemE k p e → SemE k' p e`) via `le_trans`, which needed real machinery — inversion of `Le (succ m) c` by a natrec-COMPUTED motive + `J`-transport of the endpoint; for THIS relation monotonicity runs UPWARD (budget widening); downward closure of the value relation is trivial until TFn indexes `SemV` (named in the file). 4 negative controls refused; `le_trans` COMPUTES on concrete derivations.
- **V3-TFN OK 2026-07-16** — function-type refinements, the relation goes RECURSIVE: `RTy : Ty → Type` (erasure = the index, no transport), `SemV` by `indrec RTy` (large elim; RFn = IsVal + applicative clause over the IHs), `Sub` grows `SubFn` (contravariant domain / covariant codomain), `sub_sound_v`'s SubFn case fires both IHs in opposite directions. Ratified fork: the index is INERT inside SemV at this rung (Σ k' existential budget in the arrow clause — the ∃-form SemE cannot budget it honestly, false at j = 0); it becomes load-bearing at descend, when E flips to ∀/safety. 4 negative controls refused (variance flip, IsVal forge, codomain promise, erasure seam); found `W` reserved in lcore's parser. Story: LOG.md ▶▶ V3-TFN.
- **V3-FUND OK 2026-07-16 — THE SUMMIT, Pitch 1** — the fundamental lemma: a refined typing judgment `HasR` (RT_Int demands payload EVIDENCE, RT_Var reads the rider off `RCtx` by computation, RT_App demands the argument's refinement EXACTLY, RT_If by J-transport along RBool's pinning + boolrec, RT_Sub = the calculus's `Sub`) and `fund : HasR g rg t r e → GoodEnv g rg env → Σk. SemE t r k (e[env])` by `indrec HasR` — every derivation lands in the relation. Congruence lifts through the CBV frames by `Id`-coerced motives (the le_inv trick lifted from Nat to Ty; coercions compute away at refl); budgets concatenate (`plus`/`le_plus_mono`/`steps_append`). RT_Lam/RT_Let DEFERRED to Pitch 2: the substitution lemma bottoms out at kernel-opaque `weaken` — named, priced, not fudged; higher-order USE is proven (functions enter as `GoodEnv` hypotheses). Showcase smoke `f (if true then 2 else 3)` fires every rule and COMPUTES to the canonical 2-step certificate at the weakened `{ge1}`. 4 negative controls refused (payload forge, rider forge, no-implicit-subsumption at App, SemV forge). Story: LOG.md ▶▶ V3-FUND.
- **V3-WK0 OK 2026-07-16 — PITCH 2's ENABLING RUNG** — the diagnosis-then-fix that unblocks the substitution lemma. The kernel primitive `weaken` (eval.c `weaken_expr_val`) `exit(1)`s on a constructor with NEUTRAL CHILDREN — exactly the `indrec Expr` case shape — so it can never be the subject of an induction (probe_weaken.lcore). FIX: weakening rebuilt IN lcore with an explicit Nat cutoff — `ins`/`shift`/`wk`/`wk0` in `lark-subst.lcore`, computing ONE constructor-layer at a time (the succ case rides the outer natrec ih, making `ins a (succ m) (ext s g) ≡ ext s (ins a m g)` definitional even on neutral tails). `weaken_semctx_d`/`sub_open` rebased onto `wk0` (drop-in, same type), taking the whole `sub_ground` path — hence StepBeta/StepLetBeta's contractum — off the kernel primitive: TRUSTED BASE SHRINKS. A latent kernel quirk surfaced (kernel `weaken` mis-encodes the `there` sub-context on the Var case; `wk0`/`shift` get front-insert right — never bit Pitch 1, where `weaken_semctx_d` was unused). Green before and after. Story: LOG.md ▶▶ V3-WK0.
- **V3-SIGMA-1 OK 2026-07-16 — σ-FUSION PILE, Var/ENVIRONMENT LAYER** — the substitution lemma's non-`indrec-Expr` obligations, three small commutation lemmas in `lark-subst.lcore`, each refl-in-base + IH-in-step, NO J, green at each step. (1) `wk_lookup`: lookup commutes with env weakening — `sem_lookup_d (ext a d) g t v (weaken_semctx_d a d g env) = wk0 a d t (sem_lookup_d d g t v env)` (clean because `weaken_semctx_d` changes only the OUTPUT context, so the source var is looked up unchanged). (2a) `del` (delete the env entry at de Bruijn depth n, `natrec`+`indrec Ctx` mirroring `ins`) + `sdl`: shift/del/lookup cancellation `sem_lookup_d d (ins a n g) t (shift a g t v n) env = sem_lookup_d d g t v (del a n g d env)` — the Var case of the coming big induction. Story: LOG.md ▶▶ V3-SIGMA-1.
- **V3-SIGMA-2 OK 2026-07-16 — σ-FUSION PILE, WEAKEN-SUBST COMMUTATION `GenCancel`** — the big brick, the one obligation needing `indrec Expr`: `sub_open (ins a n g) t (wk a g t e n) d env = sub_open g t e d (del a n g d env)` (substitute into a weakened term = substitute into the original under the env with the inserted entry deleted). Landed with a generic J-based Id-congruence toolkit `ap`/`trans`/`ap2`/`ap3` (first reusable congruence helpers in the lark files) and `del_wk` (`del` commutes with `weaken_semctx_d`, `natrec`+`indrec Ctx`, for the binder cases). `GenCancel` = `indrec Expr`: literals=refl, EVar=`sdl`, EApp=`ap2`, EIf=`ap3`, ELam=`ap(ELam)∘trans∘del_wk`, ELet=`trans∘ap` (sub_open inlines let, so its case substitutes the value into the env). 6 ground smokes cancel to `refl` — every branch fires. `del_wk` re-bit the natrec-scrutinee lesson (missing `\n.` → "unbound variable 'n'"). REMAINING (brick 3): instantiate GenCancel at n=0 → assemble THE FUSION. Story: LOG.md ▶▶ V3-SIGMA-2.
- **V3-SIGMA-3 OK 2026-07-17 — σ-FUSION PILE, THE GSW TOWER (weakening⇄substitution⇄composition), CLOSED** — the autosubst machinery V3-SIGMA-2 flagged as "genuine, large in raw lcore", built brick-by-brick in `lark-subst.lcore`, green at each step. (3d) THE EXCHANGE SWAMP: `shift_shift` (two-cutoff de Bruijn var exchange under the `ins_ins` coercion) + `wk_wk` (its Expr-level lift). (3e) `weaken_n_commute` (the two `SemCtx_d` env-weakenings commute; ext-case head = `wk_wk`@0 on the nose since `ins_ins@0 ≡ refl` kills the residual `trC`) → `GSW` (substitution commutes with weakening the OUTPUT context, cutoff-generalised, `indrec Expr` mirroring GenCancel) → `sub_weaken` = `GSW`@0. (3f) `comp_weaken` (`comp` commutes with weakening under a binder; env-induction, per-entry brick = `trans (GenCancel@0) sub_weaken` — this is WHY `sub_weaken` came first) → `sub_sub` THE COMPOSITION LEMMA: `sub_open d1 t (sub_open g t e d1 env1) d2 env2 = sub_open g t e d2 (comp d1 d2 env2 g env1)` (sub∘sub = sub-with-composed-env), `indrec Expr` with EVar=`comp_lookup` on the nose, binder cases fire the IH then reconcile envs via `comp_weaken` (orientation reverses GSW's). Load-bearing at each rung (watched-to-fail: refl-swaps refused). lcore lesson re-banked: REPL is LINE-BASED, a `:let` must be one physical line. Story: LOG.md ▶▶ V3-SIGMA-3d / 3e / 3f.
- **V3-SIGMA-3g OK 2026-07-17 — σ-FUSION PILE, THE FUSION `fuse`, CAP** — the capstone identity RT_Lam/RT_Let consume, landed in `lark-subst.lcore` (between `sub_sub` and `IsVal`), green (`OK: 5 files, 0 errors`). `fuse`: `sub_open (ext a empty) b (sub_open (ext a g) b body (ext a empty)(EVar…, weaken… env)) empty (V,star) = sub_open (ext a g) b body empty (V, env)` — LHS is EXACTLY the `StepBeta`/`StepLetBeta` contractum `sub_ground (ext a empty) b BODY (V,star)`; RHS is the honest one-shot `body[V,env]`. Proof = `trans (sub_sub …) (ap∘ap (comp_weaken_cancel a V g env))`: `sub_sub` collapses sub∘sub into sub-with-composed-env, the composite head reduces to `V` definitionally, and `comp_weaken_cancel` (already in the file) rewrites the tail `comp-tail ≡ env`. Watched-to-fail: `comp_weaken_cancel → refl env` refused (`definition of 'fuse' failed`). The WHOLE σ-FUSION PILE is now CLOSED (1 → 2 → 3d/3e/3f → 3g). Story: LOG.md ▶▶ V3-SIGMA-3g.
- **V3-FUND-P2 OK 2026-07-17 — PITCH 2, RT_Lam & RT_Let, `fund` COMPLETE** — the two λ-introduction constructors added to `data HasR` and their cases to the `indrec HasR` in `fund` (`lark-refine.lcore`); `fund` now covers the FULL calculus. Both bottom out at `fuse` exactly as designed. Seven helpers before `fund`: `lb` (opened λ-body), `lam_app_cert` (applicative-clause cert = `StepBeta` + `J`-transport along `sym(fuse)`), `fund_lam_case` (value at j=0, arrow clause runs the body IH), `lift_let` (`StepsN` congruence through the let scrutinee via `StepLet`), `semv_isval` (`SemV`⇒`IsVal`, fires `StepLetBeta`), `let_cert` (`lift_let` + `StepLetBeta` + `J`/`fuse` + `steps_append`/`le_plus_mono`), `fund_let_case` (threads the bound val's value + `SemV` goodness into the body IH). Two closed smokes run through `fund` (`(λx:{ge2}.x):{ge2}→{ge2}`, `let x=2 in x : {ge2}`); 4 negative controls refused with the chain loaded, honest probe accepted (non-vacuous — first run was vacuous via a zsh word-split bug, caught and reran). `tools/parens.py` gated each single-line def. Green: `OK: 5 files, 0 errors`. Story: LOG.md ▶▶ V3-FUND-P2.
- **V3-DESCEND-WALL NOPE 2026-07-17 — the ∀/safety form CLOSED as a named boundary (V3 upward axis complete).** Took DESCEND (flip `SemE` to ∀/safety) seriously into scratchpad probes, hit a hard kernel wall, reframed, turned back. Landed green as the record of where the wall is (scratchpad, not shared): `minus`+`minus_plus` (truncated subtraction, definitional); the flipped `SemEV2/SemV2/SemE2` (well-formed, vacuous at k=0); `stepsN_inv_succ` (count-inversion, works because the count is `Ctx`-free); `NV`/`isval_nv`/`step_not_val` (the negative/uniform direction). **Stopped at** `step_det`/positive `Step` inversion — inexpressible in lcore (the inversion motive would have to reconstruct the redex contractum from a generic source `Expr`, refining the `Ctx` index inside `indrec Expr`; the `beta_det` motive fails `inferred Expr empty b / expected Expr empty t1`). **Reframe:** Lark is SN, so the ∀-form's safety-under-divergence is vacuous and the ∃-form (V3-FUND) is the stronger total-correctness statement — nothing to descend to. **Decision (ratified with Set):** V3-FUND is the summit; ∀-form + the CBV non-determinism defect recorded as boundaries (§4 V3); reverted to the last green state (never left — all work stayed in scratchpad). Story: LOG.md ▶▶ V3-DESCEND-WALL.
- **STRAND-DENOT OK 2026-07-17 — the denotational model climbs WALL-FREE past DESCEND; full fundamental lemma proven, both λ-introductions in ONE LINE.** First of three post-summit STRANDS (`formal/proof/strands/`, order denot → solver → vdeep). Interprets refinement types as lcore TYPES and proves soundness by recursion on the DERIVATION (`indrec HasR`), never eliminating `Step` — so the DESCEND wall is structurally absent. `TyD`/`RTyD` ({v:Int|p}↦`Σ(n:Nat).IsTrue(p n)`, refined fn↦a dependent map); `sub_denot` (subtyping soundness, `f↦λx.ihc(f(ihd x))`, far cleaner than `sub_sound_v`); `DEnv`/`denot_lookup`; and **`fundD : HasR → DEnv → RTyD t r`** over all 8 rules, every case ONE LINE — `RT_Lam ↦ \env.\x. ihbody (x,env)` and `RT_Let ↦ \env. ihbody (ihval env, env)` need NONE of Pitch 2's substitution-lemma pile. Showcase `fundD_id` (identity on `{Int|ge2}`). 4/4 controls refused. New Makefile targets `denot` (6 files/0) + `denot-controls`; `make check` untouched at 5/0. **Named boundary:** soundness-of-the-model, NOT adequacy — no bridge yet from denotation to the CEK machine's output (complementary to operational V3); the adequacy bridge's forward direction should dodge the wall, untried, in `strands/denot/PLAN.md`. Story: LOG.md ▶▶ STRAND-DENOT.
- **STRAND-SOLVER ◐ 2026-07-17 — BOTH QF-UFLIA halves proven (not modelled): the interval LIA fragment AND congruence-closure soundness.** *LIA half:* `leB : Nat → Nat → Bool` (a real boolean ≤; the spine's `ge1`/`ge2` ARE `\n. leB c n` definitionally), proven sound AND complete vs the inductive `Le` (`leB_sound` by double natrec + `abort`; `leB_complete` by `indrec Le`). `entail_ge` decides one comparison `c2 ≤ c1` and transports via the existing `le_trans` to CONSTRUCT the `SubBase` premise; `sub_ge` emits the `Sub` certificate; **`sub_fixture : Sub TInt rge2 rge1`** discharges the exact seam V3 took on faith and `sub_fixture_sem` feeds it into `sub_sound_v`. S2 (`nmax`/`NList`/`norm`/`sub_conj`) handles constraint SETS by normalizing to the tightest bound. *UF half (STRAND-SOLVER-CC):* `data Tm`/`eval` (first-order terms interpreted in ANY model), `data Ax` (a concrete axiom `f a = a`), `data Cong` (the congruence closure as an inductive derivation), and **`cc_sound : Cong a b → Id D (eval a) (eval b)` in every model of the axioms** by `indrec Cong` (cAx↦hyp, cRefl↦`refl`, cSym↦`sym`, cTrans↦`trans`, cApp↦`ap2`) — the closure cannot derive a false equality; `cc_smoke_sem` reifies `f(f a) = a` and its normal form consumes the axiom twice. 8/8 controls refused (4 interval + 4 CC) — the solver cannot certify a false entailment or a false equality. `make solver` 6/0 + `make solver-controls` 8/8; `check` untouched 5/0. Both cores proven; full multi-var Omega + CC completeness remain optional WIDTH in `strands/solver/PLAN.md`. Story: LOG.md ▶▶ STRAND-SOLVER + ▶▶ STRAND-SOLVER-CC.
- **STRAND-VDEEP OK 2026-07-17 — a VERIFIED ELABORATION of every Lark derivation into an intrinsically-typed MLTT term; NO re-hit of the DESCEND wall.** Last, Set's pick — turned out the deepest AND wall-free. A minimal intrinsically-typed object theory inside lcore (`MTy`/`MCtx`/`MVar`/`MTm`, well-typing FUSED into the term index, so a closed `MTm g t` IS well-typed — no separate `HasMLTT` needed); translations `tyD`/`ctxD`/`elabVar` (`⟦·⟧`); intrinsic renaming via order-preserving embeddings (`OPE`, `ope_tm` under the mlam/mlet binder, `mweaken`) — the piece the operational proof could never reach; `elabSub` (SubBase↦`msub_weaken`, SubFn↦an η-coercion that WEAKENS `f` under the fresh binder, firing both variance IHs); and **`elab : HasR → MTm (ctxD g rg) (tyD t r)`** by `indrec HasR` over ALL 8 rules incl. both λ-introductions. C0 finding: `elab` recurses on the SOURCE `HasR` and only INTRODUCES target terms, so every rule is introduction-direction — never the positive-inversion-by-unification that killed DESCEND (the one `indrec MTm`, renaming, is still introduction-direction index-change). Smokes reuse the `fund` fixtures; `smoke_fn_coe` reifies a real function-subtyping and COMPUTES to the concrete `mweaken`-driven coercion. 4/4 controls refused. `make vdeep` 6/0 + `make vdeep-controls` 4/4; `check` untouched 5/0. Named boundary: `MSub` carries its predicate as a shallow `Nat→Bool` (semi-shallow); adequacy to the CEK output shared with denot. Story: LOG.md ▶▶ STRAND-VDEEP.

**Where that leaves it:** prove **75/0**; full `make -C 08 harden` green (drift · conservative 90/0/0 · solver · robust · fuzz · adversary · torture 14/14 · invariants I1–I6). NINE false proofs found and closed across the axis — all in the checker's translation layer, none in the solver. Deliberate boundaries, open by choice: ℤ-vs-32-bit; partial correctness; the equality seam; concrete-subfields one-sidedness (softened by rung 2, not dissolved).

**NEXT — the σ-FUSION PILE, then DESCEND (ratified 2026-07-16 "bank wk0 rung, then grind").** Pitch 2's enabling rung (V3-WK0), its Var/environment layer (V3-SIGMA-1: `wk_lookup`, `del`, `sdl`), the `indrec Expr` weaken-subst commutation (V3-SIGMA-2: `GenCancel` + `ap`/`trans`/`ap2`/`ap3` + `del_wk`), the WHOLE GSW TOWER (V3-SIGMA-3: `shift_shift`/`wk_wk` → `weaken_n_commute`/`GSW`/`sub_weaken` → `comp_weaken`/`sub_sub`), and now THE FUSION itself (V3-SIGMA-3g: `fuse`) are ALL DONE — **the σ-fusion pile is CLOSED**. `fuse` = `sub_sub` (the general composition lemma) instantiated at the β-redex + `comp_weaken_cancel`, and its LHS is literally the `Step` contractum. RT_Lam/RT_Let in `HasR` + their fund cases (the β-redex J-transported along `fuse`) are now DONE too (V3-FUND-P2) — **Pitch 2 is COMPLETE, `fund` covers the full calculus**. **The V3 UPWARD AXIS IS NOW CLOSED (2026-07-17).** DESCEND (flip E to ∀/safety) was the last candidate rung; it was explored, hit a hard kernel wall (positive `Step` inversion is inexpressible in lcore), and — since Lark is strongly normalizing, making the ∀-form's safety-under-divergence vacuous and the ∃-form's total correctness the stronger statement — was CLOSED as a named boundary rather than climbed. Full story: LOG.md ▶▶ V3-DESCEND-WALL; boundary + CBV side-finding recorded at §4 V3. **The summit is V3-FUND (∃-form), both pitches green.** Green bar for every V3 rung = `make -C formal/proof check` (fails loudly on any error line; lcore alone exits 0). The three locked decisions, and the boundaries V3 does not dissolve, are recorded in full at §4 V3. **PAST THE SUMMIT — three STRANDS (`formal/proof/strands/`, order denot → solver → vdeep, agreed with Set):** STRAND-DENOT is COMPLETE (the denotational model re-proves the whole refinement calculus wall-free, `make denot` 6/0 + `make denot-controls` 4/4); STRAND-SOLVER now proves BOTH QF-UFLIA halves (interval LIA: `leB` sound+complete, `sub_fixture` discharges the real `rge2 ⊆ rge1` seam; congruence-closure UF: `cc_sound` sound in every model), `make solver` 6/0 + `make solver-controls` 8/8); STRAND-VDEEP is COMPLETE (a verified elaboration `elab : HasR → MTm` into intrinsically-typed MLTT, all 8 rules, no DESCEND-wall re-hit, `make vdeep` 6/0 + `make vdeep-controls` 4/4). **All three strands have now reached a documented stopping line.** Each strand keeps its own green bar and never touches the main 5/0 `check`.

**Sequenced:** *after* self-hosting ([`SELFHOST.md`](./SELFHOST.md)); may also come
after the optimizer ([`OPTIMIZE.md`](./OPTIMIZE.md)). It is independent of both —
it can be prototyped in Python at any time, **in a fork of the oracle, never in
`07/src` itself** (see §0.1, which is the first thing to read).

**Goal:** let Lark *prove programs* to (something like) the standard the language
itself was proven to — move from "well-typed ⇒ won't get stuck" (the Phase 5b
metatheorem, already discharged for all programs) to "well-typed ⇒ meets its
specification" for specifications the checker can decide.

---

## 0. The two axes (why this is a separate path)

Self-hosting is about **expressive power** — can Lark build itself. This plan is
about **guarantees** — what the type system lets you *state and prove*. They are
orthogonal; finishing the bootstrap does not move this axis, and vice versa.

Today Lark gives, for *every* accepted program, exactly one proven property:
type safety (progress + preservation, `eval_produces_val` in `formal/proof/`).
That is real and free, but it is the ceiling of what HM + affine + traits can
express. To prove *correctness* ("this sort sorts", "this index is in bounds")
the type system must be able to (a) **state** the spec and (b) **decide** it.

Two flavours reach that, at very different costs:

- **Refinement types** *(the spine of this plan)*. Base types carried with a
  decidable predicate: `{ v : Int | v >= 0 }`. Function contracts may mention
  earlier arguments — dependency on *values*, but predicates stay in a decidable
  logic, so checking is automatic. This is the Liquid-Types design (Rondon–
  Kawaguchi–Jhala; Liquid Haskell; F\*'s core). It layers on the existing HM
  core with minimal disruption and gives the classic wins: bounds safety, no
  division by zero, non-negativity, sortedness, data-structure invariants.
- **Full dependent types** *(the deep stretch)*. Specs are arbitrary types and
  the checker *is* the prover (MLTT/Coq/Agda/Lean). Lark already has a home for
  this: the lcore MLTT kernel under `formal/proof/` and the ch12 `bridge/` demo
  that elaborates well-typed Lark into MLTT. This is a language redesign; we
  reach for it only where the decidable fragment cannot express the spec.

**Recommendation: refinement-first.** It is the achievable, high-payoff target
and fits Lark's character (small, purely functional, buildable from scratch,
pedagogical). Keep full dependent elaboration as `V-deep`, reusing the kernel we
already built rather than replacing the type system.

### 0.1 WARNING The oracle is frozen. This plan forks it; it does not edit it.

**Do not add `refine.py` or `solver.py` to `07/src`.** An earlier draft of this plan
said to prototype there, calling it "the frozen-oracle convention every other module
follows." That inverts the convention. Every other module was *ported from* the frozen
oracle and checked against it; **none was added to it.** The freeze is not tidiness —
it is what makes the whole method mean anything:

- `07/src` is the reference that every differential in both trees compares against.
  A reference that moves is not a reference; it is just a second implementation, and
  "the two agree" stops being a claim about correctness.
- Three fixpoints are pinned to its exact bytes — `49a4921c` (emit-only bootstrap),
  `829410dc` (typechecking bootstrap), `f1dedfa9` (the optimizing self-application).
  Touch `07/src` and all three re-open, along with every pinned count in both
  `BASELINES.md` files. We thawed it twice, on purpose, and both times cost real work
  and are recorded as *thaws* precisely because they were exceptional.

So the refinement prototype lives in **its own fork** of the oracle — `08/src/`, a copy
of `07/src` that this axis is free to change. The relationship to `07/` is the same one
`self/` has: a differential, not an edit. Where `08/` has not touched a module, it must
stay byte-identical to `07/`'s, and a drift check should say so — a `diff -r` of the two
`src/` trees, with an explicit allow-list of the modules this axis has deliberately
extended. Anything drifting that is *not* on the list is a bug, and the list is the
honest statement of how large the extension has grown.

This buys the thing that makes the axis honest: a program that type-checks in `07/`
must still type-check in `08/` with the same result *unless it carries a refinement*.
Refinements are an extension, and the extension must be conservative. Forking makes that
testable; editing in place makes it unfalsifiable.

---

## 1. Definition of done

Four milestones of increasing strength; stop where payoff/effort stops paying.

- **V1 — Refinement checker (bidirectional, annotated).** Surface syntax for
  `{ v : b | p }`, function pre/postconditions, and a decidable entailment
  check. Verifies a curated "safe" suite (bounds, div-by-zero freedom,
  non-negativity, `head`/`index` totality) and *rejects* the unsafe variants for
  the right reason. Checking only — no refinement inference yet.
- **V2 — Measures + data-structure invariants.** Structural "measures" lift
  facts into the logic (`len`, `elems`, `keys`, ordering). Express and check the
  classic demos on Lark's own samples: sorted-list `insert`, mergesort output
  sorted (`01_mergesort`), BST ordering invariant (`02_bst`). This is where
  "prove programs" becomes visibly real.
- **V3 — Soundness of the refinement calculus, mechanized.** Prove in lcore that
  refinement subtyping implies semantic implication (a refined value really
  inhabits its refinement), so the *checker itself* is proven — mirroring how the
  base language was proven. This is the milestone that answers the original
  question literally: programs are proven *because* the tool that checks them is.
- **V-deep — Dependent elaboration (stretch).** For specs beyond the decidable
  fragment, elaborate Lark terms into lcore/MLTT via the ch12 `bridge/`, carrying
  explicit proof terms. Full dependent proof for the programs that need it.

We commit to **V1 and V2**. V3 is the intellectually central goal and the reason
this belongs in *this* project (it closes the "prove programs like the language"
loop). V-deep is a genuine stretch.

---

## 2. Feasibility summary

**Layerable.** Refinement types are designed to sit *on top of* Hindley–Milner:
infer/(check) HM types first (we already do — `infer.py` / eventually
`self/infer.lark`), then run a second pass that checks refinements by reducing
subtyping to logical entailment. The HM skeleton is reused, not rebuilt.

**The one real dependency — a decision procedure.** Entailment `Γ ⊢ p ⇒ q` must be
decided. Two ways:

- **Build a small solver from scratch** *(recommended; fits the book's ethos)*.
  Target the standard refinement fragment **QF-UFLIA**: quantifier-free formulas
  over linear integer arithmetic + uninterpreted functions with equality. That
  needs (a) congruence closure for `=`/UF, (b) a decision procedure for linear
  integer arithmetic (Presburger-lite: Omega/Cooper, or a simplex + branch for
  the common linear cases), and (c) a Nelson–Oppen or DPLL(T)-style combination.
  A *decidable, from-scratch* prover is itself an excellent chapter and keeps the
  "silicon to semantics, build it yourself" arc intact — no external binary.
- **Escape hatch: shell out to Z3 (SMT-LIB)**. Fast to stand up, industrial
  strength — but an external dependency that breaks self-containment and the
  Pico/RISC-V story. Fine for an early prototype behind a flag; not the resting
  state.

**Affine × refinements — a real (and novel) wrinkle.** Refinements name values;
affine values may be named at most once. Predicates that mention an affine
binding must not count as a *use* that consumes it (refinements are erased at
runtime and should be use-neutral). The interaction of linear/affine typing with
refinement typing is under-explored in the literature — a first-class finding
opportunity for the book, not just an implementation detail. Settle it early.

---

## 3. What we are adding (surface + pipeline)

| Piece | Where | Role |
|---|---|---|
| Refinement syntax `{v:b\|p}`, contracts | lexer/parser | annotations on binders, params, returns |
| Predicate AST + well-formedness | new `refine`/`pred` module | the decidable predicate language |
| Measures | `type` decls / attributes | lift structural facts (`len`, `elems`, ordering) into the logic |
| Refinement environment + VC generation | after HM in `infer` | turn subtyping obligations into entailment queries |
| Decision procedure (QF-UFLIA) | new `solver` module | congruence closure + linear-int arith + combination |
| Soundness proof (V3) | `formal/proof/` (lcore) | subtyping ⇒ semantic implication |
| Dependent elaboration (V-deep) | ch12 `bridge/` + lcore | terms → MLTT with proof terms |

Prototype the checker + solver in **Python first** — in `08/src/`, the fork of the
oracle this axis owns (§0.1: `07/src` is frozen and is never edited), then — if/when it
matters — port to Lark the same way the compiler was self-hosted, checking the port
against `08/` exactly as `self/` checks against `07/`. Refinement *checking*
is a pure `AST × Env → obligations` transform, so it sits comfortably in Lark's
pure/affine substrate, exactly like the lexer/parser/typechecker.

---

## 4. Milestone ladder

### V1 — Refinement checker (annotated, checking-only) — OK **COMPLETE 2026-07-13**
1. OK Surface syntax + parse for `{ v : b | p }` and function contracts; predicate
   AST (linear arith, comparisons, `&&`/`||`/`not`, UF application, known vars).
   — `tree.TRefine`, `parser._parse_refine_type`, `pred.py`. The lexer needed *no*
   change (`{`, `}`, `|` were already tokens), and LL(1) survives: `{` begins no
   other type, and a predicate is an expression, whose grammar has no `|`, so the
   predicate parse stops at the closing brace on its own.
2. OK Refinement environment threaded alongside the HM env; VC generation at every
   implicit subtyping point (application, return, `let`, `if` path conditions).
   — `refine.py`: bidirectional `synth`/`check`, subtyping *is* entailment, `Env` is
   immutable so a path condition cannot leak out of its branch, function contracts
   are dependent (an argument's obligation is checked with the earlier arguments
   substituted in, which is what lets `i < len(xs)` refer to the `xs` just passed).
3. OK Decision procedure v0 — and the Z3 escape hatch **was not needed and was not
   built**. `solver.py` is from scratch: congruence closure (union-find + signature
   saturation), the **Omega test** (equality elimination incl. the symmetric-modulus
   trick, then Fourier–Motzkin with real shadow, dark shadow and **splinters** — the
   splinters are what make it a *decision* procedure over ℤ rather than over ℚ),
   Nelson–Oppen in the small between the two, all under a DPLL(T) boolean search.
   Validated against brute force on 4000 random systems, plus two purpose-built
   grey-region systems that only splintering can settle, kept as permanent rows in
   the self-check so the completeness path is never dead code.
4. OK **Validation:** [`prove/`](./prove/) — 5 safe/unsafe pairs (bounds,
   div-by-zero, non-negativity, slice totality, a user-defined `size`), 3 files
   carrying the affine finding, and an erasure file that is *checked and then run*.
   Expected verdict pinned per file in `08/tests/prove_difftest.py`, as a count:
   an obligation that quietly disappears is as suspicious as one that starts failing.
   **15 ok / 0 fail**, and `conservative` still **90/0/0** — so refinements are a
   conservative extension of Lark, demonstrated rather than asserted.

**Two findings from V1** (both §7 questions, both now answered):

- **The affine × refinement rule.** *Naming an affine binding in a predicate is a
  MENTION, not a USE; predicates are use-neutral.* It holds **by construction** —
  refinements erase in `syntype_to_mono` before inference walks them, so a predicate
  cannot increment a use count — and it is **sound because affinity restricts use,
  not truth**: Lark is pure, so consuming a value *moves* it rather than mutating
  it, and a fact proved about an affine binding stays true for its whole scope. In a
  language with mutation the rule would be unsound. The permission is paid for by
  purity and nothing else.
- **The predicate is free; the guard that establishes it is not.** `if size(b) > 0
  then take(b, 0)` *evaluates* `b` and then passes it on — two uses — so the affine
  checker rejects it. The borrow idiom that fixes the affine error (`size_of(b) :
  (Int, Buf)`) typechecks and *still* cannot be proved, because V1 has no refined
  tuple components. Affine and refinement are individually fine and **jointly
  blocked for non-Copy types** — which makes **refined products a V2 requirement
  derived rather than guessed.** (`prove/07_affine_guard.lark`, `07_affine_borrow.lark`.)

**And one thing V1 knows that it strictly should not have to:** a length is
non-negative (`refine.NONNEG_UF`, instantiated on the terms an obligation mentions,
so the fragment stays quantifier-free). Without it, `string_slice(s, 0,
string_length(s))` — slicing the whole of a string, which cannot fail — is
unprovable, because an uninterpreted symbol may return −1 for all the logic knows.
It is a one-symbol stand-in for what V2 turns into a real measure signature.
*(Paid at **V2.3**: `NONNEG_UF` is gone, a measure proves its own result refinement by
induction, and the only symbol still believed on faith is `string_length` — declared, named,
and alone, because String is primitive and has no arms to induct on.)*

### V1′ — Hardening — OK **COMPLETE 2026-07-14**

Feature-complete and green is not the same as robust. Two harnesses were added that
do not ask "is the answer right" but "does it survive", and they found three defects
that the pinned suites could not have.

5. OK **The corpus sweep** — `08/tests/robust_sweep.py`, `make -C 08 robust`. Every one
   of the 45 files of 07's real corpus through the refinement checker, in-process, with
   its verdict pinned. **45 ok / 0 fail / 0 crash.** A crash is never folded into a
   verdict: "cannot prove" and "the checker fell over" must not be the same output.
   It found that `TraitBoundError`, `LexError` and `UnifyError` escaped the CLI as raw
   Python tracebacks (fixed: `refine.FRONTEND_ERRORS` / `REFINE_ERRORS`). It also found
   two **true positives in Lark's own code** — `Div(a, b) => eval(a) / eval(b)` in
   `07/samples/05_expr.lark` and `09_parser.lark` is a latent division by zero that has
   been running for the whole project.
6. OK **The solver fuzzer** — `08/tests/solver_fuzz.py`, `make -C 08 fuzz`. Random
   QF-UFLIA formulas decided twice: once by `solver.py`, once by brute force over the box
   `[-3, 3]` (only the occurring symbols; assignments violating UF functional consistency
   discarded). **3000 cases, seed 7: 2556 agreed, 135 SAT with no model in the box, 309
   too big to brute-force, 0 unsound.** Only the *fatal* direction fails the run — a
   contradiction that isn't there, or a proof with a counterexample. SAT-with-no-witness
   is counted and never failed: Omega is exact over ℤ, and a small box is not.

**The finding: the solver could hang, and the hang was a boolean/arithmetic seam.**
`Theory.consistent` asserts that distinct integer literals are distinct (`3 ≠ 4`), and
`_lia` decides `a ≠ b` by splitting it into `a < b` or `a > b` — which costs 2^k. So a
formula merely *mentioning* seven constants arrived with 21 disequalities and asked for
2²¹ calls to Omega (the profile: 1,035,682 calls to the split, 517,825 to `omega`). Not
a wrong answer — *no* answer, which for a checker is worse. Fixed twice over: ground
disequalities are settled by inspection and never reach the split, and the split is
fenced by `MAX_DISEQ` and `MAX_SPLITS`.

**And the rule the fence taught: a budget must give up in the sound direction.** Every
`except Budget` in `solver.py` resolves towards *consistent* — "I found no contradiction"
— which makes `satisfiable` true, `valid` false, and `refine.py` say **cannot prove**. An
exhausted budget can cost a proof that was deserved; it can never manufacture one that
was not. Verified on a contradiction hidden behind an exhausted split: the solver declines
to prove the goal *even though it follows ex falso*. It surrenders capability, not
soundness. (This also fixed a quieter bug: exhaustion used to raise `PredError`, so a
resource limit was reported to the user as if their *program* were malformed.)

Every change here is **output-neutral** — drift, conservative, solver and prove are
byte-for-byte where V1 left them.

### V2 — Measures + data-structure invariants — OK **HEADLINE REACHED 2026-07-16 (boundary #3 crossed; V2.5/V2.6 below not picked up)**

**The goal:** lift recursive structure into the logic (`len`, `sorted`, `bst`) so the
solver stops being blind to what a function *computes*, and re-verify Lark's own samples
with invariants — the corpus proves itself *correct*, not merely *safe*.

**The one fact that shapes the whole milestone, and it was checked before the ladder was
written:** `self.globals` already holds every function's contract, and `_base_env` seeds
from it, so inside `_check_fn` a function's own name is in scope **with its contract**
(`08/src/refine.py`, `_base_env` / `_check_fn`). A recursive call is therefore checked
*against* the contract and may *assume* it — **induction on programs is already there, for
free.** V2 is, in essence, the same move applied to *measures*.

#### The ladder

**V2.0 — Refined products — OK COMPLETE 2026-07-14.** *First, not last.* This is the
requirement V1's finding (b) **derived** rather than guessed, it is independent of measures,
and it unblocks everything after it: `_bind_pattern` sent tuple binders through `infer_pat`,
which can only return fresh type variables at sort `OTHER`, so no VC could see through
`match f(x) with | (a,b) =>`.

What shipped, all of it in `08/src/refine.py` — **the parser needed no change at all**
(`_parse_atom_type` already parses tuple elements with `_parse_type`, and `{` already begins
an atom type, so `({v:Int | …}, {v:Buf | …})` parsed on the first try):
- `RTuple`, with **positional** components. Not dependent, and that is a decision rather than
  a shortcut: a component's predicate may mention any binder in scope *outside* the tuple —
  the argument it was computed from — but not a sibling, because the surface gives siblings no
  names to mention. Nothing in Lark wants that: a product's components are computed from a
  common input, not from each other. Inventing surface syntax for a use that does not exist is
  how a language accretes.
- **Refinements on non-Int/Bool bases** (`{v : Buf | size(v) == size(b)}`), which the borrow
  idiom turns out to require and which V1 rejected outright. This looks like a bigger extension
  than it is: the value binder is sorted OTHER, so `_int_term`'s guard keeps it out of
  arithmetic and ordering, and the only operations left are the two the solver already decides
  at *any* sort — equality, and application of an uninterpreted symbol. **Congruence closure
  does not care what a `Buf` is.** No new theory, no new sort machinery; just permission to
  name a value we cannot open.
- synth/check/subtype for products (covariant, componentwise — a product is not a function, so
  there is no contravariance to get backwards), `subst_rtype`, `_rtype_of_syn` for `TTuple`, and
  `_bind_pattern` taking the scrutinee's **already-synthesised** `RType` instead of re-inferring
  it. The fix was not to infer harder but to **stop inferring**.

**THE FINDING, AND IT IS A CORRECTION TO THIS PLAN'S OWN DoD (which said the borrow file would
flip to *proved*).** It went **half** way, and the half it did not go is the interesting one.
`prove/07_affine_borrow.lark` is now **1 of 3 proved**:
- The **consumer** is discharged. `size_of`'s contract promises `n == size(b)` and
  `size(b2) == size(b)`; the tuple pattern delivers both facts into the arm; the guard adds
  `n > 0`; `take(b2, 0)`'s precondition follows. That is the obligation the file was written
  for, and it is exactly what refined products were supposed to buy. (Verified as *not*
  vacuous: weaken the guard to `n >= 0` and the obligation fails.)
- The **producer** cannot be, and no amount of product refinement will help. Checking
  `size_of`'s own body needs `size(Buf(n)) == n` — that taking a buffer apart and putting it
  back together preserves its size. `size` is an uninterpreted symbol and `Buf(n)` an opaque
  constructor application, so the two goals left are the two halves of **one missing measure
  equation**.

> **Refined products let a fact TRAVEL; only a measure can CREATE one.** That sentence is the
> whole of why V2.0 could not have been the last rung, and it was found by building it rather
> than by reasoning about it.

- **Done (revised):** `prove/09_product_{safe,unsafe}.lark` — a pair whose components carry
  facts about a builtin that has a *real* precondition (`string_slice`), so V2.0 gets a green
  end-to-end case needing **no** measure. The mutant's right edge is one past the end and its
  helper declares that honestly: no function is wrong, the *interface* between two of them is.
  `prove` **15 → 17 ok / 0 fail**; `07_affine_borrow` re-pinned `(unproved 1,1) → (unproved
  2,3)`, and it goes to `("proved", 3)` the day V2.2 lands. Everything else **output-neutral**:
  drift 22/3/3, conservative **90/0/0**, solver **16/0** byte-for-byte, `harden` robust 45/0/0
  + fuzz 3000 / 0 unsound.

**V2.1 — Measure declarations: surface + well-formedness — OK COMPLETE 2026-07-14.** A new
top-level `MeasureDecl` — **not** an attribute on `fn`. A measure is *ghost* (it erases, as a
refinement does), it must be *structural* and *total*, and its body must live in the
*predicate fragment*: three restrictions an ordinary `fn` does not carry. Were measures just
functions, we would owe the reader an account of why some `fn`s may appear in a predicate and
others may not — and there is not a good one.
- Well-formedness (`refine.Refiner._elab_measure`): exactly one arm per constructor
  (exhaustive, non-overlapping); arm bodies in-fragment, translated **strictly**; **recursive
  calls only on direct fields of the matched constructor**; result sort `Int` or `Bool`; and
  one added on contact — **the name must belong to nothing else in the logic** (a measure
  sharing a name with an `fn` is one symbol with two definitions, and the `fn`'s body was
  never checked against the equations).
- **Done:** `prove` **17 → 25 ok / 0 fail** — `10_measure_len.lark` (checked *and run*) + 7
  negatives (`11_measure_*.lark`), each a *malformed*-class error, not an *unproved* one.
  Drift **22/3/3 unchanged** (`tree.py`, `parser.py` already EXTENDED, and their reasons grew);
  `conservative` **90/0/0**; `solver` **16/0** byte-for-byte; `harden` robust 45/0/0 + fuzz
  3000/0 unsound. **The V1′ budget did not bite** — no equation reaches the solver until V2.2,
  which is precisely when to re-check it.

**THE V2.1 FINDINGS — two, and both are about where a thing is *kept* rather than what it
does.**
1. **Erasure is by CONSTRUCTION, so there is no erasure.** A `MeasureDecl` lives in
   `Program.measures` and **never in `Program.decls`** — the two halves of a program are split
   at the parser door and never rejoined. `infer.py` and the CEK machine therefore cannot see a
   measure; there is no ghost-elimination pass because there is nothing to eliminate. The
   corollary is free and is the nicer half: **calling a measure from real code is an
   unbound-name error from HM**, not a rule anybody wrote. `10_measure_len.lark` is checked and
   then *run* to say so out loud.
2. **The declaration is what lets the name into a contract AT ALL — which is not what the plan
   thought it was buying.** Under V1, `len(v) > 0` in a contract was not an unproved obligation,
   it was a *refinement error*: `len` had no declaration, so it had no sort, so `_int_term`'s
   guard threw it out of the ordering — correctly, since an unsorted symbol has no business in
   an arithmetic comparison. The only names a V1 predicate could apply were **the program's own
   functions**, which is a strange rule to have to say out loud, and saying it is what a
   measure declaration removes. So V2.1's win is smaller than "measures work" and larger than
   "it parses": the word now *means* something to the logic (an Int-sorted symbol with one
   equation per constructor), and V2.2 is only the last step of showing those equations to the
   solver.

Also settled by building it: **`measure` is a CONTEXTUAL keyword** — a declaration could never
begin with a bare `NAME`, so the only token stream newly accepted is one that used to be a
syntax error, and the frozen oracle's lexer never learns a word that only the type layer cares
about. `lexer.py` stays byte-identical, which is why drift is still 22/3/3.

**V2.2 — Measures into the logic, with NO solver change — OK COMPLETE 2026-07-14.** The
equations reach the solver through two hooks and nothing else:
- **Building** — a constructor application gets a refined type: `Cons(x, xs)` synthesises
  `{v | v == Cons(x, xs)}` (`Refiner._synth_con`).
- **Destructing** — a constructor pattern arm *assumes* `xs == Cons(x, rest)` (`_walk_match`,
  the hook its own docstring pre-registered: "Constructor patterns say nothing until measures
  exist (V2)").

Together these instantiate each equation **at the terms the program mentions** and nowhere
else — quantifier-free: no axiom schema, no triggers, no e-matching. The day we reach for a
trigger we have left the decidable fragment, and §5's guardrail says stop.
- OK **Done:** `prove/07_affine_borrow.lark` **1 of 3 → 3 of 3 proved**, pinned `("proved", 3)`;
  `10_measure_len.lark` **unproved → `("proved", 1)`** with no change to the file; new pair
  `12_measure_safe` (4 proved, *and runs*) / `12_measure_unsafe` (3 of 4 unproved — one lie per
  hook). `prove` **25 → 27 ok / 0 fail**. Everything else unmoved: drift 22/3/3/0, conservative
  90/0/0, robust 45/0/0, fuzz 3000/0 unsound.
- OK **The claim held literally.** `solver.py` is **byte-for-byte unchanged** (solver 16/0) —
  and so are `pred.py`, `parser.py`, `lexer.py`, `tree.py`, `infer.py`. **The entire rung is
  inside `refine.py`.** `11_measure_nonstructural.lark` is still rejected at *declaration*
  time, before a single VC is built.

**THE V2.2 FINDINGS — three.**

1. **A constructor needed no theory. It needed a NAME.** The move the rung rests on is that
   `Cons(x, xs)` becomes the uninterpreted application `Cons(x, xs)` — and the solver already
   decides equality and congruence at any sort, so this costs nothing. Congruence gives exactly
   what a constructor deserves: *equal fields build equal values*. Injectivity and disjointness
   are **not** asserted, and nothing needs them — an axiom nobody needs is an axiom nobody has
   checked. And note what the destructing hook does *not* say: it does not assume
   `len(xs) == 1 + len(rest)`, it says the humbler *what the scrutinee is*, and the equation
   follows because the term is now in the hypotheses. **One mechanism (`measure_axioms`, a walk
   over the obligation's own terms), fed from two places** — rather than two mechanisms that
   have to agree. The instantiation **closes in a single pass**, and the reason is worth saying:
   the subterms of a constructor term are constructor terms, and an arm may only recurse on a
   *field*. **V2.1's structural check, written to keep the axioms consistent, turns out to be
   what makes them terminate.** The negative half of a constructor pattern is left on the table
   deliberately (it would need disjointness) — the same shape as V1's *the mention is free, the
   guard is not.*

2. **The time bomb was DETONATED, not asserted.** `11_measure_nonstructural.lark` was written at
   V2.1 against this rung. Disarm V2.1's structural check and nothing else, and V2.2 instantiates
   `bad(xs) == 1 + bad(xs)` at the `Cons` arm's own term, derives the inconsistency, and
   **verifies that `absurd` returns a negative number when it plainly returns `0`** — one false
   proof, ex falso, *measured*. The `Nil` arm stays honest (its equation is consistent), so the
   poison reaches exactly the terms it is instantiated at. **The structural check is
   load-bearing for V2.2, not good manners** — and that is now a fact on the record rather than
   an argument in a comment.

3. **A latent bug of V1's, found because V2.2 needed the thing it broke.** `_bind_pattern` built
   a **new `ty.Fresh()` on every call**, whose counter restarts at 0 and collides with the type
   variables already inside the schemes; `instantiate` then mapped a scheme's `α₀` to a "fresh"
   `α₀`, `ty.apply` chased `α₀ ↦ α₀` to a `RecursionError` — and a bare `except Exception`
   swallowed it and **bound nothing.** So a constructor pattern over a *polymorphic* ADT gave its
   binders no types at all, silently, in V1, V2.0 **and** V2.1. A *monomorphic* one (`| Buf(n) =>`)
   was always fine, because `instantiate` returns early when there is nothing to quantify — which
   is precisely why the `Buf`-shaped suite never noticed. Fixed: one seeded supply per `Refiner`,
   and the `except` narrowed to `FRONTEND_ERRORS`. **V1′'s rule again, one turn worse: a crash is
   never a verdict — and this one was a crash reported as a *proof attempt*.** Its sibling: an
   ADT-typed binder was `ROpaque`, so `| Cons(_, r) => r` could not *selfify* `r` and the fact
   never left the function. `rtype_of_mono` now knows the program's ADTs. **Refined products let
   a fact travel; a measure creates one; a NAME is what carries it out through a return.**

**V2.2′ — SOUNDNESS: the four false proofs — OK COMPLETE 2026-07-14.** Not a planned rung.
Asked "is anything else unsound?" after V2.2 landed, went looking, and found that the
answer was yes — four times. **Every one was reported as `ok: N obligation(s) proved`, and
every one then divided by zero when run.** They are the false proofs this project found BY HAND
(V2.2‴ adds three more, found by a machine that did not know where to look). They are the ones it has
produced, and they come in two families of two: the checker **believing something it had not
established** (the Float, the untranslatable guard), and the checker **speaking about a name
that no longer meant what it thought** (the shadowed symbol, the captured axiom).
- OK **A FLOAT MAY NOT ENTER THE LOGIC.** `x == x` is **valid** in the logic — equality is an
  equivalence relation and congruence closure makes it reflexive, as it must — and **false at
  run time when `x` is NaN**, which `0.0 / 0.0` and `float_sqrt(-1.0)` both produce
  (`cek.py:304`). So the else branch assumed `not (x == x)`, found it contradictory, and was
  proved **vacuously**. The other half needs no NaN: `0.0 == -0.0` is **true** at run time and
  they are **different values**, so congruence gives `f(0.0) == f(-0.0)` for an `f` that can
  tell them apart. **Reflexivity fails one way and substitutivity the other — and those two are
  the whole of what sort `OTHER` hands out.** `OTHER` means *named but not opened*, which is
  right for a String, a Buf, a List, and **too much for a Float**. Fix: `refine.FLOAT`, a sort
  at which **no term is ever built** — not opaque, *unspeakable* — guarded in `term_opt`, so a
  constructor with a Float field is unnameable too (its argument was) and a predicate over
  Floats is a refinement *error* rather than a silent lie. Note it took setting the sort on
  **both** roads into a binder's type: `rtype_of_mono` (inferred) *and* `_rtype_of_syn`
  (annotated) — the first fix looked like it worked and did not, because the probe's parameter
  was annotated.
- OK **"I COULD NOT TRANSLATE THIS" IS NOT "THIS IS TRUE."** The deeper bug, found while fixing
  the first, and **there is not a Float in it**. Both `if` sites read `cf = formula_opt(c, env)
  or Top()`, and `formula_opt` returns `None` for *cannot express this*. That `or Top()` made it
  **true**, so the else branch assumed `Not(Top())` = **FALSE** and every obligation inside it
  followed. The guard that did it is `x * y > 0` — merely **non-linear**, the everyday way out
  of a linear fragment. Fix: `refine._branch` — a condition the logic cannot express constrains
  **nothing**, so *neither* branch learns anything, and the negation is never taken.
- OK **A UF SYMBOL IS A GLOBAL FUNCTION, AND ONLY THAT.** The logic names its symbols by their
  **source name**, and source names **shadow**. A contract written against the program's own
  `size` (`{v : Int | v != size(b)}` — the `05_buf` idiom, the oldest thing in the suite) is
  discharged at a call site by a guard that says `0 != size(b)` — and if a `let size = fn(x) =>
  1` is in scope there, that guard is about a **different function**. Both become the symbol
  `size`, and congruence closure did what congruence closure does: it identified them. The
  obligation fell out of the guard, and it was false. Fix: `term_opt` refuses to build `App(f,
  …)` when `f` is in `env.vsorts` — which holds the *value variables* (params, lets, match
  binders) and never a global function. **A locally bound function is unspeakable**; it never had
  a contract to read off or an equation to instantiate, so all it ever had was congruence, and
  congruence was the bug.
- OK **AN AXIOM IS ABOUT A FUNCTION, NOT ABOUT A NAME.** The same capture at longer range, and
  **worse, because nobody has to call it for it to fire**. V1's one fact about a UF symbol is
  `refine.NONNEG_UF` = `{string_length}` — asserted of every `string_length(t)` a VC mentions,
  and *true of the primitive*. A program may declare `fn string_length(s : String) : Int = 0 - 4`,
  and the declaration overrides the builtin everywhere — including at run time. The axiom was
  then a lie about the program's own function, and `div(100, string_length(s) + 4)` was **proved**
  and divided by zero. Fix: `Refiner` intersects `NONNEG_UF` with the names the program **leaves
  alone**, and hands each VC the result. This one was temporary in the good sense, and the promise
  was kept: **V2.3 deleted `NONNEG_UF` altogether** — an axiom that has become a theorem cannot be
  captured. (Its successor, `PRIMITIVE_AXIOMS`, is still withheld from a rebound name: `string_length`
  has no arms, so it is believed rather than proved, and a belief is exactly the thing that can be
  told a lie.)
- **THE RULE, and it is V1′'s, moved one level up.** V1′ made every exhausted budget *inside
  `solver.py`* resolve toward "cannot prove", never toward a proof. The same now binds the
  checker that *builds* the obligations: **where it cannot speak it must say NOTHING — never
  `true`, never a negation, and never a claim about a name it does not own.** A verifier's
  silence is cheap; its confidence is not.
- OK **Done:** `prove` **27 → 35 ok / 0 fail** — four new pairs, `13_float_{safe,unsafe}`,
  `14_guard_{safe,unsafe}`, `15_shadow_{safe,unsafe}` and `16_axiom_{safe,unsafe}`, every mutant
  pinned as `unproved` and **every safe file RUN**, which is what shows the fix cost nothing a
  program was entitled to (same guard, same obligation, still proved, still prints its answer).
  Everything else unmoved: drift 22/3/3/0, conservative 90/0/0, solver **16/0 and still
  byte-identical**, robust 45/0/0 **with every verdict where it was**, fuzz 3000/0. That last row
  is the tell: **the proofs the fix deleted were never proofs.**

**V2.2″ — `impl` BODIES ARE CHECKED OK (2026-07-14).** *The hole the soundness hunt found and
left open, closed before V2.3 as planned. Entirely inside `refine.py`; `solver.py` untouched
again.*

- OK **THE BUG.** `refine.py` imported `ImplDecl` and never matched it, so **an impl body was
  never walked** — for V1, V1′, V2.0, V2.1 and V2.2. It was not a false proof, and the reason is
  worth keeping: the refinement on a **trait method's signature** was *dropped* rather than
  trusted (the scheme comes from `_register_trait_decl`, and `_rtype_of_mono` erases the
  predicate), so a lying impl could not discharge a caller's goal. **Sound by luck, and by luck
  in only one direction.** What it was instead is the failure mode next door: put `n / 0` inside
  an impl body, with no caller reading the trait, and the checker prints **`ok: 2 obligation(s)
  proved`, exit 0**. The division is never *seen*. **Silent under-verification is not a weak
  answer, it is a wrong report** — and a count that omits the obligation is the one thing a
  verifier's output may never be.
- OK **THE FIX IS THE TWO HALVES OF ONE DECISION.** An `ImplMethod` is checked exactly as an `fn`
  is (`_check_impl`), against the contract in the **trait** (`_impl_rtype`): the refinements come
  from the signature the trait declares, the HM types from the `TFnDecl` `infer.py` already built
  for that same body, and the parameter *names* from the impl. **And because every impl is now
  held to the signature, a CALLER may finally read it** — `_rtype_of_sig` installs the trait's
  refinement as the method's global contract. Those two are not separable: **a contract the
  callers trust and nobody checks is exactly the false proof V2.2′ was about.** So the reading is
  earned by the checking, and not one rung before.
- OK **THE TRAIT VARIABLE NEEDS NO SUBSTITUTION, AND THAT IS A RESULT, NOT AN OVERSIGHT.** The
  plan said "with the impl's type substituted for the trait variable". It is not needed, because
  a refinement can only sit on a base **the logic can name**, and the trait variable is not one —
  `_rtype_of_syn` rejects `{v : a | …}` outright. So a signature contributes **predicates and
  nothing about the type**, and the types come from HM, which checked them at the concrete type
  already. Where the trait is not declared in this file (`Copy`, `Show`), there is no signature to
  read and every part falls back to its HM type: **a trivial contract is still a contract, and the
  body is walked all the same.** Nothing is skipped, ever — which is the whole point of the rung.
- OK **A TRAIT METHOD IS A NAME THE PROGRAM OWNS.** V2.2′(d)'s lesson, applied one place further:
  `NONNEG_UF` is now also withheld from any name a **trait** declares, not just an `fn` or a `let`.
  A trait method called `string_length` is the program's, and the primitive's axiom is not about
  it.
- OK **Done:** `prove` **35 → 37 ok / 0 fail** — `17_impl_{safe,unsafe}`, the safe file **RUN**.
  **The counts are the finding.** Under the old checker *both* halves of the pair had exactly
  **one** obligation — `share`'s division, out in ordinary code — and both **failed** it, because
  the contract that discharges it had been thrown away. Now there are **four**, and the safe file
  proves all four while the mutant is caught **twice**: an arm returning `0` where the trait
  promised `{v : Int | v > 0}`, and a division inside a body that nothing else reads. *Too weak
  outside, blind inside — one bug, and the count says so.* Everything else unmoved: drift 22/3/3/0,
  conservative 90/0/0, solver 16/0, robust 45/0/0 **with every verdict on 07's corpus exactly where
  it was** (its impl bodies contain no divisions, so the fix adds obligations only where there is
  something to prove), fuzz 3000/0.
- **What it does not do.** A call's postcondition still reaches the logic **through a name** — `let
  w = weight(c) in total / w` proves, `total / weight(c)` does not, because the division's VC
  assumes `env.facts` and a bare subexpression's synthesised refinement is not one. The weak
  direction, and V2.2's own rule one rung down (*a NAME is what carries a fact out through a
  return*). Materialising a synthesised refinement at its point of use is a capability rung, not a
  soundness one.
- **What is left, and deliberately.** Two known gaps, neither a false proof *against the CEK
  machine*, both worth writing down. **(1) The logic is ℤ; the RV32 and C backends are 32-bit.**
  A refinement proved over unbounded integers may not survive `i32` wraparound (`19_intoverflow`
  is already a known optimizer xfail). The reference semantics is Python's bignum, so the checker
  is sound *for the machine it verifies against* — but a `--target rv32` claim would need either
  wrapping arithmetic in the logic or an overflow obligation per `+`/`*`. **(2) Contracts are
  partial correctness.** A non-terminating function may be given any postcondition and the
  checker will believe it (it assumes the declared result type when checking a recursive body —
  as it must). Nothing bad *happens*, because a program that never returns never reaches the
  division; but "proved" here means "if it terminates". Termination measures are the standard
  cure and are not on the plan. **(3, added V2.4c step 4) A nested measure fires only at concrete
  subfields, so its DESTRUCTING direction is one-sided.** `bst(v)` can be PROVED of a tree the
  program builds (the nested guards fire at the literal children), but a consumer given an OPAQUE
  `{v : Tree | bst(v)}` learns nothing usable from it — over `Node(l, v, r)` with `l`/`r`
  variables the guards decline (correctly: to fire them would need a quantifier over the inner
  fields). Reading order back out (`23_boolmeasure`'s destructing elegance, for a bst) needs
  `minv`/`maxv` to carry declared LOWER/UPPER-BOUND invariants proved by induction — a separate,
  larger capability rung, not a soundness gap. This is the honest edge of fire-at-concrete-subfields.

**V2.2‴ — THE ADVERSARY, and the three false proofs it found OK (2026-07-14).** *Not a planned
rung either. The four false proofs of V2.2′ were found by hand, by going looking. This rung is
what happened when we stopped looking by hand.* Entirely inside `refine.py`; `solver.py`
untouched again.

**The tool.** `08/tests/adversary.py` — random **programs**, against the checker's own promise:
*if it says `ok`, the program does not crash.* Generate, check with `refine.check_program`, and
then **RUN** on the CEK machine the ones it proved. A crash after a proof is a false proof, and
the program that caused it is printed. (A second oracle checks erasure: strip the refinements
textually, run both, demand identical output.) The generator is aimed at what has drawn blood —
non-linear divisors, unreadable guards, Floats, local lambdas, shadowed `string_length`, impls
with bodies — and, since **V2.3**, **measures**: a `List` ADT, a measure with a randomly chosen
(lie-weighted) declared result, a function whose contract equates it, and a divisor taken from the
result *through a name*. `make -C 08 adversary`; `make harden` runs it.

`fuzz` tests the **solver**, and the solver has never been the problem: every bug this project
has had is one level up, in the checker that **builds** the obligations. The adversary is the
witness for that level, and it should have existed four false proofs ago.

**THE FINDINGS — three, and the third is the worst hole this fork has had.**

1. **A GOAL it could not read was not asked** (`18_divisor`). `100 / (x * y)` — merely
   **non-linear**, so `term_opt` returned `None` — raised **no obligation at all**. Same for
   `100 / h(x)` where `h` is a local lambda (unspeakable since V2.2′(c), so the divisor's type
   came back opaque and the site declined to ask). Both printed `ok`, exit 0, then divided by
   zero. **This is V2.2′(b)'s own rule at the opposite polarity, which is exactly why it was so
   easy to get wrong:**

   > a **hypothesis** it cannot read must be **DROPPED**.
   > a **goal** it cannot read must be **ASKED ANYWAY**, and go unproved.
   >
   > *Silence about what you may assume is modesty. Silence about what you must prove is a lie.*

   The asking condition is now HM's — this is an integer division, so it owes a proof — and the
   only excuse is positively knowing the division is a **Float's**. A divisor it cannot name gets
   a **skolem** that inherits the divisor's own contract, exactly as an argument's does: so
   `100 / nz(x * y)` (a contract on an unnameable divisor) still proves, and `$k /= 0` with
   nothing said about `$k` is unprovable, which is the truth.

2. **A Float literal had no sort** (`19_floatlit`). V2.2′(a) paved the roads it could see — a
   declared parameter, a declared return — and missed the one nobody has to declare. `0.0`
   synthesised to an rtype with no sort, read as `OTHER`: an ordinary opaque value, and an opaque
   value may be **equated**. So `nan == nan` was believed, its negation was UNSAT, the else branch
   became dead code *in the logic* — and it is the branch NaN actually takes. One missing sort,
   two bugs pointing opposite ways: a falsehood **believed**, and (with the sort lost through
   arithmetic) an obligation **invented**, because `0.0 / 0.0` looked like an *integer* division.
   *Unspeakability is not a property of a literal; it is a property of every value a Float can
   reach, so the sort must survive the operations.*

3. **A division in a Bool position was never even visited** (`20_condition`). The distinction the
   code had stopped making:

   > `formula_opt` and `term_opt` **TRANSLATE**. `synth` **WALKS**.
   > Only the walk raises obligations. Translation is pure — it asks for nothing.

   Four sites translated a sub-expression **instead of** walking it: an `if`'s condition, a
   comparison, a `not`, a unary minus. Every division inside any of them **vanished**. The unary
   minus is the sharpest: it walked its operand only when `term_opt` *failed* — so the better the
   checker understood an expression, the less of it it checked. `if (x / y) < x then …` reported
   **`ok: 0 obligation(s) proved`**, exit 0, and divided by zero. *Zero.* The rule, which is the
   impl hole's rule one level down: **every sub-expression is walked exactly once, whether or not
   it is also translated; what the checker declines to UNDERSTAND it must still LOOK AT.**

   **And this was never a corner case.** 07's own primes sieve has `fn divides(d, n) = n / d * d
   == n` — a function whose entire body is a comparison — and for the whole life of this fork it
   reported **zero obligations**. A trial-division sieve, and the checker had never once looked at
   the division. That verdict has moved in `robust_sweep.py` (to `unproved`, honestly: `d : Int`
   does not promise `d /= 0`, and 07 is frozen), **and the move is the finding.**

- OK **THE LANGUAGE MAY NOT GROW BEHIND THE CHECKER'S BACK.** `synth` ended in a silent
  `return ROpaque()`, so a `BinOp` whose operator it had never heard of would fall through it —
  no obligation, no error, `ok`, exit 0. That is the impl hole's shape exactly, and `%` is the one
  waiting to happen (the CEK already divides for it and traps on 0; only the *lexer* is keeping it
  out of the language). An unknown operator now **raises**, and says what it owes. `%` can
  therefore wait for a front-end rung instead of being rushed in here.
- **The cost: nothing.** Every `_safe` file proves, runs, and prints its answer; closing holes
  this large usually spends capability, and here there was none to spend — the "capability" was
  the absence of a question. drift 22/3/3/0, conservative 90/0/0, solver 16/0, fuzz 3000/0, prove
  **43/0** (three new pairs), robust 45/0/0 with exactly one verdict moved, and that one on
  purpose.
- **The generalisation, and it is now the fork's first rule.** *A checker's silence is a verdict,
  and a report must never let silence read as approval.* `ok: 0 obligation(s) proved` was sitting
  in that output the whole time, and it reads like success.

**V2.3 — The measure's own refinement, PROVED rather than assumed — OK COMPLETE 2026-07-14.**
*The rung with the finding in it, and the debt V1 wrote down in its own comment.* `refine.NONNEG_UF`
was a set literal asserting that a length is never negative — V1 conceded it "knows something it
strictly should not have to." A measure now **declares** it (`measure len(xs : List(Int)) : {v : Int
| v >= 0}`) and the checker **proves it by structural induction: one VC per constructor arm, with
the declared refinement assumed at each recursive occurrence as the induction hypothesis.** A finite
VC set; the existing solver discharges it unchanged. **The axiom became a theorem, and `NONNEG_UF`
is deleted.** All of it inside `refine.py`; `solver.py`, `pred.py`, `parser.py`, `lexer.py`,
`infer.py`, `tree.py` untouched.
- OK **Done-when, met.** `21_result_unsafe.lark` moves one character — `{v : Int | v > 0}` for `len`
  — and is **rejected**: 1 of 5 unproved, and at exactly the right place, the **`Nil` arm**, whose
  goal `len(Nil) > 0` sits beside its own equation `len(Nil) == 0`. The `Cons` arm still proves, from
  the IH. (*A false claim about a recursive definition is usually false at the base case.*) And it is
  a **detonation, not a style complaint**: admit the declaration and `total / len(xs)` is discharged,
  `ok`, exit 0 — then `main` passes `Nil` and the machine divides 100 by 0.
- OK **AN INDUCTION VC MAY NOT ASSUME WHAT IT IS PROVING.** `Refiner.run()` hands each VC the
  results table it may assert from, and for `ind=True` VCs that table is `prim_results` — *without*
  the measures' own declared refinements. Hand the `Nil` arm the axiom it is trying to prove and it
  discharges itself; the bogus declaration passes; the checker has proved a division by zero. This
  is the one line in the rung that is doing the actual work. **Assuming the conclusion is not a
  subtle bug — it is the entire difference between an induction and a lie.**
- OK **The axiom that is left is now a NAMED one.** `PRIMITIVE_AXIOMS` — one line, one entry,
  `string_length(s) >= 0` — for the one function whose body the checker cannot see (String is
  primitive; it has no arms to induct on). Still withheld from any name the program rebinds, which
  is `16_axiom`'s finding kept. The complete list of what this checker takes on faith is now
  *readable in one place*, which is the honest version of the same thing.
- OK **THE STATEMENT PROVED MUST BE THE STATEMENT ASSERTED.** Caught in my own audit, before any
  test: for a measure with **extra parameters** (`drop(xs, i)`), the induction goal was built as
  `drop(Nil())` — a term no program mentions — while `result_axioms` asserted the refinement at
  `drop(xs, i)`, the terms programs *do* mention. Sound by luck, not by construction. The extras now
  enter as **free variables**, so such a measure goes honestly **unproved** until V2.4 lets its
  equations fire, rather than proving a theorem about something else.
- OK **The induction is load-bearing, and measured to be.** Delete the `{v : Int | v >= 0}` from
  `21_result_safe` and `avg`'s division stops proving (1 of 3 unproved) — so the theorem is what
  buys the capability, and the capability is real: **a fact about an *opaque* list**, one never
  taken apart, which is the first universal claim this checker has been able to earn.
- OK **The adversary was aimed one step to the left, and had to be re-aimed.** With `_prove_measure`
  disarmed it came back *clean* — because it generated `x / size(xs)`, a bare call, whose
  postcondition never becomes a fact (V2.2″: *a fact travels through a NAME*), so it is unprovable
  whatever the declaration says. Generating `let m = size(xs) in x / m` instead, the disarmed checker
  produced a false proof on seed 11 within seconds. **A fuzzer that cannot express the bug does not
  report its absence — it reports its own blind spot**, and the only defence is to disarm the fix and
  make the machine find it.
- **The cost: nothing.** `prove` **43 → 45** (one new pair), everything else unmoved: drift 22/3/3/0,
  conservative 90/0/0, solver 16/0 byte-for-byte, robust 45/0/0 with every verdict where it was, fuzz
  3000/0 unsound, adversary clean on three seeds.
- **Left open, deliberately:** a measure's **termination** is still structural-by-syntax (V2.1's
  check), not proved by a well-founded order — which is what entitles the induction to exist at all,
  and is the honest place to say so.

**V2.4 — Bool-valued + parametrised measures → `sorted`, `bst` — OK COMPLETE 2026-07-16** (as
V2.4 foundation + V2.4b + V2.4c steps 1–5; one line each in the ledger at top, stories in `LOG.md`).
Original rung text follows. Measures
with extra `Int` parameters, structural in the first argument.
> OK **SETTLED 2026-07-14 — SET CHOSE min/max MEASURES.** No quantifier enters the logic; ghost
> parameters stay unbuilt unless V2.5's permutation forces the issue. The fork, for the record:
> To prove `insert`
> preserves BST-ness, the VC after building `Node(insert(left,x), v, right)` needs
> `all_lt(insert(left,x), v)` — a fact about *insert's result*, for an arbitrary bound `v`.
> Two ways to state it:
> - **Ghost parameters** — universally quantified scalar ghosts on contracts, instantiated at
>   call sites. Fully general; what the literature reaches for. Also a new binding form, a new
>   quantifier story, and **precisely the scope creep §7 warns about.**
> - **min/max measures** *(recommended)* — add total `minv`/`maxv` (defaulting on `Leaf`), state
>   the invariant as `bst(Node(l,v,r)) = bst(l) && bst(r) && (l == Leaf || maxv(l) < v) &&
>   (r == Leaf || v < minv(r))`, and give `insert` the contract
>   `minv(insert(t,x)) == min(minv(t), x)` — itself structural, hence provable by V2.3's
>   induction. **No quantifier is ever introduced.** It keeps V2 inside the fragment we can
>   already decide, and it makes ghost parameters a feature we deliberately *avoided needing*
>   rather than one we bolted on.

**V2.5 — mergesort — ⏸ NOT PICKED UP** (2026-07-16: V2 closed at the destructing bst with no rung
queued; sortedness would be assembly over V2.4's machinery, permutation stays the documented
stretch — reopen deliberately or not at all). Sortedness first; it follows from V2.4's machinery with a `head`-style
measure. **Permutation is the interesting one, and it is a stretch.** A permutation is
`∀x. count(a,x) == count(b,x)`, which *looks* quantified — but **a free variable in a QF
entailment goal already IS universal validity**, so `count(merge(a,b), x) == count(a,x) +
count(b,x)` is provable with `x` free and **no solver extension at all**. The catch is that
*stating* it in a contract needs a top-level ghost binder — the very feature V2.4 is trying not
to need. Worth writing down either way: it is a good page in ch16.

**V2.6 — regression + prose — ONGOING, never a discrete rung in practice** (suites extended with
every rung above; book prose = `book/` Part III, in progress). Extend `make -C 08 test`; update the drift EXTENDED/ADDED
tables; `08/README.md`, `prove/README.md`; mark V2 here with its findings; append to `LOG.md`.

**Deferred (unchanged from the original V2):** refinement *inference* — predicate abstraction
over a fixed qualifier set (the "Liquid" in Liquid Types). §7 already calls it V2-*optional*;
annotated checking delivers program proofs without it. It is not on this ladder.

#### Pre-registered hazards (§7-style — expect these)

- **Measure totality is a soundness side condition, and it is sharper than it looks.** A
  non-terminating *program* function is harmless: no result is returned, so its contract is
  vacuously kept — that is partial correctness, and **V1 already relies on it**. A
  non-terminating *measure* is fatal: its equations become an **inconsistent axiom set** and the
  checker will prove anything. **Termination is optional for a contract and mandatory for a
  measure.** So V2.1's structural check must be *enforced*, and there must be a fixture with
  teeth: a non-structural measure that, if admitted, proves `False`.
- **The V1′ budget rule will start biting.** Measures multiply UF terms, and UF terms multiply
  disequalities — exactly what `MAX_DISEQ`/`MAX_SPLITS` fence. Expect to re-tune, and re-run
  `make -C 08 harden` **per rung**, not once at the end. Every new give-up path must resolve
  towards *consistent* → "cannot prove" (V1′'s rule: a budget gives up in the sound direction).
- **Erasure.** Measures are ghost and must not exist at runtime. The check already exists:
  `conservative` 90/0/0, plus the `prove/` file that is checked *and then run*.
- **Instantiate, never quantify.** If an equation ever needs a trigger to fire, the fragment has
  been left behind (§5). That is a stop, not a workaround.

### H — Hardening the code that is — OK **COMPLETE 2026-07-14**

*Not a rung. A pass over what exists, before climbing further.*

Every hunt up to here asked whether the checker is **right**. This one asked whether it
**answers**. The two failures a verifier may not have are *a wrong answer* and *no answer*,
and only the first had a suite pointing at it.

7. OK **The torture harness** — `08/tests/torture.py`, `make -C 08 torture`, folded into
   `harden`. Fourteen hostile-but-legal programs, each in a subprocess on a wall clock:
   3 000 terms in one expression, a predicate that is a 300-way conjunction, a constructor
   term 400 deep, 1 200 nested lets, 40 disequalities, 30 disjunctions, a measure at the
   wrong arity, `{v : Float | v == v}`, a mutually recursive measure pair. **The only failing
   grade is no answer at all.** It opened at **5 failures of 15** and closes at **0 of 14**.

**The findings.**

- **Four raw `RecursionError`s.** The checker walks a program on the C stack, and Python's
  limit is 1 000. A program deeper than that *crashed* — out of `parser.py`, `infer.py`,
  `refine.py`. Now the walk runs on a thread with a real stack (`_with_big_stack`) and what
  is left over is classified as **`TooDeep`**: *a stated limit, not a stack trace.*
- **Every fence was LOCAL, and every caller loops.** V1′ fenced the splits, but `MAX_SPLITS`
  re-arms on each `_lia`, `_propagate` calls `_lia` quadratically, and DPLL calls `consistent`
  once per node — so **the total work in one `satisfiable()` had no bound at all. A budget
  that resets is not a budget.** Fixed with a global work purse (`MAX_WORK`, one `Exhausted`
  per query, which the callers may not swallow), and — the sharper half — by bounding the
  **size** of a linear system (`MAX_LINEAR`) rather than the number of them: **Fourier–Motzkin
  is quadratic per elimination, so counting calls bounds nothing.** Both numbers were set
  against **measurement**: peak honest work over the whole prove suite *and* 07's corpus is
  **131 units** (fence: 2 000 000) and the largest honest linear system is **8 rows** (fence:
  256). The headroom is the argument that no real proof was traded away.
- **"I stopped looking" is not "this does not follow".** `solver.decide` now returns
  *(proved, gave-up)*; the CLI says **"gave up (budget exhausted)"**, and the tail line counts
  them. *The first is a fact about the program, the second a fact about the checker, and
  printing the second in the words of the first is how a tool teaches its user to distrust it.*
- **A crash was hiding a cost.** With the stack raised, the deep-expression probe stopped
  crashing and started **hanging**: translating `1 + 1 + … + 1` re-derived the linearity of the
  whole subtree **at every level** of a walk that already visits every node — 173 million
  `is_linear` calls on an 800-term sum. Fixed by checking the **node** (`pred.linear_node`,
  since a subterm the translator returns has already passed) and keeping the full `is_linear`
  as the specification, now run **once per formula at the solver's door** (`pred.formula_linear`)
  — *the fragment's boundary checked where the boundary is.* Plus `Env.memo`: `synth` walks each
  sub-expression once, but asked each node for the term of its **whole subtree**, which is n².
  **The rule: a crash can be the symptom of a cost, and fixing the crash without measuring the
  cost only moves the failure somewhere the tests cannot see it.**
- **And the walk nobody writes: `hash`.** Two walks down, the profiler said there was a third. A
  `Term` is a frozen dataclass, so `hash(t)` hashes the tuple of its fields — and a field of a
  Term *is* a Term: **a term is a tree, and its hash is a walk of that tree.** Harmless once;
  ruinous inside congruence closure, which looks a term up in a dict for every `find`, every
  merge, every subterm it registers. An O(n) hash inside an O(n) loop is **the quadratic nobody
  wrote down, because nobody wrote the loop.** A 600-term sum: 4.34 M calls to `hash`, ~40 % of
  the run. Terms are immutable and heavily *shared*, so `pred._node_hash` computes a node's hash
  once and keeps it; each node then hashes in O(arity), its children answering from their own
  caches. 4.34 M → 0, 3.8 s → 1.65 s. (It is assigned in every class body rather than inherited
  from a mixin, because `@dataclass(frozen=True)` **overwrites an inherited `__hash__` and
  respects an explicit one** — a mixin would have compiled, run, and done nothing.) The same
  sweep found `Env.sorts()` copying two dicts per call; an Env is immutable, so the table is now
  built once and is **read-only**, and the one caller that wrote into it asks `sorts_v` for a copy
  of its own. **The rule: an immutable structure may be walked once — every walk after that is a
  bug you have not noticed yet.** The checker's own share of a 1 600-term file is now **0.04 s of
  19.9 s**; what remains is 43 % frozen-oracle HM and 41 % Omega doing real work.
- **`ResultAxiom`** — see "Naming, door by door" in §7. The statement V2.3 *proves* and the
  statement `result_axioms` *asserts* are now produced by one function, at one door.

**Measured and left alone: the residual quadratic is the oracle's.** With the checker's share
gone, a 3 000-term expression is *still* quadratic — in `infer.py`'s `_apply_env`, which rebuilds
the whole type environment at every node (textbook naive HM). **07 pays it too** (7.9 s to
typecheck the same file, before any refinement work happens). It is *bounded, terminating* work:
not a hang, not a hole. Fixing it means threading the substitution lazily through inference — a
real change to the type-checker, made to the one file whose job is to be **indistinguishable from
the frozen oracle** (08's `infer.py` diff is nine lines), to speed up an input no program writes.
**§0.1 is not a rule we suspend when it is inconvenient**: the freeze is what makes every number
in this document evidence rather than preference. So it is written down, not patched. If it is
ever fixed it goes in **08's** copy, and `conservative` 90/0/0 is the harness that proves the fix
changed nothing.

---

### I — Invariants, and the eighth false proof — OK **COMPLETE 2026-07-14**

*"There have been many chance findings — a bit too many for my taste. Can we do better, and start
with more severe programming?"*

**Yes, and the complaint is exactly right.** Every bug in this axis was a **finding**. A hostile
program got lucky (V2.2‴), or a careful read got lucky (V2.2′), or a profiler got lucky (H). Seven
times. That method works — and its working is what disguises the problem with it: **a method that
finds bugs by being lucky cannot distinguish "there are none left" from "I stopped looking".** That
is the *same distinction* V1′ and H spent their entire budget forcing the checker to make about its
own budgets, and it would be a poor joke to demand it of the tool and not of the people building it.

So the rules stop being prose. `08/tests/invariants.py` (`make -C 08 invariants`, folded into
`harden`) checks three properties over all 92 corpus files, on every run. Each one is a bug we
actually shipped, generalised to its shape:

- **I1 — COVERAGE.** Every expression node in a checked body is *visited*, and visited once.
  **Missed** is the shape of V2.2‴(7): four sites *translated* a sub-expression instead of *walking*
  it, so every division in a Bool position raised no obligation at all. **Revisited** is the shape of
  H's quadratic: a subtree re-walked at every level above it. One question — *how many times did you
  look at this node?* — and the only acceptable answer is once. (The checker is bidirectional, so the
  invariant must watch **both doors**, `synth` and `check`. It did not, first time out, and reported
  a third of every program unwalked. **An invariant you have not seen fail for a reason you
  understand is not yet evidence of anything.**)
- **I2 — ASKING.** Every integer division the checker walks raises exactly one obligation. This is
  the shape of V2.2‴(5), and **coverage cannot see it** — the node *was* visited, and the checker
  declined to ask anyway, because it could not read the divisor. Obligations are matched by
  **provenance**, not by goal shape: `d /= 0` is also what a *contract* asks, and counting those
  would let a missing division hide behind a contract that happened to say the same thing.
- **I3 — WORK.** The checker's own cost is linear in the size of the program, checked by **counting,
  not timing** — the counters are deterministic, so this is a regression test and not a wall-clock
  coin flip. Measured: **2.00× per doubling** (`synth`, `term_opt`, `is_linear`) against a 2.5×
  budget; a quadratic would be 4×. The **solver** is held to a different bar *on purpose*: Omega on
  an n-term system is honestly superlinear, and is **fenced** (`MAX_WORK`), not fixed. Conflating the
  two would either excuse a quadratic in the checker or forbid an honest one in the solver.

**And I1 found an eighth false proof within minutes — the first one this project has ever found on
purpose.** 58 nodes across 7 corpus files came back **never walked**, and they were all one thing:
**the body of a lambda.** `check` walks a lambda's body, because it has an `RFun` to push into it.
`synth` returned `ROpaque()` **without looking inside** — and an unannotated `let h = fn (a) => …`
goes through `synth`:

```
let h = fn (a : Int) => 100 / a in h(0)
    ok: 0 obligation(s) proved          exit 0
    …then, at run time:                 ZeroDivisionError
```

**It is V2.2‴(7) exactly — a piece of the program the checker never walked — wearing a hat nobody
had thought to look under.** One of the 58 was a live division inside `07/tests/25_torture.lark`
(`filter(fn(x) => (x - (x / 2) * 2) == 0, xs)`), never once examined in the fork's whole life, in a
file called *torture*.

**The rule, generalised, is the thing to keep: "every sub-expression is walked exactly once" is not a
fact about EXPRESSIONS. It is a fact about EVERY PLACE CODE CAN HIDE — and a lambda is one of them.**

The fix (`synth`'s `Lambda` case): bind each parameter to what is **declared** about it — an
unannotated parameter is `ROpaque`, i.e. the checker knows *nothing*, which is the truth, because it
does not track the call sites — and then **walk the body**. A division inside is provable only if it
holds for **every** argument, and otherwise goes honestly unproved: weaker than tracking call sites,
and weak is the correct direction. The synthesised *type* stays `ROpaque` — walking a body is about
the obligations inside it, not about learning what the function returns. New pair
`prove/22_lambda_*`; `25_torture`'s pin goes 4 → **5** obligations, and the new one proves.

**And the generator's own blind spot, for the second time.** `adversary.py`'s docstring has said *"a
local lambda's result"* since V2.2‴ — and **the generator could not emit a lambda at all.** It knew
the words and not the grammar. Now it does, and per the standing rule (*never trust a fuzzer you have
not seen fail*) the fix was **disarmed** and both harnesses watched to fail: the adversary with a
false proof, I1 by naming the exact unwalked nodes. **A generator only ever finds bugs in the
language it can speak. Its grammar is a claim about which programs exist, and an unexamined grammar
is an unexamined claim.**

**The limit of the method, stated rather than left to be discovered.** I1/I2/I3 are invariants about
the **shape of the walk**, not about the **content of what is proved**. They can make one whole class
of bug — *the checker did not look* — impossible to ship quietly. They cannot tell you an axiom is
sound. The two honest gaps are unchanged: the logic is ℤ while RV32/C are 32-bit, and contracts are
partial correctness.

### V3 — Mechanized soundness of the refinement calculus *(the payoff)*
1. Model the refinement calculus (base types + predicates + subtyping) in lcore,
   reusing the existing STLC metatheory (`lark-typing/subst/step/preservation`).
2. Prove: refinement subtyping ⇒ semantic implication (denotational or
   step-indexed), hence a checked program's refinements hold at runtime.
3. **Done when:** the proof closes in lcore (0 errors, like Phase 5b), so "this
   program is proven" is discharged *by construction* whenever the checker
   accepts it. This is the literal answer to the founding question.

> **DECIDED (2026-07-16, ratified with Set) — the three forks resolved before starting:**
> **(a) Scope = the CALCULUS, not the solver, not the code.** "Prove the prover" names three
>   mountains and only one is chapter-sized. V3 proves the *rules* sound (subtyping ⇒ semantic
>   implication); it never mentions `refine.py`. Proving the from-scratch decision procedure
>   (congruence closure + Omega + DPLL(T)) sound/complete is a *separate later axis* ("prove the
>   solver", an SMT-core metatheory). Proving `refine.py`/`solver.py` decide the modelled relation
>   is *another* ("prove the code", needs the Lark port first). Both are NAMED and set aside; the
>   trust gap from the calculus to the running Python is STATED, not hidden.
> **(b) Semantics = a STEP-INDEXED LOGICAL RELATION over the existing operational metatheory** —
>   NOT a denotational model. Reason: it stands *on* `lark-step`/`preservation` (already closed at 0)
>   instead of beside them; recursion (`descend`) is admitted by the step index rather than dragging
>   in domains; and erasure models itself — V1's "a mention is not a use" reappears as the *shape* of
>   the relation (refinement = a predicate riding the relation; the erased term = the plain typed term
>   the metatheory already handles). This resolves the "(denotational or step-indexed)" left open in
>   point 2 above.
> **(c) Start with the V3-SPINE.** Refinements on base ints only, NO measures, NO higher-order, ONE
>   subtyping-soundness lemma, close in lcore at 0 — spine-first, same method as V1-before-V2 and
>   build-before-destruct. Measures-as-total-logic-functions (and the termination obligation they drag
>   in, §7 risk "Measures and termination") come AFTER the spine holds, not instead of it.
> **Boundaries V3 does NOT dissolve**: logic is ℤ / RV32+C are 32-bit; partial correctness;
>   the equality seam; concrete-subfields one-sidedness.
> **Boundary added 2026-07-17 — the ∀/safety form is unreachable in lcore, and moot for this language.**
>   DESCEND (flip `SemE` to the ∀/safety form so the step index becomes load-bearing) was taken seriously
>   and CLOSED as a deliberate boundary, not a pending rung. Two reasons: **(i)** its fund App case needs
>   *positive* `Step` inversion (decompose a reduction of `EApp f x`), and lcore cannot express the
>   inversion motive — a well-typed one must reconstruct the redex contractum from a generic source `Expr`,
>   i.e. discriminate an Expr head and refine its `Ctx` index to `empty` inside `indrec Expr`, the exact
>   thing the step file documents as impossible (lark-step.lcore:36–37). The minimal `beta_det` motive
>   fails to typecheck (`inferred Expr empty b / expected Expr empty t1`) — decisive. `step_not_val` works
>   only as the negative/uniform direction. **(ii)** Lark is strongly normalizing, so the ∀-form's only
>   gain (safety-under-divergence) is vacuous; the ∃-form we have (V3-FUND) EXHIBITS a terminating
>   reduction to a refinement-good value = total correctness, the *stronger* statement, and works precisely
>   because it only ever *introduces* `StepsN`, never inverts it. Full story: LOG.md ▶▶ V3-DESCEND-WALL.
> **CBV side-finding 2026-07-17 (fix deferred):** `StepBeta` lacks the `IsVal arg` guard its own header
>   documents → the encoded `Step` is non-deterministic and the green ∃-proofs lean on it (β on unevaluated
>   args). Real latent defect; the fix would force a "CBV-faithfulness" rework of the ∃-form arrow — a
>   separate optional project, not a soundness gap for a pure total language.
> **Book writeup of this reasoning is DONE** — the finished "The horizon" section of
>   `book/chapters/ch16_refinement.tex` (replaced the one-line stub; book compiles clean).
> **The spine is DONE (2026-07-16, closed at 0):** `formal/proof/lark/lark-refine.lcore` — story in
>   `LOG.md` under its date. (Reader-facing curation into `prove/lark-formal/` is the book-side backlog item.)

### V-deep — Dependent elaboration to MLTT *(stretch)*
1. Extend the ch12 `bridge/` from "well-typed Lark → MLTT *type*" to "Lark term
   → MLTT *term with proof obligations*".
2. Discharge obligations beyond the decidable fragment as explicit MLTT proof
   terms in lcore.
3. **Done when:** at least one program whose spec is *not* decidable (needs
   induction/quantifiers) is proven end-to-end through the bridge.

---

## 5. Strategy & guardrails

- **Oracle-first, differential everywhere.** Same discipline as self-hosting: the
  Python prototype (in `08/`, never `07/` — §0.1) is the reference; the `prove/` suite
  records the expected accept/reject verdict (and reason) per file; no silently-changing
  behaviour.
- **Conservative extension, and prove it.** Every program that checks today must still
  check, identically, through the fork — unless it carries a refinement. The fork makes
  that a test you can run; editing the oracle in place would make it a claim you could
  only assert.
- **Checking before inference.** Explicit refinement annotations first (tractable
  and pedagogically clean); predicate inference is a later, optional layer.
- **Decidable core, honest edges.** Keep the predicate logic inside a decidable
  fragment; anything that wants quantifiers/induction is explicitly V-deep, not a
  silent extension of the checker.
- **Prove the prover (V3), don't just trust it.** The whole point is to reach the
  language's own standard of proof — so the refinement calculus must itself be
  mechanized, not merely implemented.
- **No external dependency in the resting state.** Z3 may bootstrap the solver,
  but the committed system ships a from-scratch decision procedure to preserve
  the self-contained, silicon-to-semantics story (and the Pico/RISC-V target).

---

## 6. Proposed layout

```
lark/
  07/src/                 # THE FROZEN ORACLE — not touched by this plan (§0.1)
  08/src/                 # this axis's fork of it: prototype the checker + solver HERE
    refine.py             # refinement AST, env, VC generation
    solver.py             # QF-UFLIA: congruence closure + linear int arith
    (everything else)     # byte-identical to 07/src until this axis has reason to
                          # change it; drift-checked, so "until" is enforced
  self/                   # later: port to Lark, checked against 08/ as self/ is vs 07/
    refine.lark  solver.lark
  formal/proof/           # V3: soundness of the refinement calculus (lcore)
  ch12 bridge/            # V-deep: dependent elaboration to MLTT
  prove/                  # the verification suite (safe/unsafe mutant pairs)
  PROVE.md                # this file
```

---

## 7. Risks & open questions

- **Solver scope creep.** A full SMT solver is a career; scope hard to QF-UFLIA
  and the *linear* integer cases that refinements actually generate. Simplex +
  branch, or Cooper's algorithm on the Presburger fragment, is enough — resist
  general nonlinear arithmetic.
- OK **Affine × refinement typing — SETTLED in V1** (2026-07-13). Predicates *are*
  use-neutral: a mention is not a use, by construction (erasure), and it is sound
  because affinity restricts **use, not truth** — which is a fact about *purity*,
  not about affinity, and would fail in a language with mutation. The wrinkle the
  literature does not warn you about is the second one: **the guard that establishes
  a predicate is a use even though the predicate is not**, which blocks the two
  features jointly for non-Copy types and hands V2 a derived requirement (refined
  products). Both are recorded in V1 above and in `prove/`; both are book-grade.
- **Refinement inference is the hard, optional part.** Predicate abstraction over
  qualifier sets (the "Liquid" in Liquid Types) is where the cleverness lives.
  Treat it as V2-optional; annotated checking already delivers program proofs.
- **Measures and termination.** Measures must be total/terminating to be sound in
  the logic; Lark has no termination checker yet. Either restrict measures to
  structural recursion or add a small size/termination check.
- **What "proven" means at V1/V2 vs V3.** Before V3 the guarantee is "checked by
  a trusted tool"; only V3 makes it "checked by a *proven* tool." Be precise
  about which is claimed — don't oversell V1 as V3.
- **Connecting proof to the running binary.** Refinements are erased; the safety
  they guarantee holds of the *semantics*. End-to-end trust down to emitted
  C/RISC-V is a further step (verified compilation — a different project again).

### Naming, door by door — is *that* class closed? (2026-07-14)

Half of this project's false proofs were one bug wearing different clothes: **the checker
spoke about a name that did not mean what it thought.** `15_shadow` (a local `size` captured
the global one a contract was written against), `16_axiom` (a user's own `string_length` was
handed the primitive's axiom), and — found while hardening — `ResultAxiom` (a measure's own
parameter left free in the very theorem being proved). Worth asking directly whether the
*class* is closed, rather than the three instances.

**The reframing that closed it: a UF symbol is a global function, not a name.** The logic
identifies symbols by source text, and source text shadows; congruence closure then identifies
two functions because they spell the same. So the discipline is not "be careful with names" —
it is to enumerate **the doors through which a name enters the logic**, and to check each one.
There are four, and each is now shut by construction rather than by vigilance:

1. **An application becomes a term** — `term_opt` refuses `App(f, …)` when `f ∈ env.vsorts`
   (params, lets, match binders: the *value* variables, never a global fn). A locally bound
   function is **unspeakable**. Nothing sound was lost: a local function has no contract to read
   off and no equations to instantiate; all it ever had was congruence, and congruence was the bug.
2. **An axiom fires at a symbol** — `PRIMITIVE_AXIOMS` is intersected with the names the program
   **leaves alone** (fn *and* trait declarations). An axiom is about a *function*; a program that
   rebinds the name does not inherit the function's properties.
3. **A signature is trusted by a caller** — V2.2″: an `impl` method is checked against the
   **trait's** signature, which is also precisely what entitles a caller to read it. A contract the
   callers trust and nobody checks is the same bug from the other end.
4. **A declared result is instantiated** — the hardening pass's `ResultAxiom.at()`. The induction
   **proves** `at(m(C(y…)))` and every obligation **assumes** `at(m(t))`: one function, one door, so
   the statement proved and the statement asserted cannot drift apart. (Before it, a measure's own
   parameter was left free in both — sound only by the accident that free variables in a validity
   query are universally quantified, which is exactly the kind of "sound by luck" that stops being
   luck the moment someone adds a feature.)

**So: yes, with two honest qualifications.** (a) The *audit* is complete — but this class has been
re-opened twice by new machinery (V2.2‴'s new sites, V2.3's new axiom), and the pattern is that each
new rung **adds a door**. The test of a closed class is a rung that adds one and does not leak, and
**V2.4 is that test**: a parametrised measure's extras enter as free variables, which is door 4 again,
at higher arity. (b) The rule is now stated in a form a future rung can be held to, and it is the one
line worth keeping: **where the checker cannot speak, it says nothing — never `true`, never a negation,
and never a claim about a name it does not own.**

---

## 8. First step (when we pick this up)

**Step 0: fork the oracle. OK DONE 2026-07-13.** Copy `07/src` to `08/src`, stand up the drift
check that holds the untouched modules byte-identical, and confirm the existing corpus
type-checks and evaluates the same through `08/` as through `07/`. That is the
conservative-extension baseline, and it is worth having *before* the first refinement exists,
because afterwards you cannot tell a regression from a feature.

> **What Step 0 built** (`make -C 08 test`; numbers pinned in `08/README.md`):
> `08/tests/drift.py` — **25 identical / 0 extended / 0 added / 0 missing**; its `EXTENDED`
> and `ADDED` tables are the running measure of how large this extension has grown, and a
> module that drifts without appearing in one of them fails the check.
> `08/tests/conservative_difftest.py` — **90 ok / 0 fail / 0 skip**: all 45 corpus files
> through both trees' `infer.py` *and* `cek.py`, byte-identical. `cek` is in there because
> refinements erase at runtime — one that changes what a program *prints* is not a refinement.
> The baseline paid for itself immediately: it re-found the oracle's `_anon_{id(node)}`
> run-to-run nondeterminism (two runs of `07/src` alone disagree), canonicalised as in
> `self/tests/emit_c_difftest.py`.

Then prototype **V1 steps 1–3 in Python**, in `08/src`: add `{v:b|p}` syntax,
generate VCs at subtyping points, and decide them with a congruence-closure +
linear-integer-arithmetic core (Z3 behind `--smt` only to unblock). Then stand up
the `prove/` suite of safe/unsafe pairs. That single step turns "Lark proves
safety for free" into "Lark proves the properties you write down."
