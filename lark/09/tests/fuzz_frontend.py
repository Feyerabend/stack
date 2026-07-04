"""
Frontend robustness fuzzing — Phase 9, Track C step 2.

Property P8: *no input ever produces a Python traceback.*  For any input
text, the frontend (lexer → parser → type checker, including the affine,
exhaustiveness, totality, Show-bound, and ambiguous-operator passes)
either returns a typed program or raises one of the language's positioned
diagnostic exceptions.  An AttributeError, KeyError, IndexError,
RecursionError, or any other Python exception escaping the frontend is a
robustness bug: a compiler's answer to a bad program is a diagnostic, not
a stack trace.

Three input distributions, each biased toward a different failure class:

  P8a  random text     — arbitrary unicode: exercises the lexer's edges
  P8b  token soup      — random sequences of *valid* tokens: gets past the
                         lexer and hammers the parser's error paths
  P8c  mutated programs — well-typed programs from gen_prog with small
                         text mutations: gets past the parser and hammers
                         the type checker's error paths

Run:
    python3 -m pytest tests/fuzz_frontend.py -v            (make proptest)
    LARK_FUZZ_EXAMPLES=2000 python3 -m pytest tests/fuzz_frontend.py
"""

from __future__ import annotations
import os
import sys
import pathlib
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT.parent / "src"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(ROOT))

from lexer import Lexer
import parser as _parser
import infer as _infer
from gen_prog import lark_programs

# The complete set of diagnostics the frontend is *allowed* to raise —
# the same tuple every CLI runner catches.  Everything else escaping is
# a bug.
DIAGNOSTICS = _infer.DIAGNOSTICS


def _frontend(src: str) -> None:
    """Run the full frontend; success and diagnostics both count as OK."""
    try:
        tokens = Lexer(src, "<fuzz>").tokenize()
        prog   = _parser.Parser(tokens, "<fuzz>").parse()
        _infer.typecheck(prog)
    except DIAGNOSTICS:
        pass   # a positioned diagnostic is the correct answer to bad input


_MAX = int(os.environ.get("LARK_FUZZ_EXAMPLES", "400"))

_SETTINGS = dict(
    max_examples=_MAX,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large,
                           HealthCheck.filter_too_much],
)


# ── P8a — arbitrary text ──────────────────────────────────────────────────────

@settings(**_SETTINGS)
@given(st.text(max_size=300))
def test_frontend_survives_random_text(src: str) -> None:
    _frontend(src)


# ── P8b — token soup ──────────────────────────────────────────────────────────

_TOKENS = [
    # keywords
    "module", "import", "exposing", "export", "fn", "let", "in", "if",
    "then", "else", "match", "with", "end", "type", "trait", "impl",
    "for", "of", "and", "or", "not", "true", "false", "total",
    # punctuation / operators
    "(", ")", ",", ":", "=", "=>", "->", "|", "_",
    "+", "-", "*", "/", "==", "!=", "<", "<=", ">", ">=",
    # names, types, literals
    "x", "y", "f", "io", "Main", "Int", "Bool", "String", "IO",
    "List", "Cons", "Nil", "Shape", "0", "1", "42", "3.14",
    '"s"', '""',
]

# A program-shaped prefix half the time, so more soup reaches decl parsing.
_PREFIX = st.sampled_from(["", "module M\n", "module M\nfn f(x : Int) : Int =\n"])


@st.composite
def _token_soup(draw) -> str:
    prefix = draw(_PREFIX)
    n      = draw(st.integers(0, 60))
    sep    = draw(st.sampled_from([" ", " ", " ", "\n"]))
    return prefix + sep.join(
        draw(st.sampled_from(_TOKENS)) for _ in range(n))


@settings(**_SETTINGS)
@given(_token_soup())
def test_frontend_survives_token_soup(src: str) -> None:
    _frontend(src)


# ── P8c — mutated well-typed programs ─────────────────────────────────────────

@st.composite
def _mutated_program(draw) -> str:
    src = draw(lark_programs())
    for _ in range(draw(st.integers(1, 3))):
        kind = draw(st.sampled_from(
            ["delete", "duplicate", "replace", "insert", "truncate"]))
        if not src:
            break
        i = draw(st.integers(0, max(0, len(src) - 1)))
        j = draw(st.integers(i, min(len(src), i + 30)))
        if kind == "delete":
            src = src[:i] + src[j:]
        elif kind == "duplicate":
            src = src[:j] + src[i:j] + src[j:]
        elif kind == "replace":
            src = src[:i] + draw(st.sampled_from(_TOKENS)) + src[j:]
        elif kind == "insert":
            src = src[:i] + draw(st.text(max_size=5)) + src[i:]
        elif kind == "truncate":
            src = src[:i]
    return src


@settings(**_SETTINGS)
@given(_mutated_program())
def test_frontend_survives_mutations(src: str) -> None:
    _frontend(src)


# ── P8d — pathological nesting and chains ─────────────────────────────────────

@st.composite
def _pathological(draw) -> str:
    kind  = draw(st.sampled_from(["parens", "unary", "chain", "pattern",
                                  "type", "lets", "tuple"]))
    n     = draw(st.integers(1, 3000))
    # Inputs that *exceed* the parser's node budget are cheap (one
    # diagnostic, no AST); inputs just *under* it parse into deep ASTs
    # that Algorithm W then walks with quadratic substitution cost — so
    # cap the legal-but-deep shapes at sizes that still crossed the old
    # default recursion limit (they crashed pre-fix), without turning the
    # property into a five-minute performance benchmark per example.
    chain_n = n % 500 + 1
    lets_n  = n % 150 + 1
    pat_n   = n % 400 + 1
    body  = {
        "parens":  "(" * n + "1" + ")" * n,
        "unary":   "- " * n + "1",
        "chain":   " + ".join(["1"] * (chain_n + 1)),
        "pattern": None,   # built below
        "type":    None,
        "lets":    None,
        "tuple":   "(" + ", ".join(["1"] * (n % 200 + 2)) + ")",
    }[kind]
    if kind == "pattern":
        pat = "Cons(" * pat_n + "x" + ", Nil)" * pat_n
        return (f"module M\nfn f(v : List(Int)) : Int =\n"
                f"  match v with | {pat} => 1 | _ => 0 end\n")
    if kind == "type":
        t = "(" * n + "Int" + ")" * n
        return f"module M\nfn f(x : {t}) : Int = 1\n"
    if kind == "lets":
        opens = "".join(f"let v{k} = {k} in " for k in range(lets_n))
        return f"module M\nfn f(x : Int) : Int =\n  {opens}x\n"
    return f"module M\nfn f(x : Int) : Int =\n  {body}\n"


# Deep-but-legal shapes cost seconds each in the checker (Algorithm W's
# substitution composition is quadratic in AST depth), so this property
# runs fewer examples than the cheap text/soup ones.
@settings(**{**_SETTINGS, "max_examples": min(_MAX, 30)})
@given(_pathological())
def test_frontend_survives_pathological_input(src: str) -> None:
    _frontend(src)


if __name__ == "__main__":
    import pytest as _pytest
    sys.exit(_pytest.main([__file__, "-q"]))
