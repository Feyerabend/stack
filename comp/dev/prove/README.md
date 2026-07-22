
## `prove/` — the verification suite

The programs the refinement checker is judged by ([`../../PROVE.md`](../../PROVE.md) V1.4).
The checker lives next door in [`../08/`](../08/); run the suite through it from the
repository root:

```sh
make -C dev/08 prove
```

The suite is built out of __pairs__: a safe program, and a mutant of it carrying one
real bug. Both halves matter, and for opposite reasons.

> a safe program that does not check — the checker is too weak to be used
> an unsafe program that checks — the checker is worse than useless

The expected verdict of every file is pinned in `08/tests/prove_difftest.py`, as a
count: how many obligations were discharged and how many were not. A drifting count
is a finding either way — an obligation that quietly *disappears* is as suspicious
as one that starts failing.

| pair | what it proves | how the mutant breaks it |
|------|----------------|--------------------------|
| `01_bounds` | `string_index` is in range — the primitive the self-hosted lexer calls on every character | no guard; a guard that is true of every string; an index one past the end |
| `02_divzero` | no division by zero. Every `/` raises the obligation, contract or no contract | unconstrained divisor; `d >= 0` mistaken for a guard; `k - 1` where `k > 0` |
| `03_nonneg` | a postcondition `{v \| v >= 0}`, earned by branching or by calling something that already has it | the negation dropped; subtraction assumed to preserve it; the branches swapped |
| `04_slice` | `0 <= a <= b <= len(s)`. The contract on `b` mentions `a`, so the call site checks it against the `a` actually passed — a dependent function type | slicing an empty string; `a <= b` never established; one past the end |
| `05_buf` | a contract written with a function the *program itself* defines (`size`), uninterpreted to the solver | no guard; only half of it; the count used as an index |
| `09_product` | __V2.0__ — a pair whose components carry facts, destructured by the caller and still true on the other side of the comma | a right edge one past the end, declared honestly in the helper's own contract: no function is wrong, the *interface* between two of them is |
| `12_measure` | __V2.2__ — the equations. `two` __builds__ a list and proves its length; `tail_of_two` __destructs__ one, and its `Nil` arm is proved *vacuously* because a two-element list is not `Nil`; `main` carries the fact across a function boundary | one lie per hook: a 1-list called 2, the whole list returned as the tail, and `head(Nil)` — the oldest bug in functional programming, and the rung where Lark starts to see it |
| `13_float` | __soundness.__ `x == x` is valid in the logic and __false at run time for NaN__ — so the else branch was proved vacuously, and the program divided by zero | the mutant *is* the bug: it was reported __proved__ until a Float was made unspeakable. The safe file is the control — Floats still flow, they simply say nothing, and the Int obligation beside them proves as before |
| `14_guard` | __soundness, and not a Float in sight.__ A condition the logic cannot *read* must constrain __neither__ branch | the guard is `x * y > 0` — merely __non-linear__. The checker read it as `true`, negated it to `false`, and proved a division by zero out of the contradiction |
| `15_shadow` | __soundness — a NAME.__ `05_buf`'s idiom (a contract written with the program's own `size`) discharged by a guard at the call site that calls the same `size` | the mutant adds one `let size = fn(x) => 1`. Both are the symbol `size` in the logic, congruence identified them, and a guard about the local one proved an obligation about the global one |
| `16_axiom` | __soundness — an AXIOM.__ The one thing V1 believes about a UF symbol, `string_length(t) >= 0`, and the safe file leans on it entirely | the mutant adds one *declaration*: `fn string_length(s : String) : Int = 0 - 4`. The verified function is not touched. The axiom was written about a name, and the name changed hands |
| `17_impl` | __an impl body is a body.__ `refine.py` matched every declaration but `ImplDecl`, so for five rungs an impl body was __never walked__ — `n / 0` inside one raised no obligation and the checker said `ok`, exit 0. A method is now checked as an `fn` against the trait's signature, which is also what entitles a *caller* to read that signature | the count is the mutant's confession: __old, both files had ONE obligation__ — `share`'s division, out in ordinary code — and both __failed__ it, the contract having been dropped. Now four. The mutant lies once per hook: an arm returning `0` where the trait promised `{v \| v > 0}`, and a division inside a body nothing else reads |
| `18_divisor` | __soundness — a GOAL it could not read.__ A divisor the logic cannot *name* — `x * y` (non-linear), or `h(x)` for a local lambda (unspeakable since V2.2′) — raised __no obligation at all__ | the asking condition is now HM's, not the checker's understanding: this is an integer division, so it owes a proof. An unnameable divisor gets a __skolem__ that inherits its *contract*, so `nz(x * y)` still proves; a divisor with nothing said about it is `$k /= 0`, unprovable, which is the truth |
| `19_floatlit` | __soundness — the unpaved road to a Float.__ A Float *literal* had no sort, so it was `OTHER` — an ordinary opaque value, and an opaque value may be __equated__. `nan == nan` was believed, its negation was UNSAT, and the else branch NaN actually takes became dead code in the logic | one missing sort, two bugs pointing opposite ways: an obligation __invented__ (`0.0 / 0.0` looked like an *integer* division) and a falsehood __believed__. The sort must also survive arithmetic, or the fix is undone one line later |
| `20_condition` | __soundness — the question that was never asked.__ `formula_opt`/`term_opt` __translate__; only `synth` __walks__, and only the walk raises obligations. Four sites translated a sub-expression *instead of* walking it: an `if`'s condition, a comparison, a `not`, a unary minus. Every division inside any of them __vanished__ | the mutant checked as __`ok: 0 obligation(s) proved`__, exit 0 — *zero* — and then divided by zero. And it was never a corner: 07's own primes sieve (`fn divides(d, n) = n / d * d == n`, a body that __is__ a comparison) reported zero obligations for the entire life of this fork |
| `21_result` | __V2.3 — the axiom that became a theorem.__ A measure declares its own result refinement, `measure len(xs : List(Int)) : {v : Int \| v >= 0}`, and the checker __proves it by structural induction__: one VC per constructor arm, the declared refinement assumed at each recursive occurrence as the induction hypothesis. Then, and only then, is it asserted at the terms a program mentions — so a division by `len(xs) + 1` proves for an __opaque__ `xs`, with nothing believed on faith | the mutant moves one character: `{v \| v > 0}`. A length is not positive, and the induction fails at exactly one place — the `Nil` arm, whose obligation `len(Nil) > 0` sits next to its own equation `len(Nil) == 0`. The `Cons` arm still proves, from the IH. And it is a detonation, not a style complaint: admit the declaration and `total / len(xs)` is discharged, `ok`, exit 0 — then `main` passes `Nil` and the machine divides 100 by 0 |

Three further files carry the __affine × refinement__ finding — `06_affine_mention`
(the mention is free), `06_affine_control` (the binding really is affine),
`07_affine_guard` (the *guard* is not free), and `07_affine_borrow` (the idiom that
fixes the affine error).

`07_affine_borrow` is the thermometer, and it has moved once per rung, which is what a
thermometer is for. __V1: 0 of 3__ — no refined tuple components. __V2.0: 1 of 3__ — the
*consumer* (`take(b2, 0)`), because refined products now carry `n == size(b)` and
`size(b2) == size(b)` through the tuple pattern and the guard finishes the job; and no
further, because the *producer*'s body needs `size(Buf(n)) == n`, which products cannot
create. __Refined products let a fact travel; only a measure can create one.__ __V2.2: 3
of 3__ — and the diff is one word. `size` stopped being an `fn` and became the `measure`
it always was, and the two goals that were the two halves of one missing equation get
the two halves the equation supplies: `Buf(n)` in the body says what it *builds*,
`| Buf(n) =>` says what it *took apart*.

Keep `05_buf` next to it while reading. Same name, same body, same `Buf` — and `size` is
still an ordinary `fn` there, still uninterpreted, still proving what it proved at V1.
The contrast between those two files *is* the measure feature: not what the function
computes, but whether the logic is allowed to know.

`08_erasure.lark` is the odd one out: it is checked *and then run*. Every obligation
in it is discharged, and then it executes on the ordinary CEK machine and prints
what it promises — because the predicate is gone before the runtime ever sees a
type. Nothing is checked twice, and nothing is checked at run time.

### The measures (V2.1 declared them, V2.2 believed them)

`10_measure_len.lark` declares one — `measure len(xs : List(Int)) : Int` — and it took
two rungs to pay off, in two steps worth keeping apart.

__V2.1 gave the name a sort.__ Under V1 this file was not an unproved program, it was a
refinement __error__: `len` had no declaration, so it had no sort, so `len(v) > 0` was
not a predicate at all. Declaring the measure is what lets its name into a contract in
the first place — and the file's one obligation was then honestly *unproved*, which is
a different thing from broken.

__V2.2 showed the arms to the solver, and it goes green with no change to the file.__
The obligation is `len(Cons(3, Cons(4, Nil))) > 0`, and it is discharged by
instantiating `len` at the three constructor terms the program literally wrote —
`len(Nil) == 0`, so the inner `Cons` is 1, so the outer is 2, so it is positive. No
quantifier, no trigger, no schema: just the terms that are there. Like `08_erasure` and
`12_measure_safe`, it is also __run__ — a measure lives in `Program.measures` and never
in `Program.decls`, so the CEK machine has never heard the name. Erasure by
construction.

The seven `11_measure_*` files are the negatives, and they are not hygiene.
__A measure's arms become axioms__, so each of these is a soundness condition:

| file | the condition |
|------|---------------|
| `11_measure_nonstructural` | __the one with teeth, and V2.2 armed it.__ `bad(xs)` where only `bad(rest)` is allowed asserts `bad(xs) == 1 + bad(xs)` — an *inconsistent* axiom, and from an inconsistency every goal follows. Disarm the structural check and nothing else, and the checker instantiates that equation at the `Cons` arm's own term and __verifies that `absurd` returns a negative number when it plainly returns `0`.__ One false proof, ex falso, *measured* rather than argued. The `Nil` arm stays honest — its equation `bad(Nil) == 0` is consistent — so the poison reaches exactly the terms it is instantiated at, which is as good an illustration of "instantiation at terms" as the design could ask for. |
| `11_measure_partial` | a missing arm is a term the logic would have to guess a value for. A measure must be __total__. |
| `11_measure_overlap` | two arms for one constructor are two equations that can disagree. "First match wins" is an *evaluation* rule, and there is no evaluation here. |
| `11_measure_wildcard` | `\| _ =>` names no constructor, so it indexes no equation; admitting it would mean giving the arms an __order__, and ordered axioms are not axioms. |
| `11_measure_fragment` | an arm body outside linear arithmetic. Translated __strictly__, like any predicate the programmer wrote: silently weakening it would be a checker claiming to have looked. |
| `11_measure_sort` | a measure into a sort the logic does not have (`Float`). It exists to hand the solver something it can *compute* with; there are two such sorts. |
| `11_measure_clash` | a measure sharing a name with a function is __one symbol with two definitions__ — the equations would be asserted about `len`, and every predicate saying `len` would mean the other one. |

Each must fail as __malformed__ (an *error*), never as *unproved*: a bug in the source
is not a weak proof, and V1's distinction between the two is the reason a reader can
trust the counts above. And after V2.2 the first row is no longer a rule kept out of
caution — the structural check is __load-bearing__, and the file is where you can watch
what it holds up.

### The four false proofs

Everything else in this directory is a claim about a checker that is too *weak*.
`13_float`, `14_guard`, `15_shadow` and `16_axiom` are four occasions it was too __strong__.
They are the ones found __by hand__; `18`, `19` and `20` are the three the *adversary*
found afterwards, and are described in the section below this one. Every one was reported as
`ok: N obligation(s) proved`, and every one then divided by zero when run.

They are two families of two. __The checker believed something it had not established:__

- `13_float` — it believed `x == x`. The logic must (equality is an equivalence
  relation), IEEE-754 must not (NaN), and Lark reaches NaN the ordinary way. A Float is
  now *unspeakable*: it has a sort at which no term is ever built. Not "opaque" — opaque
  means __named but not opened__, which grants equality and congruence, and equality is
  the very thing a Float may not have.
- `14_guard` — it believed a condition it could not read. `formula_opt` says `None` for
  "cannot express this", and both `if` sites turned that `None` into `Top()`, so the else
  branch assumed __false__ and proved anything at all. The condition was `x * y > 0`:
  non-linear, which is the ordinary way out of the fragment, not an exotic one.

__And the checker spoke about a name that no longer meant what it thought.__ These are
the frightening pair, because nothing in the program looks wrong:

- `15_shadow` — a symbol is named by its __source name__, and source names shadow. A
  `let size = …` beside the global `size` a contract was written against gives the logic
  __one symbol for two functions__, and congruence closure identifies them. A guard about
  the local one then discharges an obligation about the global one. A locally bound
  function is now unspeakable too: a UF symbol is a *global function*, and only that.
- `16_axiom` — the same capture, made about the one __axiom__ in the checker, and worse,
  because nobody has to *call* anything for an axiom to fire. `string_length(t) >= 0` is
  true of the primitive and false of the `string_length` a program is free to declare.
  The axiom is now kept only for names the program leaves alone — and __V2.3 made the real
  repair__: `NONNEG_UF` is gone, a measure *proves* its result refinement by induction, and
  what remains taken on faith is one line, `PRIMITIVE_AXIOMS`, holding one entry, for the
  one function whose body this checker cannot see.

__The rule all four fixes obey is V1′'s, moved one level up.__ V1′ made every exhausted
budget *inside the solver* resolve toward "cannot prove", never toward a proof. The same
now binds the checker that builds the obligations: __where it cannot speak, it says
nothing — never `true`, never a negation, and never a claim about a name it does not
own.__ Each `_safe` file is the control, and it is the reason to believe the fixes were
free: same guard, same obligation, still proved, still runs, still prints its answer.
`16_axiom_safe` is the sharpest of them — it is the *unsafe* file minus one declaration,
and it still proves, because the axiom still holds of the function it was written about.

### The three the adversary found

The four above were found by hand, by going looking for them. `18_divisor`, `19_floatlit`
and `20_condition` were found by __`08/tests/adversary.py`__ — which generates random
programs, checks them, and then *runs* the ones the checker proved. It found the first two
within a few hundred cases, and the third, which is the worst hole this fork has had, on a
seed that took two minutes.

That is the honest summary of the hand-audit: __I audited this checker twice and it was
still proving programs that divide by zero.__ Not because the audits were careless, but
because an audit looks where a bug would be *interesting*, and a random program does not
know which positions are supposed to be interesting.

They are one lesson at three depths.

- `18_divisor` — __the same rule as `14_guard`, at the opposite polarity, which is what
  made it so easy to get wrong.__ V2.2′ taught the checker to *drop* a hypothesis it
  cannot read. It read that as licence to drop a __goal__ it cannot read:

      a HYPOTHESIS it cannot read must be DROPPED.
      a GOAL it cannot read must be ASKED ANYWAY, and go unproved.

  Silence about what you may __assume__ is modesty. Silence about what you must __prove__
  is a lie. The condition for asking is no longer "do I understand this divisor" — it is
  HM's, which has already ruled the division integral.

- `19_floatlit` — the Float fix paved the roads it could see (a declared parameter, a
  declared return) and missed the one nobody has to declare: a __literal__. Unspeakability
  is not a property of a *literal*; it is a property of every value a Float can reach, so
  the sort has to survive arithmetic too.

- `20_condition` — and then the floor gave way. A division in a __Bool__ position was never
  visited at all, because the checker *translated* those positions instead of *walking*
  them, and a translation asks for nothing. Nothing in a Bool position looks partial, which
  is why no human wrote this test.

      EVERY SUB-EXPRESSION IS WALKED EXACTLY ONCE, whether or not it is also translated.
      What the checker declines to UNDERSTAND, it must still LOOK AT.

__And note what these three cost the checker: nothing.__ Each `_safe` file proves, runs, and
prints its answer. Closing a hole this large usually means giving up capability; here the
capability was never real — it was the absence of a question.

The generalisation, and it is now the fork's first rule: __a checker's silence is a
verdict, and the report must never let silence read as approval.__ `ok: 0 obligation(s)
proved` was in `20_condition_unsafe`'s output the whole time, and it reads like success.
That is why `synth` now *raises* on an operator it does not know (`%`, when someone adds
it), rather than returning an opaque value and saying `ok`: the language must not be able
to grow behind the checker's back.

### What the checker can and cannot do

It __can__ carry an opaque `string_length(s)` out of a guard and into an index and
see that they agree; that is congruence closure, and it is enough for bounds safety
without knowing what a length *is*.

Since __V2.0__ it can also carry a fact __through a product__: a function may return a
pair whose components are refined, and destructuring the pair no longer throws those
facts away. A component's predicate may mention anything in scope outside the tuple —
the argument it was computed from, typically — but not a sibling component, which has
no name to be mentioned by. Nothing in Lark has wanted one.

Since __V2.2__ it can also __compute on the shape of data__ — but only where the program
already committed to a shape. A measure's arms are equations, and an equation is
instantiated at each constructor term an obligation *mentions*: never as a schema, never
under a quantifier, because `forall xs. len(Cons(x, xs)) == 1 + len(xs)` would leave
QF-UFLIA and take the decision procedure with it. So there are two ways in, and they are
the two things a program does with a constructor — it __builds__ one (`Cons(a, Nil)`
synthesises `{v | v == Cons(a, Nil)}`) or it __takes one apart__ (`| Cons(x, r) =>`
assumes `xs == Cons(x, r)`). Note the second says the humbler thing: *what the scrutinee
is*. The equation follows on its own, because the term is now in the hypotheses and the
walk finds it there.

The negative half of a constructor pattern is left on the table, deliberately: "it was
not a `Cons` at all" needs constructor __disjointness__, an axiom the logic does not
have and nothing yet needs. The same shape as V1's finding one level up — *the mention
is free; the guard is not.*

Since __V2.3__ it can say one thing about a list it has *not* seen built. A claim about an
arbitrary list is a __universal__ claim, and the only way to earn one is __induction__ — so
a measure may now declare its own result refinement, and the checker proves it: one VC per
constructor arm, with the refinement assumed at each recursive occurrence as the induction
hypothesis, and — this is the whole of it — __withheld from the arms' own obligations__, or
the `Nil` arm would discharge itself with the very claim under proof. What the induction
establishes is then asserted at applications the way the arms' equations are, which is why
`total / (len(xs) + 1)` proves for an `xs` that was never taken apart.

So `NONNEG_UF` is gone. The one thing the logic still believes without proof is
`PRIMITIVE_AXIOMS` — a single entry, `string_length(s) >= 0`, for the one function whose
body the checker cannot see. It stays an axiom, but it is now a __declared, named__ one, in
one place, and still withheld from any name the program rebinds (that is `16_axiom`).

The next wall is __V2.4__: a measure that returns a `Bool`, or is parametrised — `sorted`,
`bst`. The induction generalises; what does not, yet, is a hypothesis it cannot name. A
call's postcondition still reaches the logic only *through* a name (`let n = size(xs) in …
/ n` proves; `… / size(xs)` does not), and the same is true of a measure with extra
parameters, whose equations do not fire until the terms they speak of exist.
