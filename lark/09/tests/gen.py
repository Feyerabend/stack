"""Property-based tests for Lark's type checker — Phase 6, Step 6.3;
extended in Phase 8 with exhaustiveness and defined-Int properties.

Run with:
    cd lark/08 && python3 -m pytest tests/gen.py -v
    cd lark/08 && python3 -m pytest tests/gen.py -v --hypothesis-show-statistics

Properties:
  P1  affine_soundness    — any IO param used ≥ 2 times raises AffineError
  P2  copy_transparency   — Copy-typed params used N times are always accepted
  P3  double_typecheck    — typecheck is pure; same input gives the same TProgram
  P4  exhaustiveness_iff  — a match on a random constructor subset is accepted
                            iff the subset is complete or a wildcard arm exists
  P5  int_backend_agree   — CEK and TAC VM integer arithmetic agree on random
                            i32 pairs, including div/0 and INT_MIN edges
"""

from __future__ import annotations
import sys
import pathlib
import pytest
from hypothesis import given, settings, example
from hypothesis import strategies as st

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT.parent / "src"
sys.path.insert(0, str(SRC))

from lexer import Lexer
import parser as _parser
import infer as _infer


def _tc(src: str):
    """Parse and typecheck a Lark source string (no imports)."""
    tokens = Lexer(src, "<gen>").tokenize()
    prog   = _parser.Parser(tokens, "<gen>").parse()
    return _infer.typecheck(prog)


# ── Strategies ────────────────────────────────────────────────────────────────

_VARS = st.sampled_from(["x", "y", "v", "w", "a", "b"])
_FNS  = st.sampled_from(["f", "g", "h", "test_fn"])
_COPY = st.sampled_from(["Int", "Bool", "Float", "String"])


@st.composite
def _affine_dup_src(draw) -> str:
    """Generate a program where an IO param is used exactly twice.

    Varies the variable name, function name, duplication pattern, and an
    optional irrelevant let-wrapper.  Every generated program must be rejected
    with AffineError.
    """
    var = draw(_VARS)
    fn  = draw(_FNS)

    # Each tuple: (body_expr, return_type_annotation).
    # The return type must match the body so that unification succeeds before
    # (or simultaneously with) the affine check firing.
    # The last two duplicate the resource through a *closure capture* rather
    # than a second occurrence of the name — the Phase 9 hardening hole:
    # a closure is Copy, so even one capture is a potential duplication.
    body, ret_ty = draw(st.sampled_from([
        (f"({var}, {var})",                              "(IO, IO)"),
        (f"let t = {var} in ({var}, t)",                 "(IO, IO)"),
        (f"let t = {var} in (t, {var})",                 "(IO, IO)"),
        (f"if True then {var} else {var}",               "IO"),
        (f"let t = {var} in let u = {var} in (t, u)",    "(IO, IO)"),
        (f"let g = fn(q : Int) => {var} in (g(1), g(2))", "(IO, IO)"),
        (f"let g = fn(q : Int) => {var} in g(0)",        "IO"),
    ]))

    # Optionally wrap in an irrelevant Int let-binding.  This exercises the
    # LetExpr code path without consuming `var`, so AffineError must still
    # fire inside the inner body.
    if draw(st.booleans()):
        lit  = draw(st.integers(min_value=0, max_value=100))
        body = f"let n = {lit} in {body}"

    return f"module Gen\nfn {fn}({var} : IO) : {ret_ty} =\n  {body}\n"


@st.composite
def _copy_multi_src(draw) -> str:
    """Generate a program where a Copy-typed param is used N >= 2 times.
    The type checker must accept every generated program.
    """
    var    = draw(_VARS)
    fn     = draw(_FNS)
    ty     = draw(_COPY)
    n_uses = draw(st.integers(min_value=2, max_value=4))

    if ty == "Bool":
        op   = draw(st.sampled_from(["and", "or"]))
        body = f" {op} ".join([var] * n_uses)
        ret  = "Bool"
    else:
        # Int, Float, String all use + (string concat / numeric add)
        body = " + ".join([var] * n_uses)
        ret  = ty

    return f"module Gen\nfn {fn}({var} : {ty}) : {ret} =\n  {body}\n"


# ── P1 — Affine soundness ─────────────────────────────────────────────────────

@settings(max_examples=300)
@example("module Gen\nfn f(x : IO) : (IO, IO) =\n  (x, x)\n")
@example("module Gen\nfn f(x : IO) : IO =\n  if True then x else x\n")
@example("module Gen\nfn f(x : IO) : (IO, IO) =\n  let t = x in (x, t)\n")
@example("module Gen\nfn f(x : IO) : (IO, IO) =\n  let n = 42 in (x, x)\n")
@example("module Gen\nfn f(x : IO) : (IO, IO) =\n"
         "  let g = fn(q : Int) => x in (g(1), g(2))\n")
@given(_affine_dup_src())
def test_affine_soundness(src: str) -> None:
    """Duplicating an IO-typed parameter — whether by a second occurrence
    of the name or by capturing it in a closure — raises AffineError."""
    with pytest.raises(_infer.AffineError):
        _tc(src)


# ── P2 — Copy transparency ────────────────────────────────────────────────────

@settings(max_examples=300)
@example("module Gen\nfn f(x : Int) : Int =\n  x + x\n")
@example("module Gen\nfn f(x : Int) : Int =\n  x + x + x\n")
@example("module Gen\nfn f(x : Bool) : Bool =\n  x and x\n")
@example("module Gen\nfn f(x : Bool) : Bool =\n  x or x or x\n")
@example("module Gen\nfn f(x : String) : String =\n  x + x\n")
@example("module Gen\nfn f(x : Float) : Float =\n  x + x + x\n")
@given(_copy_multi_src())
def test_copy_transparency(src: str) -> None:
    """Using a Copy-typed parameter any number of times is always accepted."""
    _tc(src)  # must not raise


# ── P3 — Double typecheck (idempotence / no global state) ─────────────────────

_CORPUS_FILES = sorted(ROOT.glob("[0-9]*.lark")) + [
    ROOT / "09_modules" / "main.lark",
]


@pytest.mark.parametrize("path", _CORPUS_FILES, ids=lambda p: p.stem)
def test_double_typecheck(path: pathlib.Path) -> None:
    """Calling typecheck twice on the same parsed program yields equal results.

    Catches any global mutable state that would make the checker non-idempotent.
    Error test files are excluded: they raise before returning a TProgram.
    """
    src    = path.read_text()
    tokens = Lexer(src, str(path)).tokenize()
    prog   = _parser.Parser(tokens, str(path)).parse()

    tp1 = _infer.typecheck(prog, source_file=str(path))
    tp2 = _infer.typecheck(prog, source_file=str(path))

    assert tp1 == tp2


# ── P4 — Exhaustiveness iff coverage (Phase 8) ────────────────────────────────

_CTORS = ["Red", "Green", "Blue"]


@st.composite
def _match_subset_src(draw) -> tuple[str, bool]:
    """Generate a match over a random non-empty subset of a 3-constructor ADT,
    optionally closed by a wildcard arm.  Returns (source, must_accept):
    the checker must accept iff the subset is complete or a wildcard exists.
    """
    subset   = draw(st.sets(st.sampled_from(_CTORS), min_size=1))
    wildcard = draw(st.booleans())
    # Keep declaration order for the arms so witnesses are deterministic.
    arms = [f"  | {c}   => \"{c.lower()}\"" for c in _CTORS if c in subset]
    if wildcard:
        arms.append("  | _     => \"other\"")
    src = (
        "module Gen\n"
        "type Color = | Red | Green | Blue\n"
        "fn name(c : Color) : String =\n"
        "  match c with\n" + "\n".join(arms) + "\n  end\n"
    )
    return src, (subset == set(_CTORS)) or wildcard


@settings(max_examples=200)
@given(_match_subset_src())
def test_exhaustiveness_iff(case: tuple[str, bool]) -> None:
    """The checker accepts exactly the covering matches: no false rejections
    (completeness) and no false acceptances (soundness)."""
    src, must_accept = case
    if must_accept:
        _tc(src)  # must not raise
    else:
        from exhaust import ExhaustivenessError
        with pytest.raises(ExhaustivenessError):
            _tc(src)


# ── P5 — Integer backends agree (Phase 8) ─────────────────────────────────────

_I32 = st.integers(min_value=-2**31, max_value=2**31 - 1)
_EDGE = st.sampled_from([0, 1, -1, 2**31 - 1, -2**31])


@settings(max_examples=500)
@given(
    st.one_of(_I32, _EDGE),
    st.one_of(_I32, _EDGE),
    st.sampled_from(["+", "-", "*", "/", "%"]),
)
def test_int_backend_agree(a: int, b: int, op: str) -> None:
    """CEK and TAC VM implement the same wrapping-i32 arithmetic, including
    division by zero (RISC-V: x/0 = -1, x%0 = x) and INT_MIN edges — and
    every result is itself a representable i32."""
    import cek as _cek
    import tac_vm as _tac

    cek_res = _cek.binop(op, _cek.VInt(a), _cek.VInt(b))
    tac_res = _tac._binop(op, a, b)

    assert isinstance(cek_res, _cek.VInt)
    assert cek_res.n == tac_res
    assert -2**31 <= cek_res.n <= 2**31 - 1
