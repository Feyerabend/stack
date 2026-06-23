"""
Lark liveness — backward dataflow liveness analysis over a CFG.

Computes live_in / live_out (sets of Tmp names) per basic block,
then per-instruction live sets for interference graph construction.

Algorithm: iterative backward dataflow, worklist-driven.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tac import (
    Tmp, Instr,
    IAssign, IBinOp, IUnary,
    ICall, IClosureCall, IReturn,
    ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
)
from cfg import BasicBlock, CFG


# ── Def / use of one instruction ──────────────────────────────────────────────

def _val(v) -> frozenset[str]:
    return frozenset({v.name}) if isinstance(v, Tmp) else frozenset()

def _vals(*vs) -> frozenset[str]:
    return frozenset(v.name for v in vs if isinstance(v, Tmp))


def defs(instr: Instr) -> frozenset[str]:
    match instr:
        case IAssign(dst=d):              return frozenset({d.name})
        case IBinOp(dst=d):               return frozenset({d.name})
        case IUnary(dst=d):               return frozenset({d.name})
        case ICall(dst=d) if d is not None: return frozenset({d.name})
        case IClosureCall(dst=d):         return frozenset({d.name})
        case IAlloc(dst=d):               return frozenset({d.name})
        case IGetTag(dst=d):              return frozenset({d.name})
        case IGetField(dst=d):            return frozenset({d.name})
        case IAllocClosure(dst=d):        return frozenset({d.name})
        case _:                           return frozenset()


def uses(instr: Instr) -> frozenset[str]:
    match instr:
        case IAssign(src=s):                    return _val(s)
        case IBinOp(l=l, r=r):                  return _vals(l, r)
        case IUnary(src=s):                     return _val(s)
        case ICall(args=args):                  return _vals(*args)
        case IClosureCall(fn=f, arg=a):         return _vals(f, a)
        case IReturn(val=v) if v is not None:   return _val(v)
        case ICondJump(cond=c):                 return _val(c)
        case IAlloc(fields=fs):                 return _vals(*fs)
        case IGetTag(src=s):                    return _val(s)
        case IGetField(src=s):                  return _val(s)
        case IAllocClosure(captured=caps):      return _vals(*caps)
        case _:                                 return frozenset()


# ── Per-block gen / kill ───────────────────────────────────────────────────────

def block_gen_kill(blk: BasicBlock) -> tuple[frozenset[str], frozenset[str]]:
    """Scan forward: gen = upward-exposed uses; kill = defined Tmps."""
    gen:  set[str] = set()
    kill: set[str] = set()
    for instr in blk.instrs:
        gen  |= uses(instr) - kill
        kill |= defs(instr)
    return frozenset(gen), frozenset(kill)


# ── Iterative backward dataflow ────────────────────────────────────────────────

class Liveness:
    """
    live_in[lbl]  — Tmps live on entry to block lbl
    live_out[lbl] — Tmps live on exit from block lbl
    """

    def __init__(self, cfg: CFG):
        self.cfg      = cfg
        self.live_in:  dict[str, frozenset[str]] = {}
        self.live_out: dict[str, frozenset[str]] = {}
        self._run()

    def _run(self) -> None:
        cfg = self.cfg

        gen:  dict[str, frozenset[str]] = {}
        kill: dict[str, frozenset[str]] = {}
        for blk in cfg:
            gen[blk.label], kill[blk.label] = block_gen_kill(blk)
            self.live_in[blk.label]  = frozenset()
            self.live_out[blk.label] = frozenset()

        worklist: list[str] = [blk.label for blk in cfg]
        in_wl:    set[str]  = set(worklist)

        while worklist:
            lbl = worklist.pop()
            in_wl.discard(lbl)
            blk = cfg.block(lbl)

            lo = frozenset().union(*(self.live_in[s]
                                     for s in blk.succs
                                     if s in cfg.blocks))
            li = gen[lbl] | (lo - kill[lbl])

            self.live_out[lbl] = lo

            if li != self.live_in[lbl]:
                self.live_in[lbl] = li
                for p in blk.preds:
                    if p not in in_wl:
                        worklist.append(p)
                        in_wl.add(p)

    # ── Per-instruction liveness (for interference graph) ─────────────────────

    def live_before(self, blk: BasicBlock) -> list[frozenset[str]]:
        """
        Returns live[i] = set of Tmps live BEFORE instrs[i], for i in range(n).
        live[n] would be live_out[blk] — not included; use self.live_out directly.

        Computed backward from live_out.
        """
        instrs = blk.instrs
        n      = len(instrs)
        live: list[frozenset[str]] = [frozenset()] * (n + 1)
        live[n] = self.live_out[blk.label]
        for i in range(n - 1, -1, -1):
            live[i] = (live[i + 1] - defs(instrs[i])) | uses(instrs[i])
        return live[:n]


def analyse(cfg: CFG) -> Liveness:
    return Liveness(cfg)


# ── Pretty printer ─────────────────────────────────────────────────────────────

def pretty_liveness(lv: Liveness) -> str:
    cfg = lv.cfg
    lines = [f"Liveness for {cfg.fn_name!r}:"]
    for blk in cfg:
        li  = sorted(lv.live_in[blk.label])
        lo  = sorted(lv.live_out[blk.label])
        lines.append(f"  [{blk.label}]")
        lines.append(f"    in:  {{{', '.join(li)}}}")
        lines.append(f"    out: {{{', '.join(lo)}}}")
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import parser as _parser
    import infer  as _infer
    from lower import lower
    from cfg   import cfg_of_tac

    if len(sys.argv) < 2:
        print("usage: python3 src/liveness.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)
    for cfg in cfg_of_tac(tac):
        print(pretty_liveness(analyse(cfg)))
        print()
