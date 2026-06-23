
## Chapter 08 — Optimization

Companion code for Chapter 8 of *The Language Stack: From Silicon to Semantics*.
Organised by section; each folder matches a §8.x heading in the book.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `01_meaning/` | §8.1 Meaning Preservation | `equiv_check.py` — a local differential oracle: a sound rewrite passes, a wrong one (`x - x => x`) is caught with a counterexample |
| `02_constant_folding/` | §8.2 Constant Folding and Propagation | `constant_fold.py` (evaluate constant operands at compile time) and `propagator.py` (substitute known constants forward); the two cooperate to a fixed point over a basic block |
| `03_dead_code/` | §8.3 Dead Code and Reachability | `dead_code.py` (remove computations whose results are never used) and `reachability.py` (mark the blocks reachable from the entry; the rest are dead) |
| `04_simplification/` | §8.4 Expression Simplification | `expression_simplifier.py` (algebraic identities — `x+0`, `x*1`, `x*0`, `x-x` — and strength reduction by a table of rewrites) |
| `05_licm/` | §8.5 Loop-Invariant Code Motion | `licm.py` — finds computations whose operands don't change across iterations (to a fixed point) and hoists them into a preheader |
| `06_measuring/` | §8.6 Diminishing Returns | `lark_bench.py` times `sum_to` across Lark's three backends (the honest "compiled isn't faster in a simulator" lesson), plus benchmarked naïve-vs-optimised C/Python examples |

The Lark snapshot for this chapter is `lark/06` — the hardening phase. Section
§8.1's meaning-preservation *oracle* is Lark's own differential-testing harness,
`lark/06/tests/diff_test.py`: every program is run through the CEK interpreter,
the TAC VM, and the RV32 VM, and their outputs must be byte-identical.

Every section §8.1–§8.6 now has a runnable companion. Each folder has its own
README; the `.py` files run standalone with no arguments (`lark_bench.py` drives
the real `lark/06` backends and takes ~30s).

> The classic optimizations Lark itself applies live in its back end, not here:
> move coalescing (`lark/05/src/regalloc.py`) and tail-call elimination
> (`lark/05/src/asm.py`), both discussed in Chapter 9. Lark performs no
> TAC-level optimization pass — §8.6 explains why.
