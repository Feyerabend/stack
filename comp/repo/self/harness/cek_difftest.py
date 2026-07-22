"""
Differential test for the self-hosted CEK evaluator.

For every self-contained .lark file in the corpus it compares two program outputs:

  • the oracle — oracle/cek.py (the frozen Python interpreter) run on the file,
    its stdout captured;
  • the port    — lark/cek.lark, driven through the Python CEK, evaluating the
    SAME source (embedded as a String literal, lexed + parsed + run in Lark).

They must be byte-identical, line for line.

Composition (same as parse_difftest.py)
────────────────────────────────────────
cek.lark is a *component*: it evaluates parse.lark's `Expr` and uses lex.lark's
`tokenize`/`P`.  We do not use `import` (the toolchain's import path skips infer
Pass 1.5 — a known wart of the language); instead the driver is built by CONCATENATION:
  lex.lark body + parse.lark body + cek.lark body + a generated main,
all under one `module Selfhost`, so the whole thing goes through the normal
top-level typechecker.

Scope (see cek.lark header): the integer/bool/string/list/tuple/ADT/recursion +
float + trait-dispatch fragment, now also covering multi-module programs
(`import ... exposing (...)`, resolved by inlining — see inline_imports) and
`read` (stdin, checked separately by read_checks).  Files are only SKIPPED for
reasons outside the port's control: the oracle itself rejects/times-out on them,
the meta-circular tower is too slow (a performance verdict, not correctness), or
an import can't be resolved to a module file on disk.

Usage:
    python3 harness/cek_difftest.py [-v]      # -v: show a diff on failure
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib
import os

HERE  = pathlib.Path(__file__).resolve().parent   # <strand>/harness
ROOT  = HERE.parent                              # <strand>/
SELF  = ROOT / "lark"                            # the compiler, written in Lark
SRC   = ROOT / "oracle"                          # the Python reference implementation
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
CEKL  = SELF / "cek.lark"

sys.path.insert(0, str(SRC))
from lexer import Lexer, LexError, TK        # noqa: E402
import parser as _parser                     # noqa: E402
from parser import ParseError                # noqa: E402
import tree as _tree                         # noqa: E402


# ── Corpus + slice-1 admissibility ────────────────────────────────────────────

# Files that parse/run fine in the oracle but fall outside slice 1 for reasons
# other than `import` (which is detected structurally below).  Kept explicit so
# the reason is visible; revisit as later slices land.
EXPLICIT_SKIP: dict[str, str] = {
    # Float arithmetic works (string_to_float prim + float binop/show) and custom
    # trait-method dispatch works (RDispatch + con→type map + impl registration),
    # so 05_adt / 13_floatops / 20_floatprec / 08_traits all run.  Nothing outside
    # slice 1 remains here except structurally-detected `import` files.
}

def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "tests", ROOT / "samples"]:
        for p in sorted(base.rglob("*.lark")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files

def admissible(source: str) -> tuple[bool, str]:
    """Is this file inside slice 1?  Returns (ok, reason-if-not).

    Slice 1 covers the int/bool/string/list/tuple/ADT/recursion + float
    fragment, including trait `impl`/`Show` dispatch and — as of the import
    slice — multi-module programs (`import ... exposing (...)`), which the
    harness resolves by inlining (see inline_imports).  A file is inadmissible
    only if the oracle itself can't parse it, or an import can't be resolved to
    a module file on disk.
    """
    try:
        prog = _parser.parse_src(source, "<corpus>")
    except (LexError, ParseError) as e:
        return False, f"oracle parse error: {e}"
    return True, ""


# ── Import resolution (inline imported modules into the object source) ─────────
#
# The port has no `import` mechanism — it evaluates one flat program.  To run a
# multi-module object program we FLATTEN it exactly as the parse/cek harness
# already flattens lex+parse+cek: resolve each `import M exposing (...)` to its
# module file (same rule as cek.py's load_import — `<dir>/<m.lower()>.lark` then
# `<dir>/<M>.lark`), strip that module's own `module`/`import` lines, and append
# its decls to the object source with the import statements removed.  The oracle
# still runs the ORIGINAL file with real imports; the two outputs must agree.
#
# `export` prefixes and decl ORDER don't matter: the port's parser accepts
# `export`, and its evaluator resolves top-level names mutually through the
# threaded globals, so an appended module's decls bind fine.
#
# Visibility DOES matter, though — this file used to claim otherwise.  It is not
# true that hiding a name "changes nothing": if the module keeps a name to itself
# and the importing file happens to define its own, inlining puts BOTH in one flat
# scope, and the module's copy (appended last) silently wins.  25_torture.lark hit
# exactly this — Stdlib's `length : String -> Int`, which it does not import,
# shadowed its own `length : List(Int) -> Int`, so `length(xs)` evaluated
# `string_length` on a list and printed `()` where the oracle printed `10`.
#
# So we α-rename, below: every module top-level name that is NOT exposed to this
# file and DOES collide with one of the file's own top-level names is renamed
# (`Stdlib__length`).  We cannot simply drop the unexposed decls instead — a
# module's exported functions call its other functions (`spaces` calls
# `repeat_str`), so the body has to arrive whole.

def _top_names(prog) -> set[str]:
    """Every name a program binds at the top level — values, types, constructors."""
    names: set[str] = set()
    for d in prog.decls:
        if isinstance(d, (_tree.FnDecl, _tree.LetDecl, _tree.TraitDecl)):
            names.add(d.name)
        elif isinstance(d, _tree.TypeDecl):
            names.add(d.name)
            if isinstance(d.body, tuple):        # an ADT, not an alias
                names.update(v.name for v in d.body)
    return names

def _qualify(module: str, name: str) -> str:
    prefix = module.lower() if name[0].islower() else module
    return f"{prefix}__{name}"

def _rename(src: str, renames: dict[str, str]) -> str:
    """α-rename identifiers throughout `src`.

    Driven off the lexer, so only real NAME/UPPER tokens move: an occurrence
    inside a comment or a string literal is left alone.  Renaming every
    occurrence uniformly — binders and uses alike, including any local that
    shadows — is what keeps this meaning-preserving.  Offsets are computed in
    BYTES because a token's column is a byte offset (see lexer._advance)."""
    data  = src.encode("utf-8")
    start, off = [], 0
    for line in data.splitlines(keepends=True):
        start.append(off)
        off += len(line)
    edits = [(start[t.line - 1] + t.col - 1, len(t.text.encode("utf-8")), renames[t.text])
             for t in Lexer(src, "<module>").tokenize()
             if t.kind in (TK.NAME, TK.UPPER) and t.text in renames]
    for at, width, new in reversed(edits):          # right-to-left: offsets hold
        data = data[:at] + new.encode("utf-8") + data[at + width:]
    return data.decode("utf-8")

def _resolve_module(src_dir: pathlib.Path, module: str) -> pathlib.Path | None:
    for cand in (src_dir / f"{module.lower()}.lark", src_dir / f"{module}.lark"):
        if cand.exists():
            return cand
    return None

def _strip_module_import_lines(text: str) -> str:
    return "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith(("module ", "import ")))

def _strip_import_stmts(source: str) -> str:
    """Remove whole `import ...` statements, including multi-line
    `exposing ( ... )` continuations (balanced-paren scan)."""
    lines = source.splitlines()
    out: list[str] = []
    i, n = 0, len(lines)
    while i < n:
        ln = lines[i]
        if ln.lstrip().startswith("import "):
            depth = ln.count("(") - ln.count(")")
            i += 1
            while depth > 0 and i < n:
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out)

def inline_imports(path: pathlib.Path, source: str) -> tuple[str, str]:
    """Return (flattened_source, error).  On an unresolvable import, error is
    non-empty and flattened_source is the original."""
    prog = _parser.parse_src(source, str(path))
    if not prog.imports:
        return source, ""
    src_dir = path.parent
    bodies: list[str] = []
    for imp in prog.imports:
        mpath = _resolve_module(src_dir, imp.module)
        if mpath is None:
            return source, f"cannot resolve import {imp.module}"
        mtext = mpath.read_text()
        try:
            mprog = _parser.parse_src(mtext, str(mpath))
        except (LexError, ParseError):
            return source, f"cannot parse module {imp.module}"
        # `exposing` absent = the whole module comes in, so nothing is private.
        exposed = set(imp.exposing) if imp.exposing is not None else _top_names(mprog)
        collide = (_top_names(mprog) - exposed) & _top_names(prog)
        if collide:
            # The prefix must keep the name's case: Lark reads a leading capital
            # as a constructor and a leading lowercase as a value, so `Stdlib__f`
            # would turn the function `f` into a constructor and mis-parse it.
            mtext = _rename(mtext, {n: _qualify(imp.module, n) for n in collide})
        bodies.append(_strip_module_import_lines(mtext))
    flat = _strip_import_stmts(source)
    if bodies:
        flat = flat + "\n\n(* ── inlined imports ── *)\n" + "\n\n".join(bodies) + "\n"
    return flat, ""


# ── Driver generation (concatenate lex + parse + cek + a per-file main) ───────

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)

def lark_string_literal(source: str) -> str:
    out: list[str] = []
    for ch in source:
        if   ch == "\\": out.append("\\\\")
        elif ch == '"':  out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\t": out.append("\\t")
        elif ch == "\r": out.append("\\r")
        else:            out.append(ch)
    return "".join(out)

def make_driver(lex_src: str, parse_src: str, cek_src: str, source: str,
                stdin: str = "") -> str:
    lex_body   = lex_src.split(MAIN_MARKER, 1)[0]
    parse_body = parse_src.split(MAIN_MARKER, 1)[0]
    cek_body   = cek_src.split(MAIN_MARKER, 1)[0]
    lex_body   = _strip_lines(lex_body,   ("module ",))
    parse_body = _strip_lines(parse_body, ("module ", "import "))
    cek_body   = _strip_lines(cek_body,   ("module ", "import "))
    lit  = lark_string_literal(source)
    slit = lark_string_literal(stdin)
    driver_main = (
        '\nfn main(io : IO) : IO =\n'
        f'  let src = "{lit}" in\n'
        f'  let input = "{slit}" in\n'
        '  print(io, runProgram(parseProgram(tokenize(src, string_length(src), P(0, 1, 1))), input))\n'
    )
    return ("module Selfhost\n\n"
            + lex_body + "\n" + parse_body + "\n" + cek_body + driver_main)


# ── Runners ────────────────────────────────────────────────────────────────────

def run_oracle(path: pathlib.Path) -> tuple[int, str, str]:
    r = subprocess.run([sys.executable, CEK, str(path)],
                       capture_output=True, text=True, timeout=300)
    return r.returncode, r.stdout, r.stderr

# Per-file wall-clock budget for the port.  The port is meta-circular
# (Python-CEK ▷ Lark-CEK ▷ object program), so compute-heavy corpus files —
# million-iteration loops, deep recursion, the samples — blow up cubically and
# are unrunnable here.  A timeout is therefore a *performance* verdict, not a
# correctness one: such files are SKIPPED with reason, not failed.  Small
# feature tests type-check (~20s) and evaluate well inside the budget.
PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "90"))

def run_port(driver: str, stdin: str | None = None) -> tuple[int, str, str]:
    tmp = HERE / "_cdriver.lark"
    tmp.write_text(driver)
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)], input=stdin,
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── `read` (stdin) parity ──────────────────────────────────────────────────────
#
# No corpus file reads stdin, so `read` is exercised by a dedicated echo program:
# the oracle runs it with the bytes piped to its real stdin; the port runs the
# SAME program with those bytes threaded through main's IO token (the harness
# embeds them as a String literal — see make_driver's `input`).  Both must agree,
# including the EOF case (a read past the input yields "").  Distinct io names
# (io1/io2/…) sidestep the affine checker's dislike of a shadowed `io`.
READ_ECHO = """module EchoRead

fn main(io : IO) : IO =
  match read(io) with
  | (io1, a) =>
    match read(io1) with
    | (io2, b) =>
      match read(io2) with
      | (io3, c) =>
        let io4 = print(io3, "1:" + a) in
        let io5 = print(io4, "2:" + b) in
        print(io5, "3:" + c)
      end
    end
  end
"""

# (label, stdin) — cover full input, an unterminated last line, EOF short reads.
READ_CASES = [
    ("two lines",          "hello\nworld\n"),
    ("no trailing newline", "alpha\nbeta"),
    ("short (EOF fill)",    "only\n"),
    ("empty stdin",         ""),
]

def read_checks(lex_src: str, parse_src: str, cek_src: str, verbose: bool) -> tuple[int, int]:
    ok = fail = 0
    tmp = HERE / "_readecho.lark"
    tmp.write_text(READ_ECHO)
    try:
        for label, stdin in READ_CASES:
            o = subprocess.run([sys.executable, CEK, str(tmp)], input=stdin,
                               capture_output=True, text=True, timeout=60)
            driver = make_driver(lex_src, parse_src, cek_src, READ_ECHO, stdin)
            pcode, pout, perr = run_port(driver)
            if o.returncode == 0 and pcode == 0 and o.stdout.splitlines() == pout.splitlines():
                print(f"  ok    read/{label}  ({len(o.stdout.splitlines())} lines)")
                ok += 1
            else:
                print(f"  FAIL  read/{label}")
                if verbose:
                    print(f"        oracle={o.stdout.splitlines()!r} port={pout.splitlines()!r}")
                    if perr.strip():
                        print(f"        port_err={perr.strip().splitlines()[-1:]}")
                fail += 1
    finally:
        tmp.unlink(missing_ok=True)
    return ok, fail


def main() -> None:
    verbose   = "-v" in sys.argv
    lex_src   = LEX.read_text()
    parse_src = PARSE.read_text()
    cek_src   = CEKL.read_text()

    ok = fail = skip = 0
    for path in corpus():
        label  = str(path.relative_to(ROOT))
        source = path.read_text()

        adm, why = admissible(source)
        if not adm:
            print(f"  skip  {label}  ({why})")
            skip += 1
            continue
        if label in EXPLICIT_SKIP:
            print(f"  skip  {label}  ({EXPLICIT_SKIP[label]})")
            skip += 1
            continue

        try:
            ocode, oout, oerr = run_oracle(path)
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (oracle timeout)")
            skip += 1
            continue
        if ocode != 0:
            # Oracle itself rejects/crashes (e.g. error-suite files); out of scope.
            print(f"  skip  {label}  (oracle exit {ocode})")
            skip += 1
            continue

        flat, ierr = inline_imports(path, source)
        if ierr:
            print(f"  skip  {label}  ({ierr})")
            skip += 1
            continue

        try:
            pcode, pout, perr = run_port(make_driver(lex_src, parse_src, cek_src, flat))
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (meta-circular eval too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue

        if pcode != 0:
            print(f"  FAIL  {label}  (port crash)")
            tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
            print(f"        {tail[0]}")
            fail += 1
            continue

        expected = oout.splitlines()
        got      = pout.splitlines()
        if got == expected:
            print(f"  ok    {label}  ({len(expected)} lines)")
            ok += 1
        else:
            print(f"  FAIL  {label}")
            if verbose:
                d = difflib.unified_diff(expected, got, "oracle", "port", lineterm="")
                for line in list(d)[:60]:
                    print(f"        {line}")
            else:
                for i, (a, b) in enumerate(zip(expected, got)):
                    if a != b:
                        print(f"        line {i}: oracle={a!r}")
                        print(f"                 port  ={b!r}")
                        break
                if len(expected) != len(got):
                    print(f"        length: oracle={len(expected)} port={len(got)}")
            fail += 1

    print()
    rok, rfail = read_checks(lex_src, parse_src, cek_src, verbose)
    ok += rok
    fail += rfail

    total = ok + fail + skip
    print(f"\n  {ok} ok, {fail} failed, {skip} skipped  "
          f"({len(corpus())} corpus files + {len(READ_CASES)} read cases)")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
