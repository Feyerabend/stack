
## Constant Folding over TAC

A first look at optimising the three-address code itself, rather than the source
or the AST. Once a program is in TAC, whole classes of optimisation become simple
rewrites over a flat instruction list — this folder previews two of them, and
Chapter 8 develops them as proper passes.

`folding.py` walks a TAC instruction list once and applies:

- **Constant folding** — an instruction whose two operands are both literals is
  replaced by its computed value (`t2 = 7 + 9` becomes `t2 = 16`). Folding is
  *local*: it does not propagate the new constant forward, so `t3 = 5 * t2` is
  left untouched even though `t2` is now known. Constant *propagation* — the pass
  that would feed the folded value onward — is taken up in Chapter 8.
- **Common-subexpression elimination** — the first time an expression like
  `a + b` is seen its result temporary is recorded in a symbol table; a later
  instruction computing the same expression is rewritten to reuse that temporary.

### Running

```bash
python3 folding.py
```

The script optimises a fixed example program (the TAC for
`z = (x + y) - (5 * (7 + 9)) / 2`, with `x = 2025`, `y = 1477`) and prints the
rewritten instruction list, showing `7 + 9` folded to `16`.

The DAG-based, value-numbering form of common-subexpression elimination lives in
[`../../05_dag/`](../../05_dag/); the differential oracle that keeps such rewrites
honest is the TAC VM described at the end of §7.7.
