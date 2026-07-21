"""
Smoke test for the type checker (SELFHOST M3, slice 3 — infer.lark).

infer.lark depends on lex + parse + types + tast, and the M3 pipeline is
assembled by CONCATENATION rather than `import` (see parse_difftest.py /
SELFHOST §7).  This concatenates

    lex + parse + types + tast bodies  +  infer.lark (with its smoke main)

under one module, runs it through the CEK interpreter (07/src/cek.py), and
checks the printed top-level signature block.  A green run proves infer.lark
type-checks against the whole M3 vocabulary and that Algorithm W + the passes
construct/print correctly.

Usage:
    python3 self/tests/infer_smoke.py            # exits 0 on success
"""

from __future__ import annotations
import sys, subprocess, pathlib

HERE  = pathlib.Path(__file__).resolve().parent
SELF  = HERE.parent
ROOT  = SELF.parent
CEK   = str(ROOT / "07" / "src" / "cek.py")
LEX, PARSE, TYPES, TAST, INFER = (
    SELF / "lex.lark", SELF / "parse.lark", SELF / "types.lark",
    SELF / "tast.lark", SELF / "infer.lark",
)

MAIN_MARKER = "\nfn main(io : IO) : IO ="


def _strip(src: str, prefixes: tuple[str, ...]) -> str:
    return "\n".join(ln for ln in src.splitlines()
                     if not any(ln.lstrip().startswith(p) for p in prefixes))


def make_driver() -> str:
    lex   = _strip(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse = _strip(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    types = _strip(TYPES.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    tast  = _strip(TAST.read_text().split(MAIN_MARKER, 1)[0],  ("module ", "import "))
    infer = _strip(INFER.read_text(),                          ("module ", "import "))
    return ("module Selfhost\n\n"
            + lex + "\n" + parse + "\n" + types + "\n" + tast + "\n" + infer + "\n")


EXPECTED = [
    "(module Demo)",
    "double : Int -> Int",
    "apply2 : (Int -> Int) -> Int -> Int",
    "main : IO -> IO",
]


def main() -> None:
    tmp = HERE / "_inferdriver.lark"
    tmp.write_text(make_driver())
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=180)
    finally:
        tmp.unlink(missing_ok=True)

    if r.returncode != 0:
        print("  FAIL  infer.lark smoke — CEK crash")
        for line in (r.stderr or r.stdout).strip().splitlines()[-6:] or ["?"]:
            print(f"        {line}")
        sys.exit(1)

    got = r.stdout.splitlines()
    if got == EXPECTED:
        print(f"  ok    infer.lark smoke  ({len(got)} lines, Algorithm W + passes run)")
        sys.exit(0)

    print("  FAIL  infer.lark smoke — output mismatch")
    for i in range(max(len(got), len(EXPECTED))):
        a = EXPECTED[i] if i < len(EXPECTED) else "<none>"
        b = got[i] if i < len(got) else "<none>"
        if a != b:
            print(f"        line {i}: expected={a!r}")
            print(f"                 got     ={b!r}")
    sys.exit(1)


if __name__ == "__main__":
    main()
