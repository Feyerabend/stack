
## Chapter 2 — C parallel of the stack VM

A C twin of `ch02/stack_vm.py`: the same fifteen-instruction stack machine, the
same bytecode, the same results — built so the dispatch discussion of
Section 2.4 can be *measured*, and so the Python VM has a second
implementation to check against.

| File | What it contains |
|------|------------------|
| `stack_vm.c` | The VM, implemented three ways: comparison cascade, `switch`, and computed `goto`. Shared operation macros keep the three semantically identical. Runs three sample programs and benchmarks the dispatchers on `sum 1..N`. |
| `Makefile` | `-O2 -std=gnu11` build plus `run` / `bench` / `check` / `diff` targets. |

The Python snapshot this mirrors is `ch02/stack_vm.py`.

### Run

```
make run            # samples + benchmark at N = 20,000,000
make bench          # benchmark at N = 50,000,000
make check          # correctness gate (nonzero exit on any mismatch)
make diff           # differential oracle: C vs Python on the same sum
./stack_vm 1000000  # pick your own N
```

### Why three dispatchers

- *comparison cascade* — the C analogue of Python's `if`/`elif`: a chain of
  equality tests, O(n) in the number of opcodes.
- *`switch`* — a dense switch the compiler turns into a jump table: one load
  plus one indirect branch.
- *computed `goto`* — a GCC/Clang extension (`&&label`, `goto *p`): each
  handler ends with its *own* indirect branch, giving the branch predictor a
  per-opcode history. Falls back to `switch` where the extension is unavailable.

Typical result (`-O2`, `N = 50,000,000`): computed goto is ~20% faster than
`switch`, which is barely ahead of the cascade. This is the ordering the chapter
predicts — and the opposite of what `solutions/ex05_dispatch.py` finds in
CPython, where dispatch is dominated by host-interpreter overhead. See
`../solutions/solutions.md`, Exercise 5.

### Differential oracle

`stack_vm.c` runs the *same* bytecode as `stack_vm.py` and matches its DIV
semantics (floor division, not C truncation), so the two implementations are
required to produce identical output. `make diff` shows it on `sum 1..300000`;
both print `45000150000`. Running the same program on two independent machines
and demanding identical output is the differential-testing idea the book returns
to in Chapter 11.
