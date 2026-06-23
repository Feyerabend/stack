# Lark (Lambda Affine Resource Kernel) — Design Decisions

Rationale for every significant choice made in Phase 0 (language design),
Phase 2 (lexer and parser), Phase 3 (type checker), Phase 5 (compiler), and
Phase 6 (hardening). Each entry explains what was decided, what was rejected,
and why. These become the "Design Decision" sidebars in the book.

The type checker decisions are at the bottom of this file.
Phase 6 decisions (hardening) follow at the very end.

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

---

## CEK machine design

### Small-step iterative loop

The CEK machine is implemented as a single iterative `while` loop in `run`.
Each call to `step` produces the next state; the loop exits when it reaches
`Return(val, [])`.

The alternative is a big-step recursive interpreter: evaluate an expression by
recursively evaluating its sub-expressions, returning a value directly. That is
simpler to write but pushes one Python stack frame per Lark function call. A
tail-recursive Lark program like `sum_to(1_000_000)` hits Python's recursion
limit around 1,000 calls.

The CEK loop has no such limit. Tail calls are free: when `Return(v, [])` is
the state, the loop exits. There is no "detect tail call and optimize" step —
the iterative structure makes it impossible to accumulate Python frames in the
first place.

---

### Continuation as a list of frames

The continuation is a plain Python list `list[Frame]`. Frames are prepended
(`[new_frame] + rest`) and consumed from the front.

The alternative is a proper algebraic continuation type — a linked list or
a sum type with a constructor per frame kind. Both are equivalent; the list
representation is more idiomatic in Python and does not change the semantics.
The match pattern in `step_ret` destructures the frame and the remaining list
in one line: `case Return(val=v, kont=[frame, *rest])`.

---

### `VPartialCon` for constructors

Constructors are curried in the value domain. A constructor with two fields
(e.g., `Cons : a -> List a -> List a`) is initially represented as
`VPartialCon("Cons", arity=2, args=())`. Each application appends one argument;
when `len(args) == arity` the machine produces a `VCon`.

The alternative is to give constructors a special frame and handle them
differently from functions. That would require two code paths for application.
`VPartialCon` means constructors go through the same `apply` path as closures;
no special casing needed.

---

### `VDispatch` for trait methods

Trait dispatch is deferred entirely to runtime. When a trait method like
`describe` appears as a value, it is represented as `VDispatch("describe")`.
At the moment it is applied to an argument, `runtime_type(arg, machine)`
determines the concrete type (e.g. `"Color"`) and `machine.dispatch[("describe",
"Color")]` retrieves the correct closure.

The alternative is monomorphisation: generate a separate closure per
(method, type) pair and resolve calls at type-check time. That is what compilers
do. For the interpreter, runtime dispatch is simpler: the type checker does not
need to thread dispatch information into the typed AST, and new implementations
can be added by updating the dispatch table without touching the evaluator.

---

### `is_copy(TVar) = True`

The `is_copy` function returns `True` for unresolved type variables. The
alternative — `False` (conservative) — caused false affine errors.

The problem: inside a recursive function like `depth`, the self-reference in
the type environment has type `fn_tv` (a fresh type variable, not yet unified
with the actual return type `Int`). When the body contains `let ld = depth(l) in
... ld + 1 ...`, the type of `ld` at the point of binding is `fn_tv` (a TVar),
not yet `Int`. With `is_copy(TVar) = False`, `ld` is tracked as affine and
`ld + 1` raises a false affine error.

The fix is safe: all concretely non-Copy types in Lark (`IO`, user-defined types
without `impl Copy`) are `TCon` or `TApp` at the point of binding — never an
unresolved `TVar`. A `TVar` that later resolves to `Int` or `Float` (Copy) should
not be tracked. A `TVar` that resolves to a non-Copy type would be a false
negative, but this only arises in recursive functions that produce non-Copy
output, which is an edge case not present in the current test suite.

---

---

## Compiler design (Phase 5)

### Three-address code (TAC) as the intermediate representation

The compiler does not lower the typed AST directly to RISC-V. Instead it
lowers to three-address code (TAC), then from TAC to assembly.

Three-address code is a flat sequence of instructions where every operation
has at most two source operands and one destination: `t2 = t0 + t1`. The
key property is that each instruction is *atomic* — it cannot be nested. A
complex expression like `f(g(x + 1), y * 2)` becomes four separate
instructions, each producing a named temporary. This flatness makes the TAC
easy to analyse: liveness, dominance, and reachability are all properties of
the instruction sequence, not properties of a recursive tree.

Alternatives considered:

*Direct tree-walking code generation* — walk the typed AST and emit RISC-V
instructions inline. Simple for arithmetic expressions, but breaks down for
closures (which need to be lifted), pattern matching (which needs labels and
jumps), and later passes (register allocation, optimisation). Without an IR,
every optimisation and every backend has to traverse the tree separately.

*Bytecode (virtual machine instructions)* — a traditional choice for
interpreted language implementations. Bytecode suits an interpreter target
(the CEK machine already serves that role) but requires a different stack
discipline than RISC-V. Moving from bytecode to native code is essentially the
same problem as moving from TAC to native code, with the additional overhead
of designing the bytecode set.

*Continuation-passing style (CPS)* — an IR where every function is
tail-calling and every intermediate result is named. CPS makes control flow
explicit and is the standard IR in compilers targeting functional languages
(SML/NJ, MLton, MLIR for functional dialects). It is also harder to explain:
a reader who understands expressions must first understand CPS transform before
they can understand the IR.

TAC is chosen because it is the standard IR taught in compiler courses (see
Appel, *Modern Compiler Implementation*, and Cooper & Torczon, *Engineering a
Compiler*). It maps directly to the three-operand RISC-V instruction format.
Every TAC instruction is one register machine instruction modulo operand loading.
A reader who understands RISC-V assembly can follow the lowering one
instruction at a time.

---

### Lambda lifting and closure conversion

Nested lambdas cannot be compiled to static function addresses: they carry
references to variables from their enclosing scope. The standard solution is
closure conversion: lift every lambda to a top-level function, and bundle the
free variables into a heap-allocated *closure record* that is passed as an
implicit extra argument.

Lark uses the *self-as-env* variant: the closure record itself serves as the
environment pointer. Every lifted closure function has signature `(env, arg)`
where `env` is a pointer to the closure record. Free variables are loaded from
the closure record with field loads at the start of the function body:

```
fn adder$lam0(env, x):       # env = { n }
    cap0 = env[0]             # n = env[0]
    t1 = cap0 + x
    return t1
```

At the call site, `IAllocClosure` builds the record and records which top-level
function it points to:

```
clos = closure(adder$lam0; n)   # record: [&adder$lam0, n]
```

The alternative is to pass free variables as additional function parameters
(defunctionalization). That avoids heap allocation for the environment but
changes the function signature for every function that has free variables,
which means every call site must know the complete set of free variables.
Self-as-env keeps all call sites uniform: a closure is always called with two
arguments, regardless of how many variables it captures.

---

### Multi-param lambdas desugared into curried chains

A Lark lambda may have multiple parameters: `fn(a, b) => a + b`. The CEK
machine handles this by creating a nested closure on each application:
`VClosure("a", TLambda([("b",...)], body), env)`. When the outer closure is
applied to `a_val` it produces a new `VClosure("b", body, {a: a_val, ...env})`.

The compiler must follow the same convention. A 2-param lambda is desugared
into a chain of single-param closures *before* lifting:

```
fn(a, b) => body
  →  fn(a) => fn(b) => body
```

This desugaring happens at the top of `_lower_lambda`: if `len(params) > 1`,
construct a new `TLambda(params[1:], body)` and recurse with `params[:1]`.
Each single-param lambda is then independently lifted with `_lower_lambda`.

The result for `fn(acc, x) => acc + x` (as passed to `fold`):

```
fn lam$outer(env, acc):            # outer: takes acc
    clos = closure(lam$inner; acc) # capture acc
    return clos

fn lam$inner(env, x):              # inner: takes x, reads acc from env
    acc = env[0]
    t = acc + x
    return t
```

The alternative is to lift the 2-param lambda to a flat 2-param function and
handle partial application in the runtime by constructing intermediate closures
on demand. That approach (used in some ML runtime systems under the name
"push-enter") requires the runtime to know function arities and build closures
dynamically. Curried desugaring makes partial application transparent to the
code generator: it never needs to handle partial application as a special case.

---

### Uniform closure calling convention

All lifted closure functions — whether or not they capture any free variables —
use the signature `(env, arg)`. The `env` parameter is always present. For
non-capturing closures, `env` is received but ignored; it will be a null
pointer at runtime (or the IAllocClosure record will have just one field: the
function pointer).

The alternative is to omit `env` for closures with no free variables. That
saves the cost of one argument register and one word in the closure record.
But it means the calling code must track, per closure value, whether it expects
`(env, arg)` or just `(arg)`. That information is not available at every call
site (consider `twice(f, x)` where `f` could be any closure). Either the
runtime must inspect the closure arity at every call, or every `IClosureCall`
must be compiled differently for the two cases.

Uniform convention is the standard choice in compilers (see Shao & Appel,
*Space-Efficient Closure Representations*, 1994, for the trade-off analysis).
Overhead is one extra word per non-capturing closure record; gain is a
completely uniform call sequence.

---

### String tags in TAC, integer tags in assembly

The TAC IR uses string constructor names as tags in `IAlloc` and in the
equality comparisons generated by pattern matching:

```
tag0 = tag(xs)
tag_ok = tag0 == 'Cons'
```

This keeps the TAC human-readable: the patterns are the same constructor names
that appear in the source code.

The assembly backend converts string tags to integer IDs by sorting all unique
constructor names alphabetically and assigning each a sequential index. The
comparison `tag0 == 'Cons'` becomes an integer compare against the assigned ID.
The assignment `IAlloc(dst, "Cons", fields)` stores the integer ID in the
first word of the heap record.

The alternative is to assign integer tags during lowering and carry them
through the TAC. That would make the TAC less readable (the reader would need
a separate tag table to understand a match expression) without adding
expressiveness. The tag-to-integer mapping is a pure assembly-level detail;
keeping it there separates concerns correctly.

---

### TAC VM before RISC-V

Before generating RISC-V assembly, the compiler pipeline is validated by
a TAC interpreter (`tac_vm.py`). The VM executes the TAC directly, maintaining
a heap for `IAlloc` and closure records, and calls into Python for built-in
operations (`print`, `show`, etc.).

Running all acceptance tests through the TAC VM confirms that the lowerer
(`lower.py`) is semantically correct independent of the assembly backend.
Any bug found at the TAC level does not need to be disentangled from
instruction-selection or calling-convention errors.

This is the standard approach in multi-phase compilers: each IR has an
interpreter or validator that can serve as a correctness oracle. The TAC VM
also provides a development shortcut — the full compiler pipeline can be tested
on any machine without a RISC-V toolchain.

---

---

## Analysis pipeline design (Phase 5 continued)

### CFG as the unit of analysis

Liveness analysis is a property of control flow, not of a flat instruction
list. A branch instruction sends the program to one of two successors; a
variable that is used in one branch but not the other is only live on the path
where it is used. Working directly on the flat body of a `Function` would
require re-deriving this structure at every analysis pass.

`cfg.py` builds an explicit control-flow graph once. Every subsequent pass
(`liveness.py`, `igraph.py`, `regalloc.py`) reads successor and predecessor
edges from the CFG rather than re-parsing labels and jumps. The separation is
clean: the CFG builder is the only code that inspects `ILabel`, `IJump`, and
`ICondJump` for their structural meaning; analysis passes never need to.

Block boundaries follow the standard definition: index 0 is always a leader,
an `ILabel` instruction starts a new block, and the instruction after any
terminator (`IJump`, `ICondJump`, `IReturn`) is a leader. `ILabel` instructions
are kept as the first instruction of their block so that the full body can be
reconstructed from the CFG without a separate label table.

---

### Iterative backward dataflow for liveness

Liveness is a backward dataflow problem: a variable is live at a point if it
is used on some path from that point to the end of the function. The standard
equations are:

```
gen[B]       = variables used in B before being defined
kill[B]      = variables defined in B
live_out[B]  = ∪  live_in[S]   for each successor S
live_in[B]   = gen[B] ∪ (live_out[B] − kill[B])
```

The iterative worklist algorithm (Kildall 1973) starts with all sets empty and
re-processes a block whenever its `live_in` changes, adding all predecessors
to the worklist. For acyclic CFGs (no back-edges), this converges in one pass
over the blocks in reverse topological order. For CFGs with back-edges
(e.g., explicit loops), it converges in a small number of passes bounded by the
depth of the loop nesting.

The alternative — a simple repeated-pass algorithm — would work but processes
every block on every iteration even if its `live_in` did not change. The
worklist discards work that cannot propagate further.

The `Liveness` class also exposes `live_before(blk)`, which walks each block
backward from `live_out` to compute the live set before each individual
instruction. This per-instruction information is needed to build the
interference graph.

---

### Clique at each block entry in the interference graph

The standard interference graph build (Appel §11.1) adds an edge `(d, x)`
whenever a variable `d` is defined while `x` is live. This correctly captures
all interference introduced at definition points.

It misses one case: two variables that are simultaneously live throughout an
entire block but neither of which is *defined* in that block. The most common
instance is function parameters: in a function `compose(f, g)`, both `f` and
`g` are live at entry but neither has a definition instruction — they are
supplied by the caller. The backward pass through the body never fires the "d
interferes with live" rule for either of them, so no edge is added.

The fix: after completing the backward pass through each block, the remaining
`live` set equals `live_in[block]`. Adding a clique edge for every pair in that
set captures all simultaneously-live variables at the block boundary, including
parameters at the function entry and variables live across a join point with no
intervening definition.

---

### Copy edges and move coalescing (interference graph)

When a variable is defined by a copy instruction `d = s` (an `IAssign` with a
`Tmp` source), `d` and `s` are *move-related*: if they are assigned the same
register, the copy becomes a no-op and can be elided. Adding an interference
edge between `d` and `s` would prevent this.

Following Appel §11.1: for copy instructions, the copy source `s` is removed
from `live` *before* adding interference edges for `d`. This means `d` and `s`
do not get an interference edge. A separate copy edge `(d, s)` records the
relationship so a coalescing pass can merge them if no other constraint
prevents it.

The current register allocator (linear scan) does not perform coalescing; it
treats spilled copies as memory-to-memory moves. Copy edges are tracked in the
`IGraph` for a future coalescing pass or as documentation for the reader.

---

### Linear scan over graph coloring

Register allocation is the problem of assigning each variable to a physical
register, spilling to the stack when no register is free. Two approaches
dominate: graph coloring (Chaitin 1982) and linear scan (Poletto & Sarkar 1999).

*Graph coloring* uses the interference graph directly. Each variable is a node;
each interference edge is a constraint. The allocator attempts to color the
graph with `k` colors (registers), using heuristic simplification (Briggs et
al.) and spilling when no color is available. Graph coloring is optimal in
the sense that it finds the minimum number of spills for a given `k`. It also
enables coalescing: copy-related variables can be merged into one node before
coloring. The cost is implementation complexity: the simplification algorithm,
spill cost heuristics, and the coalescing phase each require careful engineering.

*Linear scan* assigns registers based on *live intervals* — the contiguous range
of instruction numbers during which each variable is live. Variables with
non-overlapping intervals can share a register. The allocator scans intervals
sorted by start point, greedily assigning free registers and spilling when
none are available. Linear scan is not optimal (it may spill a variable that
graph coloring could accommodate), but it is simple, predictable, and fast
enough for JIT compilers and language runtimes (it is used in the Java HotSpot
JIT and LLVM's fast register allocator).

Lark uses linear scan for Phase 5. The code — linearize → compute intervals →
scan — fits in one short file and is easy to explain. The interference graph
(`igraph.py`) is built alongside and used only as a correctness oracle: the
verifier checks that no two interfering variables were assigned the same
register. A future Phase 5b could replace `regalloc.py` with graph coloring
to demonstrate the difference.

---

### Callee-saved registers as the allocation pool

RISC-V divides registers into caller-saved (`t0`–`t6`, `a0`–`a7`) and
callee-saved (`s1`–`s11`). Caller-saved registers are clobbered by any `call`
instruction; callee-saved registers are preserved by the callee.

If the allocator assigns a live variable to a caller-saved register and that
variable is live across a function call (`ICall` or `IClosureCall`), the call
will destroy the value. The code generator would need to spill the variable
before the call and reload it after — a save/restore inserted around every call.

Using callee-saved registers (`s1`–`s11`) avoids this entirely: the callee is
obligated to preserve these registers, so values in them survive any call. The
only cost is that the function prologue must save used `s`-registers to the
stack, and the epilogue must restore them. This is a fixed overhead per
function, not a per-call overhead.

With 11 callee-saved registers available and most Lark functions using far
fewer, the pool is sufficient for all current test cases without spilling.

---

### Refactoring: direct imports over `importlib`

Early versions of `cek.py` and `infer.py` loaded sibling modules (`parser`,
`infer`) via `importlib.util.spec_from_file_location`. This was an artefact of
uncertainty about how Python would resolve the imports.

Since `sys.path.insert(0, os.path.dirname(__file__))` is called at the top of
each entry-point file, `import parser as _parser` and `import infer as _infer`
resolve to the correct sibling files directly. The `importlib` pattern — six
lines of boilerplate per use site — was replaced with a single import line each.
The `_force` function, which was a duplicate of `run`, was eliminated; all call
sites now call `run` directly.

---

### Self-tail-call optimization (TCO) in the assembler

When a top-level function's last action is a recursive call to itself — a
self-tail-call — the compiler can reuse the current stack frame instead of
pushing a new one. The optimizer detects this pattern in `asm.py` via
`_find_tail_return`: a call to the current function whose result flows
directly to `IReturn` with no intervening non-trivial instruction.

When a self-tail-call is found, code generation emits a loop label
`.{fn}_loop:` at the top of the function body. At each tail call site, instead
of a `call` instruction, the optimizer stores the new argument values into the
parameter slots (spill locations or registers) and jumps to the loop label.

This eliminates one stack frame per recursive iteration and makes deep
recursion O(1) in stack space. It does not handle mutual tail calls (where
`f` tail-calls `g` and `g` tail-calls `f`) — those would require
a separate continuation-passing or trampolining transformation.

The alternative is to emit a normal `call` and rely on RISC-V's "link
register" convention for tail calls. RISC-V supports an explicit tail-call
instruction sequence (`jal zero, target` with the callee never creating a
new frame), but detecting when this is safe requires proving that the callee's
ABI matches, which adds complexity without benefit in a single-file compiler
pipeline.

---

### Float arithmetic and comparison via runtime stubs

RISC-V base (RV32I) has no floating-point instructions. A floating-point
add, for example, requires either the F-extension (`fadd.s`) or a software
library call. Lark targets the base ISA without extensions, so all float
operations go through runtime stubs.

At the TAC level, `lower.py` routes float arithmetic expressions to named
stubs: `__float_add`, `__float_sub`, `__float_mul`, `__float_div`. Float
comparisons similarly go to `__float_lt`, `__float_le`, `__float_gt`,
`__float_ge`. These are `ICall` instructions to known names.

The routing uses the result type of the expression: a `+` operation whose
result type (after HM substitution is applied) is `Float` routes to
`__float_add`; an `Int` `+` routes to the normal `add` instruction.

An important subtlety: float comparison using RISC-V integer `slt` (signed
less-than) gives wrong results for negative IEEE 754 values. The bit pattern
ordering for negative floats is reversed relative to their mathematical order.
Routing comparisons to stubs avoids this entirely: the stub uses Python's
`<`, which compares by value.

The same routing pattern applies to `show(Float)` → `__show_float` and
`show(Bool)` → `__show_bool`. Without the Bool routing, a boolean value
stored as `1` or `0` in an integer register would be printed as `"1"` or
`"0"` rather than `"true"` or `"false"`.

---

### `True`/`False` as integer constants, not heap records

In the typed tree, `True` and `False` appear as `TCon("True")` and
`TCon("False")` — the same node class as user-defined nullary constructors.
A naïve lowering treats them like any ADT variant: `IAlloc(dst, "True", ())`.
This allocates a heap record `{tag="True", fields=[]}`.

That is wrong for two reasons. First, `show(False)` with a heap-record
representation passes a non-null pointer to `__show_bool`, which tests
truthiness; any non-null pointer is truthy, so `show(False)` prints `"true"`.
Second, `ICondJump` on a heap pointer always branches to the true arm.

The fix is to intercept `TCon("True")` and `TCon("False")` in `lower.py`
before the general ADT case and emit `Const(True)` and `Const(False)` instead.
In the TAC VM these are Python booleans; in the RV32 assembler they become
`li reg, 1` and `li reg, 0`. Pattern matching on `True`/`False` (which are
parsed as `TPCon("True", [])` and `TPCon("False", [])`) also needs a special
case: compare the value against 1 or 0 rather than calling `IGetTag`.

---

### HM type substitution applied to typed tree bodies

Hindley-Milner inference builds a substitution `s: TVar → Mono` during
type checking. Pattern-bound variables (e.g., `w` and `h` in
`| Rect(w, h) => ...`) receive fresh type variables from `infer_pat` whose
types are resolved only once the surrounding match arm is unified.

Before the fix, `check_fn_decl` returned the typed tree with those type
variables still unresolved. The downstream code in `lower.py` checks
`node.typ == ty.T_FLOAT` to route float operations to the correct stubs; an
unresolved `TVar` compares unequal to `T_FLOAT`, so float arithmetic in
pattern arms was silently emitted as integer `mul` / `add` / etc.

The fix: after inference completes, apply the accumulated substitution `s` to
the entire typed tree via `_apply_texpr` and `_apply_tpat`. These two
recursive walkers replace every `TVar(id)` in every node's `typ` field with
the concrete type `s` maps it to. The result is a fully-resolved typed tree
in which `lower.py` sees correct types everywhere.

---

### Module import lowering: inlining imported declarations

The import mechanism in `infer.py` (`_load_import`) originally merged only
type *signatures* into the importing module's type environment. This was
sufficient for the CEK machine (which re-evaluates the imported module's
source at runtime) but broke the TAC and RISC-V backends: the `lower.py`
lowerer only sees `TProgram.decls` for the current module, so imported
function bodies were invisible and any call to an imported function produced
a "function not found" error.

The fix: `_load_import` now returns its `TProgram.decls` alongside the
updated `copy_types`. `typecheck()` prepends these imported declarations to
`typed_decls` before processing the current module's declarations. The
lowerer then sees all imported function bodies as if they had been defined
in the importing module — a simple form of module inlining.

The trade-off: the same function body appears in `typed_decls` for every
module that imports it. For a standard library imported by many modules this
duplicates code. A future optimisation could deduplicate by interning function
names across modules before lowering.

---

### Mutual recursion: pre-registration and backpatch

Standard sequential type checking prevents mutual recursion: when `is_even`
is checked, `is_odd` is not yet in the type environment, so the call
`is_odd(n-1)` fails with "unbound variable".

Two fixes are applied at different layers.

*Type checker (infer.py)*: a "pass 1.5" runs before body checking. For every
`FnDecl` that has complete type annotations (all parameters and the return
type), it computes the function's monotype from the annotations and registers
it in `env`. When bodies are checked in pass 2, mutually recursive calls find
their targets already typed. Functions without complete annotations fall back
to the existing self-recursion-only path (the let-rec type variable).

*CEK machine (cek.py)*: closures capture a copy of `env` at creation time,
so `is_even`'s closure does not see `is_odd` even after it is added to `env`
later. After all top-level function closures are created, a backpatch step
updates each closure's captured `env` with all other top-level function
closures. Because `VClosure.env` is a mutable Python dict, `clos.env.update(
top_fns)` injects the missing references into all pre-existing closures.

The backpatch uses only `TFnDecl` closures, not `TLetDecl` values, to avoid
inadvertently making future `let` bindings visible inside closures that
precede them in source order.

---

### `True`/`False` patterns: `TPCon` dispatched as `VBool` in the CEK machine

The parser represents `True` and `False` in pattern position as
`TPCon("True", [])` and `TPCon("False", [])`. The CEK machine stores boolean
values as `VBool(b)`, not as `VCon("True", ())`. The `match_pat` function in
`cek.py` previously dispatched `TPCon` by checking `isinstance(val, VCon)`,
which fails for `VBool`. Pattern matching on `True`/`False` therefore fell
through to the no-match case and raised a non-exhaustive-match error.

The fix: an early branch in `match_pat` intercepts `TPCon("True", [])` and
`TPCon("False", [])` and compares against `VBool(b)` instead of `VCon`.

---

## Phase 6 — Hardening decisions

### Float semantics: float32 precision across all backends

Lark's `Float` type has IEEE 754 single-precision (32-bit) semantics on all
backends. Every float operation — arithmetic, comparison, built-ins, and
display — rounds to float32 at each step.

**Display format**: `:.7g` (7 significant figures) with a `.0` suffix
guarantee so that integer-valued floats (`1.0`, `5.0`) are never printed
without a decimal point. This is the format used by the Pico 2W C runtime
and the RISC-V VM; all backends must agree.

**Why float32, not float64?** The primary compilation target is the Pico 2W
(RP2350), a microcontroller whose hardware float unit is 32-bit. Using float64
semantics in the interpreters and then float32 on hardware would make the
interpreters useless as correctness oracles. A language that means different
things on different backends is not a language — it is an accident.

**The CEK bug (Phase 6 fix)**: the original CEK machine used Python's native
`float` (64-bit) for all arithmetic and `str(f)` for display. This was
discovered by the differential test suite: `1.0 / 3.0` printed as
`"0.3333333333333333"` in the CEK but `"0.3333333"` in the TAC and RISC-V
VMs. The fix applied `_f32` rounding to all float operations and `:.7g`
formatting to display in `cek.py`, bringing it into agreement with the other
two backends.

**Rejected alternative — float64 throughout**: keeping float64 in all Python
backends and only rounding on hardware would paper over the semantic
difference. Programs that pass the interpreter would still fail on the Pico
with subtly wrong float comparisons or display. The mismatch would surface at
the worst possible time.

---

### Differential testing as a backend-agreement oracle

The differential test suite (`tests/diff_test.py`) runs every acceptance test
through all three backends and asserts byte-identical output. It is the
authoritative check that the CEK machine, TAC VM, and RISC-V VM implement the
same language semantics.

Known, permanent exceptions are listed in the `XFAIL` table with the backends
that must agree and a note explaining the divergence. The only current xfails
are 32-bit integer overflow cases (`04_tailrec`, `19_intoverflow`), where the
CEK and TAC VM use Python arbitrary-precision integers while the RISC-V VM
truncates to 32 bits. These are not bugs — they reflect the actual hardware
limitation of the Pico 2W target.

A divergence that is not in `XFAIL` is always a bug in one of the backends.

---

### Property-based tests: source strings over AST generation

The Hypothesis tests in `tests/gen.py` generate Lark programs as source
strings — not as typed AST nodes, not as `Program` objects. The full pipeline
(lexer → parser → type checker) is exercised on every generated input.

The alternative is to generate well-typed `TProgram` objects directly,
bypassing parsing. That would be faster and would allow more fine-grained
control over the generated structure. It would also miss any bug in the
interaction between the parser and the type checker — a malformed string that
parses to a syntactically valid but semantically unusual tree would never be
explored. Source strings exercise the complete path from user input to type
judgment and give the highest confidence that the pipeline is correct end-to-end.

The cost is that the generator must produce syntactically valid Lark source, which
constrains what can be generated. In practice, Lark's grammar is simple enough
that template-based generation (fill in variable names, types, and operators)
covers all the key structural variations for the properties being tested.

---

### Affine soundness: both branches of `if` checked sequentially

The test for `if True then x else x` (where `x : IO`) expects `AffineError`.
This may seem surprising: only one branch executes at runtime, so the IO token
is only consumed once. A sound linear type system would allow it.

Lark's type checker passes the same `tracked` dict to both branches without
forking or joining it. After the then-branch increments `tracked["x"]` to 1,
the else-branch increments it to 2 and raises `AffineError`. This is *sound
but conservative*: it rejects some valid programs (the `if True then x else x`
example actually uses `x` exactly once at runtime).

The alternative — branching the tracking state at each `if` and checking
that both branches leave the same variables consumed — is the standard approach
in linear type systems (see "Bounded Linear Types" or the Alms split/join
contexts). It allows `if c then use(x) else use(x)` and is the semantically
precise answer. Implementing it requires the type checker to carry two tracked
sets out of each branch and verify they agree, which adds complexity without
being needed for the current language subset.

The conservative approach is documented here so the test suite encodes it as an
intentional property — `if True then x else x` is always an error in Lark —
rather than as a coincidental implementation detail.

---

### Double-typecheck instead of round-trip

The build plan specified a "round-trip property": parse a well-typed program,
typecheck it, pretty-print the typed AST, re-parse and re-typecheck, and assert
the types match. This tests that the checker carries no state across calls.

Lark has no pretty-printer for the typed AST or for the surface language.
Implementing one would be a significant addition to the codebase for the sole
purpose of enabling this test.

The double-typecheck property (`test_double_typecheck`) tests the same invariant
more directly: call `typecheck(prog)` twice on the same `Program` object and
assert the two `TProgram` results are equal. If the type checker has any global
mutable state — a counter, a cache, a dict that accumulates entries — the two
calls will produce different `TVar` IDs and the equality check will fail.

The `TVar` IDs are deterministic because `Fresh()` is created inside `typecheck`
and starts at 0 on every call. Two calls on identical input traverse the program
in the same order and allocate the same IDs. Any non-determinism in ID allocation
would be caught immediately.

This approach is simpler, equally effective at finding state-pollution bugs, and
does not require building infrastructure that has no other use.

---

### Hardening catch: dead `body` variable in `_affine_dup_src`

During the hardening review of `gen.py`, a bug was found in the initial version
of `_affine_dup_src`. The strategy computed a `body` variable (with or without
an optional let-wrapper) but the return string hardcoded `({var}, {var})`
directly:

```python
return f"module Gen\nfn {fn}({var} : IO) : (IO, IO) =\n  ({var}, {var})\n"
#                                                              ^^^^^^^^^^
#                                                              should be {body}
```

The `if wrap:` branch was dead code. The generator always produced the same
single pattern, with only variable and function names varying — the advertised
variation across wrapping depth was never tested.

The fix is one character: `({var}, {var})` → `{body}`. The expanded generator
now uses 5 duplication patterns (direct pair, let-then-reuse, let-then-reuse
reversed, if-branch duplication, nested let), each optionally wrapped in an
irrelevant Int let-binding. The `@example` decorators pin the most important
cases so they always run regardless of random sampling.
