"""
Differential test for emit_tac_c.py (the M7.0 TAC→C oracle).

For each acceptance corpus file, at each -O level, run
    parse → typecheck → lower → optimize → emit_tac_c → clang → run
and assert the program's stdout is byte-identical to the CEK reference
(cek.py) on the same file.  CEK is the semantic ground truth.

The corpus is run with an empty stdin (matching diff_test.py), so `read`
sees EOF.  clang is invoked with -fwrapv so signed Int overflow wraps
two's-complement, matching the VM word model.

Usage:
    python3 tests/emit_tac_c_difftest.py [-O0 -O1 -O2 -O3]   # default: all
"""

from __future__ import annotations
import subprocess, sys, pathlib, tempfile, os

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT.parent / "src"
CEK  = str(SRC / "cek.py")
EMIT = str(SRC / "emit_tac_c.py")

# Expected divergences from CEK that are NOT emit_tac_c bugs.  The xfail branch
# only fires when output actually differs, so a file listed here still shows
# "ok" at any -O level where it happens to match.
#
#   19_intoverflow — at -O1+ the optimizer's constant-folder evaluates
#     `100000 * 100001` with 32-bit wrap (opt._wrap32; its target is the 32-bit
#     RV32 backend) and bakes 1410165408 into the TAC as a Const.  emit_tac_c
#     faithfully emits that folded literal, so it diverges from CEK's
#     arbitrary-precision 10000100000.  At -O0 (no folding) the 64-bit runtime
#     matches CEK.  This is the same class as diff_test.py's RV32 XFAIL for this
#     file — a 32-bit-vs-bignum artifact, surfaced here through the fold width.
XFAIL_64BIT: set[str] = {"19_intoverflow.lark"}


def collect() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for item in sorted(ROOT.iterdir()):
        if not (item.name[0].isdigit()):
            continue
        if item.is_file() and item.suffix == ".lark":
            paths.append(item)
        elif item.is_dir():
            m = item / "main.lark"
            if m.exists():
                paths.append(m)
    return paths


def cek_out(path: pathlib.Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, CEK, str(path)],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL,
                       timeout=120)
    return r.returncode, r.stdout


def emit_out(path: pathlib.Path, level: int, workdir: str) -> tuple[bool, str]:
    """Emit C, compile, run.  Returns (ok, stdout_or_error)."""
    c = subprocess.run([sys.executable, EMIT, str(path), f"-O{level}"],
                       capture_output=True, text=True, timeout=120)
    if c.returncode != 0:
        return False, "emit failed: " + (c.stderr.strip().splitlines() or ["?"])[-1]
    cfile = os.path.join(workdir, "prog.c")
    exe   = os.path.join(workdir, "prog")
    with open(cfile, "w") as f:
        f.write(c.stdout)
    b = subprocess.run(["clang", "-O2", "-fwrapv", "-w", cfile, "-o", exe],
                       capture_output=True, text=True, timeout=120)
    if b.returncode != 0:
        return False, "clang failed: " + (b.stderr.strip().splitlines() or ["?"])[-1]
    try:
        r = subprocess.run([exe], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL, timeout=120)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    if r.returncode != 0:
        return False, f"runtime exit={r.returncode}"
    return True, r.stdout


def main() -> None:
    levels = [int(a[2:]) for a in sys.argv[1:] if a.startswith("-O")]
    if not levels:
        levels = [0, 1, 2, 3]

    total_ok = total_fail = total_skip = 0
    with tempfile.TemporaryDirectory() as wd:
        for level in levels:
            print(f"── emit_tac_c vs CEK,  -O{level} ─────────────────────────")
            ok = fail = skip = 0
            for path in collect():
                label = path.relative_to(ROOT).as_posix()
                code, want = cek_out(path)
                if code != 0:
                    print(f"  skip  {label}  (CEK exit={code})")
                    skip += 1
                    continue
                good, got = emit_out(path, level, wd)
                if not good:
                    print(f"  FAIL  {label}  — {got}")
                    fail += 1
                elif got != want:
                    if path.name in XFAIL_64BIT:
                        print(f"  xfail {label}  (64-bit vs bignum)")
                        ok += 1
                    else:
                        print(f"  FAIL  {label}  — output differs from CEK")
                        wl, gl = want.splitlines(), got.splitlines()
                        for i in range(max(len(wl), len(gl))):
                            a = wl[i] if i < len(wl) else "<none>"
                            b = gl[i] if i < len(gl) else "<none>"
                            if a != b:
                                print(f"        CEK[{i}]: {a!r}")
                                print(f"        C  [{i}]: {b!r}")
                                break
                        fail += 1
                else:
                    print(f"  ok    {label}")
                    ok += 1
            print(f"  → {ok} ok, {fail} fail, {skip} skip\n")
            total_ok += ok; total_fail += fail; total_skip += skip

    print(f"TOTAL: {total_ok} ok, {total_fail} fail, {total_skip} skip")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
