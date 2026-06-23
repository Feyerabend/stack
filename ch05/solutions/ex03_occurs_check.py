"""
Chapter 5, Exercise 3 — solution code.

The occurs check prevents infinite types. Construct a term that would trigger an
infinite type if the occurs check were removed. Show the unification steps, name
the variable and the type it would be bound to, and explain why that infinite
type is not a valid member of the Type datatype.

How to run:   python3 ex03_occurs_check.py
Expected:     "self-application rejected by occurs check (t0 = t0 -> t1)"

THE TERM: self-application  lambda x. x x.

UNIFICATION STEPS (with x : t0 fresh):
  - inferring the application `x x`, the function `x` has type t0 and the
    argument `x` has type t0; a fresh t1 is made for the result.
  - the rule unifies the function type with (arg -> result):
        unify( t0 ,  t0 -> t1 )
  - this tries to bind  t0 := t0 -> t1 . The variable t0 OCCURS inside the type
    t0 -> t1 it is being bound to, so the occurs check fires and inference fails.

WHY THE INFINITE TYPE IS NOT A VALID Type. Binding t0 := t0 -> t1 and expanding
gives  t0 = (t0 -> t1) -> t1 = ((t0 -> t1) -> t1) -> t1 = ...  — an infinitely
deep tree. The Type datatype is an INDUCTIVE (finite) structure: every TypeVar,
TypeConst, or FunctionType is built from strictly smaller finite types. No finite
term of that datatype satisfies t0 = t0 -> t1, so the equation has no solution in
Type; the occurs check is exactly the test that rejects it.
"""

import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_HM = os.path.join(os.path.dirname(_HERE),
                   "04_lambda_calculus", "calculus", "hm.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hm = _load(_HM, "hm")
Var, Abs, App = hm.Var, hm.Abs, hm.App
TypeVar, FunctionType = hm.TypeVar, hm.FunctionType
Substitution = hm.Substitution
infer = hm.infer
TypeEnvironment, TypeVarGenerator = hm.TypeEnvironment, hm.TypeVarGenerator


if __name__ == "__main__":
    # Inferring lambda x. x x must fail.
    self_app = Abs("x", App(Var("x"), Var("x")))
    try:
        infer(self_app, TypeEnvironment(), TypeVarGenerator())
        rejected = False
    except hm.TypeInferenceError:
        rejected = True
    assert rejected, "self-application should be rejected"

    # The decisive step in isolation: unify(t0, t0 -> t1) must fail the occurs
    # check (and binding it would be accepted only with the check removed).
    t0, t1 = TypeVar("t0"), TypeVar("t1")
    assert hm.occurs_check("t0", FunctionType(t0, t1), Substitution()) is True
    try:
        hm.unify(t0, FunctionType(t0, t1), Substitution())
        unify_ok = True
    except hm.TypeInferenceError:
        unify_ok = False
    assert not unify_ok, "unify(t0, t0 -> t1) must fail"

    print("self-application rejected by occurs check (t0 = t0 -> t1)")
