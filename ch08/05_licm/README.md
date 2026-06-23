# §8.5 — Loop-Invariant Code Motion

`licm.py` — a self-contained LICM pass over a tiny three-address loop. It finds
computations whose operands do not change across iterations — to a *fixed point*,
so a value that is invariant only because another invariant one feeds it is also
caught — and hoists them into a preheader that runs once before the loop.

    python3 licm.py

In the worked loop, `t1 = a * b` and the dependent `t2 = t1 + 1` are hoisted out
of the body, removing two operations per iteration (`2n` over the whole loop).
The loop test stays, and the analysis assumes a single-block body in which each
destination is assigned once — stated in the source.
