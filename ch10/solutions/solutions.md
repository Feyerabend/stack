# Chapter 10 — Solutions

Solutions to the exercises in Chapter 10, *Abstract Machines and Operational
Semantics*, of *The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|---|---|---|
| 1 (four levels of meaning) | analysis below | — |
| 2 (SECD dump vs CEK frame) | analysis below | — |
| 3 (`ApplyFnF` is `[·] e2`) | `ex03_apply_context.py` | `python3 ex03_apply_context.py` |
| 4 (miniature Prolog) | `ex04_prolog.py` | `python3 ex04_prolog.py` |
| 5 (call-by-name vs value) | `ex05_cbn_cbv.py` | `python3 ex05_cbn_cbv.py` |

Code drives Lark's CEK (`lark/04/src/cek.py`), the chapter's Prolog
(`ch10/06_prolog/sprolog.py`), and the vm-theory Krivine/CEK machines.

---

## Exercise 1 — Four levels of meaning for `let x = 2 + 3 in x * x`

- **Denotational.** Assigns the mathematical value directly and compositionally:
  `⟦let x = e₁ in e₂⟧ρ = ⟦e₂⟧ρ[x ↦ ⟦e₁⟧ρ]`. Here `⟦2+3⟧ρ = 5`, so
  `⟦x*x⟧ρ[x↦5] = 25`. The meaning *is* the number **25** — a function from
  environments to a value, with no notion of steps.
- **SOS (small-step).** A derivation that rewrites the term one reduction at a
  time: `2 + 3 → 5`; `let x = 5 in x*x → 5*5`; `5*5 → 25`. The meaning is the
  *reduction sequence* ending in `25`.
- **CEK machine.** A sequence of machine states (`Eval`/`Return` with environment
  and continuation) that computes `25` — the trace of Chapter 6, Exercise 1.
- **Hardware (Chapter 9).** RISC-V instructions that compute `25` in registers
  (`li`/`add`/`mul`), the result sitting in a register. The meaning is the
  machine's effect on the register file.

**(b)** The two that are "the same definition seen from two distances" are the
**SOS and the CEK machine**. The CEK machine is the structural operational
semantics *made executable*: its continuation frames are precisely the SOS
evaluation contexts (Exercise 3), and it realises the same reduction sequence as
a state-transition function. The denotational account is a different *style*
(meaning as value, not as steps), and the hardware is an *implementation* of the
same operational behaviour at a far lower level.

---

## Exercise 2 — SECD Dump vs CEK frame on a tail call

**(a)** On a function call the **SECD** machine saves the whole current
`S`/`E`/`C` triple onto the **Dump** — for *every* call, including a tail call —
and restores it when the callee returns. So the Dump grows by one entry per
(tail) call: plain SECD does not reuse its state, and recursion through tail
calls deepens the Dump without bound. The **CEK** machine, on a tail call, hands
the callee the **current continuation unchanged**: `apply` returns
`Eval(body, new_env, kont)` with the *same* `kont` it was given, pushing no
frame. Only the CEK machine reuses its state without growing, because a tail call
adds nothing to the continuation — there is no "return here afterwards" to
remember, so nothing is saved.

**(b)** This is exactly the jump the compiler emitted for `sum_to`. The CEK's
"same `kont`, no new frame" tail call is, at the machine level,
`j .sum_to_loop` (Chapter 9): a jump that re-enters the function reusing the
current stack frame, with no new activation record. The back edge in the
control-flow graph is the compiled form of the CEK's constant-continuation tail
call; both say "continue with the work already pending, in place."

---

## Exercise 3 — `ApplyFnF` is the evaluation context `[·] e₂`

`ex03_apply_context.py` traces Lark's CEK on `(f x) + 1` (with `f = λy.y`,
`x = 3`).

**(a)** SOS derivation (call-by-value). To reduce `(f x) + 1` we work in the
context `[·] + 1` (reduce the left operand first). To reduce `f x`, with `f`
already a value, we evaluate the function position in the context `[·] x` (the
operator with its operand pending), then apply:

```
(f x) + 1
  → [reduce f x, in context [·] + 1]
      f is a value; context [·] x  (evaluate operator, operand x pending)
      x → 3 ; (f 3) → 3            (variable lookup, then β)
  → 3 + 1
  → 4
```

The context `[·] x` is "the hole where the function goes, with argument `x` still
to apply" — an evaluation context.

**(b)** In the CEK trace, the frame that reifies `[·] x` is **`ApplyFnF([x], env)`**:
it sits on the continuation while the function position is evaluated, recording
that the argument `x` is still pending. Once the function is a value, an
`ApplyArgF` frame takes over to evaluate the argument. The script asserts both
frames appear and the result is `4`.

**(c)** "The machine and the semantics are the same definition" means the CEK
transition relation and the small-step SOS generate the *same* reduction
sequence — the machine's frames *are* the SOS evaluation contexts, represented as
data instead of as syntax-with-a-hole.

---

## Exercise 4 — The miniature Prolog

`ex04_prolog.py` drives the companion `sprolog`.

**(a) Search tree** for `grandparent(john, W)` with `parent(john, bob)`,
`parent(bob, ann)`, `grandparent(X,Y) :- parent(X,Z), parent(Z,Y)`:

```
grandparent(john, W)
└─ unify head: X=john, Y=W   → goals: parent(john, Z), parent(Z, W)
   └─ parent(john, Z): unify parent(john, bob) → Z=bob        [unify]
      └─ parent(bob, W): unify parent(bob, ann) → W=ann       [unify]
         └─ SUCCESS: W = ann
```

No backtracking is needed (one parent fact for `john`, one for `bob`). The script
confirms `W = ann`.

**(b) Depth-first order.** Adding `parent(john, carol)` and `parent(carol, dave)`
gives a second path. DFS tries facts in source order, and `parent(john, bob)`
precedes `parent(john, carol)`, so it finds `W = ann` first (via `bob`), then on
backtracking explores `Z = carol` and finds `W = dave`. Order: **`[ann, dave]`**
(the script asserts this).

**(c) Cut.** To commit to the first grandparent found, the textbook rule is

```
first_gc(X, Y) :- grandparent(X, Y), !.
```

The `!` discards the choice points created while solving `grandparent` — here the
`Z = carol / W = dave` branch — so `first_gc(john, W)` yields only `W = ann` (the
script asserts this).

> **Companion repair.** Working this exercise turned up two bugs in `sprolog`,
> both now fixed (regression suite: `ch10/06_prolog/test_cut.py`).
>
> 1. **Variable collision.** A query variable could collide with a rule's
>    variable because both were numbered from 0 and `Variable` equality was by
>    that integer id — so `grandparent(john, W)` silently returned nothing. The
>    proper fix is *standardizing apart* by construction: `Variable` now uses
>    **object identity** (each `Variable()` is a brand-new, globally unique
>    variable; equality is `is`), and a single id source. Two independently
>    parsed `X`s are simply different variables — no counters to keep in sync.
> 2. **Cut scoping.** Cut was caught at the innermost clause loop, pruning only
>    the *immediate* goal's choice points, not those inside a *called* rule (so
>    `first_gc :- grandparent(X,Y), !` did not commit). The fix gives each clause
>    activation a **cut barrier** and tags every `!` with its clause's barrier, so
>    a cut propagates up through called rules and is caught exactly at its home
>    clause.
>
> `test_cut.py` (11 tests) covers commitment, sibling-clause and called-rule
> pruning, goals-after-cut backtracking, query-level cut, variable-name
> independence, fresh-variable distinctness, and `\=`/`sibling`.

---

## Exercise 5 — Call-by-name vs call-by-value

`ex05_cbn_cbv.py` runs the *same* term on the Krivine machine (call-by-name) and
the vm-theory CEK machine (call-by-value).

**(a) The changed rule.** Two congruence rules govern where reduction may happen
in an application: one steps the **function** position (`e₁ → e₁' ⟹ e₁ e₂ →
e₁' e₂`), the other steps the **argument** (`e₂ → e₂' ⟹ v e₂ → v e₂'`, once the
function is a value). Call-by-value **keeps** the argument-congruence rule (reduce
the operand to a value before entering the function). Call-by-name **drops** it:
the argument is passed unevaluated (a thunk) and reduced only if the body uses it.
So the *operand-evaluation congruence rule* is the one that changes.

**(b) Observable difference.** Let `Ω = (λx. x x)(λx. x x)` be non-terminating,
and consider `(λx. 0) Ω`. Under **call-by-name** the argument is never used (the
body is `0`), so the program returns **0**. Under **call-by-value** the argument
must be reduced first, so evaluation **diverges**. The script confirms it: Krivine
returns `0`; the CEK machine exceeds its step bound. Same expression — one rule
yields a value, the other never terminates.

**(c) CBV in `ApplyArgF`.** Lark's CEK pushes an `ApplyArgF` frame to reduce each
argument to a value *before* entering the closure. That frame is the
operand-congruence rule made into a machine step: its very existence is the
commitment to call-by-value. The Krivine (call-by-name) machine has no such
frame — it binds the argument as an unevaluated thunk and enters the body at once.
