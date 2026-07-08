
## The Language Stack: From Silicon to Semantics

*Code Crafting no. 4, by Set Lonnert (2026)*

### The central question

The book is not built around *how do I build a compiler?* but around a different question: __what kind of thinking does a programming language embody, and how does that thinking propagate from hardware up through syntax to the type system?__ Language design could be treated as partly a philosophical problem rather than a solved engineering one--asking what a type system should be able to express, when a constraint counts as a safety property versus a limitation, and what ownership actually owns. These questions lack algorithmic answers but have precise ones, reachable through the propagative reasoning that compilers reward.

### Why the existing books don't fill the gap

The books surveys four well-regarded texts and explains what each leaves unaddressed:

- *The Dragon Book* (Aho, Lam, Sethi, Ullman)--comprehensive and authoritative, but a dense reference text organized for lookup and oriented toward production compilers. Learning from it is likened to understanding a cathedral by reading its maintenance manual.
- *Modern Compiler Implementation* (Appel)--has the right instinct of building one language (Tiger) from chapter one, but is now a quarter-century old, and its three editions feel like incomplete versions of the same idea. Its type system isn't the kind interesting languages now have.
- *Crafting Interpreters* (Nystrom)--exceptionally clear, with a sound two-implementation approach, but deliberately stops before the formally interesting territory: no real type system, no ownership semantics. The result is a pleasant scripting language, by design.
- *Engineering a Compiler* (Cooper, Torczon)--the most accurate and organized, but hardest as a first encounter because it's structured the way a compiler is, not the way understanding develops.

### What this book does differently

Four commitments distinguish it:

1. *Hardware is not abstracted away.*
   Real instruction sets appear as working systems with measurable costs--the 6502 as a
   historical "clarity instrument" whose constraints make hidden costs visible, and RISC-V
   as the modern target. By the end, programs run as native machine code on a Raspberry Pi Pico 2/2W.
2. *Theory is earned, not assumed.*
   Type-theory content (Hindley-Milner inference, affine types, trait bounds) is introduced
   only when the implementation needs it, after the reader has seen what the implementation
   does without it. We frame this as the correct epistemological ordering.
3. *One language, start to finish.*
   Every chapter advances a single language rather than offering scattered illustrative
   fragments, so the reader finishes with something that works.
4. *The safety argument is structural.*
   Following Rust's central insight, memory safety and ownership are enforced by the
   type system rather than a garbage collector. Affine types enter in Chapter 5 and
   shape every later decision through the code generator (Chapter 9) and the formal
   treatment (Chapter 11).

### The language: Lark

*[Lark](./lark/lang/tutorial.html)*--*Lambda Affine Resource Kernel*--is a small, purely functional language with Hindley-Milner type inference, affine ownership, and RISC-V as its compilation target. Its connection to Rust is explicit but bounded (Lark is not Rust), and it sits in a lineage of languages that treat ownership as a type-theoretic property rather than a runtime mechanism, including Clean and Cogent. Its closest research precedent is __[Alms](https://users.cs.northwestern.edu/~jesse/pubs/alms/)__ (Tov and Pucella, 2011), OCaml extended with affine types; Lark is roughly Alms made compilable, using traits instead of a module system for structured polymorphism.

### The LLM question

The book confronts a 2026-specific objection: if large language models can generate parsers, type checkers, and compilers on demand, why learn how they work? One reply is that the objection proves too much--a surgeon who understands anatomy still reasons differently from one who doesn't, even when a robot makes the incision. Language implementation is where system-level reasoning lives in its most concentrated form: a type system is a formal claim about what programs mean, a register allocator is a constraint-satisfaction problem with a cost model, a calling convention is a contract between modules. None can be safely outsourced without the practitioner understanding what the tool does. LLMs are strong at reproducing seen patterns but weak at the *propagative reasoning* needed when a pattern doesn't fit--exactly the skill building a language cultivates. Lark itself was built with LLM assistance, but the reasoning behind each decision lives in the book and repository, not hidden inside a generation process--the intended model being tool-assisted construction with human-owned understanding.

### Who it's for, and where it ends

The book targets technically literate programmers who want to understand what underlies their language. It is not a first programming book; it assumes familiarity with Python or C (preferably both) and basic data structures, and suits advanced undergraduates, graduate students, and working practitioners.

It stops at a defined point on the type-theory ladder: Hindley-Milner inference plus affine types plus trait-bounded polymorphism. The next rung named is *dependent types*, where the type checker and the proof checker become the same thing--the territory of Idris, Agda, and Lean. The Conclusion points readers who want to go further toward that rung.

### The companion code

This repository holds the runnable companion to each chapter. Every chapter folder
builds and runs on its own — see its `README.md`, and its `Makefile` where one
applies (`make run`).

| Chapter | Folder             | Title                                       |
|---------|--------------------|---------------------------------------------|
| 1       | [`ch01/`](./ch01/) | Instruction Sets and Memory                 |
| 2       | [`ch02/`](./ch02/) | A Virtual Machine in Software               |
| 3       | [`ch03/`](./ch03/) | Lexical Analysis                            |
| 4       | [`ch04/`](./ch04/) | Parsing                                     |
| 5       | [`ch05/`](./ch05/) | Names, Scope, and Types                     |
| 6       | [`ch06/`](./ch06/) | A Working Interpreter                       |
| 7       | [`ch07/`](./ch07/) | Intermediate Representations                |
| 8       | [`ch08/`](./ch08/) | Optimization                                |
| 9       | [`ch09/`](./ch09/) | Code Generation                             |
| 10      | [`ch10/`](./ch10/) | Abstract Machines and Operational Semantics |
| 11      | [`ch11/`](./ch11/) | Correctness                                 |
| 12      | [`ch12/`](./ch12/) | Types as Proofs                             |
| 13      | [`ch13/`](./ch13/) | The Adversary                               |

[`lark/`](./lark/) is the Lark reference implementation — interpreter, compiler,
and the machine-checked soundness proof in [`lark/formal/proof/`](./lark/formal/proof/).
[`solutions/`](./solutions/) holds worked solutions to the chapter exercises.


### Continued in the repository ..

I keep a few planned extensions that will not appear in a revised edition of the book,
but will instead be published here as downloadable supplements. The first is a
self-hosting Lark: Lark compiling Lark, the ultimate self-test, now complete.
Next come optimizations. They were mentioned only briefly in the book, at a
theoretical level; here they are worked out in practice. Finally, affine and
refinement types make their entrance in what I hope will become:
we proved programs the way we proved the language ..

