
## `self/` — the self-hosted compiler

Lark, written in Lark. Each module here is a port of its Python twin in the frozen
oracle [`../07/src`](../07/src), and each is held against that twin by a
differential test: same input, same output, or the port is wrong. This is the
working source for two of the book's three strands — the reader's
[`repo/self`](../../repo/self) and [`repo/optimize`](../../repo/optimize) trees are
generated from it. See [`../../SELFHOST.md`](../../SELFHOST.md) and
[`../../OPTIMIZE.md`](../../OPTIMIZE.md).

### The one rule

> `../07/src` is the oracle and is frozen. Every module here is a *differential*
> against it, never an edit of it.

### The modules

The front end and interpreter (Part I — self-hosting):

```
lex.lark      the lexer         (vs ../07/src/lexer.py)
parse.lark    the parser        (vs ../07/src/parser.py)
types.lark    the type language
tast.lark     the typed AST
infer.lark    Hindley–Milner inference + affine tracking (vs infer.py)
cek.lark      the CEK interpreter                        (vs cek.py)
emit_c.lark   the AST→C emitter                          (vs emit_c_ast.py)
```

The optimizing middle and back end (Part II — the same meaning, faster):

```
tac.lark        the three-address IR
lower.lark      typed AST → TAC
opt.lark        the optimization passes (copy prop, DCE, CSE, ...)
emit_tac_c.lark TAC → C
regalloc.lark   register allocation
asm.lark        RV32 assembly
```

`lex_smoke.lark` is a standalone driver a reader can run to watch the lexer work
without the harness scaffolding.

### `tests/`

The differential harnesses, one per stage, plus the bootstrap scripts. Each
harness concatenates the Lark modules it needs into a throwaway driver, runs it
through the oracle's CEK interpreter, and compares the result to the Python twin.
`BASELINES.md` pins the numbers a clean run prints; `AUDIT.md` records the language
warts self-hosting turned up. `bootstrap.py`, `bootstrap_tc.py` and
`bootstrap_opt.py` are the self-application: the compiler compiling itself to a
fixpoint.

### Running it

`make help` lists every target. The pattern is one differential per module, plus
`make test` for the lot and `make bootstrap` for the fixpoint:

```sh
make lextest      # lex.lark agrees with lexer.py across the corpus
make infertest    # inferred types agree
make cektest      # evaluated values agree
make test         # every differential, in order
make bootstrap    # the compiler compiles itself
```

Each is meta-circular and therefore slow (an interpreter running an interpreter);
run them one at a time.
