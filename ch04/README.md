
## Chapter 04 - Parsing

Companion code for Chapter 4 of *The Language Stack: From Silicon to Semantics*.
Organised by section; each folder matches a §4.x heading in the book.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `02_recursive/` | §4.2 Recursive Descent | Arithmetic parser in C and Python (two variants) |
| `03_ll1/` | §4.3 LL(1) Parsing | Table-driven LL(1) parser for arithmetic expressions |
| `04_pushdown/` | §4.4 Pushdown Automata | PDA in C and Python |
| `05_bottomup/` | §4.5 Bottom-Up Parsing | Shift-reduce: brackets, precedence, AABB grammar |
| `06_alternatives/` | §4.6 Choosing a Strategy | Combinator, Earley, packrat, LR(1), SLR(1); PEG and CYK notes |
| `07_ast/` | §4.7 Abstract Syntax Trees | Parse tree vs AST; recursive, combinator, and packrat AST variants |

The Lark snapshot for this chapter is [lark/02/src/parser.py](./../lark/02/src/parser.py).
