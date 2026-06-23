"""
Lark test runner — checks acceptance tests against embedded expected output
and confirms that error tests exit non-zero.

Usage:
    python3 tests/run_tests.py
"""

from __future__ import annotations
import re, subprocess, sys, pathlib

ROOT = pathlib.Path(__file__).parent
SRC  = ROOT.parent / "src"
CEK  = str(SRC / "cek.py")


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


def run(path: pathlib.Path) -> tuple[int, str, str]:
    r = subprocess.run(
        [sys.executable, CEK, str(path)],
        capture_output=True, text=True, timeout=60,
    )
    return r.returncode, r.stdout, r.stderr


def check_acceptance(path: pathlib.Path) -> tuple[bool, str]:
    try:
        code, out, err = run(path)
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

    print("── acceptance ──────────────────────────────────────────────")
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

    print(f"\n  {ok} passed, {fail} failed")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
