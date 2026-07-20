"""
cek_test.py — Run all corpus files through the C CEK machine and compare
output to the Python CEK (the correctness oracle).

For each test file:
  1. Run Python CEK → capture stdout/stderr and exit code.
  2. Emit C AST (emit_c_ast.py) → compile with cek.c + larkrun.c → run binary.
  3. Assert the outputs are identical and exit codes agree (zero/non-zero).

Exit codes: 0 = all passed, 1 = at least one failure.
"""

from __future__ import annotations
import os, subprocess, sys, tempfile, pathlib, textwrap

HERE    = pathlib.Path(__file__).parent
REPO    = HERE.parent
SRC     = REPO / 'src'
TESTS   = HERE

# Files to test: all numbered acceptance tests + module tests + error tests.
# 09_modules/ is a directory; its entry point is main.lark.
ACCEPT = sorted(TESTS.glob('[0-9][0-9]_*.lark')) + [TESTS / '09_modules' / 'main.lark']
ERRORS = sorted((TESTS / 'errors').glob('*.lark'))

# Tests known to be non-deterministic or hardware-specific — skip for now.
SKIP = {
    '04_tailrec.lark',       # sum_to(1_000_000) = 500_000_500_000 overflows int32_t
    '19_intoverflow.lark',   # RV32 32-bit overflow: CEK gives Python int, not truncated
}

CC     = os.environ.get('CC', 'cc')
# Use a large arena for test builds; tail-recursive programs need O(n) arena
# with the current bump-pointer allocator.  The static BSS is mmap'd on demand
# on both Linux and macOS, so 256 MB costs nothing if unused.
CFLAGS = ['-std=c11', '-O2', '-Wall', '-Wextra', '-Wno-unused-parameter',
          '-DLARK_ARENA_SIZE=(256u*1024u*1024u)']


# ── Python CEK oracle ─────────────────────────────────────────────────────

def run_python_cek(lark_file: pathlib.Path) -> tuple[bytes, int]:
    """Run the Python CEK; return (stdout+stderr, exit_code)."""
    result = subprocess.run(
        [sys.executable, str(SRC / 'cek.py'), str(lark_file)],
        capture_output=True, timeout=60,
    )
    return result.stdout + (result.stderr if result.returncode != 0 else b''), result.returncode


# ── C CEK ─────────────────────────────────────────────────────────────────

def build_c_cek(lark_file: pathlib.Path, prog_c: str, binary: str) -> str | None:
    """
    Emit C AST for lark_file into prog_c, compile to binary.
    Returns None on success, or an error string on failure.
    """
    # Step 1: emit
    r = subprocess.run(
        [sys.executable, str(SRC / 'emit_c_ast.py'), str(lark_file), prog_c],
        capture_output=True, timeout=15,
    )
    if r.returncode != 0:
        return f'emit_c_ast failed:\n{r.stderr.decode()}'

    # Step 2: compile
    r = subprocess.run(
        [CC] + CFLAGS + [f'-I{SRC}',
         str(SRC / 'cek.c'), str(SRC / 'larkrun.c'), prog_c,
         '-o', binary, '-lm'],
        capture_output=True, timeout=30,
    )
    if r.returncode != 0:
        return f'compile failed:\n{r.stderr.decode()}'

    return None


def run_c_cek(binary: str) -> tuple[bytes, int]:
    result = subprocess.run([binary], capture_output=True, timeout=15)
    return result.stdout + (result.stderr if result.returncode != 0 else b''), result.returncode


# ── Test runner ───────────────────────────────────────────────────────────

def run_tests(files: list[pathlib.Path], label: str) -> tuple[int, int]:
    """Return (passed, failed)."""
    passed = failed = 0

    with tempfile.TemporaryDirectory() as tmp:
        prog_c = os.path.join(tmp, 'prog_ast.c')
        binary = os.path.join(tmp, 'larkrun')

        for lark_file in files:
            name = lark_file.name
            if name in SKIP:
                print(f'  SKIP  {name}')
                continue

            py_out, py_rc = run_python_cek(lark_file)

            err = build_c_cek(lark_file, prog_c, binary)
            if err:
                # For error tests: a compile-time rejection by emit_c_ast is
                # the expected C-pipeline behaviour.  Count it as ok when the
                # Python CEK also rejected the program (non-zero exit).
                if label == 'error' and py_rc != 0:
                    print(f'  ok    {name}  (compile-time error)')
                    passed += 1
                else:
                    print(f'  FAIL  {name}  (build error)')
                    print(textwrap.indent(err, '        '))
                    failed += 1
                continue

            c_out, c_rc = run_c_cek(binary)

            # For error tests: both must exit non-zero (exact output may differ).
            # For acceptance tests: outputs must be byte-identical and both zero.
            if label == 'error':
                if (py_rc != 0) == (c_rc != 0):
                    print(f'  ok    {name}')
                    passed += 1
                else:
                    print(f'  FAIL  {name}  '
                          f'(py_rc={py_rc} c_rc={c_rc})')
                    failed += 1
            else:
                if py_out == c_out and py_rc == c_rc:
                    print(f'  ok    {name}')
                    passed += 1
                else:
                    print(f'  FAIL  {name}')
                    if py_out != c_out:
                        import difflib
                        diff = difflib.unified_diff(
                            py_out.decode(errors='replace').splitlines(keepends=True),
                            c_out.decode(errors='replace').splitlines(keepends=True),
                            fromfile='python-cek', tofile='c-cek', n=3,
                        )
                        print(''.join(diff))
                    if py_rc != c_rc:
                        print(f'        exit: python={py_rc} c={c_rc}')
                    failed += 1

    return passed, failed


def main() -> int:
    total_pass = total_fail = 0

    print('── Acceptance tests ──────────────────────────────────────────────')
    p, f = run_tests(ACCEPT, 'accept')
    total_pass += p; total_fail += f

    print('── Error tests ───────────────────────────────────────────────────')
    p, f = run_tests(ERRORS, 'error')
    total_pass += p; total_fail += f

    print()
    print(f'{total_pass} passed, {total_fail} failed')
    return 0 if total_fail == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
