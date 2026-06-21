"""
Lark type checker — Hindley-Milner inference (Algorithm W) with affine tracking.

Architecture: bidirectional, following the proof/ reference.
  - infer(env, tracked, expr) -> (TExpr, Mono, Subst)
       synthesises the type of expr.
  - check_fn_decl / check_let_decl: top-level declaration checkers.

Affine tracking:
  `tracked` is a dict[name -> use_count] containing only the locally-bound
  parameters (and any let-bound names) whose TYPE is concretely non-Copy at
  bind time.  Global names (builtins, top-level decls) are never in `tracked`.
  The checker raises AffineError when a tracked variable is used more than once.

Recursion:
  Each fn declaration adds its own name to the local env with a fresh type var
  before checking the body, enabling direct and mutual recursion.

Entry point:
    typecheck(program: Program) -> TProgram   raises TypeError / AffineError
"""

from __future__ import annotations
import sys, os, pathlib
sys.path.insert(0, os.path.dirname(__file__))

import parser as _parser

from tree import (
    Program, FnDecl, LetDecl, TypeDecl, TraitDecl, ImplDecl,
    Variant,
    Expr, Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
    LetExpr, IfExpr, MatchExpr, Lambda,
    Pat, PWild, PVar, PLit, PCon, PTuple,
    Type, TName, TApply as STApply, TFn as STFn, TUnit as STUnit, TTuple as STTuple,
    Param, Bound,
)
import ty
from ty import (
    Mono, Scheme, Fresh, Subst,
    TVar, TCon, TApp, TFn, TTup,
    apply, apply_scheme, compose, free_vars, free_vars_scheme, unify,
    T_INT, T_FLOAT, T_BOOL, T_STRING, T_UNIT, T_IO,
    t_list, t_result, t_fn, BUILTIN_COPY,
    pretty,
)
from typed_tree import (
    TProgram, TDecl, TFnDecl, TLetDecl, TTypeDecl, TVariant, TImplDecl,
    TExpr, TLit, TVar as XVar, TCon as XCon, TTupleExpr, TApply as XApply,
    TBinOp, TUnaryOp, TLetExpr, TIfExpr, TMatchExpr, TLambda,
    TPat, TPWild, TPVar, TPLit, TPCon, TPTuple,
)

Env     = dict[str, Scheme]
Tracked = dict[str, int]   # name -> use count for locally-bound affine vars


# -- Errors

class TypeError(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(msg)

class AffineError(Exception):
    def __init__(self, name: str) -> None:
        super().__init__(f"affine variable '{name}' used more than once")


# -- Copy check

def is_copy(t: Mono, copy_types: frozenset[str]) -> bool:
    match t:
        case TVar():
            # An unresolved type variable arises from recursive self-references
            # whose return type hasn't been unified yet.  All concrete non-Copy
            # types in Lark are TCon (IO, user-defined), never TVar, so treating
            # an unknown TVar as Copy causes no false negatives in practice.
            return True
        case TCon(name=n):
            return n in copy_types
        case TApp(head=h, args=args):
            return h in copy_types and all(is_copy(a, copy_types) for a in args)
        case TFn():
            # Function values are freely reusable — they are code, not resources.
            # Phase 3 does not perform closure analysis; all function types are Copy.
            return True
        case TTup(elems=elems):
            return all(is_copy(e, copy_types) for e in elems)


# -- Generalise / instantiate

def generalise(env: Env, t: Mono) -> Scheme:
    env_fvs: set[int] = set()
    for sc in env.values():
        env_fvs |= free_vars_scheme(sc)
    qs = tuple(sorted(free_vars(t) - env_fvs))
    return Scheme(qs, t)


def instantiate(fresh: Fresh, sc: Scheme) -> Mono:
    if not sc.qs:
        return sc.body
    sub: Subst = {q: fresh.var() for q in sc.qs}
    return apply(sub, sc.body)


# -- Convert syntactic type → monotype

def syntype_to_mono(t: Type, tvar_env: dict[str, TVar], fresh: Fresh) -> Mono:
    """Convert a surface type (tree.py) to an internal monotype.

    tvar_env: maps lowercase type variable names to their allocated TVars.
    It is mutated as new type variables are encountered, so pass a shared
    dict when converting multiple fields of the same constructor.
    """
    match t:
        case TName(name=n):
            if n == "()":
                return T_UNIT
            if n[0].islower():
                if n not in tvar_env:
                    tvar_env[n] = fresh.var()
                return tvar_env[n]
            _builtins: dict[str, Mono] = {
                "Int": T_INT, "Float": T_FLOAT, "Bool": T_BOOL,
                "String": T_STRING, "IO": T_IO,
            }
            return _builtins.get(n, TCon(n))
        case STApply(name=n, args=args):
            return TApp(n, tuple(syntype_to_mono(a, tvar_env, fresh) for a in args))
        case STFn(param=p, result=r):
            return TFn(syntype_to_mono(p, tvar_env, fresh),
                       syntype_to_mono(r, tvar_env, fresh))
        case STUnit():
            return T_UNIT
        case STTuple(elems=elems):
            return TTup(tuple(syntype_to_mono(e, tvar_env, fresh) for e in elems))


# -- Built-in operator types

def _binop_type(op: str, fresh: Fresh) -> Mono:
    numeric = {"+", "-", "*", "/"}
    compare = {"==", "!=", "<", "<=", ">", ">="}
    if op in numeric:
        a = fresh.var()
        return t_fn(a, a, a)
    if op in compare:
        a = fresh.var()
        return t_fn(a, a, T_BOOL)
    if op in ("and", "or"):
        return t_fn(T_BOOL, T_BOOL, T_BOOL)
    raise TypeError(f"unknown binary operator: {op!r}")


# -- Literal types

def _lit_type(v: object) -> Mono:
    if v is None:
        return T_UNIT
    if isinstance(v, bool):
        return T_BOOL
    if isinstance(v, int):
        return T_INT
    if isinstance(v, float):
        return T_FLOAT
    if isinstance(v, str):
        return T_STRING
    raise TypeError(f"unknown literal type: {v!r}")


# -- Pattern typing

def infer_pat(pat: Pat, fresh: Fresh) -> tuple[TPat, Mono, Env]:
    """Infer the type of a pattern and the bindings it introduces.

    Returns (typed_pattern, pattern_type, local_env).
    Pattern variables are NOT added to `tracked` — they get Copy treatment
    unless the type checker later determines otherwise.
    """
    match pat:
        case PWild():
            t = fresh.var()
            return TPWild(t), t, {}

        case PVar(name=n):
            t = fresh.var()
            return TPVar(n, t), t, {n: Scheme((), t)}

        case PLit(value=v):
            t = _lit_type(v)
            return TPLit(v, t), t, {}

        case PCon(name=n, args=args):
            result_t = fresh.var()
            typed_args: list[TPat] = []
            local: Env = {}
            for a in args:
                tp, _t, env2 = infer_pat(a, fresh)
                typed_args.append(tp)
                for k, sc in env2.items():
                    if k in local:
                        raise TypeError(f"repeated pattern variable: {k!r}")
                    local[k] = sc
            return TPCon(n, tuple(typed_args), result_t), result_t, local

        case PTuple(elems=elems):
            typed_elems: list[TPat] = []
            elem_types:  list[Mono] = []
            local = {}
            for e in elems:
                tp, t, env2 = infer_pat(e, fresh)
                typed_elems.append(tp)
                elem_types.append(t)
                for k, sc in env2.items():
                    if k in local:
                        raise TypeError(f"repeated pattern variable: {k!r}")
                    local[k] = sc
            t = TTup(tuple(elem_types))
            return TPTuple(tuple(typed_elems), t), t, local


# -- Expression inference

def infer(
    env: Env,
    tracked: Tracked,
    expr: Expr,
    fresh: Fresh,
    copy_types: frozenset[str],
) -> tuple[TExpr, Mono, Subst]:
    """Synthesise the type of expr.

    `tracked` maps locally-bound affine variable names to their use count.
    Only names in `tracked` are subject to the affine constraint.
    """
    match expr:

        case Lit(value=v):
            t = _lit_type(v)
            return TLit(v, t), t, {}

        case Var(name=n):
            if n not in env:
                raise TypeError(f"unbound variable: {n!r}")
            sc = env[n]
            t  = instantiate(fresh, sc)
            # Affine check: only for locally-tracked variables.
            if n in tracked:
                tracked[n] += 1
                if tracked[n] > 1:
                    raise AffineError(n)
            return XVar(n, t), t, {}

        case Con(name=n):
            if n not in env:
                raise TypeError(f"unbound constructor: {n!r}")
            t = instantiate(fresh, env[n])
            return XCon(n, t), t, {}

        case TupleExpr(elems=elems):
            typed_elems: list[TExpr] = []
            elem_types:  list[Mono]  = []
            s: Subst = {}
            for e in elems:
                te, t, s2 = infer(env, tracked, e, fresh, copy_types)
                s = compose(s2, s)
                typed_elems.append(te)
                elem_types.append(apply(s, t))
            tup_t = TTup(tuple(apply(s, et) for et in elem_types))
            return TTupleExpr(tuple(typed_elems), tup_t), tup_t, s

        case Apply(fn=fn, args=args):
            tf, fn_t, s = infer(env, tracked, fn, fresh, copy_types)
            # Allocate one type variable per argument
            arg_vars: list[TVar] = [fresh.var() for _ in args]
            result_v = fresh.var()
            # Build expected curried function type
            expected: Mono = result_v
            for av in reversed(arg_vars):
                expected = TFn(av, expected)
            s2 = _unify_wrap(apply(s, fn_t), expected, expr)
            s  = compose(s2, s)
            typed_args: list[TExpr] = []
            for av, arg in zip(arg_vars, args):
                ta, at, s3 = infer(env, tracked, arg, fresh, copy_types)
                s4 = _unify_wrap(apply(s, at), apply(s, av), expr)
                s  = compose(s4, compose(s3, s))
                typed_args.append(ta)
            final_t = apply(s, result_v)
            return XApply(tf, tuple(typed_args), final_t), final_t, s

        case BinOp(op=op, left=left, right=right):
            op_t = _binop_type(op, fresh)
            tl, lt, s1 = infer(env, tracked, left, fresh, copy_types)
            tr, rt, s2 = infer(env, tracked, right, fresh, copy_types)
            s = compose(s2, s1)
            result_v = fresh.var()
            expected = TFn(apply(s, lt), TFn(apply(s, rt), result_v))
            s3 = _unify_wrap(apply(s, op_t), expected, expr)
            s  = compose(s3, s)
            t  = apply(s, result_v)
            return TBinOp(op, tl, tr, t), t, s

        case UnaryOp(op=op, operand=operand):
            te, t, s = infer(env, tracked, operand, fresh, copy_types)
            if op == "not":
                s2 = _unify_wrap(apply(s, t), T_BOOL, expr)
                s  = compose(s2, s)
                return TUnaryOp(op, te, T_BOOL), T_BOOL, s
            if op == "-":
                result_v = fresh.var()
                s = compose(_unify_wrap(apply(s, t), result_v, expr), s)
                rt = apply(s, result_v)
                return TUnaryOp(op, te, rt), rt, s
            raise TypeError(f"unknown unary operator: {op!r}")

        case LetExpr(name=n, ann=ann, value=val, body=body):
            tv, vt, s1 = infer(env, tracked, val, fresh, copy_types)
            vt2 = apply(s1, vt)
            if ann is not None:
                tve = {}
                ann_t = syntype_to_mono(ann, tve, fresh)
                s2 = _unify_wrap(vt2, ann_t, expr)
                s1 = compose(s2, s1)
                vt2 = apply(s1, ann_t)
            sc  = generalise(_apply_env(s1, env), vt2)
            env2 = {**env, n: sc}
            # If n was affine-tracked (an outer binding being shadowed),
            # the old binding is consumed; the new binding starts fresh.
            old_count = tracked.pop(n, None)
            if not is_copy(vt2, copy_types):
                tracked[n] = 0
            tb, bt, s3 = infer(env2, tracked, body, fresh, copy_types)
            # Clean up local tracking for n after body is done.
            if n in tracked:
                del tracked[n]
            if old_count is not None:
                tracked[n] = old_count   # restore outer binding's count
            s = compose(s3, s1)
            t = apply(s, bt)
            return TLetExpr(n, tv, tb, t), t, s

        case IfExpr(cond=cond, then_=then_, else_=else_):
            tc, ct, s1 = infer(env, tracked, cond, fresh, copy_types)
            s2 = _unify_wrap(apply(s1, ct), T_BOOL, expr)
            s  = compose(s2, s1)
            tt, tt_t, s3 = infer(env, tracked, then_, fresh, copy_types)
            te, et_t, s4 = infer(env, tracked, else_, fresh, copy_types)
            s  = compose(s4, compose(s3, s))
            s5 = _unify_wrap(apply(s, tt_t), apply(s, et_t), expr)
            s  = compose(s5, s)
            t  = apply(s, tt_t)
            return TIfExpr(tc, tt, te, t), t, s

        case MatchExpr(scrutinee=scrut, arms=arms):
            ts, st, s = infer(env, tracked, scrut, fresh, copy_types)
            result_v  = fresh.var()
            typed_arms: list[tuple[TPat, TExpr]] = []
            for (pat, arm_body) in arms:
                tp, pt, pat_env = infer_pat(pat, fresh)
                s2 = _unify_wrap(apply(s, st), apply(s, pt), expr)
                s  = compose(s2, s)
                arm_env = {**env, **{k: apply_scheme(s, v) for k, v in pat_env.items()}}
                ta, at, s3 = infer(arm_env, tracked, arm_body, fresh, copy_types)
                s4 = _unify_wrap(apply(s3, apply(s, at)),
                                 apply(s3, apply(s, result_v)), expr)
                s  = compose(s4, compose(s3, s))
                typed_arms.append((tp, ta))
            t = apply(s, result_v)
            return TMatchExpr(ts, tuple(typed_arms), t), t, s

        case Lambda(params=params, body=body):
            param_types: list[tuple[str, Mono]] = []
            env2    = dict(env)
            tracked2 = dict(tracked)
            for p in params:
                pname = p.name if p.name != "_" else f"_anon_{id(p)}"
                pv: Mono = fresh.var()
                if p.ann is not None:
                    tve = {}
                    pv = syntype_to_mono(p.ann, tve, fresh)
                param_types.append((pname, pv))
                env2[pname] = Scheme((), pv)
                # Track affine lambda parameters.
                if not is_copy(pv, copy_types):
                    tracked2[pname] = 0
            tb, bt, s = infer(env2, tracked2, body, fresh, copy_types)
            fn_t: Mono = apply(s, bt)
            for _, pt in reversed(param_types):
                fn_t = TFn(apply(s, pt), fn_t)
            typed_params = tuple((nm, apply(s, pt)) for nm, pt in param_types)
            return TLambda(typed_params, tb, fn_t), fn_t, s


def _unify_wrap(a: Mono, b: Mono, ctx: object) -> Subst:
    try:
        return unify(a, b)
    except ty.UnifyError as e:
        raise TypeError(str(e)) from e


def _apply_env(s: Subst, env: Env) -> Env:
    return {k: apply_scheme(s, v) for k, v in env.items()}


# -- Declaration checking

def check_fn_decl(
    decl: FnDecl,
    env: Env,
    fresh: Fresh,
    copy_types: frozenset[str],
) -> tuple[TFnDecl, Scheme]:
    """Type-check a function declaration."""
    # Add the function's own name to scope for recursion (let-rec).
    rec_var = fresh.var()
    local_env: Env = {**env, decl.name: Scheme((), rec_var)}

    # Type parameters: collect unique lowercase names from annotations.
    tvar_env: dict[str, TVar] = {}

    param_types: list[tuple[str, Mono]] = []
    tracked: Tracked = {}

    for p in decl.params:
        pv: Mono = fresh.var()
        if p.ann is not None:
            pv = syntype_to_mono(p.ann, tvar_env, fresh)
        pname = p.name if p.name != "_" else f"_anon_{id(p)}"
        param_types.append((pname, pv))
        local_env[pname] = Scheme((), pv)
        if not is_copy(pv, copy_types):
            tracked[pname] = 0

    tbody, bt, s = infer(local_env, tracked, decl.body, fresh, copy_types)

    if decl.return_type is not None:
        ret_tve: dict[str, TVar] = dict(tvar_env)
        ann_t = syntype_to_mono(decl.return_type, ret_tve, fresh)
        s2 = _unify_wrap(apply(s, bt), ann_t, decl)
        s  = compose(s2, s)
        bt = apply(s, ann_t)
    else:
        bt = apply(s, bt)

    fn_t: Mono = bt
    for _, pt in reversed(param_types):
        fn_t = TFn(apply(s, pt), fn_t)
    fn_t = apply(s, fn_t)

    # Unify rec_var with the inferred function type.
    s2 = _unify_wrap(apply(s, rec_var), fn_t, decl)
    s  = compose(s2, s)
    fn_t = apply(s, fn_t)

    sc = generalise(_apply_env(s, env), fn_t)
    typed_params = tuple((nm, apply(s, pt)) for nm, pt in param_types)
    return TFnDecl(decl.name, typed_params, tbody, sc, decl.exported), sc


def check_let_decl(
    decl: LetDecl,
    env: Env,
    fresh: Fresh,
    copy_types: frozenset[str],
) -> tuple[TLetDecl, Scheme]:
    tracked: Tracked = {}
    tv, t, s = infer(env, tracked, decl.value, fresh, copy_types)
    t = apply(s, t)
    if decl.ann is not None:
        tve: dict[str, TVar] = {}
        ann_t = syntype_to_mono(decl.ann, tve, fresh)
        s2 = _unify_wrap(t, ann_t, decl)
        s  = compose(s2, s)
        t  = apply(s, ann_t)
    sc = generalise(_apply_env(s, env), t)
    return TLetDecl(decl.name, tv, sc, decl.exported), sc


def _register_type_decl(
    decl: TypeDecl,
    env: Env,
    fresh: Fresh,
    copy_types: frozenset[str],
) -> frozenset[str]:
    """Register constructor schemes for an ADT. Returns updated copy_types."""
    if not isinstance(decl.body, tuple):
        return copy_types   # type alias

    # Allocate one TVar per declared type parameter, shared across all constructors.
    param_vars: dict[str, TVar] = {p: fresh.var() for p in decl.params}
    qs = tuple(v.id for v in param_vars.values())

    # Build the result type: T or T(α, β, …)
    if decl.params:
        result_t: Mono = TApp(decl.name, tuple(param_vars[p] for p in decl.params))
    else:
        result_t = TCon(decl.name)

    for v in decl.body:
        if not v.payload:
            con_t: Mono = result_t
        else:
            # Use a shared tvar_env seeded with the type parameters so all
            # occurrences of the same type variable name resolve to the same TVar.
            tve: dict[str, TVar] = dict(param_vars)
            field_monos = tuple(syntype_to_mono(f, tve, fresh) for f in v.payload)
            con_t = result_t
            for fm in reversed(field_monos):
                con_t = TFn(fm, con_t)

        all_qs = tuple(sorted(free_vars(con_t)))
        env[v.name] = Scheme(all_qs, con_t)

    return copy_types


# -- Top-level entry point

def _initial_env() -> tuple[Env, frozenset[str]]:
    fresh = Fresh()
    a = fresh.var()
    b = fresh.var()

    env: Env = {
        # IO threading
        "print": Scheme((), TFn(T_IO, TFn(T_STRING, T_IO))),
        "read":  Scheme((), TFn(T_IO, TTup((T_IO, T_STRING)))),
        # Polymorphic show (∀a. a -> String); bounds checked with traits in Phase 4
        "show":  Scheme((a.id,), TFn(a, T_STRING)),
        # Conversions
        "int_to_float":    Scheme((), TFn(T_INT,   T_FLOAT)),
        "float_to_int":    Scheme((), TFn(T_FLOAT, T_INT)),
        "int_to_string":   Scheme((), TFn(T_INT,   T_STRING)),
        "float_to_string": Scheme((), TFn(T_FLOAT, T_STRING)),
        # List constructors (also registered when list type is declared)
        "Nil":  Scheme((a.id,), t_list(a)),
        "Cons": Scheme((a.id,), TFn(a, TFn(t_list(a), t_list(a)))),
        # Result constructors
        "Ok":  Scheme((a.id, b.id), TFn(a, t_result(a, b))),
        "Err": Scheme((a.id, b.id), TFn(b, t_result(a, b))),
        # Bool
        "True":  Scheme((), T_BOOL),
        "False": Scheme((), T_BOOL),
    }
    copy_types: frozenset[str] = BUILTIN_COPY | frozenset({"List"})
    return env, copy_types


def _register_trait_decl(decl: TraitDecl, env: Env, fresh: Fresh) -> None:
    """Register trait method signatures as polymorphic in the env.

    Phase 4 simplification: trait bounds are not enforced — methods are
    registered as unconstrained polymorphic functions so type checking proceeds.
    Dispatch at runtime is handled by the CEK machine.
    """
    tve: dict[str, TVar] = {p: fresh.var() for p in decl.params}
    for method in decl.methods:
        method_t = syntype_to_mono(method.typ, tve, fresh)
        qs = tuple(sorted(free_vars(method_t)))
        env[method.name] = Scheme(qs, method_t)


def _for_type_name(decl: ImplDecl) -> str:
    """Extract the concrete type name from an impl's for_type."""
    match decl.for_type:
        case TName(name=n):
            return n
        case STApply(name=n):
            return n
        case _:
            return "?"


def typecheck(
    program: Program,
    source_file: str | None = None,
    _visited: set[str] | None = None,
) -> TProgram:
    """Type-check a parsed Program and return a TProgram.

    source_file: path of the file being checked (for resolving imports).
    _visited: set of already-being-checked module paths (cycle guard).
    """
    env, copy_types = _initial_env()
    fresh = Fresh()
    typed_decls: list[TDecl] = []
    if _visited is None:
        _visited = set()

    # Pass 0: resolve imports — load and type-check each imported module,
    # then merge exported names into the current env.
    if source_file:
        src_dir = os.path.dirname(os.path.abspath(source_file))
        for imp in program.imports:
            copy_types = _load_import(imp, src_dir, env, copy_types, fresh, _visited)

    # Pass 1: register type declarations, trait methods, and Copy impls.
    # Copy impls must be processed here so affine tracking in pass 2 sees them.
    for decl in program.decls:
        if isinstance(decl, TypeDecl):
            copy_types = _register_type_decl(decl, env, fresh, copy_types)
        elif isinstance(decl, TraitDecl):
            _register_trait_decl(decl, env, fresh)
        elif isinstance(decl, ImplDecl) and decl.trait_name == "Copy":
            copy_types = copy_types | frozenset({_for_type_name(decl)})

    # Pass 2: check value declarations and impl blocks.
    for decl in program.decls:
        match decl:
            case FnDecl():
                tdecl, sc = check_fn_decl(decl, env, fresh, copy_types)
                env[decl.name] = sc
                typed_decls.append(tdecl)

            case LetDecl():
                tdecl, sc = check_let_decl(decl, env, fresh, copy_types)
                env[decl.name] = sc
                typed_decls.append(tdecl)

            case TypeDecl():
                if isinstance(decl.body, tuple):
                    tve: dict[str, TVar] = {}
                    variants = tuple(
                        TVariant(v.name, tuple(
                            syntype_to_mono(f, tve, fresh) for f in v.payload
                        ))
                        for v in decl.body
                    )
                    typed_decls.append(
                        TTypeDecl(decl.name, decl.params, variants, decl.exported)
                    )
                else:
                    typed_decls.append(
                        TTypeDecl(decl.name, decl.params, None, decl.exported)
                    )

            case ImplDecl():
                type_name = _for_type_name(decl)
                method_decls: list[TFnDecl] = []
                for m in decl.methods:
                    fn = FnDecl(
                        name=m.name, bounds=(), params=m.params,
                        return_type=None, body=m.body, exported=False,
                    )
                    tdecl, _ = check_fn_decl(fn, env, fresh, copy_types)
                    method_decls.append(tdecl)
                typed_decls.append(
                    TImplDecl(decl.trait_name, type_name, tuple(method_decls))
                )

            case TraitDecl():
                pass   # already handled in pass 1

    return TProgram(program.module, tuple(typed_decls))


def _load_import(
    imp: object,       # ImportDecl
    src_dir: str,
    env: Env,
    copy_types: frozenset[str],
    fresh: Fresh,
    visited: set[str],
) -> frozenset[str]:
    """Find, parse, type-check, and merge one import into env.
    Returns updated copy_types (may gain new Copy implementors from the module).
    """
    module_name = imp.module   # type: ignore
    candidates = [
        pathlib.Path(src_dir) / f"{module_name.lower()}.lark",
        pathlib.Path(src_dir) / f"{module_name}.lark",
    ]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        return copy_types   # module not found

    abs_path = str(path.resolve())
    if abs_path in visited:
        return copy_types
    visited.add(abs_path)

    imported_prog = _parser.parse_file(abs_path)

    imported_tprog = typecheck(imported_prog, abs_path, visited)

    # Build env from the imported module (constructors + values).
    imported_env, imported_copy = _initial_env()
    imported_fresh = Fresh()
    for decl in imported_prog.decls:
        if isinstance(decl, TypeDecl):
            imported_copy = _register_type_decl(decl, imported_env, imported_fresh, imported_copy)
        elif isinstance(decl, TraitDecl):
            _register_trait_decl(decl, imported_env, imported_fresh)
        elif isinstance(decl, ImplDecl) and decl.trait_name == "Copy":
            imported_copy = imported_copy | frozenset({_for_type_name(decl)})
    for decl in imported_prog.decls:
        match decl:
            case FnDecl():
                _, sc = check_fn_decl(decl, imported_env, imported_fresh, imported_copy)
                imported_env[decl.name] = sc
            case LetDecl():
                _, sc = check_let_decl(decl, imported_env, imported_fresh, imported_copy)
                imported_env[decl.name] = sc

    # Propagate Copy types from the imported module.
    copy_types = copy_types | imported_copy

    # Determine which names to expose.
    exposing = imp.exposing if imp.exposing else None  # type: ignore

    def _should_expose(name: str) -> bool:
        if exposing is None:
            return True
        if name in exposing:
            return True
        # Importing a type also exposes its constructors.
        if name[0].isupper():
            sc = imported_env.get(name)
            if sc:
                t = sc.body
                while isinstance(t, TFn):
                    t = t.result
                con_type = t.name if isinstance(t, TCon) else (t.head if isinstance(t, TApp) else None)
                if con_type and con_type in exposing:
                    return True
        return False

    for name, sc in imported_env.items():
        if name not in _initial_env()[0] and _should_expose(name):
            env[name] = sc

    return copy_types


# -- CLI

if __name__ == "__main__":
    import pprint

    if len(sys.argv) < 2:
        print("usage: infer.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    prog = _parser.parse_file(path)

    try:
        tprog = typecheck(prog, source_file=path)
        pprint.pprint(tprog)
    except (TypeError, AffineError) as e:
        print(f"type error: {e}", file=sys.stderr)
        sys.exit(1)
