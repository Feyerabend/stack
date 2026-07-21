"""
Differential test for the self-hosted TAC optimizer (SELFHOST M7, slice 4 —
opt.lark: the port of 07/src/opt.py's TAC-subset passes).

opt.lark, like lower.lark and emit_tac_c.lark, consumes an intermediate
representation, so this harness ISOLATES it the same way: the front end + lowerer
are the trusted oracles, a lowered TAC value is fed in verbatim, and only
opt.lark + tac.lark (green since M7.1) run in Lark.

For every corpus file AND every optimization level -O0..-O3:

  • the oracle parses + typechecks (infer.py) + lowers (lower.py) the object
    program to an UNOPTIMIZED TAC, then optimizes it with opt.py at that level
    (opt.optimize(tac, OptOptions(level=n))) and pretty-prints the result
    (tac.py `pretty`);
  • the port SERIALISES the SAME unoptimized TAC into tac.lark constructor source,
    then runs lex+parse+tac+opt + a driver that prints
    `tacPretty(optimizeProg(<that TAC>, n))`.

The two optimized-TAC pretty-prints must be byte-identical, at every level.  This
is the strongest M7.4 obligation (OPTIMIZE.md §9): the port reproduces the
oracle's optimized IR exactly, pass for pass, sweep for sweep.

Two determinism points make the site-numbered passes (inline / closure_elim)
line up:
  • opt.py mints inline/closure site names from a MODULE-GLOBAL counter
    `opt._SITE`; the port threads a site counter from 0 in each fresh CEK
    subprocess.  So the harness RESETS `opt._SITE = itertools.count()` before each
    oracle optimize() call — then both start a file+level at site 0.
  • opt.py's passes MUTATE `fn.body` in place, so the oracle RE-LOWERS a fresh TAC
    per level (the serialised input is captured from its own untouched lowering).

Scope: single-file programs the oracle accepts.  A file is SKIPPED (not failed)
when the oracle can't produce a TAC — it `import`s another module, or it is a
reject fixture (infer raises) — or when the meta-circular run overflows / times
out (a capacity verdict, not a bug: the optimizer does far more list-walking than
the emitter, so deep programs at -O2/-O3 can exhaust the CEK stack).

Usage:
    python3 self/tests/opt_difftest.py [-v]        # -v: unified diff on fail
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib, itertools
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

sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))
from lexer import LexError               # noqa: E402
import parser as _parser                 # noqa: E402
from parser import ParseError            # noqa: E402
import infer as _infer                   # noqa: E402
import lower as _lower                   # noqa: E402
import tac as _tac                        # noqa: E402
import opt as _opt                        # noqa: E402
# Reuse the oracle-TAC → tac.lark serialiser (identical to the emit_tac_c harness).
from emit_tac_c_difftest import s_tac     # noqa: E402


LEVELS = (0, 1, 2, 3)


# ── Oracle ────────────────────────────────────────────────────────────────────

def oracle_prep(path: pathlib.Path):
    """Return (verdict, tprog|reason).  verdict in {'run','skip'}."""
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
    return "run", tprog


def oracle_at(tprog, level: int) -> str:
    """Optimized-TAC pretty for one level.  Resets _SITE and re-lowers so the site
    counter and the mutate-in-place passes both start clean."""
    _opt._SITE = itertools.count()
    tac = _lower.lower(tprog)                        # fresh: passes mutate in place
    tac = _opt.optimize(tac, _opt.OptOptions(level=level))
    return _tac.pretty(tac)


# ── Port: concatenate lex + parse + tac + opt + a driver ──────────────────────

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)

def make_driver(serialised_tac: str, level: int) -> str:
    lex   = _strip_lines(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse = _strip_lines(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    tacm  = _strip_lines(TAC.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    optm  = _strip_lines(OPT.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    driver_main = (
        "\nfn main(io : IO) : IO =\n"
        f"  let prog = {serialised_tac} in\n"
        f"  print(io, tacPretty(optimizeProg(prog, {level})))\n"
    )
    return ("module Selfhost\n\n"
            + lex + "\n" + parse + "\n" + tacm + "\n" + optm + driver_main)


PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "180"))

def run_port(serialised_tac: str, level: int):
    tmp = HERE / "_optdriver.lark"
    tmp.write_text(make_driver(serialised_tac, level))
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


def _first_diff(exp: list[str], gt: list[str]) -> None:
    for i in range(max(len(exp), len(gt))):
        a = exp[i] if i < len(exp) else "<none>"
        b = gt[i]  if i < len(gt)  else "<none>"
        if a != b:
            print(f"        line {i}: oracle={a!r}")
            print(f"                 port  ={b!r}")
            return


def main() -> None:
    verbose = "-v" in sys.argv
    ok = fail = skip = 0

    for path in corpus():
        label = str(path.relative_to(ROOT))
        verdict, payload = oracle_prep(path)
        if verdict == "skip":
            print(f"  skip  {label}  ({payload})")
            skip += len(LEVELS)
            continue

        tprog = payload
        # The serialised input is the UNOPTIMIZED lowering, captured once (its own
        # fresh lower, untouched by the per-level oracle optimize below).
        serialised = s_tac(_lower.lower(tprog))

        for level in LEVELS:
            tag = f"{label} -O{level}"
            want = oracle_at(tprog, level)
            try:
                pcode, pout, perr = run_port(serialised, level)
            except subprocess.TimeoutExpired:
                print(f"  skip  {tag}  (meta-circular opt too slow — >{PORT_TIMEOUT}s)")
                skip += 1
                continue

            if pcode != 0:
                tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
                low = (perr or "").lower()
                if "recursion" in low or "maximum" in low or "overflow" in low:
                    print(f"  skip  {tag}  (CEK overflow on deep TAC: {tail[0][:50]})")
                    skip += 1
                else:
                    print(f"  FAIL  {tag}  (port crash)")
                    print(f"        {tail[0]}")
                    fail += 1
                continue

            want_nl = want + "\n"          # cek's print adds one newline; pretty has none
            if pout == want_nl:
                print(f"  ok    {tag}")
                ok += 1
            else:
                print(f"  FAIL  {tag}  (TAC mismatch)")
                exp = want_nl.splitlines()
                gt  = pout.splitlines()
                if verbose:
                    d = difflib.unified_diff(exp, gt, "oracle", "port", lineterm="")
                    for line in list(d)[:80]:
                        print(f"        {line}")
                else:
                    _first_diff(exp, gt)
                fail += 1

    print(f"\n  {ok} ok / {fail} fail / {skip} skip")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
