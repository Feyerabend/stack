# Lark — Design Decisions

Rationale for every significant choice made in Phase 0 (language design),
Phase 2 (lexer and parser), and Phase 3 (type checker). Each entry explains
what was decided, what was rejected, and why. These become the "Design
Decision" sidebars in the book.

The type checker decisions are at the bottom of this file.

---

## Language design

### Delimiter-based syntax

Lark uses `in` to close `let` and `end` to close `match`. There is no
indentation sensitivity.

The alternative — Python-style significant whitespace — is friendlier in small
programs. But it requires the lexer to emit synthetic INDENT and DEDENT tokens
and makes the grammar context-sensitive at the lexical level. The parser then
has to handle two kinds of "end of block": an explicit token and an inferred
one. Every error-recovery case doubles.

Delimiters keep the grammar LL(1) and the lexer stateless. A reader can follow
the grammar and the parser side by side without any special cases. The
trade-off is slightly more typing for the programmer; the gain is a grammar you
can hold in your head.

---

### Copy as a trait

All Lark types are affine by default: a value may be used at most once. A type
opts into free copying by implementing the `Copy` marker trait. Built-in types
(`Int`, `Float`, `Bool`, `String`) implement `Copy`. User-defined types do not
unless the programmer writes `impl Copy for T = {}`.

The alternative is "purity as default": pure algebraic values are always freely
copyable, and only types explicitly declared as resources are affine. This is
more permissive and would make most programs less annotated. But it requires a
separate "resource type" declaration mechanism, and the type checker must carry
two flags (is it pure? is it a resource?) rather than one (does it implement
`Copy`?).

Rust's experience with opt-in `Copy` is the deciding precedent. Resources are
safe by default; the programmer explicitly opts data types into copyability.
`IO` has no `Copy` impl — which is not a special case, just the ordinary
consequence of the rule.

---

### Result type for errors

`type Result a b = | Ok of a | Err of b`. Errors are values, handled by pattern
matching. There are no exceptions.

Exceptions break referential transparency: a function that might throw is
indistinguishable in its type from one that cannot. They also complicate the
CEK machine semantics considerably — exception handling requires a special
continuation frame and a mechanism for unwinding the stack.

`Result` makes errors visible in types. The caller must pattern-match on the
result; it cannot ignore the error case without explicit effort. The trade-off
is verbosity: propagating errors through several function calls requires
threading `Result` values explicitly. A `?` operator (like Rust's) could be
added as surface sugar later; for now the verbosity is pedagogically useful
because it makes every error-handling decision visible.

---

### File-level modules

Each `.lark` file is a module. `module Name` declares the module. `export`
makes a declaration public. `import Name exposing (x, y)` brings names into
scope.

The alternative of having no module system — all standard library definitions
in global scope — works for tiny programs but gives readers no model for
organizing larger ones. The book builds a complete language; the language should
be organizable.

OCaml's first-class module system (functors, module types) is more powerful
but significantly more complex to implement and explain. Lark uses traits for
structured polymorphism instead, which covers most of what OCaml uses modules
for. A file-level module system is the minimum needed for code organization
without the full OCaml complexity.

---

### Affine IO via resource threading

`IO` is a resource type. IO operations take the IO resource and return it:

```
fn print(io : IO, s : String) : IO = ...
fn read(io : IO) : (IO, String) = ...
```

The programmer threads the IO resource explicitly through every IO operation.
Since `IO` has no `Copy` impl, the type checker ensures you cannot use the
same IO token twice — which means you cannot have two interleaved threads of IO
without explicit sequencing.

The main alternatives are monadic IO (Haskell's approach) and algebraic effects
(Koka's approach). Both are theoretically elegant. Monadic IO requires `do`-
notation as surface sugar over `bind` and `return`, and asks the reader to
understand monads before they can write a hello-world program. Algebraic effects
require a separate effect system layered on top of the type system.

Resource threading is the oldest and most direct approach — it is essentially
what Clean's uniqueness types enforce. In Lark's context it has a clear
advantage: it makes IO completely transparent. Every IO operation is a function
call that takes and returns the IO token. The type checker enforces the sequencing
by virtue of affinity alone. No special cases, no monads, no effect rows.

---

## Lexer design

### name / Name lexical convention

Identifiers starting with a lowercase letter (`name`) are variables, function
names, and type variables. Identifiers starting with an uppercase letter
(`Name`) are types, constructors, and module names. The standalone `_` is a
WILDCARD token; identifiers may not start with `_`.

This convention is borrowed from ML and Haskell. Its primary benefit is in
pattern matching: in `match e with | Nil => ... | Cons(x, rest) => ...`, the
lexer tells the parser immediately that `Nil` and `Cons` are constructors and
`x` and `rest` are binders. The parser needs no symbol table to parse a pattern.

The alternative — a single identifier class, distinguished by context — forces
the parser to carry type information into pattern parsing, or to perform a
post-parse disambiguation pass. Both are possible; neither is as simple as a
lexical rule.

---

### `()` as a single UNIT token

The unit value and type are both written `()`. The lexer produces a single
`UNIT` token when it sees `(` immediately followed by `)` (no whitespace
between them). `( )` with a space produces `LPAREN` then `RPAREN`, which the
parser handles as an empty argument list or grouping.

The alternative is to let the parser distinguish `()` from `( )` contextually.
This works but adds two extra production rules to the grammar. Treating `()` as
a lexical token keeps the grammar simpler and avoids any ambiguity.

---

### Nested block comments

Comments are written `(* ... *)` and may be nested:
`(* outer (* inner *) still outer *)`. The lexer tracks comment depth with a
counter: `(*` increments, `*)` decrements, depth zero ends the comment.

Nested comments are not strictly necessary but are practically useful: you can
comment out a block of code that already contains comments without modification.
OCaml supports them for the same reason. The implementation cost is one integer
counter in the lexer.

---

## Parser design

### Hand-written recursive descent

The Lark parser is a hand-written recursive descent parser. One function per
grammar rule. No parser generator, no combinator library.

Parser generators (ANTLR, PLY) produce correct parsers quickly but generate
opaque code. A reader cannot follow the connection from a grammar rule to the
code that handles it. The book's purpose is to show how languages are built;
the parser must be as readable as the grammar.

Parser combinators are composable but add a dependency and hide the structure
behind a combinator API. The resulting code is more abstract than the grammar
it implements.

Recursive descent is the oldest and most direct approach. Each grammar rule
becomes a method. The call stack is the parse stack. The code is longer than
a parser generator output but completely transparent. A reader who understands
the grammar can read the parser function by function and see exactly what
happens for each token.

One limitation: recursive descent as written here does not handle left-recursive
grammars directly. Lark's grammar is designed to avoid left recursion; operator
expressions use the level-chain pattern described below.

---

### Operator precedence via level-chain

Binary operator precedence is encoded as a chain of five functions:

```
_parse_or  →  _parse_and  →  _parse_compare  →  _parse_add  →  _parse_mul
```

Each function loops on its own operators and calls the next function for
operands. This makes `*` bind tighter than `+` because `_parse_mul` is called
by `_parse_add` — the tighter binding is a consequence of the call graph.

The alternative is a Pratt parser (top-down operator precedence), which handles
any number of precedence levels in a single function driven by a precedence
table. Pratt parsers are compact and elegant for languages with many operators.
Lark has five precedence levels; the level-chain approach is simpler to explain
and equally correct. Adding a new level means adding one function; the structure
remains obvious.

---

### Separate syntactic and typed AST

The parser produces a syntactic AST (`tree.py`). The type checker will produce
a separate typed AST (`typed_tree.py`, Phase 3). They are distinct data
structures that do not share node types.

A single AST with optional type annotations — the simpler initial design —
requires the type checker to either mutate the tree (problematic with frozen
dataclasses) or carry a parallel map from node to type. Either approach makes
the phase boundary invisible in the code and harder to test in isolation.

Separate trees make the boundary explicit: the parser's output is complete and
correct without any type information. The type checker takes a syntactic program
and produces a typed one. Each phase can be tested independently.

---

### `_` in parameter position

The grammar defines `_` as a WILDCARD pattern token. The parser also accepts
it in function parameter position (`fn(acc, _) => ...`), producing a `Param`
with name `"_"`.

This is a small pragmatic extension to the grammar — technically `_` is not
a valid `name` (names must start with lowercase). But every functional language
that has a wildcard pattern also allows it in lambda parameters, and forbidding
it would produce confusing errors on natural code. The type checker can treat
`_` parameters as anonymous bindings that are never referenced.

---

## Type checker design

### Hindley-Milner with bidirectional checking

The Lark type checker implements Algorithm W (Hindley-Milner inference) with a
bidirectional structure borrowed from the proof/ reference implementation.
Every expression is either inferred (the type is synthesised from the term) or
checked (the type flows in from context). In practice, the top-level functions
are inferred; type annotations on parameters and return types are unified with
the inferred types.

The alternative — a constraint-based solver (Algorithm J, or a Damas-Milner
with explicit constraint propagation) — is more efficient on large programs but
harder to explain. The per-node substitution threading in Algorithm W makes the
flow of type information visible: every `infer` call returns a substitution, and
composing substitutions is the only mechanism by which type information propagates.

The bidirectional element is important for affine types: when a parameter is
annotated with `IO`, that annotation flows in and the parameter is immediately
marked as affine in the tracked set. Without bidirectional propagation we would
have to wait until unification to discover the parameter's type.

---

### Separate internal type representation (`ty.py`)

The type checker uses its own type representation (`ty.py`) distinct from the
surface types in `tree.py`. Internal types use integer-identified type variables
(`TVar(id=3)`) rather than string names (`TName("a")`). Type constructors
(`TCon`, `TApp`, `TFn`, `TTup`) match the surface types structurally but are
not the same classes.

The alternative — reusing `tree.py` types — would avoid the conversion step but
requires unification to operate on types that were designed for readability, not
inference. String-named type variables make occurs-check bookkeeping harder and
require careful scoping to avoid name collisions between user type variables in
different function signatures.

Integer-identified type variables are the standard approach in every Haskell
implementation of HM. The conversion from surface type to internal type is a
single function (`syntype_to_mono`) and the boundary is explicit.

---

### Affine tracking via an explicit tracked set

The checker does not attempt to check affinity for every non-Copy type. Instead
it maintains a `tracked` set: names of locally-bound parameters whose annotation
type is concretely non-Copy at bind time. Only variables in `tracked` are subject
to the use-count check; global names (builtins, top-level functions) are never
tracked.

The alternative — tracking all variables by type, checking is-copy eagerly
during inference — produced false positives. Pattern-bound variables (like `r`
in `| Circle(r) =>`) start with unknown types that resolve to `Float` (Copy)
only after unification. Checking before unification flagged `r * r` as an
affine violation.

The `tracked` set is pre-populated with parameters whose annotations are
concretely non-Copy (e.g., `io : IO`). When a `let` binding shadows a tracked
name, the old tracking entry is removed (the old value is consumed) and a new
one is added only if the new value's type is non-Copy. This handles the
IO-threading pattern: each successive `let io = print(io, ...) in` correctly
consumes the old token and tracks the new one.

---

### Function types are Copy

Function values (type `TFn`) are treated as freely copyable. A function can be
referenced any number of times without being "consumed."

The alternative — making closures affine if they capture a non-Copy value —
would be correct in theory but requires closure analysis (which captured
variables does each function reference?). Phase 3 does not perform closure
analysis.

The practical justification: in Lark's purely functional fragment, functions
do not own resources. The IO resource is threaded explicitly through function
arguments, not captured. A function like `f : Int -> Int -> Int` applied twice
to the same `f` parameter is safe and common — `fold(f, f(acc, x), rest)`.
Making function types non-Copy would force every higher-order function to thread
function values through a chain of let-bindings, which is both impractical and
unsupported by the type theory we are building toward.

---

### Let-recursion via a fresh type variable

Each function declaration adds its own name to the local environment with a
fresh type variable before type-checking the body. After the body is checked,
the fresh variable is unified with the inferred function type. This is the
standard let-rec extension to Algorithm W.

The alternative — forbidding direct recursion — would make the language far
less useful and would require a dedicated `letrec` construct at the surface
level. Every practical functional language supports recursion; the let-rec
extension is minimal.

The current implementation handles direct recursion correctly. Mutual recursion
across top-level declarations is handled by the two-pass architecture: all
types are registered before any function body is checked.

---

### ADT constructor types

Each variant of an ADT becomes a function in the type environment. A nullary
constructor `| Nil` gets the type of the ADT directly. A unary constructor
`| Circle of Float` gets type `Float -> Shape`. A multi-field constructor
`| Cons of a, List(a)` gets a curried type `a -> List(a) -> List(a)`.

This is the standard ML encoding. It means constructors are ordinary values
and can be passed as higher-order functions. Pattern matching deconstructs
them; the constructor function constructs them.

The `Variant.payload` field was changed from `Type | None` (where `None` meant
nullary and `TTuple` meant multi-field) to `tuple[Type, ...]` (empty = nullary,
one element = unary, multiple = curried multi-field). The old representation
was ambiguous: `| Box of (Float, Float)` (one tuple field) looked the same
as `| Rect of Float, Float` (two separate fields). The tuple representation
makes the distinction structural.
