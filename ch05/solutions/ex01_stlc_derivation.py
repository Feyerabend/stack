"""
Chapter 5, Exercise 1 — solution code.

Write the full typing derivation for
    (lambda f:(Int -> Int). f 1) (lambda x:Int. x + 1)
in the STLC. Identify the rule at each node and the environment at each leaf.
What is the type of the whole expression?

How to run:   python3 ex01_stlc_derivation.py
Expected:     "whole expression : Int"

The full derivation tree is in solutions.md. The result is Int.

Pure STLC has no literals or operators, so `1` and `+` are modelled the standard
way: as typed CONSTANTS in the context (`one : Int`, `plus : Int -> Int -> Int`),
exactly how the simply-typed calculus treats primitives. The structure of the
term — and therefore its derivation — is unchanged. This drives the chapter's
companion STLC checker, ch05/04_lambda_calculus/calculus/lambda.py.
"""

import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_CALC = os.path.join(os.path.dirname(_HERE),
                     "04_lambda_calculus", "calculus", "lambda.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


stlc = _load(_CALC, "stlc")
Var, Abs, App = stlc.Var, stlc.Abs, stlc.App
BaseType, FunctionType = stlc.BaseType, stlc.FunctionType
TypeContext, typecheck = stlc.TypeContext, stlc.typecheck

INT = BaseType("Int")
INT_TO_INT = FunctionType(INT, INT)


if __name__ == "__main__":
    # Constants modelling the primitives `1` and `+`.
    ctx = TypeContext()
    ctx = ctx.extend("one", INT)                                   # 1 : Int
    ctx = ctx.extend("plus", FunctionType(INT, INT_TO_INT))        # + : Int->Int->Int

    # inner = lambda x:Int. x + 1   ==   lambda x:Int. ((plus x) one)
    inner = Abs("x", INT,
                App(App(Var("plus"), Var("x")), Var("one")))

    # outer = lambda f:(Int->Int). f 1   ==   lambda f. (f one)
    outer = Abs("f", INT_TO_INT,
                App(Var("f"), Var("one")))

    whole = App(outer, inner)

    # Sanity on the parts (these are the subtrees of the derivation):
    assert str(typecheck(inner, ctx)) == "Int → Int"          # inner : Int -> Int
    assert str(typecheck(outer, ctx)) == "(Int → Int) → Int"  # outer : (Int->Int)->Int

    t = typecheck(whole, ctx)
    assert isinstance(t, BaseType) and t.name == "Int", t
    print(f"whole expression : {t}")
