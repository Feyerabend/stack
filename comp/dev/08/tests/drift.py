"""
Drift check — 08/src is a *fork* of the frozen oracle 07/src, not an edit of it.

Every file in 08/src must be byte-identical to its 07/src twin unless this axis
has a declared reason to have changed it. The two tables below are that
declaration, and they are the honest statement of how large the refinement
extension has grown:

    EXTENDED — modules copied from 07/src that PROVE.md has since changed.
    ADDED    — modules that exist only in 08/src (refine.py, solver.py, ...).

Anything drifting that is not named here is a bug: either an accidental edit, or
an extension nobody wrote down. A file that vanishes from 08/src is a bug too.

    python3 08/tests/drift.py          # or: make -C 08 drift

⛔ This check never touches 07/src. If a run of *anything* modifies 07/src, three
fixpoints (49a4921c, 829410dc, f1dedfa9) and both BASELINES.md re-open. See
PROVE.md §0.1.
"""

from __future__ import annotations
import hashlib, pathlib, sys

ROOT   = pathlib.Path(__file__).resolve().parent.parent   # .../lark/08
ORACLE = ROOT.parent / "07" / "src"                       # frozen — read only
FORK   = ROOT / "src"

# Modules this axis has deliberately extended: name -> why.
# Empty at Step 0, and every entry added here is a claim to be defended.
EXTENDED: dict[str, str] = {
    "tree.py":   "TRefine node: {v:Int|p} joins the syntactic Type union; "
                 "MeasureDecl, which pointedly does NOT join Decl — it lives in "
                 "Program.measures, and that is where a measure's erasure IS",
    "parser.py": "_parse_refine_type: '{' begins a type, LL(1) intact; "
                 "_parse_measure_decl: 'measure' is a CONTEXTUAL keyword, so the "
                 "oracle's lexer needs no word it does not have",
    "infer.py":  "syntype_to_mono erases TRefine to its base — the line that "
                 "joins the refinement layer to HM and the affine checker; plus "
                 "the HM schemes for the `min`/`max` builtins (V2.4c step 1)",
    "cek.py":    "the `min`/`max` builtins at run time (V2.4c step 1) — the FIRST "
                 "PROVE rung to touch the runtime, because a measure/refinement is "
                 "ghost but `min`/`max` are real functions the program calls: arity, "
                 "the two-argument dispatch, and the VBuiltin table entries",
}

# Modules that exist only in the fork: name -> why.
ADDED: dict[str, str] = {
    "pred.py":   "the predicate language: QF-UFLIA terms and formulas",
    "solver.py": "the decision procedure: congruence closure + Omega, DPLL(T) "
                 "on top — from scratch, no Z3",
    "refine.py": "the VC generator: bidirectional check/synth, subtyping as "
                 "entailment; the only module that asks solver.valid()",
}


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def files(d: pathlib.Path) -> set[str]:
    return {
        p.name for p in d.iterdir()
        if p.is_file() and not p.name.startswith(".")
    }


def main() -> int:
    oracle, fork = files(ORACLE), files(FORK)
    problems: list[str] = []

    missing = sorted(oracle - fork)
    for name in missing:
        problems.append(f"MISSING   {name}  — in 07/src, absent from 08/src")

    added = sorted(fork - oracle)
    for name in added:
        if name in ADDED:
            print(f"  added     {name:<16} {sha(FORK / name)}  — {ADDED[name]}")
        else:
            problems.append(f"UNDECLARED {name} — new in 08/src, not in ADDED")

    same = extended = 0
    for name in sorted(oracle & fork):
        a, b = sha(ORACLE / name), sha(FORK / name)
        if a == b:
            if name in EXTENDED:
                problems.append(
                    f"STALE     {name} — listed EXTENDED but identical to 07/src"
                )
            same += 1
        elif name in EXTENDED:
            print(f"  extended  {name:<16} {a} -> {b}  — {EXTENDED[name]}")
            extended += 1
        else:
            problems.append(
                f"DRIFT     {name} — differs from 07/src ({a} -> {b}) "
                f"and is not in EXTENDED"
            )

    print(
        f"\n  {same} identical, {extended} extended, "
        f"{len(added)} added, {len(missing)} missing"
    )
    if problems:
        print("\n  drift check FAILED:")
        for p in problems:
            print(f"    {p}")
        return 1
    print("  drift check clean — the fork is where it says it is.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
