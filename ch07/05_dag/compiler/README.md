
## Common-Subexpression Elimination via a DAG

Two compilers for the same tiny language, compared head to head, to show what the
DAG of §7.5 buys you. Both target the small PL/0-style stack machine defined at
the top of the file; the difference is only in how they treat repeated
computation.

- **`NaiveCompiler`** walks each assignment's expression as a tree and emits code
  for every node — so a subexpression that appears three times is computed three
  times.
- **`DAGCompiler`** first builds a DAG over *all* the assignments, sharing
  identical computations by value numbering. A shared interior computation is
  evaluated **once**, spilled to a temporary slot, and loaded back on each later
  use — which is precisely how a real compiler implements common-subexpression
  elimination: the value lives in a register or memory cell rather than being
  recomputed.

`compiler.py` compiles the example program with both, prints the generated code,
and then **runs both on the interpreter and checks the results are identical** —
the non-negotiable property of any optimisation: it may not change what the
program computes.

### Running

```bash
python3 compiler.py
```

The example assigns `3 + 5` three times. The report counts **arithmetic
operations** performed, which is the honest measure of CSE: the DAG compiler does
the `+` twice instead of four times (a 50% saving on real work), while every
variable ends with the same value under both compilers.

> Raw instruction count is a poor yardstick on this stack machine — spilling a
> trivial constant expression to a slot and loading it back can cost as much as
> recomputing it. CSE pays when the shared work is substantial; the metric here
> counts that work, not the bookkeeping around it.

The pure AST→DAG construction, without code generation, is in
[`../simple/`](../simple/).
