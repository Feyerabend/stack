
## Chapter 11 — Correctness

Companion code for Chapter 11 of *The Language Stack: From Silicon to Semantics*.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `02_hoare/` | §11.2 Hoare Logic | `vcgen.py` / `vcgen_enhanced.py` — annotate programs with pre/postconditions and loop invariants and generate the verification conditions; `demo.py` |
| `05_testing/` | §11.5 Testing a Compiler | `testing_methods.py` — differential, property-based, and fuzzing on one tiny language, each finding a bug the others structurally miss |

`verification/` (supplementary, no dedicated chapter section) holds the
automated-reasoning middle of the spectrum between §11.5's testing and §11.3's
proof: `z3/` symbolic execution with the Z3 SMT solver — the engine that
*discharges* the verification conditions `02_hoare/` generates; `model/` model
checking; `presburger/` a decision procedure for Presburger arithmetic.

**Lark's own correctness results are referenced by path, not duplicated here.**
The machine-checked type-soundness proof is `lark/formal/proof/`
(`lark-{typing,subst,step,preservation}.lcore`, checked by the `lcore` kernel in
`code/core/`) with the formal specification `lark-formal.tex`, discussed in
§11.3–§11.4. The tests that guard the compiler are `lark/06/tests/`
(`diff_test.py`, `gen.py`), discussed in §11.5.

§11.1 (the three meanings of "correct") and the type-safety *argument* of §11.3
are conceptual. The dependent-types material that §11.6 only glimpses — the proof
kernels, MLTT/HoTT, linear logic — now lives with Chapter 12, which teaches that
rung in full: see `ch12/`.
