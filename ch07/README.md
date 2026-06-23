
## Chapter 07 — Intermediate Representations

Companion code for Chapter 7 of *The Language Stack: From Silicon to Semantics*.
Organised by section; each folder matches a §7.x heading in the book.

| Folder | Section | What it contains |
|--------|---------|------------------|
| `01_ir/` | §7.1 The Case for an IR | ILOC — a full AST→IR→RISC-V educational pipeline (`iloc/`); LLVM IR examples and notes (`llvm/`); `notes/` on the history of intermediate code and Pascal p-code |
| `02_tac/` | §7.2 Three-Address Code | TAC generators and interpreters in C and Python (`demo/`, `simple/`); a small lambda→TAC compiler (`lambda/`); constant folding over TAC (`optimise/`) |
| `03_cfg/` | §7.3 Control-Flow Graphs | Tiny C compilers that build basic blocks and control-flow graphs (`compiler/`, `demo/`), with HTML visualisations of if/else, nested, switch, and while-loop graphs |
| `04_ssa/` | §7.4 Static Single Assignment | An SSA compiler in C with φ-function placement tests (`compiler/`); a Python SSA demo (`demo/`) |
| `05_dag/` | §7.5 Common Subexpressions / DAG | DAG construction and value numbering for common-subexpression elimination (`simple/`, `compiler/`) |

Section §7.6 (Lowering Lark to TAC) has no standalone folder here: it is Lark's
own lowerer, discussed directly from [lark/05/src/lower.py](./../lark/05/src/lower.py).

The Lark snapshot for this chapter is [lark/05/src/](./../lark/05/src/)
— the compiler phase. The three files the chapter cites are `tac.py` (the IR),
`lower.py` (typed tree → TAC), and `cfg.py` (the control-flow graph).
The `02_tac/optimise/` folder previews constant folding, which Chapter 8
develops as a proper optimisation pass.
