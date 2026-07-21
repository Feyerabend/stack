
## strands/ — the three climbs past the V3 summit

The V3 upward axis (`../lark/lark-refine.lcore`) reached its summit — `fund`, the
fundamental lemma of a step-indexed logical relation, covers the __whole__
refinement calculus in its ∃-form (total correctness), both pitches green. Then it
hit a wall: __DESCEND__ — flipping the relation to the ∀/safety form — needs
*positive `Step` inversion inside `indrec Expr`*, and lcore cannot refine the `Ctx`
index to `empty` under the eliminator. That form is also *vacuous*: Lark is strongly
normalizing (STLC, no recursion), so the ∃-form already IS the stronger statement.
DESCEND was closed as a named boundary, not climbed (`../../../LOG.md` ▶▶
`V3-DESCEND-WALL`).

These three strands are the *other* ways up. Each re-proves or extends the guarantee
from a different direction, and each __dodges__ the DESCEND wall rather than assaulting
it. They are exploratory: the main proof (`make check`, 5 files / 0 errors) never
depends on any of them.

### The one picture

All three answer a single question — *what does a Lark refinement derivation `HasR`
buy you?* — and they answer it in three different target languages:

```
                          HasR g rg t r e
              (a Lark refinement typing derivation)
                                 |
        +------------------------+------------------------+
        |                        |                        |
      DENOT                   SOLVER                    VDEEP
   into lcore's           into a decision           into an MLTT
   own TYPES              procedure's verdict        object term
        |                        |                        |
   fundD : HasR →         sub_fixture :            elab : HasR →
   DEnv → RTyD t r        Sub TInt rge2 rge1       MTm (ctxD g rg)
   (a semantic value)     (the SubBase premise,      (tyD t r)
        |                  decided not assumed)     (a syntactic term)
        |                        |                        |
   "the type is           "the checker's           "the derivation IS
    inhabited"             implication is true"      a proof, reified"
```

- __denot__ takes the semantic route: it *interprets* the types and produces an
  inhabitant, proving the derivation meaningful.
- __solver__ takes the decision route: it *discharges* the very implication premise
  (`SubBase`) the summit took on faith, so the checker's "⊆" is decided rather than
  hypothesized.
- __vdeep__ takes the syntactic route: it *reifies* the derivation as a term in a
  second object theory, realizing Curry–Howard literally — the type is a proof you
  can hold.

Together they close the triangle: the summit proves the calculus __sound
operationally__; denot re-proves it __denotationally__; solver removes the last
__assumed__ hypothesis; vdeep shows the whole thing is a __compiler into proofs__.

### The three, in one line each

| strand | theorem | target | status |
|--------|---------|--------|--------|
| __denot__ | `fundD : HasR → DEnv → RTyD t r` — soundness by `indrec HasR`, all 8 rules one line each, both λ-introductions free | refinement types ⟶ lcore __types__ (`{v:Int\|p} ↦ Σ(n:Nat).IsTrue(p n)`) |  __complete__ |
| __solver__ | `sub_fixture` via `leB` sound+complete (LIA) __+__ `cc_sound : Cong a b → Id (eval a)(eval b)` in every model (UF) | the `SubBase` implication ⟶ a __decided__ verdict; both QF-UFLIA halves | ◐ __both halves proven__ |
| __vdeep__ | `elab : HasR → MTm (ctxD g rg) (tyD t r)` — all 8 rules incl. function-subtyping coercion | derivations ⟶ intrinsically-typed __MLTT terms__ |  __complete__ |

### Two more — a NEW question and an empirical property (added 2026-07-18)

These are __not__ further routes to refinement soundness; they widen the frontier and
then bridge back to the book. Sequenced __affine → fixpoint → resume the book__
(see `../../book/PLAN.md`); both are now landed. (A third, *semantic preservation*,
was considered and __scrapped 2026-07-18__ — its tractable form already lives in the
book as ch13/ch17 prose, and a partial lcore slice would have made the un-proven rest
read as *unfinished* rather than *consciously bounded*.)

| strand | question | kind | status |
|--------|----------|------|--------|
| __affine__ | *what does Lark's affine discipline buy?* — `affine_sound : HasA g t g' → Consumed g g'` (no double-use), the __A in Lark__, the one first-class mechanism that was only *described* | kernel-checked, wall-dodging (recurse on `HasA`; functional `SlotLe`/`Consumed` — no Id/J/inversion; threading subsumes Split) |  __M0–M2 spine done__ (`affine/PLAN.md`); `make affine` + `affine-controls` 4/4 |
| __fixpoint__ | *what does self-application buy — and not?* the byte-identical bootstrap (`make -C self bootstrap`) as a stability witness, plus the __Trusting Trust__ caveat that stability ≠ trust | empirical (build-verified, __not__ kernel) |  __re-verified `49a4921c` + articulated__ (`fixpoint/PLAN.md`); book beat pending |

### Why none of them re-hit the wall

The wall was *positive inversion of an operational `Step` relation under `indrec`*.

- __denot__ never eliminates `Step` at all — it recurses on the *derivation* and lands
  in lcore's meta-level types. Nothing operational to invert.
- __solver__ works below the relation entirely, on `Nat`/`Bool`, the inductive
  `Le`, and first-order terms — the `Step` relation is not in scope. Both the LIA
  (arithmetic) and UF (congruence-closure) halves are ordinary `natrec`/`indrec`
  over first-order `data`, exactly where lcore is strong.
- __vdeep__ recurses on the *source* `HasR` and only *introduces* target `MTm` terms.
  Every rule — including both λ-introductions — is introduction-direction. The one
  place needing `indrec MTm` (intrinsic renaming under a binder, via order-preserving
  embeddings → `mweaken`) is *still* introduction-direction index-change (building a
  term in a bigger context), never inversion-by-unification.

The common shape: __recurse on the derivation, build in the target.__ That is the
move DESCEND could not make (it had to invert a runtime step), and it is why all
three go through.

### What each one leaves open (named boundaries, not gaps)

- __denot__ — soundness of the model, __not adequacy__: no bridge yet from a
  denotation back to the CEK machine's output. The forward direction of an adequacy
  logical relation should also dodge the wall; untried (`denot/PLAN.md`).
- __solver__ — both QF-UFLIA *cores* are proven (interval LIA + congruence-closure
  UF), but each at its floor: LIA is the single-variable `{n ≥ c}` slice, CC is
  soundness (not completeness). Full multi-variable Omega and CC completeness widen
  them to the rest of QF-UFLIA (`solver/PLAN.md`).
- __vdeep__ — `MSub` carries its refinement predicate as a __shallow__ `Nat → Bool`
  (semi-shallow embedding); a fully syntactic predicate object would make
  `MSub`/`msub_weaken` deep too. Adequacy to CEK output is shared with denot
  (`vdeep/PLAN.md`).

None of these is required for the strand to stand: each has a documented stopping
line and its own green bar.

### Running

```
make denot             # denotational strand            (6 files / 0 errors)
make denot-controls    #   its negative controls        (OK = 4/4 refused)
make solver            # solver strand                  (6 files / 0 errors)
make solver-controls   #   its negative controls        (OK = 8/8 refused)
make vdeep             # elaboration strand             (6 files / 0 errors)
make vdeep-controls    #   its negative controls        (OK = 4/4 refused)
make check             # the untouched main summit      (5 files / 0 errors)
```

Every strand ships __negative controls__ — deliberate lies (a forged bound, a
flipped variance, a false implication, a mis-indexed variable, an invented axiom)
that the kernel must refuse. denot and vdeep run 4 each; solver runs 8 (4 interval +
4 congruence closure). A controls PASS means the kernel refused *all* of them — it is
what keeps a green bar from being vacuous.

### Order, and why vdeep was last

Agreed with Set: __denot → solver → vdeep__. The denotational model was the natural
first climb — wall-free, and it re-proves the whole calculus far more cleanly than
the operational relation. solver came next because its `sub_fixture` plugs straight
back into the summit's one remaining hypothesis. vdeep was saved for last by
preference: the most open-ended, and the one that risked re-hitting the wall from a
new angle (nested indexed induction over MLTT's own context). It got the most runway
— and went through deep, no shallow floor needed.

If a strand does not complete, its `PLAN.md` stands on its own as a reviewable design.
That is the point of keeping all three here.
