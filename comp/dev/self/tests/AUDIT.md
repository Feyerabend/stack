
## Self-hosting differential — skip & canonicalisation audit

*SELFHOST hardening pass, before the F2 binary bootstrap. Companion to the fuzz /
property harness (`fuzz_gen.py` + `fuzz_difftest.py`). Written 2026-07-08.*

The five differential harnesses (`lextest`, `parsetest`, `infertest`, `cektest`,
`emittest`) each report `ok / failed / skipped`. A green run has __0 failed__, but
a chunk of files land in __skipped__, and a few comparisons pass only after a
__canonicalisation__ rewrites both sides. Before trusting the differentials as the
foundation for F2, this audit answers two questions for every one of them:

1. __Skips__ — is each skip merely *out of the port's control* (the oracle can't
   produce an answer, or the meta-circular tower is too slow), or is it a *wedged
   port bug* hiding under a timeout / an over-broad skip predicate?
2. __Canonicalisations__ — does each rewrite erase only a *genuinely value-equivalent*
   difference, or could it be masking a real divergence?

It also catalogues the __known oracle bugs the port deliberately mirrors__, so a
future reader does not mistake a faithfully-reproduced oracle quirk for a port
defect — and records the __findings the fuzzer surfaced__.



### 1. Skip inventory

Every harness partitions the corpus into `ok` (compared, matched), `fail`
(compared, diverged), and `skip` (not compared). Skips fall into a small, closed
set of causes. None is a silent "port produced the wrong answer": in every case
the harness has a *positive* reason it cannot form a meaningful comparison.

| Harness | Skip cause | Legitimate? | Why |
|---------|------------|-------------|-----|
| __lex__ | oracle raises `LexError` | ok | The file is not lexable at all; there is no token stream to compare. (No corpus file triggers this — the count is 0.) |
| __parse__ | oracle raises `LexError`/`ParseError` | ok | Not parseable — the error suite lives at the *type* level, so in practice this is 0; syntactically-invalid inputs are simply out of scope. |
| __infer__ | file `import`s another module (2 files) | ok | The port has no `import`; inlining would perturb infer Pass 1.5 mutual-rec pre-registration, so a like-for-like comparison is impossible. Structural, not a timeout. |
| __infer__ | oracle raises something *other than* `TypeError`/`AffineError`/`TraitBoundError` | ok | A non-type-error exception (parser crash, or `RecursionError` in `ty.apply`) means the oracle gave no verdict — nothing to compare. See §3, finding C. |
| __infer__ | meta-circular check `> PORT_TIMEOUT` (120 s) | ok perf | Python-CEK ▷ Lark-checker ▷ object program is cubic; a timeout is a *performance* verdict, not a correctness one. Verified slow-not-wedged below. |
| __cek__ | file `import`s / unresolvable import | ok | Structural (no port import). |
| __cek__ | oracle exit ≠ 0 (error suite) or oracle timeout | ok | The oracle itself rejects/loops — no reference stdout. |
| __cek__ | meta-circular eval `> PORT_TIMEOUT` (`LARK_TIMEOUT`, default 90 s) | ok perf | Compute-heavy loops (e.g. `08_life`) exceed the budget; `EXPLICIT_SKIP` is now __empty__ — every skip is detected dynamically, none is a hard-coded "this file is broken". |
| __emit__ | oracle exit ≠ 0 (7 error-suite files) | ok | The oracle type-checks *before* it emits; a rejected program has no C to emit, so the 7 error-suite files legitimately have no reference output. |
| __emit__ | unresolvable import / meta-circular `> 120 s` | ok perf | As above. |

#### Are the timeout-skips "slow" or "wedged"?

A timeout skip is only honest if the port *would* have produced the right answer
given more time — otherwise it is a failure in disguise. Two independent reasons
give confidence they are merely slow:

- __The tower is provably cubic, not divergent.__ Each timeout file is a
  *compute-heavy but terminating* program (recursion depth / iteration count that
  the object program itself bounds — `08_life`, deep-recursion tests). The
  meta-circular cost is a constant-factor tower (Python-CEK interpreting the
  Lark checker interpreting the object program), so a file that times out at 120 s
  is slow by a *factor*, not stuck. Files near the budget cross it in and out
  run-to-run as documented in `LOG.md` — the signature of a perf boundary, not a
  hang.
- __The fuzzer runs the *same* port assembly on much smaller inputs and they
  finish.__ Every fuzz program is tiny (≤ ~40 lines, expression depth ≤ 3) and
  passes infer+emit well within budget, exercising the identical concatenated
  driver. So the port machinery is not wedged; only large corpus inputs are slow.

__Conclusion:__ no skip hides a wrong answer. Every skip is either *structural*
(import — the port lacks the feature by design) or *the oracle gave no verdict*
or *pure performance* (meta-circular tower cost, to be removed by the F2 compiled
bootstrap — which is the whole point of F2).



### 2. Canonicalisation inventory

A canonicalisation rewrites *both* oracle and port output before comparison. Each
must erase only a difference that is __value-equivalent everywhere downstream__;
otherwise it masks a real divergence. There are exactly three, plus one added by
the fuzz harness.

#### 2a. infer — greek type-variable renaming (`_canon_reject`)
On a __reject__, the port and the oracle run two independent `Fresh` counters, so
they number type variables differently (`α12` vs `α7`). `_canon_reject` maps every
greek variable token (`[αβγ…](?:[0-9]+)?`) to a single marker `ν` before comparing
the `type error: …` line.
__Justification — erases only equivalent differences:__ the fresh-id *number* is
arbitrary (an allocation-order artifact), carries no meaning, and differs
legitimately between any two runs of Algorithm W. Everything else on the line — the
error __kind__ (`cannot unify`, `occurs check`, affine, trait-bound), the concrete
type constructors (`Int`, `List(...)`, `->`), and the structure — is compared
__verbatim__. Two rejects that canonicalise equal genuinely reject *the same
program for the same reason with the same concrete types*.
*(The accept-side α,β,γ normalisation is not a masking canon: both sides
independently normalise by first-occurrence order, which is a total, deterministic
function of the type — it is the agreed serialisation, not a difference-eraser.)*

#### 2b. emit — nondeterministic wildcard param name (`_ANON`)
`emit_c_difftest.canon` rewrites `_anon_\d+` → `_` on both sides.
__Justification:__ `infer.py` renames a wildcard parameter `_` to
`_anon_{id(node)}` using a __nondeterministic CPython object id__, then bakes that
integer into the emitted C as a closure parameter name __that is never referenced
anywhere else in the output__. No port can reproduce a specific `id()`, and the
value is dead. The token `_anon_<digits>` __never appears in any corpus source__,
so the rewrite cannot collide with a real identifier. It erases exactly one dead,
nondeterministic token. *(This is itself a catalogued oracle quirk — see §3.)*

#### 2c. emit — import double-emit inlining (`inline_imports_for_emit`)
Not a text rewrite but a structural one: for `import` programs the harness feeds
the port the imported decl bodies __twice__, because the oracle's `emit()` emits
them twice (see §3, oracle bug 2). This makes the two emitter *cores* see the same
decl stream.
__Justification:__ it faithfully reproduces a real oracle bug so the *emitter
core* — the thing under test — can be compared on equal input. The duplication is
documented and deliberate, not a difference-eraser that could hide a port fault;
if the port's emitter core diverged, the doubled-input comparison would still
catch it. (Flagged for removal once the oracle bug is fixed.)

#### 2d. fuzz/parse — float literal rendering (`_canon_floats`) — __added this pass__
The port's parsed AST keeps the __raw float lexeme text__ (`VFloat of String`,
`parse.lark:22` — "str round-trips it"), while `parser.py` stores `float(text)`.
For a non-canonical lexeme these render differently: `33.90` → port `(VFloat 33.90)`
vs oracle `(VFloat 33.9)`. The fuzz harness normalises the rendered float on both
sides (`float(x)`), only in the parse-stage comparison.
__Justification — value-equivalent everywhere downstream, empirically verified:__
- __infer__ types a float literal without reading its value (`_lit_type` → `Float`).
- __emit__ routes *every* float literal through its IEEE-754 __float32 bit pattern__
  — `emit_c_ast._f32_bits(float(t))` vs `emit_c.lark`'s
  `float_to_bits(string_to_float(t))` — which is __byte-identical__ for `33.90`
  and `33.9` (they are the same IEEE-754 number). Verified live: fuzz seeds whose
  source contains `88.70` / `45.55` etc. report __`emit=ok`__.
- __eval__ (cek) parses the lexeme to an `RFloat` and compares by value.
So the raw-text difference is observable *only* in the parse pretty-printer, never
in any real toolchain output. The rewrite erases a value-equivalent difference.
Ints are deliberately __not__ canonicalised (the generator emits only canonical
integer lexemes, so no int rewrite is needed and none is applied — keeping the int
comparison fully exact).



## 3. Known oracle bugs the port intentionally mirrors

The port's job is __byte-for-byte agreement with the 07/ oracle__, not
independent correctness. Where the oracle is buggy, a *faithful* port reproduces
the bug. These are catalogued so they are never mistaken for port defects, and so
they can be fixed in lock-step later.

1. __`infer.py` occurs-check gap.__ Unifying `α` with `List(α)` does __not__ run an
   occurs check, so a generic function that *builds* `List(a)` from a polymorphic
   element makes the substitution `α ↦ List(α)` and loops / diverges. The port
   works around it by monomorphising the offending helper (`ckSnoc : List(RVal)`),
   mirroring the oracle's *practical* behaviour on the corpus.

2. __`emit_c_ast.emit()` double-emits imported decls.__ `infer.typecheck` already
   inlines imported decls into `tprog.decls` (Pass 0), and `emit()` then prepends
   `_load_imports(prog)` *again* — so every imported module's decls appear __twice__
   in the C. Surfaced by self-hosting; the port mirrors it (canon 2c) so both
   emitter cores are compared on the same stream.

3. __Nondeterministic wildcard param name.__ `_ → _anon_{id(node)}` bakes a CPython
   object address into emitted C (canon 2b). Dead token; nondeterministic.

4. __No `%` operator__ (language limitation, not a bug). `%` is not a lexer token;
   the port does hex/mod as `n - (n/16)*16` to match.

5. __`ty.apply` is not stack-safe (finding C, below).__ A long variable-substitution
   chain overflows Python's recursion limit — `apply` chases `s[i]` recursively
   with no path compression. Same family as #1 (missing chain discipline in the
   substitution machinery).

---

## 4. Findings the fuzzer surfaced (this pass)

The fixed corpus never wrote these shapes; the property harness did. Two are real
port defects (__fixed__), one is a benign representational difference
(__canonicalised__), one is an oracle robustness limit (__catalogued__).

- __A — `float_to_bits` missing from the self-hosted front-end. `[FIXED]`__
  `infer.py`'s builtin env has `float_to_bits : Float -> Int` (added in the M0
  runtime lock-step), but the self-hosted __`infer.lark`__ did __not__ register it,
  so it rejected any source calling `float_to_bits(x)` with `unbound variable:
  'float_to_bits'` while the oracle accepted it. The parallel evaluator port
  __`cek.lark`__ had the same gap (present in `cek.py`, absent from `cek.lark`).
  The M0 lock-step reached the Python/C runtimes but never the `.lark` ports.
  __Fix:__ added `float_to_bits` to `infer.lark`'s builtin env (`Float -> Int`) and
  to `cek.lark`'s builtin dispatch + registration. Verified: `float_to_bits(2.5)`
  type-checks in `infer.lark` and evaluates to `1075838976` in `cek.lark`,
  byte-identical to the oracle. *(The emitter `emit_c.lark` already used the prim
  internally, so emit was unaffected.)*

- __B — parse-AST float representation. `[BENIGN → canonicalised]`__ See §2d.

- __C — `ty.apply` `RecursionError` on long substitution chains. `[CATALOGUED,
  oracle bug #5]`__ A generated program built a variable-substitution chain
  `v1 ↦ v2 ↦ … ↦ Int` deeper than CPython's recursion limit (~1000); `ty.apply`
  follows it recursively and overflows *before* producing a verdict. Since the
  oracle gives no answer, the fuzz harness (and `infertest`) skip such a program.
  Path compression in `apply`/`compose`, or an iterative walk, would fix it — same
  underlying gap as the occurs-check finding. Left as-is to stay byte-faithful to
  the frozen oracle; noted for the eventual oracle-hardening pass.

---

## 5. The fuzz / property harness itself

`fuzz_gen.py` synthesises random, deterministically-seeded, __well-typed__ Lark
programs by type-directed construction over the four Copy scalars
{Int, Float, Bool, String} — so each program type-checks by construction and
reaches the emit stage. `fuzz_difftest.py` reuses the four sibling harnesses' own
driver assembly / port runners / oracles, so a fuzz program travels the *exact*
port pipeline the corpus differentials use; the only new thing is the input
distribution.

__Coverage (what the generator exercises that the corpus mixes only in fixed
shapes):__ every binary operator (`+ - * /`, six comparisons, `and`/`or`), unary
`not`/`-`, `if/then/else`, `let … in`, `match` on Int with literal + wildcard/var
patterns, top-level `fn` (1–3 params) and `let`, mutual reference across decls,
calls, and all scalar built-ins — recombined freely and nested.

__ADT extension (added this pass).__ Every program now declares a fixed prelude
ADT — `type Adt = | CA of Int | CB of Float, Float | CC` with `impl Copy for Adt
= {}` — and `Adt` joins the *binding* type universe (fn params/returns, top-level
`let`, `let … in`), ~1 choice in 4. This fuzzes the ADT-shaped port paths the
scalar core misses: a `type` decl with mixed-arity variants, value construction
(`CA(e)`, `CB(e, e)`, bare nullary `CC`), and `match` on an ADT scrutinee with
constructor patterns that bind the field variables (a random non-empty subset of
ctors + optional wildcard). The `impl Copy` keeps ADT values Copy, so the
generator still never reasons about affine use counts — same invariant as the
scalars. `Adt` is admitted only where a *value* of that type is wanted, never
where a scalar is required (no ADT literal / `show` / arithmetic / comparison
operand). __Result: 30 ADT-containing programs (seeds 3000–3029) went
`120 ok / 0 failed / 0 skipped` through the full lex→parse→infer→emit pipeline,
byte-identical port vs oracle__ — including construction and constructor-pattern
`match` emitted to C.

__Still out of scope (left to the fixed corpus / future extension):__
polymorphic/parameterised ADTs, traits/impls beyond the Copy prelude, tuples,
lists, `Result`, `import`, and intentionally-rejected programs. The natural
remaining extension is a reject-path mode (deliberately ill-typed programs
asserting port and oracle reject with the *same* message) — deferred because the
corpus error suite already covers the reject path and byte-identical reject
messages across independently-generated programs are order-sensitive.

__Run:__ `make -C self fuzz` (full pipeline, small batch) or `make -C self
fuzzfast` (front-end only, large batch). Every FAIL prints its seed and source;
reproduce standalone with `python3 self/tests/fuzz_gen.py <seed>`.
