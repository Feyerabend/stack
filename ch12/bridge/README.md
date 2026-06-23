# The Lark ↔ MLTT Bridge

Companion to **Chapter 12, "Types as Proofs"** (§12.1 Curry–Howard made exact,
§12.4 Lark's soundness proof, read).

The chapter's central claim is that **type-checking is proof-checking**: a type
is a proposition, a program of that type is a proof, and the type checker of
Chapter 5 and the proof checker of Chapter 12 are the same kind of program. This
directory lets you *run* that claim on actual Lark programs, rather than take it
on faith.

It adds no new proof. The proof is Lark's own, in
[`lark/formal/proof/`](../../lark/formal/proof/) — the four `.lcore` files and the
`lcore` kernel that Chapter 11 stood on. This directory is only a guided way to
feed concrete examples to that kernel and read its verdict.

## Run it

```sh
./run_bridge.sh
```

(The script builds the `lcore` kernel if needed, then runs the real proof.)

## What it shows

### Direction 1 — a well-typed program *is* a proof

Each Lark program below is written by hand as an intrinsically typed `lcore` term
`Expr g t` (the smoke tests already in `lark-typing.lcore`). Building that term
**is** discharging the typing derivation; the kernel confirms it by reporting the
type it assigns.

| Lark program | lcore term | kernel assigns |
|---|---|---|
| `fn f(x : Bool) : Bool = x` | `id_bool` | `Expr empty (TFn TBool TBool)` |
| `if true then 1 else 2` | `ite_int` | `Expr empty TInt` |
| `fn app(f : Int -> Int, x : Int) : Int = f x` | `apply_f` | `Expr (ext TInt (ext (TFn TInt TInt) empty)) TInt` |

Read `id_bool : Expr empty (TFn TBool TBool)` as: *in the empty context, this term
is a proof that the proposition `Bool → Bool` is inhabited* — which is exactly
what it means for `fn f(x:Bool):Bool = x` to type-check. The context `ext … empty`
in `apply_f` is the typing environment of Chapter 5, written as a de Bruijn list.

### Direction 2 — an ill-typed program has *no* proof

```
Lark (rejected):  (42)(true)        -- apply an Int as if it were a function
lcore:  EApp empty TBool TBool (ELitInt empty) (ELitBool empty true)
```

`EApp` demands its function argument have type `Expr empty (TFn TBool TBool)`, but
`ELitInt empty` has type `Expr empty TInt`. There is no term of the required type,
so the proposition has no proof, and the kernel refuses to build it:

```
type error: type mismatch
  inferred: Expr empty TInt
  expected: Expr empty (TFn TBool TBool)
```

A Lark type error and a failed proof are the same event.

## Why the bridge lives in the comments of `lark-typing.lcore`

Every smoke test in
[`lark-typing.lcore`](../../lark/formal/proof/lark/lark-typing.lcore) is annotated
with the Lark program it encodes (`-- Lark: fn f(x : Bool) : Bool = x`). That file
*is* the bridge — the correspondence table at its top maps each Lark/`infer.py`
construct to its `lcore` counterpart. This directory pulls those annotations into
the foreground and runs them, so the correspondence is something you watch happen
rather than something you read about.

## Where to go next

- **`../kernel/`** — a HoTT/MLTT proof-checker in C, a readable sibling of
  `lcore`: both the type theory it implements and *how* a
  type-checker-that-is-a-proof-checker is built (§12.2, §12.3).
- **`../../lark/formal/proof/`** — Lark's mechanised type-soundness proof, checked
  by the `lcore` kernel (§12.4).
