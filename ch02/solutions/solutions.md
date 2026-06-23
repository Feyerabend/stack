
## Chapter 2 — Solutions

Solutions to the exercises in Chapter 2, *A Virtual Machine in Software*, of
*The Language Stack: From Silicon to Semantics*.

All five exercises are code-bearing; each script is runnable and self-checking.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (`MOD` instruction) | `ex01_mod.py` | `python3 ex01_mod.py` |
| 2 (trace `fact(3)`) | `ex02_trace.py` | `python3 ex02_trace.py` |
| 3 (iterative factorial) | `ex03_iterative_fact.py` | `python3 ex03_iterative_fact.py` |
| 4 (caller/callee-saved split) | `ex04_callee_saved.py` | `python3 ex04_callee_saved.py` |
| 5 (dispatch strategies) | `ex05_dispatch.py` | `python3 ex05_dispatch.py [N]` |

The scripts import the chapter's companion modules (`stack_vm.py`,
`assembler.py`, `reg_vm.py`) from the parent directory.



### Exercise 1 — Add a `MOD` instruction

> Add a `MOD` instruction (pop `b`, pop `a`, push `a % b`) to the stack VM. Give
> its opcode number, the dispatch branch that implements it, and the entry it
> needs in the assembler's `WIDTHS` table.

Three additions, all in `ex01_mod.py`:

1. *Opcode number:* `MOD = 15` — the next free value after `RET = 14` in the
   base fifteen-instruction VM. (The chapter's `LOADK` and `JMPIND` extensions
   reuse 15/16, but those are separate VMs; a unified machine would simply renumber.)

2. *Dispatch branch* (mirrors `ADD`/`SUB`, no operand byte):

   ```python
   elif op == MOD:
       b = self.stack.pop()
       self.stack[-1] %= b
   ```

3. *`WIDTHS` entry:* `15: 1`. `MOD` carries no operand, so its instruction is
   one byte wide — exactly like `ADD`. It also needs `'MOD': 15` in the assembler's
   `OPCODE` map.

Why the `WIDTHS` entry matters: the assembler's first pass sums instruction
widths to compute label addresses. If `MOD`'s width were missing or wrong, every
label *after* a `MOD` would be off, and a `JMP` to such a label would land in the
middle of an instruction. `ex01_mod.py` proves the entry is right by assembling a
program with a `JMP` over code, *past* a `MOD`, and confirming it computes
`17 % 5 = 2`:

```
$ python3 ex01_mod.py
17 % 5 = 2  (assembled, MOD width accounted for)
```



### Exercise 2 — Trace the operand stack at the deepest `CALL` of `fact(3)`

> The factorial passes its argument on the operand stack. Trace, value by value,
> what sits on the operand stack at the moment of the deepest recursive `CALL`
> when computing `fact(3)`. Explain why each multiplicand is still present when
> its `MUL` finally executes.

`ex02_trace.py` instruments the VM to snapshot the operand stack at every `CALL`:

```
operand stack at each CALL (outermost first):
  [3]
  [3, 2]
  [3, 2, 1]
  [3, 2, 1, 0]
deepest CALL operand stack: [3, 2, 1, 0]
```

*At the deepest `CALL`* — `fact(1)` calling `fact(0)` — the operand stack holds
`[3, 2, 1, 0]`:

- `3`, `2`, `1` are the *kept multiplicands*, one per still-active frame
  (`fact(3)`, `fact(2)`, `fact(1)`). Each was placed there by the *first*
  `LOAD 0` of the recursive case, just before that frame made its own recursive
  call.
- `0` is the *argument* being passed to `fact(0)`.

*Why each multiplicand survives until its `MUL`.* The recursive body is
`LOAD 0` (push n, the multiplicand) `… compute n-1 … CALL … MUL`. The `MUL`
runs only *after* the call returns. In between, the operand stack is preserved
across the whole sub-computation, because the call protocol never disturbs the
values beneath the argument: `CALL` leaves the operand stack untouched; the
callee removes *only* its argument with `STORE 0`; and `RET` pushes *one* return
value back. So the multiplicand a frame pushed is exactly where it left it when
control returns, ready for the `MUL`. The operand stack is, in effect, acting as
the spine of pending multiplications — the same role the machine's own call stack
plays for return addresses.



### Exercise 3 — Iterative factorial

> Rewrite the stack-VM factorial iteratively, with a loop and no recursion. Does
> your version use the call stack (`frames`) at all? What is the maximum
> operand-stack depth it reaches, and how does that compare with the recursive
> version?

`ex03_iterative_fact.py` implements `acc = 1; while 0 < n: acc *= n; n -= 1` in
bytecode, with `n` in `locals[0]` and `acc` in `locals[1]`:

```
$ python3 ex03_iterative_fact.py
fact(5) = 120  | frames used: 0  | max operand depth: 2
```

- *The call stack is never used.* There is no `CALL` or `RET`, so `frames`
  stays empty for the entire run (the script asserts `max_frames_depth == 0`).
- *Maximum operand-stack depth is 2*, and it is *constant* — it does not grow
  with `n`. The peak occurs while a binary operation has both operands pushed
  (e.g. `LOAD 1`, `LOAD 0` before `MUL`).
- *Comparison with the recursive version.* Recursion grows *both* stacks
  linearly in `n`: the operand stack reaches depth `n + 1` (the kept
  multiplicands plus the final argument — `[5,4,3,2,1,0]` for `fact(5)`, per
  Exercise 2), and `frames` holds one entry per active call. The iterative
  version replaces that *O(n)* space with *O(1)*. This is the canonical
  reason to turn recursion into a loop, and it foreshadows tail-call elimination
  in Chapters 6 and 9, which buys the same space saving *without* rewriting the
  source.



### Exercise 4 — A caller-saved / callee-saved split

> The register VM's `RCALL` zeroes every register. Modify `RCALL` and `RRET` to
> implement a caller-saved/callee-saved split: `r2`–`r7` may be clobbered by the
> callee, while `r8`–`r15` must be preserved across the call. Which registers
> does each instruction now copy, and where does the saved copy live?

`ex04_callee_saved.py` defines `RegVMSplit` with two changed branches:

```python
elif op == RCALL:
    target = self._u16()
    self.frames.append((r[8:16], self.pc))   # save ONLY r8-r15
    self.pc = target
elif op == RRET:
    rs = code[self.pc]; self.pc += 1
    val = r[rs]
    saved, self.pc = self.frames.pop()
    r[8:16] = saved                          # restore ONLY r8-r15
    r[1] = val                               # r2-r7 keep callee's values
```

- *`RCALL` copies only the eight callee-saved registers `r8`–`r15`* (plus the
  return `pc`). It does not touch `r2`–`r7`.
- *`RRET` restores those eight `r8`–`r15`* from the frame, writes the return
  value into `r1`, and restores the `pc`. It leaves `r2`–`r7` holding whatever
  the callee left in them.
- *Where the saved copy lives:* in the frame on `self.frames` (the call
  stack) — the same place the full 16-register copy lived in the original VM,
  but now it is an eight-element slice.

The script demonstrates both halves of the convention:

```
$ python3 ex04_callee_saved.py
split: after call  r2=7 (clobbered)  r8=200 (preserved)  OK
factorial(5) with n in callee-saved r8 = 120  OK
```

The first line is a direct test: a callee overwrites both `r2` and `r8`; after
the return, `r2` shows the callee's value (caller-saved, not restored) while
`r8` is back to the caller's (callee-saved, preserved). The second line is the
consequence for real code — a value that must survive a call has to live in a
callee-saved register, so the recursive factorial now keeps `n` in `r8`. (Note
that `reg_vm.py`'s version kept `n` in `r6` and only worked because that VM
saved the *entire* file; under a realistic split, `r6` would be clobbered.)



### Exercise 5 — Two dispatch strategies, timed

> Implement two dispatch strategies for the stack VM — the `if`/`elif` chain
> shown here and a dictionary mapping each opcode to a handler function — and
> time both on the sum-to-one-million loop. Which is faster under CPython? Does
> the ordering match the C intuition from Section 2.x, and if not, why might the
> host interpreter change the answer?

`ex05_dispatch.py` runs both VMs on `sum 1..N` and times them. They are *close —
within about 10% — and which one wins depends on the CPython version.* Example
run (CPython 3.14):

```
$ python3 ex05_dispatch.py 300000
sum 1..300000 = 45000150000  (both strategies agree)
  strategy             seconds
  if/elif chain          0.68
  dict dispatch          0.61
  faster: dict dispatch  (1.11x)
```

*Does it match the C intuition?* Not in magnitude, and the *sign* even shifts
across releases:

- In *C*, a dense `switch` compiles to a jump table — O(1) dispatch that
  clearly beats an O(n) comparison chain, with computed `goto` faster still.
  That is a large, reliable win.
- In *CPython*, the dict maps opcodes to *function objects*, so each dispatched
  opcode pays a Python-level *function call*. Historically that overhead made
  the `if`/`elif` chain *faster* than dict dispatch. Since 3.11, calls and dict
  lookups are heavily optimised (the adaptive specialising interpreter), so on
  3.14 the dict's O(1) lookup edges slightly *ahead* — the opposite of the old
  lore, and still nowhere near the C-style multiple-x win.

*Why the host interpreter changes the answer.* The per-opcode cost in Python
is dominated not by the branch logic but by interpreter overhead the two
strategies *share*: fetching the opcode byte, integer-boxing, and especially the
operand-stack memory traffic the chapter's profiling section calls out as the
real bottleneck. Whether dispatch is a chain or a table moves a small slice of
that total, and the host's evolving optimisations decide the sign. The honest
conclusion is the chapter's: *measure, don't assume* — dispatch is usually not
where the time goes.

*Seeing the C intuition actually hold.* The chapter's claim is about *C*, where
a `switch` becomes a real jump table and computed `goto` adds per-opcode branch
prediction. The companion `../c/stack_vm.c` is the same VM built all three ways
(comparison cascade, `switch`, computed `goto`) so you can measure it:

```
$ cd ../c && make bench
dispatch on sum 1..50000000 (best of 3, lower is better):
  strategy               seconds
  comparison cascade       0.601
  switch                   0.590
  computed goto            0.491
```

Here the C intuition holds: computed `goto` is ~20% faster than `switch`, which
edges the cascade. The contrast with the Python numbers above is the whole point
— *the same algorithmic choice pays off in C and barely registers in CPython*,
because the host interpreter's per-opcode overhead swamps it. And because
`stack_vm.c` runs the identical bytecode with identical (floor-division)
semantics, it doubles as a differential check on the Python VM: `make diff`
confirms both compute `sum 1..300000 = 45000150000`.
