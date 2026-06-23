"""
Lark linear-scan register allocator (Poletto & Sarkar, 1999).

Pipeline:  CFG + Liveness  →  live intervals  →  linear scan  →  Allocation

Allocation maps every Tmp name to either a physical register or a spill slot.

Register pool: s1–s11 (11 callee-saved RISC-V registers).
  Callee-saved registers survive across ICall/IClosureCall without any
  caller-side save/restore in the code generator.  The function prologue
  saves every s-register actually used; the epilogue restores them.

Spill slots are 4-byte words at negative offsets from the frame pointer:
  slot n → fp − (save_area + (n+1)·4)
  where save_area = 8 + 4·len(regs_used)  (ra + saved fp + callee-saved s-regs)
The exact byte offset is computed in asm.py's spill_off(); location() below
shows a simplified form for display only.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass, field
from tac import Instr, TAC
from cfg import CFG, cfg_of_tac
from liveness import Liveness, analyse, defs, uses

# Callee-saved RISC-V registers available for allocation
_REGS: list[str] = [f"s{i}" for i in range(1, 12)]   # s1 … s11


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class Interval:
    """Live interval for one Tmp in the linearized instruction stream."""
    name:  str
    start: int    # first instruction number where the Tmp is live
    end:   int    # last  instruction number where the Tmp is live

    def __lt__(self, other: "Interval") -> bool:
        return self.start < other.start

    def overlaps(self, other: "Interval") -> bool:
        return self.start <= other.end and other.start <= self.end


@dataclass
class Allocation:
    """Register assignment and spill decisions for one function."""
    fn_name:   str
    reg:       dict[str, str]    # Tmp → "s1"…"s11"
    slot:      dict[str, int]    # Tmp → spill-slot index
    num_slots: int               # total spill slots
    regs_used: list[str]         # callee-saved regs actually used (for prologue)

    def location(self, name: str) -> str:
        """Human-readable location: register name or 'N(s0)'."""
        if name in self.reg:
            return self.reg[name]
        if name in self.slot:
            return f"{-(self.slot[name] + 1) * 4}(s0)"
        return f"<unallocated:{name}>"

    def is_reg(self, name: str) -> bool:
        return name in self.reg

    def is_spill(self, name: str) -> bool:
        return name in self.slot


# ── Step 1: linearize ─────────────────────────────────────────────────────────

def _linearize(cfg: CFG) -> dict[str, int]:
    """Assign instruction numbers in CFG block order.
    Returns block_start: block label → first instruction number."""
    block_start: dict[str, int] = {}
    n = 0
    for blk in cfg:
        block_start[blk.label] = n
        n += len(blk.instrs)
    return block_start


# ── Step 2: compute live intervals ────────────────────────────────────────────

def _compute_intervals(cfg: CFG, lv: Liveness,
                       block_start: dict[str, int],
                       params: list[str] | None = None) -> dict[str, Interval]:
    ivs: dict[str, Interval] = {}

    def extend(name: str, point: int) -> None:
        if name in ivs:
            if point < ivs[name].start: ivs[name].start = point
            if point > ivs[name].end:   ivs[name].end   = point
        else:
            ivs[name] = Interval(name=name, start=point, end=point)

    # Parameters arrive in argument registers at function entry (position 0).
    # Force their intervals to start there so the allocator never shares their
    # register with an earlier Tmp (even if the first use is in a later block).
    if params:
        for p in params:
            extend(p, 0)

    for blk in cfg:
        s = block_start[blk.label]
        e = s + len(blk.instrs) - 1   # last instruction position in this block

        if e < s:                      # empty block — nothing to do
            continue

        # Variables live across the entire block
        for name in lv.live_in[blk.label]:
            extend(name, s); extend(name, e)
        for name in lv.live_out[blk.label]:
            extend(name, s); extend(name, e)

        # Individual def/use points
        for i, instr in enumerate(blk.instrs):
            p = s + i
            for name in defs(instr): extend(name, p)
            for name in uses(instr): extend(name, p)

    return ivs


# ── Step 3: linear scan core ──────────────────────────────────────────────────

def _linear_scan(intervals: list[Interval],
                 regs: list[str]) -> tuple[dict[str, str], dict[str, int]]:
    """
    Poletto & Sarkar 1999.
    Intervals are sorted by start on entry (via Interval.__lt__).
    Returns (reg_assign, spill_slots).
    """
    reg_assign:  dict[str, str] = {}
    spill_slots: dict[str, int] = {}
    spill_count: int = 0

    free:   list[str]      = list(regs)   # stack of available registers
    active: list[Interval] = []           # currently live, sorted by end

    for iv in sorted(intervals):
        # Expire intervals that ended before iv starts
        still_active = []
        for a in active:
            if a.end < iv.start:
                free.append(reg_assign[a.name])
            else:
                still_active.append(a)
        active = still_active

        if not free:
            # Spill: the interval with the latest end point
            spill_cand = max(active, key=lambda a: a.end)
            if spill_cand.end > iv.end:
                # Give spill_cand's register to iv; send spill_cand to memory
                reg_assign[iv.name] = reg_assign.pop(spill_cand.name)
                spill_slots[spill_cand.name] = spill_count;  spill_count += 1
                active.remove(spill_cand)
                active.append(iv)
                active.sort(key=lambda a: a.end)
            else:
                spill_slots[iv.name] = spill_count;  spill_count += 1
        else:
            r = free.pop()
            reg_assign[iv.name] = r
            active.append(iv)
            active.sort(key=lambda a: a.end)

    return reg_assign, spill_slots


# ── Top-level ─────────────────────────────────────────────────────────────────

def allocate(cfg: CFG, lv: Liveness,
             regs: list[str] | None = None,
             params: list[str] | None = None) -> Allocation:
    """Linearize → compute intervals → linear scan → Allocation."""
    if regs is None:
        regs = _REGS

    block_start           = _linearize(cfg)
    ivs                   = _compute_intervals(cfg, lv, block_start, params)
    reg_assign, spill_slots = _linear_scan(list(ivs.values()), regs)

    reg_order  = {r: i for i, r in enumerate(_REGS)}
    regs_used  = sorted(set(reg_assign.values()),
                        key=lambda r: reg_order.get(r, 99))

    return Allocation(
        fn_name   = cfg.fn_name,
        reg       = reg_assign,
        slot      = spill_slots,
        num_slots = len(spill_slots),
        regs_used = regs_used,
    )


def allocate_tac(tac: TAC, regs: list[str] | None = None) -> list[Allocation]:
    result = []
    for fn, cfg in zip(tac.functions, cfg_of_tac(tac)):
        lv = analyse(cfg)
        result.append(allocate(cfg, lv, regs, params=list(fn.params)))
    return result


# ── Verifier ──────────────────────────────────────────────────────────────────

def verify(alloc: Allocation, ig) -> list[str]:
    """
    Check that no two interfering Tmps share a register.
    Returns a list of violation strings; empty means correct.
    Uses the IGraph from igraph.py.
    """
    errors: list[str] = []
    for u, nbrs in ig.interf.items():
        for v in nbrs:
            if v < u:               # each undirected edge once
                continue
            ru = alloc.reg.get(u)
            rv = alloc.reg.get(v)
            if ru is not None and ru == rv:
                errors.append(f"conflict: {u} and {v} both in {ru}")
    return errors


# ── Pretty printer ─────────────────────────────────────────────────────────────

def pretty_allocation(alloc: Allocation, intervals: dict[str, Interval] | None = None) -> str:
    lines = [
        f"Allocation {alloc.fn_name!r}"
        f"  {len(alloc.reg)} reg  {alloc.num_slots} spill"
        f"  regs_used={alloc.regs_used}"
    ]
    all_names = sorted(set(alloc.reg) | set(alloc.slot))
    for name in all_names:
        loc  = alloc.location(name)
        ivs  = f"  [{intervals[name].start},{intervals[name].end}]" if intervals and name in intervals else ""
        lines.append(f"  {name:14s} → {loc}{ivs}")
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import parser as _parser
    import infer  as _infer
    from lower  import lower
    from igraph import build_igraph

    if len(sys.argv) < 2:
        print("usage: python3 src/regalloc.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)

    for cfg in cfg_of_tac(tac):
        lv       = analyse(cfg)
        ig       = build_igraph(cfg, lv)
        blk_s    = _linearize(cfg)
        ivs      = _compute_intervals(cfg, lv, blk_s)
        alloc    = allocate(cfg, lv)

        print(pretty_allocation(alloc, ivs))
        errs = verify(alloc, ig)
        print(f"  verify: {'OK' if not errs else 'FAILED'}")
        for e in errs:
            print(f"    {e}")
        print()
