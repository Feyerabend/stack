"""
Conservative-extension differential — 08/src vs the frozen oracle 07/src.

The claim this axis has to keep true, from the first refinement to the last:

    a program that carries no refinement must type-check and evaluate through
    08/ exactly as it does through 07/ — same verdict, same bytes, same exit.

So we take 07's whole corpus (which by construction carries no refinements),
push every file through *both* trees' `infer.py` (front end + Algorithm W) and
`cek.py` (evaluator), and demand byte-identical stdout/stderr/returncode.

Today, with 08/src a fresh copy, this is trivially green — and that is the point
of running it *now*, before the first refinement exists. Afterwards a red row
cannot be read: you can no longer tell a regression from a feature.

    python3 08/tests/conservative_difftest.py     # or: make -C 08 conservative

Env: LARK_TIMEOUT (seconds per run, default 120).

⛔ Reads 07/ — never writes it (PROVE.md §0.1).
"""

from __future__ import annotations
import difflib, os, pathlib, re, subprocess, sys

ROOT   = pathlib.Path(__file__).resolve().parent.parent   # .../lark/08
LARK   = ROOT.parent                                      # .../lark
ORACLE = LARK / "07" / "src"
FORK   = ROOT / "src"
CORPUS = [LARK / "07" / "tests", LARK / "07" / "samples"]

TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))

# Both stages are compared. `infer` is where refinements will land; `cek` is the
# runtime check that erasure really is erasure (a refinement must not change what
# a program prints).
STAGES = ["infer.py", "cek.py"]

# The oracle renames a wildcard param `_` to `_anon_{id(node)}` (infer.py:420,588),
# baking a CPython object address into the typed AST it prints.  That address moves
# between *any* two runs — including two runs of 07/src itself — so it is noise here,
# not divergence.  Canonicalise it exactly as self/tests/emit_c_difftest.py does;
# `_anon_<digits>` never appears in the corpus, so this cannot mask a real name.
_ANON = re.compile(r"_anon_\d+")

# The reject fixtures die with an uncaught Python exception, so their stderr is a
# TRACEBACK — and a traceback carries the line numbers of the interpreter's own
# source.  Adding nine lines to infer.py shifts every line number below them, in
# every fixture, without changing a single thing about what Lark decided.  So the
# numbers are canonicalised and everything else in the traceback is not: the frame
# names, the source lines, the exception type and its message are all still
# compared byte for byte.  A real divergence has nowhere to hide behind `line N`.
# (Python 3.14 colourises tracebacks, so the number sits inside an ANSI escape —
# hence the optional escape in the pattern.  Matching bare `line \d+` silently
# matches nothing at all, which looks exactly like a passing canonicalisation.)
_LINENO = re.compile(r"(line )(\x1b\[[0-9;]*m)?\d+")


def corpus() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for d in CORPUS:
        paths += sorted(p for p in d.rglob("*.lark"))
    return paths


def run(src: pathlib.Path, stage: str, f: pathlib.Path):
    """Run one file through one tree's stage. Returns (rc, out, err) or None on timeout."""
    try:
        r = subprocess.run(
            [sys.executable, str(src / stage), str(f)],
            capture_output=True, text=True, timeout=TIMEOUT,
            stdin=subprocess.DEVNULL, cwd=str(LARK),
        )
    except subprocess.TimeoutExpired:
        return None
    # Three things may legitimately differ between the trees without being a
    # divergence: the interpreter's own path (07/src vs 08/src), the object address
    # in `_anon_`, and the line numbers in a traceback.  Canonicalise all three, so
    # a red row can only be real.
    def canon(s: str) -> str:
        s = s.replace(str(src), "<src>")
        s = _ANON.sub("_", s)
        return _LINENO.sub(r"\1N", s)
    return r.returncode, canon(r.stdout), canon(r.stderr)


def main() -> int:
    ok = fail = skip = 0
    files = corpus()
    print(f"conservative-extension differential — {len(files)} files x {len(STAGES)} stages\n")

    for f in files:
        rel = f.relative_to(LARK)
        for stage in STAGES:
            label = f"  {rel}  [{stage[:-3]}]"
            a = run(ORACLE, stage, f)
            b = run(FORK, stage, f)
            if a is None or b is None:
                # A timeout is a property of the box, not of the fork — but if
                # only one side timed out, that is a divergence.
                if a is None and b is None:
                    print(f"{label:<52} skip (timeout, both)")
                    skip += 1
                else:
                    slow = "07" if a is None else "08"
                    print(f"{label:<52} FAIL (timeout in {slow} only)")
                    fail += 1
                continue
            if a == b:
                print(f"{label:<52} ok")
                ok += 1
                continue
            fail += 1
            print(f"{label:<52} FAIL")
            print(f"      rc:  07={a[0]}  08={b[0]}")
            for name, x, y in (("stdout", a[1], b[1]), ("stderr", a[2], b[2])):
                if x != y:
                    d = difflib.unified_diff(
                        x.splitlines(), y.splitlines(),
                        fromfile=f"07 {name}", tofile=f"08 {name}", lineterm="",
                    )
                    for line in list(d)[:24]:
                        print(f"      {line}")

    print(f"\n  {ok} ok / {fail} fail / {skip} skip")
    if fail:
        print("\n  THE FORK IS NOT A CONSERVATIVE EXTENSION. Every red row above is a")
        print("  refinement-free program that 08/ answers differently from 07/.")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
