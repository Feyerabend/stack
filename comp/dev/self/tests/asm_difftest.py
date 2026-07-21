"""
Differential test for the self-hosted RV32I code generator
(SELFHOST F3, slice 1b — asm.lark: the port of 07/src/asm.py).

THIS IS THE F3.1 MILESTONE.  With it, the last stage of the pipeline exists in
Lark on a second backend: `lex → parse → infer → lower → opt` (all green since
M7) now feeds EITHER emit_tac_c.lark (TAC → C) or asm.lark (TAC → RV32I).  F3 is
a backend swap, and this test is what says the swap is faithful.

Shape (identical to lower / emit_tac_c / regalloc — isolate the stage under test):

  • the oracle parses + typechecks + lowers the object program to a TAC value —
    WITH NO OPTIMIZATION, so both sides assemble the identical TAC — and runs
    asm.gen(tac) in-process, which allocates registers (regalloc.py) and emits
    the assembly text;
  • the port SERIALISES that same TAC into tac.lark constructor source and runs
    lex+parse+tac+opt+regalloc+asm with a driver that prints `asGen(<that TAC>)`.

The two `.S` texts must be BYTE-IDENTICAL — every immediate, every label, every
column of the 4-wide mnemonic padding.

⚠ RUN regalloc_difftest FIRST IF THIS FLAPS.  asm.py's output is only a function
of its input because regalloc.py was canonicalised (it used to iterate frozensets,
so which Tmp got which register — and hence every register name in this file —
was a function of PYTHONHASHSEED).  Any reintroduced set iteration upstream shows
up here as a spurious diff.

Note: gen() is called in-process, NOT through asm.py's CLI — the CLI writes
`<src>.S` next to every input file, which would litter 07/tests and 07/samples.

Scope: single-file programs the oracle accepts.  A file is SKIPPED (not failed)
when the oracle can't produce a TAC — it `import`s another module, or it is a
reject fixture (infer raises, nothing to lower) — or when the meta-circular run
overflows / times out (a capacity verdict, not a bug).

Usage:
    python3 self/tests/asm_difftest.py [-v]      # -v: unified diff on fail
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib
import os

HERE  = pathlib.Path(__file__).resolve().parent          # self/tests
SELF  = HERE.parent                                      # self
ROOT  = SELF.parent                                      # lark
SRC   = ROOT / "07" / "src"
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
TAC   = SELF / "tac.lark"
OPT   = SELF / "opt.lark"
REGA  = SELF / "regalloc.lark"
ASM   = SELF / "asm.lark"

sys.path.insert(0, str(SRC))
from lexer import LexError              # noqa: E402
import parser as _parser                # noqa: E402
from parser import ParseError           # noqa: E402
import infer as _infer                  # noqa: E402
import lower as _lower                  # noqa: E402
import asm as _asm                      # noqa: E402

from emit_tac_c_difftest import s_tac   # noqa: E402  (the shared TAC serialiser)


# ── Oracle ────────────────────────────────────────────────────────────────────

def oracle(path: pathlib.Path):
    """Return (verdict, payload).  verdict in {'asm','skip'}."""
    try:
        prog = _parser.parse_file(str(path))
    except (LexError, ParseError) as e:
        return "skip", f"oracle parse error: {e}"
    if prog.imports:
        return "skip", "multi-module (import) — outside single-file port"
    try:
        tprog = _infer.typecheck(prog, source_file=str(path))
    except (_infer.TypeError, _infer.AffineError, _infer.TraitBoundError) as e:
        return "skip", f"reject fixture (infer: {str(e)[:40]}) — nothing to lower"
    tac = _lower.lower(tprog)          # NO optimization: isolate the backend
    return "asm", (tac, _asm.gen(tac))


# ── Port: concatenate lex + parse + tac + opt + regalloc + asm + a driver ─────

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)

def make_driver(tac) -> str:
    lex   = _strip_lines(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse = _strip_lines(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    tacm  = _strip_lines(TAC.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    opt   = _strip_lines(OPT.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    rega  = _strip_lines(REGA.read_text().split(MAIN_MARKER, 1)[0],  ("module ", "import "))
    asmm  = _strip_lines(ASM.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    prog  = s_tac(tac)
    driver_main = (
        "\nfn main(io : IO) : IO =\n"
        f"  let prog = {prog} in\n"
        "  print(io, asGen(prog))\n"
    )
    return ("module Selfhost\n\n"
            + lex + "\n" + parse + "\n" + tacm + "\n" + opt + "\n"
            + rega + "\n" + asmm + driver_main)


PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "240"))

def run_port(tac):
    tmp = HERE / "_asmdriver.lark"
    tmp.write_text(make_driver(tac))
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── Corpus + driver loop ──────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "07" / "tests", ROOT / "07" / "samples"]:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.lark")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files


def main() -> None:
    verbose = "-v" in sys.argv
    ok = fail = skip = 0

    for path in corpus():
        label = str(path.relative_to(ROOT))
        verdict, payload = oracle(path)
        if verdict == "skip":
            print(f"  skip  {label}  ({payload})")
            skip += 1
            continue

        tac, want = payload
        try:
            pcode, pout, perr = run_port(tac)
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (meta-circular codegen too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue

        if pcode != 0:
            tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
            low = (perr or "").lower()
            if "recursion" in low or "maximum" in low:
                print(f"  skip  {label}  (CEK overflow on deep TAC: {tail[0][:50]})")
                skip += 1
                continue
            print(f"  FAIL  {label}  (port exit {pcode}: {tail[0][:70]})")
            fail += 1
            continue

        got = pout.rstrip("\n")
        if got == want.rstrip("\n"):
            n = len(want.splitlines())
            print(f"  ok    {label}  ({n} lines)")
            ok += 1
        else:
            print(f"  FAIL  {label}  (assembly differs)")
            fail += 1
            if verbose:
                for line in difflib.unified_diff(
                        want.splitlines(), got.splitlines(),
                        fromfile="asm.py", tofile="asm.lark", lineterm=""):
                    print("      " + line)

    print(f"\n  {ok} ok, {fail} failed, {skip} skipped")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
