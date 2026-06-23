"""
Shared CEK-driving helpers for the Chapter 6 solutions.

Drives the real Lark interpreter, lark/04/src/cek.py (the pure-interpreter
phase), so the traces and measurements come from the actual machine the chapter
describes.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
sys.path.insert(0, os.path.join(_LANG, "lark", "04", "src"))

import lexer    # noqa: E402
import parser   # noqa: E402
import infer    # noqa: E402
import cek      # noqa: E402


def setup(src):
    """Parse, type-check, and evaluate top-level decls; return (env, machine)."""
    prog = parser.Parser(lexer.Lexer(src).tokenize()).parse()
    tprog = infer.typecheck(prog)
    m = cek.Machine()
    env = cek.eval_program(prog, tprog, None, m)
    return env, m


def run_states(env, m, fn="main", arg=None):
    """Step the CEK machine from `fn` applied to `arg` (VIO by default),
    returning (list_of_states, final_value). Each state is an Eval or Return."""
    a = cek.VIO() if arg is None else arg
    state = cek.apply(env[fn], a, [], m)
    states = []
    while not (isinstance(state, cek.Return) and not state.kont):
        states.append(state)
        state = cek.step(state, m)
    states.append(state)
    return states, state.val


def snapshot(state):
    """(kind, payload, [frame names], kont_len) for one state."""
    konts = [type(f).__name__ for f in state.kont]
    if isinstance(state, cek.Eval):
        payload = type(state.expr).__name__
    else:
        payload = repr(state.val)
    return (type(state).__name__, payload, konts, len(state.kont))


def max_kont_depth(states):
    return max(len(s.kont) for s in states)
