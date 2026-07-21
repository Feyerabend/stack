
## Strand C - V-DEEP: elaborate Lark into MLTT  -- COMPLETE

__Status:__ DONE (2026-07-17). `elab : HasR g rg t r e → MTm (ctxD g rg) (tyD t r)`
- a verified elaboration of every Lark refinement derivation into an
intrinsically-typed MLTT term of the translated type - is green, all 8 rules.
Lives in `lark-vdeep.lcore`. `make vdeep` → 6/0; `make vdeep-controls` → 4/4 refused.
The scout's verdict held: __vdeep never re-hit the DESCEND wall.__

## What landed

| construct | meaning |
|-----------|---------|
| `MTy`/`MCtx`/`MVar`/`MTm` | a minimal intrinsically-typed MLTT object theory inside lcore - well-typing FUSED into the term's index, so a closed `MTm g t` IS a well-typed term (no separate `HasMLTT` needed) |
| `tyD` / `ctxD` / `elabVar` | the translations `⟦·⟧`: refined type → `MTy`, refined ctx → `MCtx`, Lark var → `MVar` at the translated slot |
| `OPE` + `ope_var`/`ope_id`/`ope_tm` + `mweaken` | intrinsic renaming via order-preserving embeddings (McBride thinnings); `ope_tm` goes UNDER the `mlam`/`mlet` binder via `ope_keep` - the piece the operational proof could never reach |
| `elabSub` | reifies a `Sub` derivation as an MLTT coercion: `SubBase ↦ msub_weaken`; `SubFn ↦` an η-expanded coercion `λx. ihc (f (ihd x))` that WEAKENS `f` under the fresh domain binder (consumes `mweaken`) and fires both variance IHs |
| `elab` | `indrec HasR` over all 8 rules → the full elaboration |
| smokes | `smoke_lam`/`smoke_let`/`smoke_sub`/`smoke_fn_coe` elaborate the SAME derivations the operational `fund` proof uses; `smoke_fn_coe` reifies a genuine function-subtyping and COMPUTES to the concrete `mweaken`-driven coercion term |
| `controls.lcore` | 4/4 refused: wrong-result-refinement, function-variance flip, false implication ({n≥1}⊆{n≥2}), de-Bruijn index forge |

## The C0 finding (why there was no wall)

`elab` recurses on the *source* `HasR` and only *introduces* target `MTm` terms, so
all 8 rules - including both λ-introductions - are wall-free. The one place that
needs `indrec MTm` (renaming) is still *introduction-direction* index-change
(building a term in a bigger context), never the positive-inversion-by-unification
that killed DESCEND. Landing fix banked: lcore interleaves each recursive argument's
IH immediately after it (`\x. \ihx.` per premise, not bunched).

## Optional deepenings (not needed for done)

- A deep predicate layer: `MSub` currently carries the refinement predicate as a
  shallow `Nat → Bool` (semi-shallow embedding). A fully syntactic predicate object
  would make `MSub`/`msub_weaken` deep too. Named boundary, not a gap.
- Adequacy: relate the elaborated `MTm` back to the CEK machine output (shared with
  strand denot's adequacy boundary).
Scheduled last (denot → solver → __vdeep__) - Set's stated preference: the most
interesting and most open-ended, so it gets the most runway.

## C0 progress (resume here)

The scout DID NOT hit the DESCEND wall in the introduction-only fragment - as
`fundD` predicted, `elab` recurses on the *source* `HasR` and only *introduces*
target `MTm` terms, so all 8 rules bar RT_Sub's SubFn are one-liners.

- __Block A - VERIFIED green this session.__ Intrinsically-typed object theory
  (`MTy`/`MCtx`/`MVar`/`MTm`, well-typing fused into the term index - cleaner than
  a separate `HasMLTT`), the two translations `tyD : RTy → MTy` /
  `ctxD : RCtx → MCtx`, `elabVar : Var → MVar`, and the introduction-only elab
  CASES `elab_int/bool/var/app/lam/let/if` (standalone, typed to the `indrec HasR`
  motive instances). Piped after meta+refine → 0 errors; `elab_lam` (the λ case)
  inferred clean = the C2 "real test" is wall-free.
- __Block B - VERIFIED green.__ The crux the operational proof could not reach:
  intrinsic renaming `mweaken` via order-preserving embeddings (`OPE` = keep/drop
  thinnings; `headCtx`/`tailCtx`; `mvcase`; `ope_var`; `ope_id`; `ope_tm` going
  under the mlam/mlet binder via `ope_keep`; `mweaken`). `mweaken : MTm g t →
  MTm (mcons s g) t` and `ope_tm` infer their intended types - so `indrec MTm`
  DOES go under a binder that changes the context index, in the *introduction*
  direction. __vdeep does not re-hit the DESCEND wall, not even here.__ (Landing
  fix: lcore interleaves each recursive argument's IH immediately after it, so the
  mapp/mif/mlet cases bind `\x. \ihx.` per premise, not all IHs bunched at the end.)

### The rest (all DONE - see "What landed" above)
`elabSub` (SubBase ↦ `msub_weaken`, SubFn ↦ the `mweaken`-driven η-coercion), the
`elab = indrec HasR` assembly, the showcase smokes, `controls.lcore`, the `vdeep`/
`vdeep-controls` Makefile targets, and README/LOG/PROVE/memory updates all landed.
The fallback floor (`fundD` as a shallow elaboration) turned out unneeded - the deep
version went through.

## The boundary this closes

Everything so far says *Lark has a sound refinement checker*. V-deep aims one level
up: __Lark's types ARE proofs__ - realise the Curry–Howard slogan the companion
book (`Types as Proofs`, lang-stack ch12) makes, by giving a __verified
elaboration__ from Lark refinement derivations into MLTT (lcore) terms. Not a
semantic *model* of the types (that is strand denot), but a *translation of the
programs* into a proof assistant's term language, with a theorem that the
translation preserves typing.

## The shape

A function, in lcore, of roughly:

```
elab : HasR g rg t r e  →  <an lcore term of type ⟦t,r⟧ in context ⟦g,rg⟧>
```

where `⟦·⟧` reuses the strand-denot interpretations (`TyD`/`RTyD`/`DEnv`). Note
that __`fundD` from strand denot is already almost this__ - it maps a derivation to
an inhabitant of `RTyD t r`. The difference V-deep chases is *reification*: instead
of computing a semantic value inside lcore's meta-level, emit a __syntactic MLTT
term__ (a `data MLTT` object) and prove *it* well-typed by a separate `data HasMLTT`
judgment - i.e. a translation between two *object* languages, verified.

That extra `data MLTT` + `HasMLTT` layer is what makes this deep: it needs a small
dependent type theory defined *inside* lcore, and a preservation theorem
`HasR → HasMLTT` over it.

## Staging (smallest-first, find-the-wall-first)

1. __C0 - scouting probe (one session).__ Define a *minimal* `data MLTT` (Nat, Π,
   a subset former) and `data HasMLTT`, then try `elab` on just `RT_Int` and
   `RT_Var`. Goal: hit the first wall. Prime suspects for the wall, to test early:
   - representing MLTT __binding__ (de Bruijn `data MLTT` indexed by its own `Ctx`)
     inside lcore - does `indrec` over a *nested* indexed syntax go through, or does
     it re-trigger the same `Ctx`-refinement limitation that killed DESCEND?
   - the `RT_Sub` case: elaborating subsumption needs the solver-implication term as
     a first-class MLTT proof - which reaches into strand __solver__'s territory.
2. __C1 - the non-binding fragment.__ If C0's binding representation holds, prove
   `elab` for RT_Int/Bool/Var/App/If/Sub (mirrors denot's wall-free set).
3. __C2 - λ-introduction.__ RT_Lam/RT_Let. In denot these were one-liners; whether
   they stay easy here depends entirely on how C0's binding representation behaves
   under an extended context. This is the real test of the strand.

## The honest risk (why scout first)

V-deep is the one strand that might __re-encounter the DESCEND wall from a new
angle__: defining a dependent object theory `data MLTT` indexed by its own context,
and eliminating over it, is exactly the kind of *nested indexed induction* where
lcore's inability to refine an index under `indrec` bit before. C0 exists to find
that out in one session rather than after a month of build-up. If C0 walls, the
fallback is the __shallow__ version: skip the syntactic `data MLTT` and let `fundD`
(strand denot) stand as the "elaboration into lcore's *own* type theory" - which is
already done, just not reified. That fallback is worth stating up front so the
strand has a guaranteed floor.

## Dependencies

- __strand denot__ - reuses `TyD`/`RTyD`/`DEnv`; `fundD` is the shallow floor.
- __strand solver__ - `RT_Sub` elaboration wants the solver's implication as a
  reified proof term. V-deep can stub this (take it as a hypothesis, as the whole
  V3 proof does) until solver lands.

## Definition of done

- __C0__ when the scouting probe either elaborates RT_Int/RT_Var into `HasMLTT`
  __or__ produces a crisp, documented wall (either outcome is a real result).
- __C1/C2__ - as the fragments above typecheck with controls.
- __Floor__ - if the deep version walls, `fundD` is recorded as the shallow
  elaboration and the strand closes honestly at that line.
