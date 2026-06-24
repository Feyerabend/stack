
## Chapter 10 — Abstract Machines and Operational Semantics

Companion code for Chapter 10 of *The Language Stack: From Silicon to Semantics*.

This chapter is served by two coherent companions rather than one folder per
section. `vm-theory/` is a self-contained *Theory of Virtual Machines* — a LaTeX
document (`theory_of_virtual_machines.tex`) plus a curated "Exploring Abstract
Machines" code library — and it already covers §10.1–§10.5. `06_prolog/` is the
logic-programming side, §10.6. The map:

| Section | Where |
|---------|-------|
| §10.1 What an abstract machine is | `vm-theory/theory_of_virtual_machines.tex` (the theory); `vm-theory/code/` overview |
| §10.2 The SECD machine | `vm-theory/code/secd/secd.py` |
| §10.3 The CEK machine | `vm-theory/code/cek/cek.py` (and the call-by-name cousin `vm-theory/code/krivine/krivine.py`) |
| §10.4 Machines as operational semantics | `04_derivation/derivation.py` (the small-step → CEK derivation); `vm-theory/code/smallstep/smallstep.py` (small-step SOS) |
| §10.5 The WAM | `vm-theory/code/wam/` (`wam.py`, `WAM.md`) |
| §10.6 A miniature Prolog | `06_prolog/` (`sprolog.py` with cut, `mprolog.py` iterative, `nlp/` a parser in Prolog) |
| §10.7 What abstract machines teach | conceptual — no code |

`vm-theory/code/` also holds broader illustrations the chapter draws on: a full
`jvm/` interpreter (a stack-based abstract machine), `hoare/` (Hoare-logic
examples the document discusses), and `cost/` and `simulation/`.

*Lark's own CEK machine is not duplicated here* — §10.3 discusses it directly
from [lark/04/src/cek.py](./../lark/04/src/cek.py) (the readable Python definition)
and [lark/07/src/cek.c](./../lark/07/src/cek.c) (the same machine in C, on the Pico 2W).
The `cek.py` in `vm-theory/` is a standalone illustration of the CEK *idea*,
separate from Lark's.

The set is complete with respect to the chapter: every section that has runnable
content has a demo. The small-step → CEK derivation of §10.4 — the explicit
"reify the evaluation context as a continuation" transformation — is mechanised
in `04_derivation/`, alongside the standalone `smallstep/` and `cek/` endpoints
in `vm-theory/`.

## Running

```sh
make run        # all Python demos + Prolog tests + Hoare C + the JDK-less JVM Example
make run-jvm    # compile and run the Java examples (needs a JDK)
make clean      # remove build artifacts (C binaries, .class, __pycache__, .dSYM)
```

The Python demos each self-run with no arguments (e.g. `python3
vm-theory/code/secd/secd.py`, `python3 06_prolog/sprolog.py`, `python3
vm-theory/code/wam/wam.py`). `06_prolog/mprolog.py` is an interactive REPL, so it
is not part of `make run`. The JVM interpreter needs a Java compiler only to build
the `examples/`; see `vm-theory/code/jvm/README.md`.
