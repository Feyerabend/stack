
## Chapter 1 — Solutions

Solutions to the exercises in Chapter 1, *The Hardware Machine*, of
*The Language Stack: From Silicon to Semantics*.

Code-bearing solutions are runnable and verified:

| Exercise | Code | Run |
|----------|------|-----|
| 1 (SUB, JMP) | `../fde.py` (already in the chapter repo) | `python3 ../fde.py` |
| 2 (stack-machine loop) | `ex02_loop.py` | `python3 ex02_loop.py` |
| 3–5 | analysis only | — |



### Exercise 1 — Extend the machine with `SUB` and `JMP`

> Extend the toy fetch-decode-execute machine with two new instructions:
> `SUB` (pop two values, push their difference) and `JMP` (an unconditional
> jump). What extra byte does `JMP` read from memory, and how does its effect
> on `pc` differ from that of `PUSH`?

*The extra byte.* `JMP` reads one extra byte — the *target address* — from the
cell immediately after its opcode (`memory[pc]`). It is an operand byte, exactly
like the literal that follows `PUSH`.

*The difference from `PUSH`.* Both read one operand byte, but they use it
differently, and that difference is the whole point of having a jump:

- `PUSH` reads its operand, *consumes* it, and then advances `pc` past it
  (`pc += 1`). Control still flows to the next instruction in sequence. The net
  effect on `pc` is `+2` (opcode + operand), always forward, always sequential.
- `JMP` reads its operand and *assigns it to* `pc` (`pc = target`). Control
  jumps to an arbitrary address. The change to `pc` is not a fixed increment but
  a replacement, and it can move execution backward (the basis of loops) or
  forward over code (skipping it).

So `PUSH` treats its operand as *data* placed on the stack; `JMP` treats its
operand as a *code address* loaded into the program counter. Same encoding
(opcode then one byte), opposite roles.

*Code.* This is implemented in the chapter's companion file, `../fde.py`, in
the `FDE` class (opcodes `SUB = 3`, `JMP = 4`). Running `python3 ../fde.py`
prints the `3 + 4` example, a straight-line sum, and a `JMP` demo that jumps
over a `PUSH 100` to prove the jump takes effect.

Note that with only `JMP` (an *unconditional* jump) you cannot yet write a
terminating loop — you would jump back forever. A *conditional* branch is what
closes the gap, which is exactly what Exercise 2 introduces as `BNZ`.



### Exercise 2 — Rewrite the ten-iteration loop for a stack machine

> Rewrite the ten-iteration loop for a stack machine whose only instructions are
> `PUSH`, `ADD`, `SUB`, `DUP` (duplicate the top of stack), and `BNZ` (branch if
> the top of stack is non-zero). What is the greatest number of values on the
> stack at any one moment during your loop?

The 6502 version counts *up* (`LDX #0 / INX / CPX #10 / BNE`). A stack machine
with no registers and no compare instruction is easier to drive by counting
*down* to zero, because `BNZ` already tests "is the top non-zero?" — so the loop
counter doubles as the branch condition.

```
   addr  instr        stack after      depth
   0      PUSH 10      [10]             1
   loop @ 2:
   2      PUSH 1       [c, 1]           2   <- peak
   4      SUB          [c-1]            1
   5      DUP          [c-1, c-1]       2   <- peak
   6      BNZ loop     [c-1]            1     (BNZ pops the copy)
   8      HALT         counter is 0
```

The counter starts at 10 and is decremented once per pass; the body runs ten
times and the loop exits when the counter reaches 0. `DUP` is needed because
`BNZ` consumes the value it tests — we duplicate the counter so that one copy is
spent on the test and the other survives as the next iteration's counter.

*Greatest stack depth: 2.* The stack holds at most two values at any instant
(during `PUSH 1` before the `SUB`, and during `DUP` before the `BNZ`). It never
needs a third slot. `ex02_loop.py` instruments the machine and asserts all three
facts — ten iterations, final counter 0, and maximum depth 2:

```
$ python3 ex02_loop.py
10 iterations, max stack depth = 2
```



### Exercise 3 — Minimum live values for `(a × b) + (c × d)`

> Consider the expression `(a × b) + (c × d)`. Count the minimum number of values
> that must be live at once to evaluate it. On the 6502, with its three
> registers, what does this force the compiler to do that it would not have to do
> on RISC-V?

*Minimum simultaneously-live values: 3.* Evaluate one product, say `a × b`,
leaving its result `p1` live. To evaluate the second product you load `c` and
`d` — and `p1` is still live, because you will need it for the final `+`. At
that moment three values are live at once: `p1`, `c`, `d` (equivalently `p1`
plus the two operands of the second multiply). After the second multiply two
values are live (`p1`, `p2`), and after the add, one. The peak is three.

This is the Sethi–Ullman number of the tree: a leaf needs 1, and a binary node
whose two subtrees each need `n` needs `n + 1`. Each product needs 2; the root
`+` has two subtrees each needing 2, so it needs 3. You cannot do better by
reordering — the expression is balanced, so neither product can be evaluated
"for free" while holding the other.

*What it forces on the 6502.* The 6502 has three registers, but only the
accumulator `A` performs arithmetic; `X` and `Y` are index registers. It cannot
hold three independent arithmetic values at once. So the compiler must *spill an
intermediate to memory* (typically zero page): compute `a × b`, store it,
compute `c × d`, then load the stored product back to add. RISC-V, with 32
general-purpose registers all capable of arithmetic, keeps `p1`, `c`, `d`, and
`p2` in registers and never touches memory for the intermediates. The exercise
is a concrete instance of why register *count* and *generality* drive how much
load/store traffic a compiler is forced to emit — the theme that returns in
register allocation (Chapter 9).



### Exercise 4 — Increment a 32-bit value at the address in `a0`

> RISC-V's load-store discipline forbids arithmetic directly on memory. Write the
> RISC-V sequence that increments the 32-bit value stored at the address held in
> `a0`. How many memory accesses does it take, and why can it not be fewer?

```asm
    lw   t0, 0(a0)     # load the word from memory into a register
    addi t0, t0, 1     # increment it in the register
    sw   t0, 0(a0)     # store the result back to memory
```

*Memory accesses: 2* — one load (`lw`) and one store (`sw`). The `addi` touches
no memory.

*Why not fewer.* Under load-store discipline, arithmetic instructions operate
only between registers; no single instruction both reads memory, adds, and writes
back (that would be a read-modify-write memory operand, which RISC-V deliberately
does not have). The value must therefore be *brought into* a register to be
modified (1 access) and *written back* to be visible in memory (1 access). One
access cannot suffice, because a lone `lw` leaves memory unchanged and a lone
`sw` has nothing new to store. Two is the floor. (Contrast a CISC machine such as
x86, where `inc dword [rax]` does it in one instruction — but still, underneath,
two bus cycles.)



### Exercise 5 — A 300-byte local array on a 2 KB system

> A function on the 2 KB embedded system declares a 300-byte local array.
> Explain, in terms of the three memory regions, why this is a different kind of
> risk than a 300-byte `malloc` on a desktop — and state what an affine type
> system would have to establish to place such a value safely.

*The three regions.* A program's RAM divides into static/global storage, the
*stack* (function frames, growing toward the heap), and the *heap* (dynamic
allocation, growing toward the stack). A *local* array lives in the current
stack frame; a `malloc`'d array lives on the heap.

*Why the risks differ.*

- On the *2 KB embedded* system, the 300-byte array is a stack allocation —
  about 15% of *all* RAM, in a single frame. There is no virtual memory and no
  operating system to police the boundary. If the stack grows into the heap or
  the globals, the result is *silent corruption*: a write to one variable
  quietly clobbers another, with no fault and no diagnostic. The failure is
  undetectable at the point it happens and may surface arbitrarily later.
- On the *desktop*, the 300-byte `malloc` is a heap allocation on a large,
  virtual-memory-backed heap managed by an allocator. If the request cannot be
  satisfied it fails *explicitly* — `malloc` returns `NULL` — and the program can
  check for it. The risk is real but *detectable and local*.

So the embedded case is dangerous because the cost is paid in a scarce, shared,
unguarded region (the stack) where overflow is silent; the desktop case fails
loudly and in a region designed to absorb it.

*What an affine type system must establish.* To place such a value safely —
on the stack, or reusing space — the type system must prove that the array has a
*single owner and does not escape its scope*: it is used *at most once* along
any path, it is not aliased by another live reference, and no reference to it
outlives the frame that holds it. Establishing single ownership plus no-escape
lets the compiler bound the value's lifetime statically and therefore bound the
stack footprint, placing the 300 bytes safely (or freeing/reusing them) without
runtime checks. This is precisely the affine discipline Lark adopts in
Chapter 5, whose payoff in code generation (no ownership checks needed) appears
in Chapter 9.
