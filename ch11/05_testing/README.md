
## §11.5 — Testing a Compiler

`testing_methods.py` — three testing methods on one tiny expression language,
each finding a bug the others structurally cannot:

- *Differential* — two evaluators compared; finds where the "fast" one diverges
  from the reference (a backwards subtraction).
- *Property-based* — one `simplify` pass checked against the invariant *meaning
  is preserved*; finds the input where `e * 0` was wrongly rewritten to `e`.
- *Fuzzing* — random strings fed to the parser; finds the truncated input that
  crashes it instead of failing cleanly.

```
python3 testing_methods.py
```

Each prints the bug it found and why the other two miss it. The actual tests that
guard Lark are in `lark/06/tests/` — `diff_test.py` (differential, across the
CEK/TAC/RV32 backends) and `gen.py` (property-based, with Hypothesis).
