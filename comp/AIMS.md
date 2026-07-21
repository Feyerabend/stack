
## AIMS — what Lark, and its book, are for

*The north star. Every chapter written, every plan under `formal/proof/strands/`,
every pedagogical comment in the public repo serves the aim below. When a choice is
unclear, this is what it is measured against.*



### The one aim

__To carry a programmer who already knows how to program a little way into logic —
without ever asking them to study logic first.__

The reader we are writing for is a computer science student, or a working programmer:
someone at home with code and the machine, who finds *a language that compiles
itself* a vivid idea and *the same program, made faster* an obvious good — but for
whom __proof__, __soundness__, and __logic__ feel like a neighbouring country with a
hard border and its own language. Lark's book is a road across that border that
starts on the side the reader already lives on.

### The arc that carries them: a language earning the right to make promises

The project — self-host, optimize, prove — is one story told in three moves,
each a larger promise, each needing a little more logic to state and to keep:

1. __It builds itself.__ A language compiles its own compiler (the chicken and the
   egg). This is autonomy, and it is where the reader is most at home — no logic
   needed, just the delight of the thing biting its own tail.
2. __It makes itself faster — without changing what it means.__ Optimization is the
   first promise *about meaning*: the output must run quicker and compute the same
   answer. The reader already wants speed; here they meet, gently, the idea that
   "same answer" is a claim someone has to be able to check.
3. __It makes and keeps promises about programs — and then about itself.__ A type
   says a program is *meaningful*. But well-typed is not correct. So the reader is led
   to want *more* — to say "this divisor is never zero," "this index is in range,"
   "this tree stays sorted" — and to have a machine check it. That wanting is where
   the logic arrives, not as a prerequisite but as the tool the desire requires. At
   the top, the language proves its own promising-machinery sound.

Nobody is asked to learn logic in the abstract. They are shown a thing they want to
be able to say about a program, and the logic is what it takes to say it.

### How it teaches

- __Start where the reader already lives.__ Self-hosting and optimization are the
  on-ramp because they are a programmer's home turf. The unfamiliar is
  always reached *from* the familiar, never dropped in cold.
- __Let hard ideas arrive as needs, not as syllabus.__ A refinement type shows up
  because you want to forbid division by zero — decidability shows up because you want
  the check to happen without writing a proof by hand. Every abstraction enters as the
  answer to a question the reader is already asking.
- __Proof is an extension of programming, not a separate discipline.__ The ladder —
  type safety, then refinements, then measures, then the language's own soundness — is
  a sequence of small, motivated steps, each one a programmer's move.
- __Candour is the pedagogy.__ The book shows the real system: the false proofs found
  and fixed, the oracle frozen so its numbers mean something, the quadratic left
  unrepaired on purpose, the boundaries not crossed (32-bit integers, full compiler
  correctness, the affine layer). A student learns more from a real artifact with
  named limits than from a tidy fiction. *Here is how far we got, and here is what we still trust.*
- __It runs, and it is yours.__ Everything the book describes, the reader can open,
  run, break, and watch complain. The public repository is a laboratory, not an
  appendix.

### What the reader carries away

A CS reader who never took a logic course will, by the end, have met — through
building, never as dry theory — a working sense of: a *decidable fragment* (and why a
tool declines rather than guesses at its edge); *propositions as types* (a glimpse);
*operational semantics* and what it means to *preserve* meaning; *soundness* and what
a proof actually buys; and the *trusted base* — the humbling, clarifying question of
what you still have to take on faith. Not a logician. But no longer a stranger to it.

### The three artifacts, one aim

- __The book__ (`book/`, *Lark Builds Itself*) — the narrative that does the carrying.
- __The repository__ (public, reader-facing: `self/ optimize/ prove/`) — the
  laboratory: runnable, commented for a reader, candid about its own scars.
- __The proofs__ (`formal/proof/`, and the strands: refinements, affinity, the
  fixpoint) — the summit the reader is walked toward, always in reachable steps with
  the un-climbed parts named, not hidden.

### What this is *not* (the boundaries are features)

Not a logic textbook — it teaches only the logic the building demands. Not a compiler
theory monograph — it is a single small language followed all the way down, not a
survey. Not a research paper — where a proof is out of reach (full compiler
correctness), the book says so and shows the truthful substitute (differential testing)
rather than pretending. The point is never completeness. The point is a programmer who
crosses a border they thought was closed to them, and finds they were already halfway
across.
