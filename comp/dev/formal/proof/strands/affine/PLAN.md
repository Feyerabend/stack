
## Strand — prove AFFINITY (the A in Lark)  M0–M2 SPINE DONE

> __Status:__ M0 (`Usage`/`LCtx`/`UseVar`), M1 (`HasA`), and __M2 the spine
> (`affine_sound : HasA g t g' → Consumed g g'`) are proven and green__ — `make affine` →
> 2 files / 0 errors, `make affine-controls` → 4/4 refused, main summit untouched. Built
> `SlotLe`/`Consumed` as __functional recursive predicates__ (no Id/J/inversion) and used
> __context threading__ (subsumes the `Split` sketched below — no partition relation needed).
> Story: `../../../LOG.md` ▲ STRAND-AFFINE. __Remaining, optional:__ M3 (the IO
> token `TIO`), the `Expr Γ τ`/`Ctx` erasure bridge, M4 (operational reading — named boundary
> if it walls). The rung ladder below is the original design; it stands as written.


__A new summit, not a fourth route to the old one.__ denot / solver / vdeep all
answer *what does a refinement derivation `HasR` buy?* — three roads to the same
peak. This strand asks a __different__ question: *what does Lark's affine discipline
buy?* Lark is the __Lambda Affine Resource Kernel__; affinity is the property that
names the language, and it is the one first-class mechanism the metatheory still only
*describes* (`../../lark/lark-formal.tex` lists "affine ownership" among the features
"not [yet] formalized"). This strand mechanizes it.

__File (to write):__ `lark-affine.lcore`. __Green bar (target):__ `make affine` →
N files / 0 errors; `make affine-controls` → all refused.

__Why before the book (the reason this is front-loaded, not a detour).__ Part III's
ch14 ("A Proof Checker in C") and ch15 ("Proving the Language") must currently list
affine ownership under *described, not formalized* — a hole in a Part titled *What the
Machine Can Promise*, for the very property in the language's name. Proving the affine
spine first lets those chapters __report__ it instead of deferring it. The book's
central claim gets stronger exactly where it is weakest. That payoff exists only if
the proof lands *before* the chapters are written — hence: affine → fixpoint → book.



### The property, precisely

__Affine soundness:__ a well-typed program consumes each affine-bound variable __at
most once__. Operationally, the resource that carries effects — the affine __IO
token__ `TIO` (`lark-formal.tex`: `TIO` is *no*-copy, affine) — is never duplicated,
so effect ordering is well-defined and purity of the non-IO fragment is preserved.

This is not a refinement property and not a type-*safety* property; it is a
*resource* property, orthogonal to both. It is well-trodden (affine/linear type
soundness) and therefore genuinely provable — the risk is lcore expressiveness, not
mathematics.

### The design (already sketched in the code)

`lark-typing.lcore:60–62` fixes the shape: __each `Var` node must consume its
variable__, modelled as a __linear context — a list with removal__. So the judgment
is context-*threading*: a context flows in, the used binding is removed, a smaller
context flows out. App __splits__ the context disjointly between function and
argument (the move that forbids sharing one affine var across both). This is the
standard input/output-context ("consumption") presentation of a linear type system,
and it is exactly what `infer.py`'s affine use-tracking already does dynamically.

### The ladder (spine first, wall-dodging — recurse on the DERIVATION, never invert `Step`)

| rung | content | teeth |
|------|---------|-------|
| __M0__ | `LCtx` = list of `(Var,Ty)`; `use : Var → LCtx → Option (Ty × LCtx)` (lookup-__and__-remove); `Split : LCtx → LCtx → LCtx → Type` (disjoint partition for App) | `use` on an absent/already-used var = `none` |
| __M1__ | `HasA : LCtx → Expr → Ty → LCtx → Type` — the affine judgment, context-in / context-out. `AVar` consumes (in has `x`, out lacks it); `AApp` threads left→right over a `Split`; `ALam` binds then requires the bound var consumed; `ALit` passes the context through untouched | ill-threaded context = unconstructible |
| __M2 — the spine__ | `affine_sound : HasA Γin e t Γout → Consumed Γin Γout` by `indrec HasA` — the __no-double-use__ invariant: `Γout` is `Γin` with each used binding removed exactly once; nothing is consumed twice, nothing reappears. Wall-free: recursion is on `HasA`, lands in structural facts about `LCtx`. | the summit |
| __M3 — the IO token__ | `TIO` as an affine resource: an effectful path threads one world token; `affine_sound` specialized shows it is consumed exactly once → no duplicated effect, sequencing is linear | forge a program that copies the token → refused |
| __M4 — boundary (optional)__ | the *operational* reading (an affine value is never reused at __run time__) needs `Step` in scope and risks the DESCEND wall (positive `Step` inversion under `indrec`). __If it walls, name it and stop__ — M2's structural soundness is the honest floor, the same way denot stops at soundness-not-adequacy. | — |

### Negative controls (what keeps the green bar honest)

At least four deliberate lies the kernel must refuse:
1. __double-use forge__ — the same affine `Var` consumed in both halves of an `AApp` (no valid `Split` exists) → unconstructible;
2. __non-consuming Var forge__ — an `AVar` whose out-context still holds `x`;
3. __resurrection forge__ — a binding absent from `Γin` reappearing in `Γout`;
4. __IO duplication forge__ — the world token threaded into two consumers.

A controls PASS = the kernel refused *all* of them; that is what stops M2 from being
vacuous.

### Named boundaries (declared up front, not discovered as gaps)

- __Structural, not operational__ (M2 vs M4): first summit proves the *discipline* is
  internally sound (linear consumption), not the *runtime* no-reuse — the latter is
  M4, walled or not.
- __Affine, not full linear/borrow:__ Lark is affine (use *at most* once), not linear
  (*exactly* once) and has no regions/borrows; the proof targets what the language
  has, nothing more.
- __Effects = the IO token only:__ purity of the non-IO fragment is a *consequence*
  of the token being the sole affine resource, not a separately axiomatized claim.

## Definition of done

1. `lark-affine.lcore` type-checks: `make affine` → 0 errors.
2. `make affine-controls` → all forges refused.
3. A payoff fixture pair: a real __double-use rejected__, a real __linear use
   accepted__ (the affine analogue of the strands' smoke terms).
4. `strands/SUMMARY.md` gains the row; `LOG.md` gets the dated story.
5. ch14/ch15 can now __report__ affine soundness as mechanized — update those stubs'
   author-notes to say so (done when the book reaches them).
6. Not committed (Set commits).

*If it does not complete:* this PLAN stands on its own as reviewable design, and the
walled rung becomes a named boundary — same contract as the other strands.
