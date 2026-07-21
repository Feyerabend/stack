"""
rv32c — build the self-hosted RV32 cross-compiler as a NATIVE BINARY.
(SELFHOST F3, the bridge from F3.1's differential to F3.2/F3.3's hardware runs.)

    lark source on stdin  →  RV32I assembly on stdout

The compiler is Lark's, written in Lark: ten module bodies concatenated under one
`module Selfhost` —

    lex → parse → types → tast → infer → tac → lower → opt → regalloc → asm

which is `bootstrap_opt.py`'s optimizing compiler with its terminal stage swapped:
`emitTacC` (TAC → C) becomes `asGen` (TAC → RV32I).  That swap is the whole of F3.
Everything before it is the same code that closed the O5′ fixpoint.

WHY A NATIVE BINARY, when asm_difftest already proves the port byte-identical?
Two reasons, and the second is the one that matters:

  • REACH.  The differential runs the port meta-circularly, on the CEK interpreter
    in Python, and three of the corpus's deepest programs (24_stringprims, 05_expr,
    09_parser) overflow CPython's stack before they finish — they are skipped there.
    Two of those three are among the nine programs with prebuilt firmware.  Compiled
    natively, the same Lark compiler runs them without complaint.  A skip is a
    capacity verdict about the harness, not the port; this is how you cash that in.

  • HONESTY.  Firmware built from a Python compiler tests Python.  For the .uf2 on
    the board to be a claim about the SELF-HOSTED compiler, the assembly it is built
    from has to come out of the self-hosted compiler.

Build path (identical in shape to the O5′ ladder's stage0→stage1):
    emit_tac_c.py rv32compiler.lark -O0  →  self-contained C  →  cc  →  ./rv32c
The Python oracle only ever builds the binary; what the binary EMITS is Lark's.

⚠ CROSS-COMPILATION.  The host binary is native (arm64/x86-64); it emits RV32I text
for the RP2350.  Nothing here runs Lark's compiler on the Pico — a self-compile wants
a multi-GB arena and the chip has 520 KB.

Usage:
    python3 self/tests/rv32c.py --out build/rv32c          # build the binary
    ./build/rv32c < 07/samples/03_primes.lark > primes.S   # use it
    python3 self/tests/rv32c.py --check                    # build + .S == asm.py on the samples
"""

from __future__ import annotations
import argparse, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent           # self/tests
SELF = HERE.parent                                       # self
ROOT = SELF.parent                                       # lark
SRC  = ROOT / "07" / "src"

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SRC))

from bootstrap_opt import (                    # noqa: E402  — the ladder's own helpers
    module_body, compile_selfcontained, run_compiler, EMIT_TAC, _raise_stack,
)

# The O5′ module list with the backend swapped: …opt → regalloc → asm (not emit_tac_c).
MODULES = ["lex", "parse", "types", "tast", "infer", "tac", "lower", "opt",
           "regalloc", "asm"]

# The samples that have prebuilt firmware in 07/firmware/.
SAMPLES = sorted((ROOT / "07" / "samples").glob("*.lark"))


def assemble_compiler(level: int) -> str:
    """The ten module bodies + a stdin main that prints RV32I assembly.

    io is affine — it cannot be used in two match arms — so the main builds the
    output String purely and prints once (the M5.5 idiom).  A rejected program
    prints the same `type error:` line the C compiler prints; the caller sees a
    non-empty stdout that is not assembly, which is what the harness checks.
    """
    bodies = "\n".join(module_body(m) for m in MODULES)
    main = (
        "\nfn main(io : IO) : IO =\n"
        "  match read_all(io) with\n"
        "  | (io2, src) =>\n"
        "      let prog = parseProgram(tokenize(src, string_length(src), P(0, 1, 1))) in\n"
        "      let out = match inferProgram(prog) with\n"
        '                | Err(m) => "type error: " + m\n'
        f"                | Ok(tprog) => asGen(optimizeProg(lowerProgram(tprog), {level}))\n"
        "                end in\n"
        "      print(io2, out)\n"
        "  end\n"
    )
    return "module Selfhost\n\n" + bodies + main


def build(out: pathlib.Path, level: int = 0, heap_bytes: int = 12 * 1024**3,
          keep: pathlib.Path | None = None, quiet: bool = False) -> pathlib.Path:
    """Emit the compiler's own C with the Python oracle, then cc it. Returns `out`."""
    work = keep or pathlib.Path(tempfile.mkdtemp(prefix="lark-rv32c-"))
    work.mkdir(parents=True, exist_ok=True)
    src = work / "rv32compiler.lark"
    src.write_text(assemble_compiler(level))
    n = len(src.read_text().splitlines())
    if not quiet:
        print(f"  assembled {src.name}  ({n} lines, -O{level} baked in)", flush=True)

    c = work / "rv32compiler.c"
    if not quiet:
        print("  stage0: emit_tac_c.py -O0 → C ...", flush=True)
    with c.open("wb") as fout:
        subprocess.run([sys.executable, EMIT_TAC, str(src), "-O0"],
                       stdout=fout, check=True)
    if not quiet:
        print(f"  cc (self-contained, heap={heap_bytes // 1024**3} GiB) → {out} ...", flush=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    compile_selfcontained(c, out, heap_bytes)
    return out


def compile_lark(binary: pathlib.Path, source: pathlib.Path) -> str:
    """Run the self-hosted compiler on one Lark file; return its RV32I assembly."""
    with source.open("rb") as fin:
        r = subprocess.run([str(binary)], stdin=fin, capture_output=True,
                           check=True, preexec_fn=_raise_stack)
    return r.stdout.decode()


def check(binary: pathlib.Path, level: int) -> int:
    """Every sample: the Lark compiler's .S must equal the Python oracle's, byte for byte."""
    import lower as _lower, infer as _infer, parser as _parser, opt as _opt, asm as _asm

    ok = fail = 0
    for path in SAMPLES:
        prog  = _parser.parse_file(str(path))
        tprog = _infer.typecheck(prog, source_file=str(path))
        _opt._SITE = __import__("itertools").count()   # site ids restart per program
        tac   = _opt.optimize(_lower.lower(tprog), _opt.OptOptions(level=level))
        want  = _asm.gen(tac)
        got   = compile_lark(binary, path).rstrip("\n")
        if got == want.rstrip("\n"):
            print(f"  ok    {path.name}  ({len(want.splitlines())} lines of RV32I)")
            ok += 1
        else:
            print(f"  FAIL  {path.name}  (assembly differs from asm.py)")
            fail += 1
    print(f"\n  {ok} ok, {fail} failed  "
          f"(native self-hosted compiler vs the Python oracle, -O{level})")
    return 1 if fail else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="build the self-hosted RV32 cross-compiler")
    ap.add_argument("--out", default=str(ROOT / "build" / "rv32c"))
    ap.add_argument("--level", type=int, default=0,
                    help="optimization level baked into the compiler (default 0 — the "
                         "level the prebuilt firmware was built at)")
    ap.add_argument("--heap-gb", type=int, default=12)
    ap.add_argument("--keep", metavar="DIR", help="keep the assembled source + C here")
    ap.add_argument("--check", action="store_true",
                    help="after building, assert .S == asm.py on every sample")
    args = ap.parse_args()

    out = pathlib.Path(args.out).resolve()
    keep = pathlib.Path(args.keep).resolve() if args.keep else None
    build(out, args.level, args.heap_gb * 1024**3, keep)
    print(f"\n  rv32c: {out}\n")
    if args.check:
        return check(out, args.level)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
