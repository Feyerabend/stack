"""
Lark lowerer — typed AST  →  TAC.

Entry point:
    lower(tprog: TProgram) -> TAC

Design
------
Every TExpr node is lowered by lower_expr(), which appends instructions to
the current Function and returns the Val (Tmp or Const) that holds the result.

Closures
--------
TLambda nodes are closure-converted inline:
  1. Compute the set of free variables (vars in body not bound by the lambda's
     own parameters or any enclosing let/match binding added since the
     enclosing function started).
  2. If there are no free variables: lift to a top-level function; emit
     IAllocClosure with an empty captured list (the runtime can optimise
     the env away).
  3. If there are free variables: lift to a top-level function with an
     extra leading `env` parameter; emit IAllocClosure with the free values.
     Inside the lifted function, each free variable is loaded with IGetField
     from env at the start.

The lifted function name is unique: <enclosing_fn>$lam<n>.

Pattern matching
----------------
Each match arm generates:
  • a tag-check / literal-check that jumps to the arm body or falls through
    to the next arm
  • binding of pattern variables via IGetField (for constructor fields)
  • the arm body, assigned to a shared destination temporary

Builtins
--------
print, show, read, and the conversion builtins are lowered as ICall nodes.
The callee names match what the runtime library exports.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Union
import ty

from typed_tree import (
    TProgram, TFnDecl, TLetDecl, TTypeDecl, TImplDecl,
    TExpr, TLit, TVar, TCon, TTupleExpr, TApply, TBinOp, TUnaryOp,
    TLetExpr, TIfExpr, TMatchExpr, TLambda,
    TPat, TPWild, TPVar, TPLit, TPCon, TPTuple,
)
from tac import (
    TAC, Function, Val, Tmp, Const,
    IAssign, IBinOp, IUnary, ICall, IClosureCall,
    IReturn, ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
)

# Names of builtin functions — lowered as direct ICall nodes.
_BUILTINS: frozenset[str] = frozenset({
    "print", "read", "read_all", "show",
    "int_to_float", "float_to_int", "int_to_string", "float_to_string",
    "__show_float", "__show_bool",
    "__float_add", "__float_sub", "__float_mul", "__float_div",
    "__float_lt", "__float_le", "__float_gt", "__float_ge",
    "__str_concat",
    # stdlib built-ins
    "string_length",
    "int_abs", "float_abs", "float_sqrt", "float_floor", "float_ceil",
    # string-decomposition prims (self-host M0): scalar-returning ones lower to a
    # plain ICall + runtime stub; string_to_int/string_to_float return a Result
    # and are special-cased in _lower_apply (see _lower_string_to_result).
    "string_index", "string_slice", "char_to_string", "float_to_bits",
    "string_to_int", "string_to_float",
})


# -- Free-variable analysis --

def _free(expr: TExpr, bound: frozenset[str]) -> frozenset[str]:
    """Return the set of names used in expr that are not in bound."""
    match expr:
        case TVar(name=n):
            return frozenset({n}) - bound
        case TCon() | TLit():
            return frozenset()
        case TTupleExpr(elems=es):
            return frozenset().union(*(_free(e, bound) for e in es))
        case TApply(fn=f, args=args):
            return _free(f, bound) | frozenset().union(*(_free(a, bound) for a in args))
        case TBinOp(left=l, right=r):
            return _free(l, bound) | _free(r, bound)
        case TUnaryOp(operand=e):
            return _free(e, bound)
        case TLetExpr(name=n, value=v, body=b):
            return _free(v, bound) | _free(b, bound | {n})
        case TIfExpr(cond=c, then_=t, else_=e):
            return _free(c, bound) | _free(t, bound) | _free(e, bound)
        case TMatchExpr(scrutinee=s, arms=arms):
            fvs = _free(s, bound)
            for pat, body in arms:
                fvs |= _free(body, bound | _pat_bound(pat))
            return fvs
        case TLambda(params=params, body=b):
            inner_bound = bound | frozenset(n for n, _ in params)
            return _free(b, inner_bound)
        case _:
            return frozenset()

def _pat_bound(pat: TPat) -> frozenset[str]:
    match pat:
        case TPWild() | TPLit():    return frozenset()
        case TPVar(name=n):         return frozenset({n})
        case TPCon(args=subs):      return frozenset().union(*(_pat_bound(s) for s in subs))
        case TPTuple(elems=es):     return frozenset().union(*(_pat_bound(e) for e in es))
        case _:                     return frozenset()


# -- Main lowerer --

class Lowerer:
    def __init__(self) -> None:
        self._tac          = TAC()
        self._global_fns:  set[str] = set(_BUILTINS)
        self._lambda_ctr:  int      = 0
        self._type_tags:   dict[str, list[str]] = {}  # type_name -> [constructor tags]
        self._trait_impls: dict[str, list[str]] = {}  # method_name -> [type_names]
        self._global_lets: set[str]             = set()  # top-level let names
        self._show_impls:  dict[str, str]       = {}  # type_name -> "show$TypeName"
        self._global_arity: dict[str, int]      = {}  # user fn/method name -> #params

    # -- Program entry --

    def lower(self, tprog: TProgram) -> TAC:
        # Collect type declarations, trait impls, and global let names.
        for decl in tprog.decls:
            if isinstance(decl, TTypeDecl) and decl.variants is not None:
                self._type_tags[decl.name] = [v.name for v in decl.variants]
            elif isinstance(decl, TImplDecl) and decl.trait_name != "Copy":
                for m in decl.methods:
                    self._trait_impls.setdefault(m.name, []).append(decl.for_type)
            elif isinstance(decl, TLetDecl):
                self._global_lets.add(decl.name)

        # Register all top-level function names before lowering bodies so
        # mutual recursion and forward references work.
        for decl in tprog.decls:
            if isinstance(decl, TFnDecl):
                self._global_fns.add(decl.name)
                self._global_arity[decl.name] = len(decl.params)
            elif isinstance(decl, TImplDecl):
                for m in decl.methods:
                    mn = m.name + "$" + decl.for_type
                    self._global_fns.add(mn)
                    self._global_arity[mn] = len(m.params)

        # Register trait dispatch stubs as global functions so call sites
        # emit ICall("describe", [x]) instead of IClosureCall(Tmp("describe"), x).
        for method_name in self._trait_impls:
            self._global_fns.add(method_name)

        # Compute show_impls before lowering so _lower_apply can route show(x)
        # to show$TypeName when x has a user-defined Show impl.
        self._show_impls = {
            tn: f"show${tn}"
            for tn in self._trait_impls.get("show", [])
        }

        # Collect top-level let declarations; they become a __global_init__ fn.
        global_lets: list[tuple[str, object]] = [
            (d.name, d.value)
            for d in tprog.decls
            if isinstance(d, TLetDecl)
        ]
        if global_lets:
            init_fn  = Function("__global_init__", ())
            init_env: dict[str, Val] = {}
            for gname, gexpr in global_lets:
                v = self._expr(gexpr, init_fn, init_env)
                dst = Tmp(gname)
                init_fn.emit(IAssign(dst, v))
                init_env[gname] = dst
            init_fn.emit(IReturn(Const(None)))
            self._tac.add(init_fn)

        for decl in tprog.decls:
            match decl:
                case TFnDecl():
                    self._tac.add(self._lower_fn(decl))
                case TImplDecl(for_type=ft, methods=methods):
                    for m in methods:
                        fn = self._lower_impl_method(m, ft)
                        self._tac.add(fn)
                case _:
                    pass   # TTypeDecl / TLetDecl: handled above

        # Generate one dispatch stub per trait method.
        # Skip methods that are builtins — they are routed statically in _lower_apply.
        for method_name, type_names in self._trait_impls.items():
            if method_name in _BUILTINS:
                continue
            self._tac.add(self._make_dispatch_stub(method_name, type_names))

        self._tac.global_names = frozenset(self._global_lets)
        return self._tac

    # -- Function declarations --

    def _lower_fn(self, decl: TFnDecl) -> Function:
        params = tuple(n for n, _ in decl.params)
        fn  = Function(decl.name, params)
        env: dict[str, Val] = {n: Tmp(n) for n in params}
        result = self._expr(decl.body, fn, env)
        fn.emit(IReturn(result))
        return fn

    def _lower_impl_method(self, decl: TFnDecl, for_type: str) -> Function:
        """Trait implementation method — mangled name: method$Type."""
        mangled = decl.name + "$" + for_type
        params  = tuple(n for n, _ in decl.params)
        fn  = Function(mangled, params)
        env: dict[str, Val] = {n: Tmp(n) for n in params}
        result = self._expr(decl.body, fn, env)
        fn.emit(IReturn(result))
        return fn

    def _make_dispatch_stub(self, method: str, type_names: list[str]) -> Function:
        """Generate a runtime-dispatch function for a trait method.

        Checks the constructor tag of the argument against each implementing
        type's constructors and calls method$Type(x) for the first match.
        Falls through to __lark_match_fail if no type matches.
        """
        fn  = Function(method, ("x",))
        dst = fn.fresh("r")
        l_end = fn.label("dispatch_end")

        tag_tmp = fn.fresh("tag")
        fn.emit(IGetTag(tag_tmp, Tmp("x")))

        # Pre-generate one arm label per implementing type that has known constructors.
        arm_labels: dict[str, str] = {
            tn: fn.label(f"arm_{tn}")
            for tn in type_names
            if self._type_tags.get(tn)
        }

        # Emit tag-check chain: for each tag of each implementing type, jump to
        # the arm on match, otherwise fall through to the next check.
        for type_name in type_names:
            tags = self._type_tags.get(type_name, [])
            if not tags:
                continue
            l_arm = arm_labels[type_name]
            for tag in tags:
                eq_tmp = fn.fresh("eq")
                l_next = fn.label("nxt")
                fn.emit(IBinOp(eq_tmp, "==", tag_tmp, Const(tag)))
                fn.emit(ICondJump(eq_tmp, l_arm, l_next))
                fn.emit(ILabel(l_next))

        # No type matched.
        fn.emit(ICall(None, "__lark_match_fail", ()))

        # Arm bodies: call method$Type(x), assign to shared dst, jump to end.
        for type_name in type_names:
            if not self._type_tags.get(type_name):
                continue
            fn.emit(ILabel(arm_labels[type_name]))
            call_dst = fn.fresh("call_r")
            fn.emit(ICall(call_dst, f"{method}${type_name}", (Tmp("x"),)))
            fn.emit(IAssign(dst, call_dst))
            fn.emit(IJump(l_end))

        fn.emit(ILabel(l_end))
        fn.emit(IReturn(dst))
        return fn

    # -- Expression lowering --

    def _expr(self, expr: TExpr, fn: Function, env: dict[str, Val]) -> Val:
        """Lower expr, emit instructions into fn, return the result Val."""
        match expr:

            case TLit(value=v):
                return Const(v)

            case TVar(name=n):
                if n in env:
                    return env[n]
                # Global function used as a value.  A closure is invoked with
                # the (env, arg) convention (a0=env, a1=arg), but a top-level fn
                # `f(x)` expects its first arg in a0 — so pointing a closure
                # record straight at `f` feeds it the record instead of the arg.
                # Eta-expand instead: lower `f` as `fn(a0,..,ak) => f(a0,..,ak)`,
                # reusing the (already correct, curried) lambda-lifting path.  We
                # only do this when the arity is known (user fns / impl methods);
                # builtins and trait stubs keep the legacy direct wrap.
                if n in self._global_arity and self._global_arity[n] >= 1:
                    k = self._global_arity[n]
                    ps = tuple((f"$eta{i}", ty.T_UNIT) for i in range(k))
                    body: TExpr = TApply(
                        TVar(n, ty.T_UNIT),
                        tuple(TVar(p, ty.T_UNIT) for p, _ in ps),
                        ty.T_UNIT,
                    )
                    return self._lower_lambda(ps, body, fn, env)
                if n in self._global_fns:
                    dst = fn.fresh("fn")
                    fn.emit(IAllocClosure(dst, n, ()))
                    return dst
                if n in self._global_lets:
                    # asm resolves top-level `let` names via the global-var table.
                    return Tmp(n)
                # Reached only when infer accepted a name the lowerer does not
                # know — almost always a builtin present in cek/infer but missing
                # from lower._BUILTINS (and hence the whole RV32 backend). Fail
                # loudly HERE: the old silent `return Tmp(n)` emitted a read of an
                # unassigned register, which downstream became a jump to garbage
                # (this is exactly how 24_stringprims used to crash).
                raise RuntimeError(
                    f"lower: unbound name {n!r} — not a param, global fn, or "
                    f"top-level let. If it is a builtin, register it in "
                    f"lower._BUILTINS AND the RV32 backend (riscv_asm.RUNTIME_STUBS "
                    f"+ riscv_vm stub_map + tac_vm._BUILTINS).")

            case TCon(name=n):
                if n == "True":  return Const(True)
                if n == "False": return Const(False)
                # Nullary user constructor.
                dst = fn.fresh()
                fn.emit(IAlloc(dst, n, ()))
                return dst

            case TTupleExpr(elems=()):
                return Const(None)   # unit

            case TTupleExpr(elems=elems):
                fields = tuple(self._expr(e, fn, env) for e in elems)
                dst = fn.fresh()
                fn.emit(IAlloc(dst, "()", fields))
                return dst

            case TBinOp(op=op, left=l, right=r, typ=t):
                lv = self._expr(l, fn, env)
                rv = self._expr(r, fn, env)
                dst = fn.fresh()
                op = {"and": "&&", "or": "||"}.get(op, op)
                if op == '+' and t == ty.T_STRING:
                    fn.emit(ICall(dst, '__str_concat', [lv, rv]))
                elif t == ty.T_FLOAT and op in ('+', '-', '*', '/'):
                    _float_arith = {'+':"__float_add", '-':"__float_sub",
                                    '*':"__float_mul", '/':"__float_div"}[op]
                    fn.emit(ICall(dst, _float_arith, [lv, rv]))
                elif t == ty.T_BOOL and l.typ == ty.T_FLOAT and op in ('<', '<=', '>', '>='):
                    _float_cmp = {'<':"__float_lt", '<=':"__float_le",
                                  '>':"__float_gt", '>=':"__float_ge"}[op]
                    fn.emit(ICall(dst, _float_cmp, [lv, rv]))
                else:
                    fn.emit(IBinOp(dst, op, lv, rv))
                return dst

            case TUnaryOp(op=op, operand=e):
                v   = self._expr(e, fn, env)
                dst = fn.fresh()
                fn.emit(IUnary(dst, op, v))
                return dst

            case TLetExpr(name=n, value=v_expr, body=body):
                v       = self._expr(v_expr, fn, env)
                new_env = {**env, n: v}
                return self._expr(body, fn, new_env)

            case TIfExpr(cond=c, then_=t, else_=e):
                return self._lower_if(c, t, e, fn, env)

            case TMatchExpr(scrutinee=s, arms=arms):
                return self._lower_match(s, arms, fn, env)

            case TApply(fn=fn_expr, args=args):
                return self._lower_apply(fn_expr, args, fn, env)

            case TLambda(params=params, body=body):
                return self._lower_lambda(params, body, fn, env)

            case _:
                raise RuntimeError(f"lower: unhandled expr {type(expr).__name__}")

    # -- If / else --

    def _lower_if(
        self, cond: TExpr, then_: TExpr, else_: TExpr,
        fn: Function, env: dict[str, Val],
    ) -> Val:
        cv     = self._expr(cond, fn, env)
        l_then = fn.label("then")
        l_else = fn.label("else")
        l_end  = fn.label("end")
        dst    = fn.fresh("r")

        fn.emit(ICondJump(cv, l_then, l_else))

        fn.emit(ILabel(l_then))
        tv = self._expr(then_, fn, env)
        fn.emit(IAssign(dst, tv))
        fn.emit(IJump(l_end))

        fn.emit(ILabel(l_else))
        ev = self._expr(else_, fn, env)
        fn.emit(IAssign(dst, ev))
        fn.emit(IJump(l_end))

        fn.emit(ILabel(l_end))
        return dst

    # -- Match --

    def _lower_match(
        self, scrut_expr: TExpr,
        arms: tuple[tuple[TPat, TExpr], ...],
        fn: Function, env: dict[str, Val],
    ) -> Val:
        sv  = self._expr(scrut_expr, fn, env)
        dst = fn.fresh("r")
        l_end = fn.label("match_end")

        for pat, body in arms:
            l_body = fn.label("arm")
            l_next = fn.label("next")

            # Emit checks: fall through to l_next if no match.
            self._pat_check(pat, sv, fn, l_body, l_next)

            fn.emit(ILabel(l_body))
            arm_env = dict(env)
            self._pat_bind(pat, sv, fn, arm_env)
            body_val = self._expr(body, fn, arm_env)
            fn.emit(IAssign(dst, body_val))
            fn.emit(IJump(l_end))

            fn.emit(ILabel(l_next))

        # Dead code if match is exhaustive, but emit a trap anyway.
        fn.emit(ICall(None, "__lark_match_fail", ()))
        fn.emit(ILabel(l_end))
        return dst

    def _pat_check(
        self, pat: TPat, sv: Val,
        fn: Function, l_match: str, l_fail: str,
    ) -> None:
        """Emit a check: jump to l_match if pat matches sv, else l_fail."""
        match pat:
            case TPWild() | TPVar():
                fn.emit(IJump(l_match))

            case TPLit(value=v):
                cmp = fn.fresh("eq")
                fn.emit(IBinOp(cmp, "==", sv, Const(v)))
                fn.emit(ICondJump(cmp, l_match, l_fail))

            case TPCon(name=tag, args=sub_pats):
                if tag in ("True", "False") and not sub_pats:
                    cmp = fn.fresh("eq")
                    fn.emit(IBinOp(cmp, "==", sv, Const(tag == "True")))
                    fn.emit(ICondJump(cmp, l_match, l_fail))
                    return
                tag_tmp = fn.fresh("tag")
                fn.emit(IGetTag(tag_tmp, sv))
                tag_ok = fn.fresh("tag_ok")
                fn.emit(IBinOp(tag_ok, "==", tag_tmp, Const(tag)))
                if not sub_pats:
                    fn.emit(ICondJump(tag_ok, l_match, l_fail))
                else:
                    # Also need to check sub-patterns — chain checks.
                    l_tag_ok = fn.label("tag_ok")
                    fn.emit(ICondJump(tag_ok, l_tag_ok, l_fail))
                    fn.emit(ILabel(l_tag_ok))
                    # Check each sub-pattern against the corresponding field.
                    for i, sp in enumerate(sub_pats):
                        field_tmp = fn.fresh("fld")
                        fn.emit(IGetField(field_tmp, sv, i))
                        l_sub_ok = fn.label("sub")
                        self._pat_check(sp, field_tmp, fn, l_sub_ok, l_fail)
                        fn.emit(ILabel(l_sub_ok))
                    fn.emit(IJump(l_match))

            case TPTuple(elems=sub_pats):
                for i, sp in enumerate(sub_pats):
                    field_tmp = fn.fresh("fld")
                    fn.emit(IGetField(field_tmp, sv, i))
                    l_sub_ok = fn.label("sub")
                    self._pat_check(sp, field_tmp, fn, l_sub_ok, l_fail)
                    fn.emit(ILabel(l_sub_ok))
                fn.emit(IJump(l_match))

    def _pat_bind(
        self, pat: TPat, sv: Val,
        fn: Function, env: dict[str, Val],
    ) -> None:
        """Add pattern-bound names to env, emitting IGetField as needed."""
        match pat:
            case TPWild() | TPLit():
                pass
            case TPVar(name=n):
                env[n] = sv
            case TPCon(args=sub_pats):
                for i, sp in enumerate(sub_pats):
                    field_tmp = fn.fresh("f")
                    fn.emit(IGetField(field_tmp, sv, i))
                    self._pat_bind(sp, field_tmp, fn, env)
            case TPTuple(elems=sub_pats):
                for i, sp in enumerate(sub_pats):
                    field_tmp = fn.fresh("f")
                    fn.emit(IGetField(field_tmp, sv, i))
                    self._pat_bind(sp, field_tmp, fn, env)

    # -- Application --

    def _lower_apply(
        self, fn_expr: TExpr, args: tuple[TExpr, ...],
        fn: Function, env: dict[str, Val],
    ) -> Val:
        match fn_expr:
            case TVar(name=n) if n in ("string_to_int", "string_to_float"):
                # Result-returning prims: a raw stub parses and returns a heap
                # pair [flag, payload]; we wrap it in Ok/Err here so the tag ids
                # get numbered by asm._collect_tags exactly like user Ok/Err.
                return self._lower_string_to_result(n, args, fn, env)

            case TVar(name=n) if n in self._global_fns:
                # Static call — all args at once.
                arg_vals = tuple(self._expr(a, fn, env) for a in args)
                dst = fn.fresh()
                if n == 'show' and args:
                    # Route show to type-specific stubs using static type info.
                    typ = args[0].typ
                    if typ == ty.T_FLOAT:
                        fn.emit(ICall(dst, '__show_float', arg_vals))
                    elif typ == ty.T_BOOL:
                        fn.emit(ICall(dst, '__show_bool', arg_vals))
                    elif isinstance(typ, ty.TCon) and typ.name in self._show_impls:
                        fn.emit(ICall(dst, self._show_impls[typ.name], arg_vals))
                    elif isinstance(typ, ty.TApp) and typ.head in self._show_impls:
                        fn.emit(ICall(dst, self._show_impls[typ.head], arg_vals))
                    else:
                        fn.emit(ICall(dst, 'show', arg_vals))
                else:
                    fn.emit(ICall(dst, n, arg_vals))
                return dst

            case TCon(name=tag):
                # Constructor application — build an ADT record.
                field_vals = tuple(self._expr(a, fn, env) for a in args)
                dst = fn.fresh()
                fn.emit(IAlloc(dst, tag, field_vals))
                return dst

            case _:
                # Indirect call through a closure (curried, one arg at a time).
                closure_val = self._expr(fn_expr, fn, env)
                result: Val = closure_val
                for arg in args:
                    arg_val = self._expr(arg, fn, env)
                    dst     = fn.fresh()
                    fn.emit(IClosureCall(dst, result, arg_val))
                    result = dst
                return result

    def _lower_string_to_result(
        self, name: str, args: tuple[TExpr, ...],
        fn: Function, env: dict[str, Val],
    ) -> Val:
        """Lower string_to_int / string_to_float into a Result-producing sequence.

        The runtime stub `__<name>_raw` parses the string and returns a heap
        record it fabricates as [word0, flag@word1, payload@word2] (flag=1 → Ok
        payload, flag=0 → Err payload).  We branch on the flag and build Ok/Err
        with IAlloc so their tag ids are assigned by asm._collect_tags in
        lock-step with any user-written Ok/Err.

        REPRESENTATION CONTRACT (OPTIMIZE.md §8d item [5], part a) — the two
        IGetField reads below and the stub's 3-word packing MUST agree: IGetField
        reads field `idx` from word `(idx+1)` (word0 is the ADT tag slot, skipped),
        so IGetField(_,raw,0)=flag lands on word1 and IGetField(_,raw,1)=payload on
        word2 — exactly the layout `riscv_vm._rt_string_to_{int,float}_raw` writes
        with `pack_into('<III', mem, rec, 0, <word0>, flag, payload)`. The stub is
        NOT a real ADT (no constructor, no tag), it just borrows the ADT field
        offsets. If asm/lower ever change IGetField's `(idx+1)*4` offset, BOTH this
        function and those two VM stubs must move together; no test isolates this
        coupling (the corpus checks end-to-end output, not the intermediate word)."""
        argv = self._expr(args[0], fn, env)
        raw  = fn.fresh()
        fn.emit(ICall(raw, "__" + name + "_raw", (argv,)))
        flag    = fn.fresh()
        payload = fn.fresh()
        fn.emit(IGetField(flag, raw, 0))
        fn.emit(IGetField(payload, raw, 1))
        l_ok  = fn.label("res_ok")
        l_err = fn.label("res_err")
        l_end = fn.label("res_end")
        dst   = fn.fresh("r")
        fn.emit(ICondJump(flag, l_ok, l_err))
        fn.emit(ILabel(l_ok))
        ok = fn.fresh()
        fn.emit(IAlloc(ok, "Ok", (payload,)))
        fn.emit(IAssign(dst, ok))
        fn.emit(IJump(l_end))
        fn.emit(ILabel(l_err))
        er = fn.fresh()
        fn.emit(IAlloc(er, "Err", (payload,)))
        fn.emit(IAssign(dst, er))
        fn.emit(IJump(l_end))
        fn.emit(ILabel(l_end))
        return dst

    # -- Lambda / closure conversion --

    def _lower_lambda(
        self, params: tuple[tuple[str, object], ...],
        body: TExpr,
        fn: Function, env: dict[str, Val],
    ) -> Val:
        """Lift the lambda to a top-level function; return a closure value."""
        # Desugar multi-param lambdas into curried single-param closures,
        # matching the CEK machine's make_closure convention.
        if len(params) > 1:
            inner = TLambda(params[1:], body, ty.T_UNIT)
            return self._lower_lambda(params[:1], inner, fn, env)

        param_names  = frozenset(n for n, _ in params)
        # Free variables in the body that are neither params nor global names.
        # Global lets are excluded — they are accessed via Tmp(name) which falls
        # back to _globals at runtime; they must not be captured in the closure.
        all_bound    = param_names | self._global_fns | _BUILTINS | self._global_lets
        free         = sorted(
            _free(body, all_bound) - self._global_fns - _BUILTINS - self._global_lets
        )

        # Fresh name for the lifted function.
        lam_name    = f"{fn.name}$lam{self._lambda_ctr}"
        self._lambda_ctr += 1
        self._global_fns.add(lam_name)

        # All lifted closures use (env, param) so the runtime calling convention
        # is uniform regardless of whether the closure captures anything.
        lam_params = ("env",) + tuple(n for n, _ in params)
        lam_fn = Function(lam_name, lam_params)

        # In the lifted function, free variables come from env fields.
        lam_env: dict[str, Val] = {n: Tmp(n) for n in lam_params}
        for i, fv in enumerate(free):
            fld = lam_fn.fresh("cap")
            lam_fn.emit(IGetField(fld, Tmp("env"), i))
            lam_env[fv] = fld

        result = self._expr(body, lam_fn, lam_env)
        lam_fn.emit(IReturn(result))
        self._tac.add(lam_fn)

        # At the call site, allocate a closure record.
        # Every name in free must be in env — if not, that is a compiler bug.
        captured = tuple(env[fv] for fv in free)
        dst = fn.fresh("clos")
        fn.emit(IAllocClosure(dst, lam_name, captured))
        return dst


# -- Entry point --

def lower(tprog: TProgram) -> TAC:
    return Lowerer().lower(tprog)


# -- CLI --

if __name__ == "__main__":
    import pprint
    from tac import pretty as tac_pretty

    if len(sys.argv) < 2:
        print("usage: lower.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    import parser as _parser
    import infer  as _infer

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)
    print(tac_pretty(tac))
