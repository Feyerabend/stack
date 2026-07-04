"""
Lark test runner — checks acceptance tests against embedded expected output
and confirms that error tests exit non-zero.

Usage:
    python3 tests/run_tests.py
"""

from __future__ import annotations
import re, subprocess, sys, pathlib

ROOT    = pathlib.Path(__file__).parent
SRC     = ROOT.parent / "src"
CEK     = str(SRC / "cek.py")
TAC_VM  = str(SRC / "tac_vm.py")
RV32_VM = str(SRC / "riscv_vm.py")

TAC_VM_SKIP: set[str] = set()

# RV32 VM known limitations:
#   xfail = expected failure with reason (wrong output, not crash)
#   skip  = no output expected at all (not yet implemented)
# Phase 8: empty — Int is a wrapping i32 in every backend, so the former
# overflow xfail (04_tailrec) now passes everywhere with the same output.
RV32_SKIP:  set[str] = set()
RV32_XFAIL: dict[str, str] = {}


def extract_expected(path: pathlib.Path) -> list[str] | None:
    text = path.read_text()
    m = re.search(r'Expected output:\s*\n((?:[ \t]+\S[^\n]*\n?)+)', text)
    if not m:
        return None
    lines = []
    for line in m.group(1).splitlines():
        s = line.strip()
        # Strip the Lark comment-close token that may end the last line
        s = re.sub(r'\s*\*\)\s*$', '', s)
        if s:
            lines.append(s)
    return lines


def run(path: pathlib.Path, runner: str = CEK) -> tuple[int, str, str]:
    r = subprocess.run(
        [sys.executable, runner, str(path)],
        capture_output=True, text=True, timeout=60,
    )
    return r.returncode, r.stdout, r.stderr


def check_acceptance(
    path: pathlib.Path, runner: str = CEK,
) -> tuple[bool, str]:
    try:
        code, out, err = run(path, runner)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    if code != 0:
        last = (err or out).strip().splitlines()[-1] if (err or out).strip() else "?"
        return False, f"CRASH: {last}"
    expected = extract_expected(path)
    if expected is None:
        return True, "ok (no expected)"
    actual = [l for l in out.splitlines() if l]
    if actual == expected:
        return True, "ok"
    lines = []
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            lines.append(f"    line {i+1}: got {a!r}, want {e!r}")
    if len(actual) != len(expected):
        lines.append(f"    {len(actual)} lines, expected {len(expected)}")
    return False, "FAIL\n" + "\n".join(lines)


def check_error(path: pathlib.Path) -> tuple[bool, str]:
    try:
        code, out, err = run(path)
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    if code != 0:
        msg = (err or out).strip().splitlines()[-1] if (err or out).strip() else "?"
        return True, f"ok ({msg})"
    return False, "FAIL (expected non-zero exit)"


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


def main() -> None:
    ok = fail = 0

    print("── CEK machine ─────────────────────────────────────────────")
    for path in collect_acceptance():
        label = str(path.relative_to(ROOT))
        passed, msg = check_acceptance(path)
        print(f"  {'ok' if passed else 'FAIL':<4}  {label:<40} {msg}")
        if passed: ok += 1
        else:       fail += 1

    error_dir = ROOT / "errors"
    if error_dir.exists():
        print("\n── error tests ─────────────────────────────────────────────")
        for path in sorted(error_dir.glob("*.lark")):
            label = str(path.relative_to(ROOT))
            passed, msg = check_error(path)
            print(f"  {'ok' if passed else 'FAIL':<4}  {label:<40} {msg}")
            if passed: ok += 1
            else:       fail += 1

    print("\n── TAC VM ──────────────────────────────────────────────────")
    tac_ok = tac_fail = tac_skip = 0
    for path in collect_acceptance():
        if path.name in TAC_VM_SKIP:
            print(f"  skip  {str(path.relative_to(ROOT)):<40} (not yet implemented)")
            tac_skip += 1
            continue
        label = str(path.relative_to(ROOT))
        passed, msg = check_acceptance(path, runner=TAC_VM)
        print(f"  {'ok' if passed else 'FAIL':<4}  {label:<40} {msg}")
        if passed: tac_ok += 1
        else:       tac_fail += 1
    print(f"\n  TAC VM: {tac_ok} passed, {tac_fail} failed, {tac_skip} skipped")

    print("\n── RV32 VM ─────────────────────────────────────────────────")
    rv_ok = rv_fail = rv_skip = rv_xfail = 0
    for path in collect_acceptance():
        name  = path.name
        label = str(path.relative_to(ROOT))
        if name in RV32_SKIP:
            print(f"  skip  {label:<40} (not yet implemented)")
            rv_skip += 1
            continue
        if name in RV32_XFAIL:
            reason = RV32_XFAIL[name]
            passed, msg = check_acceptance(path, runner=RV32_VM)
            if not passed:
                print(f"  xfail {label:<40} ({reason})")
                rv_xfail += 1
            else:
                print(f"  XPASS {label:<40} (was expected to fail: {reason})")
                rv_fail += 1
            continue
        passed, msg = check_acceptance(path, runner=RV32_VM)
        print(f"  {'ok' if passed else 'FAIL':<4}  {label:<40} {msg}")
        if passed: rv_ok += 1
        else:       rv_fail += 1
    print(f"\n  RV32 VM: {rv_ok} passed, {rv_fail} failed, {rv_xfail} xfail, {rv_skip} skipped")

    total_fail = fail + tac_fail + rv_fail
    print(f"\n  total: {ok + tac_ok + rv_ok} passed, {total_fail} failed")
    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()
