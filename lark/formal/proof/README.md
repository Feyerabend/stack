
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
  parsed : succ (succ zero)
  type   : Nat
  normal : succ (succ zero)
> :i Π(A : Type). A → A
  term   : Π(A : Type). A → A
  type   : Type_1
  normal : Π(A : Type). A → A
> :let id = (\A x. x : Π(A : Type). A → A)
  id : Π(A : Type). A → A
```

Commands: a bare term is type-checked, then normalised — a term whose
type cannot be inferred is an error, so `(star : Empty)` is rejected,
not normalised.  `:i e` infers and prints the type of `e`.  `:let name
= expr` adds a global definition (expr must be inferrable).  `:nf e`
normalises WITHOUT type checking (the untyped-NbE playground; `:nf
(\x. x x) (\x. x)` is fine here and only here).  `:t` runs the built-in
self-tests.  Any failed line makes the process exit non-zero, so a
piped run of a proof file fails loudly.

For the graph-reducer layer:

```
cd code/lang && make && ./llang
:load "lib/prelude.lam"
```

llang is a *programming language*, not a proof checker: it has `fix`
(via `let rec`), so its type system is deliberately inconsistent as a
logic, and bare expressions and unannotated `let`s reduce without type
checking — it is a runner.  Proof claims belong in lcore, which refuses
`fix` outright (see step 9.12 note below).



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
| `lark-affine.lcore` | Graded ({0,1,ω}) affine typing: `Grade`, `GCtx`, `GVar`, `GExpr`; `no_use_in_erased`, `capture_rejected`, `no_second_use` |
| `lark-weaken.lcore` | `weaken_l`: positional-insertion weakening, discharging the `TM_WEAKEN` kernel primitive (and documenting the bug found in it) |
| `lark-subst.lcore` | Semantic environments, substitution, value predicate |
| `lark-erase.lcore` | Id-toolkit (via `J`); `erase : GExpr → Expr`; `strip_demote`; `graded_eval_sound` — the affine layer inherits the STLC dynamics |
| `lark-step.lcore` | Small-step reduction (`Step`), multi-step (`Eval`) |
| `lark-preservation.lcore` | `eval_produces_val`: every evaluated term is a value |
| `lark-formal.tex` | Typeset account of the proof (build with `tectonic`) |

#### Running the proofs

```
cd code/core && make
cat lark/lark-typing.lcore lark/lark-affine.lcore \
    lark/lark-weaken.lcore lark/lark-subst.lcore \
    lark/lark-step.lcore lark/lark-preservation.lcore \
    lark/lark-erase.lcore \
  | grep -v '^--' | grep -v '^$' | ./lcore
```

The exit code is the verdict: `0` means every `:let`, bare claim and
`:i` query in the stack type-checked; any failure prints its error and
the run exits `1` (`lcore: one or more inputs FAILED`).  This is strict
since the step 9.11 fix — previously bare (non-`:let`) terms were
normalised without type checking, so `(star : Empty)` slipped through
and greenness rested on the discipline of routing every claim through
`:let`.

Relatedly (step 9.12): `fix` — general recursion, which the llang layer
needs for `let rec` — used to live ungated in the shared parser and
checker, so lcore accepted `(fix (\x. x) : Empty)` as a proof of Empty.
The kernel now refuses `fix` on every path (`core_allow_fix`, default
closed); only llang, a partial programming language rather than a proof
checker, opens the gate at startup.

#### The affine layer (`lark-affine.lcore`, Phase 9)

The layer deferred by `lark-typing.lcore` is now mechanised as a graded
type system over the {0, 1, ω} semiring (QTT's grades; the affine
fragment uses the order, `gplus`/`gtimes` are defined and law-tested for
the Track B elaboration).  The judgment is *leftover typing* —
`GExpr g t g'` consumes usage budget `g` and returns leftover `g'` —
because that is literally what `infer.py`'s `tracked` dict does,
including its conservative sequential threading through both branches of
an `if`.  The lambda rule **demotes** the enclosing context (grade 1 → 0)
before checking the body: closure capture of an affine variable, the
soundness hole found by the Phase 9 hardening review, is impossible by
construction, and demotion is exactly where the 0 grade enters.  The
central theorem, `no_use_in_erased`, shows a variable lookup in a
fully-erased context is `Empty`; its corollaries replay error test 16
(`capture_rejected`) and property P1 (`no_second_use`) at proof level.
The dynamic side is closed by `lark-erase.lcore`: an erasure functor
`erase : GExpr g t g' → Expr (strip g) t` maps every graded derivation
to the STLC expression it refines, so closed graded programs inherit
the whole dynamic stack — `Step` (intrinsically type-preserving),
`Eval`, and `eval_produces_val` (`graded_eval_sound`).  The blocker
`strip (demote g) ≡ strip g` fell to a ten-line `Id`-toolkit (`sym`,
`trans`, `ap`, `transport`, all instances of `J`) plus one induction;
the leftover-context mismatches in the application, let, and if cases
fall to the companion lemma `gexpr_preserves_types` (grading consumes
grades, never bindings).  Affine soundness itself stays static: graded
programs that would duplicate a resource do not exist to be erased.

#### The `weaken` kernel primitive — DISCHARGED (Phase 9)

The substitution lemma requires **weakening**:

```
weaken : Π(a : Ty). Π(g : Ctx). Π(t : Ty). Expr g t → Expr (ext a g) t
```

This was the proof's one trusted-base hole: a C-level primitive
(`TM_WEAKEN` / `weaken_expr_val` in `code/core/eval.c`), used because a
naive lcore implementation via `indrec Expr` fails — the ELam case
produces a body in context `ext a_lam (ext a g)` but needs
`ext a (ext a_lam g)`, and these are definitionally distinct.

**The discharge** (`lark-weaken.lcore`): generalise the statement to
insertion at an arbitrary *position*, computed by a recursive function —
`insert pz a g = ext a g`, `insert (ps n) a (ext s g) = ext s (insert n a g)`.
Under a binder the recursion moves to position `ps n`, and the required
context equation holds *definitionally*; the ext-commutativity problem
never arises.  `weaken_l` is the head-position specialisation, a pure
checked lcore term with exactly the primitive's type.  `lark-subst.lcore`
now uses `weaken_l`; no proof depends on `TM_WEAKEN`.

**The bug the discharge found.** The two implementations disagreed on
variables — and the *kernel* was wrong: `shift_var_val`'s here-case at
cutoff 0 passed `g` as `there`'s first argument where the inner
variable's context `ext t g` is required, producing an ill-typed value
the kernel never re-checks (primitive outputs are trusted).  The
kernel's own type checker rejects the term the primitive built.  The C
code is fixed (all 339 kernel self-tests pass), but the structural
lesson stands: every earlier proof run that weakened a variable
manipulated ill-typed evidence, and only discharging the primitive —
forcing an independent, fully-checked implementation to exist — made
the divergence observable.  Same pattern as the compiler's certifying
register allocator: don't trust, check every answer.

**Syntax in `.lcore` files:**
```
weaken sigma Delta tau e    -- e : Expr Delta tau  →  result : Expr (ext sigma Delta) tau
```

**Neutrals.** When `e` is a neutral (bound variable during type-checking),
`weaken` records a `SP_WEAKEN` spine entry and returns a neutral value.
This ensures the bidirectional type checker can check lambdas in
`weaken_semctx_d` against their annotated type without crashing.
`conv_spine` (in `check.c`) compares `SP_WEAKEN` entries by their three
parameters (`a_ty`, `ctx_g`, `ty_t`) so that definitional equality is
not falsely asserted between `weaken` applications at different types.

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
