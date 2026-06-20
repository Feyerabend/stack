# §4.3 — LL(1) Parsing

Companion code for §4.3 of *The Language Stack*.

| File | Description |
|------|-------------|
| `LL1.py` | Table-driven LL(1) parser for arithmetic expressions |

The grammar is the standard left-recursion-eliminated form:

```
E  → T E'
E' → + T E' | - T E' | ε
T  → F T'
T' → * F T' | / F T' | % F T' | ε
F  → num | ( E )
```

The parsing table is hard-coded in the class, matching the FIRST/FOLLOW
analysis in the chapter.
