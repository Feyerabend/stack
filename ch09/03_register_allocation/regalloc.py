"""
Register allocation — Chapter 9, §9.3.

Two classic algorithms on the same small IR, side by side:

  * Linear scan (Poletto & Sarkar, 1999) — sweep the live intervals in order of
    their start, keep a pool of free registers, and when the pool is empty spill
    the interval that ends latest.
  * Graph colouring — build the interference graph (an edge between any two
    temporaries that are live at the same time) and colour it greedily with k
    colours, spilling a node that cannot be coloured.

Both map an unbounded supply of temporaries onto k physical registers, spilling
to memory when k is not enough. A verifier confirms the central invariant: no
two interfering temporaries share a register.

The example program keeps four values live at once, so with k = 3 registers one
of them must spill. Run with different k to watch the spill appear and vanish.

Run:  python3 regalloc.py
"""

from __future__ import annotations
from dataclasses import dataclass


# ── A tiny straight-line IR ───────────────────────────────────────────────────
# Each instruction defines a temporary from zero or more earlier temporaries.

@dataclass
class Instr:
    dst: str
    uses: tuple = ()

# e = a + b ; f = c + d ; g = e + f ; return g
# a, b, c, d are all live going into the first add, so four values overlap.
PROGRAM = [
    Instr("a"), Instr("b"), Instr("c"), Instr("d"),
    Instr("e", ("a", "b")),
    Instr("f", ("c", "d")),
    Instr("g", ("e", "f")),
    Instr("ret", ("g",)),     # a final use of g
]


# ── Live intervals ────────────────────────────────────────────────────────────

def live_intervals(prog: list[Instr]) -> dict[str, tuple[int, int]]:
    """Interval [definition, last use] for each temporary.

    Positions count uses and defs separately: a use at instruction i sits at
    2*i, a def at 2*i+1. This keeps a value's *last use* strictly before another
    value's *definition* at the same instruction, so they do not falsely
    interfere -- the classic def/use boundary subtlety of liveness."""
    start: dict[str, int] = {}
    end:   dict[str, int] = {}
    for i, ins in enumerate(prog):
        for u in ins.uses:
            end[u] = 2 * i                  # use position
        if ins.dst != "ret":
            start[ins.dst] = 2 * i + 1      # def position
            end.setdefault(ins.dst, 2 * i + 1)
    return {v: (start[v], end[v]) for v in start}


def overlap(x: tuple[int, int], y: tuple[int, int]) -> bool:
    return x[0] <= y[1] and y[0] <= x[1]


# ── Algorithm 1: linear scan ──────────────────────────────────────────────────

def linear_scan(intervals: dict[str, tuple[int, int]], k: int):
    order  = sorted(intervals, key=lambda v: intervals[v][0])   # by start
    free   = [f"r{i}" for i in range(k)]
    active: list[str] = []                                       # sorted by end
    reg:    dict[str, str] = {}
    spill:  set[str] = set()

    for v in order:
        s, e = intervals[v]
        # expire intervals that ended before v starts
        for a in [a for a in active if intervals[a][1] < s]:
            active.remove(a); free.append(reg[a])
        if not free:
            # spill the active interval that ends latest (or v itself)
            latest = max(active, key=lambda a: intervals[a][1])
            if intervals[latest][1] > e:
                reg[v] = reg.pop(latest); spill.add(latest)
                active.remove(latest); active.append(v)
            else:
                spill.add(v)
        else:
            reg[v] = free.pop(0)
            active.append(v)
        active.sort(key=lambda a: intervals[a][1])
    return reg, spill


# ── Algorithm 2: graph colouring ──────────────────────────────────────────────

def interference(intervals: dict[str, tuple[int, int]]) -> dict[str, set[str]]:
    g = {v: set() for v in intervals}
    vs = list(intervals)
    for i, u in enumerate(vs):
        for w in vs[i + 1:]:
            if overlap(intervals[u], intervals[w]):
                g[u].add(w); g[w].add(u)
    return g


def colour(graph: dict[str, set[str]], k: int):
    regs = [f"r{i}" for i in range(k)]
    reg:   dict[str, str] = {}
    spill: set[str] = set()
    # colour high-degree nodes first (a simple, effective ordering)
    for v in sorted(graph, key=lambda v: len(graph[v]), reverse=True):
        used = {reg[n] for n in graph[v] if n in reg}
        choice = next((r for r in regs if r not in used), None)
        if choice is None:
            spill.add(v)
        else:
            reg[v] = choice
    return reg, spill


# ── Verifier ──────────────────────────────────────────────────────────────────

def verify(reg, graph) -> list[str]:
    bad = []
    for u, nbrs in graph.items():
        for w in nbrs:
            if u < w and u in reg and w in reg and reg[u] == reg[w]:
                bad.append(f"{u} and {w} interfere but both in {reg[u]}")
    return bad


# ── Report ────────────────────────────────────────────────────────────────────

def report(name, intervals, reg, spill, graph):
    print(f"  {name}:")
    for v in sorted(intervals):
        where = reg[v] if v in reg else "SPILLED to memory"
        print(f"    {v} {str(list(intervals[v])):<9} -> {where}")
    errs = verify(reg, graph)
    print(f"    spills: {sorted(spill) or 'none'}   verify: "
          f"{'OK' if not errs else 'FAILED ' + str(errs)}\n")


if __name__ == "__main__":
    intervals = live_intervals(PROGRAM)
    graph     = interference(intervals)

    print("Program:  e = a+b;  f = c+d;  g = e+f;  return g")
    print("Live intervals [def, last use] (positions: use=2i, def=2i+1):")
    for v in sorted(intervals):
        print(f"    {v}: {list(intervals[v])}")
    span = range(2 * len(PROGRAM))
    max_live = max(sum(s <= p <= e for (s, e) in intervals.values()) for p in span)
    print(f"Register pressure: up to {max_live} temporaries live at once.\n")

    for k in (4, 3):
        print(f"=== k = {k} registers ===")
        r1, s1 = linear_scan(intervals, k)
        report("linear scan", intervals, r1, s1, graph)
        r2, s2 = colour(graph, k)
        report("graph colouring", intervals, r2, s2, graph)
