
## AST → DAG: Sharing Common Subexpressions

The directed acyclic graph (DAG) of §7.5, built directly from a parsed
expression. Where a syntax tree gives every occurrence of `a * b` its own
subtree, a DAG gives the two occurrences the *same node*: identical computations
are shared rather than duplicated, and that sharing is exactly what
common-subexpression elimination reads off the graph.

Two standalone scripts, each parsing an infix expression with the shunting-yard
algorithm and then collapsing it to a DAG:

| File | Expression | What it highlights |
|------|------------|--------------------|
| `dag.py` | `a * (b - 1) + a * (b - 1)` | renders the tree with `⟲`/`★` markers for shared nodes and reference counts, then reports the node count and the space saved |
| `dag2.py` | a nested arithmetic expression | a leaner version printing the AST and the DAG side by side, marking the reused subtree |

Sharing is detected by **value numbering**: each distinct computation gets a key
built from its operator and the keys of its operands; when a key is seen again,
the existing node is reused instead of building a new one. It is a hash table and
a single pass.

### Running

```bash
python3 dag.py
python3 dag2.py
```

Each script has its expression built in and prints the tree, the shared DAG, and
(for `dag.py`) the node-count statistics. The compiler that turns this sharing
into actual generated code — and checks the result against a naive compiler —
is in [`../compiler/`](../compiler/).
