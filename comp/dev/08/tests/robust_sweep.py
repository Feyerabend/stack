"""
Robustness sweep — the refinement checker, pointed at all of 07's real corpus.

`prove/` is a suite written *for* the checker: every file in it was authored by
someone who knew what the checker could do. This sweep is the opposite, and that
is its whole value — 45 files of real Lark (`09_parser`, `08_life`, the stdlib,
the torture test, every reject fixture), none of which has ever heard of a
refinement. It answers three questions the `prove/` suite structurally cannot:

  1. **Does the checker crash?**  On any input, for any reason, a Python traceback
     is a bug. A refinement checker runs *after* the type checker, so it must be
     able to say "this does not typecheck" for EVERY reason the type checker has —
     including the rare ones. (This sweep is how `TraitBoundError`, `LexError` and
     `UnifyError` were found missing from the handler: the errors/ fixtures crashed.)

  2. **Does it terminate?**  Refinement-free code still generates obligations —
     every `/`, every `string_index` — and they are generated from code nobody
     shaped to be easy. The solver has budgets (`solver.MAX_CLAUSES`, `MAX_OMEGA`);
     this is where they get exercised on programs rather than on test vectors.

  3. **What does it say about honest code?**  Pinned below, per file. Two rows are
     the interesting ones, and they are TRUE POSITIVES on Lark's own samples:

         07/samples/05_expr.lark    | Div(a, b) => eval(a) / eval(b)
         07/samples/09_parser.lark  | Div(a, b) => eval(a) / eval(b)

     Both evaluators really can divide by zero — `Div(Num(1), Num(0))` is a term
     you can build and neither program checks for it. The checker is not being
     pedantic here; it is right, and it found it in code that has been running for
     the whole project.

A `proved: 0` row is not a failure. It means the file raises no obligations at all,
which is what "no refinements, no division, no indexing" is supposed to look like.

    python3 08/tests/robust_sweep.py         # or: make -C 08 robust

⛔ Reads 07/. Writes nothing, anywhere. (PROVE.md §0.1)
"""

from __future__ import annotations
import pathlib, sys, time, traceback

ROOT = pathlib.Path(__file__).resolve().parent.parent     # .../lark/08
LARK = ROOT.parent
SRC  = ROOT / "src"

sys.path.insert(0, str(SRC))
# 09_parser and 21_deeprec are deep; the recursion limit is a property of CPython,
# not of the checker, and the CLI raises it for the same reason.
sys.setrecursionlimit(20000)

import refine                                             # noqa: E402


# The verdict for every file in 07's corpus.  ("proved", n) / ("unproved", k, n) /
# ("rejected",) — the last meaning the front end threw it out before the checker ran,
# which for the errors/ fixtures is the correct answer.
EXPECT: dict[str, tuple] = {
    "07/samples/01_mergesort.lark":        ("proved", 1),
    "07/samples/02_bst.lark":              ("proved", 0),
    # This verdict MOVED, and the move is the finding.  `divides(d, n) = n / d * d == n`
    # is a function whose whole body is a COMPARISON, and a comparison used to be
    # TRANSLATED into a formula rather than WALKED — so the division inside it was never
    # visited and the file reported 0 obligations.  Zero.  A trial-division sieve, and the
    # checker had never once looked at the division.
    #
    # It looks at it now, and cannot prove it, which is the truth: `d : Int` does not say
    # `d /= 0`.  Every caller passes d >= 2 and the program is fine at run time, but the
    # SIGNATURE is what a modular checker gets to read, and this one is silent.  The fix
    # is a contract (`d : {v : Int | v /= 0}`), not a cleverer checker — and it is 07's
    # frozen code, so the honest verdict is `unproved` and it stays that way.
    "07/samples/03_primes.lark":           ("unproved", 1, 1),   # n / d, inside a Bool
    "07/samples/04_queens.lark":           ("proved", 0),
    "07/samples/05_expr.lark":             ("unproved", 1, 1),   # eval(a) / eval(b)
    "07/samples/06_rle.lark":              ("proved", 0),
    "07/samples/07_hanoi.lark":            ("proved", 0),
    "07/samples/08_life.lark":             ("proved", 0),
    "07/samples/09_parser.lark":           ("unproved", 1, 1),   # eval(a) / eval(b)
    "07/tests/01_hello.lark":              ("proved", 0),
    "07/tests/02_arithmetic.lark":         ("proved", 0),
    "07/tests/03_recursion.lark":          ("proved", 0),
    "07/tests/04_tailrec.lark":            ("proved", 0),
    "07/tests/05_adt.lark":                ("proved", 0),
    "07/tests/06_lists.lark":              ("proved", 0),
    "07/tests/07_result.lark":             ("proved", 1),
    "07/tests/08_traits.lark":             ("proved", 0),
    "07/tests/09_modules/main.lark":       ("proved", 0),
    "07/tests/09_modules/shapes.lark":     ("proved", 0),
    "07/tests/10_closures.lark":           ("proved", 0),
    "07/tests/11_tree.lark":               ("proved", 0),
    "07/tests/12_tuples.lark":             ("proved", 0),
    "07/tests/13_floatops.lark":           ("proved", 0),
    "07/tests/14_stringops.lark":          ("proved", 0),
    "07/tests/15_tailrec2.lark":           ("proved", 0),
    "07/tests/16_stdlib.lark":             ("proved", 0),
    "07/tests/17_mutual_rec.lark":         ("proved", 0),
    "07/tests/18_litpat.lark":             ("proved", 0),
    "07/tests/19_intoverflow.lark":        ("proved", 0),
    "07/tests/20_floatprec.lark":          ("proved", 0),
    "07/tests/21_deeprec.lark":            ("proved", 0),
    "07/tests/22_io_seq.lark":             ("proved", 0),
    "07/tests/23_show_impl.lark":          ("proved", 0),
    "07/tests/24_stringprims.lark":        ("unproved", 7, 7),   # unguarded index/slice
    # 4 → 5 obligations when `synth` learned to walk a LAMBDA's body (the eighth false
    # proof, found by tests/invariants.py).  The new one is the `x / 2` inside
    # `filter(fn(x) => (x - (x / 2) * 2) == 0, xs)` — a division the checker had never
    # once looked at, in a file called `torture`.  It proves (the divisor is 2); the 3
    # that do not are the string ones, unchanged.
    "07/tests/25_torture.lark":            ("unproved", 3, 5),
    "07/tests/Stdlib.lark":                ("proved", 0),
    "07/tests/errors/01_affine.lark":      ("rejected",),
    "07/tests/errors/02_nocopy.lark":      ("rejected",),
    "07/tests/errors/03_missing_bound.lark": ("rejected",),
    "07/tests/errors/04_nonexhaustive.lark": ("proved", 0),      # no exhaustiveness check
    "07/tests/errors/05_undef_ctor.lark":  ("rejected",),
    "07/tests/errors/06_matchfail.lark":   ("proved", 0),        # a runtime failure, not a static one
    "07/tests/errors/07_traitbound.lark":  ("rejected",),
    "07/tests/errors/08_show_fn.lark":     ("rejected",),
    "07/tests/errors/09_lambda_mono.lark": ("rejected",),
}


def verdict(path: pathlib.Path) -> tuple:
    """A crash is a CRASH — it is never folded into a verdict."""
    try:
        r = refine.check_program(str(path))
    except refine.FRONTEND_ERRORS:
        return ("rejected",)
    except refine.REFINE_ERRORS as e:
        return ("error", str(e))
    except RecursionError:
        return ("CRASH", "RecursionError")
    except Exception:
        return ("CRASH", traceback.format_exc(limit=3))
    if r.failed:
        return ("unproved", len(r.failed), r.total)
    return ("proved", r.proved)


def main() -> int:
    files = sorted(p for d in ("07/tests", "07/samples")
                   for p in (LARK / d).rglob("*.lark"))
    ok = fail = crash = 0
    t0 = time.time()

    print(f"robustness sweep — the checker over 07's {len(files)} real files\n")

    for f in files:
        rel  = str(f.relative_to(LARK))
        got  = verdict(f)
        want = EXPECT.get(rel)

        if got[0] == "CRASH":
            print(f"  CRASH {rel:<34} {got[1].splitlines()[-1] if got[1] else ''}")
            crash += 1
        elif want is None:
            print(f"  NEW   {rel:<34} {show(got)} — not in EXPECT")
            fail += 1
        elif got == want:
            print(f"  ok    {rel:<34} {show(got)}")
            ok += 1
        else:
            print(f"  FAIL  {rel:<34} want {show(want)}  got {show(got)}")
            fail += 1

    missing = [k for k in EXPECT if not (LARK / k).exists()]
    print(f"\n  {ok} ok, {fail} fail, {crash} crash    ({time.time() - t0:.1f}s)")
    for k in missing:
        print(f"    MISSING  {k}")

    if crash:
        print("\n  THE CHECKER CRASHED. A traceback is never an answer — every input\n"
              "  it cannot handle must come back as a message the language already has.")
        return 1
    if fail or missing:
        print("\n  robustness sweep FAILED")
        return 1
    print("  sweep clean — no crashes, and the verdicts on real code are where they were.")
    return 0


def show(v: tuple) -> str:
    match v:
        case ("proved", n):
            return f"{n} proved"
        case ("unproved", k, n):
            return f"{k} of {n} unproved"
        case ("rejected",):
            return "rejected by the front end"
        case ("error", t):
            return f"refinement error: {t}"
    return str(v)


if __name__ == "__main__":
    sys.exit(main())
