
## Chapter 01 — Instruction Sets and Memory

Companion code for Chapter 1 of *The Language Stack: From Silicon to Semantics*.

The chapter establishes the ground floor of the stack: how a processor turns a
list of numbers in memory into behaviour. Three small interpreters make the two
dominant machine models — **stack** and **register** — concrete and runnable,
and show where the costs live (instruction dispatch, register pressure, the
fixed-size hardware stack).

| File | Section | What it shows |
|------|---------|---------------|
| `fde.py` | §1.1 | The fetch-decode-execute loop, reproduced verbatim from the book, then wrapped in an `FDE` stack machine extended with `SUB` and `JMP` (Exercise 1). Demos: `3 + 4`, a straight-line sum, and a `JMP` that skips dead code. |
| `min_riscv.py` | §1.2, §1.4 | A minimal RV32I interpreter (`li`, `addi`, `add`, `sub`, `beq`, `bne`, `ret`). Demos: register addition (§1.2) and a ten-iteration counted loop (§1.4). |
| `min6502.py` | §1.3 | A minimal 6502 interpreter with the page-`$01` hardware stack modelled exactly (256 bytes, `SP` from `$FF`). `JSR`/`RTS` consume two bytes per call, so the depth limit the book describes is directly observable — deep nesting raises `StackOverflow`. |
| `Makefile` | — | `make run` executes all three interpreters. |

### Running

```sh
make run          # run all three
python3 fde.py
python3 min_riscv.py
python3 min6502.py
```

Each script ends with `assert`s, so a clean run with the expected printout is the
test: any regression aborts with an `AssertionError`.

### Notes on the models

- **Stack vs. register.** `fde.py` reaches an operand implicitly (top of stack);
  `min_riscv.py` names operands explicitly (`add t2, t0, t1`). The same `3 + 4`
  in both makes the trade-off visible: stack code is shorter to encode, register
  code avoids the push/pop traffic.
- **The hardware stack is finite.** `min6502.py` keeps a real 256-byte page-`$01`
  stack; the overflow demo (129 nested `JSR`s × 2 bytes > 256) shows why call
  depth is a hardware-bounded resource, not an abstraction — a theme the later
  chapters return to when calling conventions and frames appear.
- **Signed ints, no truncation.** The RISC-V interpreter keeps values as Python
  ints for readability; a real emulator would mask every write to 32 bits. The
  6502 interpreter, by contrast, masks to 8 bits throughout because its flag
  behaviour depends on it.

Solutions to the chapter exercises live in `solutions/` (not part of the build).
