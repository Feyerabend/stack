# Chapter 9 — Solutions

Solutions to the exercises in Chapter 9, *Code Generation*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|---|---|---|
| 1 (`n == 0` to fewest instrs) | analysis below | — |
| 2 (register sharing / spill) | `ex02_regalloc.py` | `python3 ex02_regalloc.py` |
| 3 (linear scan vs colouring) | `ex03_linear_vs_color.py` | `python3 ex03_linear_vs_color.py` |
| 4 (tail call → jump) | `ex04_tail_call.py` | `python3 ex04_tail_call.py` |
| 5 (the 6502 contrast) | analysis below | — |

The code drives Lark's real back end (`lark/05/src`: `regalloc.py`, `asm.py`) and
the chapter's register-allocation companion (`ch09/03_register_allocation`).

---

## Exercise 1 — `n == 0` in the fewest instructions

The naive selection was five instructions:

```
mv   t0, s10        # n into scratch
li   t1, 0          # zero
sub  t2, t0, t1     # n - 0
seqz t2, t2         # (n == 0)
mv   s9, t2         # result
```

**(a)** RISC-V has a hardwired zero register (`x0`/`zero`) and a
branch-if-equal-zero, so the comparison-and-branch is **one** instruction:

```
beqz s10, .then        # branch to the then-arm if n == 0
```

(or `beq s10, x0, .then`). No scratch moves, no materialised zero, no `seqz`: the
branch reads `n` directly from its register and tests against the hardwired zero.

**(b)** The `mv` chain is removed by **copy propagation** (Chapter 8) — folding
`mv t0, s10` so later uses read `s10` directly — together with the peephole that
fuses compare-and-branch. The right stage is **instruction selection / a peephole
pass after it**, not the IR. The redundant moves do not exist in the TAC; they are
*introduced* by the selector's "load each operand into a scratch register"
pattern. An IR-level copy-propagation pass therefore never sees them. They must be
cleaned up where they are born — at or just after selection — which is exactly
where the register allocator's move coalescing (Section 9.3) and a peephole would
act.

---

## Exercise 2 — Register sharing and spilling

**(a)** From Lark's allocator (`ex02_regalloc.py` reads the real intervals):

```
t0 -> s9   [0, 1]
r4 -> s9   [2, 12]
```

`t0` is last used at point 1; `r4` is first defined at point 2. The intervals
`[0,1]` and `[2,12]` **do not overlap**, so `s9` holds `t0` first and then `r4` —
the script confirms `t0.overlaps(r4)` is `False`.

**(b)** Real functions rarely need more than eleven `s`-registers, so — exactly as
the chapter's companion does (`ch09/03_register_allocation` uses `k = 3`) — the
script models scarcity by allocating `sum_to` from a small register set. With too
few registers, linear scan **spills the latest-ending interval** among those
competing, because it is the one most likely to keep a register tied up while
shorter intervals come and go. Here `r4` (`[2,12]`) ends latest, so it is the
first sent to a stack slot.

**(c) The condition:** two temporaries may share one register **iff their live
intervals do not overlap** — equivalently, they are never simultaneously live (no
edge between them in the interference graph).

---

## Exercise 3 — When linear scan loses to graph colouring

**(a) Why "latest-ending."** When a register must be freed, evicting the interval
that ends *latest* frees a register for the longest remaining span — it removes
the interval most likely to block future allocations. "Earliest-ending" would
evict an interval that was about to release its register anyway (pure waste).
"Always spill the current interval" ignores that the current one may be short and
cheap to keep, while a long-lived active interval keeps causing pressure;
spilling the long one can prevent further spills. Latest-ending is the greedy
choice that keeps the most registers usefully busy.

**(b) Where linear scan is worse — a live range with a hole.** Linear scan models
each temporary as one **contiguous** interval `[first use, last use]`, so a value
that is live, dies, and is live again is treated as live across the gap. Graph
colouring on the *true* interference sees the gap is free. Take `a` live at
`{0,1}` and `{5,6}` (dead 2–4), and `b` live at `{2,3,4}` — entirely inside a's
gap:

- Linear scan sees `a = [0,6]`, `b = [2,4]`; they overlap, so with **one**
  register it must spill one of them.
- True interference: `a` and `b` are never live together, so they don't interfere;
  colouring fits both in **one** register, no spill.

`ex03_linear_vs_color.py` runs the chapter's companion `linear_scan` and `colour`
on exactly this case at `k = 1`: linear scan spills 1, graph colouring spills 0
(and `a`, `b` share the single register). Linear scan: 2 registers (or 1 spill at
k=1); optimal: 1 register, 0 spills.

---

## Exercise 4 — The tail call as a jump

`ex04_tail_call.py` reads the real emitted assembly.

**(a) The stack pointer.** The prologue runs `addi sp, sp, -32` **once**, before
the `.sum_to_loop:` label. Each iteration jumps back to that label (below the
prologue), and the iteration body contains **no `addi sp` and no `call`**. So
`sp` is set once and never moves: across a million iterations the stack stays at
constant depth. A `call` would instead push a return address (and a fresh frame)
per iteration — `sp` would descend a million frames deep and overflow.

**(b) No overflow.** The recursive evaluator (Chapter 6) recursed in the host and
grew the host stack per call until it overflowed. The compiled tail call is a
**back edge**: the else branch jumps to the function's own loop label instead of
calling, so the recursion is a loop in bounded stack space — the cycle lives in
the control-flow graph, not on the call stack.

**(c) Mutual tail recursion.** Lark's transform only rewrites a tail call to the
**same** function (it jumps to *this* function's loop label). `is_even`'s tail
call is to `is_odd` — a different function with a different entry — so there is no
local label to jump to, and Lark emits a real `call` (the script confirms
`call is_odd`). A general tail-call optimization would have to turn *any* tail
call into a jump that **reuses the current stack frame** instead of pushing a new
one: move the arguments into the convention's registers and `j is_odd` with no
`call`/return (or route through a trampoline). That requires a uniform tail-call
protocol across functions, which Lark's simple self-loop rewrite does not provide.

---

## Exercise 5 — The 6502 contrast

**(a) `sum_to`'s loop body on the 6502.** The 6502 has one 8-bit accumulator `A`
and two narrow index registers; arithmetic goes through `A`, and operands live in
zero-page memory. With `acc` and `n` at zero-page addresses, one iteration of
`acc = acc + n; n = n - 1` is roughly:

```
LDA acc        ; A <- acc           (load)
CLC
ADC n          ; A <- acc + n       (load n)
STA acc        ; acc <- A           (store)
LDA n          ; A <- n             (load)
SEC
SBC #1         ; A <- n - 1
STA n          ; n <- A             (store)
```

**(b) Memory accesses per iteration.** Each `LDA`/`ADC`/`SBC`/`STA` of a zero-page
location is a memory access: here `LDA acc`, `ADC n`, `STA acc`, `LDA n`,
`STA n` — **five** data accesses per iteration (more once the loop counter test
and branch touch memory). The RISC-V version keeps `acc` and `n` in registers
`s10`/`s11` for the whole loop: **zero** data-memory accesses per iteration.

**(c) The property and the lesson.** The 6502 has **too few registers, and only
one that does arithmetic**, so values cannot stay in registers across a loop —
they must shuttle through memory, and memory traffic dominates. The general lesson
is that an instruction set and its compiler are co-designed: a register-rich,
orthogonal load-store ISA (RISC-V) lets the compiler keep working values in
registers and makes register allocation the lever that matters; a register-poor
ISA forces the compiler into memory traffic no allocator can remove. The same
high-level program, the same algorithm, costs orders of magnitude more on the
machine whose architecture denies the compiler registers to work with.
