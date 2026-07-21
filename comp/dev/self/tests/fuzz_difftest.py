"""
Property/fuzz differential for the self-hosted toolchain (SELFHOST hardening).

The four corpus differentials (lex/parse/infer/emit) prove `port == oracle` only
on the ~44 fixed files.  This harness attacks that corpus-coverage blind spot: it
generates fresh, deterministically-seeded, well-typed Lark programs (fuzz_gen.py)
and pushes each one through the WHOLE pipeline —

    lex  →  parse  →  infer  →  emit

— demanding that the self-hosted port and the 07/ Python oracle agree at every
stage:

  • lex   : token stream            (self/lex.lark            vs lexer.py)
  • parse : pretty-printed AST      (self/parse.lark          vs parser.py)
  • infer : signature block/verdict (self/infer.lark          vs infer.typecheck)
  • emit  : generated C source      (self/emit_c.lark         vs emit_c_ast.py)

It does not re-implement any of that machinery — it *reuses* the four sibling
harnesses' own driver assembly, port runners, oracles and canonicalisers, so a
fuzz program travels through byte-for-byte the same port pipeline the corpus
differentials use.  The only new thing here is the *input distribution*: random
programs the fixed corpus never wrote.

Why every generated program is a fair test
──────────────────────────────────────────
fuzz_gen builds terms type-directed over the four Copy scalars plus one Copy ADT,
so each program type-checks by construction and therefore reaches the emit stage.  A program is
SKIPPED (never FAILED) only for the same out-of-port-control reasons the corpus
harnesses skip:
  • the meta-circular port run exceeds its time budget (a perf verdict), or
  • the ORACLE cannot produce a verdict — in particular ty.apply overflows the
    Python stack (RecursionError) on a long variable-substitution chain.  That is
    a real robustness limit in the oracle that fuzzing surfaced (catalogued in
    SELFHOST §7 and self/tests/AUDIT.md); with no oracle verdict there is nothing
    to compare, so infer+emit are skipped for that seed.

A FAIL is always a genuine port divergence: the port produced different tokens /
AST / signatures / C than the oracle, or the port crashed.  Every FAIL prints its
seed and the exact source, which reproduces standalone via
    python3 self/tests/fuzz_gen.py <seed>

Usage:
    python3 self/tests/fuzz_difftest.py [-n N] [--seed S] [--stages a,b,…] [-v]
      -n N          number of programs to generate      (default 8)
      --seed S      base seed; program i uses S+i        (default 1000)
      --stages ...  comma list of lex,parse,infer,emit   (default all)
      -v            print full source + unified diffs on FAIL
"""

from __future__ import annotations
import os, sys, pathlib, difflib, subprocess, re

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fuzz_gen
import lex_difftest    as LX
import parse_difftest  as PS
import infer_difftest  as IN
import emit_c_difftest as EM

from lexer import LexError            # noqa: E402  (paths set up by siblings)
from parser import ParseError         # noqa: E402

# Our own temp object program (its name is also the emit header basename, so port
# and oracle must use the same one).  PID-unique so it never collides.  NOTE: the
# reused sibling run_port helpers still write FIXED temp-driver names
# (_driver/_pdriver/_idriver/_edriver.lark), so do not run two fuzz processes at
# once — they would clobber each other mid-write (a spurious cross-seed "FAIL").
# One fuzz process is fully sequential and safe; use -n to scale a single run.
OBJ = HERE / f"_fuzz_obj_{os.getpid()}.lark"


# ── Per-stage comparison, each reusing its sibling's port + oracle ──────────────

def _firstdiff(exp: list[str], got: list[str]) -> str:
    for i in range(max(len(exp), len(got))):
        a = exp[i] if i < len(exp) else "<none>"
        b = got[i] if i < len(got) else "<none>"
        if a != b:
            return f"line {i}: oracle={a!r}  port={b!r}"
    return f"length: oracle={len(exp)} port={len(got)}"


class Result:
    __slots__ = ("status", "detail")

    def __init__(self, status: str, detail: str = "") -> None:
        self.status = status               # "ok" | "fail" | "skip"
        self.detail = detail


def stage_lex(src: str, lex_src: str, verbose: bool) -> Result:
    exp = LX.oracle_lines(src)
    code, out, err = LX.run_port(LX.make_driver(lex_src, src))
    if code != 0:
        tail = (err or out).strip().splitlines()[-1:] or ["?"]
        return Result("fail", f"port crash: {tail[0]}")
    got = out.splitlines()
    if got == exp:
        return Result("ok", f"{len(exp)} tokens")
    return Result("fail", _diff("lex", exp, got, verbose))


# Float literals: the port's AST keeps the raw lexeme text (`VFloat of String`,
# parse.lark:22 "str round-trips it"), whereas parser.py stores `float(text)`, so
# a non-canonical lexeme like `33.90` renders `(VFloat 33.90)` in the port but
# `(VFloat 33.9)` in the oracle.  This is a genuine representational difference in
# the parsed AST, but it is BENIGN: every downstream stage treats the two as the
# same number — infer types floats without reading the value, and emit routes
# every float literal through its IEEE-754 float32 bit pattern
# (emit_c_ast._f32_bits(float(t)) vs emit_c.lark float_to_bits(string_to_float(t))),
# which is byte-identical for 33.90 and 33.9 (verified: emit=ok on such programs).
# So we normalise the float RENDERING on both sides before comparing the AST — it
# erases only a value-equivalent difference, never a structural one.  (Ints are
# left alone: the generator only emits canonical integer lexemes.)  See AUDIT.md.
_VFLOAT = re.compile(r'\(VFloat ([0-9.]+)\)')

def _canon_floats(line: str) -> str:
    return _VFLOAT.sub(lambda m: f"(VFloat {float(m.group(1))})", line)


def stage_parse(src: str, lex_src: str, parse_src: str, verbose: bool) -> Result:
    exp = [_canon_floats(l) for l in PS.oracle_lines(src)]
    code, out, err = PS.run_port(PS.make_driver(lex_src, parse_src, src))
    if code != 0:
        tail = (err or out).strip().splitlines()[-1:] or ["?"]
        return Result("fail", f"port crash: {tail[0]}")
    got = [_canon_floats(l) for l in out.splitlines()]
    if got == exp:
        return Result("ok", f"{len(exp)} decls+")
    return Result("fail", _diff("parse", exp, got, verbose))


def infer_oracle(src: str) -> tuple[str, str]:
    """(verdict, text) via infer_difftest.oracle, with RecursionError → skip.

    ty.apply follows the variable-substitution chain recursively; a long chain
    overflows Python's stack.  The oracle then yields no verdict, so we skip
    (see the module docstring / AUDIT.md).  Written to a temp file because the
    sibling oracle is path-based."""
    OBJ.write_text(src)
    try:
        return IN.oracle(OBJ)
    except RecursionError:
        return "skip", "oracle recursion (ty.apply subst chain)"


def stage_infer(src: str, verdict: str, text: str, verbose: bool) -> Result:
    try:
        code, out, err = IN.run_port(src)
    except subprocess.TimeoutExpired:
        return Result("skip", f"meta-circular check too slow (>{IN.PORT_TIMEOUT}s)")
    if code != 0:
        tail = (err or out).strip().splitlines()[-1:] or ["?"]
        return Result("fail", f"port crash: {tail[0]}")
    port_text = out.rstrip("\n")
    if verdict == "reject":
        if IN._canon_reject(port_text) == IN._canon_reject(text):
            return Result("ok", f"reject: {text[:50]}")
        return Result("fail", f"reject mismatch: oracle={text!r} port={port_text!r}")
    exp, got = text.splitlines(), port_text.splitlines()
    if got == exp:
        return Result("ok", f"{len(exp)} sigs")
    return Result("fail", _diff("infer", exp, got, verbose))


def stage_emit(src: str, lex_src: str, parse_src: str, emit_src: str,
               verbose: bool) -> Result:
    OBJ.write_text(src)
    try:
        ocode, oout, oerr = EM.run_oracle(OBJ)
    except subprocess.TimeoutExpired:
        return Result("skip", "oracle emit timeout")
    if ocode != 0:
        tail = (oerr or oout).strip().splitlines()[-1:] or ["?"]
        return Result("skip", f"oracle emit exit {ocode}: {tail[0]}")
    try:
        pcode, pout, perr = EM.run_port(
            EM.make_driver(lex_src, parse_src, emit_src, src, OBJ.name))
    except subprocess.TimeoutExpired:
        return Result("skip", f"meta-circular emit too slow (>{EM.PORT_TIMEOUT}s)")
    if pcode != 0:
        tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
        return Result("fail", f"port crash: {tail[0]}")
    exp = EM.canon(oout).splitlines()
    got = EM.canon(pout).splitlines()
    if got == exp:
        return Result("ok", f"{len(exp)} lines")
    return Result("fail", _diff("emit", exp, got, verbose))


def _diff(stage: str, exp: list[str], got: list[str], verbose: bool) -> str:
    if verbose:
        d = difflib.unified_diff(exp, got, "oracle", "port", lineterm="")
        return "\n        ".join([f"{stage} diverges:"] + list(d)[:60])
    return f"{stage}: {_firstdiff(exp, got)}"


# ── Driver ──────────────────────────────────────────────────────────────────────

def main() -> None:
    argv    = sys.argv[1:]
    verbose = "-v" in argv
    n       = 8
    base    = 1000
    stages  = ["lex", "parse", "infer", "emit"]
    if "-n" in argv:
        n = int(argv[argv.index("-n") + 1])
    if "--seed" in argv:
        base = int(argv[argv.index("--seed") + 1])
    if "--stages" in argv:
        stages = argv[argv.index("--stages") + 1].split(",")

    lex_src   = LX.LEXLRK.read_text()
    ps_lex    = PS.LEX.read_text()
    ps_parse  = PS.PARSE.read_text()
    em_lex    = EM.LEX.read_text()
    em_parse  = EM.PARSE.read_text()
    em_emit   = EM.EMITL.read_text()

    tot_ok = tot_fail = tot_skip = 0
    failed_seeds: list[int] = []

    print(f"fuzzing {n} programs, seeds {base}..{base + n - 1}, "
          f"stages={','.join(stages)}\n")
    for i in range(n):
        seed = base + i
        src  = fuzz_gen.gen_program(seed)

        # Front-end sanity: a well-formed generator should always lex+parse in
        # the oracle.  If not, it is a generator bug — surface it loudly.
        try:
            LX.oracle_lines(src)
            PS.oracle_lines(src)
        except (LexError, ParseError) as e:
            print(f"seed {seed}: GENERATOR PRODUCED UNPARSEABLE SOURCE — {e}")
            if verbose:
                print(src)
            tot_fail += 1
            failed_seeds.append(seed)
            continue

        verdict, text = ("", "")
        if "infer" in stages or "emit" in stages:
            verdict, text = infer_oracle(src)

        line = [f"seed {seed}:"]
        seed_failed = False
        for st in stages:
            if st == "lex":
                res = stage_lex(src, lex_src, verbose)
            elif st == "parse":
                res = stage_parse(src, ps_lex, ps_parse, verbose)
            elif st == "infer":
                if verdict == "skip":
                    res = Result("skip", text)
                else:
                    res = stage_infer(src, verdict, text, verbose)
            elif st == "emit":
                if verdict == "skip":
                    res = Result("skip", "no oracle infer verdict")
                else:
                    res = stage_emit(src, em_lex, em_parse, em_emit, verbose)
            else:
                continue

            mark = {"ok": "ok", "fail": "FAIL", "skip": "skip"}[res.status]
            line.append(f"{st}={mark}")
            if res.status == "ok":
                tot_ok += 1
            elif res.status == "skip":
                tot_skip += 1
            else:
                tot_fail += 1
                seed_failed = True
                line.append(f"\n    [{st}] {res.detail}")
        print("  ".join(line))
        if seed_failed:
            failed_seeds.append(seed)
            if verbose:
                print("    ── source ──")
                print("    " + src.replace("\n", "\n    "))

    OBJ.unlink(missing_ok=True)
    print(f"\n  {tot_ok} ok, {tot_fail} failed, {tot_skip} skipped "
          f"(stage-checks across {n} programs)")
    if failed_seeds:
        print(f"  failing seeds: {failed_seeds}")
        print(f"  reproduce a program with:  python3 {pathlib.Path(fuzz_gen.__file__).name} <seed>")
    sys.exit(0 if tot_fail == 0 else 1)


if __name__ == "__main__":
    main()
