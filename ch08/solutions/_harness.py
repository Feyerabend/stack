"""Shared helper for the Chapter 8 solutions — drives Lark's real lowerer
(lark/06/src, the hardening-phase snapshot for this chapter)."""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "06", "src"))

import lexer    # noqa: E402
import parser   # noqa: E402
import infer    # noqa: E402
import tac      # noqa: E402
import lower    # noqa: E402
import cfg      # noqa: E402


def lower_src(src):
    prog = parser.Parser(lexer.Lexer(src).tokenize()).parse()
    return lower.Lowerer().lower(infer.typecheck(prog))
