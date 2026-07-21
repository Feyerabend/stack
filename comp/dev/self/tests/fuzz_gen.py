"""
Random *well-typed* Lark program generator (SELFHOST hardening pass).

The differential harnesses (lex/parse/infer/emit) prove `port == oracle` only on
the constructs the ~44 fixed corpus files happen to exercise.  This generator
attacks that blind spot: it synthesises fresh, deterministically-seeded programs
that mix the expression/decl core in shapes the corpus never wrote, so
`fuzz_difftest.py` can push each one through lex → parse → infer → emit and
demand byte-identical agreement.

Design — type-directed synthesis over the four Copy base types
──────────────────────────────────────────────────────────────
Every generated term is built *for a target type*, so the program type-checks by
construction (Algorithm W accepts it) and therefore reaches the emit stage — the
newest, least-exercised port.  The type universe is deliberately the four
built-in Copy scalars {Int, Float, Bool, String}:

  • all four are Copy (ty.BUILTIN_COPY), so a bound variable may be used any
    number of times — the generator never has to reason about affine use counts;
  • all four satisfy the built-in Show instance, so `show(e)` is always legal;
  • they have literals, a rich set of built-in operations between them, and the
    polymorphic arithmetic/comparison operators, giving broad combinatorial cover
    without the polymorphism/annotation hazards of Nil/Ok/ADTs.

What is exercised: top-level `fn` (0–3 params) and annotated `let` decls, mutual
reference between them (bodies see every signature — infer Pass 1.5), calls,
`if/then/else`, `let … in`, `match` on an Int scrutinee with literal + wildcard/
var patterns (infer does no exhaustiveness check, so partial matches are legal),
every binary operator (`+ - * /`, the six comparisons, `and`/`or`), unary `not`
and `-`, and the scalar built-ins (`show`, the conversions, the math and string
prims).  Every compound form is fully parenthesised, so operator precedence is
never relied upon — a divergence is always a real port bug, never a paren bug.

One user-defined ADT (`Adt`) is always declared in a fixed prelude, together with
`impl Copy for Adt = {}` so its values are Copy like the scalars — the generator
still never reasons about affine use counts.  It exercises the ADT-shaped port
paths the scalar core misses: a `type` decl with mixed-arity variants, value
construction (`CA(e)`, `CB(e, e)`, bare nullary `CC`), and `match` on an ADT
scrutinee with constructor patterns that bind the field variables.  `Adt` joins
the type universe wherever a *binding* type is chosen (fn params/returns,
top-level `let`, `let … in`), but never where a scalar is required (no ADT
literal, `show`, arithmetic or comparison operand).

Out of scope for this generator (left to the fixed corpus / future extensions):
polymorphic/parameterised ADTs, traits/impls beyond the Copy prelude, tuples,
lists, Result, `import`, and programs that are *meant* to be rejected.  See
fuzz_difftest.py's module docstring.

`gen_program(seed)` is a pure function of the seed: the same seed always yields
the same source, so any divergence reproduces from its printed seed alone.
"""

from __future__ import annotations
import random

BASE = ("Int", "Float", "Bool", "String")

# The one user ADT every program declares (fixed prelude).  Mixed variant arity —
# a single-field ctor, a two-field ctor, and a nullary ctor — to exercise the
# constructor-pattern and construction paths at each arity.  `impl Copy` keeps its
# values Copy, so ADT-typed bindings need no affine bookkeeping (same rule as the
# scalars).  Field types are scalars, so ctor arguments reuse the scalar synthesis.
ADT          = "Adt"
ADT_CTORS: list[tuple[str, list[str]]] = [
    ("CA", ["Int"]),
    ("CB", ["Float", "Float"]),
    ("CC", []),
]
ADT_PRELUDE = [
    "type Adt =",
    "  | CA of Int",
    "  | CB of Float, Float",
    "  | CC",
    "",
    "impl Copy for Adt = {}",
    "",
]

# Built-in operations, indexed later by result type.  (name, [arg types], result)
# Mirrors the scalar built-ins in infer.py's initial environment.  string_to_int
# / string_to_float are omitted (they return Result, off the base-type universe).
BUILTINS: list[tuple[str, list[str], str]] = [
    ("int_abs",         ["Int"],                  "Int"),
    ("float_abs",       ["Float"],                "Float"),
    ("float_sqrt",      ["Float"],                "Float"),
    ("float_floor",     ["Float"],                "Float"),
    ("float_ceil",      ["Float"],                "Float"),
    ("int_to_float",    ["Int"],                  "Float"),
    ("float_to_int",    ["Float"],                "Int"),
    ("float_to_bits",   ["Float"],                "Int"),
    ("int_to_string",   ["Int"],                  "String"),
    ("float_to_string", ["Float"],                "String"),
    ("char_to_string",  ["Int"],                  "String"),
    ("string_length",   ["String"],               "Int"),
    ("string_index",    ["String", "Int"],        "Int"),
    ("string_slice",    ["String", "Int", "Int"], "String"),
]

# Which binary operators yield which result type (operands share the type shown).
# + - * / are polymorphic (a -> a -> a); we only ever apply them to a single base
# type at a time.  For String we keep just `+` (concatenation) for readability —
# the type checker would accept the others, but `+` is the one that means anything.
NUM_OPS  = ["+", "-", "*", "/"]
STR_OPS  = ["+"]
CMP_OPS  = ["==", "!=", "<", "<=", ">", ">="]


class Gen:
    def __init__(self, seed: int, *, max_decls: int = 4, max_depth: int = 3,
                 max_params: int = 3, max_prints: int = 4) -> None:
        self.r          = random.Random(seed)
        self.max_decls  = max_decls
        self.max_depth  = max_depth
        self.max_params = max_params
        self.max_prints = max_prints
        self._vc = 0                       # fresh local-variable counter
        # Top-level bindings visible to every body: name -> ("fn", [argtypes], ret)
        # or name -> ("val", type).  Populated in phase 1, read in phase 2.
        self.top: dict[str, tuple] = {}
        # Top-level `let` names emitted so far.  Functions are pre-registered
        # (infer Pass 1.5) and may be called before their definition, but a
        # top-level `let` value is only in scope *after* its line — so a body may
        # reference only the vals already emitted above it.
        self.visible_vals: set[str] = set()

    # -- names -----------------------------------------------------------------
    def _fresh(self, prefix: str) -> str:
        self._vc += 1
        return f"{prefix}{self._vc}"

    # -- types -----------------------------------------------------------------
    def _pick_type(self) -> str:
        """A binding type: a scalar, or the ADT ~1 time in 4."""
        return ADT if self.r.random() < 0.25 else self.r.choice(BASE)

    # -- literals --------------------------------------------------------------
    def lit(self, ty: str) -> str:
        r = self.r
        if ty == "Int":
            return str(r.randint(0, 99))
        if ty == "Float":
            return f"{r.randint(0, 99)}.{r.randint(0, 99)}"
        if ty == "Bool":
            return r.choice(["true", "false"])
        if ty == "String":
            n = r.randint(0, 5)
            return '"' + "".join(r.choice("abcdefghijklmnopqrstuvwxyz ")
                                 for _ in range(n)) + '"'
        raise AssertionError(ty)

    # -- expression synthesis --------------------------------------------------
    def expr(self, env: dict[str, str], ty: str, depth: int) -> str:
        """A parenthesis-safe expression of type `ty` under `env` (name->type)."""
        r = self.r
        # Leaf choices: a matching variable, or a type-appropriate atom (a scalar
        # literal, or — for the ADT, which has no literal — a construction).
        vars_of_ty = [n for n, t in env.items() if t == ty]
        if depth <= 0 or r.random() < 0.30:
            if vars_of_ty and r.random() < 0.6:
                return r.choice(vars_of_ty)
            return self._atom(env, ty, depth)

        # Compound forms — collect the applicable builders, pick one.
        builders = [self._call, self._builtin, self._show, self._if,
                    self._let, self._match]
        if ty in ("Int", "Float", "String"):
            builders.append(self._arith)
        if ty == "Bool":
            builders += [self._compare, self._logic, self._not]
        if ty in ("Int", "Float"):
            builders.append(self._neg)
        if ty == ADT:
            builders.append(self._construct)

        r.shuffle(builders)
        for b in builders:
            out = b(env, ty, depth)
            if out is not None:
                return out
        # Fallback (e.g. no callable of this type): a leaf atom.
        return vars_of_ty[0] if vars_of_ty else self._atom(env, ty, depth)

    def _atom(self, env, ty, depth):
        """A leaf value of `ty`: a scalar literal, or a (small) ADT construction."""
        if ty == ADT:
            return self._construct(env, ty, 0)   # depth 0 → prefers nullary `CC`
        return self.lit(ty)

    def _construct(self, env, ty, depth):
        if ty != ADT:
            return None
        # At the bottom of the budget, keep it finite by favouring nullary ctors.
        pool = ADT_CTORS if depth > 0 else [c for c in ADT_CTORS if not c[1]] or ADT_CTORS
        name, fields = self.r.choice(pool)
        if not fields:
            return name                          # bare nullary ctor, no parens
        args = [self.expr(env, ft, depth - 1) for ft in fields]
        return f"{name}({', '.join(args)})"

    def _arith(self, env, ty, depth):
        op  = self.r.choice(STR_OPS if ty == "String" else NUM_OPS)
        l   = self.expr(env, ty, depth - 1)
        rr  = self.expr(env, ty, depth - 1)
        return f"({l} {op} {rr})"

    def _compare(self, env, ty, depth):          # ty is Bool
        t  = self.r.choice(BASE)
        op = self.r.choice(CMP_OPS)
        return f"({self.expr(env, t, depth - 1)} {op} {self.expr(env, t, depth - 1)})"

    def _logic(self, env, ty, depth):            # ty is Bool
        op = self.r.choice(["and", "or"])
        return f"({self.expr(env, 'Bool', depth - 1)} {op} {self.expr(env, 'Bool', depth - 1)})"

    def _not(self, env, ty, depth):              # ty is Bool
        return f"(not {self.expr(env, 'Bool', depth - 1)})"

    def _neg(self, env, ty, depth):              # ty is Int or Float
        return f"(- {self.expr(env, ty, depth - 1)})"

    def _if(self, env, ty, depth):
        c = self.expr(env, "Bool", depth - 1)
        t = self.expr(env, ty, depth - 1)
        e = self.expr(env, ty, depth - 1)
        return f"(if {c} then {t} else {e})"

    def _let(self, env, ty, depth):
        vt  = self._pick_type()
        v   = self._fresh("v")
        val = self.expr(env, vt, depth - 1)
        body_env = dict(env); body_env[v] = vt
        body = self.expr(body_env, ty, depth - 1)
        return f"(let {v} : {vt} = {val} in {body})"

    def _match(self, env, ty, depth):
        # Match on an Int scrutinee (literal patterns) or on the ADT (constructor
        # patterns).  infer runs no exhaustiveness check, so partial matches are
        # legal in both modes.
        if self.r.random() < 0.5:
            return self._match_adt(env, ty, depth)
        return self._match_int(env, ty, depth)

    def _match_adt(self, env, ty, depth):
        # One arm per distinct constructor (a random non-empty subset), each
        # binding fresh variables for its fields; an optional wildcard catch-all.
        scrut = self.expr(env, ADT, depth - 1)
        ctors = list(ADT_CTORS)
        self.r.shuffle(ctors)
        chosen = ctors[: self.r.randint(1, len(ctors))]
        arms = []
        for name, fields in chosen:
            if fields:
                binds   = [self._fresh("b") for _ in fields]
                arm_env = dict(env)
                for bn, ft in zip(binds, fields):
                    arm_env[bn] = ft
                pat = f"{name}({', '.join(binds)})"
            else:
                arm_env, pat = env, name
            arms.append(f"  | {pat} => {self.expr(arm_env, ty, depth - 1)}")
        if len(chosen) < len(ADT_CTORS) and self.r.random() < 0.5:
            arms.append(f"  | _ => {self.expr(env, ty, depth - 1)}")
        return "(match " + scrut + " with\n" + "\n".join(arms) + "\n  end)"

    def _match_int(self, env, ty, depth):
        # match on an Int scrutinee: 1-2 literal arms + a wildcard/var catch-all.
        scrut = self.expr(env, "Int", depth - 1)
        arms  = []
        used  = set()
        for _ in range(self.r.randint(1, 2)):
            k = self.r.randint(0, 9)
            if k in used:
                continue
            used.add(k)
            arms.append(f"  | {k} => {self.expr(env, ty, depth - 1)}")
        if self.r.random() < 0.5:                # bind the scrutinee value
            n = self._fresh("m")
            catch_env = dict(env); catch_env[n] = "Int"
            arms.append(f"  | {n} => {self.expr(catch_env, ty, depth - 1)}")
        else:
            arms.append(f"  | _ => {self.expr(env, ty, depth - 1)}")
        return "(match " + scrut + " with\n" + "\n".join(arms) + "\n  end)"

    def _call(self, env, ty, depth):
        cands = [(n, sig) for n, sig in self.top.items()
                 if sig[0] == "fn" and sig[2] == ty]
        cands += [(n, sig) for n, sig in self.top.items()
                  if sig[0] == "val" and sig[1] == ty and n in self.visible_vals]
        if not cands:
            return None
        n, sig = self.r.choice(cands)
        if sig[0] == "val":
            return n
        args = [self.expr(env, at, depth - 1) for at in sig[1]]
        return f"{n}({', '.join(args)})"

    def _builtin(self, env, ty, depth):
        cands = [b for b in BUILTINS if b[2] == ty]
        if not cands:
            return None
        name, argts, _ = self.r.choice(cands)
        args = [self.expr(env, at, depth - 1) for at in argts]
        return f"{name}({', '.join(args)})"

    def _show(self, env, ty, depth):
        if ty != "String":
            return None
        at = self.r.choice(BASE)
        return f"show({self.expr(env, at, depth - 1)})"

    # -- declarations ----------------------------------------------------------
    def program(self) -> str:
        r = self.r
        # Phase 1: choose signatures for the top-level decls (bodies see all).
        decls: list[tuple] = []            # ("fn", name, [(pname,pty)], ret) | ("val", name, ty)
        n_decls = r.randint(1, self.max_decls)
        for i in range(n_decls):
            if r.random() < 0.75:
                name  = f"f{i}"
                # At least one param: `fn f()` lexes `()` as the UNIT token, which
                # the decl grammar rejects (there are no nullary fns — use `let`).
                nps   = r.randint(1, self.max_params)
                ps    = [(f"p{j}", self._pick_type()) for j in range(nps)]
                ret   = self._pick_type()
                decls.append(("fn", name, ps, ret))
                self.top[name] = ("fn", [t for _, t in ps], ret)
            else:
                name = f"g{i}"
                ty   = self._pick_type()
                decls.append(("val", name, ty))
                self.top[name] = ("val", ty)

        # Phase 2: emit each decl with a type-directed body, after the fixed ADT
        # prelude (its `type` + Copy impl are always in scope).
        lines = ["module Fuzz", ""] + ADT_PRELUDE
        for d in decls:
            if d[0] == "fn":
                _, name, ps, ret = d
                env = {pn: pt for pn, pt in ps}
                params = ", ".join(f"{pn} : {pt}" for pn, pt in ps)
                body = self.expr(env, ret, self.max_depth)
                lines.append(f"fn {name}({params}) : {ret} =\n  {body}")
            else:
                _, name, ty = d
                # Top-level let value: closed (no params in scope).
                body = self.expr({}, ty, self.max_depth)
                lines.append(f"let {name} : {ty} = {body}")
                self.visible_vals.add(name)   # in scope for decls emitted below
            lines.append("")

        # main: thread io through a few prints of String expressions.
        env = {}                            # only top-level names + builtins
        prints = [self.expr(env, "String", self.max_depth)
                  for _ in range(r.randint(1, self.max_prints))]
        body = ["fn main(io : IO) : IO ="]
        for s in prints[:-1]:
            body.append(f"  let io = print(io, {s}) in")
        body.append(f"  print(io, {prints[-1]})")
        lines.append("\n".join(body))
        return "\n".join(lines) + "\n"


def gen_program(seed: int, **kw) -> str:
    return Gen(seed, **kw).program()


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(gen_program(seed), end="")
