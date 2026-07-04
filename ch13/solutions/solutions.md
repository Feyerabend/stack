
## Chapter 13 — Solutions

Solutions to the exercises in Chapter 13, *The Adversary*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|----------|------|-----|
| 1 (defined semantics, well-foundedness) | `ex01_wrapping_descent.py` | `python3 ex01_wrapping_descent.py` |
| 2 (the generator and its blind spots) | `ex02_edge_bias.py` | `python3 ex02_edge_bias.py` |
| 3 (the certificate) | analysis below | — |
| 4 (graded typing) | `ex04_graded_typing.py` | `python3 ex04_graded_typing.py` |
| 5 (the kernel's three failures) | analysis below | — |

`ex04` drives the real proof kernel against the real graded model
(`lark/formal/proof/lark/lark-affine.lcore`), and reads its verdicts from
the exit code — the machine-checkable strictness that section 13.6
installed. Per the chapter's boxed principle, the script checks both
directions: a claim that must be accepted and a claim that must be
rejected.


### Exercise 1 — Defined semantics as the precondition for testing

**(a) Why an `XFAIL` table poisons a differential oracle.** The oracle's
entire value is one implication: *divergence implies bug*. P7 states it
universally — every generated program, byte-identical output on every
back end. An excuse table replaces that theorem with "divergence implies
bug, *unless* the divergence is of a kind we have decided to expect," and
the exception is defined in terms of behaviour (overflow), not in terms
of programs. So when a fuzzer finds a divergence, the alarm no longer
carries a verdict; a human must adjudicate whether this is a *new* bug or
the *old* excuse, and adjudication is exactly the manual step that
unbounded generation cannot afford. Worse, the excuse can shelter real
bugs: a genuine RV32 miscompilation whose symptom happens to look like
overflow disagreement is filed under the exemption and never seen.
Defining the semantics deletes the middle case: after Phase 8, a back end
that disagrees on any program is simply wrong.

**(b) `n - 1` is not well-founded on wrapping i32.** A relation is
well-founded exactly when it admits no infinite descending chain. On a
wrapping i32, the "descent" step `n -> n - 1` is a bijection whose orbit
is a single cycle through all 2^32 values:

    0 > -1 > -2 > ... > INT_MIN > INT_MAX > ... > 1 > 0 > -1 > ...

Follow the chain long enough and it returns to its start; a cycle *is* an
infinite descending chain, so no measure into the naturals can strictly
decrease along it, and no totality checker can certify the step. The
failure is not only metatheoretic: stepping by 2 preserves parity, and
2^32 is even, so `f(n) = if n == 0 then 0 else f(n - 2)` from any odd `n`
visits odd values forever and never meets its base case — a concretely
non-terminating countdown. (`ex01_wrapping_descent.py` demonstrates both:
the wrap at `INT_MIN`, and ten million parity-preserving steps that never
reach 0.) This is why the checker's diagnostic says *recurse on data, not
on integers*: constructors do not wrap, so structural descent is
well-founded by construction.

**(c) A rule that would accept integer countdowns.** The checker would
have to recover a genuine natural-number measure from flow information —
in effect, *bounded descent*: accept a recursive call `f(n - d)` (with
`d` a positive constant) as decreasing when

1. the call site is **dominated by a guard** that establishes `n > b` for
   some base bound `b` (every path from the function's entry to the call
   passes the test);
2. the step **cannot wrap in the guarded range** — `n - d` stays above
   `INT_MIN`, which the guard `n > b` gives as long as `b >= INT_MIN + d`;
3. the measure `n - b`, now a value in the naturals, **strictly
   decreases** by `d` at every such call.

Each condition is checkable, but note what the rule has become: a small
flow-sensitive range analysis attached to the totality checker — a first
step toward refinement types, where "an `Int` known to be positive" is a
type the checker can speak. Lark's v1 declines the machinery and keeps
the honest, smaller rule; the exercise shows the price of accepting
integer descent is real analysis, not a special case.


### Exercise 2 — The generator and its blind spots

**(a) Why generate-then-filter fails under affine types.** "Generate
random ASTs, keep the ones that typecheck" makes well-typedness a lottery
rather than an invariant, and the affine discipline collapses the odds.
A random program is well typed only if *every* variable use is
type-consistent **and** the `IO` token threads linearly through the whole
of `main` — one use per binding, re-bound at each step, never duplicated,
never dropped into a dead branch. Each additional statement multiplies in
another improbability, so the survival rate decays exponentially with
program size: the filter passes almost nothing but trivial programs, and
the back half of the compiler — lowering, allocation, code generation,
exactly where section 13.2's bug lived — is never exercised. (Shrinking
breaks too: shrinking a filtered value has no reason to preserve
typedness, so counterexamples degrade into rejected programs.) Inverting
the rules makes both properties invariants of construction: every
generated program typechecks and threads its resources, so the entire
generation budget lands past the frontend.

**(b) Another under-sampled corner, and its bias.** Section 13.1 pins
three division identities, and two of them live at a single point:
`INT_MIN / -1 = INT_MIN` and `INT_MIN % -1 = 0`. A uniformly random
32-bit operand is `INT_MIN` with probability 2^-32 — the same corner
problem as the zero divisor, but sharper. The bias that covers it: draw
integer *literals* from the edge set `{0, 1, -1, INT_MIN, INT_MAX}` some
fraction of the time (and, for division specifically, pair an `INT_MIN`
numerator with a `-1` divisor deliberately). The planted-mutation check
that validated the divisor bias applies unchanged: plant
`INT_MIN / -1 = 0` in one back end and confirm the biased generator
catches and shrinks it; a bias that has never been seen to catch its
planted bug is as much a hope as the fuzzer it tunes.
(`ex02_edge_bias.py` models why the corner is invisible to uniform
generation and near-immediate under bias.)

**(c) What excluding `Float` makes invisible, and what must be unified
first.** Every miscompilation whose symptom is a floating-point value is
outside the generator's sight: wrong rounding of intermediates, a backend
computing in the wrong width, mishandled `NaN`/negative-zero/infinity in
comparisons or in the simplifier's algebra (exactly the trap Chapter 8
flagged — `x + 0.0` is not `x` at `-0.0`), and formatting divergence in
`show`. The blocker is that the back ends do not agree on what `Float`
*is*: the CEK rounds through single precision while the TAC machine
computes in Python doubles, so random float programs would diverge *by
design* and drown real signals in false alarms — an `XFAIL` table by
another name. The unification must come first: one width (f32,
matching the RV32 target) enforced in every runtime, bit-stable
formatting, and defined comparison semantics for the specials; then
`Float` can enter the generator with its own edge set
(`±0.0`, `NaN`, `inf`, denormals) and its own planted mutation.


### Exercise 3 — The certificate

**(a) A liveness bug that fools the correlated oracle.** Suppose
`liveness.py` drops the loop's back edge — the successor map forgets that
the conditional jump at the loop's bottom can return to the header. Then
a temporary `t1` defined before the loop and used inside it on the next
iteration appears dead after its last *textual* use: its live interval
ends mid-loop. The allocator, consuming that analysis, reuses `t1`'s
register for a loop-local `t2`; on the second iteration `t1`'s value is
gone. Now ask the old `verify()`: it derives interference from the same
`cfg.py` + `liveness.py`, sees the same truncated interval, finds no
overlap, and approves. Both sides of the check read the same wrong fact —
correlated error, silent approval. `regcheck` is immune by construction:
it never consults `cfg.py`, but rebuilds successors from the labels in
the flat instruction list and runs its own backward fixpoint, so `t1` is
live around the back edge in *its* analysis, and the write to the shared
register violates R3 at a named instruction.

**(b) Why R3 needs the dead-def clause.** Consider:

    t1 = 5          ; allocator: t1 -> s1
    t2 = t1 + 0     ; t2 never used; allocator (buggy) also picks s1
    print(t1)

`t2` is dead everywhere — it is live at no program point — so the plain
exclusivity condition "simultaneously live temporaries occupy distinct
registers" is satisfied vacuously. But the second instruction still
*writes* `s1`, and `t1`, which is live across it, is destroyed: `print`
emits garbage. Hence R3's second clause: no instruction may write a
register that a *different* live-out temporary occupies, whether or not
the written temporary is itself live. Dead code computes nothing, but it
still clobbers.

**(c) Certificate versus verified allocator.** The proof is the stronger
statement: it quantifies over *all* inputs, once and forever, including
programs no fuzzer will ever generate. But it is a statement about one
implementation — change the allocator (linear scan to graph colouring, a
new spilling heuristic) and the proof is re-opened, and for an allocator
the mechanisation cost is serious. The certificate is the weaker
statement made where it matters: it guarantees nothing about the
allocator in general and everything about *this compilation* — which is
precisely what the user of the emitted binary needs — and it survives any
rewrite of the allocator unchanged, because it checks outputs against the
spec, not the algorithm. The engineering answer is the chapter's:
translation validation on every run, stress-fed by the fuzzer, with the
proof reserved for the small core where it is affordable. (CompCert sits
at one end of this trade; Lark, deliberately, at the other.)


### Exercise 4 — Graded typing

**(a) The derivation for `fn(x : Int) => x + x`.** `Int` is `Copy`, so
`x` enters the context at grade ω. Reading the leftover judgements
top-down (Γ before use ⇒ Γ after):

    x : Int @ ω  ⊢  x  :  Int   leaves  x @ ω      (gv_herew: ω is free)
    x : Int @ ω  ⊢  x  :  Int   leaves  x @ ω      (gv_herew again)
    ─────────────────────────────────────────────
    x : Int @ ω  ⊢  x + x : Int  leaves  x @ ω
    ─────────────────────────────────────────────
    ⊢  fn(x : Int) => x + x  :  Int -> Int          (GELam, q = ω)

In semiring terms the two uses demand `1 + 1 = ω`, and ω is exactly what
a `Copy` binding supplies — the equation that rejects an affine double
use is the same one that licenses this. The model has no `+`, so the
kernel-checkable twin replaces it with the structural equivalent
`let y = x in x` (two lookups of `x` through `gv_herew`, one of them
stepping over the binder with `gv_there`); `ex04_graded_typing.py`
submits it and the kernel accepts, printing its type.

**(b) Where the capture counterexample gets stuck.** For
`let g = fn(x : Int) => io in (g(1), g(2))` the enclosing context is
`io : IO @ 1`. `GELam` does not check its body in that context — it
checks it in `demote g`, where every grade-1 entry is knocked to 0: the
body sees `io : IO @ 0`. The body's reference to `io` now needs a `GVar`
derivation whose context entry has grade 0, and there is none:
`gv_here1` requires grade 1, `gv_herew` requires ω, and a rule for G0
was deliberately never written — the missing rule *is* the capture ban,
the proof-level twin of `AffineError`. `ex04_graded_typing.py` submits
exactly such a grade-0 lookup and the kernel rejects it (exit 1). Note
the shape of the mechanism: the counterexample is not caught by a check
that runs, but excluded by a derivation that cannot be built — the same
trick that made preservation unstatable-wrongly in Chapter 11.

**(c) A lambda called at most once.** The closure itself would need
grade 1: an *affine function*, a `⊸`-arrow whose values the context
tracks exactly as it tracks `io` — created once, consumed by its single
call, never duplicated. That is grades on the function type (the
multiplicities of quantitative type theory), not just on bindings.
"Called at most once" is harder than "captures nothing" because it is a
global property of every place the closure *flows*: stored in a tuple,
passed to a helper, returned from a function, each alias is a potential
second call, so the checker must track the closure value affinely through
the whole program. "Captures no affine variable" is decided locally, in
the `Lambda` case of `infer`, by looking at the body's free variables.
Lark chose the check it could make airtight in one place; the graded
model shows what the global version would cost, and QTT is where that
road leads.


### Exercise 5 — The kernel's three failures

**(a) Why intrinsic typing could not protect against the `weaken` bug.**
The intrinsic encoding guarantees that ill-typed *derivations cannot be
constructed inside the theory*: every constructor application is checked,
so garbage cannot be built. `TM_WEAKEN` was not inside the theory. It was
a C function that manufactured a value and *asserted* its type index; the
kernel injected the result into checked developments without re-checking
it, because primitive outputs were trusted by definition. Indices protect
construction, not assertion — a typed interface does not check an
implementation that bypasses the type checker. That is what "trusted
computing base" means operationally: the intrinsic discipline's
guarantees are conditional on every primitive below it, and the weaken
episode measured the condition's worth. The repair was structural, not
just a bugfix: discharge the primitive so no proof depends on the
assertion at all.

**(b) Inconsistency, and why one inhabitant of `Empty` is the end.**
A proof checker is *consistent* when there is no closed term of type
`Empty` — when falsehood has no proof. Suppose one exists: some
`bad : Empty`. `Empty` has no constructors, so its eliminator has no
cases to supply; for any proposition `P` whatsoever,
```
    absurd P bad  :  P        (indrec Empty with motive P — zero cases)
```
is a checked proof of `P`. Every theorem in the stack, its negation, and
`Id Nat 0 1` are all now provable, all green. "Checked by the kernel"
ceases to distinguish true from false, retroactively — including for
every proof checked before anyone wrote `fix`. That is why the gate is
not a feature toggle but the wall around the logic, and why the boundary
between the total kernel and the partial `llang` must be checked, not
documented.

**(c) The remaining trusted base, and what to attack next.** After
Chapter 13 the list is: (1) the `lcore` kernel's ~8,000 lines of C —
self-tested, strict at its front door, `fix`-gated, one primitive
discharged, but still the single unverified judge of every proof;
(2) the C compiler and libc beneath it; (3) the Python interpreter that
runs the Lark compiler itself; (4) the operating system and the silicon
of Chapter 1 — with Thompson's lecture standing warrant that the list
never reaches empty. The right next target is the kernel's
conversion-and-normalisation core, on the chapter's own evidence: it is
where the kernel's bug history lives (the spine-equality bug found in
Phase 5's hardening, the weaken value bug, the unchecked front door, the
`fix` reachability), it is the least redundant component — nothing
cross-checks a normal form — and it is exercised by every single proof.
The attack follows the de-correlation principle: a second, independent
normaliser (different author, different language, different algorithm —
a hundred-line NbE in Python suffices for the proof stack's fragment)
re-checking every accepted `:let` and every conversion the kernel
performs on the seven-file stack, with planted wrong normal forms to
validate the validator. Agreement between two uncorrelated
implementations is not proof — but it is exactly the kind of evidence
this chapter has been buying all along, at the one place where the book
currently owns none of it.
