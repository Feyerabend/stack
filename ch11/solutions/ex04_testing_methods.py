"""
Chapter 11, Exercise 4 — solution code.

Each testing method has a distinct job. (a) construct a compiler bug differential
testing catches but property testing doesn't, and one for which the reverse
holds. (b) explain why neither could replace the type-safety proof, and why the
proof could not replace either.

How to run:   python3 ex04_testing_methods.py
Expected:     "differential found A; property found B; fuzzing found C; "
              "each misses the other two by construction"

Drives the chapter's companion ch11/05_testing/testing_methods.py — one tiny
expression language carrying three planted bugs:
  A  eval_fast subtracts backwards          (a second, wrong implementation)
  B  simplify rewrites e*0 to e             (a violated semantic invariant)
  C  parse crashes on truncated input       (a robustness/crash bug)

(a) THE PAIR.
  * Bug A is caught by DIFFERENTIAL testing (it compares eval_ref against the
    second implementation eval_fast) but NOT by property testing: the property
    "simplify preserves meaning" only ever calls eval_ref, so it never exercises
    eval_fast and cannot see A.
  * Bug B is caught by PROPERTY testing (the invariant eval(simplify e) == eval e
    fails) but NOT by differential testing: differential compares two evaluators
    and never invokes simplify, so it cannot see B. (To catch B differentially
    you would need a *correct* second simplify to compare against — i.e. the
    thing you are trying to test.)
  So A and B are the requested pair; fuzzing catches C, which feeds malformed
  input the other two never generate (both build only well-formed expressions).

(b) NEITHER REPLACES THE PROOF, AND THE PROOF REPLACES NEITHER.
  * Testing SAMPLES finitely many inputs; type safety (preservation + progress,
    Ex.2/3) covers the INFINITE space of well-typed terms once and for all. No
    number of passing tests proves "no well-typed program gets stuck."
  * But the proof is about ONE property (type soundness) of the SEMANTICS. It
    says nothing about whether a particular pass is faithful (differential), or
    whether `simplify` preserves meaning (property), or whether the parser is
    robust to garbage (fuzzing). Those are properties of code the proof does not
    range over. The proof and the tests guard different things.
"""

import os
import random
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH11 = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_CH11, "05_testing"))

import testing_methods as T   # noqa: E402


if __name__ == "__main__":
    random.seed(11)
    a = T.differential()      # bug A
    b = T.property_based()    # bug B
    c = T.fuzzing()           # bug C

    assert a is not None and "fast=" in a, a       # found a ref-vs-fast disagreement
    assert b is not None and "simplify" in b       # found an invariant violation
    assert c is not None and "crashed" in c        # found a crash on bad input

    # Structural misses (a): the property invariant never touches eval_fast, and
    # differential never touches simplify — so neither can find the other's bug.
    import inspect
    prop_src = inspect.getsource(T.property_based)
    diff_src = inspect.getsource(T.differential)
    assert "eval_fast" not in prop_src    # property can't see bug A
    assert "simplify" not in diff_src     # differential can't see bug B

    print("differential found A; property found B; fuzzing found C; "
          "each misses the other two by construction")
