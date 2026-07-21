
## Strand B — prove the SOLVER  ◐ BOTH QF-UFLIA HALVES PROVEN (interval + congruence closure)

__Status:__ both halves of QF-UFLIA's *core* are now built and green. The __LIA__
(arithmetic) half: the interval / lower-bound fragment — a real decision procedure,
proven sound *and* complete, whose verdict discharges the `SubBase` seam on the
spine's actual `ge` fixtures. The __UF__ (equational) half: __congruence-closure
soundness__ — every closure-derived equality holds in every model of the axioms.
What remains is *width* (full multi-variable Omega, CC completeness), not a missing
half. Second of three strands (denot → __solver__ → vdeep).

__File:__ `lark-solver.lcore`. __Green bar:__ `make solver` → 6 files / 0 errors.
`make solver-controls` → 8/8 refused (4 interval + 4 congruence closure).

### What landed (the interval fragment — was B2 + B3 in the original staging)

| construct | meaning |
|-----------|---------|
| `leB : Nat → Nat → Bool` | the DECISION PROCEDURE — a boolean `≤`. The spine's predicates literally are this: `ge1 ≡ \n. leB 1 n`, `ge2 ≡ \n. leB 2 n`, __definitionally__ |
| `leB_sound` / `leB_complete` | the verdict reflects the inductive `Le`, both directions — `leB a b = true ⇔ Le a b`. Verdict ⇒ truth is the heart of solver soundness |
| `entail_ge` | interval entailment: to prove `{n≥c1} ⊆ {n≥c2}` decide the single comparison `c2 ≤ c1`, then `le_trans`. This produces the `SubBase` premise __from a decision__ |
| `sub_ge` | the solver EMITS a `Sub TInt (RInt {n≥c1}) (RInt {n≥c2})` certificate from a decided bound |
| `sub_fixture` | the payoff: `Sub TInt rge2 rge1` — the exact certificate the V3 proof took on faith — and `sub_fixture_sem` flows it into the existing `sub_sound_v`, so the solver's verdict feeds the operational soundness map |
| `nmax` / `NList` / `norm` / `sub_conj` | S2: conjunctions of lower bounds, normalized to the tightest (`nmax`-fold), entailment reduced to comparing normalized bounds — the solver handling constraint SETS |

__Controls (`controls.lcore`, 4/4 refused):__ false-entailment forge (`{n≥1} ⊄ {n≥2}`),
forged soundness (`leB_sound` on a false verdict), reversed certificate (mismatch),
conjunction-weakening forge. The solver __cannot emit a certificate for a false
entailment__ — that is the teeth.

### What this closes

The "solver is modelled, not proven" boundary (PROVE.md §4 V3), __for the interval
fragment__ — the fragment the spine's refinements actually inhabit. `SubBase`'s
`imp` hypothesis is now *constructed by a proven decision procedure* for `{n≥c}`
refinements, not assumed. That is the strand's floor, and it is reached.

### What landed (the congruence-closure fragment — was B1, the UF half)

| construct | meaning |
|-----------|---------|
| `Tm` / `eval` | first-order terms (Nat-indexed atoms + one binary application) interpreted in ANY model — a domain `D`, an atom valuation, an `app`. The `Π D val app` quantification IS "in every model" |
| `Ax` | the hypothesis set the solver is handed — a concrete axiom `f a = a` (the classic congruence example) |
| `Cong` | the congruence closure as an inductive derivation: reflexivity, symmetry, transitivity, the congruence rule over application, and axiom leaves — exactly the moves union-find + congruence make |
| `cc_sound` | the theorem: `Cong a b → Id (eval a) (eval b)` in every model satisfying the axioms. By `indrec Cong` — cAx↦hyp, cRefl↦`refl`, cSym↦`sym`, cTrans↦`trans`, cApp↦`ap2` on `app`. CC cannot certify a false equality, same teeth as `leB` |
| `cc_smoke` / `cc_smoke_sem` | a genuine two-step run: congruence lifts `f a = a` to `f(f a) = f a`, transitivity gives `f(f a) = a`; `cc_smoke_sem` reifies it as "in every model of the axiom, `f(f a) = a`" and its normal form consumes the axiom hypothesis twice (not vacuous) |

__Controls (5)–(8), 4/4 refused:__ reflexivity forge (distinct atoms equated),
congruence forge (unequal head manufactured), axiom forge (a hypothesis invented),
transitivity gap (broken middle). The closure cannot build a false equation.

### What remains (width, not a missing half)

__Status of the rest below:__ design only. No lcore yet. These *widen* the two
proven cores; neither is a prerequisite for the seam the spine uses.

### The boundary this closes

Throughout the V3 proof, the refinement *solver* — Lark's from-scratch QF-UFLIA
decision procedure (congruence closure + Omega under DPLL(T), no Z3) — is
__modeled, not proven__. `SubBase` takes the predicate implication `Π n. IsTrue
(p n) → IsTrue (q n)` as a *given hypothesis*: the proof says "*if* the solver's
verdict is correct, subtyping is sound." PROVE.md names this the "solver is
modeled" / "equality seam" boundary. This strand would discharge that hypothesis:
prove the decision procedure itself sound, so `SubBase`'s premise becomes a
*theorem* instead of an assumption.

### Scope decision (to make before writing)

The full solver is congruence closure + Omega. Proving *both* in lcore from scratch
is a large project. Proposed staging, smallest-first:

1. __Congruence closure, soundness only__ (was B1, NOT yet built). Model terms as a
   `data Term` (vars, app, a few uninterpreted functions), a union-find state as a
   `Fin`-indexed telescope, and prove: if CC reports `a ≐ b`, then `a` and `b` are
   equal in every model (a `Π`-quantified interpretation). Soundness is the half
   that guards against *false* proofs; completeness (it finds every equality) is
   decidability, deferrable. Orthogonal to the interval fragment already done —
   this is the equational (uninterpreted-function) half of QF-UFLIA.
2. __Full multi-variable Omega__ (the deep end of B2, NOT yet built). The interval
   fragment done above is the single-variable slice. General Omega proves a
   satisfying assignment for a conjunction of `Σ aᵢ xᵢ ≤ b` constraints, and backs
   an `UNSAT` verdict with a Farkas-style nonnegative combination witnessing
   `0 < 0`. Full elimination (dark shadow / splinters) is the far deep end.
3. __Wider bridge__ (the single-variable bridge is DONE — `sub_fixture`). Extend
   the discharge from interval refinements to CC- and multi-variable-backed
   `SubBase` premises as 1 and 2 land.

### Why lcore can likely carry this

Unlike DESCEND, none of this needs positive `Step` inversion or `Ctx`-refinement
under `indrec Expr`. It is arithmetic and equational reasoning over first-order
`data` types — `natrec`/`indrec` over `Term`, `List`, `Fin`, plus `Id`/`J` for the
equational core. That is squarely inside what lcore already does in the metatheory.

### Risks / open questions

- __Model choice.__ Interpretations over `Nat` vs `Int`. The spine uses `Nat`
  payloads (the ℤ-vs-32-bit boundary is already named and deliberate); Omega wants
  `Int`. Decide whether to prove over `Nat` (matching the spine) or introduce a
  `data Int` and pay the sign-handling cost.
- __State representation.__ Union-find in a purely functional kernel: a list of
  parent-pointers indexed by `Fin n`, or an explicit equivalence-relation object?
  The latter proves more cleanly but is further from the real `adversary.py`/solver.
- __How faithful to the real solver?__ A pedagogical re-derivation (prove *a*
  sound CC/Omega) vs a proof *about the actual Python solver's algorithm*. The
  former is achievable; the latter needs a model of the real code and is closer to
  a full verification project. Recommend the former, clearly labelled.

### Definition of done (staged)

- __Interval fragment + bridge__ DONE — `leB` proven sound/complete, `sub_ge`
  emits certificates, `sub_fixture` discharges the real `rge2 ⊆ rge1` seam, 4/4
  controls refused. This is the strand's floor, and it converts the spine's actual
  `SubBase` hypothesis into a theorem.
- __CC-soundness__ DONE — `cc_sound : Cong a b → Id (eval a) (eval b)` in every
  model of the axioms, by `indrec Cong`; `cc_smoke_sem` reifies `f(f a) = a`; 4
  controls refused. The equational (UF) half of QF-UFLIA is now proven sound.
- __Multi-variable Omega__ ◻ when linear-SAT-soundness + a Farkas UNSAT witness typecheck.
- __CC completeness__ ◻ (decidability — CC finds *every* entailed equality). Soundness
  is the half that guards against false proofs; completeness is deferrable.

Both QF-UFLIA cores — the interval LIA fragment and CC soundness — now stand proven,
each closing the "solver modelled, not proven" seam for its half. Full multi-variable
Omega and CC completeness widen them to the rest of QF-UFLIA and are optional
deepenings, not prerequisites for the seam the spine uses.
