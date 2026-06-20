# §4.2 — Recursive Descent

Companion code for §4.2 of *The Language Stack*.

| File | Description |
|------|-------------|
| `parse.py` | Recursive descent parser for arithmetic (operators, identifiers, floats) |
| `parse2.py` | Extended variant: member access, array indexing, fuller AST |
| `arith.c` | Same recursive descent logic in C |

Both Python variants mirror the operator-precedence chain described in the chapter
(`_parse_add` → `_parse_mul` → `_parse_unary` → `_parse_atom`).
For the Lark version of this chain see [lark/02/src/parser.py](./../../lark/02/src/parser.py).
