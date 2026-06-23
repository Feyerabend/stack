
## Lark — Phase 3 (the type checker)

This snapshot adds Lark's *type system*: *Hindley–Milner* inference
(Algorithm W) extended with *affine ownership* tracking and *trait* bounds. A
parsed program is checked and annotated, producing a typed AST.

```
src/lexer.py / parser.py / tree.py   the front end (phases 0–2)
src/infer.py        Algorithm W: unification, generalisation, instantiation;
                    the affine context ("tracked" set); trait resolution
src/ty.py           the type representation (type vars, constructors, schemes)
src/typed_tree.py   the typed AST produced by checking
docs/               grammar.ebnf, decisions.md
tests/              the acceptance programs
```

Two ideas are central here: *let-polymorphism* (a `let`-bound value is
generalised to a scheme and instantiated fresh at each use) and the **affine
discipline** (a non-`Copy` value may be used at most once — the checker tracks
each binding's uses alongside its type). A bidirectional layer lets explicit
type annotations meet the inferred types.

### Try it

```sh
make typecheck FILE=tests/05_adt.lark   # type-check one program, print its typed AST
make typecheck                          # type-check every acceptance test
make parse FILE=tests/05_adt.lark       # (front-end stages remain available)
```

### Where this goes

Programs don't *run* yet — that arrives in **[`../04/`](../04/)**, the CEK
interpreter. See the top-level [`../README.md`](../README.md) for the full map.
