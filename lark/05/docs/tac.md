
## Lark TAC — Three-Address Code IR

Reference for the intermediate representation used in Phase 5.
Source: `05/src/tac.py` and `05/src/lower.py`.



### Overview

The TAC IR sits between the typed AST (`typed_tree.py`) and the RISC-V
assembler (`asm.py`).  Every expression in the typed AST is flattened into
a sequence of instructions that each name at most one result:

```
t2 = t0 + t1
```

This flatness is the key property: each instruction corresponds directly to one
or two RISC-V instructions, the liveness of every temporary is visible from
the instruction sequence alone, and optimisation passes can insert or delete
instructions without restructuring a tree.

**Pipeline position**

```
parser → infer → lower → tac_vm          (correctness oracle)
                       ↓
                      cfg → liveness → igraph → regalloc → asm → runtime → RV32I
```

| Module | Input | Output |
|--------|-------|--------|
| `lower.py` | `TProgram` | `TAC` |
| `tac_vm.py` | `TAC` | execution (oracle) |
| `cfg.py` | `Function` | `CFG` — basic blocks + successor/predecessor edges |
| `liveness.py` | `CFG` | `Liveness` — `live_in`/`live_out` per block; per-instruction sets |
| `igraph.py` | `CFG` + `Liveness` | `IGraph` — interference edges + copy edges |
| `regalloc.py` | `CFG` + `Liveness` | `Allocation` — Tmp → register or spill slot |
| `asm.py` | `TAC` + `Allocation` | RISC-V assembly text |



### Values

Every operand in a TAC instruction is a `Val`, one of:

| Class | Description |
|-------|-------------|
| `Tmp(name)` | A named temporary. Every computation produces one. |
| `Const(value)` | A compile-time constant: `int`, `float`, `bool`, `str`, or `None` (unit). |

Temporaries are strings, not integers.  A fresh name like `t3` or `clos0`
makes printed TAC self-explanatory.



### Instructions

#### Data movement

| Instruction | Notation | Meaning |
|-------------|----------|---------|
| `IAssign(dst, src)` | `dst = src` | Copy a value to a fresh temporary. Used to collect match-arm results into a shared destination. |
| `IBinOp(dst, op, l, r)` | `dst = l op r` | Binary operation. `op` is `+`, `-`, `*`, `/`, `%`, `==`, `!=`, `<`, `>`, `<=`, `>=`, `&&`, `\|\|`. For strings, `+` is concatenation. |
| `IUnary(dst, op, src)` | `dst = op src` | Unary operation. `op` is `-` (arithmetic negation) or `not` (boolean negation). |

#### Calls

| Instruction | Notation | Meaning |
|-------------|----------|---------|
| `ICall(dst, fn, args)` | `dst = call fn(args...)` | Static call to a known named function. `dst` may be `None` for void calls (e.g., `__lark_match_fail`). |
| `IClosureCall(dst, fn, arg)` | `dst = fn(arg)` | Indirect call through a closure value. Always passes **one** argument — closures are curried. |

#### Control flow

| Instruction | Notation | Meaning |
|-------------|----------|---------|
| `ILabel(name)` | `name:` | A branch target. Labels begin with `.`. |
| `IJump(label)` | `jump label` | Unconditional branch. |
| `ICondJump(cond, true_label, false_label)` | `if cond jump T else F` | Branch on a boolean temporary. |
| `IReturn(val)` | `return val` | Return from the current function. `val` is `None` for functions returning unit. |

#### Heap allocation and access

| Instruction | Notation | Meaning |
|-------------|----------|---------|
| `IAlloc(dst, tag, fields)` | `dst = alloc tag(fields...)` | Heap-allocate a tagged record. `tag` is the constructor name (string). Fields are stored in order after the tag. |
| `IGetTag(dst, src)` | `dst = tag(src)` | Read the constructor tag of a heap record. Used in match pattern checks. |
| `IGetField(dst, src, idx)` | `dst = src[idx]` | Read one field from a heap record. Field index 0 is the first field (the tag word is not counted). |
| `IAllocClosure(dst, fn_name, captured)` | `dst = closure(fn; caps...)` | Build a closure record: first word is the function pointer `fn_name`, remaining words are captured values. |



### Functions and programs

```
Function(name, params, body)
```

A `Function` is a flat list of instructions.  `params` is a tuple of
parameter names (strings).  `body` is a list of `Instr` objects.

```
TAC(functions)
```

A `TAC` program is a list of `Function` objects in definition order.
Functions appear before their callers (the lowerer emits lifted lambdas before
the enclosing function).



### Calling conventions

#### Top-level functions

```
fn foo(a, b):
    …
    return result
```

Parameters arrive in positional order.  Return value is the argument to
`IReturn`.  At the RISC-V level, parameters go in `a0`–`a7`; the return
value comes back in `a0`.

#### Closure functions

All lifted lambda functions use the uniform signature `(env, arg)`:

```
fn foo$lam0(env, x):
    cap0 = env[0]    ← first captured variable
    cap1 = env[1]    ← second captured variable
    …
```

`env` is the closure record itself (first word = function pointer, remaining
words = captured values).  Every closure function has `env` as its first
parameter, even if it captures nothing — the runtime calling convention is
uniform.

#### `IClosureCall` dispatch

```
dst = f(arg)
```

At runtime:
1. `fn_ptr = f[0]`          — load function pointer from closure record
2. `call fn_ptr(f, arg)`    — `a0 = f` (env = the closure), `a1 = arg`
3. `dst = a0`               — result from `a0`



### Heap representation

#### ADT / tuple

```
alloc Cons(head, tail)   →   { tag="Cons", fields=[head, tail] }
```

- First word: tag (string in the IR; integer tag-id in the assembly)
- Words 1…n: the fields, in declaration order

`IGetTag(t, src)` loads the tag.  `IGetField(t, src, 0)` loads field 0.

#### Closure

```
closure(fn; x, y)   →   { fn_ptr=&fn, caps=[x, y] }
```

- First word: function pointer
- Words 1…n: captured values, in the order they appear as free variables
  (sorted alphabetically by name)

`IGetField(cap0, env, 0)` inside a lifted function loads the first captured
variable from the closure record that was passed as `env`.

#### Unit tuple

`TTupleExpr([])` (empty tuple / unit) lowers to `Const(None)`.
A non-empty tuple `(a, b)` lowers to `IAlloc(dst, "()", [a, b])`.



### Multi-param lambda desugaring

A multi-param lambda is desugared into a chain of single-param closures
before lifting.  This matches the CEK machine's curried closure semantics.

```
fn(a, b) => a + b
```

becomes two lifted functions:

```
fn encl$lam0(env, a):
    clos0 = closure(encl$lam0$lam1; a)
    return clos0

fn encl$lam0$lam1(env, b):
    cap0 = env[0]          ← a
    t0 = cap0 + b
    return t0
```

Calling `f(3)` gives back a closure.  Calling that closure with `4` gives `7`.



### Pattern match lowering

A match expression generates a sequence of arm-check blocks.  Each arm gets
two labels: `l_body` (check passed) and `l_next` (try the next arm).

```lark
match xs with
| Nil       => acc
| Cons(x, rest) => fold(f, f(acc, x), rest)
```

lowers to:

```
    tag0 = tag(xs)
    eq1  = tag0 == 'Nil'
    if eq1 jump .arm2 else .next3
.arm2:
    r0 = acc
    jump .match_end
.next3:
    tag4 = tag(xs)
    eq5  = tag4 == 'Cons'
    if eq5 jump .tag_ok6 else .next7
.tag_ok6:
    …                   ← sub-pattern checks (always pass for TPVar)
    jump .arm8
.arm8:
    x    = xs[0]
    rest = xs[1]
    …
    jump .match_end
.next7:
    call __lark_match_fail()
.match_end:
    return r0
```

Tags are string constants in the TAC IR.  The assembler converts them to
integer IDs (sorted alphabetically over all constructors in the program).



### Global let declarations

Top-level `let` bindings are lowered into a special `__global_init__`
function that runs before `main`:

```lark
let pi = 3.14159
```

becomes:

```
fn __global_init__():
    pi = 3.14159
    return ()
```

In the TAC VM, `__global_init__` runs first and its final register state
becomes the global environment.  Any frame that cannot find a temporary in its
own registers falls back to the global environment.

In the RISC-V backend, global variables will be stored in the `.data` section.



### Named built-ins

The following names are treated as static calls (`ICall`) and resolved by the
runtime. The lowerer (`lower.py`) routes source-level operations to the
appropriate built-in based on the operand types in the typed tree.

#### I/O

| Name | Signature | Notes |
|------|-----------|-------|
| `print` | `(IO, String) → IO` | Prints the string, returns the IO token |
| `read` | `(IO) → (IO, String)` | Reads a line from stdin |
| `__lark_match_fail` | `() → ⊥` | Called when no match arm succeeds |

#### Show and conversion

| Name | Signature | Notes |
|------|-----------|-------|
| `show` | `(a) → String` | Generic show; used for ADT, Int, String values |
| `__show_float` | `(Float) → String` | Routed by `show(Float expr)` |
| `__show_bool` | `(Bool) → String` | Routed by `show(Bool expr)`; returns `"true"`/`"false"` |
| `int_to_float` | `(Int) → Float` | |
| `float_to_int` | `(Float) → Int` | Truncates toward zero |
| `int_to_string` | `(Int) → String` | |
| `float_to_string` | `(Float) → String` | |

#### Float arithmetic (RV32I has no FP instructions)

| Name | Signature | Notes |
|------|-----------|-------|
| `__float_add` | `(Float, Float) → Float` | Routed by `+` on Float operands |
| `__float_sub` | `(Float, Float) → Float` | Routed by `-` on Float operands |
| `__float_mul` | `(Float, Float) → Float` | Routed by `*` on Float operands |
| `__float_div` | `(Float, Float) → Float` | Routed by `/` on Float operands |
| `__float_lt`  | `(Float, Float) → Bool`  | Routed by `<` when left operand is Float |
| `__float_le`  | `(Float, Float) → Bool`  | Routed by `<=` when left operand is Float |
| `__float_gt`  | `(Float, Float) → Bool`  | Routed by `>` when left operand is Float |
| `__float_ge`  | `(Float, Float) → Bool`  | Routed by `>=` when left operand is Float |

Float comparisons must go through stubs because RISC-V `slt` (signed
integer less-than) gives wrong results for negative IEEE 754 values.

#### String

| Name | Signature | Notes |
|------|-----------|-------|
| `__str_concat` | `(String, String) → String` | Routed by `+` on String operands |
| `string_length` | `(String) → Int` | |

#### Math

| Name | Signature | Notes |
|------|-----------|-------|
| `int_abs` | `(Int) → Int` | |
| `float_abs` | `(Float) → Float` | RV32 VM clears the sign bit |
| `float_sqrt` | `(Float) → Float` | Returns NaN for negative input |
| `float_floor` | `(Float) → Float` | |
| `float_ceil` | `(Float) → Float` | |



### Worked example

```lark
fn adder(n: Int): Int -> Int = fn(x: Int) => n + x
```

*TAC output*

```
fn adder$lam0(env, x):
    cap0 = env[0]      ← n
    t1   = cap0 + x
    return t1

fn adder(n):
    clos0 = closure(adder$lam0; n)
    return clos0
```

*Execution trace* for `adder(5)(10)`:

```
call adder(5)
  → IAllocClosure: clos0 = { fn=adder$lam0, caps=[5] }
  → return clos0

IClosureCall: t = clos0(10)
  → fn_ptr = clos0[0] = adder$lam0
  → call adder$lam0(env=clos0, x=10)
    → cap0 = env[0] = clos0.caps[0] = 5
    → t1 = 5 + 10 = 15
    → return 15
  → t = 15
```
