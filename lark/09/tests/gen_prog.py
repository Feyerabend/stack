"""
Well-typed Lark program generator — Phase 9, Track C step 1.

Where gen.py checks local properties of the type checker against a handful
of fixed templates, this module generates whole random programs by
*inverting the typing rules* (Palka, Claessen, Russo & Hughes 2011,
"Testing an optimising compiler by generating random lambda terms"):
pick a goal type, pick a rule whose conclusion produces that type, recurse
into the rule's premises.  Every program is well typed by construction,
which yields two properties:

  P6  generator_soundness — every generated program passes the type
      checker (validates that the generator really inverts the rules,
      including the affine, exhaustiveness and Show-bound disciplines)
  P7  backend_agreement   — every generated program produces identical
      output on the CEK, TAC VM and RV32 VM backends (differential
      compiler fuzzing, reusing the diff_test oracle)

Scope (v1) — chosen so every generated program has *defined* semantics on
every backend:

  · expression types: Int, Bool, String, one user ADT (Shape), and pairs
    (in match destructuring)
  · Int arithmetic only (wrapping i32: division and remainder by zero are
    defined).  Float is excluded: the TAC VM computes in f64 while the
    CEK rounds through f32, so random float expressions diverge by
    design — closing that gap is future Track C work.
  · comparisons on Int only (the runtimes define ordering only there)
  · String: + (concat), show(Int), show(Bool), int_to_string,
    string_length, int_abs
  · affine discipline respected during generation: non-Copy values (IO;
    Shape when no Copy impl is generated) are consumed at most once per
    program, matching the checker's conservative cross-branch count
  · helpers are non-recursive (the call graph is a DAG), so every
    generated program terminates by construction

Besides the affine state, the generator threads a *groundedness* flag per
expression: an unannotated lambda parameter that the body never constrains
stays a generalized type variable, and the checker conservatively rejects
`show` on such a type ("no Show instance for α") — the Show-bound pass
runs on the generalized body, before call sites pin the type.  This very
generator discovered that rule the hard way (its first soundness
counterexample was `let f = (fn(a) => show(a)) in f(0)`), so it now
tracks which expressions may be non-ground and only passes ground ones
to show, grounding fragile arguments with an identity operation
(`x + 0`, `x or false`) whose builtin type forces unification.

Hypothesis drives the generation, so failing programs shrink to minimal
counterexamples automatically.

Run:
    python3 -m pytest tests/gen_prog.py -v                  (make proptest)
    make fuzz N=500        — longer differential fuzzing run
    python3 tests/gen_prog.py show 5     — print 5 sample programs
"""

from __future__ import annotations
import os
import sys
import pathlib
import tempfile
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT.parent / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT))

from lexer import Lexer
import parser as _parser
import infer as _infer
import diff_test as _diff


# ── Generation parameters ─────────────────────────────────────────────────────

BASE_TYPES  = ("Int", "Bool", "String")
PARAM_TYPES = ("Int", "Bool", "String", "Shape")

INT_EDGES = (0, 1, -1, 2147483647, -2147483648)

_STR_ALPHABET = "abcxyzXYZ019 _.,!"

SHAPE_DECL = "type Shape =\n  | Dot\n  | Line of Int\n  | Rect of Int, Int\n"
SHAPE_CTORS = ("Dot", "Line", "Rect")   # payload arities 0, 1, 2


def _render_int(n: int) -> str:
    """Render an i32 as a Lark expression.  Negative literals don't exist in
    the grammar (integer = digit+), so build them with subtraction; INT_MIN
    itself is not representable as -(2^31), so build it in two steps."""
    if n == -(2**31):
        return "((0 - 2147483647) - 1)"
    if n < 0:
        return f"(0 - {-n})"
    return str(n)


# An expression is a (source, fragile) pair.  fragile=True means the
# expression's type, as the checker sees it inside the enclosing function
# body, may still be an unconstrained (generalizable) type variable — such
# expressions must not reach `show` directly.  The tracking is conservative:
# marking a ground expression fragile only costs coverage, never soundness.
GenExpr = "tuple[str, bool]"


class _Gen:
    """One program generation session.

    Carries the Hypothesis draw function, a fresh-name counter, the set of
    already-consumed affine variables, and the helper-function signatures
    generated so far (so later bodies can call earlier helpers — a DAG).

    Contexts (ctx) map variable name -> (type_name, is_affine, is_fragile).
    A variable with is_affine=True may be referenced at most once in the
    whole program; that matches the checker's conservative rule, which
    counts uses across both branches of an if and across all match arms.
    is_fragile marks unannotated lambda parameters (and values derived
    only from them) whose checker-type may stay a type variable.
    """

    def __init__(self, draw) -> None:
        self.draw = draw
        self._n = 0
        self.used_affine: set[str] = set()
        self.helpers: list[tuple[str, tuple[str, ...], str]] = []
        self.shape_copy = False

    def fresh(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}{self._n}"

    def pick(self, weighted: list[tuple[int, str]]) -> str:
        bag: list[str] = []
        for w, name in weighted:
            bag.extend([name] * w)
        return self.draw(st.sampled_from(bag))

    def _affine(self, ty: str) -> bool:
        return ty == "Shape" and not self.shape_copy

    # ── Goal-directed expression generation ──────────────────────────────────
    # Each r_* method is one typing rule read backwards: given the goal type
    # in its conclusion, generate the premises.  Every rule returns
    # (source, fragile).

    def expr(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        rules: list[tuple[int, str]] = [(3, "lit")]
        if self._vars_of(goal, ctx):
            rules.append((4, "var"))
        if fuel > 0:
            rules += [(1, "if_"), (1, "let_"), (1, "match_bool"),
                      (1, "match_int"), (1, "match_tuple"),
                      (1, "match_shape"), (1, "letfn")]
            if any(ret == goal for _, _, ret in self.helpers):
                rules.append((2, "call"))
            if goal == "Int":
                rules += [(3, "arith"), (1, "neg"),
                          (1, "strlen"), (1, "int_abs")]
            elif goal == "Bool":
                rules += [(3, "cmp"), (2, "andor"), (1, "not_")]
            elif goal == "String":
                rules += [(2, "concat"), (2, "show_int"),
                          (1, "show_bool"), (1, "int_to_str")]
        return getattr(self, "r_" + self.pick(rules))(goal, ctx, fuel)

    def _vars_of(self, goal: str, ctx: dict) -> list[str]:
        return sorted(
            n for n, (t, affine, _) in ctx.items()
            if t == goal and not (affine and n in self.used_affine)
        )

    # — leaves —

    def r_lit(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        if goal == "Int":
            n = self.draw(st.one_of(
                st.integers(0, 20),
                st.sampled_from(INT_EDGES),
                st.integers(-(2**31), 2**31 - 1),
            ))
            return _render_int(n), False
        if goal == "Bool":
            return self.draw(st.sampled_from(["true", "false"])), False
        if goal == "String":
            s = self.draw(st.text(alphabet=_STR_ALPHABET, max_size=6))
            return f'"{s}"', False
        if goal == "Shape":
            if fuel <= 0:
                return "Dot", False
            ctor = self.draw(st.sampled_from(SHAPE_CTORS))
            if ctor == "Dot":
                return "Dot", False
            arity = 1 if ctor == "Line" else 2
            args = ", ".join(self.expr("Int", ctx, fuel - 1)[0]
                             for _ in range(arity))
            return f"{ctor}({args})", False
        raise AssertionError(f"no literal rule for {goal}")

    def r_var(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        name = self.draw(st.sampled_from(self._vars_of(goal, ctx)))
        _, affine, fragile = ctx[name]
        if affine:
            self.used_affine.add(name)
        return name, fragile

    # — generic compounds —

    def r_if_(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        c, _  = self.expr("Bool", ctx, fuel - 1)
        a, fa = self.expr(goal, ctx, fuel - 1)
        b, fb = self.expr(goal, ctx, fuel - 1)
        # The branches unify: one ground branch grounds the other.
        return f"(if {c} then {a} else {b})", fa and fb

    def r_let_(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        vty = self.draw(st.sampled_from(PARAM_TYPES))
        val, vf = self.expr(vty, ctx, fuel - 1)
        x   = self.fresh("v")
        annotate = self.draw(st.booleans())
        ann = f" : {vty}" if annotate else ""
        # An annotation unifies the value with a concrete type, so the
        # binding is ground; otherwise it inherits the value's fragility.
        bound_fragile = vf and not annotate
        body, bf = self.expr(
            goal, {**ctx, x: (vty, self._affine(vty), bound_fragile)},
            fuel - 1)
        return f"(let {x}{ann} = {val} in {body})", bf

    def r_match_bool(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        s, _  = self.expr("Bool", ctx, fuel - 1)
        a, fa = self.expr(goal, ctx, fuel - 1)
        b, fb = self.expr(goal, ctx, fuel - 1)
        return (f"(match {s} with | True => {a} | False => {b} end)",
                fa and fb)

    def r_match_int(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        s, _ = self.expr("Int", ctx, fuel - 1)
        lits = sorted(self.draw(st.sets(st.integers(0, 5),
                                        min_size=1, max_size=2)))
        arms: list[str] = []
        fragile = True
        for k in lits + ["_"]:
            e, f = self.expr(goal, ctx, fuel - 1)
            fragile = fragile and f
            arms.append(f"| {k} => {e}")
        return f"(match {s} with {' '.join(arms)} end)", fragile

    def r_match_tuple(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        t1 = self.draw(st.sampled_from(BASE_TYPES))
        t2 = self.draw(st.sampled_from(BASE_TYPES))
        e1, f1 = self.expr(t1, ctx, fuel - 1)
        e2, f2 = self.expr(t2, ctx, fuel - 1)
        x, y = self.fresh("m"), self.fresh("m")
        body, bf = self.expr(
            goal, {**ctx, x: (t1, False, f1), y: (t2, False, f2)},
            fuel - 1)
        return (f"(match ({e1}, {e2}) with | ({x}, {y}) => {body} end)", bf)

    def r_match_shape(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        s, _ = self.expr("Shape", ctx, fuel - 1)
        covered = sorted(self.draw(st.sets(st.sampled_from(SHAPE_CTORS),
                                           min_size=1)))
        arms: list[str] = []
        fragile = True
        for ctor in SHAPE_CTORS:
            if ctor not in covered:
                continue
            if ctor == "Dot":
                pat = "Dot"
                arm_ctx = ctx
            elif ctor == "Line":
                x = self.fresh("m")
                pat = f"Line({x})"
                arm_ctx = {**ctx, x: ("Int", False, False)}
            else:
                x, y = self.fresh("m"), self.fresh("m")
                pat = f"Rect({x}, {y})"
                arm_ctx = {**ctx, x: ("Int", False, False),
                           y: ("Int", False, False)}
            e, f = self.expr(goal, arm_ctx, fuel - 1)
            fragile = fragile and f
            arms.append(f"| {pat} => {e}")
        if len(covered) < len(SHAPE_CTORS):
            e, f = self.expr(goal, ctx, fuel - 1)
            fragile = fragile and f
            arms.append(f"| _ => {e}")
        return f"(match {s} with {' '.join(arms)} end)", fragile

    def r_letfn(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        f      = self.fresh("f")
        n_par  = self.draw(st.integers(1, 2))
        params = [(self.fresh("a"), self.draw(st.sampled_from(BASE_TYPES)))
                  for _ in range(n_par)]
        annotate = self.draw(st.booleans())
        # Unannotated parameters are the fragility source: inside the
        # lambda body their type is a fresh variable that only unification
        # against something concrete can ground.  Affine outer variables
        # are excluded: the checker rejects closures that capture them
        # (a closure may be called many times — Phase 9 hardening rule).
        lam_ctx = {n: e for n, e in ctx.items() if not e[1]}
        lam_ctx.update({p: (t, False, not annotate) for p, t in params})
        body, bf = self.expr(goal, lam_ctx, fuel - 1)
        sig  = ", ".join(f"{p} : {t}" if annotate else p for p, t in params)
        args = ", ".join(self.expr(t, ctx, fuel - 1)[0] for _, t in params)
        # The call instantiates f's generalized type; if the body's type was
        # ground the result is ground.  (Conservative: a body returning a
        # bare parameter is grounded by the argument, but we keep bf.)
        return f"(let {f} = (fn({sig}) => {body}) in {f}({args}))", bf

    def r_call(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        name, ptys, _ = self.draw(st.sampled_from(
            [h for h in self.helpers if h[2] == goal]))
        args = ", ".join(self.expr(t, ctx, fuel - 1)[0] for t in ptys)
        return f"{name}({args})", False   # helper signatures are annotated

    # — Int rules —

    def r_arith(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        op = self.draw(st.sampled_from(["+", "-", "*", "/"]))
        l, fl = self.expr("Int", ctx, fuel - 1)
        # Division edges (x/0 = -1, INT_MIN/-1 wraps) are where backends are
        # most likely to disagree, but a random subtree almost never evaluates
        # to exactly 0 or -1 — so for '/' force an edge divisor half the time.
        if op == "/" and self.draw(st.booleans()):
            r, fr = _render_int(self.draw(st.sampled_from([0, 1, -1]))), False
        else:
            r, fr = self.expr("Int", ctx, fuel - 1)
        # Operators dispatch on their operand type, and the checker rejects
        # an operator whose operand type stays a type variable (the
        # ambiguous-operator restriction) — so ground one side if needed.
        l = self._ground_int(l, fl and fr)
        return f"({l} {op} {r})", False

    def r_neg(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, f = self.expr("Int", ctx, fuel - 1)
        return f"(- {self._ground_int(e, f)})", False

    def r_strlen(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, _ = self.expr("String", ctx, fuel - 1)
        return f"string_length({e})", False   # builtin: String -> Int

    def r_int_abs(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, _ = self.expr("Int", ctx, fuel - 1)
        return f"int_abs({e})", False          # builtin: Int -> Int

    # — Bool rules —

    def r_cmp(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        op = self.draw(st.sampled_from(["==", "!=", "<", "<=", ">", ">="]))
        l, fl = self.expr("Int", ctx, fuel - 1)
        r, fr = self.expr("Int", ctx, fuel - 1)
        l = self._ground_int(l, fl and fr)   # ambiguous-operator restriction
        return f"({l} {op} {r})", False      # a -> a -> Bool: result ground

    def r_andor(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        op = self.draw(st.sampled_from(["and", "or"]))
        l, _ = self.expr("Bool", ctx, fuel - 1)
        r, _ = self.expr("Bool", ctx, fuel - 1)
        return f"({l} {op} {r})", False        # Bool -> Bool -> Bool

    def r_not_(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, _ = self.expr("Bool", ctx, fuel - 1)
        return f"(not {e})", False             # not : Bool -> Bool

    # — String rules —

    def r_concat(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        l, fl = self.expr("String", ctx, fuel - 1)
        r, fr = self.expr("String", ctx, fuel - 1)
        if fl and fr:   # ambiguous-operator restriction: ground one side
            l = f'({l} + "")'
        return f"({l} + {r})", False

    def _ground_int(self, e: str, fragile: bool) -> str:
        """Force an Int expression's type to unify with Int, identity-wise."""
        return f"({e} + 0)" if fragile else e

    def _ground_bool(self, e: str, fragile: bool) -> str:
        """Force a Bool expression's type to unify with Bool, identity-wise."""
        return f"({e} or false)" if fragile else e

    def r_show_int(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, f = self.expr("Int", ctx, fuel - 1)
        return f"show({self._ground_int(e, f)})", False

    def r_show_bool(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, f = self.expr("Bool", ctx, fuel - 1)
        return f"show({self._ground_bool(e, f)})", False

    def r_int_to_str(self, goal: str, ctx: dict, fuel: int) -> tuple[str, bool]:
        e, _ = self.expr("Int", ctx, fuel - 1)
        return f"int_to_string({e})", False    # builtin: Int -> String

    # ── Declarations ─────────────────────────────────────────────────────────

    def global_decl(self, globals_ctx: dict) -> str:
        """A top-level constant.  Kept literal-only: globals are initialised
        by __global_init__ in the TAC/RV32 backends before main runs, and a
        literal never depends on evaluation order."""
        name = self.fresh("g")
        ty   = self.draw(st.sampled_from(BASE_TYPES))
        val, _ = self.expr(ty, {}, 0)
        globals_ctx[name] = (ty, False, False)
        return f"let {name} : {ty} = {val}\n"

    def helper_decl(self, globals_ctx: dict) -> str:
        """A pure top-level function over Copy/Shape values.  Its body may
        call previously generated helpers only, so no recursion arises."""
        name   = self.fresh("h")
        n_par  = self.draw(st.integers(1, 3))
        params = [(self.fresh("p"), self.draw(st.sampled_from(PARAM_TYPES)))
                  for _ in range(n_par)]
        ret = self.draw(st.sampled_from(PARAM_TYPES))
        ctx = dict(globals_ctx)
        for p, t in params:
            ctx[p] = (t, self._affine(t), False)
        body, _ = self.expr(ret, ctx, self.draw(st.integers(1, 4)))
        self.helpers.append((name, tuple(t for _, t in params), ret))
        sig = ", ".join(f"{p} : {t}" for p, t in params)
        return f"fn {name}({sig}) : {ret} =\n  {body}\n"

    def io_helper_decl(self, globals_ctx: dict) -> tuple[str, str, str]:
        """An IO-threading function: takes the IO token and one value, prints
        something derived from it, returns the new token.  Exercises the
        affine discipline across a function boundary."""
        name = self.fresh("ph")
        x    = self.fresh("p")
        ty   = self.draw(st.sampled_from(BASE_TYPES))
        ctx  = dict(globals_ctx)
        ctx[x] = (ty, False, False)
        s, _ = self.expr("String", ctx, self.draw(st.integers(1, 3)))
        decl = (f"fn {name}(io : IO, {x} : {ty}) : IO =\n"
                f"  print(io, {s})\n")
        return decl, name, ty

    def program(self) -> str:
        parts: list[str] = ["module Fuzz\n", SHAPE_DECL]

        self.shape_copy = self.draw(st.booleans())
        if self.shape_copy:
            parts.append("impl Copy for Shape = {}\n")

        globals_ctx: dict = {}
        for _ in range(self.draw(st.integers(0, 2))):
            parts.append(self.global_decl(globals_ctx))
        for _ in range(self.draw(st.integers(0, 2))):
            parts.append(self.helper_decl(globals_ctx))

        io_helpers: list[tuple[str, str]] = []
        if self.draw(st.booleans()):
            decl, name, ty = self.io_helper_decl(globals_ctx)
            parts.append(decl)
            io_helpers.append((name, ty))

        stmts: list[str] = []
        for _ in range(self.draw(st.integers(1, 4))):
            fuel = self.draw(st.integers(1, 5))
            if io_helpers and self.draw(st.booleans()):
                name, ty = self.draw(st.sampled_from(io_helpers))
                arg, _ = self.expr(ty, globals_ctx, fuel)
                stmts.append(f"{name}(io, {arg})")
            else:
                s, _ = self.expr("String", globals_ctx, fuel)
                stmts.append(f"print(io, {s})")

        main_lines = ["fn main(io : IO) : IO ="]
        for stmt in stmts[:-1]:
            main_lines.append(f"  let io = {stmt} in")
        main_lines.append(f"  {stmts[-1]}")
        parts.append("\n".join(main_lines) + "\n")

        return "\n".join(parts)


@st.composite
def lark_programs(draw) -> str:
    """A closed, well-typed, terminating Lark program with observable output."""
    return _Gen(draw).program()


# ── Oracles ───────────────────────────────────────────────────────────────────

def _tc(src: str):
    tokens = Lexer(src, "<gen_prog>").tokenize()
    prog   = _parser.Parser(tokens, "<gen_prog>").parse()
    return _infer.typecheck(prog)


def _run_backends(src: str) -> dict[str, tuple[int, str, str]]:
    with tempfile.TemporaryDirectory() as d:
        path = pathlib.Path(d) / "fuzz.lark"
        path.write_text(src)
        return {name: _diff.run(path, runner)
                for name, runner in _diff.BACKENDS}


def _fmt_failure(src: str, results: dict[str, tuple[int, str, str]]) -> str:
    lines = ["generated program:", src, "backend results:"]
    for name, (code, out, err) in results.items():
        lines.append(f"── {name} (exit {code}) ──")
        lines.append(out if code == 0 else (err or out))
    return "\n".join(lines)


# ── P6 — every generated program is well typed ────────────────────────────────

@settings(max_examples=int(os.environ.get("LARK_GEN_EXAMPLES", "300")),
          deadline=None,
          suppress_health_check=[HealthCheck.too_slow,
                                 HealthCheck.data_too_large])
@given(lark_programs())
def test_generated_programs_typecheck(src: str) -> None:
    """Generator soundness: the generator inverts the typing rules, so its
    output must always pass the checker — including the affine,
    exhaustiveness and Show-bound passes."""
    _tc(src)   # must not raise


# ── P7 — all backends agree on every generated program ────────────────────────

@settings(max_examples=int(os.environ.get("LARK_FUZZ_EXAMPLES", "25")),
          deadline=None,
          suppress_health_check=[HealthCheck.too_slow,
                                 HealthCheck.data_too_large])
@given(lark_programs())
def test_backends_agree_on_generated(src: str) -> None:
    """Differential fuzzing: CEK, TAC VM and RV32 VM must all run every
    generated program successfully and produce byte-identical output."""
    results = _run_backends(src)
    codes = {name: code for name, (code, _, _) in results.items()}
    assert all(c == 0 for c in codes.values()), \
        f"backend crash {codes}\n{_fmt_failure(src, results)}"
    outs = {out for _, out, _ in results.values()}
    assert len(outs) == 1, f"backends diverge\n{_fmt_failure(src, results)}"


# ── CLI: eyeball sample programs / ad-hoc fuzzing ─────────────────────────────

def _sample(n: int) -> list[str]:
    import warnings
    from hypothesis.errors import NonInteractiveExampleWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", NonInteractiveExampleWarning)
        return [lark_programs().example() for _ in range(n)]


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "show"
    n    = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    if mode == "show":
        for i, src in enumerate(_sample(n)):
            print(f"── sample {i + 1} " + "─" * 50)
            print(src)
    elif mode == "fuzz":
        bad = 0
        for i, src in enumerate(_sample(n)):
            results = _run_backends(src)
            outs  = {out for _, out, _ in results.values()}
            codes = {c for c, _, _ in results.values()}
            if codes != {0} or len(outs) != 1:
                bad += 1
                print(_fmt_failure(src, results))
            else:
                print(f"  ok  sample {i + 1}")
        print(f"\n  {n - bad} ok, {bad} divergences")
        sys.exit(0 if bad == 0 else 1)
    else:
        print("usage: gen_prog.py [show|fuzz] [n]", file=sys.stderr)
        sys.exit(1)
