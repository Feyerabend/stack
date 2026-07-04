"""Shared helper for the Chapter 13 solutions.

Drives the proof kernel `lcore` and the machine-checked graded (affine)
typing model from Chapter 13 (`lark-typing.lcore` + `lark-affine.lcore`).

Unlike the Chapter 12 harness, the success/failure contract here is the
*exit code* — deliberately. Chapter 13 (section 13.6) made the kernel
machine-checkably strict: every line is type-checked before it is
normalised, and any failed line makes the whole run exit non-zero
("lcore: one or more inputs FAILED"). So `exit 0` means every claim in
the run was checked and accepted, and `exit 1` means the kernel rejected
something — no string-scraping required. These solutions lean on exactly
that guarantee.
"""

import os
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))

# The proof tree lives at lark/formal/proof. Candidate locations cover
# this folder sitting at <repo>/lark/book/solutions-ch13 (the bbe tree)
# or at <repo>/ch13/solutions (the stack companion tree).
_CANDIDATES = [
    os.path.join(_HERE, "..", "..", "formal", "proof"),
    os.path.join(_HERE, "..", "..", "lark", "formal", "proof"),
]


def _proof_root() -> str:
    for c in _CANDIDATES:
        c = os.path.abspath(c)
        if os.path.exists(os.path.join(c, "lark", "lark-affine.lcore")):
            return c
    raise SystemExit("cannot locate lark/formal/proof (tried: %s)"
                     % ", ".join(map(os.path.abspath, _CANDIDATES)))


def ensure_built() -> str:
    """Return the path to the lcore binary, building it if needed."""
    core = os.path.join(_proof_root(), "code", "core")
    lcore = os.path.join(core, "lcore")
    if not os.path.exists(lcore):
        subprocess.run(["make"], cwd=core, check=True,
                       capture_output=True, text=True)
    return lcore


def _strip(src: str) -> str:
    """The run-line filter from the proof files themselves: drop comment
    and blank lines (lcore's REPL grammar is line-oriented)."""
    keep = [ln for ln in src.splitlines()
            if ln.strip() and not ln.lstrip().startswith("--")]
    return "\n".join(keep) + "\n"


def run_with_affine_prelude(claims: str):
    """Feed lark-typing.lcore + lark-affine.lcore + `claims` to lcore.
    Returns (exit_code, combined_output)."""
    root = _proof_root()
    lcore = ensure_built()
    src = ""
    for f in ("lark-typing.lcore", "lark-affine.lcore"):
        with open(os.path.join(root, "lark", f), encoding="utf-8") as fh:
            src += _strip(fh.read())
    src += _strip(claims)
    r = subprocess.run([lcore], input=src, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr
