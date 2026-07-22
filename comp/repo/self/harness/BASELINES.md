# Frozen baselines — the self-hosting compiler

Pinned reference values for the self-hosted Lark toolchain at the freeze point.
Any later change must keep every differential green and every
*output-neutral* artifact byte-identical. If a number here moves, either a real
regression happened or the change is genuinely output-changing (then update this
file in the same commit, with the reason).

Regenerate all with `make <target>`; each is meta-circular (slow), so run
**one at a time** (siblings share fixed temp-driver filenames).

## ⚠ Which of these numbers are about the compiler, and which about the machine

Read this before treating any count below as a contract. The numbers are of two
kinds, and only one kind is a claim about Lark.

**Invariant — true on any machine.** These are the actual results:

- **`0 failed`, everywhere.** A *failure* means the Lark implementation and the
  Python reference disagreed about a program they both finished. That is a fact
  about the compiler and holds on a Raspberry Pi.
- The **accept/reject verdicts** in the error suite.
- The **fixpoint shas** (`8f9596d9`; C1 == C2 == C3) — the emitted C is
  deterministic, so a different machine reproduces the same bytes. (The *binary*
  is not: Mach-O carries a UUID and paths. That is noted where it appears.)

**Environment-dependent — true of *this* machine, on the day it was pinned.**
These are budgets, and the numbers that fall out of budgets:

- **`LARK_TIMEOUT`** is wall clock. The port is an interpreter running an
  interpreter, so a per-file budget is unavoidable — but it measures the box, not
  the compiler.
- **Therefore the `ok`/`skip` split moves with the box** — but only partly, and it is
  worth knowing which part. Of `cektest`'s 14 skips, **3 are timing** (files this
  machine could not finish in 90 s: a faster box turns them into `ok`, a slower one
  does the reverse) and **11 are structural** (the oracle itself exits non-zero: the
  error suite, and two import fragments with no `main`). No machine, however fast,
  turns a structural skip green. The count is a report, not a promise. What *is*
  promised is that of the files that ran, none disagreed.
- **And measure on a quiet box.** These harnesses are slow enough that anything else
  running is contention, so a timing skip can appear out of nowhere and look exactly
  like a pin that has gone stale. They are not the same thing and the fix is opposite:
  a timing skip means re-run, a stale pin means re-pin. Re-running under the *same*
  interference and getting the same number proves nothing — a reproduced number is not
  an independent one if the interference was reproduced with it.
- **Arena sizes** (12–15 GB, lazily committed) and the `ulimit -s` bump for
  macOS's 8 MB stack.

Consequently: **a moved `ok`/`skip` boundary is not a regression — a `fail` is.**
Every harness now reports a timeout as a *skip with a reason*, never as a failure,
so that a slow machine cannot masquerade as a disagreement. (Before 2026-07-12,
`lextest` and `parsetest` alone counted a timeout as `FAIL`. It bit exactly as you
would expect: at the 300 s default `parsetest` reported a red on `infer.lark`; at
900 s the same code, unchanged, reported 52/0/0.)

If you are re-pinning on new hardware: raise `LARK_TIMEOUT` until the skip count
stops falling, and expect these counts to be *at least* as green as the table.

## Differential test counts

| target          | result           | what it proves                                              |
|-----------------|------------------|-------------------------------------------------------------|
| `lextest`       | **52 ok / 0 fail / 0 skip** | `lex.lark` == `lexer.py` (token streams, incl. line/col). The corpus is every `.lark` in `tests/`, `samples/` and the compiler's own source, so it **grows with the compiler** — the old "46/46" was pinned when the compiler was one module. Re-pinned 2026-07-11 when the byte/codepoint fix (below) turned the last 3 failures green. Slow: use `LARK_TIMEOUT=900` (`opt.lark` alone is 1,770 lines). |
| `parsetest`     | **52 ok / 0 fail / 0 skip** | `parse.lark` == `parser.py` (syntax trees). Same growing corpus as `lextest`. **Newly pinned 2026-07-12** — it had no row here, which is how a timeout sat unnoticed: at the 300 s default it reported a FAIL on `infer.lark` (1,200 lines through a parser written in Lark); at `LARK_TIMEOUT=900` it is 52/0/0. The `Makefile` now defaults it to 900. |
| `infertest`     | **42 ok / 0 fail / 3 skip** | `infer.lark` == `infer.py` (Algorithm W + affine + traits); 3 skips = the 3 `import` files (`09_modules/main`, `16_stdlib`, `25_torture`) |
| `cektest`       | **35 ok / 0 fail / 14 skip** | `cek.lark` == `cek.py` (evaluator). Re-pinned 2026-07-13 (was 34/0/15). The 14 skips are **11 structural** — `oracle exit 1`: the 9-file error suite, plus `09_modules/shapes.lark` and `Stdlib.lark`, which are import fragments with no `main` of their own — and **3 timing**: `04_tailrec`, `15_tailrec2` and `04_queens` exceed the meta-circular eval budget (`LARK_TIMEOUT`, default **90 s**; raise it and they go green). Held at 35/0/14 across four runs in two load conditions, with a file-for-file identical skip list — which is what earns a pin, as against `emittest` above, where the arithmetic itself had gone stale. Earlier history: 33/0/15, then 33/1/15 once `25_torture` (added a day after that pin) was actually run against it. The red was the **harness's** import-inlining, not the port — see *Closed* below; fixing it made `25_torture` the 34th green. |
| `emittest`      | **38 ok / 0 fail / 7 skip** | `emit_c.lark` == `emit_c_ast.py` (C from syntactic AST); 7 skips = error suite (no C to compare). Re-pinned 2026-07-12: was 37/0/7, which added up to 44 — one short of the 45-file corpus, because the pin predates `25_torture` being added to it. The 45th file had been passing the whole time; it was the *pin* that had gone stale, not the port. A number here that no longer covers the corpus has quietly stopped being a claim about it — the same drift the `cektest` row records. |
| `typechecktest` | **42 ok / 0 fail / 3 skip** | the **typechecking** compiler: accept→oracle-identical C, reject→oracle-identical `type error:`; strictly stronger than emittest (the 7 error-suite skips become live tests); 3 skips = the 3 `import` files |

`typechecktest` dominates `emittest`: same acceptance C **plus** the reject
diagnostics. It is the load-bearing freeze witness.

## The emit-only fixpoint (the bootstrap)

`make bootstrap` — the emit-only compiler (`lex + parse + emit_c`,
1858 lines) reproduces its own emitted C.

| artifact                     | sha (first 8) | note                                              |
|------------------------------|---------------|---------------------------------------------------|
| C1 == C2 == C3               | `49a4921c`    | emitted-C fixpoint, byte-identical across 3 stages |
| stage2 binary == stage3      | *(not pinned)* | Mach-O `LC_UUID` + embedded paths are nondeterministic; only the C-source fixpoint is asserted |

**Re-pin note (2026-07-08, the emitter join fix):** the C sha moved
`2ce6a281 → 49a4921c` *intentionally* (BASELINES invariant #2). `lark/emit_c.lark`'s
`ecJoinNL` was changed from an O(n²) right-fold to a balanced bottom-up pairwise
join (`ecJoinPairs`) — output-identical (string concat is associative), verified
by `emittest` 37/0/7 and `typechecktest` 42/0/2 staying byte-identical. But the
compiler's *own source* now contains that new code, so the C it emits for itself
differs, and the ladder settles at a new fixpoint. The **arena requirement
collapsed**: the emit-only self-compile peaks at **177 MB** (was ~3 GB) and the
fixpoint closes at a **512 MB** arena (was 8 GB reserved). `bootstrap.py` still
defaults to a large arena; pass `LARK_ARENA_SIZE` to run it small.

## The native fixpoint of the *typechecking* compiler (closed 2026-07-08)

`make bootstrap-tc` (`harness/bootstrap_tc.py`) — the full six-module
typechecking compiler (`lex + parse + types + tast + infer + emit_c` + `tcGate`,
3562 lines) type-checks **its own source** and reproduces its own emitted C.

| artifact        | sha (first 8) | note                                                      |
|-----------------|---------------|-----------------------------------------------------------|
| C1 == C2 == C3  | `829410dc`    | emitted-C fixpoint (19415 lines), byte-identical across 3 native stages |

**Re-pin note (2026-07-12, stale pin — found by actually running the target):** the
sha moved `45c1982a → 829410dc` (18877 → 19415 C lines; assembled source 3562 → 3718
lines) because `lark/infer.lark` changed on 2026-07-11 (commit `1badfd5`), *after* the
previous pin was taken. This is the ordinary consequence the two re-pin notes below
already describe: the compiler's **own source** is an input to the self-compile, so
changing it moves the sha of the C it emits for itself. Not a regression — the
oracle-based differentials (`infertest` **42/0/3**, `typechecktest` **42/0/3**, which
compare against the unchanged Python `infer.py` rather than against the self-compile)
stayed byte-identical, which is what "output-neutral" means here. The fixpoint still
closes: C1 == C2 == C3.

The lesson is the mirror of `optcompilertest`'s above. That number was never written
down; this one was written down and then left to rot for three days while the source
moved underneath it. **A pin that is not re-checked is indistinguishable from a pin
that is wrong** — and it costs more, because it looks like a guarantee. Re-run
`make bootstrap-tc` whenever any of the six modules it assembles changes.

**How it closed (2026-07-08):** the join fix was only the
first wall. With it, parse+emit of the 3534-line source is 353 MB, but adding the
`infer` pass (the gated `tcGate`) overflowed the no-GC arena past **12 GB** —
Algorithm W's assoc-list `Subst` applied O(n) times and never freed. **Fix:**
`lark/types.lark` `applyScheme` now short-circuits when the scheme is *closed*
(`monoVarsAllIn(body, qs)` — every var bound by the quantifier list), returning it
unchanged instead of `apply(removeKeys(s,qs), body)`. Applying a substitution to a
closed (fully-generalised, top-level) scheme is provably the identity, so this is
**output-neutral** — `infertest` **42/0/2** and `typechecktest` **42/0/2** stayed
byte-identical. It removed the env-side O(env × |s|) multiplier that `applyEnv`
paid at every sub-expression: the tc self-compile went from **>12 GB overflow →
10.15 GB completing high-water**, closing the fixpoint (ran at a 14 GiB
lazily-committed arena for headroom; peak touched ~10.15 GB).

**Residual CLOSED (2026-07-09, balanced-tree `Subst`):** the substitution fix left a
subst-side multiplier — `substGet`/`apply` scanned the assoc-list `Subst` linearly,
and Algorithm W allocates fresh vars monotonically, so the list degraded to a chain
on exactly the keys unification looks up hardest (~O(n^1.9)). `lark/types.lark`'s
`Subst` is now an **Int-keyed Okasaki red-black tree** (`type Subst = SLeaf | SNode
of SColor, Subst, Int, Mono, Subst`): `substGet` is O(log n), `subInsert` rebalances,
and `compose`/`removeKeys` fold through `subInsert` (overriding on shared keys, so the
tree caps at distinct-key count instead of accumulating duplicate assoc entries).
**Output-neutral** — apply reads only the key→Mono mapping, so `infertest` **42/0/3**
and `typechecktest` **42/0/3** stayed byte-identical against the oracle. Effect: the
tc self-compile peak dropped **10.15 GB → 4.73 GB** (stage1, 58 s wall; measured
`/usr/bin/time -l ./stage1 < tc_compiler.lark`).

**Re-pin note (2026-07-09, balanced-tree `Subst`):** the bootstrap-tc emitted-C sha
moved `34a07692 → 45c1982a` (18549 → 18877 lines) *intentionally*, exactly as the
join fix did: the compiler's **own source** now contains the red-black-tree code,
so the C it emits for itself differs and the ladder settles at a new fixpoint
(C1==C2==C3 byte-identical). Not a regression — the oracle-based differentials
(`infertest`/`typechecktest`, which compare against the unchanged Python `infer.py`,
not the self-compile) stayed byte-identical, proving the change is output-neutral.

## Invariants for this strand

1. All six differential counts above stay exactly as written (or improve skips→ok).
2. `bootstrap` emitted-C sha stays `49a4921c` and `bootstrap-tc` stays `829410dc`
   **unless** the change intentionally alters emitted C — in which case re-pin here
   with the new sha and the reason. Note that editing *any* of the modules the
   self-compile assembles counts as intentionally altering emitted C: the compiler's
   own source is one of its inputs. Re-run the target rather than assuming.
3. The reject diagnostics stay oracle-identical (that is what makes it a compiler).

## Closed: `cektest` / `25_torture.lark` — the harness was wrong, not the port

Bisected 2026-07-11. **`cek.lark` was innocent**; the bug was in this directory,
in `cek_difftest.py`'s `inline_imports`.

The symptom: the port printed `()` where the oracle printed `10`, on

```lark
let io = print(io, int_to_string(length(xs))) in     (* xs = range(1, 11) *)
```

The cause: `25_torture.lark` defines its own `fn length(xs : List(Int))`, and
imports `Stdlib exposing (Option, None, Some, unwrap_or, map_opt, and_then,
pow_int, min_int, max_int, clamp_int)` — a list that does **not** include
`length`. But `Stdlib.lark:62` declares one anyway:

```lark
export fn length(s : String) : Int = string_length(s)
```

The port has no `import`, so the harness flattens multi-module programs by
inlining the module wholesale — and it appended *every* Stdlib decl, `exposing`
be damned, on the reasoning (written into the comment above `inline_imports`)
that hiding a name can only ever remove bindings and so cannot change an
accept-test's output. That reasoning is false when a hidden name **collides**:
both `length`s landed in one flat scope, the inlined one came last and won, and
`length(xs)` became `string_length` applied to a list — which yields `()`.

The minimal repro is 19 lines, and one declaration toggles it:

```lark
module Mini                                     (* Mini.lark *)
export fn helper(n : Int) : Int = n + 1
export fn length(s : String) : Int = string_length(s)     (* delete → port matches *)
```
```lark
module Main                                     (* main.lark *)
import Mini exposing (helper)                   (* NB: `length` not exposed *)

type List a = | Nil | Cons of a, List(a)
impl Copy for List(Int) = {}

fn length(xs : List(Int)) : Int =
  match xs with
  | Nil           => 0
  | Cons(_, rest) => 1 + length(rest)
  end

fn main(io : IO) : IO =
  let xs = Cons(7, Cons(8, Cons(9, Nil))) in
  print(io, int_to_string(length(xs)))          (* oracle 3 · port () *)
```

**The fix** (`inline_imports`, both copies): still inline the module whole — its
exported functions call each other (`spaces` calls `repeat_str`), so filtering the
body down to the `exposing` list would break them — but **α-rename** every module
top-level name that is *not* exposed to the importing file *and* collides with one
of that file's own top-level names (`length` → `stdlib__length`). The rename runs
off the lexer's token stream, so occurrences in comments and string literals are
left alone, and it preserves the name's case, because Lark reads a leading capital
as a constructor.

Only the two `cek_difftest.py` copies are patched. `emit_c_difftest.py` inlines the
same way but compares *emitted C*, where the oracle spells the imported decls out
under their original names; renaming there would break a green baseline to fix
nothing.

*Why nobody caught it:* `25_torture.lark` was added **2026-07-09**, a day after the
`cektest` baseline (33/0/15) was pinned, so it entered the corpus behind a frozen
number. It is also the one deep integration file — the only corpus member that both
imports a module and defines a common name of its own.

## Oracle thaws — the complete list

The Python reference is frozen; three times it was not. Every one is here.

| # | When | File | Change | Why it was unavoidable |
|---|------|------|--------|------------------------|
| 1 | the bootstrap (2026-07-08) | `cek.py` | new `read_all` primitive | the bootstrap compiler must read a whole program from stdin, and no existing primitive could |
| 2 | the bootstrap (2026-07-08) | `cek.c` | arena `static` → `malloc` | so `-DLARK_ARENA_SIZE` can reach multi-GB; no semantic change |
| 3 | **2026-07-11** | `cek.py`, `lexer.py` | **a String is UTF-8 bytes; a column is a byte offset** | the oracle contradicted *itself*: `string_index` returned a codepoint, `char_to_string` truncated to a byte, so the two stopped being inverses above U+007F. `parse.lark` rebuilds every string literal through that pair, so the self-hosted parser silently corrupted non-ASCII literals. C was already byte-oriented and correct; Python was the odd one out. Fixed by making Python agree. |

Thaw 3 is the only one where the **port was right and the oracle was wrong**, and
the only one no fixpoint could have caught (all three bootstrap stages corrupt
identically, so C1==C2==C3 still held). It re-pins `lextest` at 52/0/0; nothing
else moves, because the AST carries no positions and the corpus is otherwise
ASCII.
