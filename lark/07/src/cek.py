"""
Lark CEK machine — small-step interpreter for the typed AST.

State = Eval(expr, env, kont)   — reducing an expression
      | Return(val, kont)        — delivering a value to the continuation

The main loop is iterative (one `while` in `run`). No Python stack frames are
pushed per Lark function call, so tail-recursive Lark programs run without
Python stack overflow even on millions of iterations.

Entry point:
    run_file(path)    parse, type-check, call main(io), print output
"""

from __future__ import annotations
import sys, os, pathlib, struct as _struct
sys.path.insert(0, os.path.dirname(__file__))

def _f32(x: float) -> float:
    return _struct.unpack('f', _struct.pack('f', float(x)))[0]

def _show_float(f: float) -> str:
    s = f"{_f32(f):.7g}"
    return s if '.' in s or 'e' in s else s + '.0'

import parser as _parser
import infer  as _infer

from dataclasses import dataclass, field
from typing import Union

from tree import Program, ImportDecl
from typed_tree import (
    TProgram, TFnDecl, TLetDecl, TTypeDecl, TImplDecl,
    TExpr, TLit, TVar, TCon, TTupleExpr, TApply, TBinOp, TUnaryOp,
    TLetExpr, TIfExpr, TMatchExpr, TLambda,
    TPat, TPWild, TPVar, TPLit, TPCon, TPTuple,
)
import ty


# ── Values ────────────────────────────────────────────────────────────────────

@dataclass
class VInt:
    n: int
    def __repr__(self): return str(self.n)

@dataclass
class VFloat:
    f: float
    def __repr__(self): return str(self.f)

@dataclass
class VBool:
    b: bool
    def __repr__(self): return "true" if self.b else "false"

@dataclass
class VStr:
    s: str
    def __repr__(self): return self.s

@dataclass
class VUnit:
    def __repr__(self): return "()"

@dataclass
class VTuple:
    elems: tuple[Value, ...]
    def __repr__(self): return "(" + ", ".join(repr(e) for e in self.elems) + ")"

@dataclass
class VCon:
    """Fully-applied ADT constructor."""
    tag:     str
    payload: tuple[Value, ...]
    def __repr__(self):
        if not self.payload: return self.tag
        return self.tag + "(" + ", ".join(repr(a) for a in self.payload) + ")"

@dataclass
class VPartialCon:
    """Constructor waiting for more arguments."""
    tag:   str
    arity: int
    args:  tuple[Value, ...]

@dataclass
class VClosure:
    """Lambda closure with one parameter (all functions are curried)."""
    param:    str
    body:     TExpr
    env:      dict
    rec_name: str | None = None   # if set, self is rebound on entry

@dataclass
class VBuiltin:
    """Named built-in function (print, show, read, …)."""
    name: str
    def __repr__(self): return f"<{self.name}>"

@dataclass
class VPrintIO:
    """Intermediate: print partially applied to its IO argument."""
    io: Value

@dataclass
class VDispatch:
    """Trait method — dispatches at runtime to the correct impl."""
    method: str

@dataclass
class VIO:
    """IO resource token."""
    def __repr__(self): return "<IO>"

Value = Union[
    VInt, VFloat, VBool, VStr, VUnit, VTuple,
    VCon, VPartialCon, VClosure, VBuiltin, VPrintIO, VDispatch, VIO,
]


# ── Continuation frames ───────────────────────────────────────────────────────

@dataclass
class ApplyFnF:
    args: list[TExpr]
    env:  dict

@dataclass
class ApplyArgF:
    fn_val:    Value
    remaining: list[TExpr]
    env:       dict

@dataclass
class LetF:
    name: str
    body: TExpr
    env:  dict

@dataclass
class IfF:
    then_: TExpr
    else_: TExpr
    env:   dict

@dataclass
class MatchF:
    arms: tuple
    env:  dict

@dataclass
class BinOpLF:
    op:    str
    right: TExpr
    env:   dict

@dataclass
class BinOpRF:
    op:       str
    left_val: Value

@dataclass
class UnaryF:
    op: str

@dataclass
class TupleF:
    remaining: list[TExpr]
    done:      list[Value]
    env:       dict

Frame = Union[ApplyFnF, ApplyArgF, LetF, IfF, MatchF,
              BinOpLF, BinOpRF, UnaryF, TupleF]


# ── States ────────────────────────────────────────────────────────────────────

@dataclass
class Eval:
    expr: TExpr
    env:  dict
    kont: list[Frame]

@dataclass
class Return:
    val:  Value
    kont: list[Frame]

State = Union[Eval, Return]


# ── Machine context ───────────────────────────────────────────────────────────

@dataclass
class Machine:
    dispatch:    dict[tuple[str, str], Value] = field(default_factory=dict)
    con_to_type: dict[str, str]               = field(default_factory=dict)
    con_arity:   dict[str, int]               = field(default_factory=dict)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _lit_val(v: object) -> Value:
    if v is None:            return VUnit()
    if isinstance(v, bool):  return VBool(v)
    if isinstance(v, int):   return VInt(v)
    if isinstance(v, float): return VFloat(v)
    if isinstance(v, str):   return VStr(v)
    raise RuntimeError(f"unknown literal: {v!r}")

def _val_eq(a: Value, b: Value) -> bool:
    match (a, b):
        case (VInt(n=x),   VInt(n=y)):   return x == y
        case (VFloat(f=x), VFloat(f=y)): return x == y
        case (VBool(b=x),  VBool(b=y)):  return x == y
        case (VStr(s=x),   VStr(s=y)):   return x == y
        case (VUnit(),     VUnit()):      return True
        case _: return False

def show(v: Value) -> str:
    match v:
        case VInt(n=n):     return str(n)
        case VFloat(f=f):   return _show_float(f)
        case VBool(b=b):    return "true" if b else "false"
        case VStr(s=s):     return s
        case VUnit():       return "()"
        case VTuple(elems=es): return "(" + ", ".join(show(e) for e in es) + ")"
        case VCon(tag=t, payload=p):
            if not p: return t
            return t + "(" + ", ".join(show(a) for a in p) + ")"
        case _: return repr(v)

def runtime_type(v: Value, m: Machine) -> str:
    match v:
        case VInt():   return "Int"
        case VFloat(): return "Float"
        case VBool():  return "Bool"
        case VStr():   return "String"
        case VUnit():  return "()"
        case VCon(tag=t): return m.con_to_type.get(t, t)
        case _: return "?"


# ── Arithmetic / logic ────────────────────────────────────────────────────────

def binop(op: str, l: Value, r: Value) -> Value:
    if op == "+" and isinstance(l, VStr) and isinstance(r, VStr):
        return VStr(l.s + r.s)
    if isinstance(l, VInt) and isinstance(r, VInt):
        match op:
            case "+":  return VInt(l.n + r.n)
            case "-":  return VInt(l.n - r.n)
            case "*":  return VInt(l.n * r.n)
            case "/":  return VInt(l.n // r.n)
            case "==": return VBool(l.n == r.n)
            case "!=": return VBool(l.n != r.n)
            case "<":  return VBool(l.n <  r.n)
            case "<=": return VBool(l.n <= r.n)
            case ">":  return VBool(l.n >  r.n)
            case ">=": return VBool(l.n >= r.n)
    if isinstance(l, VFloat) and isinstance(r, VFloat):
        lf, rf = _f32(l.f), _f32(r.f)
        match op:
            case "+":  return VFloat(_f32(lf + rf))
            case "-":  return VFloat(_f32(lf - rf))
            case "*":  return VFloat(_f32(lf * rf))
            case "/":  return VFloat(_f32(lf / rf) if rf else float('nan'))
            case "==": return VBool(lf == rf)
            case "!=": return VBool(lf != rf)
            case "<":  return VBool(lf <  rf)
            case "<=": return VBool(lf <= rf)
            case ">":  return VBool(lf >  rf)
            case ">=": return VBool(lf >= rf)
    if op == "and": return VBool(isinstance(l, VBool) and isinstance(r, VBool) and l.b and r.b)
    if op == "or":  return VBool((isinstance(l, VBool) and l.b) or (isinstance(r, VBool) and r.b))
    raise RuntimeError(f"cannot apply '{op}' to {l!r} and {r!r}")

def unaryop(op: str, v: Value) -> Value:
    if op == "-":
        if isinstance(v, VInt):   return VInt(-v.n)
        if isinstance(v, VFloat): return VFloat(_f32(-_f32(v.f)))
    if op == "not" and isinstance(v, VBool):
        return VBool(not v.b)
    raise RuntimeError(f"cannot apply unary '{op}' to {v!r}")


# ── Pattern matching ──────────────────────────────────────────────────────────

def match_pat(pat: TPat, val: Value, env: dict) -> dict | None:
    match pat:
        case TPWild():
            return env
        case TPVar(name=n):
            return {**env, n: val}
        case TPLit(value=v):
            return env if _val_eq(val, _lit_val(v)) else None
        case TPCon(name=n, args=sub_pats):
            if n in ("True", "False") and not sub_pats:
                expected = (n == "True")
                return env if isinstance(val, VBool) and val.b == expected else None
            if not isinstance(val, VCon) or val.tag != n:
                return None
            if len(sub_pats) != len(val.payload):
                return None
            e = env
            for sp, sv in zip(sub_pats, val.payload):
                e = match_pat(sp, sv, e)
                if e is None:
                    return None
            return e
        case TPTuple(elems=sub_pats):
            if not isinstance(val, VTuple) or len(sub_pats) != len(val.elems):
                return None
            e = env
            for sp, sv in zip(sub_pats, val.elems):
                e = match_pat(sp, sv, e)
                if e is None:
                    return None
            return e
    return None


# ── Application ───────────────────────────────────────────────────────────────

def apply(fn: Value, arg: Value, kont: list[Frame], m: Machine) -> State:
    """Apply fn to arg, returning the next CEK state."""
    match fn:
        case VClosure(param=p, body=body, env=cenv, rec_name=rn):
            new_env = dict(cenv)
            new_env[p] = arg
            if rn:
                new_env[rn] = fn
            return Eval(body, new_env, kont)

        case VPartialCon(tag=tag, arity=arity, args=args):
            new_args = args + (arg,)
            v = VCon(tag, new_args) if len(new_args) == arity else VPartialCon(tag, arity, new_args)
            return Return(v, kont)

        case VBuiltin(name=name):
            return builtin(name, arg, kont, m)

        case VPrintIO(io=io):
            if not isinstance(arg, VStr):
                raise RuntimeError(f"print expected String, got {arg!r}")
            print(arg.s)
            return Return(io, kont)

        case VDispatch(method=meth):
            type_name = runtime_type(arg, m)
            impl = m.dispatch.get((meth, type_name))
            if impl is None:
                raise RuntimeError(f"no impl of '{meth}' for type '{type_name}'")
            return apply(impl, arg, kont, m)

        case _:
            raise RuntimeError(f"not a function: {fn!r}")


def builtin(name: str, arg: Value, kont: list[Frame], m: Machine) -> State:
    match name:
        case "print":
            return Return(VPrintIO(arg), kont)
        case "read":
            line = sys.stdin.readline().rstrip("\n")
            return Return(VTuple((arg, VStr(line))), kont)
        case "show":
            return Return(VStr(show(arg)), kont)
        case "int_to_float":
            assert isinstance(arg, VInt)
            return Return(VFloat(float(arg.n)), kont)
        case "float_to_int":
            assert isinstance(arg, VFloat)
            return Return(VInt(int(_f32(arg.f))), kont)
        case "int_to_string":
            return Return(VStr(show(arg)), kont)
        case "float_to_string":
            return Return(VStr(show(arg)), kont)
        case "int_abs":
            assert isinstance(arg, VInt)
            return Return(VInt(abs(arg.n)), kont)
        case "float_abs":
            assert isinstance(arg, VFloat)
            return Return(VFloat(_f32(abs(_f32(arg.f)))), kont)
        case "float_sqrt":
            import math as _math
            assert isinstance(arg, VFloat)
            f = _f32(arg.f)
            v = _f32(_math.sqrt(f)) if f >= 0.0 else float('nan')
            return Return(VFloat(v), kont)
        case "float_floor":
            import math as _math
            assert isinstance(arg, VFloat)
            return Return(VFloat(_f32(float(_math.floor(_f32(arg.f))))), kont)
        case "float_ceil":
            import math as _math
            assert isinstance(arg, VFloat)
            return Return(VFloat(_f32(float(_math.ceil(_f32(arg.f))))), kont)
        case "string_length":
            assert isinstance(arg, VStr)
            return Return(VInt(len(arg.s)), kont)
        case _:
            raise RuntimeError(f"unknown builtin: {name!r}")


# ── CEK steps ─────────────────────────────────────────────────────────────────

def step(state: State, m: Machine) -> State:
    match state:
        case Eval(expr=e, env=env, kont=kont):
            return step_eval(e, env, kont, m)
        case Return(val=v, kont=[frame, *rest]):
            return step_ret(v, frame, rest, m)
        case _:
            raise RuntimeError(f"stuck state: {state!r}")


def step_eval(expr: TExpr, env: dict, kont: list[Frame], m: Machine) -> State:
    match expr:

        case TLit(value=v):
            return Return(_lit_val(v), kont)

        case TVar(name=n):
            if n not in env:
                raise RuntimeError(f"unbound: {n!r}")
            return Return(env[n], kont)

        case TCon(name=n):
            if n not in env:
                raise RuntimeError(f"unbound constructor: {n!r}")
            return Return(env[n], kont)

        case TTupleExpr(elems=elems):
            if not elems:
                return Return(VUnit(), kont)
            return Eval(elems[0], env, [TupleF(list(elems[1:]), [], env)] + kont)

        case TApply(fn=fn, args=args):
            if not args:
                raise RuntimeError("application with no arguments")
            return Eval(fn, env, [ApplyFnF(list(args), env)] + kont)

        case TBinOp(op=op, left=l, right=r):
            return Eval(l, env, [BinOpLF(op, r, env)] + kont)

        case TUnaryOp(op=op, operand=e):
            return Eval(e, env, [UnaryF(op)] + kont)

        case TLetExpr(name=n, value=v, body=body):
            return Eval(v, env, [LetF(n, body, env)] + kont)

        case TIfExpr(cond=c, then_=t, else_=e):
            return Eval(c, env, [IfF(t, e, env)] + kont)

        case TMatchExpr(scrutinee=s, arms=arms):
            return Eval(s, env, [MatchF(arms, env)] + kont)

        case TLambda(params=params, body=body):
            name0, _ = params[0]
            if len(params) == 1:
                return Return(VClosure(name0, body, dict(env)), kont)
            # Desugar: wrap remaining params in a nested TLambda
            inner = TLambda(params[1:], body, ty.T_UNIT)   # type: ignore
            return Return(VClosure(name0, inner, dict(env)), kont)

        case _:
            raise RuntimeError(f"unknown expr: {type(expr).__name__}")


def step_ret(val: Value, frame: Frame, rest: list[Frame], m: Machine) -> State:
    match frame:

        case TupleF(remaining=[], done=done, env=_):
            return Return(VTuple(tuple(done + [val])), rest)

        case TupleF(remaining=[nxt, *rem], done=done, env=env):
            return Eval(nxt, env, [TupleF(rem, done + [val], env)] + rest)

        case ApplyFnF(args=[arg, *rem], env=env):
            # fn evaluated to val; start on first argument
            return Eval(arg, env, [ApplyArgF(val, rem, env)] + rest)

        case ApplyArgF(fn_val=fn, remaining=[], env=_):
            # last argument: apply and pass result onward
            return apply(fn, val, rest, m)

        case ApplyArgF(fn_val=fn, remaining=[nxt, *rem], env=env):
            # intermediate argument: apply to get partial, then eval next
            partial = run(apply(fn, val, [], m), m)
            return Eval(nxt, env, [ApplyArgF(partial, rem, env)] + rest)

        case LetF(name=n, body=body, env=env):
            return Eval(body, {**env, n: val}, rest)

        case IfF(then_=t, else_=e, env=env):
            if not isinstance(val, VBool):
                raise RuntimeError(f"if condition not bool: {val!r}")
            return Eval(t if val.b else e, env, rest)

        case MatchF(arms=arms, env=env):
            for (pat, body) in arms:
                new_env = match_pat(pat, val, env)
                if new_env is not None:
                    return Eval(body, new_env, rest)
            raise RuntimeError(f"non-exhaustive match on {val!r}")

        case BinOpLF(op=op, right=r, env=env):
            return Eval(r, env, [BinOpRF(op, val)] + rest)

        case BinOpRF(op=op, left_val=lv):
            return Return(binop(op, lv, val), rest)

        case UnaryF(op=op):
            return Return(unaryop(op, val), rest)

        case _:
            raise RuntimeError(f"unknown frame: {type(frame).__name__}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def run(init: State, m: Machine) -> Value:
    state = init
    while True:
        match state:
            case Return(val=v, kont=[]):
                return v
            case _:
                state = step(state, m)


# ── Program evaluation ────────────────────────────────────────────────────────

def make_closure(name: str, params: tuple, body: TExpr, env: dict) -> Value:
    """Build a (possibly curried) named closure."""
    if not params:
        raise RuntimeError(f"{name!r} has no params")
    p0, _ = params[0]
    if len(params) == 1:
        return VClosure(p0, body, dict(env), rec_name=name)
    inner = TLambda(params[1:], body, ty.T_UNIT)   # type: ignore
    return VClosure(p0, inner, dict(env), rec_name=name)


def initial_env(m: Machine) -> dict:
    """Built-in names available in every Lark program."""
    env = {
        "print": VBuiltin("print"),
        "read":  VBuiltin("read"),
        "show":  VBuiltin("show"),
        "int_to_float":    VBuiltin("int_to_float"),
        "float_to_int":    VBuiltin("float_to_int"),
        "int_to_string":   VBuiltin("int_to_string"),
        "float_to_string": VBuiltin("float_to_string"),
        "int_abs":         VBuiltin("int_abs"),
        "float_abs":       VBuiltin("float_abs"),
        "float_sqrt":      VBuiltin("float_sqrt"),
        "float_floor":     VBuiltin("float_floor"),
        "float_ceil":      VBuiltin("float_ceil"),
        "string_length":   VBuiltin("string_length"),
        "Nil":   VCon("Nil", ()),
        "Cons":  VPartialCon("Cons", 2, ()),
        "Ok":    VPartialCon("Ok",  1, ()),
        "Err":   VPartialCon("Err", 1, ()),
        "True":  VBool(True),
        "False": VBool(False),
    }
    for tag in ("Nil", "Cons"):
        m.con_to_type[tag] = "List"
    m.con_arity.update({"Nil": 0, "Cons": 2})
    for tag in ("Ok", "Err"):
        m.con_to_type[tag] = "Result"
    m.con_arity.update({"Ok": 1, "Err": 1})
    return env


def eval_program(
    prog: Program,
    tprog: TProgram,
    source_file: str | None,
    m: Machine,
    env: dict | None = None,
) -> dict:
    """Evaluate all declarations; return the final environment."""
    if env is None:
        env = initial_env(m)

    # Register ADT constructors from TTypeDecl
    for td in tprog.decls:
        if isinstance(td, TTypeDecl) and td.variants:
            for v in td.variants:
                arity = len(v.payload)
                m.con_to_type[v.name] = td.name
                m.con_arity[v.name]   = arity
                env[v.name] = VCon(v.name, ()) if arity == 0 else VPartialCon(v.name, arity, ())

    # Load imports before evaluating anything that might reference them
    if source_file:
        src_dir = os.path.dirname(os.path.abspath(source_file))
        for imp in prog.imports:
            load_import(imp, src_dir, env, m)

    # Evaluate declarations in source order (original sequential behaviour).
    for td in tprog.decls:
        match td:
            case TFnDecl(name=name, params=params, body=body):
                env[name] = make_closure(name, params, body, env)

            case TLetDecl(name=name, value=val_expr):
                env[name] = run(Eval(val_expr, env, []), m)

            case TImplDecl(trait_name=_, for_type=type_name, methods=methods):
                for meth in methods:
                    closure = make_closure(meth.name, meth.params, meth.body, env)
                    m.dispatch[(meth.name, type_name)] = closure
                    if meth.name not in env or not isinstance(env[meth.name], VDispatch):
                        # First impl for this method: if it was previously a builtin
                        # (e.g. show), seed primitive types in the dispatch table so
                        # they continue to work after routing switches to VDispatch.
                        if isinstance(env.get(meth.name), VBuiltin):
                            builtin_val = env[meth.name]
                            for prim in ("Int", "Float", "Bool", "String", "()"):
                                if (meth.name, prim) not in m.dispatch:
                                    m.dispatch[(meth.name, prim)] = builtin_val
                        env[meth.name] = VDispatch(meth.name)

            case _:
                pass   # TTypeDecl already handled above

    # Backpatch: update every top-level function closure's captured env with
    # all other top-level function closures.  This wires mutual references so
    # that is_even can call is_odd even though is_odd was defined later.
    top_fns = {
        td.name: env[td.name]
        for td in tprog.decls
        if isinstance(td, TFnDecl) and td.name in env
    }
    for clos in top_fns.values():
        if isinstance(clos, VClosure):
            clos.env.update(top_fns)

    return env


def load_import(imp: ImportDecl, src_dir: str, env: dict, m: Machine) -> None:
    """Find, evaluate, and merge an imported module."""
    module_name = imp.module
    candidates  = [
        pathlib.Path(src_dir) / f"{module_name.lower()}.lark",
        pathlib.Path(src_dir) / f"{module_name}.lark",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return

    abs_path      = str(path.resolve())
    imported_prog = _parser.parse_file(abs_path)
    imported_tp   = _infer.typecheck(imported_prog, source_file=abs_path)

    # Evaluate the module into a fresh env (shared machine for constructor info)
    mod_env = eval_program(imported_prog, imported_tp, abs_path, m, initial_env(m))

    exposing = set(imp.exposing) if imp.exposing else None

    for name, val in mod_env.items():
        if isinstance(val, VBuiltin):
            continue   # don't re-import built-ins
        exposed = (
            exposing is None
            or name in exposing
            or (
                name[0].isupper()
                and m.con_to_type.get(name) in exposing
            )
        )
        if exposed:
            env[name] = val


# ── Entry point ───────────────────────────────────────────────────────────────

def run_file(path: str) -> None:
    """Parse, type-check, and run a Lark source file."""
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)

    m   = Machine()
    env = eval_program(prog, tprog, path, m)

    if "main" not in env:
        print(f"(no main in {path})", file=sys.stderr)
        sys.exit(1)

    run(apply(env["main"], VIO(), [], m), m)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: cek.py <file.lark>", file=sys.stderr)
        sys.exit(1)
    run_file(sys.argv[1])
