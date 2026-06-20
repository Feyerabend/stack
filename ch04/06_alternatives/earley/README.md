
## §4.6 — Earley Parser

Companion code for §4.6 of *The Language Stack* (alternative strategies).

| File | Description |
|------|-------------|
| `earley.py` | Chart-based Earley parser: predict / scan / complete loop |

The Earley algorithm (1970) handles any context-free grammar, including
ambiguous and left-recursive grammars, in O(n³) time worst-case (O(n²)
for unambiguous grammars). The chapter mentions it as the go-to choice
when grammar coverage matters more than parse speed.
