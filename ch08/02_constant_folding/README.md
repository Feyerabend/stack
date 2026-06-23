# §8.2 — Constant Folding and Propagation

`constant_fold.py` evaluates operations on constant operands at compile time;
`propagator.py` substitutes known constants forward, exposing more folding. Run
to a fixed point, `2 + 3` becomes `5` and the addition never reaches run time.

    python3 constant_fold.py
