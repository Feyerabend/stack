
## §4.5 — Choosing a Strategy

Companion code for §4.5 of *The Language Stack*. Recursive descent (§4.2) is the
right default and the one Lark uses, but it is not the only option. This folder
collects the main alternatives so their trade-offs — power, speed, table size,
ease of writing — can be compared on the same kind of grammar.

| Folder / File | Strategy | One-line trade-off |
|---------------|----------|--------------------|
| [`combinator/`](./combinator/) | Parser combinators | Parsers as composable first-class functions; reads like the grammar. |
| [`earley/`](./earley/) | Earley | Handles *any* CFG (ambiguous, left-recursive); O(n³) worst case. |
| [`packrat/`](./packrat/) | Packrat (PEG) | Memoised recursive descent; linear time, more memory; PEGs are unambiguous by construction. |
| [`slr1/`](./slr1/) | SLR(1) | Simplest bottom-up table method; resolves conflicts with FOLLOW sets. |
| [`lr1/`](./lr1/) | LR(1) | Most powerful table method here; per-item lookahead, larger tables. |
| [`cyk-notes.md`](./cyk-notes.md) | CYK (notes) | Dynamic-programming recogniser for grammars in Chomsky Normal Form. |
| [`peg-notes.md`](./peg-notes.md) | PEG (notes) | Where "the grammar *is* the parser"; the formalism behind packrat. |

Each subfolder has its own README. The `*-notes.md` files are explainer/exercise
notes rather than runnable programs.
