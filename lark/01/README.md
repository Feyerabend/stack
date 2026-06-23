
## Lark — Phase 0 (design and lexer)

The starting point of the build. The language is first settled *on paper* —
[`docs/grammar.ebnf`](docs/grammar.ebnf) is the ground truth — and then the first
piece of the implementation is written: the **lexer**, which turns Lark source
text into a stream of tokens.

```
src/lexer.py        a single-pass, state-machine lexer
docs/grammar.ebnf   the complete grammar (EBNF) the whole language is built to
docs/decisions.md   why the syntax is the way it is
tests/              the acceptance programs used from here to the end
```

The lexer is deliberately simple and is carried forward **unchanged in
architecture** by every later phase — the rest of the language is layered on top
of these tokens.

### Try it

```sh
make lex FILE=tests/01_hello.lark   # show the tokens for one program
make lex                            # lex every acceptance test
make check                          # verify the expected files are present
```

### Where this goes

This is the first of the sealed phase snapshots. Next, **[`../02/`](../02/)** adds
a parser that turns these tokens into a syntax tree. See the top-level
[`../README.md`](../README.md) for the whole phase-by-phase map.
