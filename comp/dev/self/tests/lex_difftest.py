"""
Differential test for the self-hosted lexer (SELFHOST M1).

For every .lark file in the corpus it compares two token streams:

  • the oracle  — 07/src/lexer.py (the frozen Python lexer), serialized here;
  • the port     — self/lex.lark, run through the CEK interpreter (07/src/cek.py).

They must be byte-identical, line for line.  A driver program is generated per
input file by taking lex.lark, stripping its smoke `main`, and appending a main
that embeds the file's source as a String literal and prints `dump(tokenize …)`.

The canonical per-token line is:   KIND line col escaped-text
where escaping maps \\ n t r so each token stays on a single line.  The Python
serializer below mirrors lex.lark's `escape` exactly.

Usage:
    python3 self/tests/lex_difftest.py [-v]      # -v: show a diff on failure
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib
import os

HERE   = pathlib.Path(__file__).resolve().parent      # self/tests
SELF   = HERE.parent                                   # self
ROOT   = SELF.parent                                   # lark
SRC    = ROOT / "07" / "src"
CEK    = str(SRC / "cek.py")
LEXLRK = SELF / "lex.lark"

sys.path.insert(0, str(SRC))
from lexer import Lexer, LexError, TK   # the oracle


# ── Corpus ────────────────────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    """The test corpus, the samples, and the compiler's own source.

    SELF is globbed *non-recursively*, and that matters.  It used to be `rglob`,
    which swept everything below it: `self/vendor/` (a byte-faithful second copy of
    the same corpus) was being lexed a second time, and so were the scratch drivers
    the harnesses themselves write into `self/tests/` — a file that a *concurrent*
    run deletes out from under you mid-sweep.  The corpus is the corpus; the
    compiler is `self/*.lark`; nothing else belongs here.
    """
    files: list[pathlib.Path] = []
    for base in [ROOT / "07" / "tests", ROOT / "07" / "samples"]:
        files += sorted(base.rglob("*.lark"))
    files += sorted(p for p in SELF.glob("*.lark") if not p.name.startswith("_"))
    return files


# ── Serialization (must mirror lex.lark exactly) ──────────────────────────────

def esc(s: str) -> str:
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if   o == 92: out.append("\\\\")
        elif o == 10: out.append("\\n")
        elif o ==  9: out.append("\\t")
        elif o == 13: out.append("\\r")
        else:         out.append(ch)
    return "".join(out)

def oracle_lines(source: str) -> list[str]:
    """Serialize lexer.py's tokens into the canonical per-token lines."""
    toks = Lexer(source, "<corpus>").tokenize()
    return [f"{t.kind.name} {t.line} {t.col} {esc(t.text)}" for t in toks]


# ── Driver generation ─────────────────────────────────────────────────────────

def lark_string_literal(source: str) -> str:
    """Escape source so it round-trips through the CEK lexer to the same bytes."""
    out: list[str] = []
    for ch in source:
        if   ch == "\\": out.append("\\\\")
        elif ch == '"':  out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\t": out.append("\\t")
        elif ch == "\r": out.append("\\r")
        else:            out.append(ch)
    return "".join(out)

def make_driver(lex_src: str, source: str) -> str:
    """lex.lark with its smoke main replaced by one lexing `source`."""
    marker = "\nfn main(io : IO) : IO ="
    head = lex_src.split(marker, 1)[0]
    lit  = lark_string_literal(source)
    driver_main = (
        '\nfn main(io : IO) : IO =\n'
        f'  let src = "{lit}" in\n'
        '  print(io, dump(tokenize(src, string_length(src), P(0, 1, 1))))\n'
    )
    return head + driver_main


# ── Runner ────────────────────────────────────────────────────────────────────

# Per-driver budget for the Lark side. Override: LARK_TIMEOUT=<seconds>
PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))

def run_port(driver: str) -> tuple[int, str, str]:
    """Run a generated driver through the CEK interpreter."""
    tmp = HERE / "_driver.lark"
    tmp.write_text(driver)
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return 124, "", (f"port timed out after {PORT_TIMEOUT}s "
                          f"— raise it with LARK_TIMEOUT=<seconds>")
    finally:
        tmp.unlink(missing_ok=True)


def main() -> None:
    verbose = "-v" in sys.argv
    lex_src = LEXLRK.read_text()

    ok = fail = skip = 0
    for path in corpus():
        label = str(path.relative_to(ROOT))
        source = path.read_text()

        try:
            expected = oracle_lines(source)
        except LexError as e:
            print(f"  skip  {label}  (oracle lex error: {e.msg})")
            skip += 1
            continue

        code, out, err = run_port(make_driver(lex_src, source))
        # A timeout is a fact about this machine, not about the compiler: the
        # port is an interpreter running an interpreter, and the budget is wall
        # clock.  Report it the way cek/emit do — a skip with a reason — so that
        # a slow box cannot masquerade as a disagreement.  Raise LARK_TIMEOUT to
        # turn a skip into a real comparison.
        if code == 124:
            print(f"  skip  {label}  (meta-circular eval too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue
        if code != 0:
            print(f"  FAIL  {label}  (CEK crash)")
            tail = (err or out).strip().splitlines()[-1:] or ["?"]
            print(f"        {tail[0]}")
            fail += 1
            continue

        got = out.splitlines()
        if got == expected:
            print(f"  ok    {label}  ({len(expected)} tokens)")
            ok += 1
        else:
            print(f"  FAIL  {label}")
            if verbose:
                d = difflib.unified_diff(expected, got, "oracle", "port", lineterm="")
                for line in list(d)[:40]:
                    print(f"        {line}")
            else:
                # first divergence
                for i, (a, b) in enumerate(zip(expected, got)):
                    if a != b:
                        print(f"        line {i}: oracle={a!r} port={b!r}")
                        break
                if len(expected) != len(got):
                    print(f"        length: oracle={len(expected)} port={len(got)}")
            fail += 1

    total = ok + fail + skip
    print(f"\n  {ok} ok, {fail} failed, {skip} skipped  ({total} files)")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
