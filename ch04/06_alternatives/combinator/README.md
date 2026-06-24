
## §4.5 — Parser Combinators

Companion code for §4.5 of *The Language Stack* (alternative strategies).

| File | Description |
|------|-------------|
| `combinator.py` | Functional combinator library: `literal`, `regex`, `seq`, `choice`, `many`, `opt`; demo parses a Lisp-like expression language |

Combinator parsers treat parsers as first-class composable functions.
The chapter discusses them as an alternative to hand-written recursive descent
for grammars that fit a functional style naturally.
