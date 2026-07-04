"""
Lark differential test runner — runs each acceptance test through all three
backends (CEK, TAC VM, RV32 VM) and asserts outputs are byte-identical.
Reports any unexpected divergence with the backend names and a unified diff.

Usage:
    python3 tests/diff_test.py
"""

from __future__ import annotations
import subprocess, sys, pathlib, difflib

ROOT    = pathlib.Path(__file__).parent
SRC     = ROOT.parent / "src"
CEK     = str(SRC / "cek.py")
TAC_VM  = str(SRC / "tac_vm.py")
RV32_VM = str(SRC / "riscv_vm.py")

BACKENDS: list[tuple[str, str]] = [
    ("CEK",  CEK),
    ("TAC",  TAC_VM),
    ("RV32", RV32_VM),
]

# Tests where some backends are expected to produce different output.
# "agree" lists the backend names that MUST produce identical output.
# Backends not in "agree" are allowed to diverge; a note is shown.
# Phase 8: empty — Int is a wrapping i32 everywhere, so the two former
# overflow divergences (04_tailrec, 19_intoverflow) now agree by definition.
XFAIL: dict[str, dict] = {}


def run(path: pathlib.Path, runner: str) -> tuple[int, str, str]:
    """Run a Lark file through one backend. Returns (exit_code, stdout, stderr).
    exit_code == -1 means timeout."""
    try:
        r = subprocess.run(
            [sys.executable, runner, str(path)],
            capture_output=True, text=True, timeout=60,
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def collect_acceptance() -> list[pathlib.Path]:
    paths: list[pathlib.Path] = []
    for item in sorted(ROOT.iterdir()):
        name = item.name
        if not (name[0].isdigit() and name != "errors"):
            continue
        if item.is_file() and item.suffix == ".lark":
            paths.append(item)
        elif item.is_dir():
            main = item / "main.lark"
            if main.exists():
                paths.append(main)
    return paths


def collect_error_tests() -> list[pathlib.Path]:
    error_dir = ROOT / "errors"
    if not error_dir.exists():
        return []
    return sorted(error_dir.glob("*.lark"))


def udiff(a: str, b: str, name_a: str, name_b: str) -> str:
    la = a.splitlines(keepends=True)
    lb = b.splitlines(keepends=True)
    return "".join(difflib.unified_diff(la, lb, fromfile=name_a, tofile=name_b))


def _classify(code: int, out: str, err: str) -> tuple[str, str]:
    """Return (status, detail) for a backend run result."""
    if code == -1:
        return "TIMEOUT", ""
    if code != 0:
        tail = (err or out).strip().splitlines()[-1] if (err or out).strip() else "?"
        return "CRASH", tail
    return "OK", out


def main() -> None:
    ok = fail = 0

    print("── Acceptance tests (cross-backend diff) ───────────────────")

    for path in collect_acceptance():
        label = str(path.relative_to(ROOT))
        name  = path.name
        xfail = XFAIL.get(name)
        agree_set: set[str] = set(xfail["agree"]) if xfail else {"CEK", "TAC", "RV32"}

        raw: dict[str, tuple[int, str, str]] = {}
        for bname, runner in BACKENDS:
            raw[bname] = run(path, runner)

        # Only the agree backends must produce identical successful output.
        # Use BACKENDS order so agree[0] is always deterministic.
        agree = [(b, _classify(*raw[b])) for b, _ in BACKENDS if b in agree_set]

        if not agree:
            print(f"  FAIL  {label}  (no agree backends configured)")
            fail += 1
            continue

        # Crashes or timeouts on agree backends are immediate failures.
        bad = [(b, status, detail) for b, (status, detail) in agree if status != "OK"]
        if bad:
            print(f"  FAIL  {label}")
            for b, status, detail in bad:
                print(f"    {b}: {status}" + (f" — {detail}" if detail else ""))
            fail += 1
            continue

        # All agree backends ran successfully — check that outputs match.
        first_b, (_, first_out) = agree[0]
        mismatches = [
            (b, out) for b, (_, out) in agree[1:] if out != first_out
        ]

        if mismatches:
            print(f"  FAIL  {label}")
            for b, out in mismatches:
                d = udiff(first_out, out, first_b, b)
                for line in d.splitlines():
                    print(f"    {line}")
            fail += 1
        elif xfail:
            non_agree = [(b, _classify(*raw[b])) for b in raw if b not in agree_set]
            diverged = any(out != first_out for _, (_, out) in non_agree)
            if diverged:
                print(f"  xfail {label:<40} ({xfail['note']})")
            else:
                print(f"  XPASS {label:<40} (was xfail: {xfail['note']})")
            ok += 1
        else:
            print(f"  ok    {label}")
            ok += 1

    print(f"\n  {ok} ok, {fail} divergences")

    print("\n── Error tests (all backends must exit non-zero) ───────────")
    err_ok = err_fail = 0

    for path in collect_error_tests():
        label = str(path.relative_to(ROOT))
        raw = {b: run(path, r) for b, r in BACKENDS}

        problems = []
        for b, (code, out, err) in raw.items():
            if code == 0:
                problems.append((b, "exit=0 (expected non-zero)"))
            elif code == -1:
                problems.append((b, "TIMEOUT"))

        if problems:
            print(f"  FAIL  {label}")
            for b, reason in problems:
                print(f"    {b}: {reason}")
            err_fail += 1
        else:
            msgs = {
                b: ((err or out).strip().splitlines()[-1] if (err or out).strip() else "?")
                for b, (code, out, err) in raw.items()
            }
            print(f"  ok    {label}")
            for b, msg in msgs.items():
                print(f"    {b}: {msg}")
            err_ok += 1

    print(f"\n  {err_ok} ok, {err_fail} failed")

    total_fail = fail + err_fail
    print(f"\n  total: {ok + err_ok} passed, {total_fail} failed")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
