
## Chapter 7 — Solutions

Solutions to the exercises in Chapter 7, *Intermediate Representations*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (lowering + value numbering) | `ex01_value_numbering.py` | `python3 ex01_value_numbering.py` |
| 2 (basic blocks / CFG) | `ex02_cfg.py` | `python3 ex02_cfg.py` |
| 3 (SSA) | analysis below | — |
| 4 (`let` emits no instruction) | `ex04_let_no_instr.py` | `python3 ex04_let_no_instr.py` |
| 5 (closure conversion) | `ex05_closure_conv.py` | `python3 ex05_closure_conv.py` |

The code drives Lark's real lowerer (`lark/05/src/{lower,tac,cfg}.py`) via
`_harness.py`.



### Exercise 1 — Lowering `(a + b) * (a + b)` and value numbering

*(a)* Lark emits the obvious instruction per node, so the expression lowers to
*three* `IBinOp` (`ex01_value_numbering.py` confirms it):

```
t0 = a + b
t1 = a + b
t2 = t0 * t1
return t2
```

*(b)* Local value numbering hashes each expression by `(op, value-numbers of
operands)`. The second `a + b` gets the same value number as the first, reuses
`t0`, and `t1` becomes dead:

```
t0 = a + b
t2 = t0 * t0
return t2
```

*two* `IBinOp`. (The script implements a minimal LVN pass and checks 3 → 2,
with the multiply now reading `t0 * t0`.)

*(c) Soundness condition.* Reusing the earlier result for a later identical
expression is valid only if *neither operand was reassigned between the two
occurrences* (and nothing aliases or otherwise changes them). Within one basic
block this always holds — a basic block is straight-line, single-entry code, and
Lark's temporaries are assigned once, so `a + b` cannot change between its two
uses. Across two blocks it need not hold: control may reach the second block by
an edge on which `a` or `b` was redefined, so a value computed in block 1 cannot
be assumed valid in block 2 without a global data-flow analysis. Hence *local*
value numbering.



### Exercise 2 — Basic blocks and the CFG of `sum_to`

*(a)* The leader rule (index 0; any label; the instruction after a
jump/branch/return) carves the `sum_to` TAC into exactly *four* blocks
(`ex02_cfg.py` confirms):

```
__entry__   ->  [.then1, .else2]
.then1      ->  [.end3]
.else2      ->  [.end3]
.end3       ->  []
```

*(b) The CFG is acyclic — no back edge.* The recursive call lowers to an
`ICall` (`t7 = call sum_to(...)`) sitting *inside* `.else2`; a call is an ordinary
instruction, not a control-flow edge, so nothing loops back to `__entry__`. The
transformation that turns this tail call into a back edge — replacing the
call-then-return with a jump to the entry — is *tail-call elimination in
Chapter 9*.

*(c)* `return r4` cannot be locally rewritten to `return t7`. `r4 = t7` only in
the *else* branch; in the *then* branch `r4 = acc`. The merge block `.end3`
returns whichever `r4` the taken branch produced, so substituting `t7` would be
wrong on the *then* branch (where `t7` is not the value, and may not even
exist). The non-local change that *would* remove `r4` and the merge block is to
give each branch its own return (`return acc` in then, `return t7` in else),
deleting the merge — copy propagation and its limits, in Chapter 8.



### Exercise 3 — `sum_to` in SSA form

Taking the four-block CFG from Exercise 2, with `r4` assigned in both branches:

*(a) Version each assignment to `r4`:*

```
.then1:  r4_1 = acc
.else2:  t5 = n ; t6 = acc ... ; t7 = call sum_to(...) ; r4_2 = t7
```

*(b) The φ-function `.end3` needs:*

```
.end3:  r4_3 = φ( r4_1 from .then1 , r4_2 from .else2 )
        return r4_3
```

On the incoming edge from `.then1` the φ selects *`r4_1`*; on the edge from
`.else2` it selects *`r4_2`*. A φ is exactly "pick the version that flowed in
along the edge actually taken," made explicit so each variable still has a single
static definition.

*(c) Why `acc` and `n` need no φ.* A φ is required only where a variable has
*two or more reaching definitions meeting at a merge*. `acc` and `n` are
parameters: each has a *single* definition (the function entry) that reaches
every use. The recursive call does not *reassign* this invocation's `acc`/`n`; it
passes new values as arguments to a *fresh* activation. And — the key link to
Exercise 2 — because there is *no back edge*, no edge carries a *second*
definition of `acc`/`n` back to a merge within this function. With only one
reaching definition, there is nothing for a φ to choose between, so `acc` and `n`
stay un-versioned. (A loop — the back edge tail-call elimination would add in
Chapter 9 — is exactly what would force φ-functions for the loop-carried values.)



### Exercise 4 — A `let` emits no TAC instruction

*(a)* A `let x = e in body` denotes no computation of its own — it just gives
the value of `e` a *name* for use in `body`. The lowerer has already produced a
`Val` (a temporary or constant) for `e`; binding `x` is a compile-time map update
(`{*env, x: v}`), and the body's instructions refer to that same `Val`
directly. So no copy/assign is emitted for the binding — only the instructions
for `e` and for `body`. `ex04_let_no_instr.py` lowers `let x = a + b in x * x`
and confirms the body is exactly three instructions (`+`, `*`, `return`), with
*zero* `IAssign` for the binding and the multiply reading the very temp the add
produced.

*(b)* The recursive evaluator (Chapter 6) allocated a fresh environment
dictionary at *run time* for every `let`, on every execution. Lowering does
that environment threading *once, at compile time*, collapsing each name to the
`Val` it stands for. The run-time dictionary cost disappears entirely: at run
time there is no environment object, only temporaries (and later registers). The
cost moved from every execution to a single compile pass.



### Exercise 5 — Closure conversion of `adder`

For `fn adder(n : Int) : Int -> Int = fn(x : Int) => n + x`
(`ex05_closure_conv.py` confirms each point against the lowered TAC):

*(a)* The inner lambda binds `x`; its only *free variable is `n`* (bound by
the outer `adder`).

*(b)* Lark lifts the lambda to a top-level function (`adder$lam0`) with an
extra leading `env` parameter. At `adder`'s body it emits

```
IAllocClosure(dst, "adder$lam0", captured=(n,))
```

packaging the lifted function with the captured value of `n`; at the top of the
lifted function it emits

```
IGetField(n_tmp, env, 0)
```

loading `n` from the captured record before computing `n + x`.

*(c)* When `adder(5)` is evaluated, `n = 5`, so the `IAllocClosure`'s captured
list holds `5`: the closure record is `{fn: adder$lam0, captured: [5]}`. This is
the explicit, heap-allocated form of the interpreter's `dict(env)` capture
(Chapter 6): rather than copying a whole environment dictionary, the lowerer
computed exactly which variables are free (only `n`) and captures just those, by
value, in a flat record the lifted function reads back with `IGetField`.
