"""
Chapter 9, Exercise 2 — solution code.

In sum_to, t0 and r4 share register s9. (a) write their live intervals and
confirm they do not overlap. (b) construct a function whose temporaries cannot
all fit, forcing a spill, and identify which interval linear scan spills and why.
(c) state the exact condition under which two temporaries may share a register.

How to run:   python3 ex02_regalloc.py
Expected:     "t0[0,1] r4[2,12] share s9 (no overlap); forced spill picks the "
              "latest-ending interval; share iff intervals don't overlap"

(c) CONDITION: two temporaries may share one register iff their live intervals
    DO NOT OVERLAP — equivalently, they are never live at the same program point
    (no edge between them in the interference graph). t0 is dead (last use at 1)
    before r4 is born (first def at 2), so s9 can hold first t0, then r4.

(b) Forcing a spill: real functions rarely exceed eleven s-registers, so — as the
    chapter's own companion does (ch09/03_register_allocation uses k=3) — we model
    "not enough registers" by allocating sum_to from a SMALL register set. With
    too few registers, linear scan spills the interval that ENDS LATEST among
    those competing, because it is the one most likely to keep a register tied up
    while others come and go. r4 ([2,12]) ends latest, so it is the first to spill.
"""

from _harness import lower_src, alloc_with

SUM_TO = ("module M\n"
          "fn sum_to(n : Int, acc : Int) : Int = "
          "if n == 0 then acc else sum_to(n - 1, acc + n)")


if __name__ == "__main__":
    fn = lower_src(SUM_TO).functions[0]

    # (a) full allocation with the real register file
    alloc, ivs = alloc_with(fn)
    t0, r4 = ivs["t0"], ivs["r4"]
    assert (t0.start, t0.end) == (0, 1) and (r4.start, r4.end) == (2, 12)
    assert alloc.reg["t0"] == "s9" and alloc.reg["r4"] == "s9"
    assert not t0.overlaps(r4)                    # the sharing condition

    # (b) restrict the register set to force a spill
    alloc2, _ = alloc_with(fn, regs=["s1", "s2"])
    spilled = set(alloc2.slot)
    assert spilled, "a 2-register budget should force a spill"
    # the latest-ending interval overall is r4 ([2,12]); the spill rule sends it
    # (the latest-ending) to memory
    latest = max(ivs.values(), key=lambda iv: iv.end).name
    assert latest == "r4"
    assert "r4" in spilled, spilled

    print(f"t0[{t0.start},{t0.end}] r4[{r4.start},{r4.end}] share "
          f"{alloc.reg['r4']} (no overlap); forced spill picks the "
          f"latest-ending interval ({latest}); share iff intervals don't overlap")
