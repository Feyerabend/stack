
## §4.5 — LR(1) Parser

Companion code for §4.5 of *The Language Stack* (alternative strategies).

| File | Description |
|------|-------------|
| `LR1.py` | Canonical LR(1) parser: builds the LR(1) item sets and ACTION/GOTO tables from an augmented arithmetic grammar, then drives a shift-reduce parse |

LR(1) is the most powerful of the bottom-up table methods shown here. Each item
carries a one-token lookahead, so it builds its ACTION/GOTO tables from the full
canonical collection of LR(1) item sets — handling grammars that SLR(1)
([../slr1/SLR1.py](./../slr1/SLR1.py)) cannot, at the cost of a larger table.
The demo parses `3 + 4 * (2 + 5)` over the classic expression grammar.
