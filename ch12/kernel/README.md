
## A Proof Checker for Homotopy Type Theory, Written in C

This repository is a programming language laboratory for students studying
dependent type theory and Homotopy Type Theory (HoTT).
It implements Martin-Löf Type Theory extended with HoTT features--identity types,
univalence, higher inductive types, universe polymorphism, and inductive
families - in around 4 000 lines of C source that you can read, run, and
extend.

The central idea: a term `t : A` is simultaneously a *program* of type `A`,
a *proof* that `A` is inhabited, and a *computation* that the evaluator can
normalise. The type checker is the proof checker. The normaliser is the
operational semantics. These are not analogies--they are the same object
seen from different angles.

The concrete goal of the repository is to write the type soundness proof for
a small typed language *inside the system itself*, as an inhabitant of a
dependent type. Getting there requires indexed inductive families, universe
polymorphism, and implicit arguments--all of which are present.



### Repository layout

```
code/
  core/                   The mathematical kernel: parser, bidirectional type checker,
                          NbE evaluator, elaborator. REPL: lcore.
  lang/                   A call-by-need graph reducer using the same surface syntax
                          and type checker. REPL: llang.
```

**`lcore` vs `llang`** — they share the same front end (parser, de Bruijn
conversion, bidirectional type checker; `lang/` links `core/`'s `term.c`,
`eval.c`, `check.c`, …) and differ only in the *back end* and what each is for:

- **`lcore`** is the **proof kernel**. Its evaluator is *normalisation by
  evaluation* (NbE): it reduces terms to a normal form so the conversion check can
  decide when two types are definitionally equal. This is the machinery that makes
  it a type-checker-that-is-a-proof-checker (§12.3). Its REPL infers types (`:i`),
  defines globals (`:let`), and runs the test suite (`:t`).
- **`llang`** is a **program runner**. Its evaluator is a *call-by-need graph
  reducer* — it shares subterms and evaluates lazily, the way a practical
  functional language runs — and it adds the conveniences that running programs
  wants: `:load` for files, `:conv` to test convertibility, `let rec`/`fix` for
  self-reference (see `samples/factorial.lam`, `samples/fibonacci.lam`). Same types,
  same checker; a different reduction strategy aimed at execution rather than proof.



### Building and running

```
cd code/core && make
./lcore
```

The `lcore` REPL takes one expression per line. A bare term is normalised and its
type inferred; commands start with a colon:

```
> succ (succ zero)
  normal : succ (succ zero)
> :i Π(A : Type). A → A
  type   : Type_1
> :let id = (\A x. x : Π(A : Type). A → A)
  id : Π(A : Type). Π(_ : A). A
> :i id _ zero
  type   : Nat
  normal : zero
```

Commands: `:i e` infers (and normalises) `e`; `:let name = expr` adds a global;
`:t` runs the built-in test suite (`./lcore --test` does the same
non-interactively); `:q` quits. A `:let` term must be *inferrable*, so a bare
lambda needs an annotation — `(\x. … : T)` — because in bidirectional checking a
lambda is checked against an expected type, not inferred. Inferrable terms
(`succ (succ zero)`, a fully applied function) need none.

For the graph-reducer layer, whose REPL adds `:load`, `:type`, and `:conv` and
lets the annotation sit on the binding (`let name : type = expr`):

```
cd code/lang && make && ./llang
:load "lib/prelude.lam"
let id : Π(A : Type). A → A = \A x. x
:type id
```



### What the system demonstrates

*Types as propositions, terms as proofs.* The same syntax that writes
`plus : Nat → Nat → Nat` also writes `plus_comm : Π(m n : Nat). Id Nat (plus m n) (plus n m)`.
They are checked by the same checker and run by the same evaluator.
`plus_comm 2 3` reduces to `refl 5` - a concrete witness that both sides
compute to the same number.

*Length-indexed vectors.* `head` on an empty vector is a type error, not
a runtime crash. The length is part of the type; the type checker enforces
bounds statically.

```
data Vec (A : Type) : Nat → Type where
  vnil  : Vec A zero
  vcons : Π(n : Nat). A → Vec A n → Vec A (succ n)
```

*Proofs that compute.* Identity type proofs are programs. Run them and they
reduce. `plus_comm (succ (succ zero)) (succ (succ (succ zero)))` normalises
to `refl (succ (succ (succ (succ (succ zero)))))`.

*Universe polymorphism.* Definitions can be quantified over universe
levels so they work at `Type_0`, `Type_1`, or any `Type_ℓ`. The level is an
explicit argument (`lzero`, `lsuc lzero`, …):

```
:let lid = (\l A x. x : Π(l : Level). Π(A : Type_l). A → A)
lid lzero Nat zero         -- at level 0:  normal : zero,  type : Nat
lid (lsuc lzero) Type Nat  -- at level 1:  normal : Nat,   type : Type
```

*Implicit arguments.* Underscores `_` are holes the elaborator fills by
unification:

```
id _ zero    -- A inferred as Nat
id _ true    -- A inferred as Bool
```



### How to read the code

The code is structured so that every type-theoretic concept maps to a
specific piece of C. There are no magic numbers, no hidden invariants that
require external documentation. Read the source files in this order:

1. `code/core/term.h` - All `TM_` and `VL_` tags. Skim once, return as reference.
2. `code/core/eval.c` - `nbe_eval`, `nbe_vapp`, the eliminators.
3. `code/core/check.c` - `infer`, `check`, `conv`.
4. `code/core/parse.c` - `parse_term`, `parse_atom`, de Bruijn conversion.
5. `code/core/elab.c` - Hole filling. Only relevant when you write `_`.

The standard library in [code/lang/lib/](./code/lang/lib) shows the system
in use: programs and proofs written in the same language, running through
the same machinery. [code/lang/lib/README.md](./code/lang/lib/README.md)
is a detailed walkthrough of everything in the library.



### The standard library

`code/lang/lib/` contains:

| File          | Contents                                                         |
|---------------|------------------------------------------------------------------|
| `nat.lam`     | `Nat`, `plus`, `mult`, `pred`, `iszero`                          |
| `vec.lam`     | `Vec`, `vlength`, `vmap`, `vconcat`, `head`                      |
| `fin.lam`     | `Fin`, `toNat`, `finWeaken` - bounded natural numbers            |
| `proofs.lam`  | `plus_zero_l`, `plus_zero_r`, `plus_succ_r`, `plus_comm`         |
| `prelude.lam` | Entry point - imports all of the above                           |
