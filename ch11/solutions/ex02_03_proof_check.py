"""
Chapter 11, Exercises 2 & 3 — solution code (grounding).

Ex.2 states preservation/progress; Ex.3 is about the typed Step relation
(Step : Expr g t -> Expr g t -> Type) and "preservation by construction." Both
rest on Lark's machine-checked soundness proof in lark/formal/proof/. This script
runs the lcore kernel on that proof and confirms it checks — so the claims below
are not asserted but verified by the same checker the chapter describes.

How to run:   python3 ex02_03_proof_check.py
Expected:     "lcore checked the soundness proof: N definitions, 0 errors; "
              "evaluation-soundness lemmas normalise to values"

Ex.2 — PRESERVATION and PROGRESS.
  Preservation: if  ·  ⊢ e : t  and  e → e'  then  · ⊢ e' : t.
  Progress:     if  ·  ⊢ e : t  then e is a value or ∃ e'. e → e'.
  Together: a well-typed closed term never gets stuck.
  (a) In an untyped language `true 3` (apply a boolean) is STUCK — a non-value
      with no rule. PROGRESS rules it out in a typed language: it is not
      well-typed (a Bool is not a function), so it never arises.
  (b) Lark's encoding makes preservation "DISAPPEAR": the reduction relation is
      typed as  Step : Expr g t -> Expr g t -> Type  — the SAME index t appears
      on both sides, so a step that changed the type is not even expressible.
      Preservation is still true; the work moves onto the definition of `Expr`,
      which carries the type index intrinsically (a term *is* a typed term), so
      "well-typed" is not a separate predicate to preserve but part of what a
      term is.

Ex.3 — the typed Step relation.
  (a) A reduction allowed to change a term's type would need
        Step : Expr g t -> Expr g t' -> Type   (t' possibly ≠ t).
      No constructor of the eight-rule relation can inhabit it: each rule
      (StepBeta, StepIfTrue, …) produces an Expr at the *same* index t it
      consumed, because the typing rules guarantee the redex and contractum have
      equal types. With one shared t the bad signature has no inhabitant.
  (b) Preservation (proved, total) GUARANTEES type is kept on *every* reduction
      of *every* well-typed term; the differential-testing oracle (Ch.11 §5) only
      SAMPLES finitely many runs. The proof covers the infinite space testing
      can only spot-check.
"""

import os
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_LANG = os.path.dirname(os.path.dirname(_HERE))
_PROOF = os.path.join(_LANG, "lark", "formal", "proof")
_CORE = os.path.join(_PROOF, "code", "core")
_LCORE = os.path.join(_CORE, "lcore")
_FILES = ["lark-typing", "lark-subst", "lark-step", "lark-preservation"]


def _ensure_lcore():
    if not os.path.exists(_LCORE):
        subprocess.run(["make"], cwd=_CORE, check=True,
                       capture_output=True, text=True)


def _proof_input():
    """Concatenate the four proof files, stripping comments and blank lines
    (the pipeline documented in lark-preservation.lcore's header)."""
    lines = []
    for name in _FILES:
        with open(os.path.join(_PROOF, "lark", name + ".lcore")) as f:
            for line in f:
                s = line.rstrip("\n")
                if s.lstrip().startswith("--") or not s.strip():
                    continue
                lines.append(s)
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    _ensure_lcore()
    result = subprocess.run([_LCORE], input=_proof_input(),
                            capture_output=True, text=True)
    out = result.stdout + result.stderr

    # No checker errors: lcore reports 'parse: ...' or '... failed' on any bad
    # definition (and 'inferred:/expected:' on a type mismatch).
    errors = [ln for ln in out.splitlines()
              if "failed" in ln or ln.strip().startswith("parse:")
              or "inferred:" in ln]
    assert result.returncode == 0, result.returncode
    assert not errors, f"lcore reported errors:\n" + "\n".join(errors[:5])

    # Positive evidence: the soundness lemmas are present and the
    # evaluation-soundness terms normalise to values (the proof RUNS).
    assert "NotStuck" in out, "expected the progress/soundness statement NotStuck"
    assert "eval_produces_val" in out
    assert "ValBool true" in out and "ValInt" in out, "soundness lemmas should " \
        "normalise to values"

    n_defs = out.count("parsed :")
    print(f"lcore checked the soundness proof: {n_defs} definitions, "
          f"{len(errors)} errors; evaluation-soundness lemmas normalise to values")
