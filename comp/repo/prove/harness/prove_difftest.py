"""
The verification suite — the refinement work.

Every file in fixtures/ is a claim, and this harness is where the claim is
written down. The suite is built out of PAIRS: a safe program, and a mutant of it
carrying one real bug. Both halves matter, and for opposite reasons.

    a safe program that does not check   — the checker is too weak to be used
    an unsafe program that checks        — the checker is worse than useless

A verifier is only as good as the programs it *rejects*, so the expected verdict
of every file is pinned below, per file, as a count: how many obligations were
discharged, and how many were not. A drifting count is a finding either way — an
obligation that quietly disappears is as suspicious as one that starts failing.

The last file is different: 08_erasure.lark is CHECKED and then RUN, and its
output is compared against what the program is supposed to print. That is the
whole erasure claim in one row — refinements are gone by run time, so a proved
program is an ordinary Lark program.

    python3 harness/prove_difftest.py       # or: make prove

"""

from __future__ import annotations
import os, pathlib, subprocess, sys

ROOT  = pathlib.Path(__file__).resolve().parent.parent    # .../prove
SRC   = ROOT / "oracle"
SUITE = ROOT / "fixtures"

TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))

sys.path.insert(0, str(SRC))

import refine                                             # noqa: E402
import parser as _parser                                  # noqa: E402
import infer as _infer                                    # noqa: E402


# -- The expected verdicts ------------------------------------------------------
#
#   ("proved",   n)          all n obligations discharged; nothing left over
#   ("unproved", k, n)       k of n obligations NOT discharged — the mutant's bug
#   ("rejected", text)       the program never reaches the solver: the affine or
#                            HM checker throws it out first, and `text` is why
#
# The unproved counts are not decoration. `04_slice_unsafe` has 6 obligations and
# 5 failures, not 6: one argument of the `overrun` mutant is fine, and it would be
# dishonest to pretend the checker rejects the whole call when it rejects the part
# that is actually wrong.

EXPECT: dict[str, tuple] = {
    "01_bounds_safe.lark":    ("proved", 4),
    "01_bounds_unsafe.lark":  ("unproved", 3, 4),

    "02_divzero_safe.lark":   ("proved", 4),
    "02_divzero_unsafe.lark": ("unproved", 3, 4),

    "03_nonneg_safe.lark":    ("proved", 6),
    "03_nonneg_unsafe.lark":  ("unproved", 3, 5),

    "04_slice_safe.lark":     ("proved", 8),
    "04_slice_unsafe.lark":   ("unproved", 5, 6),

    "05_buf_safe.lark":       ("proved", 2),
    "05_buf_unsafe.lark":     ("unproved", 3, 3),

    # The affine × refinement finding, in three files.  The mention is free, the
    # control shows the binding really is affine, and the guard is rejected — not
    # by the solver, by the affine checker, which is the point.
    "06_affine_mention.lark": ("proved", 0),
    "06_affine_control.lark": ("rejected", "affine variable 'b' used more than once"),
    "07_affine_guard.lark":   ("rejected", "affine variable 'b' used more than once"),

    # The borrow idiom — the row that earns all three of its proofs only once the
    # checker can see through the tuple pattern AND read `size` as a fact.  Refined
    # tuple components carry the facts to the CONSUMER (`take(b2, 0)`); the PRODUCER's
    # body needs `size(Buf(n)) == n`, which a plain function cannot supply.  `size` stopped being an `fn` and became
    # the MEASURE it always was, and the two goals that were the two halves of one
    # missing equation are the two halves the equation supplies — `Buf(n)` in the
    # body says what it builds, `| Buf(n) =>` says what it took apart.
    "07_affine_borrow.lark":  ("proved", 3),

    "08_erasure.lark":        ("proved", 6),

    # a later version on its own, with no measure needed: a pair whose components carry facts
    # about a builtin that has a real precondition.  The mutant's right edge is one
    # past the end and says so honestly in its own contract — no function is wrong,
    # the interface between two of them is.
    "09_product_safe.lark":   ("proved", 4),
    "09_product_unsafe.lark": ("unproved", 1, 4),

    # One stage declares the measure; another shows its equations to the solver.  The one
    # obligation is `len(Cons(3, Cons(4, Nil))) > 0`, and it is now PROVED — by
    # instantiating `len` at the three constructor terms the program literally wrote
    # and letting arithmetic chain them: len(Nil) == 0, so the inner Cons is 1, so the
    # outer is 2, so it is positive.  No quantifier, no trigger, no schema.
    # And it still RUNS: measures never enter Program.decls, so erasure is by
    # construction, and `len` is a name the CEK machine has never heard of.
    "10_measure_len.lark":    ("proved", 1),

    # a later version — the equations in the logic, and the pair that actually exercises the two
    # hooks.  Four obligations: `two` BUILDS a list and must prove its length, and it
    # is the *terms* that carry it (len(Nil) == 0, so the Cons above it is 1, so the
    # one above that is 2); `tail_of_two` DESTRUCTS one, and its Nil arm is proved
    # VACUOUSLY, because a two-element list is not Nil and the checker can finally
    # tell; `main` gets its fact across a function boundary, from `two`'s contract.
    #
    # The mutant matters more than the safe file.  It lies once per hook — builds a
    # 1-list and calls it 2, returns the whole list as the tail, takes the head of
    # Nil — and all three are caught.  Under the first version the last of those was not a failed
    # proof, it was an impossible one: `len` was uninterpreted, so the empty list
    # could have had any length at all.
    "12_measure_safe.lark":   ("proved", 4),
    "12_measure_unsafe.lark": ("unproved", 3, 4),

    # THE FOUR SOUNDNESS FIXTURES, and they are here because the checker FAILED them.
    # Every mutant below was once reported as `ok: N obligation(s) proved`, and every
    # one of them then divided by zero when run.  These are the FOUR THAT WERE FOUND BY
    # HAND; `18`, `19` and `20` below are the three the adversary found afterwards, and
    # the honest reading of that is at the head of those rows.  Seven in all, and the
    # project has had, and each row below is the epitaph of one.
    #
    #   13_float — `x == x`.  Valid in the logic (congruence makes equality reflexive,
    #   as it must), FALSE at run time when x is NaN — which `0.0 / 0.0` and
    #   `float_sqrt(-1.0)` both produce.  A Float now has a sort of its own at which no
    #   term is ever built: not opaque, UNSPEAKABLE.  The safe file is the control —
    #   Floats still flow, they simply say nothing, and the Int obligation beside them
    #   is proved exactly as before.
    #
    #   14_guard — the general form, and no Float in it.  `formula_opt` returns None for
    #   "cannot express this", and both `if` sites turned that into `Top()`, so the else
    #   branch assumed `Not(Top())` = FALSE and proved anything.  The guard that did it
    #   is `x * y > 0`: merely NON-LINEAR, the everyday way out of the fragment.  A
    #   condition the logic cannot read now constrains NEITHER branch.
    #
    #   15_shadow — the same mistake made about a NAME.  UF symbols are named by their
    #   source name, and source names shadow: a `let size = ...` beside the global
    #   `size` a contract was written against gave the logic one symbol for two
    #   functions, and congruence identified them.  A guard about the local one then
    #   discharged an obligation about the global one.  A UF symbol is now a global
    #   function and only that; a locally bound function is unspeakable.
    #
    #   16_axiom — the same capture, at longer range and with an AXIOM, which is worse
    #   because nobody has to call it for it to fire.  the first version's one fact about a UF symbol
    #   is `string_length(t) >= 0` — true of the PRIMITIVE, and a program may declare a
    #   `string_length` of its own that returns -4.  NONNEG_UF is now kept only for the
    #   names a program leaves alone.  The safe file is the same code with the
    #   declaration removed, and it still proves, because the axiom still holds of the
    #   function it was written about.
    #
    # Every safe file is RUN, because the fix must not cost a program anything it was
    # entitled to: same guard, same obligation, same answer.
    "13_float_safe.lark":     ("proved", 2),
    "13_float_unsafe.lark":   ("unproved", 1, 2),

    "14_guard_safe.lark":     ("proved", 2),
    "14_guard_unsafe.lark":   ("unproved", 1, 2),

    "15_shadow_safe.lark":    ("proved", 3),
    "15_shadow_unsafe.lark":  ("unproved", 1, 3),

    "16_axiom_safe.lark":     ("proved", 2),
    "16_axiom_unsafe.lark":   ("unproved", 1, 2),

    # 17_impl — the hole the soundness hunt found and did not close: `refine.py`
    # imported `ImplDecl` and never matched it, so an impl body was NEVER WALKED.  Not
    # a false proof (a refined trait method's contract was dropped rather than trusted,
    # which is sound by luck) but the failure mode next door: SILENT UNDER-VERIFICATION.
    # `n / 0` inside an impl body raised no obligation and the checker said `ok`, exit 0.
    #
    # The counts are the whole row.  Under the old checker BOTH files had exactly ONE
    # obligation — `share`'s division, outside the impl — and both FAILED it, because
    # the contract that discharges it had been thrown away.  Too weak outside, blind
    # inside; one bug.  An impl method is now checked as an `fn` against the signature
    # in the trait, which is also what entitles a caller to READ that signature: a
    # contract the callers trust and nobody checks is the false proof a later version was about.
    #
    # The mutant lies once per hook — an arm that returns 0 where the trait promised
    # `v > 0`, and a division inside a body that nothing else looks at — and `share`
    # still proves its division, which is the point: the caller is honest because the
    # impl is now held to what the caller believes.
    "17_impl_safe.lark":      ("proved", 4),
    "17_impl_unsafe.lark":    ("unproved", 2, 4),

    # 18 and 19 are the adversary's, and they are the first rows in this table that no
    # human wrote the mutant for.  `harness/adversary.py` generates programs, checks
    # them, and RUNS the ones the checker proved; both of these came back from it as a
    # proof followed by a ZeroDivisionError, within a few hundred cases.  Measured at
    # 5da6252, the two mutants below printed `ok: 2 obligation(s) proved` and `ok: 1
    # obligation(s) proved`, exit 0, and then divided by zero.
    #
    # 18 is one rule at the wrong polarity.  a later version taught the checker to DROP a
    # hypothesis it cannot read; it read that as permission to drop a GOAL it cannot
    # read.  A non-linear divisor (`x * y`) and a divisor from a local lambda (`h(x)`)
    # are both unnameable, and the division site, not understanding them, ASKED NOTHING.
    #
    #   a hypothesis it cannot read must be DROPPED.
    #   a goal it cannot read must be ASKED ANYWAY, and go unproved.
    #
    # Silence about what you may assume is modesty.  Silence about what you must prove is
    # a lie.  The condition for asking is now HM's — this is an integer division, so
    # there is an obligation — and the only excuse is knowing the division is a Float's.
    # The safe file is what survives: a skolem inherits the CONTRACT of what it stands
    # for (`nz(x * y)` proves), and a name can carry a guard (`let v = x * y` proves).
    #
    # 19 is the same missing sort, twice, in opposite directions.  A Float LITERAL had no
    # sort, so it was OTHER — an ordinary opaque value, and an ordinary opaque value can
    # be EQUATED.  So `nan == nan` was believed, its negation was UNSAT, the else branch
    # was dead code in the logic, and dead code proves everything — including `x /= 0`
    # for x = 0, on the branch NaN actually takes.  And with the sort lost through
    # arithmetic, `0.0 / 0.0` looked like an INTEGER division and raised an obligation
    # nobody owed.  One hole: an invented obligation and a believed falsehood.
    "18_divisor_safe.lark":    ("proved", 4),
    "18_divisor_unsafe.lark":  ("unproved", 2, 4),

    "19_floatlit_safe.lark":   ("proved", 1),
    "19_floatlit_unsafe.lark": ("unproved", 1, 1),

    # 20 is the deepest hole this fork has had, and the count is the whole story: the
    # mutant checked as `ok: 0 obligation(s) proved`, exit 0 — and then divided by zero.
    # ZERO.  The checker did not fail to prove the divisions; it never SAW them.
    #
    # `formula_opt`/`term_opt` TRANSLATE.  `synth` WALKS.  Only the walk raises
    # obligations, and four sites translated a sub-expression INSTEAD of walking it: an
    # `if`'s condition, a comparison, a `not`, a unary minus.  Every division inside any
    # of them vanished.  The unary minus is the sharpest: it walked its operand only when
    # `term_opt` FAILED — the better it understood the code, the less it checked it.
    #
    #   EVERY SUB-EXPRESSION IS WALKED EXACTLY ONCE, whether or not it is also translated.
    #
    # And it was not a corner case.  07's own primes sieve — `fn divides(d, n) = n / d * d
    # == n`, a body that IS a comparison — reported ZERO obligations for the whole life of
    # this fork.  That verdict has moved in robust_sweep.py, and the move is the finding.
    #
    # Found by the adversary (seed 4242), not by a human.  Nobody writes `if (x / y) < x`
    # on purpose, and nobody auditing this checker thought to look inside a Bool.
    "20_condition_safe.lark":   ("proved", 5),
    "20_condition_unsafe.lark": ("unproved", 4, 4),

    # 21 is a later version: the measure's declared result, PROVED by structural induction over
    # its own arms — one obligation per constructor, the induction hypothesis assumed
    # at the recursive occurrences and nowhere else.  An axiom becomes a theorem, and
    # `NONNEG_UF` — the set literal the first version conceded it "strictly should not have to" know —
    # is DELETED.  What is left is `refine.PRIMITIVE_AXIOMS`, one table, one line, in
    # the same language as a declaration: `string_length` stays postulated because a
    # String has no constructors and there is nothing to induct over.
    #
    # The safe file's 5 obligations are the rung end to end: 2 induction VCs (`len(Nil)
    # >= 0`; `len(Cons($f, rest)) >= 0` from the IH), 2 for `size`'s body against the
    # contract that ties it to the measure, and the division by `n + 1` — which is
    # provable ONLY from the declared result, because `xs` is a parameter and no
    # equation fires at an opaque term.  Drop the `{v : Int | v >= 0}` and that
    # division goes unproved: the theorem is load-bearing, not decoration.
    #
    # The mutant is the DONE-WHEN, and it detonates.  `{v : Int | v > 0}` is false of a
    # length, and it fails at exactly one place — the 'Nil' arm, `len(Nil) > 0` against
    # `len(Nil) == 0`; the 'Cons' arm still proves from the IH, because a false claim
    # about a recursive definition is usually false at the BASE case.  Admit it and the
    # program does not merely over-promise: `avg` divides by `n == len(xs)`, the bogus
    # claim discharges `n /= 0` at the opaque parameter, the checker prints `ok`, and
    # `main` passes `Nil` and divides 100 by 0.  It is also why an induction VC is
    # denied its own conclusion as an axiom (`Refiner.run`): hand the 'Nil' arm the
    # thing it is proving and it discharges itself.  Assuming the conclusion is not a
    # subtle bug — it is the whole difference between an induction and a lie.
    "21_result_safe.lark":     ("proved", 5),
    "21_result_unsafe.lark":   ("unproved", 1, 5),

    # A LAMBDA'S BODY IS CODE, AND CODE IS WALKED — the eighth false proof, and the first
    # one found ON PURPOSE.  `check` walked a lambda's body (it has an RFun to push in);
    # `synth` returned ROpaque() without looking, and an unannotated `let h = fn (a) => …`
    # goes through `synth`.  So a division inside a local lambda raised NO OBLIGATION:
    # `ok: 0 obligation(s) proved`, exit 0, then ZeroDivisionError.  Found by
    # tests/invariants.py asking, of every node in the corpus, "did the checker LOOK at
    # this?" — which is the question none of the other suites had ever asked.
    "22_lambda_safe.lark":     ("proved", 4),
    "22_lambda_unsafe.lark":   ("unproved", 1, 1),

    # 27 is the NINTH false proof, and 22's sibling.  22 made `synth` WALK a lambda's
    # body; that left a hole one step along.  The body is walked with the parameter bound
    # to what its annotation SAYS — `fn (k : {v | v != 0}) => 100 / k` assumes `k != 0`
    # and proves the division — but `synth` returned `ROpaque()`, which carries no
    # parameter contract, so the APPLICATION discharged nothing:
    #
    #     let g = fn (k : {v : Int | v != 0}) => 100 / k in g(0)
    #
    # reported `ok: 1 obligation(s) proved`, exit 0, and then divided by zero.  The body's
    # `k != 0` was proved from an assumption the call never had to earn.  The fix is the
    # one 22's own comment pointed at: a lambda synthesises an `RFun` carrying its
    # parameters' refinements, exactly as a top-level `fn` does, so `_apply` raises the
    # call-site obligation — and the body may keep assuming the parameter BECAUSE the
    # caller is now made to establish it.  Found by the adversary, which speaks refined
    # lambdas and RUNS what the checker proves.
    #
    # This is also why 22_lambda_safe moved from 3 to 4: its `quotient` calls `go(d)`
    # through exactly this path, and that call now honestly discharges `d != 0` (proved,
    # from `d`'s own annotation) instead of silently discharging nothing.
    #
    # The safe file's 3 obligations: the body's `k != 0` (from `k`'s annotation), the call
    # `g(d)` owing `d != 0` (from `d`'s annotation), and `main`'s `use(4)` owing `4 != 0`.
    # The mutant calls `g(x - x)` — `g(0)` — and the call owes `0 != 0`, which is false; it
    # would detonate `100 / 0` were it admitted.
    "27_lambdapre_safe.lark":   ("proved", 3),
    "27_lambdapre_unsafe.lark": ("unproved", 1, 2),

    # 23 is a later version: a BOOL-VALUED measure.  An Int measure hangs on `==` and congruence
    # closure was already built to decide those; a Bool measure is a PROPOSITION, its
    # atom is `Atom(pos(...))`, and its arm is an EQUIVALENCE (two implications).  The
    # rung's one solver cost is in `Theory.consistent`: the `BoolLit` an atom is
    # bridged to must ENTER the closure, or `true` and `false` are never asserted
    # DISTINCT and the atom decides nothing.  Revert that one line and 23_safe drops
    # from 4 to 2 — both Bool-atom obligations fail — which is what makes the row a
    # regression test for the fix and not a decoration.
    #
    # The safe file's 4 obligations are the two halves at once.  DESTRUCTING: `root`
    # knows `pos(t)` from its contract and `t == Node(l, x, r)` from the pattern, two
    # terms equal only by congruence, and `x > 0` arrives only if the atom crosses
    # that equality and resolves through the equivalence to `true`.  BUILDING: `main`'s
    # call owes `pos(Node(Leaf, 5, Leaf))`, a proposition about a term the program
    # wrote, decided in LIA and the Bool atoms.  The Tree is MONOMORPHIC, so `x` is Int
    # by construction — this rung needs nothing from the polymorphic field-sort gap.
    #
    # The mutant is one character — the built tree's root is `0`, not `5` — so the
    # call owes `pos(Node(Leaf, 0, Leaf))`, which is FALSE.  It goes unproved; were it
    # admitted, `root` returns 0 and `main` divides 100 by it.
    "23_boolmeasure_safe.lark":   ("proved", 4),
    "23_boolmeasure_unsafe.lark": ("unproved", 1, 4),

    # a later version — the POLYMORPHIC-field thermometer.  The same allpos/head/divide shape as
    # 23, but over `List(a)` destructured at `Cons(x, rest)`.  Before the fix `x` landed
    # at sort OTHER (infer_pat instantiates `Cons` with a fresh `a` and never sees the
    # scrutinee is a `List(Int)`), the `x > 0` conjunct of the measure equation was
    # DROPPED on the sort guard, and `head`'s postcondition went unproved: 3 of 4.  The
    # fix carries the scrutinee's monotype on its RBase and unifies the pattern against
    # it, pinning `x : Int` — the ADT analog of the RTuple fix — so all 4 now prove.  It
    # RUNS → 20.  The mutant builds `Cons(0, Nil)`: the call owes `allpos(Cons(0, Nil))`,
    # which is FALSE, and stays unproved — the fix pins the field at the DEFINITION of
    # `head` without making the false precondition provable at its CALL.
    "24_polylist_safe.lark":      ("proved", 4),
    "24_polylist_unsafe.lark":    ("unproved", 1, 4),

    # a later version — `min`/`max` as UNINTERPRETED symbols with their defining axioms,
    # and no new decision-procedure surface: they reach the logic exactly as
    # `string_length` does (a `_builtin_contracts` selfify to the UF term, plus a
    # `PRIMITIVE_AXIOMS` entry), instantiated at mentioned terms by `result_axioms`.
    # The three <=/>= facts and the DISJUNCTION (`min(a,b)==a or ==b`) are the whole of
    # what the checker takes on faith, and the disjunction is load-bearing: `min_pos`
    # proves `min(a,b) > 0` from `a>0 and b>0` ONLY because the result is one of the two
    # arguments — the two `<=` facts alone give an upper bound and no lower one.
    #
    # The safe file's 6 obligations: `min_le`'s body (the two `<=`), `min_pos`'s body
    # (the disjunction), `max_ge`'s body (the two `>=`), and in `main` the two call-site
    # arguments `5>0`/`2>0` plus the division `100 / m` (safe because `min_pos` returns
    # `{v > 0}`).  The mutant calls `min_pos(5, 0)`: the argument `0` fails `0 > 0`, one
    # obligation flips, and the division would detonate `100 / 0` were it admitted.
    "25_minimum_safe.lark":       ("proved", 6),
    "25_minimum_unsafe.lark":     ("unproved", 1, 6),

    # The soundness guard, `16_axiom` re-run for `min`: a program declares its own
    # `min` (here, the SUM), so the axiom is DROPPED (Refiner.__init__ intersects
    # PRIMITIVE_AXIOMS with the un-rebound names) and `min` is uninterpreted.  `bad`'s
    # `min(a,b) <= a` is then unprovable — the true answer, since `min(1,1)` is `2`.
    # Were the axiom asserted about the program's own function, it would be a false
    # proof: an axiom is about the primitive, not about the name.
    "25_minimum_redef.lark":      ("unproved", 1, 1),

    # a later version — `if` in PREDICATE position.  A guarded predicate translates to
    # `(c => p) and (not c => q)` ONLY when c, p, q all translate; otherwise the whole
    # predicate is None, and at a declaration the STRICT `formula()` rejects it — never
    # silently `true`.  No solver change (Implies/And/Not already decided); no term-level
    # `if` (a conditional in INT position stays untranslatable, which is sound).
    #
    # `abs` needs the guard on BOTH sides.  The safe file's 3 obligations: abs's body,
    # one per branch (then owes `x == x`; else owes `(0 - x) == 0 - x` and `(0 - x) >= 0`),
    # and the division `100 / a` in `main` — safe because the postcondition, instantiated
    # at the argument `-4`, takes the else disjunct and gives `a == 4`.  The mutant calls
    # `abs(0)`: the guard is TRUE, `a == 0`, the division flips to unproved, and it would
    # detonate `100 / 0` were it admitted.
    "26_ifpred_safe.lark":        ("proved", 3),
    "26_ifpred_unsafe.lark":      ("unproved", 1, 3),

    # The soundness sentinel, 25_minimum_redef re-run for `if`: the else branch is
    # `v == x * x * x`, which is NON-LINEAR, so `q` is untranslatable, the whole
    # `if`-predicate is None, and the contract is REJECTED at its declaration.  It must
    # stay rejected after step 2 lands: an `or Top()` on the untranslatable branch (false
    # proofs #2/#7) would admit a `true` where the source said `v == x * x * x`.
    "26_ifpred_drop.lark":        ("error", "not a predicate in the decidable fragment: if"),

    # a later version, Part A — the min/max-speaking adversary's first catch, and a
    # ROBUSTNESS row, not a soundness one.  `min`/`max`'s result axiom (step 1) is
    # instantiated at every application an obligation mentions; a term-level `if` argument
    # is untranslatable (step 2), so it is skolemised at sort OTHER, and the axiom read
    # `min($k1, $k2) <= $k1` — an order comparison on a non-integer term — which the solver
    # RAISED on.  A legal, at-run-time-safe program became `comparison on non-integer
    # terms`, i.e. no verdict, the one grade `torture` calls a failure.  `result_axioms`
    # now takes the sort context and DROPS any instantiation whose order-comparisons are
    # not both integers (`_instantiate`'s rule, one table over): `min`'s result stays
    # opaque and the division goes honestly UNPROVED.  It RUNS (min(5, 5) is 5 → 20) — too
    # weak, which is allowed; raising is not.  Before the fix this row was ("error", ...).
    "28_minmax_untranslatable.lark": ("unproved", 1, 1),

    # THE FLOAT INTERLUDE — 29–32.  Not a new rung: a demonstration that the ONE fact
    # a later version established (no term is ever built at sort FLOAT) is realised through
    # DIFFERENT machinery in different contexts, and a pinning of the contexts the suite
    # had left undriven.  A Float goes SILENT where a formula is optional (a program-
    # position guard, 29) and is REJECTED where a formula is mandatory (a refinement, 30;
    # a measure arm, 32) — one principle, three code paths.
    #
    # 29 is the fourth road into a Float and the only NEW soundness row here: a Float
    # carried in a CONSTRUCTOR FIELD.  Nothing in prove/ had a Float field before, so the
    # `f == f` lie of 13 was unguarded on this road.  The mutant reads the guard off the
    # Float field instead of the Int field beside it; the guard goes silent, the division
    # is honestly unproved, and — the watched-to-fail evidence — deleting the FLOAT guard
    # in `term_opt` flips it to `2 proved`, 13's false proof reached through a
    # constructor.
    "29_floatfield_safe.lark":    ("proved", 2),
    "29_floatfield_unsafe.lark":  ("unproved", 1, 2),

    # 31 is the OTHER half of the congruence lie.  13 is REFLEXIVITY (`x == x`, false for
    # NaN); 31 is SUBSTITUTIVITY (`a == b` ⊢ `tag(a) == tag(b)`, false for values that
    # compare equal but differ — `0.0` and `-0.0`).  The mutant launders a division's
    # safety through the equality of two Floats; under speakable Floats the guard `a == b`
    # asserts a term equality, congruence discharges the divisor, and it is `2 proved` —
    # so this too flips under the `term_opt` injection.  The lesson of the interlude in
    # one row: reflexivity and substitutivity are the two axioms congruence closure is
    # built from, and a SINGLE guard (no Float term is ever built, so `a == b` over Floats
    # is itself unreadable) shuts both doors.  The control divides via an honest Int.
    "31_substitutivity_safe.lark":   ("proved", 2),
    "31_substitutivity_unsafe.lark": ("unproved", 1, 2),

    # THE EQUALITY SEAM — 33, the answer to "what other types need thinking?" (String,
    # functions), and the MIRROR of the Float interlude.  These are the suite's only
    # rows that are `proved` and yet deliberately absent from RUNS, because they do not
    # run: `==` is polymorphic in HM (`forall a. a -> a -> Bool`, infer.py), reflexive in
    # the logic (String/closure are OTHER, congruence makes `s == s` valid, so the guarded
    # division is proved vacuously), but implemented ONLY for Int/Float at run time (cek.py
    # `binop` raises `cannot apply '=='` on a String or a closure).  So the checker proves
    # the division by believing `s == s`, and the machine RAISES on `s == s` before any
    # branch — no ZeroDivisionError (the narrow promise holds), but `proved` in a strictly
    # weaker sense, and that gap is the seam.  It is the opposite polarity of Float: Float's
    # `==` EXISTS and lies (a false proof, so Floats are made unspeakable); String's and a
    # function's `==` do NOT exist, and the logic believes in them anyway.  The seam is
    # documented as a boundary in the refinement notes (beside Z-vs-32-bit and partial correctness), not
    # closed — it is shared with 07 (a language property, not a fork regression), and it
    # preempts rather than produces a false proof.  The control (33_eqseam_control) is the
    # positive space: a String reasoned about soundly through `string_length`, proved AND
    # run → 33, so the seam reads as "one operator, `==`" and not "Strings are second-class".
    "33_eqseam_control.lark": ("proved", 2),
    "33_eqseam_string.lark":  ("proved", 2),   # NOT in RUNS — raises `cannot apply '=='`
    "33_eqseam_fun.lark":     ("proved", 2),   # NOT in RUNS — raises `cannot apply '=='`

    # The negatives.  A measure's arms become AXIOMS, so every one of these is a
    # soundness condition, and each must fail as MALFORMED (an error) rather than as
    # unproved — the distinction: a bug in the source is not a weak proof.
    #
    # 11_measure_nonstructural is the one with teeth, and a later version is what armed it.  Its
    # measure asserts bad(xs) == 1 + bad(xs); disarm the structural check and the
    # checker instantiates that at the Cons arm's own term, derives an inconsistency,
    # and VERIFIES that `absurd` returns a negative number when it returns 0 — one
    # false proof, ex falso, measured.  The Nil arm stays honest, because its equation
    # (bad(Nil) == 0) is consistent: the poison reaches exactly the terms it is
    # instantiated at.  a later version's structural check is what stands between the axioms and
    # that, and it is load-bearing for a later version rather than good manners.
    "11_measure_nonstructural.lark": ("error", "recursion is not structural"),
    "11_measure_partial.lark":       ("error", "has no arm for Cons"),
    "11_measure_overlap.lark":       ("error", "constructor 'Nil' has two arms"),
    "11_measure_wildcard.lark":      ("error", "every arm must be a constructor pattern"),
    "11_measure_fragment.lark":      ("error", "not expressible in the predicate language"),
    "11_measure_sort.lark":          ("error", "result type must be Int or Bool"),
    "11_measure_clash.lark":         ("error", "same name as a function or value"),

    # The Float interlude's two REJECTIONS (see 29–32 above).  30 is a refinement over a
    # Float; 32 is a measure returning a Float field.  Both are the unspeakability of a
    # Float reached where a formula is mandatory — 30 at the strict `formula()`, 32 at the
    # measure-arm expressibility check (which 11_measure_fragment already pins for a
    # non-Float arm; 32 is its Float face, kept for the interlude's side-by-side).
    "30_floatpred_reject.lark":      ("error", "not a predicate in the decidable fragment"),
    "32_floatmeasure_reject.lark":   ("error", "not expressible in the predicate language"),

    # NESTED MATCH IN A MEASURE — 34.  `rdepth` looks at a
    # CHILD's shape (a second match, on a field of the first), the move a BST's maxv/minv
    # needs and a flat measure cannot make.  The nested match FLATTENS to one equation per
    # (outer x inner) path, and those equations FIRE AT CONCRETE SUBFIELDS only.  Six
    # obligations carry the rung in both directions: 3 induction VCs proving the declared
    # `{v >= 1}` (the nested arm's target is a concrete subfield, `Node(l, v, Node(rl, rv,
    # rr))`, with the IH at `rdepth(Node(rl, rv, rr))`); `use`'s single division, safe over
    # an OPAQUE tree BECAUSE that declared result gives `d == rdepth(t) >= 1 > 0`; and the
    # two call-site obligations that fire the nested equations at the built trees — `2 ==
    # rdepth(Node(Leaf, 5, Leaf))` and `3 == rdepth(Node(Leaf, 1, Node(Leaf, 2, Leaf)))`.
    # The mutant claims the first built tree has depth 0; the nested Leaf equation fires and
    # says 2, so `0 == rdepth(Node(Leaf, 5, Leaf))` is `0 == 2`, unproved — and had it been
    # admitted, `use` would run `100 / 0`, which is why the mutant is absent from RUNS.
    "34_nestedmeasure_safe.lark":    ("proved", 6),
    "34_nestedmeasure_unsafe.lark":  ("unproved", 1, 6),

    # THE BINARY SEARCH TREE — 35, the invariant the whole axis was
    # pointed at.  No new checker mechanism: it is Part B's nested match (now two deep, on
    # both children), a later version's Bool measure, and a measure body that MENTIONS another measure
    # (`bst` calls `minv`/`maxv` on a child, fired at the physical subterms of a built tree
    # by the single-pass closure).  The direction it proves is BUILDING — that a CONSTRUCTED
    # tree is ordered; the equations fire at concrete subfields.  The safe file builds a
    # six-node bst and `use` requires `bst`, one obligation, and it runs → 3.  The mutant
    # flips one inner value so the left subtree's max (9) exceeds the root (3); `bst`'s
    # deepest arm asks `maxv(l) < v` — `9 < 3` — and the whole `bst` resolves to false, so
    # the call owes a `bst` it cannot have.  The DESTRUCTING direction (reading order back
    # out of an OPAQUE `bst(t)`) stays open here: over an opaque tree the nested guards
    # decline.  That was the boundary 35 named — and 36 crosses it.
    "35_bst_safe.lark":              ("proved", 1),
    "35_bst_unsafe.lark":            ("unproved", 1, 1),

    # THE DESTRUCTING BINARY SEARCH TREE — 36, the boundary 35 named
    # and left standing.  The way past it is NOT bound invariants on minv/maxv (those must
    # hold of every tree, and minv(t) <= maxv(t) is false for an unordered one).  It is to
    # make `bst` a SINGLE match on t and push "left child below the root" into an
    # EXTRA-PARAMETER measure: lt(t, b) / gt(t, b).  Unguarded, `bst`'s equation now fires
    # on Node(l, x, r) even when l, x, r are OPAQUE match binders, and hands out bst(l),
    # bst(r), lt(l, x), gt(r, x) — the order facts a consumer descends on.  The new
    # checker capability is that an extra-parameter measure's equation, which is about an
    # APPLICATION (the bound b lives only there), fires DEMAND-DRIVEN: it follows the first
    # argument's structure with b fixed, constructor-headed demands propagating structurally
    # and variable-headed ones bridging to constructor terms by sort.  The safe file proves
    # BOTH directions — build (a constructed tree is a bst, as 35) and leftsub/descend (from
    # an opaque bst, the left child is a bst, read out and recursed on) — six obligations,
    # and it runs → 3, 1.  The mutant lies in the DESTRUCTING direction 35 could not attempt:
    # `swap` claims a bst for Node(r, x, l), whose obligation needs lt(r, x) — the negation
    # of the gt(r, x) the opaque bst handed out — so 1 of 4 is unproved.  That the order
    # facts convict the swap is the rung.
    "36_bstdestruct_safe.lark":      ("proved", 6),
    "36_bstdestruct_unsafe.lark":    ("unproved", 1, 4),
}

# Checked *and run*: proved (or honestly unproved), then executed on the CEK machine.
# The claim is erasure — a refinement, and now a measure, is gone by run time.
RUNS = {
    "08_erasure.lark":      "7\n3\n97\n",
    "10_measure_len.lark":  "3\n",
    "12_measure_safe.lark": "3\n",
    "13_float_safe.lark":   "25\n",
    "14_guard_safe.lark":   "25\n",
    "15_shadow_safe.lark":  "25\n",
    "16_axiom_safe.lark":   "14\n",
    "17_impl_safe.lark":    "110\n",
    "18_divisor_safe.lark": "100\n",
    "19_floatlit_safe.lark": "3.5\n25\n0\n",
    "20_condition_safe.lark": "true\n0\n1\n",
    "21_result_safe.lark":    "25\n",
    "22_lambda_safe.lark":    "25\n25\n",
    "23_boolmeasure_safe.lark": "20\n",
    "24_polylist_safe.lark":    "20\n",
    "25_minimum_safe.lark":     "50\n",
    "26_ifpred_safe.lark":      "25\n",
    "27_lambdapre_safe.lark":   "25\n",
    "28_minmax_untranslatable.lark": "20\n",
    "29_floatfield_safe.lark":       "25\n",
    "31_substitutivity_safe.lark":   "25\n",
    "33_eqseam_control.lark":        "33\n",
    "34_nestedmeasure_safe.lark":    "50\n33\n",
    "35_bst_safe.lark":              "3\n",
    "36_bstdestruct_safe.lark":      "3\n1\n",
}


def matches(want: tuple, got: tuple) -> bool:
    """Counts are pinned exactly; MESSAGES are pinned by what they must SAY.

    A count that drifts is a finding, so it is compared byte for byte.  An error
    message is prose — it gets reworded, and pinning its every character would make
    the suite fail for a comma while proving nothing about the checker.  What the
    row is actually claiming is that the program is rejected FOR THE STATED REASON,
    so that is what is compared: the reason must appear in the message.
    """
    if want[0] != got[0]:
        return False
    if want[0] in ("error", "rejected"):
        return want[1] in got[1]
    return want == got


def check(path: pathlib.Path):
    """(kind, ...) — the same three shapes as EXPECT."""
    try:
        res = refine.check_program(str(path))
    except refine.FRONTEND_ERRORS as e:
        return ("rejected", str(e))
    except refine.REFINE_ERRORS as e:
        return ("error", str(e))
    if res.failed:
        return ("unproved", len(res.failed), res.total)
    return ("proved", res.proved)


def run_cek(path: pathlib.Path) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(SRC / "cek.py"), str(path)],
        capture_output=True, text=True, timeout=TIMEOUT,
        cwd=str(SRC), env={**os.environ, "PYTHONPATH": str(SRC)},
    )
    return r.returncode, r.stdout


def main() -> int:
    files = sorted(SUITE.glob("*.lark"))
    ok = fail = 0

    undeclared = [f.name for f in files if f.name not in EXPECT]
    missing    = [n for n in EXPECT if not (SUITE / n).exists()]

    for f in files:
        if f.name not in EXPECT:
            continue
        want = EXPECT[f.name]
        got  = check(f)

        if matches(want, got):
            note = ""
            # An erasure row is only green if the program also RUNS as expected.
            if f.name in RUNS:
                rc, out = run_cek(f)
                if rc != 0 or out != RUNS[f.name]:
                    print(f"  FAIL  {f.name:<30} checked, but the program did not run "
                          f"as expected (rc={rc}, out={out!r})")
                    fail += 1
                    continue
                note = "  + runs, output as expected"
            print(f"  ok    {f.name:<30} {show(got)}{note}")
            ok += 1
        else:
            print(f"  FAIL  {f.name:<30} want {show(want)}  got {show(got)}")
            fail += 1

    print(f"\n  {ok} ok, {fail} fail")
    for n in undeclared:
        print(f"    UNDECLARED  {n} — in prove/, no expected verdict")
    for n in missing:
        print(f"    MISSING     {n} — expected, not in prove/")

    if fail or undeclared or missing:
        print("\n  prove suite FAILED")
        return 1
    print("  prove suite clean — every safe program checks, every mutant is caught.")
    return 0


def show(v: tuple) -> str:
    match v:
        case ("proved", n):
            return f"{n} proved"
        case ("unproved", k, n):
            return f"{k} of {n} unproved"
        case ("rejected", text):
            return f"rejected: {text}"
        case ("error", text):
            return f"refinement error: {text}"
    return str(v)


if __name__ == "__main__":
    sys.exit(main())
