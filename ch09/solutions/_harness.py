"""Shared helper for the Chapter 9 solutions — drives Lark's real back end
(lark/05/src: lower, cfg, liveness, regalloc, asm)."""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "05", "src"))

import lexer      # noqa: E402
import parser     # noqa: E402
import infer      # noqa: E402
import lower      # noqa: E402
import cfg        # noqa: E402
import liveness   # noqa: E402
import regalloc   # noqa: E402
import asm        # noqa: E402


def lower_src(src):
    prog = parser.Parser(lexer.Lexer(src).tokenize()).parse()
    return lower.Lowerer().lower(infer.typecheck(prog))


def alloc_with(fn, regs=None):
    """Allocate one Function; return (Allocation, intervals dict)."""
    g = cfg.build_cfg(fn)
    lv = liveness.analyse(g)
    bs = regalloc._linearize(g)
    ivs = regalloc._compute_intervals(g, lv, bs, list(fn.params))
    a = regalloc.allocate(g, lv, regs=regs, params=list(fn.params))
    return a, ivs


def asm_text(src):
    return asm.gen(lower_src(src))
