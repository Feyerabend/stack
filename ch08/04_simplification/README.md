# §8.4 — Expression Simplification

`expression_simplifier.py` applies algebraic identities — `x + 0`, `x * 1`,
`x * 0`, `x - x` — and strength reduction (`x * 2` becomes `x + x`) by a table of
rewrites. A caution the chapter stresses: these laws hold over the integers but
*not* over floating point (`x + 0.0` is not `x` for negative zero), so a real
compiler must restrict them by type.

    python3 expression_simplifier.py
