"""
Chapter 10, Exercise 3 — solution code.

The ApplyFnF frame IS the evaluation context [·] e2. (a) write the small-step SOS
derivation of (f x) + 1 far enough to see the context [·] x. (b) trace the CEK
machine and identify the frame that reifies that context. (c) say in one sentence
what "the machine and the semantics are the same definition" means.

How to run:   python3 ex03_apply_context.py
Expected:     "ApplyFnF([x]) appears in kont — it reifies [·] x; result 4"

(a) SOS DERIVATION (call-by-value, → is one small step). To reduce (f x) + 1 we
    must first reduce the left operand of +, i.e. work inside the context
    [·] + 1. To reduce (f x), with f already a value, we evaluate the function
    position under the context [·] x until it is a value, then the argument:
        (f x) + 1
          → reduce  f x       in context  [·] + 1
              f is a value; to apply we are in context  [·] x  (the APP-fn rule:
              evaluate the operator with the operand pending)
              x → 3           (variable lookup)
              (f 3) → 3       (beta, since f = λy.y)
          → 3 + 1
          → 4
    The context [·] x is the "hole where the function goes, with argument x still
    to be applied" — precisely an evaluation context.

(b)/(c) below: the CEK trace shows ApplyFnF([x], env) on the kont while the
    function position is evaluated; that frame is the reified [·] x. "Same
    definition": the CEK transition relation and the small-step SOS define the
    very same reduction sequence — the frames ARE the evaluation contexts,
    represented as data instead of as syntax-with-a-hole.
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

SRC = ("module M\n"
       "fn t(io : IO) : Int = let f = fn (y) => y in let x = 3 in f(x) + 1")


def run_states(src):
    prog = parser.Parser(lexer.Lexer(src).tokenize()).parse()
    tprog = infer.typecheck(prog)
    m = cek.Machine()
    env = cek.eval_program(prog, tprog, None, m)
    state = cek.apply(env["t"], cek.VIO(), [], m)
    states = []
    while not (isinstance(state, cek.Return) and not state.kont):
        states.append(state)
        state = cek.step(state, m)
    states.append(state)
    return states, state.val


if __name__ == "__main__":
    states, result = run_states(SRC)

    # the frame that reifies [·] x is ApplyFnF (function position being evaluated,
    # argument list still pending)
    saw_applyfn = any(
        any(type(fr).__name__ == "ApplyFnF" for fr in s.kont) for s in states
    )
    # and the argument-pending frame ApplyArgF appears once the fn is a value
    saw_applyarg = any(
        any(type(fr).__name__ == "ApplyArgF" for fr in s.kont) for s in states
    )
    assert saw_applyfn, "ApplyFnF should appear (it reifies [·] x)"
    assert saw_applyarg
    assert isinstance(result, cek.VInt) and result.n == 4, result

    print("ApplyFnF([x]) appears in kont — it reifies [·] x; result 4")
