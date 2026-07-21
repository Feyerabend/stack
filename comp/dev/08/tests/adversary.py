"""
The adversary — random Lark programs against the checker's own promise.

    python3 08/tests/adversary.py [cases] [seed]      # or: make -C 08 adversary

`solver_fuzz.py` fuzzes the SOLVER, and in thousands of cases it has never found an
unsound answer.  Every real bug this project has had was one level up, in the checker
that BUILDS the obligations — the four false proofs of V2.2′ and the unwalked `impl`
body of V2.2″ — and all five were found BY HAND, under a suite that was green the whole
time.  A verifier's report cannot be its own witness.  This is the witness.

AND IT WORKED, WHICH IS THE UNCOMFORTABLE PART.  In its first afternoon this file found
THREE more false proofs, none of which two hand-audits had caught (PROVE.md V2.2‴):

  - a divisor the logic could not NAME (`x * y`, or a local lambda's result) raised no
    obligation at all — V2.2′(b)'s rule at the opposite polarity.  A hypothesis it cannot
    read must be DROPPED; a goal it cannot read must be ASKED ANYWAY.        → 18_divisor
  - a Float LITERAL had no sort, so it was an ordinary opaque value, so it could be
    EQUATED, so `nan == nan` was believed.                                   → 19_floatlit
  - and the floor: a division inside an `if` CONDITION, a comparison, a `not` or a unary
    minus was NEVER VISITED — `ok: 0 obligation(s) proved`, exit 0, then a ZeroDivisionError.
    Open since V1.  Sitting inside 07's own primes sieve the whole time.     → 20_condition

Nobody writes `if (x / y) < x` on purpose.  Nothing in a Bool position LOOKS partial.  An
audit looks where a bug would be interesting; a random program does not know which
positions are supposed to be interesting.  That is the entire argument for this file.

THE ORACLE IS THE PROMISE ITSELF, and it is executable:

    if the checker says `ok`, the program must not crash.

Lark has exactly two runtime errors a refinement is supposed to rule out — division by
zero, and an out-of-range `string_index` — and there is a real machine on the other side
(`cek.py`) that will raise them.  So: generate a program, check it, and if it is PROVED,
RUN it.  A `ZeroDivisionError` under an `ok` verdict is a false proof, printed with the
seed that made it.  An UNPROVED program that runs fine is not a failure — that is the
sound direction, the checker being too weak, and the run tells us how often.

THE SECOND ORACLE IS ERASURE.  Every program is generated twice: once with its
refinements, once with the predicates stripped to their base types.  Both are run, and
the outputs must be identical.  A refinement that changed what a program COMPUTES would
not be a type at all.

The generator is aimed at what has actually drawn blood, not at Lark in general:

  - `/` everywhere, including divisors the logic cannot name (`x * y` is NON-LINEAR,
    and a term it cannot express is a term it must not stay silent about)
  - guards it cannot read, for the same reason (V2.2′(b))
  - Floats, and the two NaN factories `0.0 / 0.0` and `float_sqrt(-1.0)` (V2.2′(a)) —
    now in BOTH the positions a Float reaches the checker from: a literal/param in a
    guard, and (the float interlude, prove/29) a CONSTRUCTOR FIELD, destructured and
    put into the same `fld == fld` reflexivity trap.  The generator could not speak a
    Float field until then, and a generator only finds bugs in the language it can speak.
  - local bindings that SHADOW a global function (V2.2′(c))
  - a program that redeclares `string_length` (V2.2′(d))
  - `impl` bodies with real code in them (V2.2″)
  - `string_index`, the one builtin with a precondition worth proving
  - `min`/`max` (V2.4c step 1), in BOTH the positions that matter: as a DIVISOR over
    arbitrary atoms, where the correct three-fact axiom leaves `min(x, 0)` non-zeroness
    unprovable and a TOO-STRONG axiom proves it and divides by zero (real runtime teeth —
    confirmed by injecting `min > 0`); and in a CONTRACT (`minpos`), the way the proving
    parts actually consume them, where the axiom's disjunction is load-bearing for a proof
  - `if`-PREDICATES (V2.4c step 2), as coverage: checked and run under random code, though
    a bug in them cannot reach a division here — the soundness teeth are at the DECL level
    (`26_ifpred_drop` + I5), because the shared translation ties body-check to call-read
    (see `abs_decls`)
  - NESTED-MATCH measures (V2.4c step 3 Part B / step 4), the shapes a BST needs and the
    last language this generator learned.  A nested measure fires only at CONCRETE
    subfields, so it cannot be consumed through a companion function the way a flat one is
    (an honest `fn f(t) : {v == m(t)}` recurses over an OPAQUE subfield and the nested
    equation DECLINES there — it does not even prove); both are consumed the fixture-34/35
    way, a parameter contract plus a concrete literal tree whose measure the generator
    computes here (see `nested_measure_decls`).  Two shapes, one per direction:
      · `rd`, a nested Int measure with a DECLARED result, consumed as a DIVISOR — the
        V2.3 lie-and-catch hazard one match deeper: `{v >= 1}` false of a Leaf arm of 0,
        believed, divides `100 / d` by zero (`34_nestedmeasure`).  Real RUN teeth; the
        correct checker rejects it at the declaration, which is what I6 watches.
      · `minv`/`maxv`/`bst`, a match TWO deep on both children with a body that mentions
        another measure — the search-tree invariant (`35_bst`).  It has NO divisor, so a
        false proof cannot crash; the generator computes `bst` of the tree it builds and a
        THIRD oracle (below) fails any PROVED program that certified a disordered tree.

Only false proofs (a crash under `ok`, or a `bst` the model calls disordered) and erasure
violations fail the run.  Everything else — a program the front end rejects, a proof the
checker misses — is counted and shown.
"""

from __future__ import annotations
import os, pathlib, random, re, subprocess, sys, tempfile, traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent          # .../lark/08
SRC  = ROOT / "src"
sys.path.insert(0, str(SRC))

import refine                                                  # noqa: E402

TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "30"))

# The runtime errors a proved program is not allowed to have.  Both are promises the
# checker actually makes: every `/` raises a non-zero obligation, and `string_index`
# carries a real precondition (`prove/01_bounds`).
CRASH_MARKERS = ("ZeroDivisionError", "IndexError", "string index out of range")


# -- the generator --------------------------------------------------------------
#
# Programs are built to TYPE-CHECK by construction — the interesting failures are the
# ones the checker gets wrong, not the ones the front end throws out — so every
# expression here is Int-typed, every name is in scope, and there is no recursion (a
# RecursionError is not a false proof, it is a fuzzer with no manners).

STRINGS = ['"abc"', '"hello world"', '""', '"x"']

class Gen:
    def __init__(self, rng: random.Random) -> None:
        self.rng   = rng
        self.n     = 0
        self.refs  = True      # emit refinements (False = the erased twin)
        self.tree_declared = False        # `program` resets these; here so a `*_decls`
        self.bst_trees: list[bool] = []   # method is safe to call standalone too

    def fresh(self, p: str = "t") -> str:
        self.n += 1
        return f"{p}{self.n}"

    # -- types --

    def refined_int(self) -> str:
        """A parameter contract, or a plain Int in the erased twin."""
        if not self.refs or self.rng.random() < 0.45:
            return "Int"
        p = self.rng.choice([
            "v > 0", "v >= 0", "v != 0", "v > 1", "v >= 0 and v < 10",
        ])
        return "{v : Int | " + p + "}"

    # -- expressions (Int) --

    def expr(self, env: list[str], depth: int) -> str:
        r = self.rng.random()
        if depth <= 0:
            return self.atom(env)

        if r < 0.16:
            op = self.rng.choice(["+", "-", "*"])
            return f"({self.expr(env, depth - 1)} {op} {self.expr(env, depth - 1)})"

        if r < 0.22:
            # `min`/`max` (V2.4c step 1) — the surface the adversary could not SPEAK
            # until now.  They are ordinary Int builtins, so this keeps the program
            # Int-typed by construction; the interesting position is as a DIVISOR (see
            # `divisor`), where the correct three-fact axiom leaves `min(x, 0)`'s
            # non-zeroness UNPROVABLE and a too-strong axiom would prove it and crash.
            fn = self.rng.choice(["min", "max"])
            return f"{fn}({self.expr(env, depth - 1)}, {self.expr(env, depth - 1)})"

        if r < 0.34:
            # THE HAZARD.  Sometimes the divisor is a term the logic cannot express —
            # `(x * y)` is non-linear — and that is the case worth generating: silence
            # about a GOAL is not the same as silence about a hypothesis.
            return f"({self.expr(env, depth - 1)} / {self.divisor(env, depth - 1)})"

        if r < 0.46:
            return (f"(if {self.cond(env, depth - 1)} "
                    f"then {self.expr(env, depth - 1)} "
                    f"else {self.expr(env, depth - 1)})")

        if r < 0.58:
            n = self.fresh("w")
            val = self.expr(env, depth - 1)
            return f"(let {n} = {val} in {self.expr(env + [n], depth - 1)})"

        if r < 0.66 and env:
            # A guarded division: the shape a checker is supposed to prove.
            d = self.rng.choice(env)
            return (f"(if {d} != 0 then {self.expr(env, depth - 1)} / {d} "
                    f"else {self.rng.randint(0, 9)})")

        if r < 0.72:
            # string_index — the builtin with a precondition.  Sometimes guarded
            # honestly, sometimes not at all.
            s = self.rng.choice(["s", self.rng.choice(STRINGS)])
            i = self.rng.choice([str(self.rng.randint(0, 3)), self.expr(env, 0)])
            if self.rng.random() < 0.5:
                return (f"(if {i} >= 0 and {i} < string_length({s}) "
                        f"then string_index({s}, {i}) else 0)")
            return f"string_index({s}, {i})"

        if r < 0.78:
            # A FLOAT, and the two NaN factories.  It may only ever reach an Int
            # through a guard — which is precisely the road V2.2′(a) came down.
            if self.has_floatbox and self.rng.random() < 0.5:
                # The SAME reflexivity trap, but the Float now arrives through a
                # CONSTRUCTOR FIELD (prove/29): build an `FB`, bind its Float field, and
                # guard on `fld == fld`.  The Int field `k` joins the environment; the
                # Float field never does, because a Float is not a term.
                fld = self.fresh("fld")
                k   = self.fresh("k")
                return (f"(match FB({self.float_expr()}, {self.rng.randint(0, 9)}) with "
                        f"| FB({fld}, {k}) => "
                        f"if {fld} == {fld} "
                        f"then {self.expr(env + [k], depth - 1)} "
                        f"else {self.expr(env + [k], depth - 1)} end)")
            return (f"(if {self.float_expr()} == {self.float_expr()} "
                    f"then {self.expr(env, depth - 1)} "
                    f"else {self.expr(env, depth - 1)})")

        if r < 0.86:
            return f"help({self.expr(env, depth - 1)}, {self.expr(env, depth - 1)})"

        if r < 0.92 and self.has_impl:
            c = self.rng.choice(["Penny", "Dime"])
            return f"weight({c})"

        if r < 0.97:
            # A LOCAL LAMBDA, WITH CODE INSIDE IT — and this generator did not emit one
            # until the eighth false proof, which is the point.  The docstring above has
            # said "a local lambda's result" since V2.2‴, because that was the SHAPE of
            # bug (5); but the fix for (5) was about a divisor the checker could not NAME,
            # and nobody noticed that the generator could not build the other half of the
            # sentence — a lambda whose BODY the checker never walked at all.
            #
            # `synth` returned ROpaque() for a Lambda without looking inside, so every
            # obligation in here was invisible: `ok: 0 obligation(s) proved`, exit 0, then
            # ZeroDivisionError.  It was found by tests/invariants.py, not by this file,
            # and that is a fact about this file worth leaving in it.
            #
            # THE LESSON, AND IT IS THE SAME ONE AS THE FUZZER'S BLIND SPOT: a generator
            # only ever finds bugs in the language it can speak.  Its grammar is a claim
            # about what programs exist, and an unexamined grammar is an unexamined claim.
            n = self.fresh("g")
            p = self.fresh("p")
            ann = self.refined_int()
            body = self.expr([p], depth - 1)
            return (f"(let {n} = fn ({p} : {ann}) => {body} in "
                    f"{n}({self.expr(env, depth - 1)}))")

        return self.atom(env)

    def divisor(self, env: list[str], depth: int) -> str:
        r = self.rng.random()
        if r < 0.30:
            # non-linear, and therefore unnameable in QF-UFLIA
            return f"({self.atom(env)} * {self.atom(env)})"
        if r < 0.45:
            return str(self.rng.choice([1, 2, 3, -1, 5]))
        if r < 0.55:
            return "0"
        if r < 0.70 and self.in_entry and self.has_measure and "m" in env:
            # V2.3's hazard — but only reachable through the NAME `m` (see `program`).
            return self.rng.choice(["m", "(m + 1)", "(m - 1)"])
        if r < 0.82:
            # `min`/`max` of two atoms — V2.4c step 1's hazard as a DIVISOR.  The atoms
            # range over 0 and negatives, so `min(x, 0)` and `max(-1, 0)` are terms the
            # CORRECT axiom cannot prove non-zero (it knows only `<= a`, `<= b`, and the
            # disjunction — an upper bound, never a lower one from unconstrained args).
            # So these divisions stay UNPROVED, the sound direction.  A too-strong axiom
            # — one that claimed `min` positive, or dropped a `<=` for a `>=` — would
            # prove one and DIVIDE BY ZERO, which the run oracle catches.  A generator
            # that only divided by min of two POSITIVES would test the provable case and
            # never this one.
            fn = self.rng.choice(["min", "max"])
            return f"{fn}({self.atom(env)}, {self.atom(env)})"
        return self.expr(env, depth)

    def atom(self, env: list[str]) -> str:
        if env and self.rng.random() < 0.6:
            return self.rng.choice(env)
        return str(self.rng.randint(-4, 9))

    def cond(self, env: list[str], depth: int) -> str:
        r = self.rng.random()
        if r < 0.25:
            # A guard the logic cannot READ (non-linear).  V2.2′(b): it must constrain
            # NEITHER branch.
            return (f"({self.atom(env)} * {self.atom(env)} "
                    f"{self.rng.choice(['>', '<', '=='])} {self.rng.randint(-2, 4)})")
        if r < 0.4:
            return (f"({self.cond(env, 0)} {self.rng.choice(['and', 'or'])} "
                    f"{self.cond(env, 0)})")
        op = self.rng.choice(["<", "<=", ">", ">=", "==", "!="])
        return f"({self.expr(env, max(0, depth - 1))} {op} {self.expr(env, 0)})"

    def float_expr(self) -> str:
        return self.rng.choice([
            "0.0 / 0.0",                  # NaN
            "float_sqrt(0.0 - 1.0)",      # NaN
            "1.0 / 0.0",                  # inf
            "f", "f * f", "0.0", "-0.0", "3.5",
        ])

    # -- the program --

    def measure_decls(self) -> list[str]:
        """A measure, a DECLARED result refinement for it, and the real function that
        computes it — the V2.3 shape, generated to be believed or caught.

        The two bodies are the SAME arms, so `size` really does compute `m1` and its
        contract (`v == m1(xs)`) is provable.  What is not necessarily true is the
        measure's declared RESULT: `{v : Int | v > 0}` is a lie about a measure whose
        `Nil` arm is 0, and the whole of V2.3 is that the lie must be caught by
        induction over those arms.  If it is not, `size(xs)` is believed non-zero, a
        division by it is PROVED, and `main` passes `Nil`.

        The recursion is bounded by the list literal `main` passes (three cells at
        most), so a RecursionError here would be a bug in the checker, not in the
        generator's manners."""
        rng = self.rng
        c0  = rng.choice([0, 0, 0, 1, 2, -1])       # the Nil arm — 0 is the interesting one
        c1  = rng.choice([1, 1, 2, 0, -1])          # what a Cons adds
        rec = rng.random() < 0.75
        step = f"{c1} + m1(rest)" if rec else f"{c1}"
        sstep = f"let n = size(rest) in {c1} + n" if rec else f"{c1}"
        ret = "Int"
        if self.refs:
            # Weighted towards the LIES — `v > 0` and `v != 0` are false of any measure
            # whose Nil arm is 0, and a checker that believes one divides by zero.  An
            # adversary that mostly generates honest declarations is mostly testing
            # nothing: aim it at the failure, and let the true declarations be the
            # control group.
            ret = self.rng.choice([
                "Int",
                "{v : Int | v >= 0}",
                "{v : Int | v > 0}",
                "{v : Int | v > 0}",
                "{v : Int | v != 0}",
                "{v : Int | v != 0}",
            ])
        return [
            "type List a =",
            "  | Nil",
            "  | Cons of a, List(a)",
            "",
            f"measure m1(xs : List(Int)) : {ret} =",
            "  match xs with",
            f"  | Nil           => {c0}",
            f"  | Cons(_, rest) => {step}",
            "  end",
            "",
            "fn size(xs : List(Int)) : {v : Int | v == m1(xs)} =",
            "  match xs with",
            f"  | Nil           => {c0}",
            f"  | Cons(_, rest) => {sstep}",
            "  end",
            "",
        ]

    def rand_tree(self, depth: int) -> str:
        """A literal Tree, weighted so a `0` node — the ZeroDivisionError seed — turns up
        often enough to matter.  A tree with any non-positive node does not satisfy `pos`,
        so a checker that PROVES `pos` of it anyway is the false proof this exists to
        catch."""
        if depth <= 0 or self.rng.random() < 0.45:
            return "Leaf"
        x = self.rng.choice([1, 2, 3, 5, 0, 0, -1])
        return f"Node({self.rand_tree(depth - 1)}, {x}, {self.rand_tree(depth - 1)})"

    def bool_measure_decls(self) -> list[str]:
        """A BOOL-valued measure and a consumer that divides by a field it guards — the
        V2.4 shape, and the language this generator learned to speak last.

        `pos(t)` holds iff every node of the tree is positive; it is a PROPOSITION, so its
        arm is an equivalence and the atom it turns on is `Atom(pos(...))`, decided by the
        solver bridge V2.4 added.  `root` may read a node's value only under `{v : Tree |
        pos(v)}`, and claims that value is `> 0` — the DESTRUCTING half, provable only
        because the measure crosses the pattern.  The hazard is the CALLER (see `program`):
        hand `root` a tree with a zero root, and the only thing between `ok` and a division
        by zero is `pos` being decided HONESTLY at the call.

        The Tree is MONOMORPHIC, so the destructured `x` is Int by construction — this
        shape needs nothing from the polymorphic field-sort gap, exactly as 23 does not.

        The `type Tree` is emitted through `_tree_type` so that when a nested measure or a
        bst is generated alongside this one, the single shared declaration is written once
        (two declarations of one type is an error — the same coordination `poly_measure_
        decls` does for `List`)."""
        decls = self._tree_type()
        return decls + [
            "measure pos(t : Tree) : Bool =",
            "  match t with",
            "  | Leaf          => true",
            "  | Node(l, x, r) => x > 0 and pos(l) and pos(r)",
            "  end",
            "",
            "fn root(t : {v : Tree | pos(v)}) : {v : Int | v > 0} =",
            "  match t with",
            "  | Leaf          => 1",
            "  | Node(l, x, r) => x",
            "  end",
            "",
        ]

    def rand_intlist(self, depth: int) -> str:
        """A literal `List(Int)`, weighted so a `0` head — the ZeroDivisionError seed —
        turns up often.  A list whose head is non-positive does not satisfy `allpos`, so
        a checker that PROVES `allpos` of it anyway is the false proof this exists to
        catch — the polymorphic-field twin of `rand_tree`."""
        if depth <= 0 or self.rng.random() < 0.40:
            return "Nil"
        x = self.rng.choice([1, 2, 3, 5, 0, 0, -1])
        return f"Cons({x}, {self.rand_intlist(depth - 1)})"

    def poly_measure_decls(self, declare_list: bool) -> list[str]:
        """The V2.4b shape: a BOOL measure over a POLYMORPHIC `List(a)`, destructured at a
        NAMED head `Cons(x, rest)` and divided by the field it guards.

        This is the path the field-sort fix opened.  `x` is the polymorphic field `a`,
        and it is pinned to `Int` ONLY because the scrutinee's monotype crosses the
        pattern; a checker that mis-sorts it drops the `x > 0` conjunct and cannot prove
        `phead`'s result positive (the SOUND direction — a dropped fact).  The hazard is
        the CALLER: hand `phead` a zero-headed list and the only thing between `ok` and a
        division by zero is `allpos` being decided honestly at the call.  The Tree in
        `bool_measure_decls` cannot reach this shape — its field is Int by construction —
        which is exactly why the generator needed to learn to speak a polymorphic one.

        `declare_list` is False when `measure_decls` already emitted `type List a`: two
        declarations of one type is an error, and the two measures share the type."""
        decls: list[str] = []
        if declare_list:
            decls += ["type List a =", "  | Nil", "  | Cons of a, List(a)", ""]
        decls += [
            "measure allpos(xs : List(Int)) : Bool =",
            "  match xs with",
            "  | Nil           => true",
            "  | Cons(x, rest) => x > 0 and allpos(rest)",
            "  end",
            "",
            "fn phead(xs : {v : List(Int) | allpos(v)}) : {v : Int | v > 0} =",
            "  match xs with",
            "  | Nil           => 1",
            "  | Cons(x, rest) => x",
            "  end",
            "",
        ]
        return decls

    def minmax_contract_decls(self) -> list[str]:
        """`min`/`max` where the PROVING PARTS actually consume them — inside a CONTRACT,
        with the axiom's disjunction load-bearing for a proof.  This is the intended use
        step 1 built them for (the `25_minimum` shape, and the bst fork's measure
        equations), not the generic runtime divisor of `divisor`/`expr`.

        `minpos` returns `{v : Int | v > 0}` from `min(a, b)` with both arguments positive,
        and that result is PROVABLE only because of the disjunction (`v == a or v == b`):
        the two `<=` facts bound `min(a, b)` from ABOVE and would let it be anything below,
        so the only thing keeping the minimum positive is that it IS one of two positives.
        This is exactly the obligation `25_minimum_safe`'s `min_pos` pins, generated here
        under random surrounding code so the disjunction is exercised at scale rather than
        by one hand-written fixture.  Divide by the result (see `program`) and the program
        RUNS iff the disjunction was decided honestly — a min axiom that dropped it could
        not prove `minpos`'s body, which is the SOUND direction (unproved), the mirror of
        the divisor hazard's too-strong direction."""
        return [
            "fn minpos(a : {v : Int | v > 0}, b : {v : Int | v > 0}) : {v : Int | v > 0} =",
            "  min(a, b)",
            "",
        ]

    def abs_decls(self) -> list[str]:
        """A function with an `if`-PREDICATE postcondition and a consumer that reads it —
        the V2.4c step 2 shape, and the second language this generator learned to speak.

        COVERAGE, NOT A RUNTIME CATCH, AND THE DIFFERENCE IS WORTH STATING.  Unlike the
        `min`/`max` divisor (a builtin, no body to gate it), an `if`-predicate bug cannot
        reach a division-by-zero here, and this was CHECKED before the comment was written:
        the translation `formula_opt` uses to build `absish`'s postcondition GOAL is the
        same one it uses to read that postcondition as a FACT at the call, so a bug in it
        breaks `absish`'s OWN body check — the whole program then goes unproved and is never
        run.  (Injecting the guard-flip `(¬c⇒p)∧(c⇒q)` left ZERO `absish` programs proved.)
        And because `absish` is total and honest, any postcondition it can PROVE is TRUE of
        its result, so at the one argument where `absish` returns 0 the checker cannot be
        made to prove the result non-zero.  The `if`-predicate's soundness teeth are
        therefore at the DECL level, where they already are: `26_ifpred_drop` (an
        untranslatable branch must stay REJECTED, never `or Top()`) and invariant I5.

        What this DOES buy: `if`-predicates checked and RUN under random surrounding code —
        the body VCs (one per branch), the call-site instantiation of the guard at a known
        argument (`absish(5)` ⇒ `ab == 5`, provable and run; `absish(0)` ⇒ `ab == 0`,
        unprovable, the sound direction), and both run oracles (no checker crash, erasure
        holds) over a surface that had NO adversary coverage at all before."""
        return [
            "fn absish(x : Int) : "
            "{v : Int | v >= 0 and (if x >= 0 then v == x else v == 0 - x)} =",
            "  if x >= 0 then x else 0 - x",
            "",
        ]

    # -- nested-match measures (V2.4c step 3 Part B / step 4): the tree shapes -----
    #
    # A nested measure takes a CHILD's shape apart — a second `match`, on a FIELD of the
    # constructor already destructured — and the checker fires its flattened equations
    # only at CONCRETE subfields.  That is why NEITHER shape below can be consumed the
    # way `measure_decls` consumes a flat one: a companion `fn f(t) : {v == m(t)}`
    # recurses over an OPAQUE subfield (`r` bound by the pattern, concrete only as an
    # equality hypothesis), and the nested equation DECLINES there — the honest companion
    # does not even prove.  So both are consumed the fixture-34 / fixture-35 way, a
    # PARAMETER contract and a CONCRETE literal tree at the call, whose measure value the
    # generator computes here in Python from the SAME structure it renders (so the
    # ground-truth oracle cannot drift from the emitted program).

    def _tree_type(self) -> list[str]:
        """`type Tree` — written once even when several Tree measures share it."""
        if self.tree_declared:
            return []
        self.tree_declared = True
        return ["type Tree = | Leaf | Node of Tree, Int, Tree", ""]

    def tree_struct(self, depth: int):
        """A random Tree as a nested tuple: `("L",)` or `("N", left, val, right)`."""
        if depth <= 0 or self.rng.random() < 0.5:
            return ("L",)
        return ("N", self.tree_struct(depth - 1),
                self.rng.randint(-2, 9), self.tree_struct(depth - 1))

    def ordered_struct(self, vals: list[int]):
        """A genuine (strict) search tree from strictly-increasing distinct `vals`,
        balanced so both children are exercised — the control the checker should PROVE."""
        if not vals:
            return ("L",)
        mid = len(vals) // 2
        return ("N", self.ordered_struct(vals[:mid]), vals[mid],
                self.ordered_struct(vals[mid + 1:]))

    @staticmethod
    def tree_lit(s) -> str:
        if s[0] == "L":
            return "Leaf"
        return f"Node({Gen.tree_lit(s[1])}, {s[2]}, {Gen.tree_lit(s[3])})"

    # The evaluators below are the measures' definitions, transcribed EXACTLY — the
    # sentinel `Leaf => 0` of `minv`/`maxv`, the two-deep nesting of `bst`.  They are the
    # independent witness; if one drifts from the emitted `.lark`, the oracle it feeds
    # cries wolf, which is why they are pinned to the same fixtures the checker is.

    @staticmethod
    def eval_rd(s, cl: int, cm: int, cd: int) -> int:
        if s[0] == "L":
            return cl
        if s[3][0] == "L":
            return cm
        return cd + Gen.eval_rd(s[3], cl, cm, cd)

    @staticmethod
    def eval_maxv(s) -> int:
        if s[0] == "L":
            return 0
        return s[2] if s[3][0] == "L" else Gen.eval_maxv(s[3])

    @staticmethod
    def eval_minv(s) -> int:
        if s[0] == "L":
            return 0
        return s[2] if s[1][0] == "L" else Gen.eval_minv(s[1])

    @staticmethod
    def eval_bst(s) -> bool:
        if s[0] == "L":
            return True
        _, l, v, r = s
        if l[0] == "L":
            return True if r[0] == "L" else (v < Gen.eval_minv(r) and Gen.eval_bst(r))
        if r[0] == "L":
            return Gen.eval_maxv(l) < v and Gen.eval_bst(l)
        return (Gen.eval_maxv(l) < v and v < Gen.eval_minv(r)
                and Gen.eval_bst(l) and Gen.eval_bst(r))

    # The SINGLE-MATCH search tree (36_bstdestruct), transcribed exactly: `lt`/`gt` are
    # the extra-parameter measures — every value below/above the bound — and `bst` is one
    # match on the root that hands them out.  Note this is the STRICT predicate (every
    # value, not just the spine extreme `minv`/`maxv` check above): a distinct evaluator,
    # feeding the same ORACLE 3, so a checker's demand-driven firing is witnessed against
    # an independent transcription of the exact measures it certifies.
    @staticmethod
    def eval_lt(s, b: int) -> bool:
        if s[0] == "L":
            return True
        _, l, x, r = s
        return x < b and Gen.eval_lt(l, b) and Gen.eval_lt(r, b)

    @staticmethod
    def eval_gt(s, b: int) -> bool:
        if s[0] == "L":
            return True
        _, l, x, r = s
        return x > b and Gen.eval_gt(l, b) and Gen.eval_gt(r, b)

    @staticmethod
    def eval_dbst(s) -> bool:
        if s[0] == "L":
            return True
        _, l, x, r = s
        return (Gen.eval_lt(l, x) and Gen.eval_gt(r, x)
                and Gen.eval_dbst(l) and Gen.eval_dbst(r))

    def nested_measure_decls(self) -> list[str]:
        """A NESTED-match Int measure with a DECLARED result, consumed as a DIVISOR — the
        `34_nestedmeasure` shape, generated to be believed or caught.

        `rd` is the length of the right spine: `rd(Leaf) == cl`, `rd(Node(_,_,Leaf)) ==
        cm`, `rd(Node(_,_,Node r…)) == cd + rd(r)`.  `cm >= 1` and `cd >= 0` are held so
        the ONLY lie source is the Leaf arm `cl`, exactly where the checker caught it in
        the probe.  The declared result is weighted toward the LIES — `{v >= 1}`/`{v >
        0}`/`{v != 0}` are false of an `rd` whose Leaf arm is 0, and a checker that
        believes the declaration installs its axiom, so `nuse` proves `100 / d` over an
        OPAQUE tree (`d == rd(t)`, `rd(t) >= 1`).  `main` then hands it a `Leaf` with the
        true `d == 0` and the machine divides by zero.  The CORRECT checker rejects the
        lie at the declaration (`arm 'Leaf' satisfies {v >= 1}` fails), so the program
        goes unproved and its crash is harmless — the sound direction, the nested twin of
        `measure_decls`' V2.3 hazard and the thing I6 watches.  An honest bound, or `Int`
        (whose `100 / d` is then unprovable), is the control group."""
        cl = self.rng.choice([1, 1, 2, 0, 0, -1])
        cm = self.rng.choice([1, 2, 2, 3])
        cd = self.rng.choice([0, 1, 1, 2])
        self.rd_params = (cl, cm, cd)
        ret = "Int"
        if self.refs:
            ret = self.rng.choice([
                "Int",
                "{v : Int | v >= 0}",
                "{v : Int | v >= 1}",
                "{v : Int | v >= 1}",
                "{v : Int | v > 0}",
                "{v : Int | v != 0}",
            ])
        return self._tree_type() + [
            f"measure rd(t : Tree) : {ret} =",
            "  match t with",
            f"  | Leaf => {cl}",
            "  | Node(l, v, r) =>",
            "      match r with",
            f"      | Leaf             => {cm}",
            f"      | Node(rl, rv, rr) => {cd} + rd(r)",
            "      end",
            "  end",
            "",
            "fn nuse(t : Tree, d : {v : Int | v == rd(t)}) : Int =",
            "  100 / d",
            "",
        ]

    def bst_decls(self) -> list[str]:
        """`minv`/`maxv`/`bst` — a match TWO deep, on both children, with a body that
        MENTIONS another measure (`bst` calls `maxv`/`minv` on a child).  The `35_bst`
        shape, and the checker's hardest construction path.

        It has NO divisor and so no RUN teeth: a `bst` is a fact about ORDER, and the
        DESTRUCTING direction that would read order back out of an opaque `bst(t)` is the
        open boundary (#3).  Its teeth here are the SEMANTIC oracle (see the loop in
        `main`): the generator computes `bst` of the concrete tree it builds, and a
        checker that PROVES `buse`'s `{v : Tree | bst(v)}` precondition of a tree the
        model calls DISORDERED is a false proof the run oracle could never see, because
        nothing crashes.  Generating it also runs the two-deep nesting and the
        cross-measure closure under random surrounding code, where a checker crash or an
        erasure drift would surface."""
        return self._tree_type() + [
            "measure maxv(t : Tree) : Int =",
            "  match t with",
            "  | Leaf => 0",
            "  | Node(l, v, r) =>",
            "      match r with",
            "      | Leaf             => v",
            "      | Node(rl, rv, rr) => maxv(r)",
            "      end",
            "  end",
            "",
            "measure minv(t : Tree) : Int =",
            "  match t with",
            "  | Leaf => 0",
            "  | Node(l, v, r) =>",
            "      match l with",
            "      | Leaf             => v",
            "      | Node(ll, lv, lr) => minv(l)",
            "      end",
            "  end",
            "",
            "measure bst(t : Tree) : Bool =",
            "  match t with",
            "  | Leaf => true",
            "  | Node(l, v, r) =>",
            "      match l with",
            "      | Leaf =>",
            "          match r with",
            "          | Leaf             => true",
            "          | Node(rl, rv, rr) => v < minv(r) and bst(r)",
            "          end",
            "      | Node(ll, lv, lr) =>",
            "          match r with",
            "          | Leaf             => maxv(l) < v and bst(l)",
            "          | Node(rl, rv, rr) => maxv(l) < v and v < minv(r) and bst(l) and bst(r)",
            "          end",
            "      end",
            "  end",
            "",
            "fn buse(t : {v : Tree | bst(v)}) : Int =",
            "  match t with",
            "  | Leaf          => 0",
            "  | Node(l, v, r) => v",
            "  end",
            "",
        ]

    def dbst_decls(self) -> list[str]:
        """The DESTRUCTING search tree (`36_bstdestruct`) — `bst` a SINGLE match on the
        root, `lt`/`gt` the EXTRA-PARAMETER measures it hands out.  Where `bst_decls`'
        nested match said nothing about an opaque tree, this one's unguarded equation fires
        on `Node(l, x, r)` at OPAQUE binders and yields `lt(l, x)`, `gt(r, x)`, `bst(l)`,
        `bst(r)` — the demand-driven extra-parameter firing this rung added.

        So `dconsume` reads order back OUT of the opaque `bst(t)` and puts it under a
        divisor: from `gt(r, x)` the checker must derive `rv > x` at the concrete right
        subfield, hence `rv - x >= 1`, to prove `100 / (rv - x)`.  This is RUN teeth on the
        destructing direction — the tooth `bst_decls` could not have, its `bst` having no
        divisor.  For a genuine search tree `rv > x` truly holds and nothing crashes; the
        crash comes only if the checker PROVES `dconsume`'s `bst(t)` precondition of a tree
        whose right grandchild is NOT above the root (`rv - x == 0`, a division by zero),
        which is a false destructing proof — and ORACLE 3, fed `eval_dbst`, catches every
        disordered tree proved besides."""
        return self._tree_type() + [
            "measure lt(t : Tree, b : Int) : Bool =",
            "  match t with",
            "  | Leaf          => true",
            "  | Node(l, x, r) => x < b and lt(l, b) and lt(r, b)",
            "  end",
            "",
            "measure gt(t : Tree, b : Int) : Bool =",
            "  match t with",
            "  | Leaf          => true",
            "  | Node(l, x, r) => x > b and gt(l, b) and gt(r, b)",
            "  end",
            "",
            "measure bst(t : Tree) : Bool =",
            "  match t with",
            "  | Leaf          => true",
            "  | Node(l, x, r) => lt(l, x) and gt(r, x) and bst(l) and bst(r)",
            "  end",
            "",
            "fn dconsume(t : {q : Tree | bst(q)}) : Int =",
            "  match t with",
            "  | Leaf          => 0",
            "  | Node(l, x, r) =>",
            "      match r with",
            "      | Leaf             => x",
            "      | Node(rl, rv, rr) => 100 / (rv - x)",
            "      end",
            "  end",
            "",
        ]

    def program(self, idx: int) -> str:
        rng = self.rng
        self.has_impl = rng.random() < 0.4
        self.has_measure = rng.random() < 0.4
        self.has_bool_measure = rng.random() < 0.35
        self.has_poly_measure = rng.random() < 0.30
        self.has_abs          = rng.random() < 0.35
        self.has_minpos       = rng.random() < 0.35
        self.has_floatbox     = rng.random() < 0.30
        self.has_nested       = rng.random() < 0.30
        self.has_bst          = rng.random() < 0.30
        # When a bst is emitted, half the time it is the DESTRUCTING single-match one
        # (36_bstdestruct) instead of the nested building-only one (35_bst).  The two share
        # `type Tree` and both define `measure bst`, so they are mutually exclusive — one
        # `bst` per program.
        self.bst_destruct     = self.has_bst and rng.random() < 0.5
        self.in_entry = False
        self.tree_declared = False    # `type Tree` is shared by bool/nested/bst measures
        self.bst_trees: list[bool] = []   # model verdict per tree passed to `buse`
        redeclare     = rng.random() < 0.2
        shadow        = rng.random() < 0.25

        out: list[str] = [f"module Fuzz{idx}", ""]

        if redeclare:
            # V2.2′(d): the program's own `string_length`, which the axiom is NOT about.
            out += [f"fn string_length(s : String) : Int = {rng.choice([-4, 0, 2])}", ""]

        if self.has_impl:
            out += [
                "type Coin =",
                "  | Penny",
                "  | Dime",
                "",
                "impl Copy for Coin = {}",
                "",
                "trait Weigh a = {",
                f"  fn weight : a -> {self.refined_int()}",
                "}",
                "",
                "impl Weigh for Coin = {",
                "  fn weight(c) =",
                "    match c with",
                f"    | Penny => {rng.randint(0, 3)}",
                f"    | Dime  => {rng.randint(0, 5)}",
                "    end",
                "}",
                "",
            ]

        if self.has_measure:
            out += self.measure_decls()

        if self.has_bool_measure:
            out += self.bool_measure_decls()

        if self.has_nested:
            out += self.nested_measure_decls()

        if self.has_bst:
            out += self.dbst_decls() if self.bst_destruct else self.bst_decls()

        if self.has_poly_measure:
            out += self.poly_measure_decls(declare_list=not self.has_measure)

        if self.has_abs:
            out += self.abs_decls()

        if self.has_minpos:
            out += self.minmax_contract_decls()

        if self.has_floatbox:
            # THE FLOAT INTERLUDE's road (prove/29).  A Float carried in a CONSTRUCTOR
            # FIELD — the fourth way a Float reaches the checker, and the one no fixture
            # drove before the interlude.  The `expr` branch below destructures an `FB`
            # and puts the Float FIELD into the `fld == fld` reflexivity trap (13's lie,
            # sourced from a constructor instead of a literal/param).  The field is unname-
            # able because a Float is, so the guard says nothing and the else's divisions
            # go unproved — unless the FLOAT-silence guard regresses, in which case the
            # else is dead code and its divisions are vacuously proved, then the machine
            # takes the else (the payload is a NaN factory) and divides by zero.
            out += [
                "type FB =",
                "  | FB of Float, Int",
                "",
            ]

        out += [
            f"fn help(a : {self.refined_int()}, b : {self.refined_int()}) : Int =",
            f"  {self.expr(['a', 'b'], 2)}",
            "",
        ]

        # `xs` is entry's alone: `size(xs)` may appear only where `xs` is in scope, and
        # `help` does not take a list.  The flag is what keeps the generator honest.
        self.in_entry = True
        body_env = ["x", "y"]
        pre = ""
        if shadow:
            # V2.2′(c): a local binding that captures a global function's NAME.
            pre = f"let help = fn(a, b) => {rng.randint(0, 3)} in\n  "
        xs_param = ", xs : List(Int)" if self.has_measure else ""
        xs_arg   = ""
        if self.has_measure:
            # THE ONLY ROAD TO V2.3'S HAZARD, and finding it took disarming the check to
            # see the adversary come back clean.  A measure is GHOST, so a divisor can
            # never mention one; it reaches the logic through `size`, whose contract says
            # `v == m1(xs)`.  And a contract reaches the logic through a NAME (V2.2″):
            # `x / size(xs)` is a bare call, and its postcondition is not a fact, so that
            # division is unprovable no matter what the measure declares — the checker's
            # known weak direction, and NOT the hazard.  `let m = size(xs) in x / m` is,
            # because now the fact is in the environment and the only thing between it
            # and a division by zero is the measure's declared result.  An adversary
            # aimed one syntactic step to the left tests nothing at all.
            body_env = body_env + ["m"]
            pre = pre + "let m = size(xs) in\n  "
            # Nil is the argument that bites: it is where a length is 0, and so where
            # `{v : Int | v > 0}` is a lie a checker can be caught believing.
            xs_arg = ", " + rng.choice(
                ["Nil", "Nil", "Cons(1, Nil)", "Cons(1, Cons(2, Nil))"])
        if self.has_bool_measure:
            # The V2.4 hazard, and it is a NAME too, for the reason the Int measure's is:
            # `100 / root(tree)` is a bare call whose `v > 0` postcondition is not a fact,
            # so it is unprovable in the sound direction and tests nothing.  `let rt =
            # root(tree) in … / rt` puts `rt > 0` in the environment, and the only thing
            # left holding that up is `pos(tree)` being decided honestly at the call — so
            # a tree with a zero root is a division by zero exactly when `pos` is believed.
            body_env = body_env + ["rt"]
            pre = pre + f"let rt = root({self.rand_tree(3)}) in\n  "
        if self.has_poly_measure:
            # The V2.4b hazard, a NAME for the same reason: `phead(list)` bare is
            # unprovable in the sound direction, so `let ph = phead(list) in … / ph` is
            # what puts `ph > 0` in scope — and the only thing holding it up is `allpos`
            # decided honestly at the call, which fails exactly for a zero-headed list.
            body_env = body_env + ["ph"]
            pre = pre + f"let ph = phead({self.rand_intlist(3)}) in\n  "
        if self.has_abs:
            # The V2.4c step 2 COVERAGE shape (see abs_decls for why it is coverage, not a
            # runtime catch).  `let ab = absish(k) in … / ab` reads the if-predicate at a
            # KNOWN argument: at `k = 5` the guard gives `ab == 5` and the division proves
            # and RUNS; at `k = 0` it gives `ab == 0` and stays UNPROVED, the sound
            # direction.  The argument is weighted to `0` so the sound-unproved path is
            # exercised as often as the proved-and-run one.
            body_env = body_env + ["ab"]
            arg = rng.choice(["0", "0", "x", "5", "0 - 3"])
            pre = pre + f"let ab = absish({arg}) in\n  "
        if self.has_minpos:
            # `min`/`max` in their INTENDED (contract) position: `let mp = minpos(p, q)`
            # puts `mp > 0` in scope ONLY if the axiom's disjunction proved `minpos`'s
            # result, and `… / mp` then hangs the program on that proof.  Positive
            # literals make it PROVE and RUN (the disjunction exercised); an unconstrained
            # `x`/`y` fails `minpos`'s `{v > 0}` precondition and goes UNPROVED — the sound
            # direction, the `25_minimum_unsafe` shape.
            body_env = body_env + ["mp"]
            a = rng.choice(["1", "2", "5", "x"])
            b = rng.choice(["3", "7", "1", "y"])
            pre = pre + f"let mp = minpos({a}, {b}) in\n  "
        body = self.expr(body_env, 3)
        if self.has_measure and rng.random() < 0.6:
            # Force the shape the rung is about rather than hoping for it: now the
            # program's fate hangs on the measure's declared result and nothing else.
            body = f"({body} / {rng.choice(['m', '(m + 1)', '(m - 1)'])})"
        if self.has_bool_measure and rng.random() < 0.7:
            # Same forcing, for the Bool measure: divide by the guarded root, so the
            # program's fate hangs on `pos` and nothing else.  `rt` is claimed `> 0`, so
            # this is proved — and runs — unless `pos` was believed of a zero-rooted tree.
            body = f"({body} / rt)"
        if self.has_poly_measure and rng.random() < 0.7:
            # Same forcing over the polymorphic list: divide by the guarded head, so the
            # program's fate hangs on `allpos` of a `List(Int)` whose `x` was pinned by
            # the field-sort fix — believed of a zero-headed list, this divides by zero.
            body = f"({body} / ph)"
        if self.has_abs and rng.random() < 0.7:
            # Force the if-predicate hazard: divide by the guarded result, so the
            # program's fate hangs on `absish`'s postcondition being read faithfully at
            # the call.  `ab` is `0` exactly when the argument is `0`, so a checker that
            # believes `ab != 0` there — a collapsed else or dropped guard — divides by
            # zero, and the run oracle catches it.
            body = f"({body} / ab)"
        if self.has_minpos and rng.random() < 0.7:
            # Force the contract hazard: divide by the guarded minimum, so the program's
            # fate hangs on `minpos`'s `{v > 0}` result — proved via the disjunction, then
            # run.  A dropped disjunction cannot prove it (sound: unproved); an honest one
            # proves it and the run confirms `min` of two positives is positive.
            body = f"({body} / mp)"
        if self.has_floatbox and rng.random() < 0.7:
            # Force the float-field hazard (prove/29_floatfield_unsafe's shape).  Wrap the
            # whole body in a match over an `FB` whose Float payload is a NaN factory, and
            # guard the body on the Float FIELD's `fld == fld`.  At run time the payload is
            # NaN, so `fld == fld` is FALSE and the ELSE — the real body, with all its
            # divisions — is the branch taken.  So the checker must prove those divisions
            # HONESTLY: it may not read `fld == fld`, and it must not let the failed self-
            # comparison make the else dead code.  Regress the FLOAT-silence guard and the
            # else is vacuously proved, the machine takes it, and a division inside detonates
            # — the run oracle catches it under an `ok` verdict.
            fld = self.fresh("fld")
            k   = self.fresh("k")
            nan = rng.choice(["0.0 / 0.0", "float_sqrt(0.0 - 1.0)"])
            body = (f"(match FB({nan}, {rng.randint(0, 9)}) with "
                    f"| FB({fld}, {k}) => if {fld} == {fld} then 0 else ({body}) end)")
        # `main` prints `entry`, then the tree consumers — each the fixture-34/35 way,
        # a concrete literal tree at the call whose measure the generator computed.
        prints = [
            f"show(entry({rng.randint(-3, 6)}, {rng.randint(-3, 6)}, "
            f"{rng.choice(STRINGS)}, {rng.choice(['1.5', '0.0', '0.0 / 0.0'])}{xs_arg}))"
        ]
        if self.has_nested:
            # A concrete tree, weighted to include the `Leaf` whose `rd` is `cl` — the
            # ZeroDivisionError seed when `cl == 0` and a lying declared result was
            # believed.  The depth passed is the TRUE `rd`, so the call's obligation `d ==
            # rd(tree)` fires at the concrete subfields and holds; the only thing left
            # holding up `100 / d` inside `nuse` is `rd`'s declared result being honest.
            cl, cm, cd = self.rd_params
            s = ("L",) if rng.random() < 0.5 else self.tree_struct(3)
            prints.append(f"show(nuse({self.tree_lit(s)}, {self.eval_rd(s, cl, cm, cd)}))")
        if self.has_bst:
            # Half genuine search trees (the checker should PROVE), half random (mostly
            # disordered, the checker should REJECT).  The model verdict is recorded; a
            # PROVED program certifying a disordered tree is the false proof the semantic
            # oracle in `main` catches — invisible to the run oracle when nothing crashes.
            if rng.random() < 0.5:
                k = rng.randint(0, 5)
                s = self.ordered_struct(sorted(rng.sample(range(-5, 12), k)))
            else:
                s = self.tree_struct(3)
            if self.bst_destruct:
                # The single-match consumer reads `gt(r, x)` out as a divisor `rv - x`, so
                # a random tree whose right grandchild equals the root (`rv == x`) both
                # fails the model (eval_dbst) AND divides by zero if wrongly proved — the
                # destructing direction's run teeth on top of ORACLE 3.
                self.bst_trees.append(Gen.eval_dbst(s))
                prints.append(f"show(dconsume({self.tree_lit(s)}))")
            else:
                self.bst_trees.append(Gen.eval_bst(s))
                prints.append(f"show(buse({self.tree_lit(s)}))")

        main_lines = ["fn main(io : IO) : IO ="]
        for pr in prints[:-1]:
            main_lines.append(f"  let io = print(io, {pr}) in")
        main_lines.append(f"  print(io, {prints[-1]})")

        out += [
            f"fn entry(x : Int, y : Int, s : String, f : Float{xs_param}) : Int =",
            f"  {pre}{body}",
            "",
            *main_lines,
            "",
        ]
        self.in_entry = False
        return "\n".join(out)


# -- the oracles ----------------------------------------------------------------

def run_cek(path: pathlib.Path) -> tuple[int, str, str]:
    r = subprocess.run(
        [sys.executable, str(SRC / "cek.py"), str(path)],
        capture_output=True, text=True, timeout=TIMEOUT,
        cwd=str(SRC), env={**os.environ, "PYTHONPATH": str(SRC)},
    )
    return r.returncode, r.stdout, r.stderr


def crashed(err: str) -> bool:
    return any(m in err for m in CRASH_MARKERS)


def main() -> int:
    cases = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed  = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    rng   = random.Random(seed)

    print(f"\n  adversary — {cases} random programs, seed {seed}")
    print("  the promise: if the checker says ok, the program does not crash.\n")

    proved = unproved = rejected = errored = weak = 0
    false_proofs: list[tuple[int, str, str]] = []
    erasure_bugs: list[tuple[int, str, str, str]] = []

    tmp = pathlib.Path(tempfile.mkdtemp(prefix="lark_adversary_"))

    for i in range(cases):
        g = Gen(rng)
        src = g.program(i)

        p = tmp / f"f{i}.lark"
        p.write_text(src)

        try:
            res = refine.check_program(str(p))
        except refine.FRONTEND_ERRORS:
            rejected += 1
            continue
        except refine.REFINE_ERRORS as e:
            errored += 1
            print(f"  refinement error  f{i}: {e}")
            continue
        except RecursionError:
            errored += 1
            continue
        except Exception:                       # a crash is never a verdict (V1′)
            print(f"\n  !! CHECKER CRASH on f{i}\n{src}\n{traceback.format_exc()}")
            false_proofs.append((i, src, "checker crashed"))
            continue

        try:
            code, out, err = run_cek(p)
        except subprocess.TimeoutExpired:
            continue

        if res.failed:
            unproved += 1
            if code == 0:
                weak += 1                        # ran fine but was not proved: sound
            continue

        proved += 1

        # ORACLE 1 — the promise.
        if code != 0 and crashed(err):
            false_proofs.append((i, src, err.strip().split("\n")[-1]))
            continue

        # ORACLE 3 — the model.  A `bst` has no divisor to detonate, so its false proof
        # is invisible to the run oracle; the generator computed the true predicate of
        # every tree it handed `buse`, and a PROVED program that certified a DISORDERED
        # tree as a search tree is a false proof with nothing to crash.
        if any(not ok for ok in g.bst_trees):
            false_proofs.append(
                (i, src, "false bst proof — the model says the tree is not a search tree"))
            continue

        # ORACLE 2 — erasure.  Strip the predicates; the output must not move.
        stripped = strip_refinements(src)
        q = tmp / f"f{i}_erased.lark"
        q.write_text(stripped)
        try:
            code2, out2, _ = run_cek(q)
        except subprocess.TimeoutExpired:
            continue
        if (code2, out2) != (code, out):
            erasure_bugs.append((i, src, out, out2))

    print(f"  {proved:5d} proved   {unproved:5d} unproved ({weak} of them ran fine — "
          f"the checker being too weak, which is allowed)")
    print(f"  {rejected:5d} rejected by the front end   {errored:5d} refinement errors\n")

    if erasure_bugs:
        for i, src, a, b in erasure_bugs[:3]:
            print(f"  !! ERASURE VIOLATION f{i}: refined printed {a!r}, erased {b!r}\n{src}")

    if false_proofs:
        print(f"  ❌ {len(false_proofs)} FALSE PROOF(S) — proved, then crashed:\n")
        for i, src, why in false_proofs[:5]:
            print(f"  --- f{i}: {why}")
            print("      " + "\n      ".join(src.strip().split("\n")))
            print()
        print(f"  reproduce with: python3 08/tests/adversary.py {cases} {seed}")
        return 1

    if erasure_bugs:
        return 1

    print("  adversary clean — every proved program ran, and erasure held.")
    return 0


REFINEMENT = re.compile(r"\{\s*\w+\s*:\s*([A-Za-z_][\w()]*)\s*\|[^{}\n]*\}")

def strip_refinements(src: str) -> str:
    """`{v : Int | p}` -> `Int`, textually.  The point of the twin is that the ONLY
    difference is the predicates: same names, same bodies, same arithmetic.

    The pattern is deliberately narrow — a binder, a base type, a bar, and a predicate
    with no braces and no newline in it.  An `impl … = { … }` block also has a `:` and a
    `|` in it, and a stripper that took those for refinements would report an erasure
    violation of its own making.  An oracle that cries wolf is worse than no oracle."""
    return REFINEMENT.sub(lambda m: m.group(1), src)


if __name__ == "__main__":
    sys.exit(main())
