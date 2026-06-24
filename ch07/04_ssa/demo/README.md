
## SSA Pipeline in Python

A compact, all-in-one Python demonstration of the §7.4 idea, meant to be read
top to bottom. Where the [`../compiler/`](../compiler/) version is a real C
program over a C subset, this one strips everything to the bone so each stage of
the static-single-assignment pipeline fits on a screen.

`compiler.py` runs and prints these stages in order:

1. **Parse** a tiny program into three-address code (non-SSA), one basic block.
2. **Convert to SSA** — each assignment to a variable gets a fresh version
   (`x_1`, `x_2`, …) and every use is rewritten to name the version it reads.
3. **Optimise over SSA** — constant propagation and folding, then dead-code
   elimination. Single-definition form is what makes these almost trivial.
4. **Generate code** for a small stack machine (the PL/0-style `Operation`
   interpreter at the top of the file), merging SSA versions back to one slot per
   original variable.
5. **Execute** the generated code and print the final variable values.

### Running

```bash
python3 compiler.py
```

No input or arguments — the example program is built into `main`. The output
walks through the IR, the SSA form (with versioned names), the optimised SSA, the
generated stack-machine instructions, and the final values.

The `BasicBlock`/`IRInstruction` types carry a `PHI` form and `phi_sources`, so
the data structures are ready for φ-functions at merge points; this demo keeps to
a single block to make the versioning and the optimisations easy to follow.
