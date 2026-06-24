
## An SSA Compiler in C

A small source-to-source compiler that takes a C-like program on standard input,
puts it into *static single assignment* (SSA) form, runs a few SSA-based
optimisations, lowers back out of SSA, and prints C again. It is the companion to
§7.4: where the book explains why SSA makes data-flow questions trivial — every
value is defined exactly once, so "which definition reaches this use?" has a
one-word answer — this builds the whole transform on a little IR.

`ssa_compiler.c` is a single file that runs the full pipeline:

1. **Lexing + parsing** of a tiny C subset (`int` functions, assignments,
   `if`/`else`, `while`, `return`).
2. **Control-flow graph** construction — basic blocks and edges.
3. **Dominator tree**, the prerequisite for placing φ-functions.
4. **SSA construction** — variables are versioned (`x_1`, `x_2`, …) and a
   **φ-function** is inserted at each merge point where two versions meet.
5. **SSA-based optimisation** — constant propagation, copy propagation, dead-code
   elimination.
6. **SSA deconstruction** — φ-functions are removed (copies on the incoming
   edges) and code is generated back to plain C.

### Running

```bash
gcc -std=c99 -o ssac ssa_compiler.c       # or: make
./ssac < simple_test.c                     # print the optimised C
```

Or drive the bundled tests, which compile each program's output and run it:

```bash
make test     # build, compile each *_test.c, run, report exit code
make demo     # show constant folding and phi-function placement side by side
make clean
```

The three test programs exercise the interesting cases:

| File | What it shows |
|------|---------------|
| `simple_test.c` | constant folding — `5 + 10` becomes `15` (returns 15) |
| `phi_test.c` | a φ-function at the merge of an `if`/`else` that assigns the same variable on both arms |
| `comprehensive_test.c` | the full pipeline over a larger program |

> **Lark does not build SSA.** As the book notes, Lark's Phase-5 compiler reaches
> the register allocator by the simpler road — backward liveness analysis
> (`lark/05/src/liveness.py`) feeding a linear-scan allocator (Chapter 9). SSA is
> here because it is the idea you must know to read any serious compiler, not
> because Lark uses it.
