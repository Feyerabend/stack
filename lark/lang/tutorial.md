# A Short Tour of Lark

*Lark — **L**ambda **A**ffine **R**esource **K**ernel. Companion to* The Language Stack: From Silicon to Semantics.

Lark is a small, purely functional language: Hindley–Milner type inference, *affine ownership* as a resource discipline (no garbage collector, no mutation), traits for polymorphism, and RISC-V as its compilation target. This tour walks the teaching programs in `lark/01/tests/` (and a few from later phases), from `Hello` to traits. Every snippet here is a real, runnable Lark program.

## 1. Hello, Lark

A program is a `module` with a `main` function. The one surprise is its signature: `main` takes an `IO` and returns an `IO`. That is the whole of Lark's effect system in miniature, and the next sections explain why.

```lark
(* module declaration, IO threading, the print built-in *)
module Hello

fn main(io : IO) : IO =
  print(io, "Hello, Lark!")
```

> **output:** Hello, Lark!

## 2. Values, functions, arithmetic

Top-level values use `let`; functions use `fn name(args) : Ret = body`. Inside a body, `let … in …` binds a local. There is no statement/expression split — everything is an expression, including `if … then … else`. `show` turns a value into a `String`.

```lark
module Arithmetic

let x : Int = 6
let y : Int = 7

fn square(n : Int) : Int = n * n

fn max(a : Int, b : Int) : Int =
  if a > b then a else b

fn main(io : IO) : IO =
  let product = x * y in
  let sq      = square(6) in
  let largest = max(3, 7) in
  let io      = print(io, show(product)) in
  let io      = print(io, show(sq)) in
  print(io, show(largest))
```

> **output:** 42 · 36 · 7

## 3. Recursion

Functions recurse directly. Lark is pure, so a loop *is* a recursion.

```lark
module Recursion

fn factorial(n : Int) : Int =
  if n == 0 then 1
  else n * factorial(n - 1)

fn fib(n : Int) : Int =
  if n < 2 then n
  else fib(n - 1) + fib(n - 2)
```

> **output:** `factorial(10)` → 3628800, `fib(10)` → 55

A *tail* call — a recursive call in tail position — is compiled to a jump, not a stack frame, so an accumulator loop runs in constant space. This one counts to a million without overflowing:

```lark
fn sum_to(n : Int, acc : Int) : Int =
  if n == 0 then acc
  else sum_to(n - 1, acc + n)   (* tail call: no stack growth *)
```

> **output:** `sum_to(1000000, 0)` → 500000500000

## 4. Affine ownership: why IO is threaded

Here is Lark's defining idea. An *affine* value may be used **at most once**. `IO` is affine — so each call to `print` *consumes* the `io` token and hands back a fresh one, which you must bind and pass on:

```lark
let io = print(io, show(product)) in   (* old io consumed, new io bound *)
let io = print(io, show(sq))      in
print(io, show(largest))               (* the last use returns the final IO *)
```

You cannot use the same `io` twice, and you cannot drop it — the type checker rejects both. That single rule gives a pure language a well-defined *order* of effects without any mutable state: the data dependency on `io` is the sequencing. The same discipline governs any resource you mark affine (a file handle, a buffer); "do not use a closed handle" becomes a compile-time guarantee rather than a runtime hope. Values that are safe to copy freely opt out with an `impl Copy` — the next section shows what its absence costs, and §9 puts one to use.

## 5. When the checker says no

The flip side of affine ownership is what the checker *refuses*. These programs type-check in most languages; Lark rejects them before they ever run. (They live in `lark/01/tests/errors/`.)

```lark
(* IO is affine: it has no Copy, so it cannot be used twice *)
module AffineError

fn use_twice(io : IO) : (IO, IO) =
  (io, io)
```

> **rejected:** type error — `io` is consumed more than once

```lark
module NoCopyError

type Handle = | Handle of Int   (* no impl Copy — so Handle is affine *)

fn duplicate(h : Handle) : (Handle, Handle) =
  (h, h)
```

> **rejected:** type error — `Handle` is not `Copy`, cannot be duplicated

A type with no `impl Copy` is affine by default; you declare `impl Copy` only when duplicating a value is genuinely free (as for `Int`, `Bool`, and the integer lists of §9). This is resource safety the compiler *proves*, not a convention you maintain by hand.

## 6. Data types and pattern matching

A `type` declares an algebraic data type — a choice of *constructors*, each carrying zero or more fields. You take them apart with `match … with … end`; `_` is a wildcard.

```lark
module Adt

type Shape =
  | Circle of Float
  | Rect   of Float, Float
  | Point

let pi : Float = 3.14159

fn area(s : Shape) : Float =
  match s with
  | Circle(r)  => pi * r * r
  | Rect(w, h) => w * h
  | Point      => 0.0
  end

fn describe(s : Shape) : String =
  match s with
  | Circle(_)  => "circle"
  | Rect(_, _) => "rect"
  | _          => "unknown"
  end
```

> **output:** `area(Circle(5.0))` → 78.53975, `area(Rect(3.0, 4.0))` → 12.0

## 7. Tuples

Tuples are anonymous, fixed-size products — `(Int, Int)` is a pair — built and destructured with the same `(…)` syntax, and matched like any other pattern.

```lark
module Tuples

fn swap(p : (Int, Int)) : (Int, Int) =
  match p with
  | (x, y) => (y, x)
  end

fn min_max(a : Int, b : Int) : (Int, Int) =
  if a < b then (a, b) else (b, a)
```

> **output:** `min_max(7, 2)` is `(2, 7)`; swapped, `(7, 2)`

## 8. Literal and boolean patterns

A `match` arm can be a literal value or the `Bool` constructors `True` / `False`, not only your own constructors. (`Bool` opts into `Copy`, so it passes around freely.)

```lark
module LitPat

impl Copy for Bool = {}

fn describe(n : Int) : String =
  match n with
  | 0 => "zero"
  | 1 => "one"
  | _ => "many"
  end

fn yesno(b : Bool) : String =
  match b with
  | True  => "yes"
  | False => "no"
  end
```

> **output:** `describe(0)` → zero, `describe(99)` → many, `yesno(True)` → yes

## 9. Generics, lists, higher-order functions

Types take parameters (`List a`), and a recursive constructor builds the classic cons-list. Functions are values: pass them as arguments, or write them inline as lambdas with `fn(args) => body`. `impl Copy for List(Int) = {}` marks integer lists as freely copyable.

```lark
module Lists

type List a =
  | Nil
  | Cons of a, List(a)

impl Copy for List(Int) = {}

fn fold(f : Int -> Int -> Int, acc : Int, xs : List(Int)) : Int =
  match xs with
  | Nil           => acc
  | Cons(x, rest) => fold(f, f(acc, x), rest)
  end

fn map(f : Int -> Int, xs : List(Int)) : List(Int) =
  match xs with
  | Nil           => Nil
  | Cons(x, rest) => Cons(f(x), map(f, rest))
  end

fn main(io : IO) : IO =
  let xs      = Cons(1, Cons(2, Cons(3, Cons(4, Cons(5, Nil))))) in
  let total   = fold(fn(acc, x) => acc + x, 0, xs) in
  let doubled = map(fn(x) => x * 2, xs) in
  print(io, show(total))
```

> **output:** `total` → 15; `doubled` is 2 4 6 8 10

## 10. Closures

A function can *return* a function that captures values from its environment — a closure. `adder(5)` hands back a function that remembers `n = 5`; `compose` builds a new function from two others.

```lark
module Closures

fn adder(n : Int) : Int -> Int =
  fn(x : Int) => n + x            (* captures n *)

fn compose(f : Int -> Int, g : Int -> Int) : Int -> Int =
  fn(x : Int) => f(g(x))

fn main(io : IO) : IO =
  let add5   = adder(5) in
  let double = fn(x : Int) => x * 2 in
  let io     = print(io, show(add5(10))) in
  print(io, show(compose(double, add5)(3)))
```

> **output:** `add5(10)` → 15, `compose(double, add5)(3)` → 16

## 11. Errors as values: Result

Lark has no exceptions. A function that can fail returns a value that says so, and the caller must `match` on it — the type system will not let you forget the error case.

```lark
type Result a b =
  | Ok  of a
  | Err of b

fn safe_divide(x : Int, y : Int) : Result(Int, String) =
  if y == 0 then Err("division by zero")
  else Ok(x / y)

fn show_result(r : Result(Int, String)) : String =
  match r with
  | Ok(n)  => show(n)
  | Err(s) => "error: " + s
  end
```

> **output:** `safe_divide(1, 0)` shown → error: division by zero

## 12. Traits: polymorphism with a bound

A `trait` names a capability; an `impl` supplies it for a type. A function can then demand the capability with a *bound* in square brackets — `[Describe a]` reads "for any type `a` that implements `Describe`."

```lark
trait Describe a = {
  fn describe : a -> String
}

impl Describe for Color = {
  fn describe(c) =
    match c with
    | Red   => "red"
    | Green => "green"
    | Blue  => "blue"
    end
}

fn label[Describe a](x : a) : String =
  "the color is " + describe(x)
```

> **output:** `label(Red)` → the color is red

## 13. Running these programs, and reading real ones

The programs above live in `lark/01/tests/` (`01_hello.lark` … `08_traits.lark`), with the closures, tuples, and literal-pattern examples in the later phases' `tests/` (`10`–`18`) and the rejected programs in `tests/errors/`. Lark is built in phases — the CEK interpreter that runs source directly is Phase 04, the compiler to RISC-V is Phase 05, and a native C runtime is Phase 07. See the top-level [lark/README.md](../README.md) for how to build and run a given phase.

When the tour is not enough, `lark/07/samples/` holds nine complete programs in pure Lark — merge sort, a binary search tree, a prime sieve, N-queens, an expression evaluator, run-length encoding, Towers of Hanoi, Conway's Game of Life, and a recursive-descent arithmetic parser — the language doing real work.

| If you want… | Look at… |
|--------------|----------|
| the grammar and lexer | `lark/01/` (book ch. 3) |
| the parser | `lark/02/` (ch. 4) |
| type inference + affine checking + traits | `lark/03/` (ch. 5) |
| the interpreter (CEK machine) | `lark/04/` (ch. 6) |
| the compiler to RISC-V | `lark/05/` (ch. 7, 9) |
| nine complete sample programs | `lark/07/samples/` (ch. 10) |
| the soundness proof | `lark/formal/proof/` (ch. 11–12) |

---

*A short tour of Lark, rebuilt from the acceptance tests in `lark/01/tests/`. For the full story — silicon to semantics — read the book.*
