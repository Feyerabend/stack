#!/usr/bin/env python3
"""
optbench — the OPTIMIZE O0 measurement + correctness ruler.

Measures the RV32I backend's output per corpus file × per -O level, so every
optimization pass can be attributed a before/after number (OPTIMIZE.md §6). Built
BEFORE any pass exists: at -O0 the optimizer (src/opt.py) is the identity, so this
first run baselines the current, un-optimized code generator.

Metrics per (file, level):
  asm_instrs   static RV32I instruction lines emitted (asm.gen output)
  bin_bytes    assembled binary size (bytes; text + data)
  dyn_instrs   executed RV32I instructions (riscv_vm counter)
  stub_calls   runtime-stub invocations (print/alloc/show/... intercepts)
  heap_allocs  heap objects bump-allocated at run time (the Tier-3 headline)
  heap_bytes   total heap bytes bump-allocated
  compile_s    wall-clock: parse→typecheck→lower→optimize→gen→assemble
  run_s        wall-clock: VM execution

Correctness (OPTIMIZE.md §2/§6): OBSERVABLE-EQUIVALENCE. For every file, the
program output (sha) at each level must equal the -O0 output. optbench flags any
divergence. (At O0-only this is trivially satisfied; the check goes live the
moment a pass changes emitted code.)

Usage:
  python3 tests/optbench.py                     # all acceptance files, -O0
  python3 tests/optbench.py --levels 0,1        # compare levels; equivalence-check
  python3 tests/optbench.py --file 02_arithmetic.lark --levels 0,1
  python3 tests/optbench.py --save baseline_O0.json
  python3 tests/optbench.py --compare baseline_O0.json    # diff vs a saved run
  python3 tests/optbench.py --pass-flags        # list toggleable passes/levels

Each (file, level) runs in a subprocess (--worker) so a runaway VM is bounded by
--timeout (default 120 s) rather than wedging the whole sweep.
"""
from __future__ import annotations
import sys, os, io, json, time, argparse, subprocess, hashlib, contextlib, pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE                       # tests/
SRC  = HERE.parent / "src"
sys.path.insert(0, str(SRC))


# ── file collection (mirrors diff_test.collect_acceptance) ───────────────────

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


def rel(path: pathlib.Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# ── worker: compile + run one (file, level), print a JSON metrics line ───────

def _count_asm_instrs(asm: str) -> int:
    """Static RV32I instruction lines: non-blank, non-label, non-directive."""
    n = 0
    for ln in asm.split("\n"):
        s = ln.split("#", 1)[0].strip()
        if not s or s.endswith(":") or s.startswith("."):
            continue
        n += 1
    return n


def run_worker(file: str, level: int, max_cycles: int) -> dict:
    import parser as P, infer as I
    from lower import lower
    from asm import gen
    from riscv_asm import assemble_lark
    from riscv_vm import LarkVM
    from opt import optimize, postgen, OptOptions, wants_graph_coloring
    from coloring import allocate_tac_color

    t0 = time.perf_counter()
    prog  = P.parse_file(file)
    tprog = I.typecheck(prog, source_file=file)
    tac   = lower(tprog)
    opts  = OptOptions.O(level)
    tac   = optimize(tac, opts)
    # O4 increment 2: graph-coloring regalloc when enabled, else linear scan.
    allocator = allocate_tac_color if wants_graph_coloring(opts) else None
    asm   = gen(tac, allocator=allocator)
    asm   = postgen(asm, opts)         # post-gen RV32I peephole (O4)
    binary, labels = assemble_lark(asm)
    compile_s = time.perf_counter() - t0

    vm = LarkVM()
    if max_cycles:
        vm.MAX_CYCLES = max_cycles
    vm.load(binary, labels)

    buf = io.StringIO()
    # Feed an empty stdin so `read`-using programs terminate deterministically.
    saved_stdin, sys.stdin = sys.stdin, io.StringIO("")
    t1 = time.perf_counter()
    try:
        with contextlib.redirect_stdout(buf):
            vm.run()
    finally:
        run_s = time.perf_counter() - t1
        sys.stdin = saved_stdin

    out = buf.getvalue()
    return {
        "status":      "fail" if vm.failed else "ok",
        "asm_instrs":  _count_asm_instrs(asm),
        "bin_bytes":   len(binary),
        "dyn_instrs":  vm.dyn_instrs,
        "stub_calls":  vm.stub_calls,
        "heap_allocs": vm.heap_allocs,
        "heap_bytes":  vm.heap_bytes,
        "compile_s":   round(compile_s, 4),
        "run_s":       round(run_s, 4),
        "out_sha":     hashlib.sha256(out.encode()).hexdigest()[:12],
        "out_len":     len(out),
    }


# ── parent: drive workers with a timeout, aggregate, report ──────────────────

def drive(file: pathlib.Path, level: int, timeout: float, max_cycles: int) -> dict:
    cmd = [sys.executable, str(pathlib.Path(__file__).resolve()),
           "--worker", str(file), "--level", str(level),
           "--max-cycles", str(max_cycles)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"status": "timeout"}
    if r.returncode != 0:
        tail = (r.stderr or r.stdout).strip().splitlines()
        return {"status": "crash", "detail": tail[-1] if tail else "?"}
    try:
        return json.loads(r.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"status": "crash", "detail": "no-metrics"}


COLS = ["asm_instrs", "bin_bytes", "dyn_instrs", "stub_calls",
        "heap_allocs", "heap_bytes"]


def fmt_row(name: str, m: dict, width: int) -> str:
    if m.get("status") != "ok":
        return f"  {name:<{width}}  {m.get('status','?'):>10}  {m.get('detail','')}"
    cells = "  ".join(f"{m[c]:>10}" for c in COLS)
    tail  = f"  c={m['compile_s']:>6}s r={m['run_s']:>6}s  {m['out_sha']}"
    return f"  {name:<{width}}  {cells}{tail}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", metavar="FILE")
    ap.add_argument("--level", type=int, default=0)
    ap.add_argument("--levels", default="0", help="comma list, e.g. 0,1")
    ap.add_argument("--file", help="single corpus file (name under tests/)")
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--max-cycles", type=int, default=0, help="0 = VM default (50M)")
    ap.add_argument("--save", metavar="JSON", help="write full results to JSON")
    ap.add_argument("--compare", metavar="JSON", help="diff vs a saved run")
    ap.add_argument("--pass-flags", action="store_true", help="list passes/levels")
    args = ap.parse_args()

    # -- worker mode: one run, emit JSON --
    if args.worker:
        try:
            m = run_worker(args.worker, args.level, args.max_cycles)
        except Exception as e:  # noqa: BLE001 — report as clean crash record
            # Exit 0: we DID produce a metrics record (status=crash). The parent
            # JSON-parses it and shows the reason; a non-zero exit is reserved for
            # the worker itself failing to run (import error, bad args).
            m = {"status": "crash", "detail": f"{type(e).__name__}: {e}"}
        print(json.dumps(m))
        return

    if args.pass_flags:
        from opt import PASSES, ASM_PASSES, CODEGEN_FLAGS, LEVELS
        print("registered TAC passes (opt.PASSES):",
              ", ".join(n for n, _ in PASSES) or "(none yet — O0 identity)")
        print("registered post-gen asm passes (opt.ASM_PASSES):",
              ", ".join(n for n, _ in ASM_PASSES) or "(none)")
        print("codegen-strategy flags (opt.CODEGEN_FLAGS):",
              ", ".join(CODEGEN_FLAGS) or "(none)")
        for lvl in sorted(LEVELS):
            print(f"  -O{lvl}: {', '.join(LEVELS[lvl]) or '(none)'}")
        return

    levels = [int(x) for x in args.levels.split(",") if x.strip() != ""]
    if args.file:
        p = (ROOT / args.file)
        files = [p if p.exists() else pathlib.Path(args.file)]
    else:
        files = collect_acceptance()

    width = max((len(rel(f)) for f in files), default=20)
    results: dict[str, dict[int, dict]] = {}

    for lvl in levels:
        print(f"\n── -O{lvl} " + "─" * 60)
        header = "  " + " " * width + "  " + "  ".join(f"{c:>10}" for c in COLS)
        print(header)
        for f in files:
            m = drive(f, lvl, args.timeout, args.max_cycles)
            results.setdefault(rel(f), {})[lvl] = m
            print(fmt_row(rel(f), m, width))

    # -- observable-equivalence check: every level's out_sha == O0's --
    base = min(levels)
    if len(levels) > 1:
        print("\n── observable-equivalence vs -O%d " % base + "─" * 40)
        diverged = 0
        for name, per in results.items():
            b = per.get(base, {})
            if b.get("status") != "ok":
                # Base itself didn't run cleanly — nothing to be equivalent to.
                continue
            for lvl in levels:
                if lvl == base:
                    continue
                m = per.get(lvl, {})
                st = m.get("status")
                if st != "ok":
                    # A pass turned a clean -O{base} run into a crash/timeout/fail:
                    # that is a correctness regression, not just a metric change.
                    print(f"  DIVERGE  {name}  -O{lvl} {st or '?'} "
                          f"(was ok at -O{base})  {m.get('detail','')}")
                    diverged += 1
                elif m["out_sha"] != b["out_sha"]:
                    print(f"  DIVERGE  {name}  -O{lvl} sha {m['out_sha']} "
                          f"!= -O{base} {b['out_sha']}")
                    diverged += 1
        print("  all levels observably equivalent to -O%d" % base
              if diverged == 0 else f"  {diverged} DIVERGENCE(S)")

    # -- totals (per level) --
    print("\n── totals " + "─" * 60)
    for lvl in levels:
        agg = {c: 0 for c in COLS}
        okc = 0
        for per in results.values():
            m = per.get(lvl, {})
            if m.get("status") == "ok":
                okc += 1
                for c in COLS:
                    agg[c] += m[c]
        cells = "  ".join(f"{agg[c]:>10}" for c in COLS)
        print(f"  -O{lvl}  ({okc:>2} ok)  {cells}")

    if args.save:
        pathlib.Path(args.save).write_text(json.dumps(results, indent=1))
        print(f"\nsaved → {args.save}")

    if args.compare:
        old = json.loads(pathlib.Path(args.compare).read_text())
        print(f"\n── vs {args.compare} " + "─" * 50)
        out_changed = regressed = 0
        for name, per in results.items():
            for lvl in levels:
                new  = per.get(lvl, {})
                oldm = old.get(name, {}).get(str(lvl)) or old.get(name, {}).get(lvl)
                if not oldm:
                    continue
                # A file that ran cleanly in the baseline but no longer does is a
                # correctness regression, not a metric delta — surface it.
                if oldm.get("status") == "ok" and new.get("status") != "ok":
                    print(f"  REGRESS  {name} -O{lvl}: was ok, now "
                          f"{new.get('status','?')}  {new.get('detail','')}")
                    regressed += 1
                    continue
                if new.get("status") != "ok" or oldm.get("status") != "ok":
                    continue
                # OUTPUT change is the load-bearing signal: optimization must be
                # observably equivalent, so a different program-output sha is an
                # alarm even when the metric columns look reasonable. (COLS-only
                # deltas below are expected — that is what a pass buys.)
                if new.get("out_sha") != oldm.get("out_sha"):
                    print(f"  OUTPUT   {name} -O{lvl}: sha "
                          f"{oldm.get('out_sha')} → {new.get('out_sha')}  "
                          f"(observable-equivalence BROKEN)")
                    out_changed += 1
                deltas = {c: new[c] - oldm[c] for c in COLS if new[c] != oldm[c]}
                if deltas:
                    ds = " ".join(f"{c}{'+' if v>0 else ''}{v}" for c, v in deltas.items())
                    print(f"  {name} -O{lvl}: {ds}")
        if out_changed or regressed:
            print(f"\n  ⚠ {out_changed} output change(s), {regressed} regression(s) "
                  f"vs {args.compare} — investigate before trusting the metric deltas")
        else:
            print(f"\n  no output changes or regressions vs {args.compare} "
                  f"(metric deltas above are expected)")


if __name__ == "__main__":
    main()
