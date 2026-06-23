
## Lark — Phase 4 (the interpreter)

This is the first snapshot where Lark programs *run*. It adds a *CEK machine* —
an iterative abstract machine (Control, Environment, Kontinuation) that evaluates
the typed AST directly.

```
src/lexer.py / parser.py / infer.py / ...   the front end + type checker (phases 0–3)
src/cek.py     the CEK interpreter
tests/         acceptance programs, each with its own "Expected output"
docs/          grammar.ebnf, decisions.md
```

The machine is **iterative** — one `while` loop, with the continuation held as an
explicit stack rather than on Python's call stack — so deeply recursive Lark
programs (e.g. `sum_to(1_000_000)`) run in bounded host stack space. Pattern
matching, trait dispatch, and the affine `IO` token are all handled here.

### Try it

```sh
make test                                     # run every acceptance test, check output
make typecheck FILE=tests/03_recursion.lark   # type-check a single program
make parse     FILE=tests/03_recursion.lark   # (earlier stages remain available)
```

### Where this goes

The CEK interpreter is Lark's reference semantics — later phases must agree with
it. **[`../05/`](../05/)** adds the compiler (an IR and a code generator);
**[`../07/`](../07/)** adds a native C version of this machine and the path to
real hardware. See the top-level [`../README.md`](../README.md).
