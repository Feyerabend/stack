# §8.3 — Dead Code and Reachability

`dead_code.py` removes computations whose results are never used (a *liveness*
question); `reachability.py` marks the blocks reachable from the entry block,
after which the unmarked blocks are dead and can be deleted.

    python3 dead_code.py
