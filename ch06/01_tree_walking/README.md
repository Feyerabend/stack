
## §6.1 — Tree-Walking Evaluation

`naive_eval.py` — the direct recursive evaluator from the chapter's first
listing: one `eval` function, one case per AST node, the value of a node
computed from the values of its children.

It is *illustrative, not Lark's interpreter.* It exists to be run and then to
fail, on purpose:

```
$ python3 naive_eval.py
let x = 2 + 3 in x * x   => VInt(n=25)
countdown(50)            => VInt(n=0)
countdown(100000)        => RecursionError (host limit 1000)
```

The first two lines show the evaluator is correct. The third is the point of
the chapter: `countdown` is *tail*-recursive — it should run in constant stack —
but the naive evaluator delegates control to Python's call stack, nesting one
host frame per Lark call, so a deep loop overflows. That failure is what forces
the explicit-continuation rebuild in §6.4.

Compare the marked `<- fatal` line in `eval` (the application case) against
[lark/04/src/cek.py](./../../lark/04/src/cek.py), where the same call passes
its continuation onward unchanged and the loop runs in bounded space.
Self-contained: standard library only.
