"""
F2 bootstrap fixpoint — the two-stage self-hosting proof for lark-in-lark.

This packages the F2 milestone (true self-hosting) as one repeatable command.
It assembles the self-hosted compiler and drives the classic bootstrap ladder:

    stage0  = the Python oracle (07/src/emit_c_ast.py) compiles compiler.lark
              to C, which links against cek.c/larkrun.c into the stage1 binary.
    stage1 < compiler.lark  ->  C1  ->  (link)  ->  stage2 binary
    stage2 < compiler.lark  ->  C2  ->  (link)  ->  stage3 binary
    stage3 < compiler.lark  ->  C3

The fixpoint is  C1 == C2 == C3  (byte-identical emitted C).  Once the compiler
compiles its own source to the same C that a compiler built from that C emits,
the ladder has reached its fixed point: the self-hosted compiler reproduces
itself.  Because the emitter is deterministic and reads only the *syntactic*
AST, this C-source fixpoint is build-environment independent — the strong,
portable proof.  Native binary equality is Mach-O-nondeterministic on macOS
(LC_UUID, embedded paths) and is deliberately NOT asserted here; see LOG.md.

The self-hosted compiler = lex.lark + parse.lark + emit_c.lark bodies under one
`module Selfhost`, plus a `read_all`/stdin `main` that compiles whatever source
it is fed.  We assemble it from those three modules (same body-stripping the
emit_c differential uses), so the bootstrap tracks the modules automatically.
infer.lark is NOT on this path — the emitter drives off the syntactic AST.

Cost: the emitter's final string join is O(n^2) in the no-GC bump arena, so
compiling the ~1850-line compiler needs a multi-GB arena and runs for a few
minutes with a ~3 GB peak.  That is a performance characteristic (OPTIMIZE.md),
not a correctness one; the arena size is overridable below.

Usage:
    python3 self/tests/bootstrap.py            # full ladder: C1==C2==C3
    python3 self/tests/bootstrap.py --stages 2 # minimal proof: C1==C2
    python3 self/tests/bootstrap.py --keep DIR # write artifacts to DIR (kept)
"""

from __future__ import annotations
import argparse, hashlib, os, pathlib, shutil, subprocess, sys, tempfile

HERE  = pathlib.Path(__file__).resolve().parent          # self/tests
SELF  = HERE.parent                                      # self
ROOT  = SELF.parent                                      # lark
SRC   = ROOT / "07" / "src"
EMIT  = str(SRC / "emit_c_ast.py")
CEK_C = str(SRC / "cek.c")
RUN_C = str(SRC / "larkrun.c")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
EMITL = SELF / "emit_c.lark"

# The self-hosted compiler concatenates three ~600-line modules and its emitter
# recurses deeply, so the C interpreter's fixed limits must be raised well past
# their corpus defaults.  The 8 GiB arena covers the O(n^2) join (see module
# docstring); override with LARK_ARENA_SIZE if you have less RAM and a smaller
# input.  These are compile-time -D overrides read by cek.c's #ifndef guards.
CC_LIMITS = [
    "-DLARK_ARENA_SIZE=" + os.environ.get("LARK_ARENA_SIZE", str(8 * 1024**3)),
    "-DLARK_KONT_MAX=1048576",
    "-DLARK_TOP_MAX=8192",
    "-DLARK_CON_MAX=4096",
    "-DLARK_DISPATCH_MAX=2048",
]

MAIN_MARKER = "\nfn main(io : IO) : IO ="

# The bootstrap main: read the whole source from stdin and compile it.  `base`
# is fixed so every stage emits the same header comment — otherwise the emitted
# C would differ only in that one filename token and the C-fixpoint would be
# spuriously broken.  This is what distinguishes compiler.lark from the emit_c
# differential's driver (which embeds a fixed source instead of reading stdin).
BOOTSTRAP_MAIN = (
    "\nfn main(io : IO) : IO =\n"
    "  match read_all(io) with\n"
    "  | (io2, src) =>\n"
    '      let base = "compiler" in\n'
    "      print(io2, emitProgram(base, parseProgram("
    "tokenize(src, string_length(src), P(0, 1, 1)))))\n"
    "  end\n"
)


def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)


def assemble_compiler() -> str:
    """lex + parse + emit_c bodies under one module, plus the stdin main."""
    lex_body   = _strip_lines(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse_body = _strip_lines(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    emit_body  = _strip_lines(EMITL.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    return ("module Selfhost\n\n"
            + lex_body + "\n" + parse_body + "\n" + emit_body + BOOTSTRAP_MAIN)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_c(c_path: pathlib.Path, bin_path: pathlib.Path) -> None:
    """Link a generated prog.c against the C CEK runtime into a binary."""
    subprocess.run(
        ["cc", *CC_LIMITS, "-I", str(SRC), CEK_C, RUN_C, str(c_path),
         "-o", str(bin_path), "-lm"],
        check=True,
    )


def run_compiler(binary: pathlib.Path, source: pathlib.Path,
                 out_c: pathlib.Path) -> None:
    """Feed `source` to a self-hosted compiler binary; capture emitted C."""
    with source.open("rb") as fin, out_c.open("wb") as fout:
        subprocess.run([str(binary)], stdin=fin, stdout=fout, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="F2 bootstrap fixpoint")
    ap.add_argument("--stages", type=int, default=3, choices=(2, 3),
                    help="ladder height: 2 asserts C1==C2, 3 asserts C1==C2==C3")
    ap.add_argument("--keep", metavar="DIR",
                    help="write artifacts to DIR and keep them (default: temp dir)")
    args = ap.parse_args()

    work = pathlib.Path(args.keep) if args.keep else pathlib.Path(tempfile.mkdtemp(prefix="lark-boot-"))
    work.mkdir(parents=True, exist_ok=True)

    compiler = work / "compiler.lark"
    compiler.write_text(assemble_compiler())
    print(f"assembled {compiler}  ({len(compiler.read_text().splitlines())} lines)")

    # stage0: Python oracle emits C for the compiler, link -> stage1 binary.
    c0 = work / "c0.c"
    print("stage0: emit_c_ast.py compiler.lark -> c0.c ...", flush=True)
    subprocess.run([sys.executable, EMIT, str(compiler), str(c0)], check=True)
    print("        link stage1 ...", flush=True)
    compile_c(c0, work / "stage1")

    outs: list[pathlib.Path] = []
    for i in range(1, args.stages + 1):
        stage_bin = work / f"stage{i}"
        c_out = work / f"c{i}.c"
        print(f"stage{i} < compiler.lark -> c{i}.c ...", flush=True)
        run_compiler(stage_bin, compiler, c_out)
        outs.append(c_out)
        if i < args.stages:                       # build the next rung
            print(f"        link stage{i+1} ...", flush=True)
            compile_c(c_out, work / f"stage{i+1}")

    hashes = [sha(p) for p in outs]
    print("\n  emitted-C hashes:")
    for p, h in zip(outs, hashes):
        print(f"    {p.name}  {h}")

    ok = len(set(hashes)) == 1
    label = "==".join(p.stem.upper() for p in outs)
    if ok:
        print(f"\nFIXPOINT REACHED — {label} byte-identical ({hashes[0][:12]})")
    else:
        print(f"\nFIXPOINT BROKEN — {label} differ")

    if not args.keep:
        shutil.rmtree(work, ignore_errors=True)
    else:
        print(f"\nartifacts kept in {work}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
