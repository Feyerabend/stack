
## Chapter 03 - Lexical Analysis

Companion code for Chapter 3 of *The Language Stack: From Silicon to Semantics*.

| File / Folder      | Description |
|--------------------|-------------|
| `dfa.py`           | Book companion: formal `DFA` class, `tokenize_simple` from §3.2, identifier / integer / comparison-operator DFAs; demos for Figure 3.1 and Exercise 3.3 |
| `Makefile`         | `make run` executes `dfa.py` |
| `tokenizer/`       | Extended tokeniser examples: regexp-based, state-machine driver, error handling |
| `finite_automata/` | Generic DFA/NFA implementations in C and Python (supplemental) |

The Lark snapshot for this chapter is [lark/01/src/lexer.py](./../lark/01/src/lexer.py).
