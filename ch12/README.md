
## Chapter 12 — Types as Proofs

Companion code for Chapter 12 of *The Language Stack: From Silicon to Semantics*.

This final chapter opens the box left closed in Chapter 11: the proof checker that
vouched for Lark's soundness. Its one idea — **a type is a proposition, a program
its proof, so type-checking *is* proof-checking** — is made concrete by two
companions, a proof kernel you can read and run, and a bridge that runs the claim
on real Lark programs.

| Section | Where |
|---------|-------|
| §12.1 Curry–Howard made exact | `bridge/` — run the type-checking-is-proof-checking claim on Lark programs |
| §12.2 What dependent types add | `kernel/` — Π, Σ, indexed families; length-indexed `Vec`, `Fin` (`code/lang/lib/`) |
| §12.3 The proof kernel `lcore` | `kernel/code/core/` — an MLTT/HoTT checker in C: parser, bidirectional type checker, NbE evaluator, elaborator (REPL `lcore`) |
| §12.4 Lark's soundness proof, read | `bridge/` + the real proof at [`lark/formal/proof/`](./../lark/formal/proof/) (the four `.lcore` files + the `lcore` kernel) |
| §12.5 The road from Lark | conceptual — HM → affine → bidirectional → full dependent types (Idris, Agda, Lean) |
| §12.6 The limit | conceptual — undecidability of full dependent type checking |

`kernel/` is a self-contained programming-language laboratory: the `code/core/`
kernel (REPL `lcore`) and a call-by-need graph reducer `code/lang/` (REPL `llang`)
sharing the same surface syntax and checker, with a standard library
(`code/lang/lib/`: `nat`, `vec`, `fin`, `proofs`) and runnable `samples/`. It is a
readable *sibling* of the kernel that checked the book's proof, not that kernel
itself.

**Lark's actual soundness proof is referenced by path, not duplicated here.** It
lives in [`lark/formal/proof/`](./../lark/formal/proof/) — `lark-typing.lcore`,
`lark-subst.lcore`, `lark-step.lcore`, `lark-preservation.lcore`, checked by the
`lcore` kernel in `lark/formal/proof/code/core/`. `bridge/` runs that real kernel
on the smoke tests in `lark-typing.lcore`, each annotated with the Lark program it
encodes, so the correspondence is something you watch happen.

> **Two binaries named `lcore`.** `bridge/run_bridge.sh` goes *directly* to the
> real proof kernel at `lark/formal/proof/code/core/lcore` (building it only if
> missing) — the one Chapter 11 stood on. The `lcore` under `kernel/code/core/` is
> the separate *teaching* kernel below; the bridge does not use it. Same name,
> different programs.

## Running

```sh
make run        # build the kernel, run its 339-test suite, exercise llang + samples, run the bridge
make repl       # build and start the lcore REPL
make bridge     # just the Lark <-> MLTT bridge
make clean      # remove build artifacts
```

The kernel is plain C (`cc`/`clang`). `kernel/code/core/` and `code/lang/` each
have their own `Makefile` (`make` builds `lcore` / `llang`). The REPLs:

```sh
cd kernel/code/core && make && ./lcore     # :i e, :let name = expr, :t, :q
cd kernel/code/lang && make && ./llang      # :load "lib/prelude.lam", :type, :conv, let name : T = e
```

See [`kernel/README.md`](./kernel/README.md) for the kernel walkthrough,
[`kernel/code/lang/lib/README.md`](./kernel/code/lang/lib/README.md) for the
standard library, and [`bridge/README.md`](./bridge/README.md) for the bridge.
