
## Strand A — the DENOTATIONAL model  COMPLETE

__File:__ `lark-denot.lcore` (piped after the metatheory + `lark-refine.lcore`).
__Green bar:__ `make denot` → 6 files / 0 errors. `make denot-controls` → 4/4 refused.

### The idea

The operational V3 relation *observes* a program: it runs `Step`, counts a budget,
proves the run reaches a value in the semantic set. DESCEND died trying to *invert*
that run. The denotational model never runs anything. It __interprets__ each
refinement type as an lcore type and proves the fundamental lemma by recursion on
the *derivation* — the syntax `HasR` — so the only eliminations are over `Ty`,
`RTy`, `Var`, `Ctx`, `HasR`, and `Bool`. There is no `Step` to invert, so the
DESCEND wall is structurally absent.

### What is proved

| construct | meaning |
|-----------|---------|
| `TyD  : Ty → Type` | Int↦`Nat`, Bool↦`Bool`, `TFn a b`↦`TyD a → TyD b`, unmodelled scalars↦`Unit` |
| `RTyD : Π t. RTy t → Type` | `{v:Int\|p}` ↦ the subset `Σ(n:Nat). IsTrue (p n)`; a refined function ↦ a __dependent__ map `RTyD a ra → RTyD b rb` |
| `sub_denot` | `Sub t r r' → (RTyD t r → RTyD t r')` — subtyping soundness. SubBase reindexes the subset witness through the predicate implication; SubFn is the classic contravariant-domain / covariant-codomain `f ↦ λx. ihc (f (ihd x))` |
| `DEnv : Π g. RCtx g → Type` | a telescope of refined denotations (the denotational GoodEnv, valued in `RTyD`) |
| `denot_lookup` | projects the vᵗʰ refined denotation out of a `DEnv` |
| `fundD` | __the fundamental lemma:__ `HasR g rg t r e → DEnv g rg → RTyD t r`, by `indrec HasR` over all 8 rules |

#### Why this is the cleaner proof

Every case of `fundD` is one line. The two that cost the operational proof its
entire __Pitch 2__ (the substitution lemma: `lb`, `fuse`, `lam_app_cert`,
`let_cert`, σ-fusion, a step budget) are here trivial:

```
RT_Lam ↦ \env. \x. ihbody (x, env)      -- lcore's own λ IS the model
RT_Let ↦ \env. ihbody (ihval env, env)
RT_App ↦ \env. ihf env (ihx env)        -- lcore's own application IS the model
```

Showcase smoke `fundD_id`: the Lark identity on `{Int|ge2}`, built with `RT_Lam`
+ `RT_Var`, denotes the identity map on `Σ(n).IsTrue(ge2 n)`. Proven with `RT_Lam`
as a one-liner — the operational path needed the whole Pitch-2 pile for the same fact.

#### Controls (all refused — `controls.lcore`)

1. __payload forge__ — `RT_Int` at `\_. false`: `IsTrue (false)` = `Empty`, no witness.
2. __variance forge__ — the `{ge2}→{ge2}` identity is not a `{ge1}→{ge2}` map.
3. __subtyping-direction forge__ — `imp21` (ge2⇒ge1) cannot witness `{ge1}⊆{ge2}`.
4. __erasure/index forge__ — `RInt ge2 : RTy TInt` cannot index `RTyD` at a `TFn`.

### The named boundary (the honest cost)

This is a __soundness-of-the-model__ result, not an __adequacy__ result. It proves:
*if a program is well-refined, its denotation lives in the interpreted subset.* It
does __not__ yet bridge back to the operational world — i.e. "the denotation of a
closed `{Int|p}` program equals the `Nat` the CEK machine actually produces, and
that `Nat` satisfies `p`." The operational V3 relation *does* deliver that
adequacy (it runs the machine). So the two proofs are complementary:

- __operational V3__ — adequate (talks about real reductions) but heavy, and walled at DESCEND.
- __denotational (this)__ — clean and total, but one inferential step short of the machine.

#### If this strand is ever pushed further

The adequacy bridge is a __logical-relations / computability__ argument between
`RTyD t r` and the operational `SemE`/`SemV`: define a relation `TyD t ≈ (closed
values of type t)` and show `fundD`'s output relates to `fund`'s. That re-imports
some operational reasoning — but crucially the *forward* direction (value → its
denotation) is uniform and does __not__ need positive `Step` inversion, so it
should stay clear of the DESCEND wall. Untried; noted for a later climb.
