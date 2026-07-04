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

---

## Phase 7 — Type system hardening decisions

### `TraitBoundError` via post-pass rather than constraint propagation

Show requires a `Show` instance for its argument type.  The two standard
implementation strategies are: thread a constraint set through `infer()` so that
every call site checks the constraint as it is generated, or add a post-pass
that walks the fully-substituted typed tree and checks constraints after all
types have been resolved.

Lark uses the post-pass (`_check_show_bounds`).  The reason is sequencing:
HM inference builds a substitution incrementally.  Inside the body of
`match r with | Ok(n) => show(n)`, the type of `n` is initially a fresh `TVar`
from `infer_pat`.  Only after unifying the pattern type with the scrutinee type
(`Result(Int, String)`) does `n` resolve to `Int`.  If the bound check runs
at the `show(n)` call site during inference, before the match unification
completes, `n`'s type is still a `TVar` and the check raises a false positive.

The post-pass runs after `_apply_texpr` replaces every `TVar` in the body with
its final concrete type.  At that point `n : Int`, `show(n)` passes, and
`show(unconstrained_x)` correctly raises `TraitBoundError`.  The trade-off:
higher-order show abuse (`let f = show in f(x)`) is not caught, because the
post-pass only checks `XApply(XVar("show"), args)` patterns directly.
This is an acceptable simplification — the language has no way to write a Show
bound on a user-defined type variable yet.

---

### `infer_pat` constructor unification returns a substitution to the caller

When `Ok(n)` appears as a pattern matched against `Result(Int, String)`, the
variable `n` should get type `Int`.  Before Step 7.2, `infer_pat` created a
fresh `TVar` for `n` and returned it as-is; only the outer match unification
(pattern type ~ scrutinee type) resolved it, but that substitution was applied
only to the type, not to the typed pattern nodes containing `n`.  The result:
`n`'s typed-tree node still carried the `TVar`, triggering a spurious
`TraitBoundError` from `_check_show_bounds`.

The fix extends `infer_pat` with an optional `env` parameter.  When a `PCon`
pattern is processed with `env` available, `infer_pat` looks up the constructor's
scheme, instantiates it, and unifies each sub-pattern type variable with the
corresponding field type extracted by peeling `TFn` layers.  The accumulated
substitution is returned as a fourth element of the result tuple.

The caller (`MatchExpr` in `infer()`) composes this `s_pat` into the outer
substitution `s` before the match-wide unification.  This ensures that by the
time `_apply_texpr` runs, the pattern-bound variables carry concrete types.

Returning the substitution to the caller — rather than applying it inside
`infer_pat` — is the key design choice.  It keeps `infer_pat` pure (no mutation
of external state) and allows the outer unification to further refine any types
that remain polymorphic after the constructor lookup.

---

### Static show routing in `lower.py`: compile-time not runtime

The lowerer routes `show(expr)` at compile time, based on `expr`'s type in the
typed AST.  An alternative is to always emit a call to the generic `show` stub
and let the runtime inspect the value's tag to decide what to print.

Static routing is correct here because the type checker guarantees that `show`
is only called on types with a `Show` instance.  For user-defined types this
means there is always a `show$TypeName` function.  For primitives the type is
known (Int, Float, Bool, String).  The static type information is therefore
complete and already present in the typed AST; no runtime inspection is needed.

The practical reason for routing Float and Bool to separate stubs:

- Float: the generic `show` stub receives an integer register containing float32
  bits.  `str(float_bits)` prints the integer value, not the float.
- Bool: the generic `show` stub receives `0` or `1`.  `str(0)` prints `"0"`,
  not `"false"`.

Routing these at compile time is the only option that works without adding
type-tag overhead to every value at runtime.

---

### Dispatch stubs skipped for built-in methods

When a trait method is defined only via user impls, `lower.py` generates a
dispatch stub — a TAC function named after the method (`describe`, `area`, etc.)
that checks the argument's constructor tag and routes to the appropriate
`method$Type` implementation.

This stub must not be generated for `show`.  The TAC VM and RISC-V VM both
provide a built-in handler named `show` that handles `Int`, `String`, and `()`.
If a TAC dispatch stub were generated with the same name, it would shadow the
built-in, and `show(42)` would call the stub, which only knows about user-defined
impl types.

The skip condition `if method_name in _BUILTINS: continue` is the correct fix.
The built-in handler remains in place; the static routing in `_lower_apply`
handles the user-defined cases by calling `show$TypeName` directly — no stub
needed.

---

### `_show_impls` computed before the lowering loop

`lower.py` populates `_show_impls` (`{type_name → "show$TypeName"}`) by
scanning `_trait_impls`, which is filled in a first pass over the program
declarations.  The dict must be ready before the lowering loop starts, because
`_lower_apply` reads it on every `show` call site.

In the initial implementation, `_show_impls` was computed after the lowering
loop — an ordering mistake.  Every call to `_lower_apply` during lowering saw
an empty `_show_impls` and fell through to the generic `show` stub, so
`show(Red)` emitted `call show(t0)` instead of `call show$Color(t0)`.  The TAC
VM still produced correct output because it re-dispatches `show` dynamically;
the bug was silent there but caused wrong output in the RISC-V VM (raw pointer
addresses printed as integers).

The fix is to move the `_show_impls` computation to immediately after
`_global_fns` is populated (which also happens before the lowering loop) and
before the global-let init function is lowered.

---

### Python CEK: seeding primitive Show into the dispatch table

When the first `impl Show for SomeType` is processed in `eval_program`, the
`env["show"]` entry switches from `VBuiltin("show")` to `VDispatch("show")`.
From that point on, every `show(arg)` call goes through `VDispatch.apply`,
which looks up `m.dispatch[("show", runtime_type(arg))]`.

If the dispatch table has no entry for `("show", "Int")` etc., then
`show(42)` raises `RuntimeError: no impl of 'show' for type 'Int'` — even
though the built-in show for integers was perfectly functional before the user
impl was registered.

The fix seeds the builtin value for all primitive types at the moment
`VDispatch` takes over:

```python
if isinstance(env.get(meth.name), VBuiltin):
    builtin_val = env[meth.name]
    for prim in ("Int", "Float", "Bool", "String", "()"):
        if (meth.name, prim) not in m.dispatch:
            m.dispatch[(meth.name, prim)] = builtin_val
```

The `if … not in m.dispatch` guard means a user `impl Show for Int` can
override the builtin by registering a dispatch entry before this code runs.
The seeding only fills gaps.

The alternative is to check `isinstance(impl, VBuiltin)` inside `apply` for
`VDispatch` and route to the builtin handler directly.  That avoids touching
the dispatch table but puts dispatch logic in two places.  Seeding the table
keeps `apply` clean: `VDispatch` always looks up the table, and the builtin is
just a value in the table like any other impl.

---

## Phase 7 — REPL decisions

### Python CEK rather than C CEK for the REPL

The C CEK (`cek.c`) is compiled from static C structs emitted by `emit_c_ast.py`.
The pipeline is: parse → typecheck → emit_c_ast.py → compile C → execute.
The compile step makes the C CEK unsuitable for an interactive REPL: compiling a
new C source on every keypress is too slow, and the emitted structs are a
compile-time encoding of the program, not a runtime interpreter.

The Python CEK (`cek.py`) evaluates the typed AST directly, with no intermediate
compilation step.  It is the natural choice for the REPL: parse, typecheck, and
call `eval_program` — the result is ready in milliseconds.

The Python CEK is the canonical correctness oracle for the whole pipeline
(differential testing uses it as the reference).  Using it in the REPL ensures
that interactive output matches file-mode output.

---

### Re-typecheck the full accumulated source on each new input

The REPL maintains the accumulated source as a list of declaration strings.
On each new input, it prepends `module Repl` and calls `typecheck()` on the
complete accumulated program.

The alternative is incremental typechecking: pass the existing type environment
into `typecheck()` and only check the new declaration.  This requires exposing
the internal type environment from `typecheck()` and redesigning the API.

Re-typechecking is O(n) per input and O(n²) total over a session of n inputs.
For a REPL session — which rarely exceeds a few dozen declarations — this is
imperceptible.  The code requires no changes to `infer.py`; the existing API
is used as-is.  The benefit: full mutual visibility across all accumulated
declarations.  Pass 1.5 pre-registers all fully-annotated function types before
checking any body, so adding a function that calls a later-defined function works
as long as both are in the accumulated source.

The trade-off: mutual recursion across *separate inputs* is not possible — when
`is_even` is typed on its own line, `is_odd` is not yet in the source, so the
type check fails.  This is the same limitation as GHCi.  The workaround is to
type both definitions in the same multi-line input using the continuation prompt.

---

### Evaluate only the new declarations, not the full accumulated program

After typechecking, `tprog.decls` contains all declarations (accumulated + new).
The REPL tracks `count` — the number of declarations evaluated in previous inputs.
It evaluates `tprog.decls[count:]` (the new slice only) against the existing env.

The alternative is to re-evaluate everything from scratch each time.  That works
for pure functions but is wrong for declarations with side effects (print, IO)
— they would run again.  And it would reset the runtime state (dispatch table,
constructor registry) unnecessarily.

Evaluating only the new slice requires `count` to be accurate.  Since imports
are disabled in the REPL (no `module Repl` with `import`), `tprog.decls` grows
by exactly the number of declarations in the new input.  The count is reliable.

---

### Global backpatch after each declaration

The standard `eval_program` backpatch wires each new closure's env with the
other closures from the same call.  When declarations are added one at a time
over multiple REPL inputs, a function added in input 5 won't see functions added
in inputs 1–4 without a broader backpatch.

After each `eval_program` call, the REPL performs a global backpatch:

```python
all_closures = {n: v for n, v in self.env.items() if isinstance(v, VClosure)}
for v in all_closures.values():
    v.env.update(all_closures)
```

This ensures that all top-level closures see each other, regardless of when they
were added.  `VClosure.env` is a mutable Python dict, so the update propagates
into previously-created closures.

The cost is O(n) per declaration for n accumulated closures.  The benefit is
that functions defined across multiple inputs can call each other without error.

---

### Expressions evaluated in a temporary env

When the user types an expression, the REPL wraps it in `let lark_repl_it = expr`
and evaluates it in `dict(self.env)` — a shallow copy of the current env.  The
result is read from the copy; the real env is not modified.

The alternative is to evaluate in the real env and clean up (`del env["lark_repl_it"]`)
afterward.  That works but is fragile: an exception during evaluation would leave
the placeholder in the env, shadowing any user variable with the same name.

The temp-copy approach is always clean and adds no persistent state.

---

### Placeholder identifier avoids leading underscore

The expression placeholder is named `lark_repl_it` (not `__repl__`).  The Lark
lexer rejects identifiers that start with `_` — they are reserved for the
WILDCARD pattern token.  `lark_repl_it` is a valid lowercase identifier.

A user who defines `let lark_repl_it = ...` would shadow the REPL's placeholder
for that expression.  This is an accepted limitation — the name is unlikely to
appear in practice and any clash produces a type error rather than silent
misbehaviour.

---

### Multi-line continuation via parse-error detection

When a declaration is being read and the parser reports an unexpected-EOF error,
the REPL re-prompts with `"   .. "` and appends the new line to the buffer.  The
loop continues until either the parse succeeds or the error is not an EOF.

The detection checks `"EOF" in e.msg` on the `ParseError` exception.  The
parser's `_expect` helper formats its message as `"expected X, got EOF ('')"` when
it hits the end of token stream, so the string "EOF" reliably appears.

A real syntax error (e.g., `"expected NAME, got PLUS"`) does not contain "EOF",
so the loop exits and the caller reports the error.

The alternative — a dedicated multi-line input mode (e.g., blank-line to
terminate) — would require users to always press Enter twice, even for
single-line declarations.  EOF-detection is unobtrusive: single-line declarations
terminate naturally; multi-line declarations continue as long as needed.

---

## Phase 8 — Rigour: exhaustiveness, totality, defined Int

### Exhaustiveness as a post-pass over the typed AST

The check (`exhaust.py`) runs after each declaration is fully type-checked and
substitution-applied, walking the typed tree exactly like the Show-bound check —
not inside `infer()` while substitutions are still in flight.  Two reasons:

1. Maranget's algorithm needs *final* column types to know each type's complete
   constructor signature.  Mid-inference, the scrutinee may still be a type
   variable.
2. Keeping it out of `infer()` keeps Algorithm W recognisable.  Exhaustiveness
   is a separate judgment with its own literature; the code should reflect that.

The witness pattern from the usefulness recursion is the error message:
`non-exhaustive match: pattern 'Cons(Err(_), Nil)' not covered`.  The recursion
that proves non-exhaustiveness *constructs* the counter-example — reporting it
costs nothing and turns a rejection into a diagnosis.

`True`/`False` may be written as constructor patterns or lowercase literals;
both normalise to Bool literals so either spelling completes the signature.

The `__lark_match_fail` trap in `lower.py` is now statically unreachable but
still emitted: the IR stays well-formed without trusting the frontend.

### `total` is a contextual modifier, not a keyword

`fn total f(xs) = ...` parses by lookahead: after `fn`, if the first name is
`total` and another name follows, it is the modifier; a function actually
named `total` continues with `(` and parses as before.  No lexer change, no
reserved word, no breakage of existing programs.

### The totality checker refuses integer descent — because Int wraps

The obvious question: why doesn't `countdown(n - 1)` count as decreasing?
Because Phase 8 defines Int as a *wrapping* i32, `n - 1` from a negative n
never reaches a `n == 0` base case — it wraps through INT_MIN and keeps going.
Structural descent into constructors is well-founded by construction; wrapping
integer descent is not, and the checker would be lying if it accepted it.
This is a case where two features designed separately (defined overflow,
totality) force each other's hand — the interaction is the design.

Deliberate v1 limits, each with its own error message: mutual recursion between
total functions (needs lexicographic or size-change measures), and passing the
function's own name as a value (would hide recursion behind a parameter).
Function-typed *parameters* are assumed total: `fn total map(f, xs)` is total
relative to its arguments, exactly as in Coq or Agda, where all values in
scope are already total.

### Int is a wrapping i32 with RISC-V division — in every backend

Through Phase 7, CEK and TAC used Python bignums while RV32 wrapped at 32
bits; three test-harness escape hatches (an xfail, a diff exemption, and two
C-CEK skips) papered over the divergence.  Phase 8 defines the semantics
instead: Int is a 32-bit two's-complement integer that wraps on overflow,
with RISC-V M-extension division rules (`x/0 = -1`, `x%0 = x`,
`INT_MIN / -1 = INT_MIN`, `INT_MIN % -1 = 0`).

The choice of *wrap* over *trap* follows the compilation target: RV32 hardware
wraps for free, so wrap is the only semantics all backends can implement at
zero cost.  The C CEK computes in `uint32_t` and casts back — unsigned
overflow is defined in C, signed is not.

Consequence: `04_tailrec` and `19_intoverflow` now expect the wrapped values
and pass identically on CEK, TAC VM, RV32 VM, and the C CEK.  All xfail/skip
bookkeeping for overflow is deleted.  A backend that disagrees on any program
is now simply wrong, which is what a differential test suite needs.


## Phase 9 — Track C: generation and fuzzing decisions

### Generate programs by inverting the typing rules, not by mutating text

The Phase 6 property tests (`tests/gen.py`) instantiate a handful of fixed
templates — good for pinning single rules (affine soundness, Copy
transparency), useless for finding interactions.  Phase 9's `gen_prog.py`
generates whole programs *goal-first* (Palka et al. 2011): to produce an
`Int`, choose among the typing rules whose conclusion is `Int` — a literal,
a variable of that type in scope, an arithmetic node, an `if`, a `match`, a
call — and recurse into the premises.  Programs are well typed by
construction, so a checker rejection is a generator bug (property P6) and a
backend disagreement is a compiler bug (property P7).

The rejected alternative — random token soup or AST mutation — mostly tests
the parser's error paths.  Inverting the rules concentrates the entire
budget on programs that reach lowering, register allocation, and codegen.

### The generator tracks the checker's *conservatisms*, not the ideal rules

Two session states thread through generation.  Affine use: IO is threaded
linearly through main and non-Copy ADT values are consumed at most once
program-wide, matching the checker's cross-branch counting.  Groundedness:
an unannotated lambda parameter that the body never constrains stays a
generalised type variable, and both `show` and (new in this phase) the
operators reject unresolved types — so the generator marks such expressions
fragile and grounds them (`x + 0`, `x or false`) before using them where
concreteness is required.  Both were discovered by P6 counterexamples, which
is the property doing its job: the generator must invert the rules as
implemented, not as remembered.

### Bias division toward its edge cases — validated by mutation testing

A planted bug (TAC VM `x/0 = -2`) survived 300 uniformly-generated programs:
a random subtree almost never evaluates to exactly zero, and a division that
does must still flow into printed output.  With '/' forcing a divisor from
{0, 1, -1} half the time, the same mutation is caught and shrunk to
`show((0 / 0))` in about a second.  The mutation test stays in the story:
a fuzzer that has never been seen to catch a planted bug is a hope, not a
tool.

### Fuzzing's first catch: reject ambiguous operators (monomorphism restriction)

The first real counterexample: `let f = (fn(x) => x + x) in f("uh oh")`.
Operators are ad-hoc polymorphic (`+ : a -> a -> a`); inside the generalised
lambda the operand type is still a variable.  The CEK and TAC VM dispatch on
the runtime value — string concatenation.  But `lower.py` selects
`__str_concat` from the *static* type, so the RV32 backend fell through to
integer `add` on two string pointers and printed raw memory.  Typechecks
everywhere, miscompiles on one backend: precisely the bug class differential
fuzzing exists for.

Three fixes were possible.  Runtime dispatch on RV32 is out — values are
raw 32-bit words with no tags.  Monomorphisation (compiling one copy of f
per instantiation) is the heavyweight answer and belongs with Track B if
ever.  Chosen: a monomorphism restriction on operators — if an operator's
operand type is still a type variable when the enclosing declaration is
generalised, that is a type error ("ambiguous operator type … add a type
annotation").  SML made the same trade for overloaded arithmetic.  The
restriction turns a silent wrong-code bug into a diagnostic, costs no
existing corpus program (all 90 still pass), and error test 15 pins it.

### Scope the generator to defined semantics; leave Float out deliberately

Generated programs use Int (fully defined since Phase 8), Bool, String
concatenation, Int comparisons, one user ADT, tuples, closures, and IO
threading.  Float is excluded on purpose: the TAC VM computes in Python
f64 while the CEK rounds through f32, so random float expressions would
diverge *by design* and drown real signals.  That divergence is a known,
documented debt — closing it (one float width everywhere, then admitting
Float to the generator) is a natural next Track C step, alongside the
sanitizer run and the lcore affine proof.

### The frontend's contract: a diagnostic or a typed program, never a traceback

Track C step 2 makes robustness a stated property (P8, `fuzz_frontend.py`):
for any input — random unicode, token soup, mutated programs, pathological
nesting — the frontend either returns a typed program or raises a
positioned diagnostic.  Fuzzing found three violations.  Deep input blew
the Python stack (recursive-descent parsing, then every recursive pass
downstream); the fix is a per-declaration budget of 2000 expression/
pattern/type nodes, which bounds parser stack depth *and* the AST depth
every later pass walks, making the whole pipeline stack-safe by a counting
argument rather than by hope.  Two lexer holes came from Python itself:
`str.isdigit` accepts superscripts that `int()` rejects, and CPython caps
int-string conversion at ~4300 digits — both are now positioned LexErrors.

The budget rejects no realistic program (2000 nodes in one declaration is
enormous handwritten code) and the errors are ordinary ParseErrors, so
the REPL and every backend inherit the protection through the shared
frontend.  One operational lesson worth keeping: Hypothesis restores
sys.recursionlimit around each example, so the limit raise lives in
parse()/typecheck(), not at module import — a library that needs stack
headroom must claim it at call time.

### Sanitizers as a standing target, validated before trusted

`make santest` rebuilds the C CEK under ASan + UBSan with
-fno-sanitize-recover and runs the whole corpus; a sanitizer report fails
the test even when exit codes agree, so an ASan abort can never
impersonate an expected compile-time rejection.  The corpus comes back
clean — the Phase 8 choice to compute Int in uint32_t (unsigned overflow
is defined C; signed is not) is what makes wrapping arithmetic
UB-free by construction.  The harness itself was validated by compiling
planted UB with the same flags and watching it abort: the same
plant-a-bug discipline as the TAC-VM mutation test in step 9.1.
libFuzzer is not available under Apple clang; corpus + generated-program
coverage stands in for it, and a Linux CI run could add it later.

### Closures may not capture affine values — the second soundness hole

The hardening review asked a simple question of every rule the affine
tracker has: where does a use *not* look like a name occurrence?  Answer:
capture.  The lambda rule checks its body against a *copy* of the tracking
map, so `let g = fn(x) => io in (g(1), g(2))` — where io appears once —
was accepted, and each call of g returns the same IO token.  P1 never
caught it because its generators only produced textual double-uses.

The fix is a rule, not a patch: **a lambda may not capture an affine
variable.**  The justification is the Copy status of function values — a
closure may be called any number of times, so even a single capture is a
license to duplicate.  The alternatives were worse: counting capture as
one use still allows double-call duplication, and making capturing
closures themselves affine requires non-Copy function types — a type
system redesign that belongs to Track B if anywhere.  The rule costs no
corpus program (closures over Copy values — the universal pattern — are
untouched), the diagnostic tells the user exactly what to do instead
("pass it as a parameter"), and error test 16 plus capture-shaped P1
generator cases pin it.  The lcore affine mechanization (next Track C
item) should treat capture as a primary case, not an afterthought.

### One diagnostics tuple, shared by the checker, the CLIs, and the fuzzer

The frontend's failure contract is now a single value: infer.DIAGNOSTICS.
The five CLI runners catch exactly that tuple (plus OSError) and print a
one-line error; the P8 fuzz property accepts exactly that tuple as a
correct outcome.  Before, each runner had its own notion — several had
none and leaked tracebacks, passing the error-test suite only because a
traceback happens to exit non-zero.  Sharing the tuple means the CLI
surface and the fuzzed property cannot drift: a new diagnostic type added
to the checker is automatically legal for the fuzzer and automatically
handled by every runner.

### Certify the allocator, don't prove it

The register allocator is the piece of the back end where a bug is both
likeliest (interval bookkeeping, off-by-ones) and quietest (wrong register
= wrong value, no crash).  Proving linear scan correct is a project;
*checking each output* is an afternoon — the classic certifying-compilation
trade (translation validation): don't verify the algorithm, verify every
answer it gives, at compile time, forever.

Independence decides the design.  regalloc.py already had a verify()
against the interference graph, but igraph.py and the allocator both stand
on cfg.py + liveness.py — a bug in the shared analysis produces a wrong
graph AND a wrong allocation that agree with each other.  regcheck.py
therefore re-derives liveness from the flat instruction list with its own
def/use and its own fixpoint, sharing only the instruction set itself.
The checker is also *finer* than the allocator (per-point liveness versus
whole intervals), which buys precision: a planted expiry off-by-one that
happens to be semantically safe — a read-ending interval meeting a
write-starting one on the same instruction — is correctly not flagged,
while genuinely premature register release is caught with the exact
instruction and the clobbered name.  Both directions were validated by
mutation before the certificate was trusted, as with the TAC planted bug
and the sanitizer planted UB: the pattern is now a habit.

One check earns its place twice: a *dead* definition still emits a write,
so the certificate rejects any def whose register holds a different
live-out Tmp even though no liveness overlap exists.  And the failure mode
is deliberately rude — RegAllocCertificateError is not in
infer.DIAGNOSTICS, because a certificate failure is never the user's
fault, and a compiler must not dress its own bugs as their type errors.
