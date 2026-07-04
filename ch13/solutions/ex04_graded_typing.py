"""
Chapter 13, Exercise 4(a)/(b) — solution code.

(a) Exhibit a well-graded derivation with two uses of a Copy (grade-omega)
binding — the kernel-checkable twin of  fn(x : Int) => x + x.
(b) Show that a use of a grade-0 (erased) binding is underivable: the
kernel rejects it, because GVar deliberately has no rule at G0.

How to run:   python3 ex04_graded_typing.py
Expected:     "PASS: omega_twice checked (exit 0)" and
              "PASS: grade-0 use rejected (exit 1)"

The graded model (lark-affine.lcore) has no arithmetic, so `x + x`
becomes its structural twin `let y = x in x`: a binding at grade omega
used once as the let's value and once more in the body. Both lookups go
through gv_herew, which leaves the grade at omega — in gplus terms the
two uses demand 1 + 1 = omega, and omega is what a Copy binding has.

The rejected term annotates a lookup in a context whose entry is G0.
The only head rules are gv_here1 (needs G1) and gv_herew (needs GW);
grade 0 matches neither, so the claim cannot check — the proof-level
twin of AffineError, and the exact mechanism by which GELam's demotion
makes the Chapter 13.5 capture counterexample underivable.

Success and failure are both read from the exit code: section 13.6 made
the kernel exit non-zero when any line fails, so "the claim checked" and
"the kernel rejected it" are machine-checkable facts, not impressions.
"""

from _harness import run_with_affine_prelude

# (a) Two uses of an omega binding: let y = x in x, with x : Int at GW.
#     Reading the leftover contexts: the value's lookup (gv_herew) leaves
#     x at GW; the body's lookup steps over the binder y (gv_there) and
#     uses x again (gv_herew); every context in the chain stays GW.
OMEGA_TWICE = (
    ":let omega_twice = ("
    "GELet (gext TInt GW gempty) (gext TInt GW gempty) (gext TInt GW gempty) "
    "G1 G1 TInt TInt "
    "(GEVar (gext TInt GW gempty) (gext TInt GW gempty) TInt "
    "(gv_herew gempty TInt)) "
    "(GEVar (gext TInt G1 (gext TInt GW gempty)) "
    "(gext TInt G1 (gext TInt GW gempty)) TInt "
    "(gv_there (gext TInt GW gempty) (gext TInt GW gempty) TInt TInt G1 "
    "(gv_herew gempty TInt))) "
    ": GExpr (gext TInt GW gempty) TInt (gext TInt GW gempty))"
)

# (b) A lookup in an erased (G0) context. gv_here1 produces evidence for
#     a G1 entry, and no rule produces evidence for G0 — the annotation
#     cannot be satisfied and the kernel must reject the line.
USE_ERASED = (
    ":let use_erased = ("
    "GEVar (gext TInt G0 gempty) (gext TInt G0 gempty) TInt "
    "(gv_here1 gempty TInt) "
    ": GExpr (gext TInt G0 gempty) TInt (gext TInt G0 gempty))"
)


def main() -> None:
    code, out = run_with_affine_prelude(OMEGA_TWICE)
    assert code == 0, f"omega_twice should check, got exit {code}:\n{out}"
    assert "omega_twice : " in out
    print("PASS: omega_twice checked (exit 0) — two uses of a GW binding "
          "are well-graded")

    code, out = run_with_affine_prelude(USE_ERASED)
    assert code == 1, f"use_erased should be rejected, got exit {code}"
    print("PASS: grade-0 use rejected (exit 1) — GVar has no rule at G0, "
          "so an erased binding cannot be referenced")


if __name__ == "__main__":
    main()
