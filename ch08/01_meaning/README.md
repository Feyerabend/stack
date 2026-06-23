# §8.1 — Meaning Preservation

`equiv_check.py` — the local model of `lark/06/tests/diff_test.py`: an optimizer
proposes a rewrite, an oracle runs the original and rewritten expression on many
random inputs and demands identical results. A sound rewrite (constant folding)
passes; a deliberately wrong one (`x - x => x`, which should be `0`) is caught
with a concrete counterexample.

    python3 equiv_check.py

The lesson: an optimization you cannot check is one you cannot safely ship.
