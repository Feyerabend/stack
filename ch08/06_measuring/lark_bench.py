"""
Measuring honestly — Chapter 8, §8.6.

Times sum_to(0, n) through Lark's three backends -- the CEK tree-walking
interpreter, the TAC virtual machine, and the RV32 machine -- for a range of n,
isolating execution time by subtracting a tiny-n baseline (startup + compile).

The point is the lesson, not the leaderboard. All three backends here are
Python programs: the RV32 "machine" is a *software simulator* that interprets
each RISC-V instruction in Python, so it carries per-instruction host overhead
and is, in this setting, no faster than the tree-walker -- sometimes slower. The
two-to-three orders of magnitude that compilation buys appear only when the
emitted code runs on real silicon (the Raspberry Pi Pico 2W of Chapter 9), not
on a host simulation of it. A benchmark that measures the wrong target misleads;
demonstrating that is exactly the point of this one.

Run:  python3 lark_bench.py
"""

from __future__ import annotations
import sys, time, subprocess, pathlib, tempfile

# Locate lark/06/src relative to this file's place in the repo.
LARK_SRC = None
for up in pathlib.Path(__file__).resolve().parents:
    cand = up / "lark" / "06" / "src"
    if cand.exists():
        LARK_SRC = cand
        break
if LARK_SRC is None:
    sys.exit("could not locate lark/06/src -- run this from inside the repository")

BACKENDS = [("CEK (tree-walk)", "cek.py"),
            ("TAC VM",          "tac_vm.py"),
            ("RV32 (simulated)", "riscv_vm.py")]

# sum_to(0, n) = n(n+1)/2; keep n small enough that the sum stays below 2^31,
# since Lark's Int is 32-bit (sum_to(0, 60000) ~ 1.8e9 < 2.147e9).
NS = [10, 20000, 40000]          # the first is the startup+compile baseline
REPEATS = 3


def program(n: int) -> str:
    return (f"module Bench\n"
            f"fn sum_to(acc : Int, n : Int) : Int =\n"
            f"    if n == 0 then acc else sum_to(acc + n, n - 1)\n"
            f"fn main(io : IO) : IO = print(io, show(sum_to(0, {n})))\n")


def time_backend(backend: str, src: pathlib.Path) -> tuple[float, str]:
    best, out = float("inf"), ""
    for _ in range(REPEATS):
        t0 = time.perf_counter()
        r = subprocess.run([sys.executable, str(LARK_SRC / backend), str(src)],
                           capture_output=True, text=True, timeout=180)
        best = min(best, time.perf_counter() - t0)
        out = r.stdout.strip()
    return best, out


def main() -> None:
    tmp = pathlib.Path(tempfile.mkdtemp())
    srcs = {n: (tmp / f"st_{n}.lark") for n in NS}
    for n, p in srcs.items():
        p.write_text(program(n))

    print(f"sum_to(0, n) through lark/06 backends -- min of {REPEATS} runs, wall seconds")
    print(f"(answers must match across backends; the last column subtracts the "
          f"n={NS[0]} baseline)\n")
    header = f"{'backend':<18}" + "".join(f"n={n:<9}" for n in NS) + f"exec(n={NS[-1]})"
    print(header)
    print("-" * len(header))

    answers = set()
    for name, bk in BACKENDS:
        times = {}
        for n in NS:
            t, out = time_backend(bk, srcs[n])
            times[n] = t
            if n == NS[-1]:
                answers.add(out)
        exec_time = times[NS[-1]] - times[NS[0]]
        print(f"{name:<18}" + "".join(f"{times[n]:<11.3f}" for n in NS) + f"{exec_time:.3f}")

    print()
    print(f"all backends returned the same answer: {answers == set(list(answers)[:1]) and len(answers)==1}")
    print(f"answer(s): {sorted(answers)}")
    print()
    print("Reading this honestly:")
    print("  * The three numbers are the same order of magnitude because all three")
    print("    backends are Python. The RV32 column is a *simulation* of machine code,")
    print("    not machine code; it pays Python overhead on every simulated instruction.")
    print("  * If you concluded from this that 'compiling did not help', you would be")
    print("    wrong -- you measured a host simulator, not the target. The real win is")
    print("    native execution on the Pico 2W (Chapter 9), which this script cannot time.")
    print("  * That is the §8.6 lesson: measure the thing you will actually ship, on the")
    print("    target you will actually run, or the measurement lies to you.")


if __name__ == "__main__":
    main()
