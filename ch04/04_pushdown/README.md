
## §4.3 — Pushdown Automata (supplemental)

Supplemental companion to §4.3 of *The Language Stack*. The book does not
present an explicit pushdown automaton as a parsing strategy; instead it makes a
conceptual point at the end of §4.3:

> the table-driven LL(1) parser **is** a pushdown automaton — a finite control
> plus an explicit stack holding the grammar symbols still to be matched. That
> stack is exactly the call stack recursive descent keeps *implicitly*.

This folder makes that abstract machine concrete in isolation, so the model the
book names can be run and inspected on its own — much as `ch03/finite_automata/`
does for the DFA/NFA model behind the scanner. The example recognises
balanced brackets, a context-free language a finite automaton provably cannot
(the chapter's motivating "something more powerful is needed").

| File | Description |
|------|-------------|
| `pda.py` | PDA in Python: explicit stack operations, balanced-bracket recogniser |
| `pda.c` | The same PDA in C |

Both implement the formal PDA model (Q, Σ, Γ, δ, q₀, Z₀, F) with the stack as an
explicit data structure — the deterministic, single-token-lookahead kind that,
as the book's endnote notes, suffices for every practical programming-language
grammar including Lark's.
