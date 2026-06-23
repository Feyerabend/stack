"""
Chapter 12, Exercise 1 — solution code.

Using the Curry–Howard table, translate each logical statement into a type and say
whether it is inhabited (provable): (a) A ⇒ A; (b) A ⇒ (B ⇒ A);
(c) (A ∧ B) ⇒ A; (d) A ∨ (A ⇒ ⊥). For the one not inhabited in constructive
logic, explain what term you would need and why you cannot write it.

How to run:   python3 ex01_curry_howard.py
Expected:     "(a),(b),(c) inhabited (kernel checked the proof terms); "
              "(d) A ∨ ¬A not inhabited; a false Id proof is also rejected"

The kernel's type checker IS the proof checker: a proposition is inhabited exactly
when a term of that type checks. This script asks lcore to check the proof terms.

  (a) A ⇒ A          ->  Π(A:Type). A → A          inhabited by  id   = λA x. x
  (b) A ⇒ (B ⇒ A)    ->  Π(A:Type).Π(B:Type). A→B→A inhabited by  K    = λA B x y. x
  (c) (A ∧ B) ⇒ A    ->  Π(A B). (A × B) → A        inhabited by  proj1 = λA B p. fst p
  (d) A ∨ (A ⇒ ⊥)    ->  Π(A:Type). Or A (A → ⊥)    NOT inhabited (excluded middle)

(d) is the law of excluded middle. To inhabit Π(A). Or A (Not A) you would have to
produce, for an ARBITRARY proposition A, either a proof of A (inl) or a proof of
¬A (inr) — a uniform decision procedure for every proposition. Constructively no
such term exists: with A abstract you have neither an `a : A` to feed inl nor a
function `A → ⊥` to feed inr. The kernel rejects every attempt (below), which is
the proof-checker's way of saying "not provable."
"""

from _harness import run, defined, failed

SRC = r""":let id    = (λA. λx. x : Π(A : Type). A → A)
:let K     = (λA. λB. λx. λy. x : Π(A : Type). Π(B : Type). A → B → A)
:let And   = (λA. λB. Σ(x : A). B : Type → Type → Type)
:let proj1 = (λA. λB. λp. fst p : Π(A : Type). Π(B : Type). And A B → A)
data Empty : Type where
data Or : Type → Type → Type where inl : Π(A : Type). Π(B : Type). A → Or A B ; inr : Π(A : Type). Π(B : Type). B → Or A B
:let Not = (λA. A → Empty : Type → Type)
:let lem = (λA. inr A (Not A) (λa. a) : Π(A : Type). Or A (Not A))
:let falseproof = (refl zero : Id Nat zero (succ zero))
"""


if __name__ == "__main__":
    out = run(SRC)

    # (a),(b),(c): inhabited — the kernel accepts the proof terms.
    for name in ("id", "K", "proj1"):
        assert defined(out, name), f"{name} should be inhabited\n{out}"

    # (d): excluded middle is not inhabited — every attempt is rejected.
    assert failed(out, "lem"), f"A ∨ ¬A must be rejected\n{out}"

    # And a flatly false proposition's "proof" is rejected too.
    assert failed(out, "falseproof"), f"refl zero : Id Nat 0 1 must fail\n{out}"

    print("(a),(b),(c) inhabited (kernel checked the proof terms); "
          "(d) A ∨ ¬A not inhabited; a false Id proof is also rejected")
