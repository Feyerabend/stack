
## §4.5 — Packrat / Memoised Parser

Companion code for §4.5 of *The Language Stack* (alternative strategies).

| File | Description |
|------|-------------|
| `packrat.py` | Recursive descent parser with a memoisation table (packrat) |

Packrat parsing memoises every parse function call, guaranteeing O(n) time
at the cost of O(n·G) space (G = grammar size). Based on parsing expression
grammars (PEGs), which are unambiguous by construction.
