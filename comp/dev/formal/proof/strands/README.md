
## strands/ — three climbs past the V3 summit

The V3 upward axis (the step-indexed logical relation in `../lark/lark-refine.lcore`)
reached its summit and then hit a wall: __DESCEND__ — flipping the relation from
the ∃-form (total correctness) to the ∀/safety form — needs *positive `Step`
inversion inside `indrec Expr`*, which lcore cannot express (it cannot refine the
`Ctx` index to `empty` under the eliminator). It is also *unnecessary*: Lark is
strongly normalizing (STLC, no recursion), so the ∃-form already IS the stronger
statement and the ∀-form's "safe under divergence" is vacuous. That boundary is
recorded in `../../../LOG.md` (entry `V3-DESCEND-WALL`) and `../../../PROVE.md`.

These three strands are the *other* ways up — each attacks or dodges a different
boundary rather than the one that walled off DESCEND. They are exploratory: the
main proof (`make check`, 5 files / 0 errors) never depends on them.

For how the three fit together — the single question they all answer, in three
target languages, and why none re-hits the wall — see [`SUMMARY.md`](SUMMARY.md).

| strand | idea | boundary it addresses | status |
|--------|------|-----------------------|--------|
| __denot__ | interpret refinement types as lcore *types*; prove soundness by recursion on the derivation, never eliminating the operational `Step` relation | dodges the DESCEND wall entirely (nothing operational to invert) |  __complete__ — subtyping soundness + full fundamental lemma (all 8 rules, both λ-introductions wall-free); 4/4 controls refused |
| __solver__ | prove the refinement *checker's* decision procedure sound against the model | the "equality seam" / "solver is modeled, not proven" boundary named in PROVE.md | ◐ __both QF-UFLIA halves proven__ — LIA: `leB` sound+complete, `sub_fixture` discharges the real `rge2 ⊆ rge1` seam. UF: `cc_sound` — congruence closure sound in every model; 8/8 controls refused. Full multi-var Omega + CC completeness remain as *width* (`solver/PLAN.md`) |
| __vdeep__ | elaborate Lark refinement derivations *into* MLTT (lcore) terms — a verified translation, not just a semantic model | the gap between "Lark has a checker" and "Lark's types ARE proofs" |  __complete__ — `elab : HasR → MTm` (intrinsically-typed MLTT), all 8 rules incl. function-subtyping coercion via intrinsic renaming (`mweaken`); showcase smokes compute concrete terms; 4/4 controls refused. Did NOT re-hit the DESCEND wall |

### Running

```
make denot            # the denotational strand, its own green bar (6 files / 0 errors)
make denot-controls   # its negative controls: OK = 4/4 refused
make solver           # the solver strand (6 files / 0 errors)
make solver-controls  # its negative controls: OK = 8/8 refused
make vdeep            # the elaboration strand (6 files / 0 errors)
make vdeep-controls   # its negative controls: OK = 4/4 refused
make check            # the untouched main summit (5 files / 0 errors)
```

### Order

Agreed with Set: __denot → solver → vdeep__. The denotational model was the
natural first climb (wall-free, and it re-proves the whole refinement calculus far
more cleanly than the operational relation). `vdeep` is last by preference — it is
the most interesting and the most open-ended, so it gets the most runway.

If solver / vdeep don't complete, their `PLAN.md` files stand on their own as
reviewable designs — that is the point of keeping them here.
