"""
Chapter 5, Exercise 2 — solution code.

Trace Algorithm W on  let f = fn x => x in (f 1, f true).  Show (a) fresh
variables, (b) the substitution after the lambda, (c) f's generalised scheme,
(d) the fresh instantiation at each call site, (e) the two component types.
Identify the step where let-polymorphism becomes visible.

How to run:   python3 ex02_algorithm_w.py
Expected:     "f :: forall t. t -> t ; components (Int, Bool) ; real Lark types "
              "the whole expr (Int, Bool)"

The narrative trace is in solutions.md. This drives the chapter's Algorithm-W
implementation (hm.py) for the mechanism and cross-checks the whole expression
against the real Lark checker.

WHERE LET-POLYMORPHISM BECOMES VISIBLE — the GENERALISE step. In hm.py's `Let`
case the value's type is passed through `generalize(env, t)`, producing a SCHEME
with quantified variables (forall t. t -> t). In the `Abs` case a parameter is
bound as `TypeScheme(set(), tvar)` — NO quantifiers, i.e. monomorphic. That one
call to `generalize` (present for let, absent for a lambda parameter) is the
entire source of let-polymorphism: only a generalised scheme can be instantiated
with a *different* fresh variable at each use site, which is what lets f serve
both `f 1` (t := Int) and `f true` (t := Bool). In textbook HM the lambda-bound
form (fn f => (f 1, f true)) (fn x => x) is rejected for exactly this reason — a
monomorphic parameter cannot be both Int -> _ and Bool -> _. Both the teaching
hm.py and the real Lark checker enforce this: the lambda-bound form fails with a
unification error, while the let-bound form typechecks (this script asserts both
in hm.py and against the real Lark checker). The scheme comparison below shows
why the let succeeds.
"""

import importlib.util
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
_HM = os.path.join(os.path.dirname(_HERE),
                   "04_lambda_calculus", "calculus", "hm.py")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


hm = _load(_HM, "hm")
Var, Abs, App, Let = hm.Var, hm.Abs, hm.App, hm.Let
TypeVar, TypeConst, FunctionType = hm.TypeVar, hm.TypeConst, hm.FunctionType
TypeScheme, TypeEnvironment, TypeVarGenerator = (
    hm.TypeScheme, hm.TypeEnvironment, hm.TypeVarGenerator)
infer, generalize = hm.infer, hm.generalize

INT, BOOL = TypeConst("Int"), TypeConst("Bool")


def base_env():
    env = TypeEnvironment()
    env = env.extend("1", TypeScheme(set(), INT))       # literal 1 : Int
    env = env.extend("true", TypeScheme(set(), BOOL))   # literal true : Bool
    return env


def _lark():
    import sys
    sys.path.insert(0, os.path.join(_LANG, "lark", "07", "src"))
    from lexer import Lexer
    from parser import Parser
    import infer as lark_infer
    return Lexer, Parser, lark_infer


def real_lark_whole():
    """The let-bound expression typechecks against the (Int, Bool) annotation."""
    Lexer, Parser, lark_infer = _lark()
    src = ("module M\n"
           "fn test(io : IO) : (Int, Bool) = "
           "let f = fn (x) => x in (f(1), f(true))")
    lark_infer.typecheck(Parser(Lexer(src).tokenize()).parse())
    return True


def real_lark_lambda_bound_rejected():
    """The lambda-bound form is rejected: a monomorphic param can't be Int & Bool."""
    Lexer, Parser, lark_infer = _lark()
    src = ("module M\n"
           "fn test(io : IO) : (Int, Bool) = "
           "(fn (f) => (f(1), f(true)))(fn (x) => x)")
    try:
        lark_infer.typecheck(Parser(Lexer(src).tokenize()).parse())
        return False
    except lark_infer.TypeError:
        return True


if __name__ == "__main__":
    # (a) fresh variables come from the generator, in order t0, t1, ...
    g = TypeVarGenerator()
    assert [g.fresh().name for _ in range(3)] == ["t0", "t1", "t2"]

    # (b) inferring the lambda `fn x => x` gives an identity type t -> t
    gen = TypeVarGenerator()
    _, id_type = infer(Abs("x", Var("x")), base_env(), gen)
    assert isinstance(id_type, FunctionType)
    assert id_type.param_type.name == id_type.return_type.name

    # (c) generalisation turns it into the scheme  forall t. t -> t
    f_scheme = generalize(base_env(), id_type)
    assert len(f_scheme.type_vars) == 1
    tv = next(iter(f_scheme.type_vars))

    # (the step) a lambda parameter would instead be bound monomorphically:
    lambda_param_scheme = TypeScheme(set(), id_type)   # how Abs binds a param
    assert len(lambda_param_scheme.type_vars) == 0      # no quantifiers => no poly

    # (d)+(e) each use site instantiates the let scheme freshly: Int then Bool
    env_with_f = base_env().extend("f", f_scheme)
    gen2 = TypeVarGenerator()
    _, t_int = infer(App(Var("f"), Var("1")), env_with_f, gen2)
    _, t_bool = infer(App(Var("f"), Var("true")), env_with_f, gen2)
    assert t_int == INT and t_bool == BOOL

    # the whole let also typechecks in hm.py (Int via the first component)
    whole = Let("f", Abs("x", Var("x")), App(Var("f"), Var("1")))
    _, wt = infer(whole, base_env(), TypeVarGenerator())
    assert wt == INT

    # let-poly vs lambda-mono, demonstrated in hm.py with const : a -> b -> a so
    # f is used at two types in one expression.
    a, b = TypeVar("a"), TypeVar("b")
    env_const = base_env().extend(
        "const", TypeScheme({"a", "b"}, FunctionType(a, FunctionType(b, a))))
    use_f_twice = App(App(Var("const"), App(Var("f"), Var("1"))),
                      App(Var("f"), Var("true")))
    # let-bound f: generalised -> accepted
    _, lt = infer(Let("f", Abs("x", Var("x")), use_f_twice),
                  env_const, TypeVarGenerator())
    assert lt == INT
    # lambda-bound f: monomorphic -> rejected
    try:
        infer(App(Abs("f", use_f_twice), Abs("x", Var("x"))),
              env_const, TypeVarGenerator())
        hm_rejects = False
    except hm.TypeInferenceError:
        hm_rejects = True
    assert hm_rejects, "hm.py should reject lambda-bound f used at Int and Bool"

    assert real_lark_whole()
    assert real_lark_lambda_bound_rejected()

    print(f"f :: forall {tv}. {tv} -> {tv} ; components (Int, Bool) ; "
          f"hm.py + real Lark: let-bound OK, lambda-bound rejected")
