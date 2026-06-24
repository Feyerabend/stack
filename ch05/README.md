
## Chapter 05 — Names, Scope, and Types

Companion code for Chapter 5 of *The Language Stack: From Silicon to Semantics*.
Organised by topic. The folder numbers are historical and do **not** all track
the book's section numbers — use the Section column below.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `01_symtable/` | §5.1 Names and the Symbol Table | Symbol-table implementations across paradigms (functional, logic, procedural) |
| `03_ontology/` | §5.3 Types as Ontology | Essays on the philosophy of types and the language/compiler/interpreter distinction (`language/`, `reference/`) |
| `04_lambda_calculus/` | §5.4 STLC, §5.5 Hindley-Milner | `calculus/`: a progression from the simply-typed λ-calculus (`lambda.py`) through HM inference (`hm.py`) to System F; `typesys/`: type-system survey projects |
| `06_affine/` | §5.7 Affine Types and Ownership | An affine-type interpreter with move semantics (`affine/`) and arena/region allocators (`arena/`) |
| `07_traits/` | §5.8 Traits | Vtable-based dynamic dispatch — the runtime mechanism behind trait resolution |

Sections §5.2 (Scope), §5.6 (Algebraic Data Types and Pattern Matching), and
§5.9 (Type Errors as Design) have no standalone code here: scope is realised by
the symbol-table chain of §5.1, and pattern matching and type-error reporting
are part of Lark's checker itself.

### Running

```sh
make run        # every Python demo, every standalone C demo, and each subproject
make run-py     # Python demos only
make run-c      # standalone C demos only
make run-sub    # the subprojects (arena compiler, css parser, vtable compiler)
make clean      # remove all binaries, generated C, and __pycache__
```

Each folder also builds and runs on its own (see its README). The C subprojects
under `06_affine/arena/` and the vtable compiler in `07_traits/` have their own
Makefiles, which the top-level `make` delegates to.

The Lark snapshot for this chapter is [lark/03/src/](./../lark/03/src/)
— the type-checker phase (Algorithm W with affine tracking).
The book's code listings show the hardened final version in
[lark/07/src/infer.py](./../lark/07/src/infer.py) and `ty.py`.
