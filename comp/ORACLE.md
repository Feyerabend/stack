
## The oracle, and what we have done to it

__Pristine oracle: `a12ad34a`__ — the commit immediately before self-hosting began
(parent of `1c42f3f`, the first commit that added `self/`).

Regenerate the ledger below with `tools/oracle_drift.sh` (or `-v` for the full
diff). It reads git, not this file. If the two disagree, git is right.



### Why this file exists

The method is differential: __the port is correct when it cannot be told apart
from the oracle.__ Every green count in `self/tests/BASELINES.md` is a claim of
that form, and so is every fixpoint sha.

A claim of that form is *empty* if the oracle moves and nobody writes down how.
"Indistinguishable from the reference" means nothing when the reference is a
moving target — you can always reach agreement by walking toward each other.
ch01 of the book puts it this way: *an oracle that moves is not an oracle; it is
a mirror.*

The oracle has moved. __3,393 insertions across 13 files__ since `a12ad34a`. Most
of that is legitimate and none of it is secret, but until it was
written down nowhere, and the book was telling readers there had been *three*
changes. That was not a lie so much as an unchecked memory, which is worse,
because a lie knows it is one.

So: everything below, or the claim is void.



## Class A — additions. New files; nothing pre-existing changed.

These are not thaws. They are a second axis (the optimizing backend, OPTIMIZE
O0–O5) built *beside* the checking path, not through it. No behaviour that any
earlier baseline pinned could move, because none of this code existed when those
baselines were cut, and nothing that did exist calls into it on the old path.

| file | what |
|------|------|
| `opt.py` | TAC→TAC optimization passes (−O0..−O3) |
| `emit_tac_c.py` | C from *optimized* TAC — the second back end |
| `coloring.py` | register allocation (RV32) |

__Witness:__ the pre-existing differentials (`difftest`, `cektest`) are unchanged
by their presence, and `tacctest` (100/0/0) pins the new path against the CEK.

### Class B — growth. The language got bigger because the port needed it.

A compiler cannot be written in a language that cannot take a string apart. These
are primitives the *port demanded*, added to the oracle first and mirrored into
the port in lock-step (SELFHOST M0). The oracle grew; it was not corrected.

| primitive | added for | rippled into |
|-----------|-----------|--------------|
| `string_index`, `string_slice`, `char_to_string` | `lex.lark` — indexing source text | `infer.py`, `cek.py`, `cek.c`, `lower.py`, `tac_vm.py`, backends |
| `string_to_int`, `string_to_float` | `lex.lark` — literal scanning | same |
| `read_all` | the bootstrap compiler reads its own source from stdin | same |
| `float_to_bits` | `emit_c.lark` — emitting float constants bit-exactly | same |

__This is the honest cost of self-hosting, and it is worth naming.__ The claim
"Lark can express its own compiler" is true *of a Lark that grew eight primitives
in order to*. Whether that is cheating depends on what you wanted the claim to
mean. It is certainly not free.

__Witness:__ `07/tests/24_stringprims.lark` (the only test of these primitives —
see the note below), plus every differential, which exercises them on every run.

### Class C — corrections. The oracle was *wrong*.

These are the real thaws. Each one re-opened, in principle, every pinned fixpoint
and every pinned count, and each was gated on all of them coming back unchanged.

#### C1 · A column is a byte offset (`lexer.py`)

The oracle counted columns in codepoints; the port counts bytes, because a Lark
`String` *is* UTF-8 bytes. The two lexers disagreed about every column after the
first non-ASCII character. __The port was right and the oracle was wrong__, and we
changed the oracle. Neither the fixpoint nor the differential could have caught it
(the corpus is almost all ASCII); a human noticed.

#### C2 · The C arena is malloc'd, not static (`cek.c`)

`static char _arena_buf[LARK_ARENA_SIZE]` cannot be sized past a few hundred MB;
the self-compiling compiler wants gigabytes. Not a correctness fix — a limit fix
— but it is an edit to the frozen artifact and it belongs here.

#### C3 · A signature licenses polymorphic recursion (`infer.py`, `ty.py`)

The big one. `check_fn_decl` bound a function's own name to a bare monotype var
while checking its body, *discarding the type pass 1.5 had already computed from
its signature*. So a polymorphic function that recurses on its own result could
not be typed — and, because `compose` ran no occurs check and `apply` chases
variable chains, the symptom was not a rejection but a __hang__.

Two changes:

- `infer.py check_fn_decl` — when a function is fully annotated, bind the
  recursive occurrence to the __generalised__ annotated scheme. (The fix.)
- `ty.py compose` / `types.lark subComposeRange` — drop a composed binding
  `k ↦ k`. It is the identity map, so dropping it is sound and total; it is why
  the symptom was an infinite loop rather than a diagnosis. (The guard.)

Mirrored into `self/types.lark` and `self/infer.lark` in the same commit.

__Witness — the whole point.__ Every differential returned to its pinned value
with *both* implementations changed:

| target | pinned | after |
|--------|--------|-------|
| `infertest` | 42 / 0 / 3 | __42 / 0 / 3__ |
| `typechecktest` | 42 / 0 / 3 | __42 / 0 / 3__ |
| `cektest` | 35 / 0 / 14 | __35 / 0 / 14__ |
| `emittest` | 38 / 0 / 7 | __38 / 0 / 7__ |
| `lowertest` | 35 / 0 / 10 | __35 / 0 / 10__ |
| `emittactest` | 32 / 0 / 13 | __32 / 0 / 13__ |
| `opttest` | 128 / 0 / 52 | __128 / 0 / 52__ |

`typechecktest` is the load-bearing one: every accepted program still emits
byte-identical C, and every *rejected* program still produces a byte-identical
`type error:`. The repair changed no type and no diagnostic on the corpus. It only
made a program legal that previously did not terminate.

The fixpoint sha __does__ move — `infer.lark` and `types.lark` are compiler source,
so the C the compiler emits for itself necessarily changes. What must survive is
not the sha but the *closure*, and it does:

```
O5' ladder, 7,688-line optcompiler.lark, baked -O3, compiling its own source:
  c1.c  8f9596d9…   49536 lines, 1,519,608 bytes
  c2.c  8f9596d9…   49536 lines, 1,519,608 bytes
  c3.c  8f9596d9…   49536 lines, 1,519,608 bytes
  C1 == C2 == C3 byte-identical            (was f1dedfa9 / 1,512,018 bytes)
```

Re-pinned in `self/tests/BASELINES.md`. __The invariant is the closure, not the
sha__ — a pin that forbids the compiler's own source from ever changing is not a
correctness property, it is a freeze on the project.

#### C4 · A stale expectation (`07/tests/24_stringprims.lark`)

Not `src/`, but it belongs in the ledger. The test's expected output is embedded in
the file as a comment. Someone extended the test with three `float_to_bits` prints
and never grew the expectation, so `make -C 07 test` reported `1 failed` for weeks
and everyone learned to scroll past it. The first 13 lines had always matched. The
fix is three lines of comment; the suite is now __81 passed, 0 failed__.

Same disease as a stale pin, one level down: *an expectation that stops covering
the program stops being a claim about it.*



### The workarounds we did __not__ remove

`ecRev` (emit_c), `etcRev` (emit_tac_c), `lwPair` (lower) are general functions
pinned to concrete element types, for no reason a reader of those files could
guess. They are the scars of C3, from the months before it was diagnosed.

They stay. They are compiler source: un-pinning them would change the emitted C
and move the fixpoint sha, and they buy nothing now that the checker is fixed.
They are archaeology, and they are load-bearing evidence for what a language
limitation looks like from the inside — not an error message, but a small
deformation, repeated, in code that has no business knowing why.



## What this file is a precondition for

`SELFHOST.md`, `OPTIMIZE.md`, and eventually `PROVE.md` all rest on the oracle
being a fixed point. It isn't one, quite — it is a __tracked__ point, which is the
best that is actually available and is fine, *so long as the tracking exists*.

Before PROVE: this is why refinement types get prototyped in an `08/src` fork
rather than in `07/src`. A guarantees axis that also drifts the reference would be
proving things about a moving target, and the proofs would be worth what the
differential was worth while the oracle moved in silence.
