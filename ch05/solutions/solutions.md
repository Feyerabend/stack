
## Chapter 5 — Solutions

Solutions to the exercises in Chapter 5, *Names, Scope, and Types*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (STLC derivation) | `ex01_stlc_derivation.py` | `python3 ex01_stlc_derivation.py` |
| 2 (Algorithm W, let-poly) | `ex02_algorithm_w.py` | `python3 ex02_algorithm_w.py` |
| 3 (occurs check) | `ex03_occurs_check.py` | `python3 ex03_occurs_check.py` |
| 4 (affine IO token) | `ex04_affine_io.py` | `python3 ex04_affine_io.py` |
| 5 (Copy trait) | `ex05_copy_trait.py` | `python3 ex05_copy_trait.py` |

Exercises 1–3 drive the chapter's teaching calculi
(`04_lambda_calculus/calculus/lambda.py`, `hm.py`); Exercises 4–5 drive the real
Lark checker ([lark/07/src/infer.py](./../../lark/07/src/infer.py)).
`1`/`+` and `true` are modelled as typed constants where a calculus lacks literals
— the standard STLC/HM treatment.


### Exercise 1 — STLC typing derivation

> Write the full typing derivation for
> `(λf:(Int→Int). f 1) (λx:Int. x + 1)`.
> Identify the rule at each node and the
> environment at each leaf. What is the type?

Model the primitives as constants: `one : Int`, `plus : Int → Int → Int`
(so `x + 1` is `((plus x) one)`). The derivation, with Γ = {one:Int,
plus:Int→Int→Int}:

```
                                                          (Var)        (Var)
                                              Γ,x:Int ⊢ plus:Int→Int→Int  Γ,x:Int ⊢ x:Int
                                              ───────────────────────────────────── (App)
                                  (Var)        Γ,x:Int ⊢ (plus x) : Int→Int        Γ,x:Int ⊢ one:Int (Var)
                              ───────────────────────────────────────────────────────────────── (App)
                                       Γ,x:Int ⊢ (plus x) one : Int
                              ─────────────────────────────────────── (Abs)
   (Var) Γ⊢f:Int→Int  (Var) Γ⊢one:Int        Γ ⊢ (λx:Int. x+1) : Int→Int
   ───────────────────────────── (App)        (right operand of the outer App)
   Γ,f:Int→Int ⊢ f one : Int
   ───────────────────────────── (Abs)
   Γ ⊢ (λf:(Int→Int). f one) : (Int→Int)→Int
   ────────────────────────────────────────────────────────────────────── (App)
   Γ ⊢ (λf:(Int→Int). f 1) (λx:Int. x+1) : Int
```

- *Leaves* are all `(Var)` lookups: `f` and `one` under `Γ,f:Int→Int`; `plus`,
  `x`, `one` under `Γ,x:Int`.
- *Rules:* `(Abs)` introduces each `λ` (extending the environment with the
  parameter); `(App)` eliminates a function type, requiring the argument's type
  to equal the parameter type.
- *Type of the whole expression: `Int`.* The outer abstraction has type
  `(Int→Int)→Int`; applied to the inner `Int→Int`, it yields `Int`.

`ex01_stlc_derivation.py` builds this term in the chapter's STLC checker and
confirms the parts (`Int→Int`, `(Int→Int)→Int`) and the result (`Int`).



### Exercise 2 — Algorithm W and let-polymorphism

> Trace Algorithm W on `let f = fn x => x in (f 1, f true)`: (a) fresh
> variables, (b) substitution after the lambda, (c) f's scheme after
> generalisation, (d) the instantiation at each call site, (e) the component
> types. Identify where let-polymorphism becomes visible.

Running the chapter's `hm.py` Algorithm W:

- *(a) fresh variables.* The generator hands out `t0, t1, t2, …` on demand.
- *(b) after the lambda.* Inferring `fn x => x` gives `x : t0` (fresh) and the
  body `x : t0`, so the lambda has type `t0 → t0` with the empty substitution
  (the identity imposes no constraints).
- *(c) generalisation.* At the `let`, `generalise` quantifies every variable
  free in `t0 → t0` but not in the environment, giving the *scheme
  `∀t0. t0 → t0`*.
- *(d) instantiation.* Each use of `f` instantiates that scheme with a *fresh*
  variable: `f 1` instantiates to `u → u` and unifies `u := Int`; `f true`
  instantiates to `v → v` and unifies `v := Bool`.
- *(e) component types.* `f 1 : Int` and `f true : Bool`, so the pair is
  `(Int, Bool)`.

*Where let-polymorphism becomes visible — the `generalise` step.* In the `Let`
case the value's type is passed through `generalise`, producing a scheme with
quantified variables; in the `Abs` case a parameter is bound monomorphically as
`Scheme((), tvar)` — no quantifiers. Only a generalised scheme can be
instantiated with a *different* fresh variable per use, which is what lets `f`
serve both `Int` and `Bool`. The lambda-bound form
`(fn f => (f 1, f true))(fn x => x)` is rejected, because the monomorphic
parameter `f` would have to be both `Int → _` and `Bool → _`.

`ex02_algorithm_w.py` shows the scheme `∀t. t → t`, the two component types, and
checks — in both the teaching `hm.py` and the real Lark checker — that the
*let-bound form typechecks* while the *lambda-bound form is rejected* with a
unification error.

(Working this exercise surfaced the *same* substitution-threading bug in `hm.py`
and in the production checker; both were fixed — see the appendix below.)



### Exercise 3 — The occurs check

> Construct a term that would trigger an infinite type without the occurs check.
> Show the unification steps, name the variable and the type, and explain why the
> infinite type is not a valid `Type`.

*The term: self-application `λx. x x`.* Inferring it (with `x : t0` fresh):

1. the function `x` has type `t0`; the argument `x` has type `t0`; a fresh `t1`
   is created for the result;
2. application unifies the function type with `arg → result`:
   `unify(t0, t0 → t1)`;
3. this tries to bind `t0 := t0 → t1`. The variable `t0` *occurs inside* the
   type it is being bound to, so the occurs check fires and inference fails.

*Why the infinite type is not a valid `Type`.* Expanding `t0 := t0 → t1` gives
`t0 = (t0 → t1) → t1 = ((t0 → t1) → t1) → t1 = …` — an infinitely deep tree.
`Type` is an *inductive* (finite) datatype: every `TypeVar`, `TypeConst`, or
`FunctionType` is built from strictly smaller finite types. No finite term
satisfies `t0 = t0 → t1`, so the equation has no solution in `Type`; the occurs
check is exactly the test that rejects it. `ex03_occurs_check.py` confirms both
the failed inference and the failing `unify(t0, t0 → t1)`.



### Exercise 4 — Double-consume of an affine IO token

> The checker raises `AffineError` on the final bare `io`. (a) trace the
> `Tracked` counts; (b) rewrite it correctly; (c) explain why shadowing a
> non-`Copy` binding is not a second use.

Lark's `let` binds a *name*, not a pattern, so the runnable version names the
discarded result `r` instead of `_`; the affine behaviour is identical.

*(a) `Tracked` counts (buggy version).*

```
fn two_prints(io : IO) : IO =
    let io = print(io, "hello") in   # rebind: the new io enters Tracked at 0
    let r  = print(io, "world") in   # reads io once  -> Tracked[io] = 1
    io                               # reads io again -> Tracked[io] = 2  -> ERROR
```

- After line 2: `{io: 0}` — the *new* token; the old one was consumed (read once
  inside `print(io,"hello")`) and then replaced.
- After line 3's `print(io,"world")`: `{io: 1, r: 0}`.
- At the final bare `io`: the read does `tracked["io"] += 1 → 2`, and `2 > 1`
  fires `AffineError('io')`.

*(b) The fix — thread `io`, shadowing it each step:*

```
fn two_prints(io : IO) : IO =
    let io = print(io, "hello") in
    let io = print(io, "world") in
    io
```

*(c) Why shadowing is not a second use.* A `let io = …` does not *read* the old
`io` a second time: the old token is read once (inside the right-hand side) and
then the name is *rebound*. In `infer.py`'s `LetExpr` case the rebinding runs
`tracked.pop(n, None)` — discarding the old counter — and, because `IO` is
non-`Copy`, installs a fresh `tracked[io] = 0`. Each shadow begins a brand-new
affine life at count 0; the only way to reach count 2 is to read the *same*
binding twice, as the bug does. `ex04_affine_io.py` runs both versions through
the real checker (buggy → `AffineError('io')`, fixed → OK).



### Exercise 5 — The `Copy` trait

> `impl Copy for T = {}` is always empty. (a) what does the checker do?
> (b) a `Point` with `Copy` used twice is fine; (c) a `Handle` without `Copy` is
> not — where does the error fire? (d) state the precise rule for entering
> `Tracked`.

*(a) What the checker does.* The empty body registers no methods. The
declaration's only effect is on the set `copy_types`: in `typecheck`'s pass 1,
`isinstance(decl, ImplDecl) and decl.trait_name == "Copy"` adds the implementing
type's name to `copy_types`. Thereafter `is_copy(t, copy_types)` returns `True`
for that type. `Copy` is a pure *marker* trait — it changes set membership and
nothing else.

*(b)/(c) Using a value twice.* `fn dup(x) = (x, x)` reads `x` twice. Whether
that is allowed is decided when `x` is *bound*: a binding enters `tracked` (at
count 0) only if its type is *not* `Copy`.

- `Point ∈ copy_types` → `is_copy(Point)` is `True` → `p` never enters `tracked`
  → the two reads are unconstrained → *OK*.
- `Handle ∉ copy_types` → `is_copy(Handle)` is `False` → `h` enters `tracked` at
  0 → first read → 1, second read → 2 → at the second read `tracked[h] > 1`
  fires *`AffineError('h')`*.

*(d) The precise rule.* A binding enters `Tracked` *iff its (concrete) type
is not `Copy`* — i.e. iff there is no `impl Copy for T` for that type. The
*presence* of the `Copy` impl keeps a binding out of `Tracked`; its *absence*
puts it in. No other trait affects this. `ex05_copy_trait.py` verifies both
programs and the `is_copy` mechanism directly.



### Appendix — the checker fixes this chapter prompted

Verifying Exercise 2 revealed the *same* bug in two places: the teaching
`hm.py` and the production `lark/07/src/infer.py` both *accepted*
`(fn f => (f 1, f true))(fn x => x)`, even though `f` is lambda-bound and should
be monomorphic.

*hm.py.* Its `App` (and `Let`) cases inferred the argument under an
*unsubstituted* copy of the environment. The fix adds `TypeEnvironment.apply`
(substitute the free variables of every scheme) and threads the substitution:
`env1 = env.apply(subst1)` before inferring the argument. All of `hm.py`'s
`main()` demos print byte-identical types afterwards; the lambda-bound form is
now rejected (`Cannot unify Int with Bool`) and let-polymorphism still works.

*[lark/07/src/infer.py](./../../lark/07/src/infer.py).* The same root cause:
the compound inference cases (`TupleExpr`, `Apply` arguments, `BinOp`, `IfExpr`,
`MatchExpr`) re-inferred each sub-expression under the *original* environment
instead of applying the accumulated substitution first. So a monomorphic
environment variable like `f : Scheme((), pv)` was never refined between its two
uses — each use unified `pv` independently, mimicking polymorphism.

The fix threads the substitution through the environment before each subsequent
sub-inference (`infer(_apply_env(s, env), …)`), which is the standard Algorithm W
discipline. After it:

- `(fn f => (f 1, f true))(fn x => x)` → *rejected* (`cannot unify Bool with
  Int`), while `let f = fn x => x in (f 1, f true)` still typechecks;
- the full lark/07 suite is unchanged: *test 76→77* (one added regression
  test `errors/09_lambda_mono.lark`), *difftest 31, repltest 31, typecheck 10,
  proptest 25, cektest 29* — all passing, no regressions.
