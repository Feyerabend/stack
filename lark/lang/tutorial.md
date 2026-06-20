# A Tour of Lark

Lark is a small, purely functional language with Hindley-Milner type inference,
algebraic data types, affine ownership, and a resource-threaded IO model.
Its design borrows from OCaml and Rust, simplified for clarity.

**The ideas behind the language.** Every design choice in Lark reflects a
concrete principle from programming language theory:

- *Purity* — functions have no hidden side effects. A function always returns
  the same result for the same arguments. IO is made explicit rather than
  being a global side channel.
- *Hindley-Milner inference* — the compiler derives the most general type for
  every expression. You annotate where it helps the reader, not where the
  compiler needs it.
- *Algebraic data types* — values are built from constructors (sums and
  products). `match` checks all cases at compile time, eliminating a large
  class of pattern-matching bugs.
- *Affine ownership* — values may be used at most once unless marked `Copy`.
  This prevents aliasing, enforces ordered IO, and catches resource-management
  bugs at compile time.
- *Traits* — a lightweight form of ad-hoc polymorphism: defining shared
  behaviour across unrelated types without inheritance.

**How Lark compares to languages you may know.** The ideas above are not
new — they come from decades of research in programming language theory. What
is unusual is having all of them together in a language small enough to read
in a day. Here is where Lark sits relative to languages you may already know.

*Python, Java, C#.* These languages are primarily *imperative and
object-oriented*. Mutation is the default: variables change, objects carry
hidden state, and functions can have invisible side effects. This makes
programs easy to write in the short term but harder to reason about as they
grow: you cannot look at a function in isolation and know what it does without
knowing the state of the world. Types in Java and C# help, but null references,
mutable fields, and unchecked exceptions still leave many bugs invisible until
runtime. Lark has none of this: every function is a pure mathematical mapping
from inputs to outputs, and the type system proves it.

*Haskell.* Haskell is the most direct intellectual ancestor of Lark. It has
purity, Hindley-Milner inference, ADTs, and type classes (Lark's equivalent of traits).
But Haskell also has lazy evaluation, higher-kinded types, type class
hierarchies, and a deep ecosystem of abstract concepts that can overwhelm a
newcomer. Effects in Haskell are handled via *monads* — a mathematically
elegant but initially opaque abstraction. Lark replaces monads with explicit
IO token threading, which is conceptually simpler: you can always see the IO
token moving through the code. Lark is Haskell's ideas, minus the advanced
machinery.

*OCaml.* OCaml is a pragmatic functional language used in compilers,
financial systems, and theorem provers. It has ADTs, pattern matching, modules,
and type inference, but it also permits mutable state and side effects
everywhere — `let x = ref 0 in x := !x + 1` is valid OCaml. The result is a
language that can be used purely or imperatively, which gives flexibility but
removes the compiler's ability to enforce discipline. Lark enforces purity: the
compiler guarantees that a function has no hidden effects, so you do not need
to read its implementation to understand its behaviour.

*Rust.* Rust has an ownership and borrowing system that is close in spirit
to Lark's affine types. Both prevent aliasing and enforce a form of single-use
discipline. But Rust is a systems programming language: its ownership rules
exist primarily to avoid heap allocations and data races in low-level code, and
the rules are correspondingly complex (lifetimes, borrow scopes, `Rc`, `Arc`,
`RefCell`). Lark's affine types serve a different purpose: they make IO
ordering visible in the type system and prevent resource handles from being
used after they are closed, with a simple rule — *use at most once* — that
the compiler checks without any lifetime annotations.

**What Lark adds, even at small scale.** Lark is designed as a teaching
language, not a production tool. Its value is in making a set of ideas
*concrete and runnable* rather than abstract. When you type `let (io, line) =
read(io) in`, you can see the IO token being passed in and returned — the type
system is not hiding an effect in a monad or a global lock; it is right there
in the code. When the compiler rejects an affine variable used twice, you
learn the ownership rule by running into it, not by reading a specification.
When HM inference infers the most general type for a polymorphic function, you
can inspect the inferred type and see exactly what the compiler learned.

These ideas increasingly appear in production software. Rust's ownership model
is directly inspired by affine/linear types. Haskell-style functional
programming patterns have spread into Python, JavaScript, and Scala. Effect
systems and type-safe IO are active research topics in mainstream type theory.
Lark gives you a working laboratory where you can encounter all of these ideas
together in a setting small enough to hold in your head at once.

This tour walks through the whole language in order. Each section builds on
the last. You can run any snippet with:

```
make tac_vm FILE=yourfile.lark
```

---

## 1. Hello, World

```lark
module Hello

fn main(io : IO) : IO =
  print(io, "Hello, Lark!")
```

Every Lark file begins with `module Name`. The entry point is `main`, which
receives an `IO` token and must return one. `print` takes the token and a
string, emits the string to stdout, and hands back a fresh token. There is no
global mutable state — IO is explicit and threaded through calls.

The type of `print` is `IO -> String -> IO`: it takes an IO token, then a
String, and returns a new IO token. The token is a *proof* that you have the
right to perform IO at this moment and that you have consumed all previous IO
tokens in order. What this means is explained in detail in Section 6 and
Section 11.

---

## 2. Lexical Conventions

**Names** — identifiers starting with a lowercase letter: `x`, `my_fn`, `result2`.
Used for variables, function names, and type variables.

**Names with capital first letter** — identifiers starting with uppercase: `Int`,
`Bool`, `Option`, `Cons`. Used for types and data constructors.

**Comments** — `(* ... *)`, may nest, may span lines.

**Keywords** — `and else end export false fn if impl import in let match module
not of or then trait true type with`.

---

## 3. Literals and Basic Types

| Literal | Type | Example |
|---|---|---|
| Integer | `Int` | `42`, `0`, `-1` |
| Float | `Float` | `3.14`, `0.5`, `1.0` |
| Boolean | `Bool` | `true`, `false` |
| String | `String` | `"hello"`, `"line\n"` |
| Unit | `()` | `()` |

String escape sequences: `\"`, `\\`, `\n`, `\t`, `\r`.

Arithmetic operators: `+`, `-`, `*`, `/`, `%`.
Comparison: `==`, `!=`, `<`, `<=`, `>`, `>=`.
Boolean: `and`, `or`, `not`.

**Type inference.** You rarely need to declare the type of a `let` binding or
the return type of a function — the compiler infers it using *Hindley-Milner
type inference*. The algorithm traces how a value is *used* and works backwards
to the most general consistent type. Writing explicit types is good style and
is required in a few specific places (mutually recursive functions), but is
never demanded by the algorithm for simple expressions.

---

## 4. Let Bindings

`let` binds a name to a value. Inside expressions, close it with `in`:

```lark
fn main(io : IO) : IO =
  let x   = 6 in
  let y   = 7 in
  let msg = "the answer is " + show(x * y) in
  print(io, msg)
```

At the top level (outside any expression), `let` is a declaration:

```lark
module Consts

let pi : Float = 3.14159
let tau : Float = pi * 2.0
```

`show` converts a value of any Show-implementing type to its `String`
representation. All built-in types (`Int`, `Float`, `Bool`, `String`) support
Show out of the box. User-defined types need an explicit `impl Show` — see
Section 13.

**Everything is an expression.** There are no statements in Lark. A
`let ... in` block is itself an expression whose value is the body after `in`.
An `if-then-else` is an expression. A `match` is an expression. This
uniformity keeps the language small and predictable: you can nest any
expression inside any other.

---

## 5. Functions

```lark
fn add(x : Int, y : Int) : Int = x + y

fn factorial(n : Int) : Int =
  if n <= 1 then 1
  else n * factorial(n - 1)
```

- Parameter and return types are optional when they can be inferred, but
  writing them is good practice and is required for mutually recursive
  functions.
- `if-then-else` is an expression, not a statement. Both branches must have
  the same type.
- Recursion is just a normal self-call — there is no special `rec` keyword.

**Function types.** A function from `A` to `B` has type `A -> B`. A function
taking two `Int` values and returning an `Int` has type `Int -> Int -> Int`,
which associates right: `Int -> (Int -> Int)`. This *curried* reading means a
two-argument function is really a one-argument function that returns another
one-argument function. Multi-argument call syntax `f(x, y)` is sugar for
applying `f` to `x` and then applying the result to `y`.

Because functions are pure — no side effects — the same call always yields the
same result. The compiler can evaluate, inline, and reorder function calls
freely, which is not possible when functions have hidden state.

**Calling a function:**

```lark
let result = factorial(10)
```

---

## 6. Multiple Results and IO Sequencing

The `IO` token is passed from one `print` call to the next. Each call consumes
the token and produces a fresh one. The canonical pattern is a chain of `let io`:

```lark
fn main(io : IO) : IO =
  let io = print(io, "first line")  in
  let io = print(io, "second line") in
  print(io, "third line")
```

Reading from stdin works the same way:

```lark
fn main(io : IO) : IO =
  let (io, line) = read(io) in
  print(io, "you said: " + line)
```

`read` returns a tuple of the new token and the line that was read — the new
IO token comes first, then the string. Destructure with `(io, line)`.

**Why thread a token?** In a purely functional language, a function applied to
the same arguments always returns the same value. Without a token, two calls
`print(io0, "x")` and `print(io0, "x")` would be identical expressions that
could legally be reordered or deduplicated by the compiler. The token breaks
this symmetry: every call consumes the current token and produces a new one, so
the calls form a *chain* — a data dependency that forces a specific order.

This is not merely a trick. It is a type-level proof that effects happen in
the exact sequence you wrote. Section 11 explains the type-theoretic foundation
(affine ownership) that makes this guarantee work.

---

## 7. Algebraic Data Types

`type` declares a new type. Constructors follow the `|` sigil and may carry
fields listed after `of`.

```lark
type Color =
  | Red
  | Green
  | Blue

type Shape =
  | Rect   of Float, Float
  | Circle of Float
```

**Sum types and product types.** `Color` is a *sum type* (tagged union): a
`Color` value is exactly one of `Red`, `Green`, or `Blue`. Each branch is
an alternative. `Shape` mixes alternatives: a `Rect` carries two `Float`
fields together — that pairing is a *product type* embedded inside the sum.

Algebraic data types (ADTs) are called "algebraic" because the number of
distinct values follows algebraic rules: a sum type with alternatives A and B
has |A| + |B| inhabitants; a product type pairing A and B has |A| × |B|.
Enumerations, optional values, trees, linked lists, and abstract syntax trees
are all naturally expressed as ADTs.

Construct values with the constructor name:

```lark
let c = Circle(5.0)
let r = Rect(3.0, 4.0)
```

Inspect them with `match`:

```lark
fn area(s : Shape) : Float =
  match s with
  | Rect(w, h) => w * h
  | Circle(r)  => 3.14159 * r * r
  end
```

`match` is closed by `end`. Every constructor of the type must be covered, or
you must include a wildcard arm `| _ => ...`. This *exhaustiveness check* is
enforced at compile time: forgetting a case is a type error, not a runtime
crash.

**Nested match:**

```lark
fn describe(s : Shape) : String =
  match s with
  | Rect(w, h) =>
    "rectangle " + show(w) + " × " + show(h)
  | Circle(r)  =>
    "circle r=" + show(r)
  end
```

**Literal and Bool patterns:**

```lark
fn fizz(n : Int) : String =
  match n with
  | 0 => "zero"
  | 1 => "one"
  | _ => "many"
  end
```

```lark
fn yn(b : Bool) : String =
  match b with
  | True  => "yes"
  | False => "no"
  end
```

---

## 8. Parametric Types

Type declarations may take type parameters (written as lowercase names):

```lark
type List a =
  | Nil
  | Cons of a, List(a)
```

`List(Int)`, `List(String)`, `List(List(Bool))` are all concrete types.
`List a` with a lowercase `a` is a *type variable* — it becomes concrete
when you use the type.

```lark
fn length(xs : List(Int)) : Int =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + length(rest)
  end
```

The wildcard `_` discards the head without binding it to a name.

**Monomorphic versus polymorphic.** When you write explicit type annotations
you *pin* the function to a specific type: the `length` above only works on
`List(Int)`. Hindley-Milner can derive a *more general* type when annotations
are omitted or left as type variables. The algorithm gathers constraints from
how a value is used and solves them, then *generalises* any remaining free
type variables into universally quantified ones. The result is a polymorphic
type like `∀a. List(a) -> Int`, meaning "for any element type `a`". This
process is called *let-polymorphism*: the generalised type is recorded at the
binding site, and each call site gets a fresh instantiation.

In practice, writing explicit types on top-level functions is good style and
makes the code self-documenting. For helper functions and local expressions,
letting the compiler infer is fine.

**Parametric functions:**

```lark
fn map(f : Int -> Int, xs : List(Int)) : List(Int) =
  match xs with
  | Nil           => Nil
  | Cons(h, rest) => Cons(f(h), map(f, rest))
  end
```

The annotations here pin `map` to `Int`. To recover full generality you would
omit the annotations and let HM infer the polymorphic type — but for tutorial
clarity the concrete type is shown.

---

## 9. Higher-Order Functions and Closures

Functions are first-class values. `fn(params) => body` is an anonymous
function (lambda):

```lark
fn adder(n : Int) : Int -> Int =
  fn(x : Int) => n + x

fn main(io : IO) : IO =
  let add5 = adder(5) in
  print(io, show(add5(10)))    (* prints 15 *)
```

`adder` returns a *closure*: an anonymous function bundled with the
environment in which it was created. When `adder(5)` is called, the result
captures `n = 5`. The closure `fn(x : Int) => n + x` can be called later with
any `x`, always using the captured `n`. Closures are the primary mechanism for
data-carrying functions in Lark.

Closures can be passed as arguments:

```lark
fn apply_twice(f : Int -> Int, x : Int) : Int =
  f(f(x))

fn main(io : IO) : IO =
  let double = fn(x : Int) => x * 2 in
  print(io, show(apply_twice(double, 3)))    (* prints 12 *)
```

`f` is called twice inside `apply_twice`. Function types are always `Copy` in
Lark — functions are code, not resources, so reusing the same function value
any number of times is unconditionally safe.

**Function composition:**

```lark
fn compose(f : Int -> Int, g : Int -> Int) : Int -> Int =
  fn(x : Int) => f(g(x))
```

---

## 10. Tuples

Tuples group values of different types without naming them:

```lark
fn swap(p : (Int, String)) : (String, Int) =
  match p with
  | (n, s) => (s, n)
  end

fn main(io : IO) : IO =
  let pair    = (42, "hello") in
  let swapped = swap(pair) in
  match swapped with
  | (s, n) =>
    let io = print(io, s) in
    print(io, show(n))
  end
```

Tuples are structural — `(Int, String)` is a distinct type from
`(String, Int)`. There is no named struct syntax; use a single-constructor ADT
when field names aid readability.

**Tuples as multiple return values.** Lark functions technically take one
argument and return one value; returning multiple results is done via a tuple.
The `read` built-in does exactly this — it returns `(IO, String)` — so you
can bind both at once with a pattern:

```lark
let (io, line) = read(io) in ...
```

A tuple pattern like `(io, line)` matches positionally: `io` is bound to the
first field and `line` to the second.

---

## 11. Affine Ownership

Lark variables are **affine** by default: each value may be used **at most
once**. This is enforced at compile time by the type checker, which counts how
many times each locally-bound variable is referenced.

```lark
type Handle = | Handle of Int    (* a resource — not Copy by default *)

fn bad(h : Handle) : (Handle, Handle) =
  (h, h)    (* ERROR — h used twice *)
```

To allow multiple uses, declare a type `Copy`:

```lark
impl Copy for Handle = {}

fn ok(h : Handle) : (Handle, Handle) =
  (h, h)    (* fine now *)
```

Built-in Copy types: `Int`, `Float`, `Bool`, `String`, `()`.
User types opt in with `impl Copy for MyType = {}`.

**The theory: linear and affine types.** The idea comes from *linear logic*,
introduced by Jean-Yves Girard in 1987. Linear logic treats logical propositions
like physical resources: using a fact *consumes* it rather than leaving it
available for reuse. Applied to types, this leads to a spectrum of disciplines:

| Discipline | Usage rule |
|---|---|
| Linear | used **exactly once** — cannot be dropped or duplicated |
| Affine | used **at most once** — can be dropped, but not duplicated |
| Relevant | used **at least once** — can be duplicated, but not dropped |
| Unrestricted | used **any number of times** — ordinary programming |

Lark adopts the *affine* discipline. You may ignore a value (drop it), but you
may not copy it without an explicit declaration. This catches three important
classes of bugs at compile time:

- **Accidental aliasing** — two names for the same mutable resource that can
  interfere with each other.
- **Use-after-consume** — accessing a resource after it has been given away or
  released.
- **Double-release** — closing or freeing a resource twice.

**Comparison with Rust.** Rust's ownership system is affine types made
practical for systems programming. A Rust value of type `T` without `Clone` is
affine: moving it invalidates the original binding. `impl Clone for T` in Rust
corresponds to `impl Copy for T` in Lark. Rust additionally provides
*borrowing* — temporary, non-consuming access to a value — which Lark omits
for simplicity.

**IO is not Copy.** Each `io` token may be used exactly once, which enforces
a sequential chain of effects. The type checker catches any attempt to use the
same `io` token in two different branches of an `if` or `match`.

**The correct IO pattern** for recursive output is to compute a `String` first
and print once, rather than threading `io` through recursion:

```lark
(* wrong — io appears in both branches of the if *)
fn countdown(io : IO, n : Int) : IO =
  if n == 0 then io
  else
    let io = print(io, show(n)) in
    countdown(io, n - 1)

(* right — build the string purely, print at the end *)
fn countdown_str(n : Int) : String =
  if n == 0 then ""
  else show(n) + "\n" + countdown_str(n - 1)

fn main(io : IO) : IO =
  print(io, countdown_str(5))
```

The "wrong" version fails because Lark's affine checker tracks use counts with
a single counter shared across *both branches* of every `if`. Even though only
one branch executes at runtime, the checker sees `io` in the `then` branch
(returned as-is) and again in the `else` branch (passed to `print`), and
counts this as a double use. This is a deliberate trade-off: the check is
simple and sound — it never misses a true double use — at the cost of
rejecting some programs that would in fact be safe at runtime.

The right pattern — compute a pure value inside the `if`, then perform IO once
outside — cleanly separates the *decision* (pure, no IO) from the *effect*
(one IO action), which is the idiomatic structure for a purely functional
program.

---

## 12. Mutual Recursion

Two functions that call each other can be declared at the top level in any
order — forward references are automatically resolved. Both functions must
carry full type signatures:

```lark
module Parity

impl Copy for Bool = {}

fn is_even(n : Int) : Bool =
  if n == 0 then True
  else is_odd(n - 1)

fn is_odd(n : Int) : Bool =
  if n == 0 then False
  else is_even(n - 1)
```

Type signatures are required for mutually recursive functions because type
inference needs a declared type to break the circularity — without it, the
checker would need to simultaneously solve the types of both functions, which
standard Hindley-Milner cannot do in a single pass.

---

## 13. Traits

A **trait** names a family of operations parameterised over a type. An **impl**
provides the implementations for a specific type.

```lark
trait Describe a = {
  fn describe : a -> String
}

type Color = | Red | Green | Blue

impl Describe for Color = {
  fn describe(c) =
    match c with
    | Red   => "red"
    | Green => "green"
    | Blue  => "blue"
    end
}
```

**Traits as ad-hoc polymorphism.** Parametric polymorphism (Section 8) lets
you write code that works for *any* type `a` with no special knowledge of `a`
at all. Traits enable *ad-hoc polymorphism*: a single name (`describe`, `show`)
can have different implementations for different types, chosen at compile time
based on the concrete type in use.

This is similar to type classes in Haskell and interfaces in Go. Unlike
object-oriented interfaces, traits in Lark are defined separately from the
type and can be added retroactively: you can implement `Describe` for a type
that was defined in a different module, without modifying it.

Functions can require a trait on a type variable by listing **bounds** in
square brackets:

```lark
fn label[Describe a](x : a) : String =
  "the color is " + describe(x)

fn main(io : IO) : IO =
  print(io, label(Red))    (* the color is red *)
```

Bounds may be stacked: `fn foo[Copy a, Show b](x : a, y : b) : String`.

**`Show` is a built-in trait.** The built-in `show` function works on `Int`,
`Float`, `Bool`, and `String` out of the box. It does *not* work on arbitrary
user types unless they implement Show. You extend `show` to your own types
with `impl Show`:

```lark
impl Show for Color = {
  fn show(c) =
    match c with
    | Red   => "Red"
    | Green => "Green"
    | Blue  => "Blue"
    end
}

fn main(io : IO) : IO =
  print(io, show(Red))     (* Red *)
```

---

## 14. Modules and Imports

Each file is a module. Use `export` to make a declaration visible to importers:

```lark
(* shapes.lark *)
module Shapes

let pi : Float = 3.14159

export type Shape =
  | Rect   of Float, Float
  | Circle of Float

export fn area(s : Shape) : Float =
  match s with
  | Rect(w, h) => w * h
  | Circle(r)  => pi * r * r
  end
```

`pi` is private (no `export`). Import selectively with `exposing`:

```lark
(* main.lark *)
module Main

import Shapes exposing (Shape, area)

fn main(io : IO) : IO =
  print(io, show(area(Circle(5.0))))
```

---

## 15. The Standard Library

Import `Stdlib` for common utilities:

```lark
import Stdlib exposing (
  min_int, max_int, abs_int, clamp_int, pow_int,
  min_float, max_float, abs_float, sqrt_float, floor_float, ceil_float,
  length, repeat_str, spaces,
  Option, None, Some,
  is_some, is_none, unwrap_or, map_opt, and_then
)
```

**Integer utilities:** `min_int`, `max_int`, `abs_int`, `clamp_int`, `pow_int`

**Float utilities:** `min_float`, `max_float`, `abs_float`, `sqrt_float`,
`floor_float`, `ceil_float`

**String utilities:** `length` (character count), `repeat_str`, `spaces`

**Option type:**
```lark
type Option a =
  | None
  | Some of a
```

The Stdlib Option helper functions are currently specialised to `Option(Int)`:

```
is_some   : Option(Int) -> Bool
is_none   : Option(Int) -> Bool
unwrap_or : Option(Int) -> Int -> Int
map_opt   : (Int -> Int) -> Option(Int) -> Option(Int)
and_then  : (Int -> Option(Int)) -> Option(Int) -> Option(Int)
```

For other element types, pattern-match on `Option` directly:

```lark
fn unwrap_string(opt : Option(String), default : String) : String =
  match opt with
  | None    => default
  | Some(s) => s
  end
```

**Built-in functions** (always in scope, no import needed):

| Function | Type | Description |
|---|---|---|
| `print` | `IO -> String -> IO` | Print a line to stdout |
| `show` | `a -> String` | Convert to String (requires Show instance) |
| `read` | `IO -> (IO, String)` | Read a line from stdin; IO token comes first |
| `string_length` | `String -> Int` | Length in characters |
| `int_abs` | `Int -> Int` | Absolute value |
| `float_abs` | `Float -> Float` | Absolute value (float) |
| `float_sqrt` | `Float -> Float` | Square root |
| `float_floor` | `Float -> Float` | Floor |
| `float_ceil` | `Float -> Float` | Ceiling |
| `int_to_float` | `Int -> Float` | Widen integer to float |
| `float_to_int` | `Float -> Int` | Truncate float to integer |
| `int_to_string` | `Int -> String` | Format integer as string |
| `float_to_string` | `Float -> String` | Format float as string |

---

## 16. Worked Examples

### Merge Sort

```lark
module MergeSort

type List a = | Nil | Cons of a, List(a)
impl Copy for List(Int) = {}

fn merge(xs : List(Int), ys : List(Int)) : List(Int) =
  match xs with
  | Nil => ys
  | Cons(x, xrest) =>
    match ys with
    | Nil => Cons(x, xrest)
    | Cons(y, yrest) =>
      if x <= y then Cons(x, merge(xrest, Cons(y, yrest)))
      else           Cons(y, merge(Cons(x, xrest), yrest))
    end
  end
```

`impl Copy for List(Int) = {}` is required here because the pattern-bound
names `xrest` and `yrest` appear in both branches of the inner `if`, so the
list type must be Copy.

### N-Queens (Backtracking)

Three functions work together to count solutions. `solve` and `try_col` call
each other (mutual recursion) while `safe` is a plain recursive helper. All
three need full type annotations. `placed` is a `List(Int)` referenced
multiple times per call, so `impl Copy for List(Int) = {}` is required:

```lark
module Queens

type List a = | Nil | Cons of a, List(a)
impl Copy for List(Int) = {}

fn safe(col : Int, placed : List(Int), dist : Int) : Bool =
  match placed with
  | Nil           => true
  | Cons(q, rest) =>
    if col == q                      then false
    else if int_abs(col - q) == dist then false
    else safe(col, rest, dist + 1)
  end

fn solve(n : Int, row : Int, placed : List(Int)) : Int =
  if row == n then 1
  else try_col(n, row, placed, 0)

fn try_col(n : Int, row : Int, placed : List(Int), col : Int) : Int =
  if col >= n then 0
  else
    let rest = try_col(n, row, placed, col + 1) in
    if safe(col, placed, 1)
    then solve(n, row + 1, Cons(col, placed)) + rest
    else rest
```

The representation is a list of column positions, one per row placed so far
(head = most recent row). `safe` checks that a new column does not conflict
with any previously placed queen on the same column or diagonal.

### Expression Evaluator

ADTs naturally model syntax trees. Two passes over the same tree — `eval` and
`pretty` — share a single `impl Copy for Expr = {}`:

```lark
type Expr =
  | Num of Int
  | Add of Expr, Expr
  | Mul of Expr, Expr

impl Copy for Expr = {}

fn eval(e : Expr) : Int =
  match e with
  | Num(n)    => n
  | Add(a, b) => eval(a) + eval(b)
  | Mul(a, b) => eval(a) * eval(b)
  end

fn pretty(e : Expr) : String =
  match e with
  | Num(n)    => show(n)
  | Add(a, b) => "(" + pretty(a) + " + " + pretty(b) + ")"
  | Mul(a, b) => "(" + pretty(a) + " * " + pretty(b) + ")"
  end
```

Both `eval` and `pretty` destructure the same `Expr` value, so `Copy` is
needed. The tree cannot be partially consumed: `impl Copy for Expr` declares
that the entire recursive structure is freely duplicable.

### Towers of Hanoi

The recursion is pure — it builds a `String` of moves. A single `print` in
`main` emits the result:

```lark
fn join2(a : String, b : String) : String =
  if string_length(a) == 0 then b
  else if string_length(b) == 0 then a
  else a + "\n" + b

fn hanoi_str(n : Int, src : String, aux : String, dst : String) : String =
  if n == 0 then ""
  else
    let before = hanoi_str(n - 1, src, dst, aux) in
    let move   = "move disk " + show(n) + ": " + src + " -> " + dst in
    let after  = hanoi_str(n - 1, aux, src, dst) in
    join2(join2(before, move), after)

fn main(io : IO) : IO =
  print(io, hanoi_str(4, "A", "B", "C"))
```

`String` is Copy, so `src`, `aux`, and `dst` can be passed to multiple
recursive calls without any `impl Copy` declaration. The function is entirely
pure; IO appears only at the outermost call.

---

## 17. Common Patterns and Pitfalls

**Pattern: accumulator for tail recursion**

```lark
fn sum_acc(xs : List(Int), acc : Int) : Int =
  match xs with
  | Nil           => acc
  | Cons(h, rest) => sum_acc(rest, acc + h)
  end

fn sum(xs : List(Int)) : Int = sum_acc(xs, 0)
```

**Pattern: reconstruct after match**

After `match t with | Node(l, v, r) =>`, the variable `t` is consumed. Use
the pattern-bound names `l`, `v`, `r` directly; do not try to use `t` again:

```lark
fn height(t : Tree) : Int =
  match t with
  | Leaf           => 0
  | Node(l, v, r)  =>
    let hl = height(l) in
    let hr = height(r) in
    1 + (if hl > hr then hl else hr)
    (* t is consumed; use l, v, r instead *)
  end
```

**Pitfall: affine variable in both branches**

This is a type error:

```lark
(* ERROR — io appears in both branches *)
fn bad(b : Bool, io : IO) : IO =
  if b then print(io, "yes")
       else print(io, "no")
```

Lark's affine checker uses a single use-count table shared across both
branches of an `if`. After the `then` branch is checked and `io` is counted,
the same count carries into the `else` branch, where `io` is seen again.
That makes the total count 2, which is rejected.

The correct fix moves `io` outside the conditional entirely:

```lark
fn main(io : IO) : IO =
  let msg = if some_condition then "yes" else "no" in
  print(io, msg)    (* io used exactly once, outside the if *)
```

This pattern — compute a pure value inside the `if`, then perform IO once
outside — separates the *decision* (pure) from the *effect*, which is the
right structure for a purely functional program.

**Pitfall: `and`/`or` vs nested `if`**

Both styles are valid and interchangeable:

```lark
if x == 0 or y == 0 then ...   (* clear *)
if x == 0 then true else y == 0  (* equivalent *)
```

**Pattern: `show` for debugging**

Chain `show` calls and concatenate strings to build multi-field messages:

```lark
print(io, "x=" + show(x) + " y=" + show(y))
```

---

## 18. A Parser in Lark

Parsing is a natural fit for a purely functional language. A grammar rule maps
directly to a recursive function; an abstract syntax tree maps directly to an
algebraic data type; errors are just another variant in a `Result` type; there
is no global mutable state to worry about.

This section builds a small arithmetic expression parser from scratch and runs
it. The technique — *recursive descent* — is the same one used by many
production compilers, including the Lark compiler itself.

### What a parser function is

A parser function takes a sequence of tokens and either succeeds or fails:

- On *success* it returns the parsed value **and** the remaining (unconsumed)
  tokens.
- On *failure* it returns an error message describing what went wrong.

In Lark we capture this with the standard `Result` type:

```lark
type Result a b = | Ok of a | Err of b
```

A single parser that produces an `Expr` has the type:

```
List(Token) -> Result((Expr, List(Token)), String)
```

Read it as: "give me a token stream; I return either `Ok` with a pair (the
parsed expression, the leftover tokens) or `Err` with an error message."

Because parsers are *functions*, they are first-class values. You can pass a
parser to another function, return one from a function, or build a new parser
by combining two existing ones. That idea — parsers as composable first-class
values — is called *parser combinators*.

### Parser combinators: `pand` and `por`

Two combinators cover almost everything in practice.

**Sequence** (`pand`): run the first parser; if it succeeds, hand the result
to a second function that returns the next parser, and run that on the
remaining tokens. This is exactly monadic bind (`>>=` in Haskell notation):
the result of step one flows into step two.

**Choice** (`por`): try the first parser; if it *fails without consuming any
tokens*, try the second parser on the same input. This corresponds to the `|`
separator in a grammar rule.

```lark
fn pand(
  p : List(Token) -> Result((Expr, List(Token)), String),
  f : Expr -> List(Token) -> Result((Expr, List(Token)), String)
) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match p(tokens) with
    | Err(msg)       => Err(msg)
    | Ok((e, rest))  => f(e)(rest)
    end

fn por(
  p : List(Token) -> Result((Expr, List(Token)), String),
  q : List(Token) -> Result((Expr, List(Token)), String)
) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match p(tokens) with
    | Ok(r)  => Ok(r)
    | Err(_) => q(tokens)
    end
```

Both functions *return a parser* — a `fn(tokens : List(Token)) => ...` closure.
`pand` closes over `p` and `f`; `por` closes over `p` and `q`. The returned
closure is a new first-class parser value that can itself be stored, passed
around, or applied to a token stream.

**Calling convention.** When you pass a parser to `pand` or `por`, wrap it in
an explicit lambda:

```lark
pand(fn(t : List(Token)) => my_parser(t), ...)
```

rather than writing `pand(my_parser, ...)` directly. Lark dispatches calls
through closures via an `(env, arg)` convention: a closure always carries an
environment record as its first implicit argument. A proper lambda has this
slot built in by the compiler. A bare top-level name used as a value is only
wrapped in a thin stub that does not include the env slot, which breaks the
dispatch. The explicit lambda is the clean solution and makes the types visible.

### Left-recursion and the tail-function pattern

The natural grammar for arithmetic is left-recursive:

```
expr   ::= expr + term | expr - term | term
term   ::= term * factor | term / factor | factor
factor ::= NUMBER | ( expr )
```

`expr` starts by trying to parse `expr`, which calls itself immediately and
loops forever in a recursive-descent parser. The standard fix rewrites the
grammar using *tail rules*:

```
expr      ::= term expr_tail
expr_tail ::= ('+' | '-') term expr_tail  |  empty
term      ::= factor term_tail
term_tail ::= ('*' | '/') factor term_tail  |  empty
factor    ::= NUMBER  |  '(' expr ')'
```

The `_tail` rules carry an *accumulator* for the left-hand side already
parsed. Each time a tail rule matches an operator and a right operand, it
builds a new tree node and recurses with the new node as the accumulator. When
no operator appears it returns the accumulated value. The left-associative
structure — `a - b - c` becoming `(a-b)-c` and not `a-(b-c)` — falls out
automatically, because each step wraps the old accumulator on the left.

In Lark the tail functions are *curried*: they take the accumulator first and
return a parser:

```lark
fn p_term_tail(lhs : Expr) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) => ...
```

Calling `p_term_tail(lhs)` does not parse anything yet. It returns a closure
that, when applied to a token stream, either consumes a `*` or `/` and
recurses, or hands `lhs` back unchanged. The first call (with the accumulator)
is a plain static function call (`ICall` in the compiler); the second call
(with the token stream) goes through the closure (`IClosureCall`). This
two-step `p_term_tail(lhs)(rest)` is idiomatic for any function that returns
a parser.

### Types: tokens and the abstract syntax tree

Both the input (tokens) and the output (parsed expressions) are algebraic data
types:

```lark
type Token =
  | TNum    of Int      (* a numeric literal *)
  | TPlus               (* + *)
  | TMinus              (* - *)
  | TStar               (* * *)
  | TSlash              (* / *)
  | TLParen             (* ( *)
  | TRParen             (* ) *)

impl Copy for Token = {}

type Expr =
  | Lit of Int
  | Add of Expr, Expr
  | Sub of Expr, Expr
  | Mul of Expr, Expr
  | Div of Expr, Expr

impl Copy for Expr = {}
```

`impl Copy for Token = {}` is needed because pattern-matching on a `Cons` cell
binds the tail list, and the same tail appears in multiple arms. `impl Copy for
Expr = {}` is needed because the same parsed tree must be passed to both `eval`
and `pretty` — two separate traversals. Without `Copy`, the affine checker
would reject the second use.

Note that `impl Copy for List(Token) = {}` is also needed (shown in the full
program below) because `run` uses the token list in two places: once to
reconstruct the source string and once to call the parser.

### The grammar rules, step by step

**`p_factor`** is the base case. It handles a literal number or a
parenthesised sub-expression:

```lark
fn p_factor(tokens : List(Token)) : Result((Expr, List(Token)), String) =
  match tokens with
  | Cons(TNum(n), rest) => Ok((Lit(n), rest))
  | Cons(TLParen, rest) =>
    match p_expr(rest) with
    | Err(msg)       => Err(msg)
    | Ok((e, rest2)) =>
      match rest2 with
      | Cons(TRParen, rest3) => Ok((e, rest3))
      | _                    => Err("expected ')'")
      end
    end
  | _ => Err("expected number or '('")
  end
```

`p_factor` calls `p_expr`, and `p_expr` calls `p_term`, which calls
`p_factor` back. All five functions form a *mutually recursive* group. Lark's
type-checker handles this via a pre-pass that registers every annotated `fn`
declaration before checking any of their bodies, so forward references are
allowed. That is why every grammar function carries a full return-type
annotation: without the annotation the function would not be registered in
the pre-pass and forward calls would be rejected as unknown names.

**`p_term_tail`** handles `*` and `/` left-associatively by accumulating:

```lark
fn p_term_tail(lhs : Expr) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match tokens with
    | Cons(TStar, rest) =>
      match p_factor(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_term_tail(Mul(lhs, rhs))(rest2)
      end
    | Cons(TSlash, rest) =>
      match p_factor(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_term_tail(Div(lhs, rhs))(rest2)
      end
    | _ => Ok((lhs, tokens))
    end
```

On each recursive call the left-hand side grows: `lhs` starts as the first
factor, becomes `Mul(first, second)` on the next iteration, then
`Mul(Mul(first, second), third)`, and so on. The final `_` arm returns
the accumulated expression unchanged, ending the loop.

**`p_term`** sequences `p_factor` with `p_term_tail` without needing `pand`:

```lark
fn p_term(tokens : List(Token)) : Result((Expr, List(Token)), String) =
  match p_factor(tokens) with
  | Err(msg)        => Err(msg)
  | Ok((lhs, rest)) => p_term_tail(lhs)(rest)
  end
```

`p_factor(tokens)` is a direct call; `p_term_tail(lhs)` is also a direct
call that returns a closure; `(rest)` applies that closure to the remaining
tokens. Writing the sequencing explicitly here is cleaner than wrapping both
in lambdas for `pand`.

**`p_expr_tail`** mirrors `p_term_tail` for `+` and `-`:

```lark
fn p_expr_tail(lhs : Expr) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match tokens with
    | Cons(TPlus, rest) =>
      match p_term(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_expr_tail(Add(lhs, rhs))(rest2)
      end
    | Cons(TMinus, rest) =>
      match p_term(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_expr_tail(Sub(lhs, rhs))(rest2)
      end
    | _ => Ok((lhs, tokens))
    end
```

**`p_expr`** demonstrates `pand` with explicit lambda wrappers:

```lark
fn p_expr(tokens : List(Token)) : Result((Expr, List(Token)), String) =
  pand(
    fn(t : List(Token)) => p_term(t),
    fn(e : Expr)        => fn(t : List(Token)) => p_expr_tail(e)(t)
  )(tokens)
```

The first lambda wraps the static `p_term` call so the combinator gets a
proper closure. The second lambda is curried: `fn(e : Expr) => fn(t) => ...`
means "given a parsed term `e`, return a parser for the expression tail."
`pand` calls the first parser, and on success calls `f(e)` (outer lambda),
which in turn returns the inner lambda, which `pand` then calls on `rest`.

### IO stays outside the parser

None of the parser or evaluator functions touch `IO`. They are completely pure:
tokens in, result out. The `run` function assembles the output string:

```lark
fn run(tokens : List(Token)) : String =
  let src = show_toks(tokens) in
  match p_expr(tokens) with
  | Err(msg)   => src + "  =>  ERROR: " + msg
  | Ok((e, _)) => src + "  =>  " + pretty(e) + "  =  " + show(eval(e))
  end
```

`tokens` is used twice — for `show_toks` and for `p_expr` — which is why
`impl Copy for List(Token) = {}` is required. `main` threads IO through a
sequence of `print` calls, each consuming one output line:

```lark
fn main(io : IO) : IO =
  let t1 = Cons(TNum(1), Cons(TPlus, Cons(TNum(2), Cons(TStar, Cons(TNum(3), Nil))))) in
  ...
  let io = print(io, run(t1)) in
  ...
  print(io, run(t5))
```

The parser never decides whether to print or return — it always returns the
result, and the caller decides what to do with it. This separation of *pure
computation* from *effects* is the defining pattern of purely functional
programming.

### The complete program

Save as `samples/09_parser.lark` and run with `make tac_vm FILE=samples/09_parser.lark`.

```lark
module Parser

type Token =
  | TNum    of Int
  | TPlus
  | TMinus
  | TStar
  | TSlash
  | TLParen
  | TRParen

impl Copy for Token = {}

type List a =
  | Nil
  | Cons of a, List(a)

impl Copy for List(Token) = {}

type Expr =
  | Lit of Int
  | Add of Expr, Expr
  | Sub of Expr, Expr
  | Mul of Expr, Expr
  | Div of Expr, Expr

impl Copy for Expr = {}

type Result a b =
  | Ok  of a
  | Err of b

fn pand(
  p : List(Token) -> Result((Expr, List(Token)), String),
  f : Expr -> List(Token) -> Result((Expr, List(Token)), String)
) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match p(tokens) with
    | Err(msg)       => Err(msg)
    | Ok((e, rest))  => f(e)(rest)
    end

fn por(
  p : List(Token) -> Result((Expr, List(Token)), String),
  q : List(Token) -> Result((Expr, List(Token)), String)
) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match p(tokens) with
    | Ok(r)  => Ok(r)
    | Err(_) => q(tokens)
    end

fn p_factor(tokens : List(Token)) : Result((Expr, List(Token)), String) =
  match tokens with
  | Cons(TNum(n), rest) => Ok((Lit(n), rest))
  | Cons(TLParen, rest) =>
    match p_expr(rest) with
    | Err(msg)       => Err(msg)
    | Ok((e, rest2)) =>
      match rest2 with
      | Cons(TRParen, rest3) => Ok((e, rest3))
      | _                    => Err("expected ')'")
      end
    end
  | _ => Err("expected number or '('")
  end

fn p_term_tail(lhs : Expr) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match tokens with
    | Cons(TStar, rest) =>
      match p_factor(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_term_tail(Mul(lhs, rhs))(rest2)
      end
    | Cons(TSlash, rest) =>
      match p_factor(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_term_tail(Div(lhs, rhs))(rest2)
      end
    | _ => Ok((lhs, tokens))
    end

fn p_term(tokens : List(Token)) : Result((Expr, List(Token)), String) =
  match p_factor(tokens) with
  | Err(msg)        => Err(msg)
  | Ok((lhs, rest)) => p_term_tail(lhs)(rest)
  end

fn p_expr_tail(lhs : Expr) : List(Token) -> Result((Expr, List(Token)), String) =
  fn(tokens : List(Token)) =>
    match tokens with
    | Cons(TPlus, rest) =>
      match p_term(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_expr_tail(Add(lhs, rhs))(rest2)
      end
    | Cons(TMinus, rest) =>
      match p_term(rest) with
      | Err(msg)         => Err(msg)
      | Ok((rhs, rest2)) => p_expr_tail(Sub(lhs, rhs))(rest2)
      end
    | _ => Ok((lhs, tokens))
    end

fn p_expr(tokens : List(Token)) : Result((Expr, List(Token)), String) =
  pand(
    fn(t : List(Token)) => p_term(t),
    fn(e : Expr)        => fn(t : List(Token)) => p_expr_tail(e)(t)
  )(tokens)

fn eval(e : Expr) : Int =
  match e with
  | Lit(n)    => n
  | Add(a, b) => eval(a) + eval(b)
  | Sub(a, b) => eval(a) - eval(b)
  | Mul(a, b) => eval(a) * eval(b)
  | Div(a, b) => eval(a) / eval(b)
  end

fn pretty(e : Expr) : String =
  match e with
  | Lit(n)    => show(n)
  | Add(a, b) => "(" + pretty(a) + "+" + pretty(b) + ")"
  | Sub(a, b) => "(" + pretty(a) + "-" + pretty(b) + ")"
  | Mul(a, b) => "(" + pretty(a) + "*" + pretty(b) + ")"
  | Div(a, b) => "(" + pretty(a) + "/" + pretty(b) + ")"
  end

fn show_tok(t : Token) : String =
  match t with
  | TNum(n) => show(n)
  | TPlus   => "+"
  | TMinus  => "-"
  | TStar   => "*"
  | TSlash  => "/"
  | TLParen => "("
  | TRParen => ")"
  end

fn show_toks(ts : List(Token)) : String =
  match ts with
  | Nil           => ""
  | Cons(t, Nil)  => show_tok(t)
  | Cons(t, rest) => show_tok(t) + " " + show_toks(rest)
  end

fn run(tokens : List(Token)) : String =
  let src = show_toks(tokens) in
  match p_expr(tokens) with
  | Err(msg)   => src + "  =>  ERROR: " + msg
  | Ok((e, _)) => src + "  =>  " + pretty(e) + "  =  " + show(eval(e))
  end

fn main(io : IO) : IO =
  let t1 = Cons(TNum(1), Cons(TPlus, Cons(TNum(2), Cons(TStar, Cons(TNum(3), Nil))))) in
  let t2 = Cons(TLParen, Cons(TNum(1), Cons(TPlus, Cons(TNum(2),
             Cons(TRParen, Cons(TStar, Cons(TNum(3), Nil))))))) in
  let t3 = Cons(TNum(10), Cons(TMinus, Cons(TNum(3), Cons(TMinus, Cons(TNum(2), Nil))))) in
  let t4 = Cons(TNum(2), Cons(TStar, Cons(TLParen, Cons(TNum(3), Cons(TPlus,
             Cons(TNum(4), Cons(TRParen, Cons(TSlash, Cons(TNum(7), Nil))))))))) in
  let t5 = Cons(TLParen, Cons(TNum(1), Cons(TPlus, Nil))) in
  let io = print(io, run(t1)) in
  let io = print(io, run(t2)) in
  let io = print(io, run(t3)) in
  let io = print(io, run(t4)) in
  print(io, run(t5))
```

Output:

```
1 + 2 * 3  =>  (1+(2*3))  =  7
( 1 + 2 ) * 3  =>  ((1+2)*3)  =  9
10 - 3 - 2  =>  ((10-3)-2)  =  5
2 * ( 3 + 4 ) / 7  =>  ((2*(3+4))/7)  =  2
( 1 +  =>  ERROR: expected number or '('
```

The first two lines verify precedence (`*` binds tighter than `+`) and
parenthesised grouping. The third verifies left-associativity. The fourth
combines both. The fifth tests error recovery on a truncated input.

---

## 19. Summary Reference

```
program      ::= module Name decl*
decl         ::= fn Name[bounds](params) : Type = expr
              |  let name : Type = expr
              |  type Name vars = | Ctor [of Type, ...] | ...
              |  trait Name var = { fn method : Type }
              |  impl Trait for Type = { fn method(params) = expr }
              |  [export] decl
              |  import Name exposing (name, ...)

expr         ::= let name = expr in expr
              |  if expr then expr else expr
              |  match expr with | pat => expr ... end
              |  fn(params) => expr
              |  expr op expr
              |  not expr | -expr
              |  name(args)    (* function call *)
              |  Name(args)    (* constructor   *)
              |  (expr, expr)  (* tuple         *)
              |  literal | name | Name

pat          ::= _  |  name  |  literal
              |  Name(pat, ...)
              |  (pat, pat)

type         ::= Name | name | (type) | type -> type
              |  Name(type, ...) | (type, type)

bounds       ::= [ TraitName typevar, ... ]
```

The samples directory (`samples/`) contains nine complete programs:
`01_mergesort`, `02_bst`, `03_primes`, `04_queens`, `05_expr`, `06_rle`,
`07_hanoi`, `08_life`, and `09_parser`. Run them all with `make samples`.
