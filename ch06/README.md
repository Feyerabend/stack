
## Chapter 06 — A Working Interpreter

Companion code for Chapter 6 of *The Language Stack: From Silicon to Semantics*.
Organised by section; each folder matches a §6.x heading in the book.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `01_tree_walking/` | §6.1 Tree-Walking Evaluation | The naive recursive evaluator (`naive_eval.py`) — runnable; correct on small programs, overflows the host stack on a deep tail recursion, motivating the CEK machine of §6.4 |
| `03_attribute_grammars/` | §6.3 Attribute Grammars | Three progressive recursive-descent evaluators that compute attributes during parsing: `01/` semantic actions on productions; `02/` a fuller expression grammar; `03/` typed evaluation with an inherited type environment (symbol table) and synthesised expression types |

The interpreter itself — tree-walking evaluation (§6.1), environments and
closures (§6.2), and the CEK machine with proper tail calls (§6.4) — is not
duplicated here: it *is* Lark's evaluator, and the chapter discusses it directly
from [lark/04/src/cek.py](./../lark/04/src/cek.py) (the pure-interpreter phase,
before any compiler machinery). This folder isolates the one idea of the chapter
that has a clean standalone illustration: the attribute-grammar framing of
§6.3, which names the shared structure behind both the type checker (synthesised
types) and the evaluator (synthesised values, inherited environment). The three
progressive attribute-grammar parsers are indexed in
[`03_attribute_grammars/README.md`](./03_attribute_grammars/README.md).

### Running

```sh
make run        # naive_eval.py + the three attribute-grammar demos
make clean      # remove __pycache__

# or individually:
python3 01_tree_walking/naive_eval.py
python3 03_attribute_grammars/01/attribute.py
python3 03_attribute_grammars/02/test_attribute.py
python3 03_attribute_grammars/03/test_attribute.py
```

`naive_eval.py` ends with a deliberate `RecursionError` (handled; exit 0) — that
overflow is the chapter's point, not a failure of the build.
