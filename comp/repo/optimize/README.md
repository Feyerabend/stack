# `optimize/` — The same meaning, faster

**Book: Part II, chapters 8–12.**

A compiler that walks the syntax tree and prints C — the one Part I builds — works,
and the C it prints is bad. This tree is about the part of a compiler that makes the output
fast — and about the rule it must never break: **the program's meaning does not
change.** Faster, and identical in what it does. Every test here is a test of
that rule.

## The shape of an optimizing compiler

The tree-walker went straight from tree to C. An optimizing compiler goes the
long way round, through a **middle language**:

```
source → tokens → syntax tree → typed tree → TAC → (optimize) → C
                                              ↑                 ↑
                                        chapter 9           chapter 11
```

**TAC** ("three-address code") is a flat, dull, deliberately unclever language
where every instruction does one thing to at most three names. It is unpleasant
to read and wonderful to analyse — and being analysable is the entire reason it
exists. Turning the tree into it is called **lowering**: the compiler gives up
structure in exchange for explicitness.

## The three folders

### `oracle/` — the reference optimizer, in Python

| File | What it does | Book |
|------|--------------|------|
| `tac.py` | the middle language itself | ch.&nbsp;8 |
| `lower.py` | typed tree → TAC | ch.&nbsp;9 |
| `opt.py` | the optimization passes | ch.&nbsp;10 |
| `cfg.py`, `liveness.py` | the analyses two of the passes need | ch.&nbsp;10 |
| `emit_tac_c.py` | optimized TAC → C | ch.&nbsp;11 |
| `regalloc.py`, `coloring.py`, `igraph.py`, `riscv_asm.py`, `asm.py` | the other way down: real machine code, real registers | ch.&nbsp;11 |
| `tac_vm.py`, `riscv_vm.py` | little machines to run the IR and the assembly | &nbsp; |

The front end (`lexer.py` … `infer.py`) is duplicated in this tree on purpose. It is
the same front end Part I builds; carrying a copy is what lets this strand run on
its own, with nothing to install and nowhere else to look.

### The passes, in the order they fire

Nine rewrites, each individually unimpressive, applied over and over until
nothing changes (eight sweeps, then we stop):

`devirt` → `inline` → `closure_elim` → `const_fold` → `copy_prop` →
`algebraic_simplify` → `cse` → `dce` → `licm`

Chapter 10 takes them one at a time. None of them is clever. The result is.

### `lark/` — the optimizing compiler, written in Lark

| File | Ports |
|------|-------|
| `tac.lark` | `tac.py` |
| `lower.lark` | `lower.py` |
| `opt.lark` | `opt.py` — all nine passes |
| `emit_tac_c.lark` | `emit_tac_c.py` |

The Python optimizer mutates: it rewrites instructions in place and keeps a
global counter. Lark cannot mutate anything. So every pass here has the shape
`(TAC, Int) -> (TAC, Int)` — take the program and the counter, return a new
program and a new counter. The book argues this is not merely a workaround but a
clarification: it makes visible, in the type, exactly what each pass touches.

### `harness/` — the tests

| Harness | Demands |
|---------|---------|
| `lower_difftest.py` | the Lark lowering emits byte-identical TAC |
| `opt_difftest.py` | the Lark passes emit byte-identical optimized TAC |
| `emit_tac_c_difftest.py` | the Lark back end emits byte-identical C |
| `optcompiler_difftest.py` | the **whole optimizing pipeline**, self-hosted, reproduces the oracle's optimized C at every optimization level |
| `bootstrap_opt.py` | the optimizing compiler compiles itself |

## Two claims, and where they stand

1. **Behavioural fixpoint** — the self-hosted optimizing compiler produces
   exactly what the reference optimizer produces, byte for byte, at every level
   from `-O0` to `-O3`. **Green** (`opt_difftest.py`: 128 ok / 0 fail / 52 skip).
2. **Self-application fixpoint** — the optimizing compiler optimizes *its own*
   ~7,500 lines. **Green.** Stages 1, 2 and 3 emit byte-identical C, and the
   compiler it produces is **18.4 % smaller** than the one it was built from.

The second claim is the one worth pausing on. The compiler is now an input to
itself, and the optimizer's reward for being correct is that it gets to improve
the thing that will next run it. Chapter 12 is about what that does and does not
mean — in particular, that "the output did not change" is the *only* thing making
any of it safe.

Getting there needed a real fix, not a flag: the first attempt wanted tens of
gigabytes, because interning string literals was quadratic in the size of the
output. Chapter 12 tells that story too, since a compiler that cannot compile
itself for want of memory is a compiler with an opinion about how large a program
may be.

## Running it

```sh
make           # the targets, and what each one shows
make opttest   # the optimizer in lark/ and the one in oracle/ must produce the
               # same optimized code — at every level, -O0 through -O3
make test      # all four differentials
make fixpoint  # the optimizing compiler optimizes its own source to a fixed point
```

`make fixpoint` is heavy: it wants roughly 15 GB of arena (lazily committed, so
it does not actually touch that much) and a C compiler. The differentials are
slow for the usual reason — a tower of interpreters. The numbers each target should
print, and which of them are invariant, are pinned in `harness/BASELINES.md`.

## A bug worth the whole tree

The self-compile found a real miscompilation that every test had missed: the C
back end compiled a comparison against a string literal as an *integer tag test*.
The self-hosted parser therefore mistook every keyword for an identifier, recursed
forever, and crashed. No corpus program was strange enough to expose it; the
compiler compiling itself was. Chapter 11 tells the story.
