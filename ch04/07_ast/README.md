
## §4.6 — Abstract Syntax Trees

Companion code for §4.6 of *The Language Stack*.

| File | Description |
|------|-------------|
| `tree.py` | Parse tree with explicit `ParseTreeNode`; builds a full CST from arithmetic input |
| `expr_ast.py` | Converts the parse tree above into a leaner AST (removes syntactic noise). Named `expr_ast.py`, not `ast.py`, so it does not shadow Python's standard-library `ast` module |
| `recursive_ast.py` | Single-pass recursive descent that builds an AST directly, no CST intermediate |
| `combinator_ast.py` | Combinator-based parser that yields an AST |
| `packrat_ast.c` | Packrat parser in C that produces an AST |

The chapter distinguishes parse trees (concrete syntax trees) from abstract
syntax trees and shows how `_parse_let_expr` in the Lark parser
([lark/02/src/parser.py](./../../lark/02/src/parser.py))
produces the frozen dataclasses in 
[lark/02/src/tree.py](./../../lark/02/src/tree.py)
directly, without a CST step.
