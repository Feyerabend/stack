# `self/` — A language that builds itself

**Book: Part I, chapters 1–7.**

The question: can Lark compile Lark? Not "can someone write a Lark compiler" —
that was the previous book — but can the compiler be written *in the language it
compiles*, and can it then compile itself, and produce itself again, unchanged?

The answer is yes, and the last part of that sentence is the whole point.

## The three folders

### `oracle/` — the reference implementation, in Python

The compiler as it was first written: readable, slow, and **correct by
definition**. Everything in `lark/` is judged against it.

| File | What it does |
|------|--------------|
| `lexer.py` | text → tokens |
| `parser.py`, `tree.py` | tokens → syntax tree |
| `ty.py`, `typed_tree.py`, `infer.py` | type inference (Hindley–Milner + affine + traits) |
| `cek.py` | the interpreter (a CEK machine) |
| `emit_c_ast.py` | syntax tree → C |
| `cek.c`, `cek.h`, `larkrun.c` | the C runtime the emitted code links against |

This code is **frozen**. An oracle that moves is not an oracle. (We were forced
to change it three times; every occasion is explained in the book, in chapter 7.
The third is the most interesting: the oracle was simply *wrong*, and the port
was right — see "What is a String, exactly?" below.)

### `lark/` — the same compiler, written in Lark

The port. Read these next to their Python counterparts — that pairing is what the
book is about.

| File | Ports | Book |
|------|-------|------|
| `lex.lark` | `lexer.py` | ch. 2 |
| `parse.lark` | `parser.py` + `tree.py` | ch. 3 |
| `types.lark`, `tast.lark`, `infer.lark` | `ty.py`, `typed_tree.py`, `infer.py` | ch. 4 |
| `cek.lark` | `cek.py` | ch. 5 |
| `emit_c.lark` | `emit_c_ast.py` | ch. 6 |

What makes these interesting is not that they work but *how they had to be
shaped*. Lark has no mutable variables, so the lexer's position counter becomes a
value threaded through every call; and it has affine types, so a variable used in
two branches of a `match` is a type error, which means the interpreter cannot
simply pass its `io` handle around. Every one of these constraints changed the
program's structure. The book's Part I interlude collects what that taught us
about the language.

### `harness/` — the proof that the port is faithful

One differential test per component. Each runs the Python and the Lark version on
the same inputs and demands identical output:

| Harness | Compares | Result |
|---------|----------|--------|
| `lex_difftest.py` | token streams | 52 / 52 identical |
| `parse_difftest.py` | syntax trees | 47 / 47 identical |
| `infer_difftest.py` | inferred types | 42 ok / 0 fail / 2 skip |
| `cek_difftest.py` | program output | 33 ok / 0 fail / 15 skip |
| `emit_c_difftest.py` | emitted C | 37 ok / 0 fail / 7 skip |
| `typecheck_difftest.py` | accept/reject **and** emitted C | 42 ok / 0 fail / 2 skip |

And then the two that close the loop:

- **`bootstrap.py`** — assembles `lex` + `parse` + `emit_c` into a single Lark
  program that reads Lark on stdin and writes C on stdout, then runs the ladder:
  compile the compiler, use the result to compile the compiler again, and again.
  Stages 1, 2 and 3 emit **byte-identical C**. That is the fixpoint.
- **`bootstrap_tc.py`** — the same, but with the type checker on the path, so the
  self-hosting compiler actually *checks* what it compiles. This is the stronger
  claim, and the one the book ends Part I with.

`BASELINES.md` pins the numbers above; `AUDIT.md` justifies every single skip.

## What is a String, exactly?

The differential harness caught the oracle telling itself a lie, and it is worth
the space to say how, because it is the best short argument for this whole
method.

Lark has two primitives that are meant to be inverses:

```
string_index(s, i)   -- the character at position i
char_to_string(n)    -- a one-character string from n
```

The C runtime had always treated a String as a row of **bytes**: `string_length`
was `strlen`, and `string_index` handed back one `unsigned char`. The Python
oracle treated it as a row of **codepoints** — but its `char_to_string` masked to
a byte, to stay in step with C. So the two primitives no longer composed. Feed
them an em dash and `char_to_string(string_index(s, i))` returns not `—` but the
control character `\x14`, because U+2014 was truncated to its low eight bits.

That is a silent, lossy bug sitting *on the compiler path*: `parse.lark` rebuilds
every string literal one character at a time. The self-hosted parser corrupted
every non-ASCII string literal it read.

Two things about it are worth more than the bug itself:

- **Every test passed anyway.** The corpus was ASCII, where a byte and a
  codepoint are the same thing. And the bootstrap fixpoint could never catch it:
  C1, C2 and C3 all corrupt *identically*, so they stay byte-identical to each
  other. A compiler comparing itself to itself cannot see its own blind spot.
  Only comparison against a *different* implementation could — and did.
- **The oracle was the wrong one.** The port, which had no choice but to build
  strings out of whatever `string_index` gives it, was right; the reference
  implementation was inconsistent with itself. So we fixed the oracle: a Lark
  String **is a sequence of UTF-8 bytes**, as C had assumed all along, and a
  *column number is a byte offset*. That is the third and last thaw of the frozen
  code (`cek.py`, `lexer.py`), and the only one where the port won the argument.

### `samples/` — the corpus

The programs everything is tested on, from `01_hello.lark` upward. The most
important input is not in this folder: it is the compiler's own source.

## Running it

```sh
make              # the targets, and what each one proves
make cektest      # e.g.: the compiler in lark/ and the reference in oracle/ must
                  # print the same bytes for every program in the corpus
make test         # all six differentials, tokens through emitted C
make bootstrap    # the fixpoint: the compiler compiles itself, C1 == C2 == C3
```

Be warned that the Lark side is an interpreter running an interpreter, so a full
`make test` runs for hours; `harness/BASELINES.md` records the numbers each
target is supposed to print, so you can tell a real regression from a slow
machine.

## Where to start reading

`lex.lark` next to `lexer.py`. They do the same thing, and they look nothing
alike. Understanding *why* is Part I.
