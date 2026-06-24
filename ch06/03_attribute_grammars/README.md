
## §6.3 — Attribute Grammars

Companion code for §6.3 of *The Language Stack*. An attribute grammar attaches
semantic rules to a grammar's productions: information flows **up** the parse
tree (*synthesised* attributes — values, types, AST nodes) and **down** it
(*inherited* attributes — the surrounding environment). These three recursive-
descent parsers compute attributes inline with parsing, each adding one idea.

| Folder | Focus | Attributes shown |
|--------|-------|------------------|
| [`01/`](./01/) | Semantic actions on productions: a single-type (`i32`) checker with a symbol table and constant folding | Synthesised values/types + an inherited symbol table |
| [`02/`](./02/) | A fuller expression grammar (unary minus, member access `.`, array indexing `[]`, bitwise `& \| ^`, assignment) building an AST | Synthesised `.ast` only |
| [`03/`](./03/) | Typed evaluation with `int`/`float`, promotion rules, and a type environment | Inherited type environment + synthesised expression types |

Each folder has a README with its full attribute-grammar specification (productions
and semantic rules). `02/` and `03/` additionally ship a `test_attribute.py`
driver that exercises the parser on a battery of inputs.

### Run

```sh
python3 01/attribute.py            # self-demoing
python3 02/test_attribute.py       # driver demo
python3 03/test_attribute.py       # driver demo
```

The attribute-grammar framing is the chapter's point: it names the shared
structure behind both the **type checker** (synthesised types, inherited
environment) and the **evaluator** (synthesised values), which Lark's
implementation then realises as one tree walk.
