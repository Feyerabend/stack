"""
Chapter 7, Exercise 2 — solution code.

Take the sum_to TAC. (a) identify every basic block and confirm the leader rule
gives exactly four. (b) draw the CFG; is there a back edge? why does the
recursive call create none here, and what later transformation introduces one?
(c) why can't `return r4` be replaced by `return t7`?

How to run:   python3 ex02_cfg.py
Expected:     "sum_to: 4 blocks [...]; back edges: 0 (acyclic)"

(b) The CFG is ACYCLIC — no back edge. The recursive call lowers to an ICall
    (`t7 = call sum_to(...)`) sitting INSIDE the .else2 block; a call is a normal
    instruction, not a control-flow edge, so it does not loop back to .entry. The
    transformation that turns this tail call into a back edge — replacing the
    call+return with a jump to the entry — is tail-call elimination in
    Chapter 9 (ch:codegen).

(c) `return r4` cannot be locally rewritten to `return t7`. In the THEN branch
    r4 = acc (the base case), where t7 does not exist / is not the value; only in
    the ELSE branch is r4 = t7. The merge block .end3 returns whichever r4 the
    taken branch produced, so substituting t7 there would be wrong on the then
    branch. The non-local change that *would* remove r4 and the merge block is to
    give each branch its own return (return acc in then, return t7 in else),
    eliminating the merge — copy propagation and its limits, taken up in
    Chapter 8.
"""

from _harness import lower_src, fn_named, cfg

SRC = ("module M\n"
       "fn sum_to(n : Int, acc : Int) : Int = "
       "if n == 0 then acc else sum_to(n - 1, acc + n)")


def back_edge_count(g):
    """A back edge is a successor pointing to an earlier (or same) block in
    definition order — the signature of a loop."""
    order = {lbl: i for i, lbl in enumerate(g.blocks)}
    n = 0
    for i, (lbl, b) in enumerate(g.blocks.items()):
        for s in b.succs:
            if order.get(s, 1 << 30) <= i:
                n += 1
    return n


if __name__ == "__main__":
    fn = fn_named(lower_src(SRC), "sum_to")
    g = cfg.build_cfg(fn)
    labels = list(g.blocks)

    # (a) exactly four blocks from the leader rule
    assert len(labels) == 4, labels

    # (b) no back edge -> acyclic
    be = back_edge_count(g)
    assert be == 0, be

    print(f"sum_to: {len(labels)} blocks {labels}; back edges: {be} (acyclic)")
    for lbl, b in g.blocks.items():
        print(f"   {lbl:12} -> {b.succs}")
