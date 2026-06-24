
## §4.5 — SLR(1) Parser

Companion code for §4.5 of *The Language Stack* (alternative strategies).

| File | Description |
|------|-------------|
| `SLR1.py` | SLR(1) parser: builds ACTION/GOTO tables from an LR(0) automaton |

SLR(1) is the simplest LR variant. It resolves shift/reduce conflicts using
the FOLLOW sets of non-terminals. LR(1) ([lr1/LR1.py](./../lr1/LR1.py)) is
stronger: it carries per-item lookaheads and handles grammars that SLR(1) cannot.
