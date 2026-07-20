#!/usr/bin/env python3
"""
opt_licm_test — exercise the LICM pass on a SYNTHETIC loop.

The Lark TAC IR is acyclic (iteration is inter-procedural recursion, not a CFG
back-edge), so no corpus program exercises `opt.licm`. This test hand-builds a
TAC function with a real back-edge and asserts:

  1. A loop-invariant, pure, header instruction is hoisted into the preheader.
  2. A loop-VARIANT instruction (operand defined in the loop) is NOT hoisted.
  3. On an acyclic function, licm is the identity (the corpus case).

Run: python3 tests/opt_licm_test.py
"""
import sys, os, pathlib

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from tac import (
    TAC, Function, Tmp, Const,
    IAssign, IBinOp, IReturn, ILabel, IJump, ICondJump,
)
from opt import licm


def _build_loop() -> Function:
    """
    A loop with a preheader, computing an invariant `inv = a + b` in the header
    and a variant `i2 = i + inv` (i is loop-carried):

        entry:                     # preheader
            a = 1
            b = 2
            i = 0
            goto head
        head:
            inv = a + b            # INVARIANT (a, b defined in preheader)
            i2  = i + inv          # VARIANT   (i is loop-carried)
            c   = i2 < 10
            if c goto body else done
        body:
            i = i2                 # loop-carried update; back-edge target head
            goto head
        done:
            return i2
    """
    fn = Function("loopy", ())
    fn.body = [
        ILabel(".entry"),
        IAssign(Tmp("a"), Const(1)),
        IAssign(Tmp("b"), Const(2)),
        IAssign(Tmp("i"), Const(0)),
        IJump(".head"),
        ILabel(".head"),
        IBinOp(Tmp("inv"), "+", Tmp("a"), Tmp("b")),   # invariant
        IBinOp(Tmp("i2"), "+", Tmp("i"), Tmp("inv")),  # variant
        IBinOp(Tmp("c"), "<", Tmp("i2"), Const(10)),
        ICondJump(Tmp("c"), ".body", ".done"),
        ILabel(".body"),
        IAssign(Tmp("i"), Tmp("i2")),
        IJump(".head"),
        ILabel(".done"),
        IReturn(Tmp("i2")),
    ]
    return fn


def _names(body, cls, op=None):
    return [i for i in body if isinstance(i, cls) and (op is None or i.op == op)]


def test_hoist():
    fn = _build_loop()
    tac = TAC(functions=[fn])
    licm(tac)
    body = fn.body

    # The invariant `inv = a + b` must now sit in the preheader (before the
    # goto .head), and NOT inside the .head block.
    idx = {id(i): k for k, i in enumerate(body)}
    head_i = next(k for k, i in enumerate(body) if isinstance(i, ILabel) and i.name == ".head")
    entry_goto = next(k for k, i in enumerate(body)
                      if isinstance(i, IJump) and i.label == ".head" and k < head_i)

    invs = [k for k, i in enumerate(body)
            if isinstance(i, IBinOp) and i.op == "+"
            and isinstance(i.l, Tmp) and i.l.name == "a"]
    assert len(invs) == 1, "invariant should still be computed exactly once"
    assert invs[0] < entry_goto, "invariant `a+b` was NOT hoisted into the preheader"

    # The variant `i2 = i + inv` must remain in the loop (after .head).
    variants = [k for k, i in enumerate(body)
                if isinstance(i, IBinOp) and i.op == "+"
                and isinstance(i.l, Tmp) and i.l.name == "i"]
    assert len(variants) == 1 and variants[0] > head_i, \
        "variant `i + inv` must NOT be hoisted"
    print("ok: invariant hoisted, variant kept")


def test_acyclic_identity():
    fn = Function("straight", ("x",))
    fn.body = [
        IBinOp(Tmp("t0"), "+", Tmp("x"), Const(1)),
        IReturn(Tmp("t0")),
    ]
    before = list(fn.body)
    licm(TAC(functions=[fn]))
    assert fn.body == before, "licm must be the identity on an acyclic function"
    print("ok: acyclic function unchanged (the corpus case)")


if __name__ == "__main__":
    test_hoist()
    test_acyclic_identity()
    print("all licm tests passed")
