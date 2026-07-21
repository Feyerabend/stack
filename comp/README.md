
## Companion to The Language Stack: From Silicon to Semantics

*Code Crafting no. 4, by Set Lonnert (2026)*


### Lark — Lambda Affine Resource Kernel

Lark is a small, serious, purely functional language: Hindley–Milner type
inference, affine ownership as a resource discipline (no GC, no mutation), traits
for structured polymorphism, and a CEK machine as its interpreter target. It was
built once from the silicon up in the previous book, *The Language Stack* (Code
Crafting no. 4). __This repository is the next book__ — the one where the finished
language goes on to build itself, optimize itself, and prove things about the
programs written in it.

Nearest existing language: OCaml without the imperative surface, with affine
ownership and traits added. Research precedent: Alms (Tov & Pucella, 2011).

### This is a working repository

It holds two trees and the machinery between them. **You edit the development tree
under `dev/`; a generator derives the reader's tree under `repo/`.** They are never
edited in the same place: `repo/` is regenerated from `dev/`, and the whole
book-and-code story is two commands — regenerate, then check that nothing drifted.

- [book/](./book/) - the book "Lark Builds Itself" (PDF only) — cites repo/ paths
- [repo/](./repo/) - the reader's companion tree — GENERATED from dev/, never hand-edited
- [dev/](./dev/) - the working tangle — this is where code is actually written
- [tools/](./tools/) - mkrepo.py (the generator) and oracle_drift.sh (the frozen-oracle audit)

For NOW: Alongside these sit the plan-and-log documents that drive the work and are not
part of the reader's tree: `AIMS.md` (the north star), `STRUCTURE.md` (how the
folders were reconciled), `LOG.md` (the dated running record), the three strand
plans `SELFHOST.md` / `OPTIMIZE.md` / `PROVE.md`, and `ORACLE.md` (what has been
done to the frozen reference). Maybe scrapped soon ..

### `dev/` — where the code lives

The development tree is laid out by *history*, not by strand. Five folders:

* [dev/07/](./dev/07/) --
              the frozen Python reference compiler — the ORACLE.  Borrowed from
              the earlier book. A sealed, complete Lark (lexer -> parser ->
              type checker -> CEK interpreter -> TAC IR -> RV32 backend ->
              C runtime -> REPL -> nine samples), plus a Raspberry Pi Pico 2 / 2W
              (RP2350, RISC-V) firmware build.  It is never edited: every claim
              in Parts I and II is "the port agrees with 07".
              See dev/07/README.md and ORACLE.md.

* [dev/08/](./dev/dev/08/) --
             the refinement-checker fork of the oracle — 07's type checker grown
              until it discharges refinement obligations ({v:Int | v > 0} and the
              like).  The subject of Part III.  See dev/08/README.md.
```
dev/self/     the self-hosted compiler: the oracle rewritten in Lark itself, file
              for file (lex.lark, parse.lark, infer.lark, cek.lark, ...), plus the
              optimizer modules and the differential harnesses that hold it against
              07.  The subject of Part I and Part II.

dev/prove/    the verification corpus: 75 refinement fixtures, each a safe program
              paired with a mutant carrying one real bug.  See dev/prove/README.md.

dev/formal/   the machine-checked metatheory: formal/proof/ holds the lcore proof
              kernel and the type-soundness proof of Lark, checked by lcore itself.
```

### `repo/` — the reader's tree (generated)

`repo/` is what the book cites and what will go public. It is laid out by *strand*,
one self-contained tree per part of the book, and it is __derived from `dev/`__ by
`tools/mkrepo.py` — every file is either copied verbatim, copied with a mechanical
path rewrite (a harness docstring that says `dev/07/src/lexer.py` upstream must say
`oracle/lexer.py` for the reader), or a hand-written repo-only file (the READMEs,
Makefiles, and baselines). Do not edit it by hand; run `make repo`.

```
repo/self/       Can a language build itself?                         (Part I)
repo/optimize/   Can it be made fast without changing what it means?  (Part II)
repo/prove/      What can it actually promise?                        (Part III)
```

Each strand has the same shape — `oracle/` (the Python reference), `lark/` (the
Lark subject), `samples/`, `harness/` (the differentials), a `Makefile`, and a
`README.md` — and each is meant to be read and run entirely on its own.

### Quick start

From the top level, `make help` lists every target:

```sh
make repo     # regenerate repo/ from dev/            (tools/mkrepo.py)
make check    # fail if repo/ drifted, then run the book's path & ref lints
make book     # build the book PDF (runs the lints, then tectonic)
make prove    # run the refinement checker over all 75 fixtures
make formal   # check the Lark soundness proof
make test     # check + prove + formal
```

Each strand under `repo/` and each folder under `dev/` also has its own `Makefile`
(`make help` lists its targets) and its own `README.md` describing what is in it
and what the code does.

### Further reading

- `book/PLAN.md` — the book's status ledger, wave order, and definition of done
- `AIMS.md` — the teaching aim the whole book is measured against
- `dev/formal/proof/README.md` — the lcore MLTT kernel and the soundness proof
- `ORACLE.md` — the frozen reference and every change made to it since the freeze

### License

To the extent possible under law, Set Lonnert has waived all copyright and
related or neighboring rights to Lark. The work is dedicated to the public
domain under the Creative Commons CC0 1.0 Universal dedication; see the
`LICENSE` file or <https://creativecommons.org/publicdomain/zero/1.0/>.
