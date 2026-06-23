# §9.3 — Register Allocation

`regalloc.py` — the chapter's centrepiece, both classic algorithms on one small
IR:

- **Linear scan** (Poletto & Sarkar): sweep live intervals by start, spill the
  latest-ending interval when the register pool is empty.
- **Graph colouring**: build the interference graph and colour it greedily,
  spilling a node that needs a colour beyond `k`.

The example keeps four values live at once, so `k = 4` fits with no spill and
`k = 3` forces exactly one — each algorithm choosing a different victim, both
correct. A verifier checks the invariant: no two interfering temporaries share a
register.

    python3 regalloc.py

Lark's own allocator is `lark/05/src/regalloc.py` (linear scan over `s1`–`s11`).
Note the positions trick (use at `2i`, def at `2i+1`) that stops a value's last
use and a new value's definition at the same instruction from falsely interfering.
