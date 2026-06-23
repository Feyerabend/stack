"""
Chapter 9, Exercise 3 — solution code.

Linear scan spills the latest-ending interval when registers run out. (a) why is
"latest-ending" better than "earliest-ending" or "the current interval"? (b) give
a sequence of intervals on which linear scan produces a worse allocation than
optimal graph colouring, and say how many registers each uses.

How to run:   python3 ex03_linear_vs_color.py
Expected:     "with 1 register: linear scan spills 1, graph colouring spills 0"

Uses the chapter's own companion algorithms,
ch09/03_register_allocation/regalloc.py (linear_scan and colour).

(a) WHY LATEST-ENDING. When a register must be freed, spilling the interval that
    ends latest frees the register for the longest remaining span — it removes the
    one most likely to block future allocations. "Earliest-ending" would evict an
    interval about to free its register on its own (wasteful: it spills something
    that was about to stop competing). "Always spill the current interval" ignores
    that the current interval might be short and cheap to keep; spilling a
    long-lived active one instead can avoid further spills. Latest-ending is the
    greedy choice that keeps the most registers usefully occupied.

(b) WHERE LINEAR SCAN IS WORSE — a live range with a HOLE. Linear scan models each
    temporary as ONE contiguous interval [first use, last use], so a variable that
    is live, then dead for a while, then live again is treated as live across the
    gap. Graph colouring on the TRUE interference (which sees the gap) knows the
    gap is free. Example below: `a` is live at points {0,1} and {5,6} (dead 2–4),
    `b` is live at {2,3,4} — entirely inside a's gap.
      • Linear scan sees a = [0,6], b = [2,4]; these overlap, so with one register
        it must SPILL one of them — it uses effectively 2 registers.
      • True interference: a and b are never simultaneously live, so they don't
        interfere; graph colouring fits both in ONE register, no spill.
    Linear scan: 2 registers (or 1 spill at k=1). Optimal: 1 register, 0 spills.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH09 = os.path.dirname(_HERE)
sys.path.insert(0, os.path.join(_CH09, "03_register_allocation"))

import regalloc as ra   # the companion's linear_scan / colour  # noqa: E402


if __name__ == "__main__":
    # `a` has a hole (dead at 2,3,4); `b` lives entirely in that hole.
    # Linear scan sees the contiguous hulls and thinks a and b interfere.
    hull_intervals = {"a": (0, 6), "b": (2, 4)}

    # The TRUE interference graph: a and b are never live together -> no edge.
    real_graph = {"a": set(), "b": set()}

    K = 1
    ls_reg, ls_spill = ra.linear_scan(hull_intervals, K)
    gc_reg, gc_spill = ra.colour(real_graph, K)

    # linear scan must spill (hulls overlap); colouring need not (no real edge)
    assert len(ls_spill) == 1, ls_spill
    assert len(gc_spill) == 0, gc_spill
    # and the colouring is valid: a and b share the one register
    assert gc_reg["a"] == gc_reg["b"]

    print(f"with {K} register: linear scan spills {len(ls_spill)}, "
          f"graph colouring spills {len(gc_spill)}")
