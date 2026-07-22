# `prove/` — What the machine can promise

**Book: Part III, chapters 13–18.**

The compiler passes every test we have. That is worth something, and it is worth
less than it sounds: the tests were written by the people who wrote the bugs, and
they cover the inputs someone thought of. This tree is about the other kind of
assurance — a claim that holds for **every** program, including the ones nobody
has written yet.

There are two such claims here, at two strengths.

> **Type safety.** Every program the type checker accepts will run without getting
> stuck. Not most — every one.

> **Refinement.** A program that carries conditions on its types — `{ v : Int | v
> >= 0 }` — and passes the checker cannot violate them: no out-of-bounds index, no
> division by zero, no broken invariant, for any input at all.

The first is proved *about the language*, once, in a proof a machine checks. The
second is checked *about your program*, every time you compile, by a decision
procedure that discharges the conditions with no proof from you. This tree holds
both — the proof and the checker — and the code that puts them to the test.

## The folders

### `oracle/` — the refinement checker

The compiler, plus the checker that rides on top of it. The three files at the
heart of it:

| File | What it does |
|---|---|
| `refine.py` | the refinement checker — reads the refined types, emits the verification conditions |
| `solver.py` | a decision procedure for the logic (`QF-UFLIA`), **from scratch** — congruence closure plus an Omega test for integer arithmetic, under a DPLL(T) loop. No Z3, no external prover. |
| `pred.py` | the predicate language — the fragment of conditions the solver can decide |

Everything else in `oracle/` is the compiler the checker leans on (the same
reference implementation the other strands call the oracle). Refinements **erase**:
a program that checks is an ordinary Lark program, and running it never mentions
them again. Chapters 16 and 18 read this code.

### `fixtures/` — the corpus, in safe/unsafe pairs

Seventy-five programs, most in pairs: a **safe** program that should check, and a
**mutant** of it carrying one real bug that must *not*. A verifier is only as good
as the programs it rejects, so both halves matter, and the expected verdict of
every file is pinned in the harness as a count — how many obligations were
discharged, and how many were not. A drifting count is a finding either way.

### `harness/` — putting the checker under attack

| File | What it does |
|---|---|
| `prove_difftest.py` | runs every fixture and checks its verdict against the pinned count; the last one is *checked and then run*, to show erasure holds |
| `adversary.py` | generates programs designed to be believed-or-caught, and confirms every "proved" program actually runs |
| `solver_fuzz.py` | fuzzes the solver against brute force — it must never claim a contradiction that does not exist, nor prove a goal with a counterexample |

Chapter 17 is about this: the checker is only trustworthy to the degree it
survives something trying to fool it.

### `lcore/` — a proof checker, in about 4,000 lines of C

A proof is only as trustworthy as the thing that checks it, so the thing that
checks it must be small enough to read. `lcore` implements **Martin-Löf type
theory**, extended with the machinery of Homotopy Type Theory (identity types,
univalence, higher inductive types).

The idea it rests on is one of the strangest and most useful in the subject:

> A type is a claim. A value of that type is a proof of that claim.
> A function is an implication. Running a program *is* checking a proof.

The type checker and the proof checker are not analogous. They are the same
program. Chapter 14 reads this C code. `lcore-README.md` is the checker's own
documentation, kept as it was.

### `lark-formal/` — the proof that Lark is sound

Lark, written down as mathematics and handed to the checker:

| File | What it states |
|---|---|
| `lark-typing.lcore` | the typing rules — when is a Lark program well-typed |
| `lark-step.lcore` | the evaluation rules — how a Lark program runs |
| `lark-subst.lcore` | the substitution lemma (the workhorse; nothing else can be proved without it) |
| `lark-preservation.lcore` | **preservation**: running a step does not change a program's type |
| `lark-formal.tex`, `lark-formal.pdf` | the whole development, written up |

Together with **progress** (a well-typed program is either finished or can take
another step), preservation gives the type-safety claim above: a well-typed
program never jams. Chapter 15 explains how such a thing is stated, how it is
proved, and what it is like to have a machine reject your first three attempts.

## Running it

```sh
make            # the targets, with what each one shows

# the refinement checker (Python only, no build)
make prove      # check all 75 fixtures against their pinned verdicts
make adversary  # generate adversarial programs and try to fool the checker
make solver     # fuzz the from-scratch solver against brute force

# the soundness proof (builds the C kernel)
make selftest   # the kernel's own 339 cases
make proofs     # CHECK THE SOUNDNESS PROOF for Lark
make test       # prove + selftest + proofs
```

`make proofs` builds the checker and feeds it the four `lark-formal/` files as a
single development, in dependency order — each one uses what the ones before it
defined. It takes seconds. If any definition fails to check, it says so and exits
non-zero: `lcore` is a REPL and exits 0 either way, so a proof that does not check
must not be allowed to pass quietly.

`make pdf` typesets the written account (`lark-formal.tex`), and `make llang`
builds the surface language that sits on top of the kernel.

## What is *not* proved — and the book says this loudly

Refinement types close part of the gap the older boundary named — they let the
language make promises about *your* program, not only about itself. But the
boundary does not vanish; it moves. Draw it honestly:

- **The compiler is not verified.** The soundness proof is about the *language* —
  its type system and its semantics. Nothing here proves that the C we emit means
  the same thing as the Lark we read. The back end is trusted, not proved.
- **The formal Lark is a model.** The language on paper and the language in the
  compiler are not the same object. The gap is small and it is real, and chapter
  15 measures it rather than hiding it.
- **The proof checker is trusted.** Something always is. The point of keeping it
  to 4,000 readable lines is to make that trust cheap.
- **Refinement is partial correctness.** It proves the conditions you write — a
  bound, a non-zero divisor, an invariant — hold on every path that returns. It
  does not prove a program terminates, and it says nothing your conditions do not.
  Type safety says your sort will not crash; a refinement can say its output is
  ordered; neither says it is a permutation of the input unless you make it.
- **Integers are mathematical.** The solver reasons over ℤ, not machine words;
  where that gap bites is named in the book, not papered over.

Chapter 16 introduces the checker, chapter 17 attacks it, and chapter 18 pushes it
as far as **measures** — facts about the *size or shape* of a value — will carry.
