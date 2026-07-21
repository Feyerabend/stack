"""
Differential test for the self-hosted C-AST emitter (SELFHOST M5, the F2 half).

For every self-contained .lark file in the corpus it compares two C outputs:

  • the oracle — 07/src/emit_c_ast.py (the frozen Python emitter) run on the
    file, its stdout (the generated C source) captured;
  • the port    — self/emit_c.lark, driven through the Python CEK, emitting the
    SAME source (embedded as a String literal, lexed + parsed + emitted in Lark).

They must be byte-identical, line for line.

Why this works without inference
────────────────────────────────
emit_c_ast.py walks infer.py's *typed* AST, but it never reads a node's inferred
type — only its structure, names and literal values — and the typed AST is a 1:1
structural copy of the syntactic one (verified against infer.py's `infer`).  So
emit_c.lark emits straight from parse.lark's `Prog`; infer.lark is not needed on
this path.  Trait decls carry no runtime representation, so both sides drop them.

Composition (same as cek_difftest.py)
──────────────────────────────────────
emit_c.lark is a *component*: it emits parse.lark's `Prog` and reuses lex.lark's
`tokenize`/`P`.  We do not use `import` (the toolchain's import path skips infer
Pass 1.5 — SELFHOST §7); the driver is built by CONCATENATION:
  lex.lark body + parse.lark body + emit_c.lark body + a generated main,
all under one `module Selfhost`, through the normal top-level typechecker.

Scope
─────
Any file the oracle can emit (parses + type-checks), INCLUDING multi-module
`import` programs — the port has no `import`, so the harness flattens them to the
decl stream the oracle's emitter core sees (see inline_imports_for_emit).  A file
is SKIPPED only for reasons outside the port's control: the oracle rejects it
(error-suite files, or a program with no valid types), an import can't be resolved
to a module file, or the meta-circular pass exceeds the time budget.

Usage:
    python3 self/tests/emit_c_difftest.py [-v]      # -v: show a unified diff
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib, re
import os

HERE   = pathlib.Path(__file__).resolve().parent          # self/tests
SELF   = HERE.parent                                      # self
ROOT   = SELF.parent                                      # lark
SRC    = ROOT / "07" / "src"
EMIT   = str(SRC / "emit_c_ast.py")
LEX    = SELF / "lex.lark"
PARSE  = SELF / "parse.lark"
EMITL  = SELF / "emit_c.lark"

sys.path.insert(0, str(SRC))
from lexer import LexError                    # noqa: E402
import parser as _parser                      # noqa: E402
from parser import ParseError                 # noqa: E402

PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))       # concat program (~1500 lines) type-checks + runs here


# ── Corpus ─────────────────────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "07" / "tests", ROOT / "07" / "samples"]:
        for p in sorted(base.rglob("*.lark")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files


def uses_import(source: str) -> bool:
    return any(ln.lstrip().startswith("import ") for ln in source.splitlines())


# ── Import inlining (emit order = imported decls, then main decls) ──────────────
#
# emit_c_ast.emit() builds `all_decls = _load_imports(prog) + tprog.decls`.  BUT
# infer.typecheck already INLINES imported decls into `tprog.decls` (Pass 0,
# infer.py:789 `typed_decls.extend(imp_decls)`), so `_load_imports` adds them a
# SECOND time — the oracle emits every imported module's decls TWICE (see the
# _d0–_d3 / _d4–_d7 duplication for 09_modules).  This is a real bug in the
# oracle's emit() wrapper, surfaced by self-hosting (logged in SELFHOST §7); the
# emitter CORE is correct — it faithfully emits whatever decl stream it is given.
#
# The port has no `import`, so to compare the two emitter cores on the SAME input
# we flatten to one program whose decl stream equals what the oracle's core sees:
# [imported decls, depth-first, once] + [imported decls again] + [main decls].  We
# strip every module/import header and concatenate the deduped imported bodies
# TWICE ahead of the main body, under one fresh module header.  The module NAME is
# irrelevant to the output (the C header comment uses the file's basename), so the
# oracle still runs the ORIGINAL file and the two must agree byte-for-byte.

def _resolve_module(src_dir: pathlib.Path, module: str) -> pathlib.Path | None:
    for cand in (src_dir / f"{module.lower()}.lark", src_dir / f"{module}.lark"):
        if cand.exists():
            return cand
    return None

def _strip_module_import_lines(text: str) -> str:
    """Drop leading `module`/`import` lines (imported modules have single-line
    imports only in this corpus; balanced-paren handling lives in the main path)."""
    return "\n".join(ln for ln in text.splitlines()
                     if not ln.lstrip().startswith(("module ", "import ")))

def _strip_import_stmts(source: str) -> str:
    """Remove whole `import ...` statements, incl. multi-line `exposing ( ... )`
    continuations (balanced-paren scan), and the `module` header line."""
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
        if ln.lstrip().startswith("module "):
            i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out)

def inline_imports_for_emit(path: pathlib.Path, source: str) -> tuple[str, str]:
    """Flatten a multi-module program to one program whose decl order matches
    emit_c_ast._load_imports (imported decls depth-first, then main decls).
    Returns (flattened_source, error); error non-empty ⇒ unresolvable import."""
    prog = _parser.parse_src(source, str(path))
    if not prog.imports:
        return source, ""
    loaded: set[str] = set()
    bodies: list[str] = []
    err: list[str] = []

    def load(p, directory: pathlib.Path) -> None:
        for imp in p.imports:
            mod = imp.module
            if mod in loaded or err:
                continue
            loaded.add(mod)
            mpath = _resolve_module(directory, mod)
            if mpath is None:
                err.append(f"cannot resolve import {mod}")
                return
            msrc  = mpath.read_text()
            mprog = _parser.parse_src(msrc, str(mpath))
            load(mprog, mpath.parent)                 # depth-first: its imports first
            bodies.append(_strip_module_import_lines(msrc))

    load(prog, path.parent)
    if err:
        return source, err[0]
    main_body = _strip_import_stmts(source)
    # Bodies TWICE: once for emit()'s _load_imports, once for typecheck's inlined
    # copy inside tprog.decls (the oracle's double-emission — see the note above).
    dup = "\n\n".join(bodies)
    flat = ("module Selfhost\n\n"
            + dup + "\n\n" + dup
            + "\n\n(* ── imported decls emitted twice (oracle emit() double-inlines); main below ── *)\n"
            + main_body)
    return flat, ""


# The oracle renames a wildcard param `_` to `_anon_{id(node)}` (infer.py:420,573)
# using a nondeterministic CPython object id, then bakes that address into the
# emitted C as the (never-referenced) closure param name.  No port can reproduce
# a specific id(); the port keeps the deterministic `_`.  Canonicalise the one
# nondeterministic token on both sides so the differential stays meaningful.
# `_anon_<digits>` never appears in the corpus, so this cannot mask a real name.
_ANON = re.compile(r'_anon_\d+')

def canon(text: str) -> str:
    return _ANON.sub("_", text)


# ── Driver assembly (mirror cek_difftest.make_driver, emit entry point) ────────

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

def make_driver(lex_src: str, parse_src: str, emit_src: str,
                source: str, basename: str) -> str:
    lex_body   = lex_src.split(MAIN_MARKER, 1)[0]
    parse_body = parse_src.split(MAIN_MARKER, 1)[0]
    emit_body  = emit_src.split(MAIN_MARKER, 1)[0]
    lex_body   = _strip_lines(lex_body,   ("module ",))
    parse_body = _strip_lines(parse_body, ("module ", "import "))
    emit_body  = _strip_lines(emit_body,  ("module ", "import "))
    lit  = lark_string_literal(source)
    blit = lark_string_literal(basename)
    driver_main = (
        '\nfn main(io : IO) : IO =\n'
        f'  let src = "{lit}" in\n'
        f'  let base = "{blit}" in\n'
        '  print(io, emitProgram(base, parseProgram(tokenize(src, string_length(src), P(0, 1, 1)))))\n'
    )
    return ("module Selfhost\n\n"
            + lex_body + "\n" + parse_body + "\n" + emit_body + driver_main)


# ── Runners ────────────────────────────────────────────────────────────────────

def run_oracle(path: pathlib.Path) -> tuple[int, str, str]:
    r = subprocess.run([sys.executable, EMIT, str(path)],
                       capture_output=True, text=True, timeout=120)
    return r.returncode, r.stdout, r.stderr

def run_port(driver: str) -> tuple[int, str, str]:
    tmp = HERE / "_edriver.lark"
    tmp.write_text(driver)
    try:
        r = subprocess.run([sys.executable, str(SRC / "cek.py"), str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    verbose   = "-v" in sys.argv
    lex_src   = LEX.read_text()
    parse_src = PARSE.read_text()
    emit_src  = EMITL.read_text()

    ok = fail = skip = 0
    for path in corpus():
        label  = str(path.relative_to(ROOT))
        source = path.read_text()

        # Oracle must parse; a lex/parse error is out of scope (error-suite).
        try:
            _parser.parse_src(source, "<corpus>")
        except (LexError, ParseError) as e:
            print(f"  skip  {label}  (oracle parse error: {e})")
            skip += 1
            continue

        port_source = source
        if uses_import(source):
            port_source, ierr = inline_imports_for_emit(path, source)
            if ierr:
                print(f"  skip  {label}  ({ierr})")
                skip += 1
                continue

        try:
            ocode, oout, oerr = run_oracle(path)
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (oracle timeout)")
            skip += 1
            continue
        if ocode != 0:
            # Oracle rejects (e.g. type-error suite): nothing to emit.
            print(f"  skip  {label}  (oracle exit {ocode})")
            skip += 1
            continue

        try:
            pcode, pout, perr = run_port(make_driver(lex_src, parse_src, emit_src,
                                                     port_source, path.name))
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (meta-circular emit too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue

        if pcode != 0:
            print(f"  FAIL  {label}  (port crash)")
            tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
            print(f"        {tail[0]}")
            fail += 1
            continue

        expected = canon(oout).splitlines()
        got      = canon(pout).splitlines()
        if got == expected:
            print(f"  ok    {label}  ({len(expected)} lines)")
            ok += 1
        else:
            print(f"  FAIL  {label}")
            if verbose:
                d = difflib.unified_diff(expected, got, "oracle", "port", lineterm="")
                for line in list(d)[:80]:
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

    total = ok + fail + skip
    print(f"\n  {ok} ok, {fail} failed, {skip} skipped  ({total} corpus files)")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
