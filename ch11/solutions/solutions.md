
## Chapter 11 — Solutions

Solutions to the exercises in Chapter 11, *Correctness*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (three meanings of correct) | analysis below | — |
| 2 (preservation & progress) | grounded by `ex02_03_proof_check.py` | `python3 ex02_03_proof_check.py` |
| 3 (the typed `Step` relation) | grounded by `ex02_03_proof_check.py` | (same) |
| 4 (testing methods) | `ex04_testing_methods.py` | `python3 ex04_testing_methods.py` |
| 5 (affine IO) | `ex05_affine_io.py` | `python3 ex05_affine_io.py` |

`ex02_03_proof_check.py` runs the *`lcore` kernel on Lark's machine-checked
soundness proof* ([lark/formal/proof/](./../../lark/formal/proof/));
ex4 drives the chapter's testing demo;
ex5 drives the real Lark checker (`lark/06`).



### Exercise 1 — Three meanings of "correct"

§11.1 separates three properties:

1. *Contract* — the program meets its specification (about *a program*).
2. *Soundness* — the type discipline keeps its promise: well-typed programs
   don't go wrong (about *a language*; proved).
3. *Faithful implementation* — the compiler preserves meaning (about *a
   compiler*; guarded by testing).

| Defect | Violates | Leaves intact |
|--------|----------|---------------|
| (a) sort returns its input unchanged | *1 (contract)* — it doesn't sort | 2 (it doesn't crash; the language is still sound) and 3 (the compiler still translates it faithfully) |
| (b) register allocator gives two interfering temporaries the same register | *3 (faithful implementation)* — the back end emits code that computes the wrong thing | 1 (the *source* program's contract is unaffected) and 2 (language soundness is untouched) |
| (c) `1 + true` type-checks and crashes at runtime | *2 (soundness)* — a well-typed term gets stuck | 1 (no particular program's contract is at issue) and 3 (the compiler faithfully implements the — unsound — language as specified) |

The point: each defect lives at a different level. A correct compiler for an
unsound language still lets `1 + true` crash; a sound language with a buggy
allocator still miscompiles; both can run a "sorter" that returns its input.



### Exercise 2 — Preservation and progress

*Statements* (for closed terms; `→` is one step):

- *Preservation:* if `· ⊢ e : t` and `e → e'` then `· ⊢ e' : t`.
- *Progress:* if `· ⊢ e : t` then `e` is a value or there is `e'` with `e → e'`.

Together they give type safety: a well-typed closed term never reaches a stuck
state (a non-value with no applicable rule).

*(a)* In an untyped language, `true 3` (applying a boolean) is *stuck* — a
non-value with no rule. *Progress* rules it out in a typed language: `true 3`
is not well-typed (a `Bool` is not a function), so a well-typed term is never of
that shape, and progress guarantees any well-typed non-value *can* step.

*(b)* Lark's encoding makes preservation *"disappear."* The reduction
relation is typed as

```
Step : Expr g t -> Expr g t -> Type
```

— the *same* type index `t` on both sides. A step that changed the type is not
even expressible, so "the type is preserved" is true by construction rather than
by a separate theorem. The work shifts onto the definition of `Expr`: it is
*intrinsically typed* (a value of `Expr g t` *is* a well-typed term of type `t`
in context `g`), so "well-typed" is not a predicate to be re-established after
each step — it is part of what a term *is*. `ex02_03_proof_check.py` runs the
proof through `lcore` and confirms it checks.



### Exercise 3 — The typed `Step` relation

*(a)* A reduction allowed to change a term's type would need

```
Step : Expr g t -> Expr g t' -> Type     (t' possibly ≠ t)
```

No constructor of the eight-rule relation (`StepBeta`, `StepIfTrue`,
`StepIfFalse`, `StepLetBeta`, `StepApp1`, `StepApp2`, `StepIf`, `StepLet`) can
inhabit it: each rule yields an `Expr` at the *same* index `t` it consumed,
because the typing rules guarantee a redex and its contractum have equal types
(e.g. `StepBeta` substitutes an argument of the parameter type into a body,
landing at the function's result type). With one shared `t`, the type-changing
signature has no inhabitant — the proof checker would reject any attempt to build
one.

*(b)* Preservation (proved and total) guarantees the type is kept on *every*
reduction of *every* well-typed term. The differential-testing oracle (§11.5)
can only *sample* finitely many programs and runs. The proof covers the
infinite space that testing spot-checks — which is exactly why both exist
(Exercise 4).



### Exercise 4 — Testing methods, each with a distinct job

`ex04_testing_methods.py` drives the chapter's demo: one tiny expression language
with three planted bugs — *A* `eval_fast` subtracts backwards, *B* `simplify`
rewrites `e*0` to `e`, *C* `parse` crashes on truncated input.

*(a) The pair.*

- *Bug A* is caught by *differential* testing (it compares `eval_ref` with the
  second implementation `eval_fast`) but *not* by property testing — the
  invariant "`simplify` preserves meaning" only ever calls `eval_ref`, never
  `eval_fast`, so it cannot see A.
- *Bug B* is caught by *property* testing (the invariant
  `eval(simplify e) == eval e` fails) but *not* by differential testing —
  differential compares two evaluators and never invokes `simplify`. (To catch B
  differentially you'd need a *correct* second `simplify` to compare against —
  the very thing under test.)

The script confirms each method finds its bug, and checks structurally that
`property_based`'s source never mentions `eval_fast` and `differential`'s never
mentions `simplify` — so the misses are by construction, not luck. (Fuzzing
catches C, which feeds malformed input the other two never generate.)

*(b) Neither replaces the proof; the proof replaces neither.* Testing
*samples* finitely many inputs; type safety covers the *infinite* space of
well-typed terms once and for all — no amount of passing tests proves "no
well-typed program gets stuck." But the proof is about *one* property
(soundness) of the *semantics*; it says nothing about whether a compiler pass
is faithful (differential), whether `simplify` preserves meaning (property), or
whether the parser survives garbage (fuzzing). They guard different things.



### Exercise 5 — Affine typing and resource correctness

`ex05_affine_io.py` drives the real checker.

*(a)* The misuse uses the `IO` token twice:

```
fn two_prints(io : IO) : IO =
    let a = print(io, "hello") in
    print(io, "world")            (* io used a second time *)
```

→ `AffineError('io')`. The rejecting rule is the *affine-variable check in
`infer`'s `Var` case*: a locally-bound non-`Copy` variable's use count is
incremented on each read, and reaching 2 raises `AffineError`. `IO` has no
`impl Copy`, so it is tracked, and the second `print(io, …)` trips it. The fix
threads the token (shadowing `io` each step) so every binding is used once.

*(b) "Used exactly once" (linear).* On top of the at-most-once check, the type
system would also reject *zero* uses: at each binding's end of scope (and at
function exit for parameters) it must verify the use count is exactly 1, not
`≤ 1`. The change is a "must be consumed" obligation — a check at scope exit that
every linear binding *was* used.

*(c) Why linear is heavier, and Lark's choice.* Linear forces the programmer to
thread and consume *every* resource on *every* path: no silently dropping a
value, no early return that leaves a token unused — you must explicitly discard
what you don't need. Affine ("at most once") permits dropping, which matches how
people actually write code. Lark chose affine because it already buys the
property the back end needs — a resource is never used twice, so no aliasing and
no runtime ownership checks (Chapter 9) — without imposing the bookkeeping of
accounting for every unused value that linearity demands.
