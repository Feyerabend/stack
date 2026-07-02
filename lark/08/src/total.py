"""
Lark totality checking — opt-in structural termination for `fn total`.

A function declared `fn total f(...)` is checked to terminate on every input:

  1. Every recursive call to f must decrease a fixed argument position
     *structurally*: the argument at that position is a variable bound
     strictly inside a constructor pattern that destructures the
     corresponding parameter (or something already smaller than it).
     Nesting is transitive: matching `Cons(x, xs)` against `xs` makes the
     new bindings smaller still.

  2. f may only refer to names that are themselves known to terminate:
     builtins, constructors, its own parameters (a total function is total
     *relative to its arguments* — the caller supplies the proof), other
     `total` functions, and plain functions whose call graph provably
     contains no cycle.

Deliberate v1 limits, each an error with its own message:
  - Mutual recursion between total functions is not analysed
    (needs lexicographic or size-change measures).
  - `n - 1` on Int does NOT count as decreasing.  Lark's Int is a
    *wrapping* i32 (Phase 8), so `f(n - 1)` from a negative n never
    reaches a base case going down — integer descent is genuinely
    unsound here, not merely unimplemented.  Recurse on data instead.
  - A total function's own name may appear only in call position;
    passing f itself as a value would let it re-enter through a
    parameter, hiding the recursion from the structural check.

The check is purely syntactic and runs on the parsed Program before
type checking; it needs no types, only binding structure.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tree import (
    Program, FnDecl, LetDecl, TypeDecl, TraitDecl, ImplDecl,
    Expr, Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
    LetExpr, IfExpr, MatchExpr, Lambda,
    Pat, PWild, PVar, PLit, PCon, PTuple,
)

# Names from infer._initial_env that denote terminating builtins.
BUILTINS: frozenset[str] = frozenset({
    "print", "read", "show",
    "int_to_float", "float_to_int", "int_to_string", "float_to_string",
    "int_abs", "float_abs", "float_sqrt", "float_floor", "float_ceil",
    "string_length",
})


class TotalityError(Exception):
    def __init__(self, fn: str, msg: str) -> None:
        super().__init__(f"fn total {fn}: {msg}")


# -- Reference collection (for the call-graph classification) --

def _refs(expr: Expr, bound: frozenset[str]) -> set[str]:
    """Free variable names referenced in expr (locals excluded)."""
    match expr:
        case Var(name=n):
            return set() if n in bound else {n}
        case Lit() | Con():
            return set()
        case TupleExpr(elems=es):
            return set().union(*(_refs(e, bound) for e in es)) if es else set()
        case Apply(fn=f, args=args):
            out = _refs(f, bound)
            for a in args:
                out |= _refs(a, bound)
            return out
        case BinOp(left=l, right=r):
            return _refs(l, bound) | _refs(r, bound)
        case UnaryOp(operand=o):
            return _refs(o, bound)
        case LetExpr(name=n, value=v, body=b):
            return _refs(v, bound) | _refs(b, bound | {n})
        case IfExpr(cond=c, then_=t, else_=e):
            return _refs(c, bound) | _refs(t, bound) | _refs(e, bound)
        case MatchExpr(scrutinee=s, arms=arms):
            out = _refs(s, bound)
            for pat, body in arms:
                out |= _refs(body, bound | _pat_vars(pat))
            return out
        case Lambda(params=ps, body=b):
            return _refs(b, bound | {p.name for p in ps})
    return set()


def _pat_vars(pat: Pat) -> frozenset[str]:
    match pat:
        case PVar(name=n):
            return frozenset({n})
        case PCon(args=args):
            return frozenset().union(*(_pat_vars(a) for a in args)) if args else frozenset()
        case PTuple(elems=es):
            return frozenset().union(*(_pat_vars(e) for e in es))
        case _:
            return frozenset()


# -- Cycle-freedom classification --

def _terminating_names(fns: dict[str, FnDecl]) -> set[str]:
    """Local functions that provably terminate without a structural check:
    `total` functions (verified separately) and functions whose reference
    graph reaches no cycle."""
    graph: dict[str, set[str]] = {}
    for name, decl in fns.items():
        params = frozenset(p.name for p in decl.params) | {name}
        graph[name] = _refs(decl.body, params) & fns.keys()
        # Self-reference: a fn that names itself is recursive — keep the edge.
        if name in _refs(decl.body, frozenset(p.name for p in decl.params)):
            graph[name].add(name)

    ok: dict[str, bool] = {}
    ACTIVE = object()
    state: dict[str, object] = {}

    def visit(n: str) -> bool:
        if fns[n].total:
            return True                       # verified by the structural check
        if n in ok:
            return ok[n]
        if state.get(n) is ACTIVE:
            return False                      # on a cycle
        state[n] = ACTIVE
        result = all(visit(m) for m in graph[n])
        state[n] = None
        ok[n] = result
        return result

    return {n for n in fns if visit(n)}


# -- The structural check --

def _check_total_fn(
    decl: FnDecl,
    allowed: set[str],
    ctors: set[str],
) -> None:
    """Verify one `fn total` declaration.  Raises TotalityError."""
    fname   = decl.name
    params  = [p.name for p in decl.params]
    pset    = set(params)

    # self_calls: (args, smaller) at each recursive call site, where
    # smaller maps a variable name -> the parameter it is strictly below.
    self_calls: list[tuple[tuple[Expr, ...], dict[str, str]]] = []

    def root_of(name: str, smaller: dict[str, str],
                shadowed: frozenset[str]) -> "str | None":
        if name in pset and name not in shadowed:
            return name
        return smaller.get(name)

    def bind_pat(pat: Pat, root: "str | None", smaller: dict[str, str],
                 depth: int = 0) -> dict[str, str]:
        """Extend smaller with pattern bindings.  Variables at depth >= 1
        (inside a constructor or tuple) are strictly smaller than root;
        a top-level alias is not."""
        out = dict(smaller)
        match pat:
            case PVar(name=n):
                if root is not None and depth >= 1:
                    out[n] = root
                else:
                    out.pop(n, None)          # alias/shadow: no ordering info
            case PCon(args=args):
                for a in args:
                    out = bind_pat(a, root, out, depth + 1)
            case PTuple(elems=es):
                for e in es:
                    out = bind_pat(e, root, out, depth + 1)
            case _:
                pass
        return out

    def walk(expr: Expr, smaller: dict[str, str],
             shadowed: frozenset[str]) -> None:
        """shadowed holds names locally rebound (let/lambda/pattern), so a
        reference to such a name is not the parameter or function it spells."""
        is_self = lambda n: n == fname and n not in shadowed and n not in pset
        match expr:
            case Var(name=n):
                if is_self(n):
                    raise TotalityError(
                        fname,
                        "the function's own name may only appear in call "
                        "position (passing it as a value hides recursion)",
                    )
            case Apply(fn=Var(name=n), args=args) if is_self(n):
                self_calls.append((args, dict(smaller)))
                for a in args:
                    walk(a, smaller, shadowed)
            case Apply(fn=f, args=args):
                walk(f, smaller, shadowed)
                for a in args:
                    walk(a, smaller, shadowed)
            case TupleExpr(elems=es):
                for e in es:
                    walk(e, smaller, shadowed)
            case BinOp(left=l, right=r):
                walk(l, smaller, shadowed)
                walk(r, smaller, shadowed)
            case UnaryOp(operand=o):
                walk(o, smaller, shadowed)
            case LetExpr(name=n, value=v, body=b):
                walk(v, smaller, shadowed)
                s2 = dict(smaller)
                # A let of something smaller stays smaller under the new name.
                if isinstance(v, Var) and smaller.get(v.name):
                    s2[n] = smaller[v.name]
                else:
                    s2.pop(n, None)
                walk(b, s2, shadowed | {n})
            case IfExpr(cond=c, then_=t, else_=e):
                walk(c, smaller, shadowed)
                walk(t, smaller, shadowed)
                walk(e, smaller, shadowed)
            case MatchExpr(scrutinee=s, arms=arms):
                walk(s, smaller, shadowed)
                root = None
                if isinstance(s, Var):
                    root = root_of(s.name, smaller, shadowed)
                for pat, body in arms:
                    s2 = bind_pat(pat, root, smaller)
                    walk(body, s2, shadowed | _pat_vars(pat))
            case Lambda(params=ps, body=b):
                s2 = dict(smaller)
                for p in ps:
                    s2.pop(p.name, None)
                walk(b, s2, shadowed | {p.name for p in ps})
            case _:
                pass  # Lit, Con

    walk(decl.body, {}, frozenset())

    # 1. Every referenced top-level name must be known to terminate.
    outside = _refs(decl.body, frozenset(pset) | {fname})
    for n in sorted(outside):
        if n in BUILTINS or n in allowed or n in ctors or n[0].isupper():
            continue
        raise TotalityError(
            fname,
            f"calls {n!r}, which is not known to terminate "
            f"(not total, and part of a recursive cycle or not in this module)",
        )

    # 2. Some fixed argument position must decrease at every self-call.
    if not self_calls:
        return
    n_params = len(params)
    for i in range(n_params):
        def decreases(call) -> bool:
            args, smaller = call
            if i >= len(args):
                return False
            a = args[i]
            return isinstance(a, Var) and smaller.get(a.name) == params[i]
        if all(decreases(c) for c in self_calls):
            return

    raise TotalityError(
        fname,
        "no argument position decreases structurally at every recursive "
        "call (note: Int is a wrapping i32, so `n - 1` does not count — "
        "recurse on data, not on integers)",
    )


# -- Entry point --

def check_program(program: Program) -> None:
    """Check every `fn total` declaration in a parsed program."""
    fns: dict[str, FnDecl] = {
        d.name: d for d in program.decls if isinstance(d, FnDecl)
    }
    if not any(d.total for d in fns.values()):
        return

    terminating = _terminating_names(fns)
    ctors: set[str] = set()
    for d in program.decls:
        if isinstance(d, TypeDecl) and isinstance(d.body, tuple):
            ctors |= {v.name for v in d.body}

    for d in fns.values():
        if not d.total:
            continue
        # Mutual recursion among total fns: reachable back to itself through
        # another function.  The structural check only handles self-calls.
        stack = [n for n in _refs(d.body, frozenset(p.name for p in d.params) | {d.name})
                 if n in fns and n != d.name]
        seen = set(stack)
        while stack:
            m = stack.pop()
            for n in _refs(fns[m].body, frozenset(p.name for p in fns[m].params)):
                if n == d.name:
                    raise TotalityError(
                        d.name,
                        f"mutual recursion through {m!r} is not supported by "
                        f"the structural totality checker",
                    )
                if n in fns and n not in seen:
                    seen.add(n)
                    stack.append(n)
        _check_total_fn(d, terminating, ctors)
