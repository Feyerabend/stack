
## Chapter 04 — Parsing

Companion code for Chapter 4 of *The Language Stack: From Silicon to Semantics*.
Organised by topic. The folder numbers are historical and do **not** track the
book's section numbers — use the Section column below for the matching §4.x
heading.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `02_recursive/` | §4.2 Recursive Descent | Arithmetic parser in C and Python (two variants) |
| `03_ll1/` | §4.3 LL(1) | Table-driven LL(1) parser for arithmetic expressions |
| `04_pushdown/` | §4.3 (PDA) | The pushdown-automaton model behind recursive descent / LL(1), in C and Python — discussed at the end of §4.3 |
| `05_bottomup/` | §4.4 Bottom-Up Parsing | Shift-reduce: brackets, precedence, AABB grammar |
| `06_alternatives/` | §4.5 Choosing a Strategy | Combinator, Earley, packrat, LR(1), SLR(1); PEG and CYK notes |
| `07_ast/` | §4.6 Abstract Syntax Trees | Parse tree vs AST; recursive, combinator, and packrat AST variants |

Each folder has its own README with the details for that strategy.

### Running

```sh
make run        # every Python demo, then build + run every C demo
make run-py     # Python demos only
make run-c      # C demos only
make clean      # remove C binaries and __pycache__

# or run any single piece directly, e.g.:
python3 03_ll1/LL1.py
python3 06_alternatives/earley/earley.py
cc -O2 -o 04_pushdown/pda 04_pushdown/pda.c && ./04_pushdown/pda
```

The C binaries are built next to their sources and removed by `make clean`.

The Lark snapshot for this chapter is [lark/02/src/parser.py](./../lark/02/src/parser.py).
