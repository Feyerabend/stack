# Chapter 8 — Solutions

Solutions to the exercises in Chapter 8, *Optimization*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|---|---|---|
| 1 (constant folding/propagation) | `ex01_const_fold.py` | `python3 ex01_const_fold.py` |
| 2 (merge variable / coalescing) | analysis below | — |
| 3 (reachability needs folding first) | `ex03_reachability.py` | `python3 ex03_reachability.py` |
| 4 (`x + 0.0` unsound) | `ex04_float_zero.py` | `python3 ex04_float_zero.py` |
| 5 (diminishing returns) | analysis below | — |

Lark performs **no** TAC-level optimization, so the passes here are written over
Lark's real lowered TAC (`lark/06/src`) the way the chapter's companion folders
illustrate them.

---

## Exercise 1 — Constant folding and propagation

**(a)** Lark lowers `let x = 2 + 3 in let y = x * x in y + x` (folding nothing) to
three `IBinOp`:

```
t0 = 2 + 3
t1 = t0 * t0      # x is reused as t0
t2 = t1 + t0
return t2
```

**(b)** Folding + propagation to a fixed point (`ex01_const_fold.py` prints each
step):

```
t0 = 2 + 3   -> t0 = 5      (both operands constant)
t1 = t0 * t0 -> t1 = 25     (t0 known = 5)
t2 = t1 + t0 -> t2 = 30     (t1 = 25, t0 = 5)
return t2    -> return 30   (propagate the constant)
```

Dead-code elimination then drops `t0`/`t1`/`t2`. Final body: `return 30` — zero
`IBinOp`, zero `IAssign`. Each fold *triggers the next* by adding a new known
constant to the table (`t0=5` enables folding `t1`, which enables `t2`).

**(c) Property.** Compile-time evaluation of `+`/`*` must give the *same* result
as run time — the op must be a pure, total, deterministic function whose host
(compiler) semantics match the target exactly. For 32-bit `Int` this holds:
two's-complement `+`/`*` are exact and wrap identically at compile and run time,
no rounding, no special values. For `Float` it needs care — IEEE-754 has rounding
modes, NaN, and signed zero, so the compiler's host float must match the target
bit-for-bit or folding changes results (Exercise 4).

---

## Exercise 2 — The merge variable and move coalescing

**(a)** Local copy propagation cannot replace `return r4` with a branch's value
because `r4` is a **merge variable with two reaching definitions**: `r4 = acc` (in
the then-block) and `r4 = t7` (in the else-block). At the merge block `.end3`,
`r4` is live-in with no single defining instruction *in that block*; a local
(intra-block) pass sees only `.end3` and cannot know which definition reached it.
Neither `acc` nor `t7` is correct on both paths, so no local substitution is
sound — the unsound rewrite would be wrong on whichever branch it did not come
from.

**(b)** The non-local rewrite **sinks the return into both branches**: replace
`r4 = acc; goto .end3` with `return acc`, and `r4 = t7; goto .end3` with
`return t7`, deleting `r4` and the merge block `.end3` entirely. The result is a
two-exit function:

```
entry:   if n == 0 goto then else else
then:    return acc
else:    t7 = call sum_to(n-1, acc+n) ; return t7
```

**(c)** Lark does neither, leaving `r4` for the register allocator's **move
coalescing** (Chapter 9). Coalescing gives `r4` and the branch temporaries the
*same physical register*, so `r4 = acc` and `r4 = t7` become
register-to-itself moves and vanish — eliminating the copies' run-time cost while
keeping the single-exit structure. What coalescing achieves that the IR rewrite
does not: zero-cost copies **without changing control flow** (and it also catches
copies the IR pass never sees). What the IR rewrite achieves that coalescing does
not: it removes the merge block and temporary **structurally** (fewer blocks,
two clean exits), which coalescing — operating within the given control-flow
graph — cannot do.

---

## Exercise 3 — Reachability must run after folding

**(a)** `fn g(io) = if true then 1 else 2` lowers to a CFG with four blocks; the
else block (`.else1`) can never execute, yet it is present (`ex03_reachability.py`
confirms all four are reachable before folding).

**(b)** Lark's lowerer **folds no constants**, so it lowers `true` to a real `Val`
and emits `ICondJump(true, .then0, .else1)` — a genuine two-target branch. Both
targets therefore receive an incoming edge.

**(c)** A plain reachability pass keeps `.else1`, because the `ICondJump` still
gives it an edge. Only after constant folding rewrites
`ICondJump(const true, T, F)` into the unconditional `IJump(T)` does `.else1`
lose its incoming edge — and only *then* does reachability from the entry see it
as dead and delete it. The script shows it: **before fold** all 4 blocks
reachable; **after fold + reachability** `.else1` is gone (3 blocks). Folding must
run first.

---

## Exercise 4 — `x + 0.0` is unsound for floating point

**(a)** The failing value is **`x = -0.0`** (negative zero). Under IEEE-754,
`(-0.0) + 0.0 == +0.0` (addition normalises the sign of zero), so the original
expression yields **`+0.0`** while the rewritten `x` yields **`-0.0`**. They
compare `==` but differ observably: the sign bit differs, and
`1.0 / (+0.0) = +inf` while `1.0 / (-0.0) = -inf`.

**(b)** The **differential oracle** runs the program before and after the rewrite
on the same input and compares output. A program printing `1.0 / (x + 0.0)`
outputs `inf`; after the unsound rewrite to `1.0 / x` it outputs `-inf`. The
outputs differ, so the oracle rejects the rewrite with a concrete counterexample
(`x = -0.0`) — no appeal to aesthetics. (`ex04_float_zero.py` exhibits exactly
this divergence.)

**(c)** The difference: **`Int` has no negative zero, no NaN, and no rounding** —
every value has one representation and `+` is exact two's-complement, so
`x + 0 == x` bit-for-bit. `Float`'s signed zero (plus NaN and rounding for
non-zero addends) is what makes the *same-looking* identity unsound: an
equivalence that holds in the real numbers fails in IEEE-754.

---

## Exercise 5 — Diminishing returns

**(a)** For `sum_to`, each CEK iteration does interpretive work the compiled loop
does not. Three costs the compiled code never pays:

1. **Environment allocation** — the CEK machine builds a fresh environment
   (a heap dict) for each call/`let`; the compiled loop keeps `n` and `acc` in
   registers, allocating nothing.
2. **Dispatch / interpretation overhead** — every step pattern-matches on the
   node kind and pushes/pops continuation frames on the `kont` list; the compiled
   loop is a handful of straight RISC-V instructions with a single branch.
3. **Boxing** — CEK values are heap objects (`VInt`, …) reached by pointer; the
   compiled loop holds raw machine words in registers, with no allocation or
   indirection per arithmetic op.

(Add variable lookup by dict hashing, and continuation-frame management.) These
are *per-iteration* costs, so the interpreter is slower by a large constant factor
on every loop — the jump a single fold cannot approach.

**(b)** Whether to add constant folding to Lark, by the chapter's two criteria:

- **Measurable benefit.** Lark targets a simulator and a teaching pipeline; the
  interpreter→compiler jump already dominates, and §8.6's measurements show the
  compiled code is not even faster than the interpreter *in the simulator*.
  Folding `2 + 3` removes work that is negligible against that backdrop, so the
  measurable benefit is near zero for Lark's actual targets. (On real hardware, in
  hot loops with constant subexpressions, folding + LICM can remove genuine
  per-iteration work — there the benefit is measurable.)
- **Demonstrable correctness.** Int folding is sound and the differential oracle
  can confirm it cheaply; Float folding risks the `x + 0.0` class of bugs and
  needs bit-exact host/target arithmetic to stay sound.

For Lark, both criteria point the same way: **decline** — the benefit is
unmeasurable on its targets and even the safe (Int) case buys nothing visible, so
the added pass and its oracle obligations are not worth it. The decision is made
on benefit and correctness, not on whether folding "looks like what a compiler
should do." A production compiler for real hardware would clear both bars and
should fold.
