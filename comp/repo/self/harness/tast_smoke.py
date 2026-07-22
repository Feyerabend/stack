"""
Smoke test for the typed AST (tast.lark).

tast.lark is pure data (the typed AST) plus a top-level signature printer.  It
depends on parse.lark (Val, Maybe) and types.lark (Mono, Scheme, pretty), and
the type checker's pipeline is assembled by CONCATENATION rather than `import` (see the note
in parse_difftest.py / a known wart of the language).  So this smoke concatenates

    parse.lark body + types.lark body + tast.lark body + tast's smoke main

under one module and runs it through the CEK interpreter (oracle/cek.py).  A
green run proves tast.lark type-checks against the real type vocabulary and that
its ADTs + signature printer construct/destructure correctly.

There is no Python twin to diff here: the typed AST's observable differential is
"inferred top-level types", which needs infer.lark (slice 3).  Until then this
is an eyeball + exit-code smoke, matching how types.lark is validated (typesmoke).

Usage:
    python3 harness/tast_smoke.py            # exits 0 on success
"""

from __future__ import annotations
import sys, subprocess, pathlib

HERE  = pathlib.Path(__file__).resolve().parent   # <strand>/harness
ROOT  = HERE.parent                              # <strand>/
SELF  = ROOT / "lark"                            # the compiler, written in Lark
SRC   = ROOT / "oracle"                          # the Python reference implementation
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
TYPES = SELF / "types.lark"
TAST  = SELF / "tast.lark"

MAIN_MARKER = "\nfn main(io : IO) : IO ="


def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)


def make_driver() -> str:
    # lex + parse + types: bodies only (drop module headers, imports, smoke mains).
    # lex is required because parse.lark builds on its Token type + Copy impls.
    lex_body   = LEX.read_text().split(MAIN_MARKER, 1)[0]
    parse_body = PARSE.read_text().split(MAIN_MARKER, 1)[0]
    types_body = TYPES.read_text().split(MAIN_MARKER, 1)[0]
    lex_body   = _strip_lines(lex_body, ("module ",))
    parse_body = _strip_lines(parse_body, ("module ", "import "))
    types_body = _strip_lines(types_body, ("module ", "import "))
    # tast: keep its smoke main; drop only the module header.
    tast_full  = _strip_lines(TAST.read_text(), ("module ", "import "))
    return ("module Selfhost\n\n"
            + lex_body + "\n"
            + parse_body + "\n"
            + types_body + "\n"
            + tast_full + "\n")


# The typed program the smoke builds by hand (Color / id / answer / Show impl).
EXPECTED = [
    "(module Demo)",
    "type Color",
    "id : forall. α -> α",
    "answer : Int",
    "impl Show for Color",
]


def main() -> None:
    driver = make_driver()
    tmp = HERE / "_tastdriver.lark"
    tmp.write_text(driver)
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=120)
    finally:
        tmp.unlink(missing_ok=True)

    if r.returncode != 0:
        print("  FAIL  tast.lark smoke — CEK crash")
        tail = (r.stderr or r.stdout).strip().splitlines()[-3:] or ["?"]
        for line in tail:
            print(f"        {line}")
        sys.exit(1)

    got = r.stdout.splitlines()
    if got == EXPECTED:
        print(f"  ok    tast.lark smoke  ({len(got)} lines, typed AST builds + prints)")
        sys.exit(0)

    print("  FAIL  tast.lark smoke — output mismatch")
    for i in range(max(len(got), len(EXPECTED))):
        a = EXPECTED[i] if i < len(EXPECTED) else "<none>"
        b = got[i] if i < len(got) else "<none>"
        if a != b:
            print(f"        line {i}: expected={a!r}")
            print(f"                 got     ={b!r}")
    sys.exit(1)


if __name__ == "__main__":
    main()
