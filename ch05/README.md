
## Chapter 05 — Names, Scope, and Types

Companion code for Chapter 5 of *The Language Stack: From Silicon to Semantics*.
Organised by section; each folder matches a §5.x heading in the book.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `01_symtable/` | §5.1 Names and the Symbol Table | Symbol-table implementations across paradigms (functional, logic, procedural) |
| `03_ontology/` | §5.3 Types as Ontology | Essays on the philosophy of types and the language/compiler/interpreter distinction (`language/`, `reference/`) |
| `04_lambda_calculus/` | §5.4 STLC, §5.5 Hindley-Milner | `calculus/`: a progression from the simply-typed λ-calculus (`lambda.py`) through HM inference (`hm.py`) to System F; `typesys/`: type-system survey projects |
| `06_affine/` | §5.6 Affine Types and Ownership | An affine-type interpreter with move semantics (`affine/`) and arena/region allocators (`arena/`) |
| `07_traits/` | §5.7 Traits | Vtable-based dynamic dispatch — the runtime mechanism behind trait resolution |

Sections §5.2 (Scope) and §5.8 (Type Errors as Design) have no standalone code
here: scope is realised by the symbol-table chain of §5.1, and type-error
reporting is part of Lark's checker itself.

The Lark snapshot for this chapter is [lark/03/src/](./../lark/03/src/)
— the type-checker phase (Algorithm W with affine tracking).
The book's code listings show the hardened final version in
[lark/07/src/infer.py](./../lark/07/src/infer.py) and `ty.py`.
