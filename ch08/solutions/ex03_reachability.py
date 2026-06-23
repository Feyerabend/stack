"""
Chapter 8, Exercise 3 — solution code.

Reachability is a graph traversal from the entry block. (a) give a small Lark
function whose lowered CFG contains a block that can never execute (if true ...).
(b) explain why Lark emits the dead block anyway. (c) show that constant folding
must run FIRST — turning the conditional jump unconditional — before reachability
can see the branch as dead and delete it.

How to run:   python3 ex03_reachability.py
Expected:     "before fold: 4 blocks, all reachable (.else1 has an edge); "
              "after fold+reachability: .else1 removed (3 blocks)"

(a) `fn g(io) = if true then 1 else 2` lowers so the else block (.else1) can
    never run, yet it is present in the CFG.

(b) Lark's lowerer folds NO constants, so it lowers `true` to a real Val and
    emits `ICondJump(true, .then0, .else1)` — a genuine two-target branch. Both
    targets therefore get an incoming edge.

(c) A plain reachability pass keeps .else1, because the ICondJump still gives it
    an edge. Only after constant folding rewrites `ICondJump(const true, T, F)`
    into the unconditional `IJump(T)` does .else1 lose its incoming edge — and
    only then does reachability from the entry see it as dead and remove it.
    Folding must run before reachability.
"""

from _harness import lower_src, tac, cfg


def reachable(g):
    """Labels reachable from the entry via successor edges (BFS)."""
    seen, frontier = {g.entry}, [g.entry]
    while frontier:
        b = g.blocks[frontier.pop()]
        for s in b.succs:
            if s not in seen:
                seen.add(s); frontier.append(s)
    return seen


def fold_condjumps(body):
    """Rewrite ICondJump with a constant condition into an unconditional IJump."""
    out = []
    for ins in body:
        if isinstance(ins, tac.ICondJump) and isinstance(ins.cond, tac.Const):
            target = ins.true_label if ins.cond.value else ins.false_label
            out.append(tac.IJump(target))
        else:
            out.append(ins)
    return out


if __name__ == "__main__":
    fn = lower_src("module M\nfn g(io : IO) : Int = if true then 1 else 2").functions[0]

    # before folding: ICondJump gives .else1 an incoming edge -> all reachable
    g0 = cfg.build_cfg(fn)
    r0 = reachable(g0)
    assert set(g0.blocks) == r0, "expected all blocks reachable before fold"
    assert ".else1" in r0
    assert any(isinstance(i, tac.ICondJump) for i in fn.body)

    # fold the constant condition, then rebuild + recompute reachability
    fn.body = fold_condjumps(fn.body)
    assert any(isinstance(i, tac.IJump) for i in fn.body)
    g1 = cfg.build_cfg(fn)
    r1 = reachable(g1)
    live = {lbl for lbl in g1.blocks if lbl in r1}
    assert ".else1" not in r1, "after fold, .else1 must be unreachable"

    print(f"before fold: {len(g0.blocks)} blocks, all reachable "
          f"(.else1 has an edge); after fold+reachability: .else1 removed "
          f"({len(live)} blocks: {sorted(live)})")
