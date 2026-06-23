
## Chapter 6 — Solutions

Solutions to the exercises in Chapter 6, *A Working Interpreter*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (recursive vs CEK trace) | `ex01_trace.py` | `python3 ex01_trace.py` |
| 2 (closures / capture) | `ex02_closure.py` | `python3 ex02_closure.py` |
| 3 (tail calls and `kont`) | `ex03_tco_kont.py` | `python3 ex03_tco_kont.py` |
| 4 (attribute grammars) | analysis below | — |
| 5 (affine I/O token) | `ex05_io_affine.py` | `python3 ex05_io_affine.py` |

The code drives the real interpreter, [lark/04/src/cek.py](./../../lark/)
(the pure-interpreter phase), via `_harness.py`.



### Exercise 1 — Recursive and CEK traces of `let x = 2 + 3 in x * x`

*(a) Recursive `eval`* (env in force shown):

```
eval(let x = 2+3 in x*x, {})
  eval(2 + 3, {})              -> 5         (to bind x)
  eval(x * x, {x:5})           -> 25        (body, env extended)
```

*(b) CEK trace* (`ex01_trace.py` prints it):

```
   ##  state   expr/value     kont (top..bottom)
   0  Eval    TLetExpr       []
   1  Eval    TBinOp         ['LetF']          <- LetF pushed
   2  Eval    TLit           ['BinOpLF', 'LetF']
   3  Return  2              ['BinOpLF', 'LetF']
   4  Eval    TLit           ['BinOpRF', 'LetF']
   5  Return  3              ['BinOpRF', 'LetF']
   6  Return  5              ['LetF']
   7  Eval    TBinOp         []                <- LetF popped (x bound to 5)
   8  Eval    TVar           ['BinOpLF']
   9  Return  5              ['BinOpLF']
  10  Eval    TVar           ['BinOpRF']
  11  Return  5              ['BinOpRF']
  12  Return  25             []
```

*(c)* `LetF` is *pushed at step 1* (when the let's value `2 + 3` begins
evaluating — the machine sets aside "bind `x`, then evaluate `x * x`") and
*popped at step 7* (the value `5` is delivered, `x` is bound, the body runs).
In the recursive version, the role of `LetF` is played by the *suspended Python
activation record* of the `eval(let …)` call: while `eval(2 + 3)` runs, that
record is paused on the host call stack, holding exactly the same pending work
the `LetF` frame makes explicit. Both versions agree on `25`.



### Exercise 2 — Closures and capture

*(a)* `adder(5)` produces (`ex02_closure.py` inspects it):

```
VClosure(param = "x",
         body  = (n + x)            ## the inner TBinOp
         env   = { n: 5, … })       ## n captured at creation
```

`add5(10)` then evaluates `n + x` with `n = 5` (captured) and `x = 10`, giving
*15*.

*(b)* If the closure captured the *caller's* environment at *call* time
(dynamic scope) instead of the *defining* environment at *creation* time, the
free variable `n` would resolve against whatever `n` exists where `add5` is
*called*. But `adder` has already returned by then — `n` may be gone, or
(worse) silently bound to an unrelated `n` at the call site. Lexical capture is
what makes `adder(5)` mean "+5" permanently, and it is the discipline the type
checker assumed in Chapter 5 (a closure's free variables were checked in its
defining scope).

*(c)* A program where the two strategies differ (`ex02_closure.py` runs it):

```
let n = 1 in
let f = fn (x) => n + x in    (* captures n = 1 *)
let n = 100 in                (* shadows n *)
f(0)
```

Lexical capture gives *1* (`f` remembers `n = 1`); dynamic capture would give
*100* (`f` would see the `n = 100` live at the call). Lark prints `1`.



### Exercise 3 — Tail calls and the continuation

`ex03_tco_kont.py` measures the maximum `kont` depth across `n`:

```
tail:     {1: 2, 3: 2, 5: 2, 10: 2}     ## flat
non-tail: {1: 3, 3: 5, 5: 7, 10: 12}    ## grows linearly in n
```

*(a)/(b) Tail form* `if n == 0 then acc else sum_to(n-1, acc+n)`: the
continuation length is *constant* — it does not grow with `n`. The responsible
behaviour is in `apply()`: applying a closure returns `Eval(body, new_env, kont)`
with the *same* `kont` it was handed, so the tail call pushes no frame. (In
`step_ret`, the `IfF` frame is consumed when the branch is chosen, and the chosen
branch — the bare recursive call — adds nothing.) The machine simply re-enters
`sum_to`'s body with the continuation it already had: a real loop in bounded
space.

*(c) Non-tail form* `n + sum_to(n-1)`: the `+` must run *after* the call
returns, so evaluating it pushes a `BinOpRF` frame (holding the left value `n`,
waiting for the right operand) onto `kont` *before* the recursive call. One
such frame survives per outstanding call, so `|kont|` grows linearly in `n` —
precisely the stack growth that tail-call elimination removes.



### Exercise 4 — Attribute-grammar classification

*(a) `TIfExpr`.* The *environment is an inherited attribute*: the parent
passes the *same* environment down to all three children — the condition, the
then-branch, and the else-branch. The *value is synthesised*: the condition
synthesises a `VBool`, and whichever branch runs synthesises the result, which
becomes the `if`'s value.

*Which* branch is evaluated is decided by the condition's synthesised value *at
run time*, and that decision is *outside* the attribute grammar. A pure
attribute grammar defines equations over a *fixed* tree — every node's attributes
are computed. Choosing to evaluate only one subtree, based on a value computed
from another, is a control-flow decision the evaluator makes (and is why `if`
cannot be a strict, all-children attribute computation: evaluating both branches
could loop or fault). The attribute equations describe *how* each branch would be
valued; *whether* a branch is valued at all is control flow.

*(b) `TMatchExpr`.* Inherited: the *environment*, flowing into the scrutinee
and into each arm. Synthesised: the *value of the chosen arm* (the match's
value). The interesting part is the pattern bindings: matching a pattern against
the scrutinee's value (e.g. `Cons(x, rest)`) produces *new bindings*. Those
bindings extend the environment in which the arm body is evaluated, so they flow
*down* into the arm body — they are most naturally seen as an *inherited*
attribute of the arm body, produced by the parent (the match, via pattern
matching) and passed downward, exactly as a `let`'s binding flows down into its
body. They cannot be synthesised by the body, because the body needs them as
input before it can be valued at all.



### Exercise 5 — The affine I/O token

`ex05_io_affine.py` runs both versions through the real checker and interpreter.

*(a)* Threading the token (each `print` consumes the current `io` and the
result is rebound) type-checks and prints two lines:

```
fn two_lines(io : IO) : IO =
  let io = print(io, "first") in
  let io = print(io, "second") in
  io
```

The version that reuses the *original* token for the second `print` is rejected:

```
fn two_lines(io : IO) : IO =
  let io2 = print(io, "first") in
  print(io, "second")          (* io used a second time *)
```

→ `AffineError('io')` — `IO` is non-`Copy`, so the original `io` may be used at
most once; the second `print(io, …)` is its second use.

*(b) If `print` were a direct effect* (call Python's `print`, return `VUnit`,
no token):

1. *Purity / referential transparency is lost.* With the token, the *order* of
   effects is forced by the data dependencies the type checker tracks (each
   token used exactly once, Chapter 5's affine discipline). A direct effect makes
   output order depend on the interpreter's evaluation order, which the pure
   semantics deliberately leaves unspecified.
2. *The code-generation licence of Chapter 9 is lost.* Because `IO` is affine
   and consumed once, the back end may treat the token as a zero-width value,
   emit no ownership/aliasing checks, and reorder pure code freely around
   effects. A direct effect reintroduces hidden ordering constraints the
   optimiser and code generator could no longer assume away — undermining the
   soundness the Chapter 11 proof depends on.
