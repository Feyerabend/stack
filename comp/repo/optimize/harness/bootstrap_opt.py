"""
The self-optimizing fixpoint — the OPTIMIZING compiler reproduces itself
(the capstone).

`bootstrap.py` closes the fixpoint for the emit-only compiler (lex+parse+emit_c,
AST→C); `bootstrap_tc.py` for the type-checking one (adds infer as a gate, still
AST→C).  This harness closes the fixpoint for the *optimizing* compiler: the full
middle end runs in Lark — parse → inferProgram → lowerProgram → optimizeProg(LEVEL)
→ emitTacC — so optimization lives INSIDE the self-hosted compiler and on the
(C) backend.  This is the first ladder whose emitted C is the *optimized* C.

    stage0 = the Python oracle (emit_tac_c.py, -O0) compiles optcompiler.lark -> C0,
             which is SELF-CONTAINED C (its own main + bump heap) and compiles
             straight into the stage1 binary.  (stage0 only needs to produce a
             CORRECT stage1; at -O0 C0 is not itself optimized — the optimization
             first appears at stage1's OUTPUT.)  The AST→C emitter (emit_c_ast.py)
             would also produce a correct stage1, but its C runs on the CEK
             interpreter and allocates into a CEK arena: on the full ~7,600-line
             self-compile that overflows a 15 GB arena, i.e. more memory than the
             machine has.  The self-contained path peaks near 6 GB, and is the one
             that produced the pinned fixpoint sha.
    stage1 < INPUT  ->  C1  ->  (link)  ->  stage2
    stage2 < INPUT  ->  C2  ->  (link)  ->  stage3
    stage3 < INPUT  ->  C3

With INPUT = optcompiler.lark (the default), C1==C2==C3 is the self-application
fixpoint on the optimized compiler.  --input FILE feeds a different program (used
to validate the ladder mechanism / gauge the arena on smaller inputs before the
full ~7300-line self-compile, which is the heaviest meta-circular load in the
tree — expect the arena wall).

The assembled compiler = the 9 module bodies under one `module Selfhost`, plus a
read_all/stdin `main` that runs the whole optimizing pipeline at LEVEL and prints
the emitted C.  io is affine, so the main builds the output String purely and
prints once (an affine wart).

Usage:
    python3 harness/bootstrap_opt.py                       # full self-compile ladder
    python3 harness/bootstrap_opt.py --input ../tests/01_hello.lark --stages 2
    python3 harness/bootstrap_opt.py --level 0             # unoptimized self-compile
    python3 harness/bootstrap_opt.py --arena-mb 15000 --keep DIR
"""

from __future__ import annotations
import argparse, hashlib, os, pathlib, resource, shutil, subprocess, sys, tempfile, time

HERE  = pathlib.Path(__file__).resolve().parent   # <strand>/harness
ROOT  = HERE.parent                              # <strand>/
SELF  = ROOT / "lark"                            # the compiler, written in Lark
SRC   = ROOT / "oracle"                          # the Python reference implementation
EMIT  = str(SRC / "emit_c_ast.py")
EMIT_TAC = str(SRC / "emit_tac_c.py")
CEK_C = str(SRC / "cek.c")
RUN_C = str(SRC / "larkrun.c")

# The compiler recurses deeply over its own 7,600-line source, and macOS gives a
# process 8 MB of stack.  Every stage runs with the stack raised to the ~64 MB
# hard cap, which is what `ulimit -s 65520` does in a shell.
STACK_BYTES = 65520 * 1024

def _raise_stack() -> None:
    """Best-effort: give the child the largest stack the OS will actually grant.

    The compiler recurses deeply over its own 7,600-line source and macOS starts a
    process with 8 MB.  Raising it is worth doing — but macOS also rejects the very
    hard limit it reports (setrlimit against `hard` raises "current limit exceeds
    maximum limit"), so walk down until one sticks, and never let this kill the run:
    a stage that would have fit in 8 MB must not fail because we tried to give it 64.
    """
    soft, hard = resource.getrlimit(resource.RLIMIT_STACK)
    for want in (STACK_BYTES, 32 * 1024 * 1024, 16 * 1024 * 1024):
        if want <= soft:
            return
        try:
            resource.setrlimit(resource.RLIMIT_STACK, (want, hard))
            return
        except (ValueError, OSError):
            continue

MODULES = ["lex", "parse", "types", "tast", "infer", "tac", "lower", "opt", "emit_tac_c"]
MAIN_MARKER = "\nfn main(io : IO) : IO ="


def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)


def module_body(name: str) -> str:
    src = (SELF / f"{name}.lark").read_text().split(MAIN_MARKER, 1)[0]
    drop = ("module ",) if name == "lex" else ("module ", "import ")
    return _strip_lines(src, drop)


def assemble_compiler(level: int) -> str:
    bodies = "\n".join(module_body(m) for m in MODULES)
    # read the whole source from stdin, run the optimizing pipeline, print once.
    main = (
        "\nfn main(io : IO) : IO =\n"
        "  match read_all(io) with\n"
        "  | (io2, src) =>\n"
        "      let prog = parseProgram(tokenize(src, string_length(src), P(0, 1, 1))) in\n"
        "      let out = match inferProgram(prog) with\n"
        '                | Err(m) => "type error: " + m\n'
        f"                | Ok(tprog) => emitTacC(optimizeProg(lowerProgram(tprog), {level}))\n"
        "                end in\n"
        "      print(io2, out)\n"
        "  end\n"
    )
    return "module Selfhost\n\n" + bodies + main


def cc_limits(arena_bytes: int) -> list[str]:
    return [
        "-DLARK_ARENA_SIZE=" + str(arena_bytes),
        "-DLARK_KONT_MAX=4194304",
        "-DLARK_TOP_MAX=16384",
        "-DLARK_CON_MAX=8192",
        "-DLARK_DISPATCH_MAX=4096",
    ]


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_stage1(c_path: pathlib.Path, bin_path: pathlib.Path, arena: int) -> None:
    """stage1 is built from C0, the emit_c_ast (AST→C) output: it runs on the
    CEK runtime, so it links cek.c + larkrun.c and sizes the CEK arena."""
    subprocess.run(
        ["cc", *cc_limits(arena), "-I", str(SRC), CEK_C, RUN_C, str(c_path),
         "-o", str(bin_path), "-lm"],
        check=True,
    )


def compile_selfcontained(c_path: pathlib.Path, bin_path: pathlib.Path, arena: int) -> None:
    """stage2+ are built from emit_tac_c (TAC→C) output, which is SELF-CONTAINED
    (its own main + bump heap, no cek.c/larkrun.c) — compile as documented in the
    emit_tac_c preamble, sizing LARK_HEAP_BYTES to the same budget as the arena."""
    subprocess.run(
        ["cc", "-O2", "-fwrapv", "-DLARK_HEAP_BYTES=" + str(arena),
         str(c_path), "-o", str(bin_path), "-lm"],
        check=True,
    )


def run_compiler(binary: pathlib.Path, source: pathlib.Path, out_c: pathlib.Path) -> float:
    t0 = time.time()
    with source.open("rb") as fin, out_c.open("wb") as fout:
        subprocess.run([str(binary)], stdin=fin, stdout=fout, check=True,
                       preexec_fn=_raise_stack)
    return time.time() - t0


def main() -> int:
    ap = argparse.ArgumentParser(description="optimizing-compiler fixpoint")
    ap.add_argument("--stages", type=int, default=3, choices=(1, 2, 3))
    ap.add_argument("--level", type=int, default=3, help="optimization level baked into the compiler (default 3)")
    ap.add_argument("--input", default=None, help="program to compile (default: the compiler itself)")
    ap.add_argument("--arena-mb", type=int, default=15000,
                    help="arena size MiB, lazily committed (default 15000)")
    ap.add_argument("--keep", metavar="DIR")
    args = ap.parse_args()
    arena = args.arena_mb * 1024 * 1024

    work = pathlib.Path(args.keep) if args.keep else pathlib.Path(tempfile.mkdtemp(prefix="lark-boot-opt-"))
    work.mkdir(parents=True, exist_ok=True)

    compiler = work / "optcompiler.lark"
    compiler.write_text(assemble_compiler(args.level))
    nlines = len(compiler.read_text().splitlines())
    inp = pathlib.Path(args.input).resolve() if args.input else compiler
    print(f"assembled {compiler}  ({nlines} lines)  -O{args.level}  arena={args.arena_mb} MiB")
    print(f"input = {inp}")

    # stage0 goes through emit_tac_c.py at -O0, NOT emit_c_ast.py.  Both emit correct
    # C, but they emit it for different runtimes: emit_c_ast's C runs on the CEK
    # interpreter (cek.c + larkrun.c) and allocates into a CEK arena, and compiling
    # the 7,600-line compiler with it overflows a 15 GB arena — more memory than most
    # machines have.  emit_tac_c's C is self-contained (its own main, a plain bump
    # heap) and peaks around 6 GB on the same input.  This is also the path that
    # produced the pinned fixpoint sha; the CEK path never closed the ladder.
    c0 = work / "c0.c"
    print("stage0: emit_tac_c.py optcompiler.lark -O0 -> c0.c ...", flush=True)
    with c0.open("wb") as fout:
        subprocess.run([sys.executable, EMIT_TAC, str(compiler), "-O0"],
                       stdout=fout, check=True)
    print("        compile stage1 (self-contained) ...", flush=True)
    compile_selfcontained(c0, work / "stage1", arena)

    outs: list[pathlib.Path] = []
    for i in range(1, args.stages + 1):
        stage_bin = work / f"stage{i}"
        c_out = work / f"c{i}.c"
        print(f"stage{i} < {inp.name} -> c{i}.c ...", flush=True)
        dt = run_compiler(stage_bin, inp, c_out)
        nl = len(c_out.read_text().splitlines())
        print(f"        {nl} C lines, {c_out.stat().st_size} bytes, {dt:.1f}s", flush=True)
        outs.append(c_out)
        if i < args.stages:
            # stageN's output (n>=1) is self-contained emit_tac_c C.
            print(f"        link stage{i+1} ...", flush=True)
            compile_selfcontained(c_out, work / f"stage{i+1}", arena)

    hashes = [sha(p) for p in outs]
    print("\n  emitted-C hashes:")
    for p, h in zip(outs, hashes):
        print(f"    {p.name}  {h}")

    ok = len(set(hashes)) == 1
    label = "==".join(p.stem.upper() for p in outs)
    if args.stages == 1:
        print(f"\n  stage1 emitted C1 ({hashes[0][:12]}) — ladder mechanism OK (single stage)")
    elif ok:
        print(f"\nFIXPOINT REACHED — {label} byte-identical ({hashes[0][:12]})")
    else:
        print(f"\nFIXPOINT BROKEN — {label} differ")

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"\nartifacts kept in {work}")
    return 0 if (ok or args.stages == 1) else 1


if __name__ == "__main__":
    raise SystemExit(main())
