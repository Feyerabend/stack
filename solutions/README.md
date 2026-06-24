
## Solutions

Worked solutions to the end-of-chapter exercises in
*The Language Stack: From Silicon to Semantics*.

Solutions live alongside the code they extend, in each chapter's companion repo
under `lang/chNN/solutions/`. This keeps the book lean and lets a solution evolve
(or get corrected) without a reprint. Each `solutions.md` restates every
exercise and gives a worked answer; exercises that call for code get a runnable,
verified script next to it.

| Chapter | Solutions | Code solutions |
|---------|-----------|----------------|
| 1 — Instruction Sets and Memory | [`ch01/solutions/`](../ch01/solutions/solutions.md) | `ex02_loop.py` (+ Ex.1 in `ch01/fde.py`) |
| 2 — A Virtual Machine in Software | [`ch02/solutions/`](../ch02/solutions/solutions.md) | `ex01_mod.py`, `ex02_trace.py`, `ex03_iterative_fact.py`, `ex04_callee_saved.py`, `ex05_dispatch.py` |
| 3 — Lexical Analysis | [`ch03/solutions/`](../ch03/solutions/solutions.md) | `ex01_number_exponent.py`, `ex02_underscore_idents.py`, `ex03_cmp_dfa.py`, `ex04_line_comments.py` |
| 4 — Parsing | [`ch04/solutions/`](../ch04/solutions/solutions.md) | `ex01_bool_rd.py`, `ex02_ll1_table.py`, `ex03_anbn.py`, `ex04_match_multi.py`, `ex05_sr_trace.py` |
| 5 — Names, Scope, and Types | [`ch05/solutions/`](../ch05/solutions/solutions.md) | `ex01_stlc_derivation.py`, `ex02_algorithm_w.py`, `ex03_occurs_check.py`, `ex04_affine_io.py`, `ex05_copy_trait.py` |
| 6 — A Working Interpreter | [`ch06/solutions/`](../ch06/solutions/solutions.md) | `ex01_trace.py`, `ex02_closure.py`, `ex03_tco_kont.py`, `ex05_io_affine.py` |
| 7 — An Intermediate Representation | [`ch07/solutions/`](../ch07/solutions/solutions.md) | `ex01_value_numbering.py`, `ex02_cfg.py`, `ex04_let_no_instr.py`, `ex05_closure_conv.py` |
| 8 — Optimisation | [`ch08/solutions/`](../ch08/solutions/solutions.md) | `ex01_const_fold.py`, `ex03_reachability.py`, `ex04_float_zero.py` |
| 9 — Code Generation | [`ch09/solutions/`](../ch09/solutions/solutions.md) | `ex02_regalloc.py`, `ex03_linear_vs_color.py`, `ex04_tail_call.py` |
| 10 — Abstract Machines | [`ch10/solutions/`](../ch10/solutions/solutions.md) | `ex03_apply_context.py`, `ex04_prolog.py`, `ex05_cbn_cbv.py` |
| 11 — Correctness | [`ch11/solutions/`](../ch11/solutions/solutions.md) | `ex02_03_proof_check.py`, `ex04_testing_methods.py`, `ex05_affine_io.py` |
| 12 — Types as Proofs | [`ch12/solutions/`](../ch12/solutions/solutions.md) | `ex01_curry_howard.py`, `ex02_dependent_types.py` |

### Conventions

- *Restate, then solve.* Every entry quotes the exercise before answering, so
  the file stands on its own.
- *Code is verified.* Each script has a top docstring (which exercise, how to
  run, expected output) and asserts its own result, so `python3 <script>.py`
  either prints the expected line or fails loudly.
- *Open-ended exercises* ("discuss…", "explain…") get a model answer plus a
  note on what a strong answer covers, rather than a single key.
