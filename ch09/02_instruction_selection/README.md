# §9.2 — Instruction Selection

`isel.py` — tree matching by *maximal munch*: at each node take the largest
machine-instruction "tile" that matches, then recurse on its leaves. A
RISC-V-flavoured tile set folds structure a naive one-instruction-per-node
selector would waste instructions on:

- `mem[a + 8]` — naive 3 instructions, munch **1** (`lw 8(a)`)
- `b*c + 1` — naive 3, munch **2** (`addi`)
- `x + 16` — naive 2, munch **1** (`addi`)

```
python3 isel.py
```

Lark's selector (`lark/05/src/asm.py`) is the naive kind, because TAC was built
to resemble RISC-V and there is little structure left to fold — §9.2 explains why
that is the right call for a load-store target.
