
## `08/` — the refinement fork of the oracle

This is the tree the *PROVE* axis owns ([`../../PROVE.md`](../../PROVE.md)): where
refinement types (`{ v : Int | v >= 0 }`), verification-condition generation and
the QF-UFLIA decision procedure get built, in Python, before any of it is ported
to Lark.

It started life as a *copy of `07/src`* and nothing else. *V1 is now complete*:
Lark can state a contract, and the checker can prove it.

### The one rule

> *`07/src` is frozen. This tree forks it; it never edits it.*

`07/src` is the reference that every differential in `self/`, `optimize/` and
this tree compares against, and three fixpoints are pinned to its exact bytes —
`49a4921c` (emit-only bootstrap), `829410dc` (typechecking bootstrap), `f1dedfa9`
(the optimizing self-application). A reference that moves is not a reference.

So `08/` relates to `07/` exactly as `self/` does: *a differential, not an edit.*

### What V1 added

Three modules are new, and they are layered so that each one can be wrong without
the one below it being wrong:

| module      | what it is                                                        |
|-------------|-------------------------------------------------------------------|
| `pred.py`   | the predicate language — QF-UFLIA: linear integer arithmetic, booleans, uninterpreted functions with equality. Multiplication is *literal × term* only, so `x * y` is not a term you can write; PROVE §7's "resist nonlinear arithmetic" is enforced at well-formedness, not hoped for. |
| `solver.py` | the decision procedure, from scratch — congruence closure (union-find + signature saturation) and the *Omega test* (equality elimination, then Fourier–Motzkin with real shadow, dark shadow and *splinters*), under a DPLL(T) boolean search. No Z3; the plan's `--smt` escape hatch was not needed and was not built. |
| `refine.py` | the VC generator — bidirectional `synth`/`check`, subtyping as entailment, path conditions through `if`/`let`/`match`, dependent function contracts. The only module that ever asks `solver.valid()`. |

Three modules are *extended*, and the third of them by a single line:

| module      | the change                                                        |
|-------------|-------------------------------------------------------------------|
| `tree.py`   | `TRefine` joins the syntactic `Type` union                        |
| `parser.py` | `{` begins a type; LL(1) survives, because `{` begins no other type and predicates contain no `\|` |
| `infer.py`  | `syntype_to_mono` *erases* `TRefine` to its base type             |

That one line in `infer.py` is the entire interface between the refinement layer
and the language. The predicate is never traversed by inference, so a name it
mentions is never `infer`red — and that is what settles the affine question below.

### The affine x refinement rule

PROVE §7 asked for this to be settled early, before the VC generator hard-coded an
answer. It is:

> *Naming an affine binding in a predicate is a MENTION, not a USE. Predicates are
> use-neutral: they never consume.*

It holds *by construction*, not by a check — refinements erase before inference
walks them, so a predicate cannot increment a use count. It is *sound* because
affinity in Lark restricts *use, not truth*: Lark is pure, so consuming a value
moves it, it does not mutate it, and a fact proved about an affine binding stays
true for its whole scope. In a language with mutation the rule would be unsound.
The permission is paid for by purity and nothing else. (`prove/06_affine_mention.lark`
makes the claim; `06_affine_control.lark` shows the binding really is affine.)

The sharper half, which the literature is thin on: *the predicate is free, but the
runtime guard that establishes it is not.* `if size(b) > 0 then take(b, 0)`
*evaluates* `b` and then passes it on — two uses — so the affine checker rejects it
(`prove/07_affine_guard.lark`). The borrow idiom that fixes the affine error
(`size_of(b) : (Int, Buf)`) typechecks and still could not be *proved* under V1,
which had no refined tuple components (`prove/07_affine_borrow.lark`). Affine and
refinement are individually fine and jointly blocked for non-Copy types. That is a
*V2 requirement derived rather than guessed*: refined products.

*V2.0 built them, and the borrow file went half way — which is the finding.* The
*consumer* is now proved: `size_of`'s contract promises `n == size(b)` and
`size(b2) == size(b)`, the tuple pattern delivers both facts into the arm, and
`take(b2, 0)`'s bound follows from the guard. The *producer* — `size_of`'s own body —
still cannot be, because it needs `size(Buf(n)) == n`, and nothing in the logic says
that taking a buffer apart and putting it back together preserves its size. That is a
*measure* equation, and it is V2.2. Stated once, because it is the sentence that
organises the rest of the milestone: *refined products let a fact travel; only a
measure can create one.*

### What V2.1 added: the measure declaration

```
    measure len(xs : List(Int)) : Int =
      match xs with
      | Nil           => 0
      | Cons(_, rest) => 1 + len(rest)
      end
```

A measure is *not an `fn`*, and refusing to make it one is the whole design. It is
*ghost* (it erases, as a refinement does), it must be *structural* and *total*, and its
body must live in the *predicate fragment* — three restrictions an ordinary function
does not carry. Were measures just functions, we would owe the reader an account of
why some `fn`s may appear in a predicate and others may not, and there is not a good
one.

Two things fall out, and both were cheaper than expected:

- *Erasure is by construction.* A `MeasureDecl` lives in `Program.measures` and
  never in `Program.decls`, so `infer.py` and the CEK machine never see one. There is
  no erasure *pass*; there is nothing to erase. The corollary comes free: calling a
  measure from real code is an unbound-name error from HM, not a rule anyone wrote.
- *The lexer did not move.* `measure` is a *contextual* keyword. A declaration could
  never begin with a bare `NAME` before, so the only token stream this newly accepts is
  one that used to be a syntax error — and the oracle's frozen lexer keeps a word it has
  no business knowing about out of its keyword table.

*The arms become AXIOMS, and that is why well-formedness is not optional.* A
non-terminating *program* function is harmless: it returns nothing, so its contract is
vacuously kept, and V1 already leans on exactly that. A non-terminating *measure* is
fatal — `len(xs) == 1 + len(xs)` is an inconsistent axiom set, and from an
inconsistency the checker proves every goal put to it, including the false ones.
*Termination is optional for a contract and mandatory for a measure.* So
`Refiner._elab_measure` enforces one arm per constructor (exhaustive and
non-overlapping), recursion only on the fields of the constructor matched, arm bodies
translated *strictly*, a result sort of `Int` or `Bool`, and a name that belongs to
nothing else in the logic. Seven negative fixtures (`prove/11_measure_*.lark`) hold
that line, each failing as *malformed* rather than *unproved*; the first of them,
`11_measure_nonstructural`, carries a false contract that a checker admitting the
measure would happily prove.

What V2.1 does *not* do is hand the equations to the solver. But declaring the
measure is already what lets its name into a contract at all: under V1 `len` had no
sort, so `len(v) > 0` was not a predicate, and the file was a refinement *error*
rather than an unproved program.

### What V2.2 added: the equations, and nothing else

*No solver change. No parser change. No lexer change.* Every line of this rung is in
`refine.py`, and it turns on one move that costs nothing:

> *A constructor is a TERM.* `Cons(x, xs)` becomes the uninterpreted application
> `Cons(x, xs)` — and that is all it takes, because the solver already decides
> equality and congruence at *any* sort. A constructor needs no new theory. It needed
> a *name*, and until V2.2 it did not have one, which is why `len(Cons(3, Nil))` was
> a term about a value the logic could not point at.

Congruence gives a constructor what it deserves and no more: equal fields build equal
values. It does *not* give injectivity, and we do not assert it — nothing needs it, and
an axiom nobody needs is an axiom nobody has checked.

With terms in hand, a measure's arms are *instantiated at the constructor terms the
obligation mentions, and nowhere else*:

```
    len(Cons(3, Nil)) == 1 + len(Nil)      because the program wrote Cons(3, Nil)
    len(Nil)          == 0                 because that term is inside the one above
```

There is no axiom schema, no trigger, no e-matching, and above all *no quantifier* —
`forall xs. len(Cons(x, xs)) == 1 + len(xs)` would leave QF-UFLIA and take the decision
procedure with it. What the checker writes down instead is the quantifier-free shadow
of that axiom. The set is finite, and *it closes in a single pass*, for a reason worth
saying out loud: the subterms of a constructor term are constructor terms, and an arm
may only recurse on a *field* — a term the walk has already seen. *V2.1's structural
check, which was there to keep the axioms consistent, turns out to be what makes them
terminate as well.*

That leaves two ways, and only two, for a constructor term to enter a VC — the plan's
two hooks:

| ways          | moves                                                                      |
|---------------|----------------------------------------------------------------------------|
| *Building*    | `Cons(x, xs)` synthesises `{v \| v == Cons(x, xs)}` (`Refiner._synth_con`) |
| *Destructing* | `\| Cons(x, rest) =>` assumes `xs == Cons(x, rest)` (`_walk_match`)        |

Note what the second is *not*. It does not assume `len(xs) == 1 + len(rest)`. It says
the humbler thing — *what the scrutinee is* — and the equation follows on its own,
because the term is now in the hypotheses and the instantiation walk finds it there.
One mechanism, fed from two places, rather than two mechanisms that have to agree.

And the negative half of a constructor pattern is *left on the table, deliberately*.
"The scrutinee was not `Cons(x, rest)`" mentions binders that exist only inside that
arm, and the fact one actually wants — "it was not a Cons *at all*" — needs constructor
*disjointness*, an axiom the logic does not have. A literal pattern's negative
information is free; a constructor's is not. (Compare V1: *the predicate is free; the
guard that establishes it is not.* The same shape, one level down.)

#### The two findings

*1. Naming is not opening — and a fact needs a name to leave a function.* V2.2 did not
work at first, and the reason was upstream of measures. `| Cons(_, r) => r` computes a
list the logic knows the length of, and then returns it as a value the logic has never
heard of: an ADT-typed binder was `ROpaque`, so `synth` could not *selfify* it, and the
hypothesis `$v == r` was never written down. The fix is V2.0's own permission applied one
level further — a value the logic cannot *open* it can still *name* (`rtype_of_mono`
now knows the program's ADTs). It costs nothing: the binder is sorted `OTHER`, so
`_int_term` keeps it out of arithmetic, and the only operations left are equality and
uninterpreted application. So: *refined products let a fact travel; a measure creates
one; a name is what carries it out through the return.*

*2. The fresh-variable supply was not fresh, and a bare `except` hid it.*
`_bind_pattern` built a *new `ty.Fresh()` on every call*, whose counter restarts at 0
and therefore collides with the type variables already inside the schemes. `instantiate`
then mapped a scheme's quantified `α₀` to a "fresh" `α₀`, and `ty.apply` chased `α₀ ↦ α₀`
until Python ran out of stack — where an `except Exception` swallowed the `RecursionError`
and bound *nothing*. So a constructor pattern over a *polymorphic* ADT gave its binders
no types at all, silently, in V1, V2.0 *and* V2.1. A *monomorphic* one (`| Buf(n) =>`)
was always fine, because `instantiate` returns early when there is nothing to quantify —
which is why the suite, `Buf`-shaped as it was, never noticed. The supply
is now seeded above every id in use, and the `except` is narrowed to `FRONTEND_ERRORS`,
so a crash can no longer masquerade as a weak proof. (V1′ found this class of bug the
same way and drew the same moral: *a crash is never a verdict.* This one was worse — it
was a crash reported as a *proof attempt*.)

#### The teeth

`prove/11_measure_nonstructural.lark` was written at V2.1 as a time bomb for this rung,
and it has now been detonated on purpose. Its measure asserts `bad(xs) == 1 + bad(xs)`.
Disarm the structural check — nothing else — and V2.2 instantiates that equation at the
`Cons` arm's own term, derives the inconsistency, and *verifies that `absurd` returns a
negative number when it plainly returns `0`.* One false proof, ex falso, measured rather
than argued. The `Nil` arm stays honest, because *its* equation (`bad(Nil) == 0`) is
consistent — the poison reaches exactly the terms it is instantiated at, which is as
good an illustration of "instantiation at terms" as the design could ask for. V2.1's
structural check is *load-bearing for V2.2*, not good manners.

### The four false proofs

Everything above is about a checker that gives up too often. This section is about the
four occasions it did not give up when it should have — the first false proofs the
project has produced, all found by *asking* rather than by waiting, and each now nailed
down by a fixture in `prove/`.

They come in two families. The first two are the checker *believing something it had
not established*. The last two are the checker *speaking about a name that no longer
meant what it thought it meant* — and those are the ones to be frightened of, because
nothing in the program looks wrong.

*1. `x == x` is not valid for a Float.* In the logic it is: equality is an equivalence
relation, congruence closure makes it reflexive, and it must. In IEEE-754 it is *false
when `x` is NaN* — and Lark makes NaN the ordinary way, since `0.0 / 0.0` returns one
(`cek.py`) and so does `float_sqrt` of a negative. So the checker assumed `not (x == x)`
in an else branch, found it contradictory, and proved the branch *vacuously* while the
machine cheerfully ran it. The other half of the same lie needs no NaN: `0.0 == -0.0` is
*true* at run time and they are *different values*, so congruence concludes
`f(0.0) == f(-0.0)` for an `f` that can tell them apart (`1.0 / x` is `+inf` for one and
`-inf` for the other).

Reflexivity fails one way, substitutivity the other — and those two are the whole of
what a sort of `OTHER` hands out. `OTHER` says *you may NAME me but not OPEN me*, and
that is right for a String, a Buf, a List. *It is too much for a Float.* So a Float now
has a sort of its own, `refine.FLOAT`, at which *no term is ever built*: not opaque,
*unspeakable*. The guard sits in `term_opt`, which refuses the term the moment it is
built — so a constructor with a Float field is unnameable too (its argument was), and a
predicate over Floats is a refinement *error* rather than a silent lie.

*2. "I could not translate this" is not "this is true."* The deeper one, found while
fixing the first, and there is not a Float in it. Both `if` sites read

```
    cf = formula_opt(c, env) or Top()
```
and `formula_opt` returns `None` for *"I cannot express this condition."* That `or Top()`
turned it into *true* — so the else branch assumed `Not(Top())`, i.e. *false*, and
from false every obligation in the branch follows. The guard that did it in the fixture
is `x * y > 0`: merely *non-linear*, which is the everyday way out of a linear
fragment, not some exotic corner. Any unreadable condition would serve.

A condition the logic cannot express *constrains nothing*, so neither branch may learn
anything from it — not the positive, and above all not the negation (`refine._branch`).
The cost is proofs. The alternative was a lie.

*3. A UF symbol is a global function, and only that.* The logic names its symbols by
their *source name*, and source names *shadow*. Take `05_buf`'s idiom — the oldest
thing in the suite, a contract written with a function the program itself defines:

```
    fn size(b : Int) : Int = 0
    fn take(b : Int, k : {v : Int | v != size(b)}) : Int = div(100, k - size(b))

    fn bad(b : Int) : Int =
      let size = fn(x : Int) => 1 in            -- the shadow
      if 0 != size(b) then take(b, 0) else 0    -- and `take`'s contract is "proved"
```

The guard and the contract both translate to `App("size", (b,))`, and *they are two
different functions*. Congruence closure identified them, and an obligation about the
global `size` was discharged by a guard about a local lambda. At run time the real
`size(b)` is 0, `k - size(b)` is 0, and `take` divides by it.

`term_opt` now refuses to build `App(f, …)` when `f` is in `env.vsorts` — which holds the
*value variables* (parameters, `let`s, match binders) and *never a global function*. A
locally bound function is *unspeakable*. Nothing sound is lost, and that is an argument
rather than a hope: a local function has no contract to read off and no equations to
instantiate, so all it ever had was congruence — and congruence is what was wrong.

*4. An axiom is about a function, not about a name.* The same capture at longer range,
and worse, because *nobody has to call it for it to fire*. `refine.NONNEG_UF` is V1's
one hand-written belief about a UF symbol: `string_length(t) >= 0`, asserted of every such
term a VC mentions. It is true of the *primitive* — and a program may declare its own:

```
    fn string_length(s : String) : Int = 0 - 4                    -- legal
    fn safe(s : String) : Int = div(100, string_length(s) + 4)    -- "proved". 100 / 0.
```

The declaration overrides the builtin everywhere, the CEK machine included, so the axiom
became a lie about the program's own function. `Refiner` now intersects `NONNEG_UF` with
the names the program *leaves alone* and hands each VC the result — beside `cons`, and
for the same reason: which axioms fire is a property of the obligation. Temporary in the
good sense, and the promise was kept: *V2.3 deleted `NONNEG_UF`* (below). What replaced
it, `PRIMITIVE_AXIOMS`, is still withheld from a name the program rebinds — an axiom about
a *function* never becomes an axiom about a *name* — but a length is no longer among the
things this checker believes on its own say-so.

This is *V1′'s rule, one level up from the solver.* V1′ made every exhausted budget
inside `solver.py` resolve toward *"cannot prove"* — never toward a proof. The same rule
now binds the checker that *builds* the obligations: *where it cannot speak, it must say
nothing — never `true`, never a negation, and never a claim about a name it does not
own.* All four fixes cost the corpus nothing — `prove` 27→35 with the eight new files,
`robust` 45/0/0 with every verdict where it was — which is the tell that the proofs they
removed were never proofs at all. And the whole pass touched *`refine.py` alone*: every
one of these was a bug in what the checker *said*, not in what the solver *decided*.

### An `impl` body is a body (V2.2″)

The hunt above left one hole open on purpose, because it was not a false proof and the
fix belonged in its own pass. `refine.py` matched every declaration except `ImplDecl` —
so *an impl body was never walked*. Five rungs of checker, and the code inside an
`impl` block had never been looked at.

It was sound, and it was sound by luck. A refinement on a trait method's signature was
*dropped* rather than trusted (`_register_trait_decl` hands back an HM scheme, and
`_rtype_of_mono` erases the predicate), so a lying impl could not discharge anybody's
goal. What it could do is the failure mode next door: put `n / 0` inside an impl body,
with no caller reading the trait, and the checker printed *`ok: 2 obligation(s)
proved`* and exited 0. The division was never *seen*. *A weak answer is a result; a
count that omits the obligation is a wrong report*, and a verifier is allowed the first
and never the second.

The fix has two halves, and they are one decision. An `ImplMethod` is now checked exactly
as an `fn` is, against the contract in the *trait* — refinements from the signature, HM
types from the `TFnDecl` `infer.py` already built for that body, parameter names from the
impl. *And because every impl is held to that signature, a caller may finally read it*:
the trait's refinement becomes the method's global contract. Neither half is safe alone.
A contract that callers trust and nobody checks is precisely the false proof the four
above were made of.

Two things fell out of it. The plan said "substitute the impl's type for the trait
variable", and it turns out *nothing needs substituting*: a refinement can only sit on a
base the logic can *name*, and a trait variable is not one, so a signature contributes
predicates and nothing about the type — the types come from HM, which checked them at the
concrete type already. And where the trait is not declared in this file (`Copy`, `Show`)
every part falls back to its HM type: *a trivial contract is still a contract, and the
body is walked all the same.* Nothing is skipped, which is the whole point.

`prove` *35 → 37* (`17_impl_{safe,unsafe}`, the safe file run), and the counts are the
finding. Under the old checker *both* halves of that pair had exactly *one* obligation —
a division out in ordinary code — and both *failed* it, the contract having been thrown
away. Now there are four. *Too weak outside, blind inside: one bug, and the count says
so.* On 07's own corpus every verdict is exactly where it was, because those impl bodies
divide by nothing — the fix adds obligations only where there is something to prove.

## The adversary, and the three it found (V2.2‴)

The four false proofs above were found *by hand* — by asking "is anything else unsound?"
and going looking. `08/tests/adversary.py` is what happened when we stopped looking by
hand: it generates random *programs*, checks them, and then *runs* the ones the checker
proved. *If it says `ok`, the program must not crash.* A crash after a proof is a false
proof, and the program that caused it is printed.

It found three more, and the third is the worst hole this fork has had.

*`18_divisor` — a goal it could not read was never asked.* `100 / (x * y)` is merely
*non-linear*, so `term_opt` said `None`, so the site raised *no obligation at all*;
likewise `100 / h(x)` for a local lambda, whose type V2.2′(c) had rightly made unspeakable.
This is `14_guard`'s rule at the *opposite polarity*, which is precisely why it was easy
to get wrong:

> a *hypothesis* it cannot read must be *DROPPED*.
> a *goal* it cannot read must be *ASKED ANYWAY*, and go unproved.
>
> *Silence about what you may assume is modesty. Silence about what you must prove is a lie.*

The asking condition is now *HM's* (this is an integer division, so it owes a proof), and
the only excuse is positively knowing the division is a Float's. An unnameable divisor gets
a *skolem* carrying its own contract — so `100 / nz(x * y)` still proves, and a divisor
with nothing said about it goes unproved, which is the truth.

*`19_floatlit` — the road into a Float that nobody had to declare.* A Float *literal* had
no sort, so it read as `OTHER`: an ordinary opaque value, and an opaque value may be
*equated*. `nan == nan` was believed, its negation was UNSAT, and the else branch — the
one NaN actually takes — became dead code in the logic. Unspeakability is not a property of
a literal; it is a property of every value a Float can reach, so the sort must *survive
arithmetic* too.

*`20_condition` — the question that was never asked.*

> `formula_opt` and `term_opt` *TRANSLATE*. `synth` *WALKS*.
> Only the walk raises obligations. Translation is pure: it asks for nothing.

Four sites translated a sub-expression *instead of* walking it — an `if`'s condition, a
comparison, a `not`, a unary minus — and every division inside any of them *vanished*.
`if (x / y) < x then …` checked as *`ok: 0 obligation(s) proved`*, exit 0, and divided by
zero. And it was never a corner: *07's own primes sieve* (`fn divides(d, n) = n / d * d ==
n`, a body that *is* a comparison) reported *zero obligations for the entire life of this
fork*. Its verdict has moved in `robust_sweep.py`, and *the move is the finding*.

> *Every sub-expression is walked exactly once*, whether or not it is also translated.
> What the checker declines to *understand*, it must still *look at*.

`synth`'s silent `return ROpaque()` fall-through is closed the same way: an operator it does
not know now *raises* and says what it owes, so `%` (which the CEK already implements, and
which traps on zero — only the *lexer* keeps it out of the language) cannot arrive without
the checker being taught it.

`prove` *37 → 43*. *The cost was nothing:* every `_safe` file still proves, runs, and
prints its answer — closing a hole this size usually spends capability, and here there was
none to spend, because the capability *was* the absence of a question. And the rule the whole
rung leaves behind: *a checker's silence is a verdict, and a report must never let silence
read as approval.* `ok: 0 obligation(s) proved` was in that output the whole time, and it
reads like success.

## The axiom that became a theorem (V2.3)

V1 shipped with one belief it could not justify, and said so in its own comment: it "knows
something it strictly should not have to." That was `NONNEG_UF`, a set literal in the
checker asserting `string_length(t) >= 0`, with a hard-coded `>= 0` buried in the axiom
walk. *It is deleted.* A measure now *declares* what its result satisfies —

```
    measure len(xs : List(Int)) : {v : Int | v >= 0}
```

— and the checker *proves the declaration, by structural induction over the measure's own
arms*. One obligation per constructor, and the solver learns nothing new:

```
    arm 'Nil'    prove  len(Nil) >= 0             from  len(Nil) == 0
    arm 'Cons'   prove  len(Cons($f, rest)) >= 0  from  len(Cons($f, rest)) == 1 + len(rest)
                                                  and   len(rest) >= 0            (the IH)
```

The equation needs no special handling: `len(Cons($f, rest))` is *in the goal*, so V2.2's
walk instantiates the arm's own equation at it and congruence does the rest. And the whole
induction is legitimate for a reason V2.1 already paid for: *an arm may only recurse on a
FIELD*, so the hypothesis is only ever assumed at a strictly smaller value. The structural
check was written to keep the axioms *consistent*; it turns out to be what makes them
*provable*.

*And the one place it could have been worthless.* An induction VC must not be handed, as
an axiom about arbitrary terms, the very refinement it is proving — the `Nil` arm would
discharge itself and a bogus declaration would sail through. `Refiner.run()` withholds it:
the induction VCs get the primitives' axioms only, and the induction *hypothesis* is
supplied by hand at the recursive occurrences. *Assuming the conclusion is not a subtle
bug; it is the entire difference between an induction and a lie.* `prove/21_result_unsafe.lark`
is what it would cost: declare `{v : Int | v > 0}` for a length, and the checker that
believed it proves `100 / size(xs)` — then `main` passes `Nil` and divides by zero.
Disarm `_prove_measure` and the *adversary finds exactly that*, in about a hundred
programs; it is now generated on purpose (`08/tests/adversary.py`, the `m1`/`size` family).

*What is left is one table.* `refine.PRIMITIVE_AXIOMS` is the complete list of what the
checker takes on faith about the primitives — currently one line, `string_length`, written
in the same language a program writes a contract in, and postulated for a stated reason:
*a String has no constructors, so there is nothing to induct over.* The difference between
`len` and `string_length` is now the right difference, and it is legible: one is a theorem,
the other is an axiom, and an axiom you cannot enumerate is an axiom nobody has audited.

*The capability it buys is not decoration.* The equations pin a measure only at the
constructor terms a program *mentions*. A *parameter* mentions none — no `Cons`, no `Nil`,
nothing to instantiate at — so before V2.3 the checker did not know `len(xs) >= 0` for an
opaque `xs`, and `total / (len(xs) + 1)` was unprovable. A fact that must survive an opaque
argument cannot come from a term; it has to come from the declaration. Delete the
declaration from `prove/21_result_safe.lark` and that division goes unproved.

`prove` *43 → 45*. Everything else unmoved: drift 22/3/3/0, conservative 90/0/0, solver
*16/0 and still byte-identical*, robust 45/0/0 with every verdict where it was.

*Two gaps left open, deliberately.* The logic reasons over *ℤ* while the RV32 and C
backends are *32-bit*, so a refinement proved here need not survive `i32` wraparound —
sound against the CEK reference (Python bignums), *not* against a 32-bit target. And
contracts are *partial correctness*: checking a recursive body assumes the declared
result type, so a function that never returns may carry any postcondition at all. Neither
is a false proof against the machine the checker verifies against; both are worth knowing
before anyone says "verified" without a qualifier. (A *measure*, note, is held to a
stricter standard than a contract: termination is *optional* for a `fn` and *mandatory*
for a measure, because a measure's arms are assumed and a non-terminating axiom set proves
everything.)

## The checks

```sh
make -C dev/08 drift          # 08/src == 07/src, except where declared
make -C dev/08 conservative   # 07's corpus behaves identically through 08/
make -C dev/08 solver         # the decision procedure's own self-check
make -C dev/08 prove          # safe programs check; their mutants are caught
make -C dev/08 test           # the four that pin behaviour

make -C dev/08 robust         # the checker over 07's whole corpus: no crash, ever
make -C dev/08 fuzz           # random QF-UFLIA vs brute force: no unsound answer
make -C dev/08 adversary      # random PROGRAMS: proved ⇒ it runs. The witness.
make -C dev/08 torture        # hostile programs: a crash is not a verdict, nor is a hang
make -C dev/08 invariants     # the rules, checked: every node walked, every division asked
make -C dev/08 harden         # test, plus the five that hunt for breakage
```

The first four pin what the checker *says*. The next four ask whether it survives at
all — a different question, and they found things the pinned suites could not: a
solver that hung on a formula naming seven constants, three frontend exceptions
escaping as raw Python tracebacks, and a latent division by zero in two of Lark's own
samples. See `PROVE.md` V1′.

*`torture`* (`tests/torture.py`) is the newest, and it asks the one question none of the
others do. They all ask whether the checker is __right__; this one asks whether it
__answers__. Fourteen hostile-but-legal programs — 3 000 terms in one expression, a
predicate that is a 300-way conjunction, a constructor term 400 deep — each in a
subprocess on a wall clock, and *the only failing grade is no answer at all*. __A
traceback is not a verdict, and neither is a hang.__ It opened at five failures of
fifteen: four raw `RecursionError`s (the checker walks a program on the C stack, and
Python's limit is 1 000 — now it runs on a real stack and calls what is left `TooDeep`, a
*stated limit* rather than a stack trace), and a hang whose cause is the finding worth
keeping. __Every fence in `solver.py` was local, and every caller loops:__ `MAX_SPLITS`
re-arms on each `_lia`, `_propagate` calls `_lia` quadratically, DPLL calls `consistent`
per node — so the total work in one query had no bound at all. *A budget that resets is
not a budget.* Now there is a global purse (`MAX_WORK`), and a fence on the __size__ of a
linear system (`MAX_LINEAR`) and not merely the number of them, because Fourier–Motzkin
is quadratic per elimination and counting calls bounds nothing.

Then, with the stack raised, a crash turned into a hang — and *that* is the lesson.
Translating `1 + 1 + … + 1` re-derived the linearity of the __whole subtree at every
level__ of a walk that already visits every node: 173 million `is_linear` calls on an
800-term sum. The stack overflow had been mercy-killing a cubic algorithm. __A crash can
be the symptom of a cost, and fixing the crash without measuring the cost only moves the
failure somewhere the tests cannot see it.__

And there was a third walk, which nobody writes and the profiler had to point at: `hash`.
A `Term` is a frozen dataclass, so hashing it hashes the tuple of its fields — and a field
of a Term is a Term. __A term is a tree, and its hash is a walk of that tree.__ Once, that
is free. Inside congruence closure, which looks a term up in a dict for every `find`, every
merge, every subterm it registers, an O(n) hash inside an O(n) loop is the quadratic nobody
wrote down *because nobody wrote the loop*: 4.34 million calls to `hash` on a 600-term sum,
about 40 % of the run. Terms are immutable and heavily shared, so a node's hash is now
computed once and kept. __An immutable structure may be walked once; every walk after that
is a bug you have not noticed yet.__ (What is left is quadratic and *inherited*:
`infer.py`'s `_apply_env` rebuilds the type environment at every node, textbook naive HM,
and __07 pays it too__. Bounded, terminating, measured, and left alone — see `PROVE.md` H.
On a 1 600-term file the checker's own share is 0.04 s of 19.9 s.)

Where the checker now gives up on a budget it *says so*: "gave up (budget exhausted)",
not "cannot prove". *The first is a fact about the checker and the second is a fact about
your program, and printing one in the words of the other is how a tool teaches its user to
distrust it.*

*`adversary`* (`tests/adversary.py`) is the one that matters most, and it is the
newest. `fuzz` tests the *solver* — and the solver has never been the problem. Every
false proof this project has had was *one level up*, in the checker that *builds* the
obligations, and every one of the first four was found *by hand*. So: random programs,
checked, and then *run* if the checker proved them. *If it says `ok`, the program does
not crash.* It found three more false proofs in its first afternoon, including one
(`20_condition`) that had been live since V1 and that sat inside 07's own primes sieve.
A human audit looks where a bug would be *interesting*; a random program does not know
which positions are supposed to be interesting. See `PROVE.md` V2.2‴.

Since *V2.3* it also generates *measures*: a `List` ADT, a `measure` with a randomly
chosen (lie-weighted) declared result, a function whose contract equates the two, and a
divisor taken from that result *through a name*. That last clause is a finding in its
own right — the generator first wrote `x / size(xs)`, a bare call, whose postcondition
never becomes a fact, so it could not have exhibited the bug even with the induction
disarmed. *A fuzzer that cannot express the bug does not report its absence; it reports
its own blind spot.* Disarm the fix and watch it go red before you trust it green.

*`invariants`* (`tests/invariants.py`) is the newest, and it is the only one that exists
because of a complaint about *method* rather than a bug. Every finding above was a
__finding__: a hostile program got lucky, or a careful read got lucky, or a profiler got
lucky. Seven times. That works — and its working is what hides the trouble with it. __A
method that finds bugs by being lucky cannot tell you the difference between "there are
none left" and "I stopped looking"__ — which is the *exact* distinction the last two
sections spent their whole budget forcing the *checker* to make about its own budgets. It
would be a poor joke to demand it of the tool and not of the people building it.

So the rules stop being prose. Three properties, checked over all 92 corpus files, every
run — each one a bug we actually shipped, generalised to its shape:

  * __coverage__ — every expression node in a checked body is *visited*, exactly once.
    *Missed* is the shape of the `formula_opt` bug (a node the checker never looked at);
    *revisited* is the shape of the quadratic (a subtree re-walked at every level above
    it). One question — *how many times did you look at this node?* — and the only
    acceptable answer is once.
  * __asking__ — every integer division walked raises exactly one obligation. Coverage
    cannot see this one: the node *was* visited, and the checker declined to ask anyway.
  * __work__ — the checker's cost is linear in program size, by __counting, not timing__.
    Deterministic counters make it a regression test rather than a wall-clock coin flip.
    Measured: 2.00× per doubling. (The *solver* is held to a different bar on purpose —
    Omega on an n-term system is honestly superlinear, and is fenced, not fixed.)

__It found an eighth false proof within minutes — the first one found on purpose.__ 58
nodes across 7 corpus files came back __never walked__, all of them the same thing: the
body of a lambda. `check` walks a lambda's body, because it has an expected function type
to push into it. `synth` returned `ROpaque()` *without looking inside*, and an unannotated
`let h = fn (a) => …` goes through `synth`. So:

```
let h = fn (a : Int) => 100 / a in h(0)
    ok: 0 obligation(s) proved          exit 0
    …and then, at run time:             ZeroDivisionError
```

One of the 58 was a real division inside `07/tests/25_torture.lark` —
`filter(fn(x) => (x - (x / 2) * 2) == 0, xs)` — never once examined in the fork's whole
life, in a file called *torture*. __The rule generalises, and it is the one to carry
forward: "every sub-expression is walked exactly once" is not a fact about expressions. It
is a fact about every place code can hide, and a lambda is one of them.__ See
`prove/22_lambda_*` and `PROVE.md` I.

And the same lesson as the fuzzer, twice now: `adversary.py`'s docstring had said "a local
lambda's result" since V2.2‴ — and the generator *could not emit a lambda at all*. It knew
the words and not the grammar. __A generator only ever finds bugs in the language it can
speak; its grammar is a claim about which programs exist, and an unexamined grammar is an
unexamined claim.__

*`drift`* (`tests/drift.py`) requires every file in `08/src` to be byte-identical
to its `07/src` twin unless it is named in the `EXTENDED` (changed) or `ADDED`
(new) table, each with a reason. Those two tables are the honest statement of how
large the refinement extension has grown; a module that drifts without appearing in
them is a bug, not a feature.

*`conservative`* (`tests/conservative_difftest.py`) is the claim that has to stay
true from the first refinement to the last:

> a program that carries no refinement must type-check and evaluate through `08/`
> exactly as it does through `07/` — same verdict, same bytes, same exit.

It pushes all 45 files of `07`'s corpus (`07/tests`, `07/samples`) through both
trees' `infer.py` *and* `cek.py` and demands byte-identical stdout/stderr/exit.
`cek` is in there because refinements erase at runtime: a refinement that changes
what a program *prints* is not a refinement.

Three tokens are canonicalised, and only three: the interpreter's own path (`07/src`
vs `08/src`); the oracle's `_anon_{id(node)}` wildcard-parameter name, which bakes a
CPython object address into the typed AST and so differs between any two runs —
including two runs of `07/src` itself; and the *line numbers inside a traceback*,
which shift for every fixture the moment a line is added to `infer.py` without
anything about Lark's answer changing. Everything else in a traceback — the frames,
the source lines, the exception and its message — is still compared byte for byte.

*`prove`* (`tests/prove_difftest.py`) runs the suite in [`../prove/`](../prove/):
safe programs paired with mutants carrying one real bug each, and the expected
verdict pinned per file. Both halves matter, for opposite reasons — a safe program
that does not check means the checker is too weak to use; an unsafe program that
checks means it is worse than useless.

## Baselines

| target         | result                                            |
|----------------|---------------------------------------------------|
| `drift`        | *22 identical / 3 extended / 3 added / 0 missing* |
| `conservative` | *90 ok / 0 fail / 0 skip* (45 files × `infer` + `cek`) |
| `solver`       | *16 ok / 0 fail* (incl. 2 grey-region cases only splintering can decide) |
| `prove`        | *45 ok / 0 fail* (16 safe/unsafe pairs + 3 affine + erasure + 1 measure, 12 checked *and run* + 7 measure negatives) |
| `robust`       | *45 ok / 0 fail / 0 crash* (07's whole corpus, verdicts pinned) |
| `fuzz`         | *3000 cases / 0 unsound* (2556 agreed, 135 SAT with no model in the box, 309 too big) |
| `adversary`    | *clean* — of 150 random programs, every one the checker proved then ran without crashing, and erasure held |

`conservative` at 90/0/0 is the number that matters most: it is unchanged from the
Step-0 baseline taken *before* the first refinement existed, which is what makes it
readable. Refinements are a conservative extension of Lark, demonstrated rather
than asserted.

`solver`'s two grey-region rows are there on purpose. A system in the gap between
the real shadow and the dark shadow can only be settled by enumerating splinters,
so without them the completeness path of the Omega test would be dead code that
nothing executes and nobody notices is broken.

`fuzz`'s 135 unconfirmed SATs are *not* failures, and a harness that treated them as
failures would be worse than no harness. The brute-force reference searches a box —
`[-3, 3]` — and Omega decides all of ℤ; a formula whose only models are large is exactly
the case the solver is *for*. The run fails on one thing only: the solver claiming a
contradiction that a model refutes, or a proof that a counterexample refutes. That is the
asymmetry the whole checker rests on. Failing to find a contradiction rejects a good
program, which is annoying; inventing one accepts a bad program, which is fatal.

