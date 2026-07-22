"""
Lark graph-coloring register allocator — Chaitin-Briggs iterated register
coalescing (Appel, *Modern Compiler Implementation*, §11.4), adapted to this
backend.

Why this exists
---------------
The default allocator is linear scan (`regalloc.py`). The O4 peephole
(`opt.peephole`) already collapses the scratch-register round-trips a fragment
emits, but it works window-locally on the caller-saved t-registers and cannot
touch the *callee-saved* s-registers, which cross basic-block boundaries. Two
inefficiencies therefore survive the peephole:

  1. **Copies that could be coalesced.** An `IAssign dst = src` emits, after the
     peephole, a real `mv s_dst, s_src` when the two temps land in different
     s-registers. If instead dst and src are assigned the *same* register the
     move degenerates to `mv sX, sX` and the peephole deletes it entirely.
     Linear scan never coalesces; graph coloring does (conservatively).
  2. **Avoidable spills / register pressure.** Linear scan's greedy interval
     packing can spill (and can occupy more distinct s-registers, inflating the
     prologue/epilogue save area) where a precise interference graph colors with
     fewer registers.

The interference graph — *including copy (move) edges* — is already built by
`igraph.py`, so the substrate is here. This module runs the classic worklist
algorithm on top of it.

Drop-in with linear scan
-------------------------
`color_allocate` returns the **same** `regalloc.Allocation` dataclass, and
`allocate_tac_color` mirrors `regalloc.allocate_tac`. `asm.gen(tac, allocator=…)`
picks the allocator; nothing downstream changes.

No program rewrite on spill
---------------------------
Textbook Chaitin-Briggs rewrites the program (inserting reload temps) and
re-runs when a node actually spills. We do **not**: this backend's `asm.load` /
`asm.store` already materialise any temp that has no register from/to its stack
slot on every use/def — exactly how linear scan spills here. So an actual spill
is just "assign a slot instead of a register", identical in effect to a linear
scan spill, and the optimistic Briggs colorer needs no restart loop.

Determinism
-----------
Every worklist choice is the minimum element (by name / move index / spill
cost), never `set.pop()`, so the allocation is reproducible regardless of
`PYTHONHASHSEED` (optbench runs each file in a fresh subprocess).
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tac import TAC
from cfg import CFG, cfg_of_tac
from liveness import Liveness, analyse, defs, uses
from igraph import IGraph, build_igraph
from regalloc import Allocation, _REGS


# -- Spill-cost weights ------------------------------------------------------

def _occurrence_weights(cfg: CFG) -> dict[str, int]:
    """Spill-cost numerator: how many instructions reference each Tmp (def or
    use). The TAC CFG is acyclic (Lark iteration is inter-procedural recursion,
    not a back-edge — see opt.licm), so there is no loop-depth factor to apply;
    a raw occurrence count is the natural estimate of reload traffic."""
    w: dict[str, int] = {}
    for blk in cfg:
        for instr in blk.instrs:
            for name in defs(instr) | uses(instr):
                w[name] = w.get(name, 0) + 1
    return w


# -- The allocator -----------------------------------------------------------

def color_allocate(cfg: CFG, lv: Liveness,
                   regs: list[str] | None = None,
                   params: list[str] | None = None) -> Allocation:
    """Colour one function's interference graph with `regs` (default s1-s11),
    coalescing move-related temps conservatively and spilling optimistically."""
    if regs is None:
        regs = _REGS
    K = len(regs)

    ig: IGraph = build_igraph(cfg, lv)
    nodes: set[str] = set(ig.nodes)

    # Mutable interference adjacency + degree. adj is never pruned (Appel keeps
    # adjList intact and prunes only the `degree` count); coalescing ADDS edges.
    adj:    dict[str, set[str]] = {n: set(ig.interf.get(n, set())) for n in nodes}
    degree: dict[str, int]      = {n: len(adj[n]) for n in nodes}

    # Moves — one per undirected copy edge (IAssign dst = src_tmp).
    moves: list[tuple[str, str]] = []
    seen: set[frozenset] = set()
    for u in sorted(ig.copies):
        for v in sorted(ig.copies[u]):
            if u == v:
                continue
            key = frozenset((u, v))
            if key in seen:
                continue
            seen.add(key)
            moves.append((u, v))
    moveList: dict[str, set[int]] = {n: set() for n in nodes}
    for i, (u, v) in enumerate(moves):
        moveList[u].add(i)
        moveList[v].add(i)

    worklistMoves: set[int] = set(range(len(moves)))
    activeMoves:   set[int] = set()
    coalescedMoves: set[int] = set()
    constrainedMoves: set[int] = set()
    frozenMoves:   set[int] = set()

    alias:          dict[str, str] = {}
    coalescedNodes: set[str] = set()
    coloredNodes:   set[str] = set()
    onStack:        set[str] = set()
    selectStack:    list[str] = []

    simplifyWorklist: set[str] = set()
    freezeWorklist:   set[str] = set()
    spillWorklist:    set[str] = set()

    weight = _occurrence_weights(cfg)

    # -- helpers --

    def node_moves(n: str) -> set[int]:
        return moveList[n] & (activeMoves | worklistMoves)

    def move_related(n: str) -> bool:
        return bool(node_moves(n))

    def adjacent(n: str) -> set[str]:
        return adj[n] - (onStack | coalescedNodes)

    def enable_moves(ns) -> None:
        for n in ns:
            for m in node_moves(n):
                if m in activeMoves:
                    activeMoves.discard(m)
                    worklistMoves.add(m)

    def decrement_degree(m: str) -> None:
        d = degree[m]
        degree[m] = d - 1
        if d == K:
            enable_moves({m} | adjacent(m))
            spillWorklist.discard(m)
            if move_related(m):
                freezeWorklist.add(m)
            else:
                simplifyWorklist.add(m)

    def get_alias(n: str) -> str:
        while n in coalescedNodes:
            n = alias[n]
        return n

    def add_worklist(u: str) -> None:
        if (not move_related(u)) and degree[u] < K:
            freezeWorklist.discard(u)
            simplifyWorklist.add(u)

    def add_edge(u: str, v: str) -> None:
        if u != v and v not in adj[u]:
            adj[u].add(v); adj[v].add(u)
            degree[u] += 1; degree[v] += 1

    def conservative(ns) -> bool:
        """Briggs: coalescing is safe if the merged node has < K neighbours of
        significant (>= K) degree — such a node is guaranteed colourable."""
        k = 0
        for n in ns:
            if degree[n] >= K:
                k += 1
        return k < K

    def combine(u: str, v: str) -> None:
        if v in freezeWorklist:
            freezeWorklist.discard(v)
        else:
            spillWorklist.discard(v)
        coalescedNodes.add(v)
        alias[v] = u
        moveList[u] |= moveList[v]
        enable_moves({v})
        for t in list(adjacent(v)):
            add_edge(t, u)
            decrement_degree(t)
        if degree[u] >= K and u in freezeWorklist:
            freezeWorklist.discard(u)
            spillWorklist.add(u)

    def freeze_moves(u: str) -> None:
        for m in list(node_moves(u)):
            x, y = moves[m]
            ax, ay, au = get_alias(x), get_alias(y), get_alias(u)
            v = ax if ay == au else ay
            activeMoves.discard(m)
            frozenMoves.add(m)
            if (not node_moves(v)) and degree[v] < K:
                freezeWorklist.discard(v)
                simplifyWorklist.add(v)

    # -- build initial worklists --

    for n in nodes:
        if degree[n] >= K:
            spillWorklist.add(n)
        elif move_related(n):
            freezeWorklist.add(n)
        else:
            simplifyWorklist.add(n)

    # -- main loop (deterministic minimum-element selection) --

    while simplifyWorklist or worklistMoves or freezeWorklist or spillWorklist:
        if simplifyWorklist:
            n = min(simplifyWorklist)
            simplifyWorklist.discard(n)
            selectStack.append(n); onStack.add(n)
            for m in adjacent(n):
                decrement_degree(m)
        elif worklistMoves:
            m = min(worklistMoves)
            worklistMoves.discard(m)
            x, y = moves[m]
            u, v = get_alias(x), get_alias(y)
            if u == v:
                coalescedMoves.add(m)
                add_worklist(u)
            elif v in adj[u]:                      # they interfere
                constrainedMoves.add(m)
                add_worklist(u); add_worklist(v)
            elif conservative(adjacent(u) | adjacent(v)):
                coalescedMoves.add(m)
                combine(u, v)
                add_worklist(u)
            else:
                activeMoves.add(m)
        elif freezeWorklist:
            u = min(freezeWorklist)
            freezeWorklist.discard(u)
            simplifyWorklist.add(u)
            freeze_moves(u)
        else:  # spillWorklist non-empty
            # cheapest to spill = lowest occurrence-weight per unit of degree
            # (frees the most interference for the least reload traffic).
            m = min(spillWorklist,
                    key=lambda n: (weight.get(n, 0) / max(degree[n], 1), n))
            spillWorklist.discard(m)
            simplifyWorklist.add(m)
            freeze_moves(m)

    # -- assign colours (optimistic: a stacked potential-spill may still get one) --

    color:       dict[str, str] = {}
    spilledNodes: set[str] = set()

    while selectStack:
        n = selectStack.pop()
        onStack.discard(n)
        used: set[str] = set()
        for w in adj[n]:
            aw = get_alias(w)
            if aw in coloredNodes:
                used.add(color[aw])
        avail = [r for r in regs if r not in used]
        if not avail:
            spilledNodes.add(n)                    # actual spill → stack slot
        else:
            color[n] = avail[0]                    # min-index reg: pack low, reuse
            coloredNodes.add(n)

    # coalesced nodes inherit their representative's decision
    for n in coalescedNodes:
        rep = get_alias(n)
        if rep in color:
            color[n] = color[rep]
        else:
            spilledNodes.add(n)

    # -- materialise the Allocation over every original Tmp --

    reg_assign: dict[str, str] = {}
    spill_slot: dict[str, int] = {}
    # one slot per spilled representative; coalesced-into-a-spill shares it
    reps_spilled = sorted({get_alias(n) for n in spilledNodes})
    slot_index = {rep: i for i, rep in enumerate(reps_spilled)}

    for n in nodes:
        rep = get_alias(n)
        if rep in color:
            reg_assign[n] = color[rep]
        else:
            spill_slot[n] = slot_index[rep]

    reg_order = {r: i for i, r in enumerate(_REGS)}
    regs_used = sorted(set(reg_assign.values()),
                       key=lambda r: reg_order.get(r, 99))

    alloc = Allocation(
        fn_name   = cfg.fn_name,
        reg       = reg_assign,
        slot      = spill_slot,
        num_slots = len(slot_index),
        regs_used = regs_used,
    )

    # -- safety net: no two interfering temps may share a register --
    # (coalesced temps DO share, but coalescing only ever merges non-interfering
    #  nodes, so the original interference graph must be conflict-free.)
    for u, nbrs in ig.interf.items():
        ru = reg_assign.get(u)
        if ru is None:
            continue
        for v in nbrs:
            if reg_assign.get(v) == ru:
                raise AssertionError(
                    f"coloring miscompile in {cfg.fn_name!r}: "
                    f"{u} and {v} both in {ru}")

    return alloc


def allocate_tac_color(tac: TAC, regs: list[str] | None = None) -> list[Allocation]:
    """Graph-colour every function in `tac`. Signature mirrors
    regalloc.allocate_tac so it is a drop-in for asm.gen(allocator=…)."""
    result: list[Allocation] = []
    for fn, cfg in zip(tac.functions, cfg_of_tac(tac)):
        lv = analyse(cfg)
        result.append(color_allocate(cfg, lv, regs, params=list(fn.params)))
    return result


# -- CLI ---------------------------------------------------------------------

if __name__ == "__main__":
    import parser as _parser
    import infer  as _infer
    from lower import lower
    from regalloc import pretty_allocation, verify

    if len(sys.argv) < 2:
        print("usage: python3 src/coloring.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)

    for cfg in cfg_of_tac(tac):
        lv    = analyse(cfg)
        ig    = build_igraph(cfg, lv)
        alloc = color_allocate(cfg, lv)
        print(pretty_allocation(alloc))
        errs = verify(alloc, ig)
        print(f"  verify: {'OK' if not errs else 'FAILED'}")
        for e in errs:
            print(f"    {e}")
        print()
