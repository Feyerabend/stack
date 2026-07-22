# Lark Builds Itself — companion code

This is the code that goes with the book. It is organised for **reading**, not
for development. The working repository that produced it keeps everything in one
tangle, because that is what development looks like; this one is deliberately cut
into three trees that do not depend on each other:

| Tree | The question it answers | Book |
|---|---|---|
| [`self/`](self/) | Can a language build itself? | Part I |
| [`optimize/`](optimize/) | Can it be made fast without changing what it means? | Part II |
| [`prove/`](prove/) | What can it actually promise? | Part III |

Each tree stands alone. You can read `optimize/` without having read `self/`, and
`prove/` without either. The price is duplication: the same lexer appears in two
trees, because both need one. That is intentional. **Nothing here is a shared
library**; each tree is a complete, readable artifact.

## What Lark is

A small, purely functional, statically typed language: algebraic data types,
pattern matching, Hindley–Milner type inference, *affine* types (a value is used
at most once), traits, and exactly one effect (`IO`, threaded by hand). It was
built in a previous book, *The Language Stack*; you do not need to have read it.
Appendix A of this book is the language reference.

## The one idea that runs through everything

**Differential testing.** There are two implementations of every part of the
compiler: a slow, readable one in Python (the *oracle*), and one written in Lark
itself. A component is not "tested"; it is required to be **byte-for-byte
indistinguishable** from the oracle on every input we have. Every `*_difftest.py`
in these trees does exactly that, and prints a line like:

```
42 ok / 0 fail / 2 skip
```

The skips are always listed and always justified — see `self/harness/AUDIT.md`.
A harness that hides its skips is a harness that is lying to you.

## Reading order

1. `self/README.md` — start here even if optimization is what you came for.
2. `optimize/README.md`
3. `prove/README.md`

## Running the tests

Each tree runs on its own, from inside itself. There is nothing to install and
nothing to configure — only Python 3 and, for the C back end, a C compiler.
Every strand has a `Makefile`, and every `Makefile` answers `make help`:

```sh
make help          # here: the three strands
cd self && make help
```

Start with `make prove`. It takes seconds, and it is the only one that finishes
while you watch — the other two are towers of interpreters and run for hours.

```sh
cd self
make lextest        # tokens
make parsetest      # syntax trees
make infertest      # types
make cektest        # behaviour — what programs actually print
make emittest       # emitted C
make typechecktest  # accept/reject, and the C
make bootstrap      # the fixpoint: C1 == C2 == C3
make test           # all six differentials
```

```sh
cd optimize && make test      # the optimizer changed the code, not its meaning
cd prove    && make test      # the kernel's 339 cases, then Lark's soundness proof
```

Every harness finds its own strand: `oracle/` is the Python reference, `lark/`
is the compiler written in Lark, `tests/` and `samples/` are the corpus. No
harness reaches outside its own tree.

The Lark side is an interpreter running an interpreter, so it is slow — several
minutes for the larger inputs, and the compiler's own source is the largest
input there is. Each harness allows a per-file budget of 120 seconds by default;
raise it when a run reports a timeout:

```sh
LARK_TIMEOUT=900 make emittest
```

### A timeout is not a failure

A timeout is a fact about your machine, not about the compiler, and every harness
reports it as a **skip with a reason** — never as a red. This matters more than it
sounds. It means the numbers a harness prints are of two kinds:

- **`0 failed` is the claim.** A failure is a *disagreement*: the compiler written
  in Lark and the Python reference finished the same program and produced different
  bytes. That is true or false on any machine.
- **The `ok` / `skip` split is a report about your box.** The files that skip are
  the files yours could not finish inside the budget. A faster machine turns skips
  into oks; a slower one does the reverse.

So a moved ok/skip boundary is not a regression — a `fail` is. Set the budget as
high as your patience allows and the skips melt away; set it to five seconds and
you will see a great many skips and still zero failures.

`harness/BASELINES.md` records the numbers the machine that pinned them printed,
and says which of them are invariant and which are about that machine.

## What you need

Python 3 and a C compiler. Nothing else — no packages, no virtualenv, no network.

The differentials are patient but cheap: they want time, not memory, and they run
on anything. **The three fixpoints are the exception**, because in each of them a
compiler written in Lark compiles its own source, and that source is thousands of
lines:

| target | where | peak memory | roughly |
|---|---|---|---|
| `make bootstrap` | `self/` | well under 1 GB | minutes |
| `make bootstrap-tc` | `self/` | **~10 GB** | tens of minutes |
| `make fixpoint` | `optimize/` | **~6 GB** | tens of minutes |

Those two large ones want a machine with **16 GB of RAM to be comfortable**, and
they allocate their heap up front (lazily committed, so the number you see in
`top` is not the number in use). If one dies with `arena overflow` or a bad
`alloc`, give it less rather than more — the default is sized for headroom, not
for your machine:

```sh
cd optimize && make fixpoint ARENA_MB=8000
```

They also recurse deeply, and macOS starts a process with an 8 MB stack. The
harnesses raise it themselves where they can; if you drive a stage by hand, do
what they do:

```sh
ulimit -s 65520
```

Everything else in these trees runs in a few hundred megabytes.
