
## Lark — Phase 2 (the parser)

This snapshot adds the *parser*: a hand-written *LL(1) recursive-descent*
parser — one function per grammar rule, no backtracking — that turns the token
stream from phase 0 into an *abstract syntax tree*.

```
src/lexer.py    the lexer (carried forward from phase 0)
src/parser.py   the recursive-descent parser
src/tree.py     the AST node types (frozen dataclasses)
docs/           grammar.ebnf, decisions.md
tests/          the acceptance programs
```

The AST defined here in `tree.py` is the contract every later phase consumes — the
type checker, interpreter, and compiler all walk these same nodes.

### Try it

```sh
make parse FILE=tests/02_arithmetic.lark   # print the AST for one program
make parse                                 # parse every acceptance test
make lex   FILE=tests/02_arithmetic.lark   # (still available from phase 0)
```

### Where this goes

Next, **[`../03/`](../03/)** adds the type checker (Hindley–Milner inference with
affine ownership). Phase numbers skip 1 by design — see the top-level
[`../README.md`](../README.md).
