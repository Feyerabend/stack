
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



### Building and running

```
cd code/core && make
./lcore
```

The REPL accepts one expression per line:

```
> succ (succ zero)
  normal : succ (succ zero)
> :type Π(A : Type). A → A
  type : Type_1
> :let id : Π(A : Type). A → A = \A x. x
> :type id _ zero
  type : Nat
```

Commands: `:type e` infers and prints the type of `e`. `:conv a b` tests
definitional equality. `:let name : type = term` adds a global definition.

For the graph-reducer layer:

```
cd code/lang && make && ./llang
:load "lib/prelude.lam"
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
levels so they work at `Type_0`, `Type_1`, or any `Type_ℓ`:

```
:let id : Π(ℓ : Level). Π(A : Type_ℓ). A → A = \ℓ A x. x
id _ Nat zero       -- level inferred as 0
id _ Type Nat       -- level inferred as 1
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



### Lark STLC proofs (`lark/`)

The `lark/` subdirectory contains a mechanised proof of type soundness for
**Lark**, a small simply-typed lambda calculus with integers, floats,
booleans, strings, unit, functions, let-bindings, and conditionals.

#### Files

| File | Contents |
|---|---|
| `lark-typing.lcore` | Inductive families: `Ty`, `Ctx`, `Var`, `Expr` |
| `lark-subst.lcore` | Semantic environments, substitution, value predicate; lcore-native weakening `ins`/`shift`/`wk`/`wk0` (V3-WK0) |
| `lark-step.lcore` | Small-step reduction (`Step`), multi-step (`Eval`) |
| `lark-preservation.lcore` | `eval_produces_val`: every evaluated term is a value |
| `lark-refine.lcore` | V3: `sub_sound_v`/`sub_sound` — refinement subtyping implies semantic implication, over a RECURSIVE relation: `RTy : Ty → Type` (erasure = the index), `SemV` by `indrec RTy` (`RInt` payload triple; `RBool` pinned literal; `RFn` = `IsVal` + applicative clause), `Sub` with `SubBase` + `SubFn` (contravariant domain / covariant codomain); monotonicity in the step budget (`le_trans` by inversion + `J`, `sem_e_mono` generic in the value relation); and the FUNDAMENTAL LEMMA `fund` — a refined typing judgment `HasR` (RT_Int/RT_Bool/RT_Var/RT_App/RT_If/RT_Sub over refined contexts `RCtx`/`GoodEnv`) with `fund : HasR → GoodEnv → Σk. SemE` by `indrec HasR` (congruence lifts via `Id`-coerced motives; budgets concatenate via `plus`/`le_plus_mono`/`steps_append`). RT_Lam/RT_Let deferred to Pitch 2 — the substitution-lemma fusion pile, now built on the inductive `wk0` (V3-WK0 retired the kernel `weaken` from the proof path). The step index is inert inside `SemV` at this rung (arrow clause carries Σ k'); it becomes load-bearing at descend |
| `lark-formal.tex` | Typeset account of the proof (build with `tectonic`) |

Note: `ELitInt` carries its numeric payload (`Π(g : Ctx). Π(n : Nat). Expr g TInt`)
so that refinement predicates in `lark-refine.lcore` have a value to predicate
over. Lark's refinement logic is ℤ; the spine models payloads as `Nat`.

#### Running the proofs

From this directory (`formal/proof/`):

```
make check    # build lcore, run all five files, FAIL on any error line
make meta     # the four Phase-5b metatheory files only
```

`make check` is the green bar: lcore is a REPL that prints `type error: ...`
but exits 0, so the Makefile greps the transcript and fails loudly instead.
The underlying pipe, for reference:

```
cd code/core && make
cat lark/lark-typing.lcore lark/lark-subst.lcore \
    lark/lark-step.lcore lark/lark-preservation.lcore \
    lark/lark-refine.lcore \
  | grep -v '^--' | grep -v '^$' | ./lcore
```

#### Weakening: `wk` in lcore (V3-WK0, 2026-07-16)

The substitution lemma requires **weakening**:

```
wk0 : Π(a : Ty). Π(g : Ctx). Π(t : Ty). Expr g t → Expr (ext a g) t
```

This inserts a new innermost type binding `a` into the context of every
expression without changing what the expression means. It is now defined
**in lcore** (`lark-subst.lcore`), by `indrec Expr` over an explicit de Bruijn
cutoff — `ins`/`shift`/`wk`, with `wk0 = wk … zero`.

**Why not the kernel primitive?** There *is* a C-level `weaken`
(`TM_WEAKEN` / `weaken_expr_val` in `code/core/eval.c`), and it was the
original weakening. But it is **opaque to induction**: on a constructor with
*neutral children* — exactly the shape an `indrec Expr` case hands you — it
`exit(1)`s (`weaken_expr_val: expected Expr VL_INDCON`), so the substitution
lemma could never be proved by structural recursion. The naive lcore attempt
that motivated the C primitive failed because the ELam case produced a body in
`ext a_lam (ext a g)` while needing `ext a (ext a_lam g)`, definitionally
distinct. The cutoff-indexed `ins` **dissolves** that mismatch:
`ins a zero g ≡ ext a g` and `ins a (succ m) (ext s g) ≡ ext s (ins a m g)`
hold *definitionally* (the succ case rides the outer `natrec` ih, not the
`indrec Ctx` one), so `wk`'s ELam case fires its IH at `succ n` and the goal
lands on the nose. `wk` computes one constructor-layer at a time — that is
what makes it inductable.

**The rebase.** `weaken_semctx_d`/`sub_open` now call `wk0` (same signature as
the kernel primitive — a drop-in), so `sub_ground`, and hence
StepBeta/StepLetBeta's contractum, are off the kernel primitive entirely: the
trusted base shrinks. The C `weaken`/`SP_WEAKEN`/`conv_spine` machinery remains
in the kernel but is **retired from the proof-critical path**.

**A latent kernel quirk this surfaced.** `wk0` agrees with the kernel `weaken`
by `refl` on payload-only trees, but on the Var case they diverge: front-insert
must send index 0 → index 1 (`here empty T ↦ there (ext T empty) T a (here…)`),
which `wk0`/`shift` produce; the kernel `weaken` prints a `there`-node carrying
the wrong sub-context. `wk0` is the correct de Bruijn semantics.

#### Semantic substitution design

`sub_open` generalises `sub_ground` by parametrising the *output* context:

```
sub_open : Π(g : Ctx). Π(t : Ty). Expr g t → Π(d : Ctx). SemCtx_d d g → Expr d t
sub_ground g t e env = sub_open g t e empty env
```

`SemCtx_d d g` maps each Γ-variable to an `Expr d t` (open in `d`).
The ELam case of `sub_open`:

1. Extends the output context with the lambda parameter: `ext a1 d`.
2. Places `EVar (ext a1 d) a1 (here d a1)` as the new innermost entry.
3. Lifts `env_d : SemCtx_d d g` to `SemCtx_d (ext a1 d) g` via
   `weaken_semctx_d a1 d g env_d`.
4. Recurses on the body with the extended open environment.

The motive `M g t _ = Π(d : Ctx). SemCtx_d d g → Expr d t` allows the IH
for the body to directly provide the function in the extended context,
avoiding any commutativity equation.
