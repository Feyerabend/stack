"""
Lark certifying register-allocation checker — Phase 9, Track C step 3.

The allocator (regalloc.py) is ~200 lines of interval bookkeeping that no
proof touches.  Instead of proving it, every compilation *certifies* its
output: this module independently validates each Allocation against the
function it was computed for, and asm.gen() refuses to emit code for an
allocation that fails.  A certificate failure is an internal compiler
error, not a user diagnostic — it raises loudly instead of joining
infer.DIAGNOSTICS.

Independence is the point.  The allocator derives interference from
cfg.py + liveness.py; a bug in that shared analysis would fool the old
igraph-based verify() too, because both sides would see the same wrong
facts.  This checker therefore re-derives everything from scratch, and
differently: it works on the *flat* instruction list (no basic blocks),
builds its own successor map from labels, defines its own per-instruction
def/use, and runs its own backward fixpoint to per-instruction liveness.
The only shared artifact is the TAC instruction set itself — the spec.

Checks, per function:
  R1  completeness — every Tmp the body mentions (and every parameter)
      has a register or a spill slot; globals live in .data and are exempt
  R2  unambiguity  — no Tmp has both a register and a spill slot
  R3  register exclusivity — at every program point, simultaneously live
      Tmps occupy distinct registers; additionally no instruction writes
      a register that a *different* live-out Tmp occupies (a dead def
      still emits a write, which would clobber a cohabitant)
  R4  spill-slot exclusivity — the same two conditions for slot indices
  R5  slot sanity — slot indices lie in [0, num_slots)

The checker's per-point liveness is strictly finer than the allocator's
live intervals, so every violation it reports is real for this allocator
(no false positives), while remaining sound for the emitted code.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tac import (
    TAC, Function, Tmp,
    IAssign, IBinOp, IUnary,
    ICall, IClosureCall, IReturn,
    ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
    Instr,
)
from regalloc import Allocation


class RegAllocCertificateError(Exception):
    """The register allocator produced an allocation that fails its
    certificate.  This is a compiler bug: it must never be caught and
    turned into a user-facing diagnostic."""
    def __init__(self, fn_name: str, violations: list[str]) -> None:
        self.fn_name    = fn_name
        self.violations = violations
        detail = "\n  ".join(violations)
        super().__init__(
            f"register allocation certificate failed for {fn_name!r}:\n"
            f"  {detail}")


# ── Independent def / use ─────────────────────────────────────────────────────
# Written against the tac.py instruction spec, deliberately not imported
# from liveness.py.

def _names(*vs) -> frozenset[str]:
    return frozenset(v.name for v in vs if isinstance(v, Tmp))


def _defs(instr: Instr) -> frozenset[str]:
    match instr:
        case (IAssign(dst=d) | IBinOp(dst=d) | IUnary(dst=d)
              | IClosureCall(dst=d) | IAlloc(dst=d) | IGetTag(dst=d)
              | IGetField(dst=d) | IAllocClosure(dst=d)):
            return frozenset({d.name})
        case ICall(dst=d) if d is not None:
            return frozenset({d.name})
        case _:
            return frozenset()


def _uses(instr: Instr) -> frozenset[str]:
    match instr:
        case IAssign(src=s):                  return _names(s)
        case IBinOp(l=l, r=r):                return _names(l, r)
        case IUnary(src=s):                   return _names(s)
        case ICall(args=args):                return _names(*args)
        case IClosureCall(fn=f, arg=a):       return _names(f, a)
        case IReturn(val=v):                  return _names(v)
        case ICondJump(cond=c):               return _names(c)
        case IAlloc(fields=fs):               return _names(*fs)
        case IGetTag(src=s):                  return _names(s)
        case IGetField(src=s):                return _names(s)
        case IAllocClosure(captured=caps):    return _names(*caps)
        case _:                               return frozenset()


# ── Independent flat-list liveness ────────────────────────────────────────────

def _successors(body: list[Instr]) -> list[list[int]]:
    """Successor instruction indices, straight off the flat list."""
    labels = {instr.name: i for i, instr in enumerate(body)
              if isinstance(instr, ILabel)}
    succs: list[list[int]] = []
    last = len(body) - 1
    for i, instr in enumerate(body):
        match instr:
            case IReturn():
                succs.append([])
            case IJump(label=l):
                succs.append([labels[l]])
            case ICondJump(label=l):
                nxt = [labels[l]]
                if i < last:
                    nxt.append(i + 1)
                succs.append(nxt)
            case _:
                succs.append([i + 1] if i < last else [])
    return succs


def _liveness(body: list[Instr]) -> tuple[list[frozenset[str]],
                                          list[frozenset[str]]]:
    """Per-instruction (live_in, live_out) by backward fixpoint."""
    n     = len(body)
    succs = _successors(body)
    use   = [_uses(ins) for ins in body]
    dfs   = [_defs(ins) for ins in body]

    live_in:  list[frozenset[str]] = [frozenset()] * n
    live_out: list[frozenset[str]] = [frozenset()] * n

    changed = True
    while changed:
        changed = False
        for i in range(n - 1, -1, -1):
            lo = frozenset().union(*(live_in[s] for s in succs[i])) \
                 if succs[i] else frozenset()
            li = use[i] | (lo - dfs[i])
            if lo != live_out[i] or li != live_in[i]:
                live_out[i] = lo
                live_in[i]  = li
                changed = True
    return live_in, live_out


# ── The certificate ───────────────────────────────────────────────────────────

def check_fn(fn: Function, alloc: Allocation,
             global_names: frozenset[str]) -> list[str]:
    """Validate one function's allocation.  Returns violations (empty = ok)."""
    violations: list[str] = []
    body = fn.body

    mentioned: set[str] = set(fn.params)
    for ins in body:
        mentioned |= _defs(ins) | _uses(ins)

    # R1 completeness + R2 unambiguity + R5 slot sanity
    for name in sorted(mentioned):
        has_reg  = name in alloc.reg
        has_slot = name in alloc.slot
        if has_reg and has_slot:
            violations.append(f"R2: {name!r} has both register "
                              f"{alloc.reg[name]} and slot {alloc.slot[name]}")
        if not has_reg and not has_slot and name not in global_names:
            violations.append(f"R1: {name!r} has no register and no slot")
        if has_slot and not (0 <= alloc.slot[name] < alloc.num_slots):
            violations.append(f"R5: {name!r} slot {alloc.slot[name]} outside "
                              f"[0, {alloc.num_slots})")

    live_in, live_out = _liveness(body)

    def _pairwise(live: frozenset[str], where: str) -> None:
        by_reg:  dict[str, str] = {}
        by_slot: dict[int, str] = {}
        for name in sorted(live):
            r = alloc.reg.get(name)
            if r is not None:
                if r in by_reg:
                    violations.append(
                        f"R3: {by_reg[r]!r} and {name!r} both live {where}, "
                        f"both in {r}")
                else:
                    by_reg[r] = name
            s = alloc.slot.get(name)
            if s is not None:
                if s in by_slot:
                    violations.append(
                        f"R4: {by_slot[s]!r} and {name!r} both live {where}, "
                        f"both in slot {s}")
                else:
                    by_slot[s] = name

    # R3/R4 at every program point (entry uses instruction 0's live-in)
    for i in range(len(body)):
        _pairwise(live_in[i], f"before instr {i}")

    # R3/R4 at def points: a write lands in the destination's location even
    # when the destination is dead afterwards — it must not clobber a
    # different Tmp that survives the instruction.
    for i, ins in enumerate(body):
        for d in _defs(ins):
            dr = alloc.reg.get(d)
            ds = alloc.slot.get(d)
            for other in sorted(live_out[i]):
                if other == d:
                    continue
                if dr is not None and alloc.reg.get(other) == dr:
                    violations.append(
                        f"R3: instr {i} writes {d!r} in {dr}, clobbering "
                        f"live {other!r}")
                if ds is not None and alloc.slot.get(other) == ds:
                    violations.append(
                        f"R4: instr {i} writes {d!r} in slot {ds}, "
                        f"clobbering live {other!r}")

    return violations


def check_tac(tac: TAC, allocs: list[Allocation]) -> None:
    """Certify every function's allocation; raise on the first failure."""
    global_names = frozenset(tac.global_names)
    for fn, alloc in zip(tac.functions, allocs):
        violations = check_fn(fn, alloc, global_names)
        if violations:
            raise RegAllocCertificateError(fn.name, violations)


# ── CLI: certify one file's allocations ───────────────────────────────────────

if __name__ == "__main__":
    import parser as _parser
    import infer  as _infer
    from lower    import lower
    from regalloc import allocate_tac

    if len(sys.argv) < 2:
        print("usage: python3 src/regcheck.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    try:
        prog  = _parser.parse_file(path)
        tprog = _infer.typecheck(prog, source_file=path)
    except (*_infer.DIAGNOSTICS, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
    tac    = lower(tprog)
    allocs = allocate_tac(tac)
    check_tac(tac, allocs)
    for a in allocs:
        print(f"  ok  {a.fn_name}  ({len(a.reg)} reg, {a.num_slots} spill)")
    print("all allocations certified")
