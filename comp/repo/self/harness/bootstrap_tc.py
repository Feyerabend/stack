"""
Native fixpoint — the *typechecking* self-hosted compiler reproduces itself.

`bootstrap.py` closes the fixpoint for the emit-only compiler (`lex + parse +
emit_c`); the emitter drives off the syntactic AST, so `infer.lark` is never on
that path.  This harness closes the stronger fixpoint: the compiler
*type-checks first* (all six modules `lex + parse + types + tast + infer +
emit_c`, plus a `tcGate` that runs `infer.lark`'s `checkProgram` passes), then
emits C for well-typed input or prints `type error: <msg>` for ill-typed input.
It is the native analog of `typecheck_difftest.py`'s gated driver, reading its
source from stdin (like `bootstrap.py`) instead of embedding one corpus file.

    stage0  = the Python oracle (oracle/emit_c_ast.py) compiles tc_compiler.lark
              -> C, linked against cek.c/larkrun.c into the stage1 binary.
    stage1 < tc_compiler.lark  ->  C1  ->  (link)  ->  stage2
    stage2 < tc_compiler.lark  ->  C2  ->  (link)  ->  stage3
    stage3 < tc_compiler.lark  ->  C3

Fixpoint: C1 == C2 == C3.  The compiler type-checks *its own source* (the gate
accepts) and emits the same C a compiler built from that C emits.

This was the optimization work's first target, and it hit TWO no-GC-arena walls:
(a) the emitter's O(n^2) line join — fixed with a balanced join (`lark/emit_c.lark`
`ecJoinNL`/`ecJoinPairs`); and (b) the infer pass's assoc-list `Subst` applied
O(n) times and never freed, which overflowed >12 GB.  The second fix — `types.lark`
`applyScheme` short-circuiting on a *closed* scheme (applying a subst to a
fully-generalised scheme is the identity) — cut the infer self-compile to a
10.15 GB completing peak, closing this fixpoint: C1==C2==C3 byte-identical, sha
34a07692, 18549 lines.  Both fixes are output-neutral (`infertest`/`typechecktest`
42/0/2 byte-identical).  The arena is lazily committed, so --arena-mb only reserves
address space; the default (14 GiB) leaves headroom above the ~10.15 GB peak.

Usage:
    python3 harness/bootstrap_tc.py                  # full ladder: C1==C2==C3
    python3 harness/bootstrap_tc.py --stages 2       # minimal: C1==C2
    python3 harness/bootstrap_tc.py --arena-mb 14336 # arena size (MiB)
    python3 harness/bootstrap_tc.py --keep DIR       # keep artifacts
"""

from __future__ import annotations
import argparse, hashlib, os, pathlib, shutil, subprocess, sys, tempfile

HERE  = pathlib.Path(__file__).resolve().parent   # <strand>/harness
ROOT  = HERE.parent                              # <strand>/
SELF  = ROOT / "lark"                            # the compiler, written in Lark
SRC   = ROOT / "oracle"                          # the Python reference implementation
EMIT  = str(SRC / "emit_c_ast.py")
CEK_C = str(SRC / "cek.c")
RUN_C = str(SRC / "larkrun.c")

sys.path.insert(0, str(HERE))
import typecheck_difftest as T   # reuse the exact gated-driver assembly (6 modules + GATE_FN)

MAIN_MARKER = "\nfn main(io : IO) : IO ="

# read the whole source from stdin, type-check via tcGate, then emit-or-reject.
# `base` is fixed so every stage emits the same header comment (otherwise the C
# would differ only in a filename token).  `prog` is used twice (gate + emit) —
# parse.lark's Prog is Copy, so that is fine (same tree gated and emitted).  io
# is printed exactly once (affine idiom: build `out` purely, print once).
STDIN_MAIN = (
    "\nfn main(io : IO) : IO =\n"
    "  match read_all(io) with\n"
    "  | (io2, src) =>\n"
    '      let base = "compiler" in\n'
    "      let prog = parseProgram(tokenize(src, string_length(src), P(0, 1, 1))) in\n"
    "      let out = match tcGate(prog) with\n"
    '                | Err(m) => "type error: " + m\n'
    "                | Ok(_) => emitProgram(base, prog)\n"
    "                end in\n"
    "      print(io2, out)\n"
    "  end\n"
)


def assemble_tc_compiler() -> str:
    """Six modules + tcGate + the stdin read_all main, under one module."""
    bodies = [
        T._strip(T.LEX,   ("module ",)),
        T._strip(T.PARSE, ("module ", "import ")),
        T._strip(T.TYPES, ("module ", "import ")),
        T._strip(T.TAST,  ("module ", "import ")),
        T._strip(T.INFER, ("module ", "import ")),
        T._strip(T.EMITL, ("module ", "import ")),
    ]
    return "module Selfhost\n\n" + "\n".join(bodies) + T.GATE_FN + STDIN_MAIN


def cc_limits(arena_bytes: int) -> list[str]:
    return [
        "-DLARK_ARENA_SIZE=" + str(arena_bytes),
        "-DLARK_KONT_MAX=1048576",
        "-DLARK_TOP_MAX=8192",
        "-DLARK_CON_MAX=4096",
        "-DLARK_DISPATCH_MAX=2048",
    ]


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_c(c_path: pathlib.Path, bin_path: pathlib.Path, arena: int) -> None:
    subprocess.run(
        ["cc", *cc_limits(arena), "-I", str(SRC), CEK_C, RUN_C, str(c_path),
         "-o", str(bin_path), "-lm"],
        check=True,
    )


def run_compiler(binary: pathlib.Path, source: pathlib.Path,
                 out_c: pathlib.Path) -> None:
    with source.open("rb") as fin, out_c.open("wb") as fout:
        subprocess.run([str(binary)], stdin=fin, stdout=fout, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="typechecking native fixpoint")
    ap.add_argument("--stages", type=int, default=3, choices=(2, 3))
    ap.add_argument("--arena-mb", type=int, default=14336,
                    help="arena size in MiB (lazily committed; default 14336 — "
                         "the infer pass peaks ~10.15 GB on the tc source, so this "
                         "leaves headroom; only touched pages cost physical memory)")
    ap.add_argument("--keep", metavar="DIR")
    args = ap.parse_args()
    arena = args.arena_mb * 1024 * 1024

    work = pathlib.Path(args.keep) if args.keep else pathlib.Path(tempfile.mkdtemp(prefix="lark-boot-tc-"))
    work.mkdir(parents=True, exist_ok=True)

    compiler = work / "tc_compiler.lark"
    compiler.write_text(assemble_tc_compiler())
    print(f"assembled {compiler}  ({len(compiler.read_text().splitlines())} lines)  arena={args.arena_mb} MiB")

    c0 = work / "c0.c"
    print("stage0: emit_c_ast.py tc_compiler.lark -> c0.c  (oracle also type-checks it) ...", flush=True)
    subprocess.run([sys.executable, EMIT, str(compiler), str(c0)], check=True)
    print("        link stage1 ...", flush=True)
    compile_c(c0, work / "stage1", arena)

    outs: list[pathlib.Path] = []
    for i in range(1, args.stages + 1):
        stage_bin = work / f"stage{i}"
        c_out = work / f"c{i}.c"
        print(f"stage{i} < tc_compiler.lark -> c{i}.c ...", flush=True)
        run_compiler(stage_bin, compiler, c_out)
        outs.append(c_out)
        if i < args.stages:
            print(f"        link stage{i+1} ...", flush=True)
            compile_c(c_out, work / f"stage{i+1}", arena)

    hashes = [sha(p) for p in outs]
    print("\n  emitted-C hashes:")
    for p, h in zip(outs, hashes):
        print(f"    {p.name}  {h}  ({len(p.read_text().splitlines())} lines)")

    ok = len(set(hashes)) == 1
    label = "==".join(p.stem.upper() for p in outs)
    if ok:
        print(f"\nF2+ NATIVE FIXPOINT REACHED — {label} byte-identical ({hashes[0][:12]})")
    else:
        print(f"\nFIXPOINT BROKEN — {label} differ")

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"\nartifacts kept in {work}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
