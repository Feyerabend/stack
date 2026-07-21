
## Strand — the SELF-HOSTING FIXPOINT   RE-VERIFIED + ARTICULATED

> __Status:__ the F2 fixpoint was __re-run this session and closes byte-identical__ —
> `python3 self/tests/bootstrap.py` → `FIXPOINT REACHED — C1==C2==C3 byte-identical (49a4921c53b2)`,
> matching the recorded F2 baseline `49a4921c`. The harness __suffices__ (DoD 1): it prints the hash
> every run and returns non-zero + `FIXPOINT BROKEN` on any drift. It checks the *fixpoint property*
> (C1==C2==C3 self-consistency), NOT equality against a pinned baseline — deliberately, because the
> project's own rule is that an intentional `07/src` edit is *expected* to move the sha and is
> re-confirmed by a human against `LOG.md`; a hard pin would fight that workflow. Second of the
> AFFINE→FIXPOINT→BOOK sequence. Story: `../../../LOG.md` ▲ STRAND-FIXPOINT. The
> is/is-not below is book-ready (DoD 2); __feeding ch13/ch15/interlude with the Thompson caveat is the
> remaining item, done when the book reaches it.__

__A different epistemic kind from the other strands.__ denot / solver / vdeep /
affine are *kernel-checked* soundness proofs. This one is an __empirical
reproducibility property__ — verified by the *build*, not by lcore — so it lives here
as an *exhibition* strand: the property already holds; what is missing is its
articulation and, more importantly, its __limit__.

__The property (DONE, not to-do).__ The Lark-written compiler, compiled by itself,
reproduces itself __byte-for-byte__: `stage1` emits `C1`, `C2` compiles it to `C2`,
`C3` to `C3`, and `C1 == C2 == C3`. Three fixpoints of increasing strength are already
closed (`../../../SELFHOST.md`): __F2__ (self-hosting fixpoint, closed 2026-07-08),
__F2⁺__ (the *typechecking* compiler's native fixpoint), and the __O5′__ optimizing
fixpoint. Verified by `self/tests/bootstrap.py` and re-runnable:

```
make -C self bootstrap       # F2  — self-hosted compiler reproduces its own C
make -C self bootstrap-tc    # F2⁺ — native fixpoint C1==C2==C3 (heavy)
```

### What it is — and what it is NOT (the whole point)

The fixpoint is __translation validation in the large__: not "the compiler is
correct," but "the compiler is a *fixed point of self-application*" — a strong
self-consistency witness. It says the bootstrap is stable and the binary is
__reproducible__: rebuild from clean and you get the same bytes.

It does __not__ say the binary is *trustworthy*. This is Ken Thompson, *Reflections on
Trusting Trust* (1984), made concrete: a compiler carrying a self-reproducing backdoor
is __also__ a fixpoint of self-application — byte-identity is exactly the property such
a backdoor preserves. So the fixpoint closes the *stability* question and leaves the
*trust* question wide open. Naming that gap honestly is the deliverable, not hiding it
behind a green checkmark.

That places it precisely in the book's trust taxonomy:
*types say meaningful · refinements say safe · the metatheory says the calculus is
sound · the fixpoint says the build is stable — and Thompson says stability is not
trust.*

### What this strand owes (small — the machinery exists)

1. __A one-line verifier target__ if not already exposed: `make fixpoint` that runs the
   bootstrap, diffs the stage hashes, and __fails loudly on drift__ (record the hash so
   a regression is visible). Check whether `self/tests/bootstrap.py` already suffices
   before adding anything.
2. __The writeup__ — this document's "is/​is-not" section, sharpened, as the source for
   the book beat: an __interlude__ or a section in ch13/ch15 on Trusting Trust. This is
   where the fixpoint earns its place in *What the Machine Can Promise* — as the
   property that shows a promise the machine __cannot__ make.
3. __The TCB line:__ the fixpoint pins one edge of "what is still trusted" (ch15) — the
   bootstrap C compiler beneath Lark remains in the trusted base; the fixpoint does not
   remove it, it *localizes* it.

### Definition of done

1. `make fixpoint` (or the documented `bootstrap` path) reproduces the recorded hash
   and fails on drift.
2. This PLAN's is/​is-not is tight enough to lift into the book verbatim.
3. `strands/SUMMARY.md` gains the row (flagged *empirical, not kernel-checked*);
   `LOG.md` gets the dated note.
4. Feeds ch13/ch15/interlude with the Thompson caveat — done when the book reaches it.

*Cost: low.* Unlike affine (a real proof), this is exhibit-and-articulate. It is second
in the sequence because it is the natural bridge from the proof work back into the
book: affine → fixpoint → book.
