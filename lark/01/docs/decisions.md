
## Lark — Design Decisions

Rationale for every significant choice made in Phase 0 (language design) and
the lexer (Phase 2, first step). Each entry explains what was decided, what was
rejected, and why. These become the "Design Decision" sidebars in the book.

The parser decisions are in the next snapshot (`02/docs/decisions.md`).



### Language design

#### Delimiter-based syntax

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



#### Copy as a trait

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



#### Result type for errors

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



#### File-level modules

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



#### Affine IO via resource threading

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
(Koka's approach). Both are theoretically elegant. Monadic IO requires
`do`-notation as surface sugar over `bind` and `return`, and asks the reader
to understand monads before they can write a hello-world program. Algebraic
effects require a separate effect system layered on top of the type system.

Resource threading is the oldest and most direct approach — it is essentially
what Clean's uniqueness types enforce. In Lark's context it has a clear
advantage: it makes IO completely transparent. Every IO operation is a function
call that takes and returns the IO token. The type checker enforces the
sequencing by virtue of affinity alone. No special cases, no monads, no effect
rows.



### Lexer design

#### name / Name lexical convention

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



#### `()` as a single UNIT token

The unit value and type are both written `()`. The lexer produces a single
`UNIT` token when it sees `(` immediately followed by `)` (no whitespace
between them). `( )` with a space produces `LPAREN` then `RPAREN`, which the
parser handles as an empty argument list or grouping.

The alternative is to let the parser distinguish `()` from `( )` contextually.
This works but adds two extra production rules to the grammar. Treating `()` as
a lexical token keeps the grammar simpler and avoids any ambiguity.



#### Nested block comments

Comments are written `(* ... *)` and may be nested:
`(* outer (* inner *) still outer *)`. The lexer tracks comment depth with a
counter: `(*` increments, `*)` decrements, depth zero ends the comment.

Nested comments are not strictly necessary but are practically useful: you can
comment out a block of code that already contains comments without modification.
OCaml supports them for the same reason. The implementation cost is one integer
counter in the lexer.
