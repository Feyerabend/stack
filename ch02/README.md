
## Chapter 02 — A Virtual Machine in Software

Companion code for Chapter 2 of *The Language Stack: From Silicon to Semantics*.

Chapter 1 ran programs on models of real hardware. This chapter builds the
machine we actually target for the rest of the book: a small **bytecode virtual
machine** in software. The stack VM is the spine; the register VM, the
assembler, and the control-flow compiler show the design space around it.

| File | Section | What it shows |
|------|---------|---------------|
| `stack_vm.py` | §2.2 | A fifteen-instruction stack machine: arithmetic, comparisons, jumps, locals, and `CALL`/`RET` with saved frames. Demos: `3*(4+5)`, recursive `factorial(5)`, and `StackVMWithPool` adding a constant pool (`LOADK`) for values too wide for a one-byte `PUSH`. |
| `reg_vm.py` | §2.3 | A fourteen-instruction **register** machine (16 registers, `r0`≡0, `r1`=result). Runs the *buggy* and *fixed* factorial side by side to make the calling-convention bug concrete: saving the register file after clobbering `r2` loses the argument. |
| `assembler.py` | §2.5 | A two-pass assembler: labels → byte addresses, then emit, resolving label references as big-endian `u16`. Turns readable assembly into bytecode `StackVM` runs. |
| `control_flow.py` | §2.5 | How structured control flow compiles to jumps: `if`/`else`, `while`, and `switch` two ways — an O(n) comparison chain vs. an O(1) jump table (`CFStackVM` adds `JMPIND`, a computed jump). |
| `Makefile` | — | `make run` executes all four Python scripts. |
| `c/` | §2.4 | A C twin of `stack_vm.py` — same bytecode, same results — built so dispatch cost (cascade vs. `switch` vs. computed `goto`) can be *measured*, and as a differential check on the Python VM. See [`c/README.md`](./c/README.md). |

### Running

```sh
make run                # all four Python scripts

cd c && make check      # build + correctness gate for the C VM
cd c && make diff       # differential oracle: C VM vs Python VM on the same sum
```

Every script ends with `assert`s; a clean run with the expected printout is the
test.

### Things worth noticing

- **Stack vs. register, again.** Following Chapter 1's theme, the same
  `factorial(5)` appears on both a stack VM and a register VM. The stack version
  needs no register bookkeeping; the register version is faster to dispatch but
  forces the calling convention into the open — which is exactly where its bug
  lives.
- **The calling-convention bug is the lesson.** `reg_vm.py` keeps the buggy book
  listing *and* the fix in one file, with an `assert` that the buggy version
  gets the wrong answer. Saving caller state must capture the value before it is
  overwritten — a constraint that returns in force when real frames and
  callee-saved registers appear in Chapter 9.
- **Two ways to switch.** `control_flow.py` runs the comparison chain and the
  jump table on the same inputs and prints both sizes, so the time/space
  trade-off is visible rather than asserted.
- **A differential twin.** The C VM runs the *same* bytecode as the Python VM
  and matches Python's floor-division semantics, so the two must agree
  byte-for-byte. Demanding identical output from two independent
  implementations is the differential-testing idea Chapter 11 formalises.

Solutions to the chapter exercises live in `solutions/` (not part of the build).
