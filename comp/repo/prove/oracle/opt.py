"""
Lark optimizer — TAC → TAC transformation pipeline.

Passes operate on the TAC IR (tac.py). Each pass is a function TAC -> TAC and is
individually toggleable, so the measurement harness (tests/optbench.py) can
attribute a speedup to a pass and bisect a regression.

Optimization levels bundle passes:
  -O0 : no passes (identity) — the correctness baseline.
  -O1 : Tier-1 scalar passes on TAC — const fold/prop, algebraic simplify,
        copy prop, DCE, CSE.
  -O2+: Tier-2/3/4.

At -O0 (or with every pass disabled) optimize() returns the TAC unchanged, so the
emitted code is byte-identical to the un-optimized pipeline. This is the property
optbench.py baselines before any real pass is written: it is the "ruler", not yet
a transform.

Correctness contract: once passes exist, the guard is
OBSERVABLE-EQUIVALENCE — optimized output must produce identical program output to
the -O0 build across the whole corpus (not byte-identical asm, which changes by
design). optbench.py enforces this per file × level.
"""

from __future__ import annotations
import sys, os, itertools
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass, field

from tac import (
    TAC, Function, Instr, Tmp, Const, Val,
    IAssign, IBinOp, IUnary, ICall, IClosureCall,
    IReturn, ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
)
from cfg import build_cfg
from liveness import analyse, defs, uses


# -- Instruction rewriting helpers -------------------------------------------
#
# The block-local passes below all work the same way: walk each basic block's
# straight-line instruction list, rewriting the VALUES used by each instruction
# (never the destinations / control flow). `_map_uses` applies a value->value
# function to every USE position of one instruction and returns a fresh instr;
# it leaves defs, ops, labels, tags, and field indices untouched.

def _map_uses(instr: Instr, f) -> Instr:
    """Return `instr` with f applied to every Val in a use position."""
    match instr:
        case IAssign(dst=d, src=s):
            return IAssign(d, f(s))
        case IBinOp(dst=d, op=op, l=l, r=r):
            return IBinOp(d, op, f(l), f(r))
        case IUnary(dst=d, op=op, src=s):
            return IUnary(d, op, f(s))
        case ICall(dst=d, fn=fn, args=args):
            return ICall(d, fn, tuple(f(a) for a in args))
        case IClosureCall(dst=d, fn=fv, arg=a):
            return IClosureCall(d, f(fv), f(a))
        case IReturn(val=v):
            return IReturn(f(v) if v is not None else None)
        case ICondJump(cond=c, true_label=t, false_label=fl):
            return ICondJump(f(c), t, fl)
        case IAlloc(dst=d, tag=tag, fields=fs):
            return IAlloc(d, tag, tuple(f(x) for x in fs))
        case IGetTag(dst=d, src=s):
            return IGetTag(d, f(s))
        case IGetField(dst=d, src=s, idx=i):
            return IGetField(d, f(s), i)
        case IAllocClosure(dst=d, fn_name=fn, captured=caps):
            return IAllocClosure(d, fn, tuple(f(x) for x in caps))
        case _:                       # ILabel, IJump — no use positions
            return instr


# A value-defining instruction is one whose result is a fresh Tmp with NO
# observable effect: dropping it (when its result is dead) removes only the
# computation. ICall / IClosureCall are excluded — a static or closure call may
# print, read, or otherwise have effects the def-liveness can't see, so they are
# kept even when their result is dead.
_PURE_DEFS = (IAssign, IBinOp, IUnary, IAlloc, IGetTag, IGetField, IAllocClosure)

def _pure_def_name(instr: Instr) -> str | None:
    """The destination name if `instr` is a pure value-def, else None."""
    if isinstance(instr, _PURE_DEFS):
        return instr.dst.name
    return None


def _blocks(fn: Function):
    """Basic blocks in definition order; concatenating their instrs == fn.body."""
    return list(build_cfg(fn).blocks.values())


# A MONOTONIC site counter shared by `inline` and `closure_elim`. Both mint
# site-unique temp/label names (`.i{s}_ret`, `_c{s}_x`, …); the names only have to
# be unique WITHIN a function, but because optimize() now iterates the pass sweep
# to a fixpoint (-O3), a per-call `site = 0` would re-mint `.i0_…` on
# the second sweep and collide with the first sweep's inlined labels. Drawing from
# one never-reset counter keeps every minted name globally unique across sweeps.
# (One process per file under optbench, so a growing counter is free.)
_SITE = itertools.count()

def _next_site() -> int:
    return next(_SITE)


# -- Constant value classifiers ----------------------------------------------
#
# `Const.value` is one of int / float / bool / str / None (unit). Python's `bool`
# is a subclass of `int`, so an INT test must exclude bools explicitly.

_MASK32 = 0xFFFF_FFFF

def _wrap32(n: int) -> int:
    """Signed 32-bit truncation — the value RV32's ADD/SUB/MUL leave in a register
    (`& 0xFFFFFFFF`) once it is printed via `signed()`. Folding to this exact value
    makes the subsequent `li` load bit-identical register contents."""
    return ((n + 0x8000_0000) & _MASK32) - 0x8000_0000

def _is_int_const(v: Val) -> bool:
    return isinstance(v, Const) and isinstance(v.value, int) and not isinstance(v.value, bool)

def _is_bool_const(v: Val) -> bool:
    return isinstance(v, Const) and isinstance(v.value, bool)


# -- Constant folding (int + bool, evaluate at compile time) -----------------
#
# Replace an IBinOp / IUnary whose operands are all constant with an IAssign of
# the computed constant. Restricted to INT and BOOL constants:
#
#   • Int +,-,* are folded under `_wrap32` (RV32 is 32-bit; Python ints are not).
#   • Int comparisons (==,!=,<,<=,>,>=) fold to a bool Const, comparing the
#     signed-wrapped operands to match the backend (`slt` is signed; `==`/`!=`
#     are `sub` then `seqz`/`snez`).
#   • `/` and `%` are NEVER folded: on ÷0 RV32 DIV/REM return sentinels
#     (-1 / dividend) where the CEK raises — divergent.
#   • Bool `&&`/`||` and unary `not` fold; unary int `-` folds under `_wrap32`.
#   • FLOAT constants are never folded — float arith/cmp are ICall on this
#     backend, but `==`/`!=` on floats stay IBinOp, so gating on INT consts is
#     what keeps float `==` (and NaN) off this path (float folding deferred).

def const_fold(tac: TAC) -> TAC:
    for fn in tac.functions:
        fn.body = [_fold_instr(i) for i in fn.body]
    return tac

def _fold_instr(instr: Instr) -> Instr:
    match instr:
        case IBinOp(dst=d, op=op, l=l, r=r):
            v = _fold_binop(op, l, r)
            return IAssign(d, v) if v is not None else instr
        case IUnary(dst=d, op=op, src=s):
            v = _fold_unary(op, s)
            return IAssign(d, v) if v is not None else instr
        case _:
            return instr

def _fold_binop(op: str, l: Val, r: Val) -> Const | None:
    if _is_int_const(l) and _is_int_const(r):
        a, b = l.value, r.value
        match op:
            case "+":  return Const(_wrap32(a + b))
            case "-":  return Const(_wrap32(a - b))
            case "*":  return Const(_wrap32(a * b))
            case "==": return Const(_wrap32(a) == _wrap32(b))
            case "!=": return Const(_wrap32(a) != _wrap32(b))
            case "<":  return Const(_wrap32(a) <  _wrap32(b))
            case "<=": return Const(_wrap32(a) <= _wrap32(b))
            case ">":  return Const(_wrap32(a) >  _wrap32(b))
            case ">=": return Const(_wrap32(a) >= _wrap32(b))
            # "/" and "%" deliberately absent — ÷0 diverges from the CEK.
        return None
    if _is_bool_const(l) and _is_bool_const(r):
        a, b = l.value, r.value
        match op:
            case "&&": return Const(a and b)
            case "||": return Const(a or b)
        return None
    return None

def _fold_unary(op: str, s: Val) -> Const | None:
    if op == "-" and _is_int_const(s):
        return Const(_wrap32(-s.value))
    if op == "not" and _is_bool_const(s):
        return Const(not s.value)
    return None


# -- Algebraic simplification (identities with a constant operand) -----------
#
# Simplify an IBinOp to one of its operands (or a constant) using arithmetic /
# boolean identities. Every identity is GATED on a constant operand of the right
# type — the int Const in `x + 0` guarantees an int context (IBinOp +,-,* are
# int-only on this backend, but the gate is the tripwire if that ever changes).
#
#   x+0, 0+x, x-0  → x        x*1, 1*x → x        x*0, 0*x → 0
#   x&&true → x    x&&false → false     x||false → x    x||true → true
#
# `x - x → 0` is intentionally NOT done: IBinOp carries no type, so the operand
# could be a float (where `x - x` is NaN, not 0).

def algebraic_simplify(tac: TAC) -> TAC:
    for fn in tac.functions:
        fn.body = [_algebraic_instr(i) for i in fn.body]
    return tac

def _algebraic_instr(instr: Instr) -> Instr:
    match instr:
        case IBinOp(dst=d, op=op, l=l, r=r):
            v = _algebraic_binop(op, l, r)
            return IAssign(d, v) if v is not None else instr
        case _:
            return instr

def _algebraic_binop(op: str, l: Val, r: Val) -> Val | None:
    zero_l, zero_r = _is_int_const(l) and l.value == 0, _is_int_const(r) and r.value == 0
    one_l,  one_r  = _is_int_const(l) and l.value == 1, _is_int_const(r) and r.value == 1
    match op:
        case "+":
            if zero_r: return l
            if zero_l: return r
        case "-":
            if zero_r: return l                 # x - 0 = x  (0 - x is NOT x)
        case "*":
            if one_r:  return l
            if one_l:  return r
            if zero_r or zero_l: return Const(0)  # x * 0 = 0 (Vals are effect-free)
    # Boolean identities — `&&`/`||` are AND/OR of 0/1 on the backend.
    true_l,  true_r  = _is_bool_const(l) and l.value, _is_bool_const(r) and r.value
    false_l, false_r = _is_bool_const(l) and not l.value, _is_bool_const(r) and not r.value
    match op:
        case "&&":
            if true_r: return l
            if true_l: return r
            if false_r or false_l: return Const(False)
        case "||":
            if false_r: return l
            if false_l: return r
            if true_r or true_l: return Const(True)
    return None


# -- Copy propagation (block-local, Tmp->Tmp) --------------------------------
#
# Within a straight-line block, an `IAssign(dst, srcTmp)` makes `dst` a copy of
# `srcTmp`; every later use of `dst` in the same block is rewritten to `srcTmp`,
# leaving `dst`'s assignment dead for DCE to remove. Restricted to Tmp->Tmp
# copies: propagating a Const would introduce constant operands in positions the
# -O0 backend never emits (e.g. a Const `ICondJump` cond) — that is const_fold's
# job (-O1), where the backend paths are checked. The map is reset per
# block because TAC is NOT globally single-assignment (an `if`/`match` result temp
# is assigned once PER arm, in different blocks — lower.py), so a copy is only
# known-valid inside the block that established it.

def copy_prop(tac: TAC) -> TAC:
    for fn in tac.functions:
        new_body: list[Instr] = []
        for blk in _blocks(fn):
            copies: dict[str, Tmp] = {}       # dst name -> canonical source Tmp
            for instr in blk.instrs:
                instr = _map_uses(
                    instr,
                    lambda v: copies.get(v.name, v) if isinstance(v, Tmp) else v,
                )
                # Any (re)definition invalidates copies of / to that name.
                d = _def_name(instr)
                if d is not None:
                    copies.pop(d, None)
                    for k in [k for k, s in copies.items() if s.name == d]:
                        copies.pop(k, None)
                if isinstance(instr, IAssign) and isinstance(instr.src, Tmp):
                    copies[instr.dst.name] = instr.src
                new_body.append(instr)
        fn.body = new_body
    return tac


def _def_name(instr: Instr) -> str | None:
    ds = defs(instr)
    return next(iter(ds)) if ds else None


# -- Dead code elimination (global liveness) ---------------------------------
#
# Drop any PURE value-def whose result is not live-out of its block and not used
# later within it. Iterated to a fixpoint because removing one dead def can make
# another dead. Guards: never drop a call (possible effects), control flow, or an
# assignment to a top-level global name — a global is written in the init
# function but read from OTHER functions, so intra-function liveness sees it as
# dead here even though it is not.

def dce(tac: TAC) -> TAC:
    globals_ = tac.global_names
    for fn in tac.functions:
        changed = True
        while changed:
            changed = False
            cfg = build_cfg(fn)
            lv  = analyse(cfg)
            new_body: list[Instr] = []
            for blk in cfg.blocks.values():
                live = set(lv.live_out[blk.label])
                keep = [True] * len(blk.instrs)
                for i in range(len(blk.instrs) - 1, -1, -1):
                    instr = blk.instrs[i]
                    d = _pure_def_name(instr)
                    if d is not None and d not in live and d not in globals_:
                        keep[i] = False
                        changed = True
                        continue          # dropped: its uses do not become live
                    live -= defs(instr)
                    live |= uses(instr)
                new_body.extend(
                    instr for i, instr in enumerate(blk.instrs) if keep[i]
                )
            fn.body = new_body
    return tac


# -- Common subexpression elimination (block-local, non-allocating) ----------
#
# Within a straight-line block, if the same pure expression is computed twice
# with the same operands, the second computation is replaced by a copy of the
# first result (copy_prop/dce then collapse the copy). Restricted to the pure,
# NON-ALLOCATING instructions — IBinOp / IUnary / IGetTag / IGetField — whose
# result is a deterministic function of their operands. These are keyed by
# OPCODE + operands (not by name), so the CSE_ELIGIBLE allowlist below does not
# apply to them; that list governs the deferred CSE of allocating pure prims.
#
# Two facts make this sound. (1) Values are immutable and equality is structural
# (see CSE_ELIGIBLE) so sharing a result is unobservable. (2) An expression's
# entry is KILLED when any operand it reads — or the temp holding its value — is
# redefined, so a stale value is never reused. TAC is not globally SSA, so the
# table is per-block; within a block fresh temps are single-assignment, but the
# kill is kept for correctness regardless. (`/`,`%` are pure on RV32 — ÷0 yields
# a sentinel, no trap — and the first, dominating occurrence computes it, so
# CSE'ing the second is safe.)

def cse(tac: TAC) -> TAC:
    for fn in tac.functions:
        new_body: list[Instr] = []
        for blk in _blocks(fn):
            avail: dict[tuple, tuple[Tmp, frozenset[str]]] = {}
            for instr in blk.instrs:
                key = _cse_key(instr)
                if key is not None and key in avail:
                    canon, _ = avail[key]
                    instr = IAssign(instr.dst, canon)
                    key = None                 # replaced: do not re-record
                d = _def_name(instr)
                if d is not None and avail:
                    for k in [k for k, (t, us) in avail.items()
                              if t.name == d or d in us]:
                        avail.pop(k, None)
                if key is not None:
                    avail[key] = (instr.dst, uses(instr))
                new_body.append(instr)
        fn.body = new_body
    return tac


def _cse_key(instr: Instr) -> tuple | None:
    """A hashable key identifying a pure non-allocating expression, or None."""
    match instr:
        case IBinOp(op=op, l=l, r=r):
            return ("binop", op, _vkey(l), _vkey(r))
        case IUnary(op=op, src=s):
            return ("unary", op, _vkey(s))
        case IGetTag(src=s):
            return ("gettag", _vkey(s))
        case IGetField(src=s, idx=i):
            return ("getfield", _vkey(s), i)
        case _:
            return None

def _vkey(v: Val):
    if isinstance(v, Tmp):
        return ("t", v.name)
    # Distinguish 1 / True / 1.0 by type — they compare/hash equal in Python.
    return ("c", type(v.value).__name__, v.value)


# -- Trait-dispatch devirtualization (O2) ------------------------------------
#
# lower.py emits, for each trait method `m` with user impls, a dispatch STUB — a
# top-level function named `m` that reads the constructor tag of its argument and
# branches to `m$Type(x)` for the implementing type (falling through to
# __lark_match_fail on no match). At a call site `ICall(dst, m, (arg,))` where the
# argument's constructor tag is statically known (it was just IAlloc'd with that
# tag in the same straight-line block), we can bypass the stub and call `m$Type`
# directly — deleting the tag read + branch chain and, crucially, exposing a
# direct call the inliner can then inline.
#
# The tag → `m$Type` map is RECOVERED from the stub's own body (opt.py sees only
# TAC, not the trait tables), by tracing each `tag == "Con"` / ICondJump to its arm
# label and reading that arm's `m$Type(x)` call. This is sound: the stub, on an
# argument with constructor tag T, computes exactly this route and has no other
# effect — so calling `m$Type` directly is observably identical.

def _extract_dispatch(fn: Function) -> dict[str, str] | None:
    """If `fn` is a trait-dispatch stub, return {constructor_tag -> "m$Type"};
    else None. Recognised by: a single param `x`, an IGetTag on `x`, a chain of
    `tag == Const` / ICondJump arms, and arm bodies calling `fn.name$Type(x)`."""
    if "$" in fn.name or not fn.params:
        return None
    p = fn.params[0]
    tag_tmp: str | None = None
    for i in fn.body:
        if isinstance(i, IGetTag) and isinstance(i.src, Tmp) and i.src.name == p:
            tag_tmp = i.dst.name
            break
    if tag_tmp is None:
        return None

    body = fn.body
    tag_to_arm: dict[str, str] = {}
    for idx in range(len(body) - 1):
        i0, i1 = body[idx], body[idx + 1]
        if (isinstance(i0, IBinOp) and i0.op == "==" and isinstance(i0.l, Tmp)
                and i0.l.name == tag_tmp and isinstance(i0.r, Const)
                and isinstance(i0.r.value, str)
                and isinstance(i1, ICondJump) and isinstance(i1.cond, Tmp)
                and i1.cond.name == i0.dst.name):
            tag_to_arm[i0.r.value] = i1.true_label

    arm_to_target: dict[str, str] = {}
    for idx, i in enumerate(body):
        if not isinstance(i, ILabel):
            continue
        j = idx + 1
        while j < len(body) and isinstance(body[j], ILabel):
            j += 1
        if j < len(body):
            c = body[j]
            if (isinstance(c, ICall) and c.fn.startswith(fn.name + "$")
                    and len(c.args) == 1 and isinstance(c.args[0], Tmp)
                    and c.args[0].name == p):
                arm_to_target[i.name] = c.fn

    mp = {tag: arm_to_target[arm]
          for tag, arm in tag_to_arm.items() if arm in arm_to_target}
    return mp or None


def devirt(tac: TAC) -> TAC:
    stubs: dict[str, dict[str, str]] = {}
    for fn in tac.functions:
        m = _extract_dispatch(fn)
        if m is not None:
            stubs[fn.name] = m
    if not stubs:
        return tac

    for fn in tac.functions:
        new_body: list[Instr] = []
        alloc_tag: dict[str, str] = {}   # tmp name -> known constructor tag (block-local)
        for instr in fn.body:
            if isinstance(instr, ILabel):
                alloc_tag = {}            # entering a new block: forget everything
            if (isinstance(instr, ICall) and instr.fn in stubs
                    and len(instr.args) == 1 and isinstance(instr.args[0], Tmp)):
                tg = alloc_tag.get(instr.args[0].name)
                mp = stubs[instr.fn]
                if tg is not None and tg in mp:
                    instr = ICall(instr.dst, mp[tg], instr.args)
            # Update tag tracking AFTER the rewrite (a def kills the old fact).
            if isinstance(instr, IAlloc):
                alloc_tag[instr.dst.name] = instr.tag
            elif isinstance(instr, IAssign) and isinstance(instr.src, Tmp):
                src_tag = alloc_tag.get(instr.src.name)
                alloc_tag.pop(instr.dst.name, None)
                if src_tag is not None:
                    alloc_tag[instr.dst.name] = src_tag
            else:
                for d in defs(instr):
                    alloc_tag.pop(d, None)
            if isinstance(instr, (IJump, ICondJump, IReturn)):
                alloc_tag = {}            # leaving the block along an edge
            new_body.append(instr)
        fn.body = new_body
    return tac


# -- Function inlining (O2) ---------------------------------------------------
#
# Replace a static call `ICall(dst, f, args)` to a small, non-recursive user
# function `f` with a fresh copy of f's body: parameters are substituted by the
# argument values, temporaries and labels are renamed to unique names, and each
# `IReturn v` becomes `dst = v; goto <ret>`. Kills call/return overhead and — the
# real prize in a curried FP language — exposes the callee's body to the Tier-1
# passes that run after it (const fold / copy prop / cse / dce across the old call
# boundary), and exposes devirtualized `m$Type` bodies.
#
# Single-level per sweep: only calls in the ORIGINAL body are expanded (calls
# introduced by an inlined body are not re-scanned), so growth is bounded by
# (call sites × callee size). Recursive callees are skipped, which also keeps
# self-recursive tail calls intact for the backend's loop lowering.
#
# After inlining, `_prune_unreachable` drops functions no longer reachable from
# the entry points — the cleanup that makes inlining a net win rather than pure
# code duplication (a callee inlined at its only call site becomes dead).

INLINE_MAX = 12   # max callee body length (instrs, incl. labels/return) to inline


def _rewrite_inlined(instr: Instr, mv, md, mlab) -> Instr:
    """Rewrite one callee instruction: uses via `mv` (Val->Val), defs via `md`
    (Tmp->Tmp), labels via `mlab` (str->str). Function names are left alone."""
    match instr:
        case IAssign(dst=d, src=s):
            return IAssign(md(d), mv(s))
        case IBinOp(dst=d, op=op, l=l, r=r):
            return IBinOp(md(d), op, mv(l), mv(r))
        case IUnary(dst=d, op=op, src=s):
            return IUnary(md(d), op, mv(s))
        case ICall(dst=d, fn=fn, args=args):
            return ICall(md(d) if d is not None else None, fn, tuple(mv(a) for a in args))
        case IClosureCall(dst=d, fn=fv, arg=a):
            return IClosureCall(md(d), mv(fv), mv(a))
        case ILabel(name=n):
            return ILabel(mlab(n))
        case IJump(label=l):
            return IJump(mlab(l))
        case ICondJump(cond=c, true_label=t, false_label=fl):
            return ICondJump(mv(c), mlab(t), mlab(fl))
        case IAlloc(dst=d, tag=tag, fields=fs):
            return IAlloc(md(d), tag, tuple(mv(x) for x in fs))
        case IGetTag(dst=d, src=s):
            return IGetTag(md(d), mv(s))
        case IGetField(dst=d, src=s, idx=i):
            return IGetField(md(d), mv(s), i)
        case IAllocClosure(dst=d, fn_name=fn, captured=caps):
            return IAllocClosure(md(d), fn, tuple(mv(x) for x in caps))
        case _:
            return instr     # IReturn handled by the caller


def _inline_call(callee: Function, call: ICall,
                 globals_: frozenset[str], site: int) -> list[Instr]:
    params_sub: dict[str, Val] = dict(zip(callee.params, call.args))
    ren:  dict[str, Tmp] = {}
    lmap: dict[str, str] = {}
    ret_label = f".i{site}_ret"

    def mv(v: Val) -> Val:
        if isinstance(v, Const):
            return v
        if v.name in params_sub:
            return params_sub[v.name]
        if v.name in globals_:
            return v
        if v.name not in ren:
            ren[v.name] = Tmp(f"_i{site}_{v.name}")
        return ren[v.name]

    def md(d: Tmp) -> Tmp:
        if d.name in globals_:
            return d
        if d.name not in ren:
            ren[d.name] = Tmp(f"_i{site}_{d.name}")
        return ren[d.name]

    def mlab(l: str) -> str:
        if l not in lmap:
            lmap[l] = f".i{site}_{l.lstrip('.')}"
        return lmap[l]

    out: list[Instr] = []
    for instr in callee.body:
        if isinstance(instr, IReturn):
            if call.dst is not None and instr.val is not None:
                out.append(IAssign(call.dst, mv(instr.val)))
            out.append(IJump(ret_label))
        else:
            out.append(_rewrite_inlined(instr, mv, md, mlab))
    out.append(ILabel(ret_label))
    return out


def _called_names(instr: Instr):
    if isinstance(instr, ICall):
        return (instr.fn,)
    if isinstance(instr, IAllocClosure):
        return (instr.fn_name,)
    return ()


def _prune_unreachable(tac: TAC) -> TAC:
    """Drop functions unreachable from the runtime entry points. Reachability
    follows named references only — ICall targets and IAllocClosure fn_names;
    indirect (closure) calls flow through the value an IAllocClosure produced, so
    its fn_name already marks the target reachable. Skipped entirely if `main` is
    absent (nothing to anchor from)."""
    fnmap = {f.name: f for f in tac.functions}
    if "main" not in fnmap:
        return tac
    roots = [n for n in ("main", "__global_init__") if n in fnmap]
    seen: set[str] = set()
    stack = list(roots)
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        f = fnmap.get(n)
        if f is None:
            continue
        for instr in f.body:
            for nm in _called_names(instr):
                if nm in fnmap and nm not in seen:
                    stack.append(nm)
    tac.functions = [f for f in tac.functions if f.name in seen]
    return tac


def inline(tac: TAC) -> TAC:
    fnmap = {f.name: f for f in tac.functions}
    globals_ = tac.global_names
    _NOINLINE = {"main", "__global_init__"}

    def eligible(name: str) -> bool:
        f = fnmap.get(name)
        if f is None or name in _NOINLINE:
            return False
        if len(f.body) > INLINE_MAX:
            return False
        pset = set(f.params)
        for i in f.body:
            # Skip self-recursive callees (would leave a residual self-call and,
            # for tail recursion, is better left to the backend's loop lowering).
            if isinstance(i, ICall) and i.fn == name:
                return False
            # A param defined in the body would break param substitution — bail.
            if defs(i) & pset:
                return False
        return True

    for fn in tac.functions:
        new_body: list[Instr] = []
        for instr in fn.body:
            if (isinstance(instr, ICall) and instr.dst is not None
                    and eligible(instr.fn)
                    and len(instr.args) == len(fnmap[instr.fn].params)):
                new_body.extend(_inline_call(fnmap[instr.fn], instr, globals_, _next_site()))
            else:
                new_body.append(instr)
        fn.body = new_body

    return _prune_unreachable(tac)


# -- Loop-invariant code motion (O2) -----------------------------------------
#
# Hoist a loop-invariant, pure, non-allocating computation out of a natural loop
# into the loop's preheader. Natural loops are found from the CFG via dominators:
# a back-edge is an edge n->h whose head h dominates its tail n; the loop is h
# plus every block that reaches n without passing through h.
#
# NOTE ON THIS IR: Lark has no iterative loop form — iteration is expressed by
# recursion, which is INTER-procedural (an ICall, not a CFG back-edge). Every
# intra-function CFG produced by lower.py is therefore ACYCLIC (all of if/match/
# dispatch emit only forward branches), so this pass finds no back-edges and is a
# no-op on the current corpus. It is implemented faithfully — and unit-tested on a
# synthetic loop (tests/opt_licm_test.py) — so it is correct the moment a loop-
# forming construct or a recursion→loop transform introduces a real back-edge.
#
# Conservative hoisting rule (safe without a full invariant fixpoint): move an
# instruction only if it is (a) in the loop HEADER block — so it dominates every
# loop use and runs on entry; (b) pure and non-allocating (IBinOp/IUnary/IGetTag/
# IGetField); (c) every operand is a Const or defined OUTSIDE the loop; (d) its
# destination is defined exactly once in the whole loop and is not a global. Such
# an instruction computes the same value every iteration, so it is hoisted to the
# unique non-back-edge predecessor (the preheader). Loops without a single such
# predecessor are skipped (no preheader to hoist into).

_LICM_PURE = (IBinOp, IUnary, IGetTag, IGetField)


def _dominators(cfg) -> dict[str, set[str]]:
    labels = list(cfg.blocks.keys())
    allset = set(labels)
    dom = {l: set(allset) for l in labels}
    dom[cfg.entry] = {cfg.entry}
    changed = True
    while changed:
        changed = False
        for l in labels:
            if l == cfg.entry:
                continue
            preds = cfg.blocks[l].preds
            new = set(allset)
            for p in preds:
                new &= dom[p]
            new = {l} | new
            if new != dom[l]:
                dom[l] = new
                changed = True
    return dom


def _natural_loop(cfg, tail: str, head: str) -> set[str]:
    loop = {head}
    stack = [tail]
    while stack:
        m = stack.pop()
        if m in loop:
            continue
        loop.add(m)
        stack.extend(cfg.blocks[m].preds)
    return loop


def licm(tac: TAC) -> TAC:
    for fn in tac.functions:
        cfg = build_cfg(fn)
        dom = _dominators(cfg)
        # Collect back-edges n -> h with h dominating n.
        back = [(blk.label, s)
                for blk in cfg.blocks.values()
                for s in blk.succs
                if s in dom.get(blk.label, set())]
        if not back:
            continue
        changed = False
        for tail, head in back:
            loop = _natural_loop(cfg, tail, head)
            # Preheader = the sole predecessor of head outside the loop.
            entries = [p for p in cfg.blocks[head].preds if p not in loop]
            if len(entries) != 1:
                continue
            pre = cfg.blocks[entries[0]]
            loop_defs: set[str] = set()
            def_count: dict[str, int] = {}
            for lbl in loop:
                for i in cfg.blocks[lbl].instrs:
                    for d in defs(i):
                        loop_defs.add(d)
                        def_count[d] = def_count.get(d, 0) + 1
            hdr = cfg.blocks[head]
            hoist: list[Instr] = []
            keep: list[Instr] = []
            for i in hdr.instrs:
                if (isinstance(i, _LICM_PURE)
                        and all(name not in loop_defs for name in uses(i))
                        and len(defs(i)) == 1
                        and def_count.get(next(iter(defs(i))), 0) == 1
                        and next(iter(defs(i))) not in tac.global_names):
                    hoist.append(i)
                else:
                    keep.append(i)
            if not hoist:
                continue
            hdr.instrs = keep
            # Insert hoisted instrs before the preheader's terminator.
            term = pre.instrs[-1] if pre.instrs else None
            at = len(pre.instrs) - 1 if isinstance(term, (IJump, ICondJump, IReturn)) else len(pre.instrs)
            pre.instrs[at:at] = hoist
            changed = True
        if changed:
            fn.body = [i for blk in cfg.blocks.values() for i in blk.instrs]
    return tac


# -- Closure elimination (O3) -------------------------------------------------
#
# Scalar-replace NON-ESCAPING closures. A closure `IAllocClosure(cv, L, caps)` is a
# heap record `[fn_ptr, cap0, cap1, …]`; `IClosureCall(dst, cv, arg)` loads
# `cv[0]` and indirect-jumps, passing the whole record as `env`. The lifted body
# `L(env, x)` reads its captures via `IGetField(_, env, i)` = `env[i+1]` = `caps[i]`.
#
# If `cv` (and every copy of it) is used ONLY as the function of an IClosureCall —
# it is never passed as an argument, returned, stored in another record, or read
# with IGetField — then the record never escapes and its identity is unobservable.
# We can then, at each call site, INLINE L's body with `IGetField(_, env, i)`
# rewritten to a direct `IAssign(_, caps[i])`, and DELETE the IAllocClosure. The
# heap record is now dead — a real `heap_allocs` decrement, the Tier-3 headline —
# and the indirect jalr becomes straight-line code.
#
# This composes with `inline`, which runs first: a closure allocated in a callee
# and returned (e.g. `adder(n) = \x -> n + x`) only becomes a LOCAL alloc-then-call
# pattern once `adder` is inlined at its use. The analysis is whole-function and
# follows single-assignment copies, so it fires across the `.i…_ret` block seam
# `inline` leaves between the (inlined) alloc and the call.
#
# Availability of `caps[i]` at each call site: captures are Consts, params, or
# single-def temps whose def dominates the alloc (data dependence: the alloc reads
# the cap, the call reads the alloc). Single-assignment ⇒ the value is the same
# wherever referenced, so hoisting the reference to the call site is sound. Multi-
# def captures are rejected (`_cap_available`). The observable-equivalence guard
# (optbench) backs the whole pass.

CLOSURE_INLINE_MAX = 24   # max lifted-body length to scalar-replace at a call site


def _closure_roots(fn: Function, defcount: dict[str, int]):
    """Map every closure-alias tmp name -> its defining IAllocClosure dst name
    ('root'), following single-assignment copies, plus root -> (L, caps)."""
    root: dict[str, str] = {}
    info: dict[str, tuple[str, tuple[Val, ...]]] = {}
    for i in fn.body:
        if isinstance(i, IAllocClosure) and defcount.get(i.dst.name, 0) == 1:
            root[i.dst.name] = i.dst.name
            info[i.dst.name] = (i.fn_name, i.captured)
    changed = True
    while changed:
        changed = False
        for i in fn.body:
            if (isinstance(i, IAssign) and isinstance(i.src, Tmp)
                    and i.src.name in root and i.dst.name not in root
                    and defcount.get(i.dst.name, 0) == 1):
                root[i.dst.name] = root[i.src.name]
                changed = True
    return root, info


def _closure_escapes(fn: Function, root: dict[str, str]) -> set[str]:
    """Root names whose closure value is used anywhere other than the function
    position of an IClosureCall or the source of a followed same-root copy."""
    escaped: set[str] = set()
    for i in fn.body:
        for name in uses(i):
            if name not in root:
                continue
            r = root[name]
            if (isinstance(i, IClosureCall) and isinstance(i.fn, Tmp)
                    and i.fn.name == name
                    and not (isinstance(i.arg, Tmp) and i.arg.name == name)):
                continue                        # ok: called, not captured
            if (isinstance(i, IAssign) and isinstance(i.src, Tmp)
                    and i.src.name == name
                    and root.get(i.dst.name) == r):
                continue                        # ok: a followed copy
            escaped.add(r)
    return escaped


def _lifted_scalar_ok(lf: Function) -> bool:
    """The lifted body reads its env ONLY via IGetField (so every capture use is a
    field load we can redirect), is non-recursive, and is small enough to duplicate."""
    if len(lf.params) != 2 or len(lf.body) > CLOSURE_INLINE_MAX:
        return False
    env = lf.params[0]
    for i in lf.body:
        if isinstance(i, ICall) and i.fn == lf.name:
            return False
        for name in uses(i):
            if name == env and not (isinstance(i, IGetField)
                                    and isinstance(i.src, Tmp)
                                    and i.src.name == env):
                return False
    return True


def _inline_closure(lf: Function, call: IClosureCall, caps: tuple[Val, ...],
                    globals_: frozenset[str], site: int) -> list[Instr]:
    """Inline lifted body `lf(env, x)` at a closure-call site: `x` -> call.arg,
    each `IGetField(_, env, i)` -> `IAssign(_, caps[i])`, and `IReturn v` ->
    `call.dst = v; goto ret`. Temps/labels are renamed site-uniquely."""
    env, actual = lf.params[0], lf.params[1]
    params_sub: dict[str, Val] = {actual: call.arg}
    ren:  dict[str, Tmp] = {}
    lmap: dict[str, str] = {}
    ret_label = f".c{site}_ret"

    def mv(v: Val) -> Val:
        if isinstance(v, Const):
            return v
        if v.name in params_sub:
            return params_sub[v.name]
        if v.name in globals_:
            return v
        if v.name not in ren:
            ren[v.name] = Tmp(f"_c{site}_{v.name}")
        return ren[v.name]

    def md(d: Tmp) -> Tmp:
        if d.name in globals_:
            return d
        if d.name not in ren:
            ren[d.name] = Tmp(f"_c{site}_{d.name}")
        return ren[d.name]

    def mlab(l: str) -> str:
        if l not in lmap:
            lmap[l] = f".c{site}_{l.lstrip('.')}"
        return lmap[l]

    out: list[Instr] = []
    for instr in lf.body:
        if (isinstance(instr, IGetField) and isinstance(instr.src, Tmp)
                and instr.src.name == env):
            out.append(IAssign(md(instr.dst), caps[instr.idx]))
        elif isinstance(instr, IReturn):
            if call.dst is not None and instr.val is not None:
                out.append(IAssign(call.dst, mv(instr.val)))
            out.append(IJump(ret_label))
        else:
            out.append(_rewrite_inlined(instr, mv, md, mlab))
    out.append(ILabel(ret_label))
    return out


def closure_elim(tac: TAC) -> TAC:
    fnmap = {f.name: f for f in tac.functions}
    globals_ = tac.global_names
    for fn in tac.functions:
        defcount: dict[str, int] = {}
        for i in fn.body:
            for d in defs(i):
                defcount[d] = defcount.get(d, 0) + 1
        root, info = _closure_roots(fn, defcount)
        if not info:
            continue
        escaped = _closure_escapes(fn, root)

        def cap_available(c: Val) -> bool:
            return (isinstance(c, Const)
                    or (isinstance(c, Tmp)
                        and (c.name in fn.params or defcount.get(c.name, 0) == 1)))

        elim: set[str] = set()
        for r, (fnm, caps) in info.items():
            lf = fnmap.get(fnm)
            if (r not in escaped and lf is not None and _lifted_scalar_ok(lf)
                    and all(cap_available(c) for c in caps)):
                elim.add(r)
        if not elim:
            continue

        new_body: list[Instr] = []
        for i in fn.body:
            if isinstance(i, IAllocClosure) and i.dst.name in elim:
                continue                        # dead: all uses were the calls below
            if (isinstance(i, IAssign) and isinstance(i.src, Tmp)
                    and root.get(i.src.name) in elim
                    and root.get(i.dst.name) == root.get(i.src.name)):
                continue                        # dead alias copy
            if (isinstance(i, IClosureCall) and isinstance(i.fn, Tmp)
                    and root.get(i.fn.name) in elim):
                fnm, caps = info[root[i.fn.name]]
                new_body.extend(_inline_closure(fnmap[fnm], i, caps, globals_, _next_site()))
                continue
            new_body.append(i)
        fn.body = new_body

    return _prune_unreachable(tac)


# -- RV32I peephole (O4, post-gen assembly pass) -----------------------------
#
# All the passes above rewrite TAC. This one is different: it runs AFTER asm.gen,
# on the emitted RV32I assembly text, because the redundancies it targets are
# artefacts of instruction selection + linear-scan regalloc that simply do not
# exist at the TAC level. The generator emits every fragment self-contained: it
# reloads its operands into the caller-saved scratch registers t0-t6, computes
# into a scratch, then copies the result to the allocated (callee-saved s-*) home
# of the destination temp. So a TAC `IAssign s2 = s1` becomes `mv t0, s1; mv s2, t0`,
# a binop becomes `mv t0,l; mv t1,r; add t2,t0,t1; mv dst,t2`, a field read becomes
# `mv t0, base; lw t1, k(t0); mv dst, t1`, and so on. The scratch round-trips are
# pure overhead the peephole removes.
#
# THE LOAD-BEARING INVARIANT that makes this sound WITHOUT whole-function register
# liveness: a t-register (t0-t6) never carries a live value across a basic-block
# boundary (a label, a branch, a call, a jump, a `jalr`, or `ret`). The generator
# always writes a t-reg (via a load) before reading it within the fragment that
# uses it, and never reads a t-reg in one fragment that was written in a previous
# one. Arguments are passed in a-regs and the return value is read from a0, so no
# t-reg is ever live INTO a call/branch/return either. Hence at every window
# boundary the live-out set of t-registers is EMPTY, and reasoning about t-regs can
# be done independently inside each straight-line window. (a-registers and s-regs
# DO carry values across boundaries — a0 holds a call's result — so the peephole
# never rewrites or deletes their definitions; it only substitutes/eliminates the
# transient t-registers.) The observable-equivalence guard (optbench --levels …,4)
# is the backstop that verifies the whole thing end to end.
#
# Three transforms, all confined to a straight-line "window" (a maximal run of
# instructions with no interior label and ending at the first control-flow op):
#   (A) copy propagation — `mv tX, R` lets later reads of tX (as a register or a
#       memory base) be rewritten to R; the now-dead copy is then removed by (B).
#   (B) dead-scratch elimination — a pure instruction whose t-reg destination is
#       never read again in the window is deleted (its result is dead).
#   (C) result coalescing — a pure `<op> tX, …` immediately followed by `mv D, tX`
#       (with tX dead after) is retargeted to `<op> D, …`, dropping the copy.
# Plus two structural rewrites over the whole listing: delete `mv rX, rX`, and
# delete a `j L` that falls straight through to `L:`.

import re

_TREGS = frozenset(f"t{i}" for i in range(7))            # t0..t6 — pure scratch
_REG_RE = re.compile(r"^(zero|ra|sp|gp|tp|fp|t[0-6]|a[0-7]|s(?:1[01]|[0-9]))$")
_MEM_RE = re.compile(r"^(-?\w+)\((\w+)\)$")               # off(reg)

# Instructions whose FIRST operand is a written destination register. Every one is
# side-effect-free (no store, no call), so a dead instance is safe to delete and a
# live one is safe to retarget to a different destination register.
_WRITE_FIRST = frozenset({
    "mv", "li", "la", "lw",
    "add", "sub", "mul", "div", "rem", "and", "or", "xor",
    "sll", "srl", "sra", "slt", "sltu",
    "addi", "andi", "ori", "xori", "slli", "srli", "srai", "slti",
    "neg", "not", "seqz", "snez",
})
_BRANCH2 = frozenset({"beq", "bne", "blt", "bge", "bltu", "bgeu"})
_BRANCH1 = frozenset({"bnez", "beqz", "bltz", "bgez", "bgtz", "blez"})
# Every mnemonic asm.gen can emit. A window containing anything else is left
# untouched (defensive: an unmodelled instruction could read/write a t-reg in a way
# the analysis below does not account for).
_KNOWN = _WRITE_FIRST | _BRANCH2 | _BRANCH1 | frozenset({
    "sw", "sb", "sh", "call", "ret", "j", "jal", "jalr",
})


def _parse(line: str):
    """(mnem, ops, comment) for an instruction line, else None (label/dir/blank)."""
    code, sep, comment = line.partition("#")
    s = code.strip()
    if not s or s.endswith(":") or s.startswith("."):
        return None
    head = s.split(None, 1)
    mnem = head[0]
    ops = [o.strip() for o in head[1].split(",")] if len(head) > 1 else []
    return mnem, ops, ("#" + comment) if sep else ""


def _render(mnem: str, ops: list[str], comment: str) -> str:
    body = f"  {mnem}" + (f"  {', '.join(ops)}" if ops else "")
    return f"{body}  {comment}" if comment else body


def _base(op: str) -> str | None:
    """The register an operand reads/writes: itself if a plain register, the base of
    a `off(reg)` memory operand, else None (immediate / label / symbol)."""
    m = _MEM_RE.match(op)
    if m:
        return m.group(2)
    return op if _REG_RE.match(op) else None


def _sub(op: str, old: str, new: str) -> str:
    m = _MEM_RE.match(op)
    if m:
        return f"{m.group(1)}({new})" if m.group(2) == old else op
    return new if op == old else op


def _reads(mnem: str, ops: list[str]) -> set[str]:
    """Registers this instruction READS."""
    if mnem in _WRITE_FIRST:
        return {b for op in ops[1:] if (b := _base(op))}
    if mnem in ("sw", "sb", "sh"):
        return {b for op in ops if (b := _base(op))}
    if mnem in _BRANCH2:
        return {op for op in ops[:2] if _REG_RE.match(op)}
    if mnem in _BRANCH1:
        return {ops[0]} if ops and _REG_RE.match(ops[0]) else set()
    if mnem == "jalr":
        r = {b for op in ops if (b := _base(op))}
        if ops and _REG_RE.match(ops[0]):
            r.discard(ops[0])                 # first operand is the link (write)
        return r
    return set()                              # call / ret / j / jal — no t-reg reads


def _wdst(mnem: str, ops: list[str]) -> str | None:
    """The destination register, if this instruction writes one via `_WRITE_FIRST`."""
    if mnem in _WRITE_FIRST and ops and _REG_RE.match(ops[0]):
        return ops[0]
    return None


class _I:
    """A mutable instruction record inside a window."""
    __slots__ = ("mnem", "ops", "comment", "orig", "dead")

    def __init__(self, mnem, ops, comment):
        self.mnem, self.ops, self.comment = mnem, ops, comment
        self.orig = tuple(ops)
        self.dead = False


def _opt_window(win: list[_I]) -> None:
    """Copy-prop + dead-scratch elimination + result coalescing over one window,
    in place, iterated to a fixpoint. t-registers only."""
    while True:
        changed = False

        # (A) forward copy propagation of `mv tX, R`.
        copy: dict[str, str] = {}
        for ins in win:
            if ins.dead:
                continue
            reads = _reads(ins.mnem, ins.ops)
            for i, op in enumerate(ins.ops):
                b = _base(op)
                if b in _TREGS and b in reads and b in copy:
                    new = _sub(op, b, copy[b])
                    if new != op:
                        ins.ops[i] = new
                        changed = True
            w = _wdst(ins.mnem, ins.ops)
            if w is not None:
                copy.pop(w, None)
                for k in [k for k, v in copy.items() if v == w]:
                    copy.pop(k, None)
            if ins.mnem == "mv" and w in _TREGS and _REG_RE.match(ins.ops[1]):
                src = ins.ops[1]
                copy[w] = copy.get(src, src)

        # (B) backward dead-scratch elimination (live-out of the window = ∅).
        live: set[str] = set()
        for ins in reversed(win):
            if ins.dead:
                continue
            w = _wdst(ins.mnem, ins.ops)
            wt = w if w in _TREGS else None
            if wt is not None and wt not in live:
                ins.dead = True                # pure def of a dead scratch — drop it
                changed = True
                continue
            if wt is not None:
                live.discard(wt)
            live |= _reads(ins.mnem, ins.ops)

        # (C) result coalescing: `<op> tX, …` ; `mv D, tX` (tX dead after) -> `<op> D, …`.
        alive = [ins for ins in win if not ins.dead]
        for a, b in zip(alive, alive[1:]):
            wt = _wdst(a.mnem, a.ops)
            if (wt in _TREGS and b.mnem == "mv" and len(b.ops) == 2
                    and b.ops[1] == wt and _REG_RE.match(b.ops[0])
                    and not _used_after(alive, alive.index(b) + 1, wt)):
                a.ops[0] = b.ops[0]
                b.dead = True
                changed = True

        if not changed:
            return


def _used_after(alive: list[_I], start: int, reg: str) -> bool:
    for ins in alive[start:]:
        if reg in _reads(ins.mnem, ins.ops):
            return True
        if _wdst(ins.mnem, ins.ops) == reg:
            return False                       # redefined before any read — dead
    return False


def _peep_local(lines: list[str], transform=_opt_window) -> list[str]:
    """Apply a windowed transform to the listing. Splits it into straight-line
    windows (broken at labels/directives/blanks and after any control-flow op) and
    runs `transform` (in place, list[_I] -> None) on each window whose every
    instruction is a known mnemonic. `transform` defaults to the t-register peephole
    (`_opt_window`); `immfold` reuses this splitting with its own per-window pass."""
    out: list[str] = []
    win: list[_I] = []
    win_lines: list[int] = []      # indices into `out` where this window's insns sit
    known = True

    def flush():
        nonlocal win, win_lines, known
        if win and known:
            transform(win)
            rebuilt = [_render(ins.mnem, ins.ops, ins.comment)
                       for ins in win if not ins.dead]
            # Replace the window's slice in `out` with the rebuilt instructions.
            lo = win_lines[0]
            del out[lo:lo + len(win_lines)]
            out[lo:lo] = rebuilt
        win = []
        win_lines = []
        known = True

    for line in lines:
        p = _parse(line)
        if p is None:
            flush()
            out.append(line)
            continue
        mnem, ops, comment = p
        out.append(line)
        win.append(_I(mnem, ops, comment))
        win_lines.append(len(out) - 1)
        if mnem not in _KNOWN:
            known = False
        # Control-flow ops terminate the window (they are its last instruction).
        if mnem in _BRANCH2 or mnem in _BRANCH1 or mnem in (
                "call", "ret", "j", "jal", "jalr"):
            flush()
    flush()
    return out


def _peep_selfmove(lines: list[str]) -> list[str]:
    """Delete `mv rX, rX` — a register move with identical source and destination."""
    out: list[str] = []
    for line in lines:
        p = _parse(line)
        if p is not None:
            mnem, ops, _ = p
            if (mnem == "mv" and len(ops) == 2 and ops[0] == ops[1]
                    and _REG_RE.match(ops[0])):
                continue
        out.append(line)
    return out


def _label_of(line: str) -> str | None:
    """The label a line defines (`foo:` / `.fn_loop:` -> `foo` / `.fn_loop`), else
    None. Directives (`.section`, `.word`, …) do not end in `:`, so return None."""
    s = line.split("#", 1)[0].strip()
    return s[:-1] if s.endswith(":") else None


def _peep_fallthrough(lines: list[str]) -> list[str]:
    """Delete a `j L` whose next executable line is `L:` (falls straight through)."""
    def next_code(i: int) -> int:
        j = i + 1
        while j < len(lines):
            s = lines[j].split("#", 1)[0].strip()
            if s:
                return j
            j += 1
        return len(lines)

    drop: set[int] = set()
    for i, line in enumerate(lines):
        p = _parse(line)
        if p is None:
            continue
        mnem, ops, _ = p
        if mnem == "j" and len(ops) == 1:
            nxt = next_code(i)
            if nxt < len(lines):
                lbl = _label_of(lines[nxt])
                if lbl is not None and lbl == ops[0]:
                    drop.add(i)
    return [ln for i, ln in enumerate(lines) if i not in drop]


def peephole(asm: str) -> str:
    """RV32I peephole: window-local t-register copy-prop / dead-scratch elimination /
    result coalescing, then self-move and fall-through-jump removal. Pure asm -> asm."""
    lines = asm.split("\n")
    lines = _peep_local(lines)
    lines = _peep_selfmove(lines)
    lines = _peep_fallthrough(lines)
    return "\n".join(lines)


# -- immfold: immediate-form instruction selection (O4, post-gen) -------------
#
# Tier-4 instruction selection. The generator materialises every
# constant operand of an ALU op with a separate `li tX, IMM`, then does a reg-reg
# op: `x + 1` becomes `li t1, 1; add t2, t0, t1`, a tag test becomes `li t1, TAG;
# sub t2, t0, t1; seqz …`, `x * 4` becomes `li t1, 4; mul t2, t0, t1`. RV32I has
# immediate forms for exactly these — addi/andi/ori/xori/slti — and multiplication
# by a power of two is a shift. Folding the constant INTO the op removes the `li`
# outright: one fewer static instruction AND one fewer executed instruction.
#
# Same window discipline and load-bearing invariant as the peephole (a t-register
# is never live across a window boundary). We track, forward through a window, the
# integer value currently held in each t-register by a `li`; when an ALU op reads a
# t-register whose value is a small constant in the right operand position, we
# rewrite it to the immediate form. The now-dead `li` is swept by re-running the
# peephole's own dead-scratch elimination (`_opt_window`) over the window. Only
# integer `li`s participate — a float-bits `li` carries a `# float` comment and is
# skipped (and float arithmetic lowers to runtime calls, never a reg-reg ALU op, so
# a float constant never reaches one of these instructions anyway).

_IMM_MIN, _IMM_MAX = -2048, 2047           # RV32I 12-bit signed immediate range

# Commutative reg-reg ALU ops with an immediate form (either operand may be the
# constant). Bitwise ANDI/ORI/XORI sign-extend the 12-bit immediate, which equals
# the constant exactly when it fits the signed 12-bit range — the guard below.
_COMM_IMM = {"add": "addi", "and": "andi", "or": "ori", "xor": "xori"}


def _fits12(n: int) -> bool:
    return _IMM_MIN <= n <= _IMM_MAX


def _pow2_shift(n: int) -> int | None:
    """k such that n == 2**k for k in 1..31, else None (mul-by-pow2 -> slli)."""
    if n >= 2 and (n & (n - 1)) == 0:
        return n.bit_length() - 1
    return None


def _li_int(ins: "_I") -> int | None:
    """The integer an `li tX, N` loads, or None if not an integer-`li` into a
    t-register (a float-bits `li` — commented `# float` — is deliberately excluded)."""
    if ins.mnem != "li" or len(ins.ops) != 2 or ins.ops[0] not in _TREGS:
        return None
    if "float" in ins.comment:
        return None
    try:
        return int(ins.ops[1])
    except ValueError:
        return None


def _immfold_window(win: list[_I]) -> None:
    """Fold constant `li` operands into immediate-form ALU ops over one window, then
    reuse the peephole's cleanup to drop the `li`s left dead."""
    imm: dict[str, int] = {}          # t-register -> integer constant it currently holds
    for ins in win:
        if ins.dead:
            continue
        m, ops = ins.mnem, ins.ops
        if len(ops) == 3:
            d, a, b = ops
            va, vb = imm.get(a), imm.get(b)
            folded: tuple[str, list[str]] | None = None
            if m in _COMM_IMM:
                nm = _COMM_IMM[m]
                if vb is not None and _fits12(vb):
                    folded = (nm, [d, a, str(vb)])
                elif va is not None and _fits12(va):
                    folded = (nm, [d, b, str(va)])
            elif m == "sub":                       # x - C  ==  x + (-C); only C = rhs
                if vb is not None and _fits12(-vb):
                    folded = ("addi", [d, a, str(-vb)])
            elif m == "slt":                       # a < C is slti; NOT commutative
                if vb is not None and _fits12(vb):
                    folded = ("slti", [d, a, str(vb)])
            elif m == "mul":                       # x * 2^k  ==  x << k
                k = _pow2_shift(vb) if vb is not None else None
                if k is not None:
                    folded = ("slli", [d, a, str(k)])
                else:
                    k = _pow2_shift(va) if va is not None else None
                    if k is not None:
                        folded = ("slli", [d, b, str(k)])
            if folded is not None:
                ins.mnem, ins.ops = folded
        # Update the tracked constant for the register this instruction writes.
        w = _wdst(ins.mnem, ins.ops)
        if w is not None:
            imm.pop(w, None)
        v = _li_int(ins)
        if v is not None:
            imm[w] = v                             # w == ins.ops[0], a t-register
    # The folds above leave some `li`s with no remaining reader; the peephole's
    # dead-scratch elimination removes them (and re-coalesces if that exposes more).
    _opt_window(win)


def immfold(asm: str) -> str:
    """RV32I immediate-form instruction selection: fold `li`-materialised constants
    into addi/andi/ori/xori/slti and mul-by-power-of-two into slli, dropping the
    `li`. Pure asm -> asm; runs after `peephole` (which leaves the `li tX, C; <op>
    …, tX` shape this folds)."""
    return "\n".join(_peep_local(asm.split("\n"), _immfold_window))


# -- branchlayout: conditional-branch inversion for fall-through (O4, post-gen)
#
# Tier-4 branch layout. Every `ICondJump` lowers to a taken
# conditional branch plus an unconditional jump: `bnez tX, TRUE; j FALSE`. The
# peephole's fall-through removal already drops the `j` when FALSE is the next
# block. When TRUE is instead the next block, the taken jump can be saved by
# inverting the branch: `bnez tX, TRUE; j FALSE; TRUE:` becomes `beqz tX, FALSE;
# TRUE:` — control still reaches TRUE by fall-through when the condition holds and
# FALSE by the branch otherwise. One fewer static and (when taken) executed jump.

_BRANCH_INVERT = {
    "bnez": "beqz", "beqz": "bnez",
    "beq": "bne", "bne": "beq",
    "blt": "bge", "bge": "blt",
    "bltu": "bgeu", "bgeu": "bltu",
    "bltz": "bgez", "bgez": "bltz",
    "bgtz": "blez", "blez": "bgtz",
}


def branchlayout(asm: str) -> str:
    """Invert a conditional branch whose target is the fall-through block, deleting
    the following unconditional jump. Pure asm -> asm."""
    lines = asm.split("\n")

    def next_code(i: int) -> int:
        j = i + 1
        while j < len(lines):
            if lines[j].split("#", 1)[0].strip():
                return j
            j += 1
        return len(lines)

    out = list(lines)
    drop: set[int] = set()
    for i, line in enumerate(lines):
        p = _parse(line)
        if p is None:
            continue
        mnem, ops, comment = p
        if mnem not in _BRANCH_INVERT or not ops:
            continue
        nj = next_code(i)                          # expect the `j FALSE`
        if nj >= len(lines):
            continue
        pj = _parse(lines[nj])
        if pj is None or pj[0] != "j" or len(pj[1]) != 1:
            continue
        nl = next_code(nj)                         # expect `TRUE:` (the branch target)
        if nl >= len(lines) or _label_of(lines[nl]) != ops[-1]:
            continue
        false_lbl = pj[1][0]
        new_ops = ops[:-1] + [false_lbl]
        out[i] = _render(_BRANCH_INVERT[mnem], new_ops, comment)
        drop.add(nj)                               # delete the now-redundant `j FALSE`
    return "\n".join(ln for k, ln in enumerate(out) if k not in drop)


# -- Pass registry -----------------------------------------------------------
#
# Each entry is (name, fn) where fn : TAC -> TAC. Order here is the order passes
# run in a single optimize() sweep. A level enables a subset (LEVELS below); the
# subset always runs in this PASSES order. O2's devirt + inline lead so the Tier-1
# passes that follow clean up across the exposed call boundaries; licm trails.
# O3's closure_elim runs right after inline (which exposes local closures) and
# before the Tier-1 cleanup passes (which sweep up the copies it leaves).

PassFn = "callable"  # TAC -> TAC

PASSES: list[tuple[str, object]] = [
    ("devirt",       devirt),              # O2 — trait-dispatch devirtualization
    ("inline",       inline),              # O2 — + reachable-function pruning
    ("closure_elim", closure_elim),        # O3 — scalar-replace non-escaping closures
    ("const_fold", const_fold),            # -O1
    ("copy_prop",  copy_prop),             # -O1
    ("algebraic",  algebraic_simplify),    # -O1
    ("cse",        cse),                   # -O1 — see CSE_ELIGIBLE below
    ("dce",        dce),                   # -O1
    ("licm",       licm),                  # O2 — loop-invariant code motion
]

_PASS_NAMES: tuple[str, ...] = tuple(name for name, _ in PASSES)


# Post-generation passes run on the emitted RV32I ASSEMBLY (str -> str), AFTER the
# TAC passes above and asm.gen. They are kept in their own registry because they
# operate on a different IR (asm text, not TAC); optbench.postgen applies them and
# the level bundles (LEVELS) name them alongside the TAC passes.
ASM_PASSES: list[tuple[str, object]] = [
    ("peephole",     peephole),            # O4 — RV32I t-register peephole
    ("immfold",      immfold),             # O4 — immediate-form instruction selection
    ("branchlayout", branchlayout),        # O4 — invert branch to fall through to target
]
_ASM_PASS_NAMES: tuple[str, ...] = tuple(name for name, _ in ASM_PASSES)


# -- CSE eligibility invariant ------------------------------------------------
#
# When the `cse` pass is written, this is the load-bearing correctness rule.
#
# CSE collapses two identical expressions into one computed value. For an
# ALLOCATING prim (string_slice, char_to_string, the string_to_{int,float} raw
# stubs — all "pure in result, but allocate a fresh heap object") this means two
# calls that today return DISTINCT-but-equal heap objects would return the SAME
# object. That is sound in Lark ONLY because of two language properties:
#
#   1. Values are IMMUTABLE — no ref cell, mutable array, in-place record update,
#      or mutable buffer exists. Aliasing a shared result is therefore
#      unobservable: nothing can mutate one alias and see the change in the other.
#   2. Equality is STRUCTURAL — there is no physical/reference equality (`is`,
#      `===`, identity hash). So two equal objects are indistinguishable whether
#      or not they share storage.
#
# If EITHER property is ever weakened (a mutable value type, or exposed pointer
# identity), CSE over allocating prims becomes UNSOUND and this invariant must be
# revisited. Both are deliberate language-design decisions, not on the roadmap;
# this note is the tripwire if that ever changes.
#
# DESIGN RULE — make CSE eligibility an ALLOWLIST, not a blocklist. CSE only prims
# named in CSE_ELIGIBLE below. Then a future effectful/mutable/nondeterministic
# prim is safe BY DEFAULT: it is simply absent from the list and never CSE'd, with
# no action required. A blocklist ("CSE everything except…") fails the opposite,
# dangerous way — a new mutable prim gets silently CSE'd and breaks. Eligibility
# also requires PURITY: never add an IO/effectful/nondeterministic prim here
# (`read`, a clock, randomness) — those must be recomputed, not shared. `read`
# already lives in IO and is not a candidate.
CSE_ELIGIBLE: frozenset[str] = frozenset({
    # Pure, immutable-result prims safe to CSE. Populate when the cse pass lands.
    # e.g. "string_slice", "char_to_string", "string_index",
    #      "float_to_bits", "__string_to_int_raw", "__string_to_float_raw",
    # plus pure arithmetic/comparison IBinOp/IUnary (handled by opcode, not name).
})


# -- Levels ------------------------------------------------------------------
#
# LEVELS[n] = the set of pass names enabled at -On. -O0 enables nothing.
# A level enables every pass named in it *that also exists in PASSES*, so a level
# can be declared ahead of the passes it will bundle without breaking.

LEVELS: dict[int, tuple[str, ...]] = {
    0: (),
    1: ("const_fold", "copy_prop", "algebraic", "cse", "dce"),
    2: ("const_fold", "copy_prop", "algebraic", "cse", "dce",
        "inline", "devirt", "licm"),
    3: ("const_fold", "copy_prop", "algebraic", "cse", "dce",
        "inline", "devirt", "licm",
        "closure_elim", "unbox", "fusion", "arena_reuse"),
    # O4 = all the O3 TAC passes, PLUS the post-gen RV32I peephole (increment 1)
    # and graph-coloring register allocation (increment 2, `regalloc_color`). The
    # TAC subset is identical to O3 by design; O4's improvement over O3 is
    # attributable to the two backend items. `regalloc_color` is neither a TAC
    # pass (PASSES) nor an asm-text pass (ASM_PASSES) — it is a codegen strategy
    # selected inside asm.gen (see wants_graph_coloring / CODEGEN_FLAGS), so it is
    # merely NAMED here and is a no-op to enabled_passes/enabled_asm_passes.
    4: ("const_fold", "copy_prop", "algebraic", "cse", "dce",
        "inline", "devirt", "licm",
        "closure_elim", "unbox", "fusion", "arena_reuse",
        "peephole", "immfold", "branchlayout", "regalloc_color"),
}
MAX_LEVEL = max(LEVELS)

# Codegen-strategy flags: named in LEVELS bundles like passes, but dispatched
# inside asm.gen rather than by optimize()/postgen (they are neither a TAC nor an
# asm-text transform). Listed by --pass-flags for discoverability.
CODEGEN_FLAGS: tuple[str, ...] = (
    "regalloc_color",   # O4 — graph-coloring regalloc instead of linear scan
)


@dataclass
class OptOptions:
    """
    Which passes run. `level` selects a bundle; `enable`/`disable` override
    individual passes on top of it (for attribution / bisection). A pass runs iff
    it is in PASSES and (in the level's bundle or force-enabled) and not
    force-disabled.
    """
    level:   int             = 0
    enable:  frozenset[str]  = field(default_factory=frozenset)
    disable: frozenset[str]  = field(default_factory=frozenset)

    @staticmethod
    def O(level: int) -> "OptOptions":
        return OptOptions(level=level)


def _bundle(opts: OptOptions) -> set[str]:
    bundle = set(LEVELS.get(opts.level, ()))
    bundle |= set(opts.enable)
    bundle -= set(opts.disable)
    return bundle


def enabled_passes(opts: OptOptions) -> list[tuple[str, object]]:
    """The (name, fn) list that optimize() will actually run, in PASSES order."""
    bundle = _bundle(opts)
    return [(name, fn) for name, fn in PASSES if name in bundle]


def enabled_asm_passes(opts: OptOptions) -> list[tuple[str, object]]:
    """The post-gen asm (name, fn) list postgen() will run, in ASM_PASSES order."""
    bundle = _bundle(opts)
    return [(name, fn) for name, fn in ASM_PASSES if name in bundle]


def wants_graph_coloring(opts: OptOptions) -> bool:
    """Whether asm.gen should use the graph-coloring allocator (-O4)
    instead of linear scan. A codegen strategy, not a TAC/asm pass — see
    CODEGEN_FLAGS. optbench queries this and passes the coloring allocator to
    gen()."""
    return "regalloc_color" in _bundle(opts)


def postgen(asm: str, opts: OptOptions | None = None) -> str:
    """Apply the enabled post-generation asm passes to the emitted RV32I assembly.
    At -O0..-O3 no asm pass is enabled, so this is the identity — the assembly is
    returned unchanged (byte-identical to the un-peepholed pipeline)."""
    if opts is None:
        opts = OptOptions()
    for _name, fn in enabled_asm_passes(opts):
        asm = fn(asm)
    return asm


# Iterate the whole enabled sweep to a fixpoint (-O3). One sweep of
# `inline` + `closure_elim` peels ONE layer: inlining a HOF (compose/twice) exposes
# the closure it returned as a local alloc-then-call, which closure_elim then
# scalar-replaces — but the closure body it splices in may itself contain further
# closure calls (`compose(f,g) = \x -> f(g(x))`), which only the NEXT sweep sees.
# Re-running until the TAC stops changing collapses these nested closures one level
# per sweep. Every pass is a sound reducer or a bounded (single-level, prune-backed)
# expander, so the composition converges; MAX_SWEEPS caps the (finite) inlining
# depth as a safety net — stopping early only leaves optimization on the table, it
# never breaks the observable-equivalence guard.
_MAX_SWEEPS = 8

def _fingerprint(tac: TAC):
    """A cheap value identity of the whole program for fixpoint detection. Instr
    are frozen dataclasses (comparable by value), so equal fingerprints ⇒ every
    function body is instruction-for-instruction identical."""
    return tuple((f.name, tuple(f.body)) for f in tac.functions)


def optimize(tac: TAC, opts: OptOptions | None = None) -> TAC:
    """
    Apply the enabled passes, in PASSES order, iterating the sweep to a fixpoint,
    and return the transformed TAC. At -O0 (default) no passes are enabled, so this
    is the identity — the TAC is returned unchanged.
    """
    if opts is None:
        opts = OptOptions()
    passes = enabled_passes(opts)
    if not passes:
        return tac
    for _ in range(_MAX_SWEEPS):
        before = _fingerprint(tac)
        for _name, fn in passes:
            tac = fn(tac)
        if _fingerprint(tac) == before:
            break
    return tac
