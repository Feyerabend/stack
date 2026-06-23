
## Chapter 12 — Solutions

Solutions to the exercises in Chapter 12, *Types as Proofs*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (Curry–Howard inhabitation) | `ex01_curry_howard.py` | `python3 ex01_curry_howard.py` |
| 2 (Π and Σ dependent types) | `ex02_dependent_types.py` | `python3 ex02_dependent_types.py` |
| 3 (indexed families) | analysis below | — |
| 4 (the `weaken` primitive) | analysis below | — |
| 5 (undecidability) | analysis below | — |

ex1 and ex2 drive the dependent-type kernel `lcore`
([kernel/code/core](./../kernel/code/core)), the readable sibling of the `lcore`
that checked Lark's soundness proof. Because the type checker *is* the proof
checker, "checks" means "is a proof".



### Exercise 1 — Curry–Howard inhabitation

| Statement | Type | Inhabited? | Proof term |
|---|---|---|---|
| (a) `A ⇒ A` | `Π(A:Type). A → A` | yes | `id = λA x. x` |
| (b) `A ⇒ (B ⇒ A)` | `Π(A:Type).Π(B:Type). A→B→A` | yes | `K = λA B x y. x` |
| (c) `(A ∧ B) ⇒ A` | `Π(A B). (A × B) → A` | yes | `proj1 = λA B p. fst p` |
| (d) `A ∨ (A ⇒ ⊥)` | `Π(A). Or A (A → ⊥)` | **no** | — |

`ex01_curry_howard.py` has the kernel **check** the terms for (a)–(c) — they are
accepted, so the propositions are inhabited.

**(d) is the law of excluded middle, and it is not inhabited constructively.** To
build a term of `Π(A:Type). Or A (Not A)` you would need, for an *arbitrary*
proposition `A`, either a proof of `A` (to use `inl`) or a function `A → ⊥` (to
use `inr`) — a uniform way to decide *every* proposition. With `A` abstract you
have neither, so no constructor of `Or` can be applied. The script confirms the
kernel rejects the attempt (and, for good measure, that a flatly false
proposition's "proof" — `refl zero : Id Nat zero (succ zero)` — is also rejected).
That rejection is the proof checker saying "not provable."



### Exercise 2 — Π versus →, Σ versus ×

**(a) Π — a vector of `n` zeros.**

```
zeros : Π(n : Nat). Vec Nat n
```

The codomain `Vec Nat n` *mentions the argument value* `n`. That is exactly what Π
buys over `→`: `a → b` has a fixed codomain, while `Π(n:Nat). Vec Nat n` has a
codomain that depends on `n`. `ex02_dependent_types.py` defines `zeros` (replicate
`n` `zero`, by `natrec`) and the kernel confirms it has this type.

**(b) Σ — an index that holds `v`.**

```
member A n xs v  =  Σ(i : Fin n). Id A (vget xs i) v
```

a pair of a witness index `i : Fin n` and a *proof* `Id A (vget xs i) v` that the
vector at `i` equals `v`. Σ generalises `×` the way Π generalises `→`: the type of
the second component (the `Id` proof) depends on the value of the first (the index
`i`). The script checks a representative Σ-over-`Fin` proposition is a well-formed
type.

**(c) Why Hindley–Milner cannot write either.** HM types are built from type
variables and type *constructors applied to types*; they can never mention a
*value*. `Vec Nat n` indexes a type by the term `n`; `Σ(i:Fin n). Id A (vget xs i)
v` indexes a type by the terms `i`, `xs`, `v`. HM has no notion of a type that
depends on a value, so neither "a vector of length `n`" nor "an index holding `v`"
is expressible. It stops one rung below dependent types.



### Exercise 3 — Indexed families make ill-typed terms unrepresentable

**(a)** `data Expr : Ctx → Ty → Type` is an *indexed family*: an `Expr g t` is, by
construction, a well-typed term of type `t` in context `g`. The constructor `EApp`
has type `Π(g).Π(a).Π(b). Expr g (TFn a b) → Expr g a → Expr g b` — the argument
*must* be an `Expr g a` whose type matches the function's domain. There is no way
to apply the constructor to mismatched types, so an ill-typed application is not a
term that fails a check — it is a term you *cannot write down*. "Well-typed" stops
being a predicate over a separate syntax and becomes part of what the datatype is.

**(b)** A type-changing step relation would be

```
Step : Expr g t → Expr g t' → Type        (t' possibly ≠ t)
```

No constructor of the eight-rule relation can inhabit it. Each rule (`StepBeta`,
`StepIfTrue`, `StepIfFalse`, `StepLetBeta`, `StepApp1`, `StepApp2`, `StepIf`,
`StepLet`) produces an `Expr` at the *same* index `t` it consumed, because the
typing rules guarantee a redex and its contractum share a type. With one shared
`t` the type-changing signature has no inhabitant — preservation is true *by
construction*, which is why Chapter 11 saw it "disappear." (`lcore` checks the
real proof; see `ch11/solutions/ex02_03_proof_check.py`.)



### Exercise 4 — The `weaken` primitive

`weaken` adds an unused binding to a context (relabelling de Bruijn indices for a
larger context). It is the one place the proof drops below the type theory into C.

**(a) The definitional equation a recursive `weaken` would need.** Written in the
object theory, `weaken` would have to commute with every constructor —
`weaken (EApp f x) = EApp (weaken f) (weaken x)`, and so on — and, at variables,
satisfy the equation that shifting an index past the new binding agrees with
re-indexing into the extended context. That last equation does **not** hold *for
free* (definitionally): it is a *theorem* about how substitution and context
extension interact, provable only by induction on the term, not by the kernel's
computation/conversion. So a recursive `weaken` in the object theory would need an
accompanying inductive proof that it respects typing.

**(b) Why implementing it in the kernel is acceptable.** `weaken` is a small,
structural, obviously meaning-preserving operation — it renumbers indices, it does
not invent or discard information. Trusting a short, auditable kernel function for
it is the *same kind* of trust already placed in the kernel's parser, evaluator,
and conversion checker. The result's trustworthiness is unaffected: anyone can
read the function and see it is the identity-up-to-reindexing.

**(c) What wholesale use would cost.** The entire value of a proof checker is a
*small trusted base* with *everything else checked*. Each lemma "implemented" in C
rather than proved is unchecked code the reader must trust, and a bug in any one
is a soundness hole. `weaken` is acceptable as a single, evidently-correct
structural exception; handling *every* hard lemma this way would inflate the
trusted base until the checker certifies little and the "proof" is mostly an
appeal to unverified C — defeating the purpose.



### Exercise 5 — Undecidability

**(a) Checking is decidable; finding is not.** *Checking* a given proof terminates:
the kernel normalises and compares types, and for the kernel's theory that
procedure always halts with yes/no. *Finding* a proof — searching for an
inhabitant of a type — is theorem proving, which is undecidable. There is no
contradiction: deciding whether a *specific* witness works is easy; deciding
whether *some* witness exists is not. A dependently typed compiler relies on
**checking** — the programmer supplies the proof term, and the compiler only
verifies it.

**(b) What Lark gives up, and what it avoids.** Lark stopped below full dependent
types, so it *cannot* state value-indexed guarantees in its types — "this vector
has length `n`", "this list is sorted", "this function is total" — that Idris or
Agda express and check. In exchange it *avoids* the cost they pay: Lark keeps
**decidable, annotation-light type inference** (Hindley–Milner infers types with
no programmer-written proofs), fast checking, and no obligation to prove
termination. The guarantee and the burden come together; Lark declined both.

**(c) Where a language should sit (example).** A systems or applications language
is well served at Lark's rung — HM inference plus an affine discipline: decidable
inference, resource safety, no proof burden, predictable compile times. A
library where a single bug is catastrophic — a cryptographic primitive, an
avionics controller — earns the higher rung (Agda/F\*/Idris): the programmer pays
in proofs and slower checking to buy machine-checked functional correctness. The
right rung is set by the cost of being wrong versus the cost of proving you are
not.



### Appendix — the kernel repair this chapter prompted

Working Exercises 1–2 surfaced that the kernel's **`llang` layer never type-checked
`let` definitions** against their annotations: `def_define_nocheck` stored the body
without checking, so `let lie : Id Nat zero (succ zero) = refl zero` was accepted.
The fix adds **`def_define_checked`** (parse the annotation, evaluate it, and run
the bidirectional `check` on the body) and routes `llang`'s `let`/`let rec` through
it when a type annotation is present.

Enabling checking required the `.lam` library to carry the explicit annotations the
checker assumes — each `natrec`/`indrec`/`boolrec` motive (`: Nat -> Type`,
`: Pi(n:Nat). Vec A n -> Type`, …) and step. All of `lib/` (`nat`, `proofs`,
`vec`, `fin`), the top-level `vec`/`fin`/`stdlib`, and the `samples/` now check
cleanly. The pass also **exposed two real latent bugs in `proofs.lam`** that the
non-checking layer had hidden: `plus_comm`'s base used `sym` with its arguments
swapped, and its `trans` used the wrong middle term. Both are fixed; every proof
now genuinely type-checks, false proofs are rejected, and the samples still
compute.
