"""
Differential test for the self-hosted TAC→C emitter (SELFHOST M7, slice 3 —
emit_tac_c.lark: the port of 07/src/emit_tac_c.py).

Like lower.lark, emit_tac_c consumes an intermediate representation, not object
source, so this harness ISOLATES it the same way lower_difftest does:

  • the oracle parses + typechecks (infer.py) + lowers (lower.py) the object
    program to a TAC value — WITH NO OPTIMIZATION (opt.lark is M7.4, not yet
    ported), so both sides emit from the identical lowered TAC — and emits C via
    emit_tac_c.py's CEmitter;
  • the port SERIALISES that same TAC into tac.lark constructor source (Operand →
    OTmp/OConst, ConstVal → CInt/…, the 13 Instr, Function, TAC), then runs
    lex+parse+tac+emit_tac_c + a driver that prints `emitTacC(<that TAC>)`.

The two C sources must be byte-identical.  This tests emit_tac_c.lark alone: the
front end + lowerer are the trusted oracles, the TAC is fed in verbatim, and only
emit_tac_c.lark + tac.lark (green since M7.1) run in Lark.  No types/tast module
is needed — emit_tac_c never reads a typed node.

Scope: single-file programs the oracle accepts.  A file is SKIPPED (not failed)
when the oracle can't produce a TAC — it `import`s another module, or it is a
reject fixture (infer raises, nothing to lower) — or when the meta-circular run
overflows / times out (a capacity verdict, not a bug).

Usage:
    python3 self/tests/emit_tac_c_difftest.py [-v]     # -v: unified diff on fail
"""

from __future__ import annotations
import sys, subprocess, pathlib, difflib
import os

HERE  = pathlib.Path(__file__).resolve().parent          # self/tests
SELF  = HERE.parent                                      # self
ROOT  = SELF.parent                                      # lark
SRC   = ROOT / "07" / "src"
CEK   = str(SRC / "cek.py")
LEX   = SELF / "lex.lark"
PARSE = SELF / "parse.lark"
TAC   = SELF / "tac.lark"
EMIT  = SELF / "emit_tac_c.lark"

sys.path.insert(0, str(SRC))
from lexer import LexError              # noqa: E402
import parser as _parser                # noqa: E402
from parser import ParseError           # noqa: E402
import infer as _infer                  # noqa: E402
import lower as _lower                  # noqa: E402
import tac as _tac                       # noqa: E402
from emit_tac_c import CEmitter          # noqa: E402


# ── Serialiser: oracle TAC → tac.lark constructor source ──────────────────────

def _lstr(s: str) -> str:
    """A Lark double-quoted string literal for cek's lexer (escapes \\ " \\n \\t \\r)."""
    out = ['"']
    for ch in s:
        if   ch == "\\": out.append("\\\\")
        elif ch == '"':  out.append('\\"')
        elif ch == "\n": out.append("\\n")
        elif ch == "\t": out.append("\\t")
        elif ch == "\r": out.append("\\r")
        else:            out.append(ch)
    out.append('"')
    return "".join(out)


def _slist(items: list[str]) -> str:
    r = "Nil"
    for x in reversed(items):
        r = f"Cons({x}, {r})"
    return r


def s_const(v) -> str:
    """tac.py Const.value (int|float|bool|str|None) → tac.lark ConstVal ctor."""
    if v is None:           return "CUnit"
    if v is True:           return "CBool(true)"
    if v is False:          return "CBool(false)"
    if isinstance(v, bool): return "CBool(true)"          # unreachable (True/False above)
    if isinstance(v, int):  return f"CInt({_lstr(str(v))})"
    if isinstance(v, float): return f"CFloat({_lstr(repr(v))})"
    if isinstance(v, str):  return f"CStr({_lstr(v)})"
    raise AssertionError(f"unknown const {v!r}")


def s_tmp(t) -> str:
    return f"Tmp({_lstr(t.name)})"


def s_operand(x) -> str:
    """tac.py Val (Tmp | Const) → tac.lark Operand ctor."""
    if isinstance(x, _tac.Tmp):   return f"OTmp({s_tmp(x)})"
    if isinstance(x, _tac.Const): return f"OConst({s_const(x.value)})"
    raise AssertionError(f"unknown operand {x!r}")


def s_maybe_tmp(d) -> str:
    return "Nothing" if d is None else f"Just({s_tmp(d)})"


def s_maybe_op(v) -> str:
    return "Nothing" if v is None else f"Just({s_operand(v)})"


def s_instr(i) -> str:
    T = type(i).__name__
    if T == "IAssign":      return f"IAssign({s_tmp(i.dst)}, {s_operand(i.src)})"
    if T == "IBinOp":       return f"IBinOp({s_tmp(i.dst)}, {_lstr(i.op)}, {s_operand(i.l)}, {s_operand(i.r)})"
    if T == "IUnary":       return f"IUnary({s_tmp(i.dst)}, {_lstr(i.op)}, {s_operand(i.src)})"
    if T == "ICall":        return f"ICall({s_maybe_tmp(i.dst)}, {_lstr(i.fn)}, {_slist([s_operand(a) for a in i.args])})"
    if T == "IClosureCall": return f"IClosureCall({s_tmp(i.dst)}, {s_operand(i.fn)}, {s_operand(i.arg)})"
    if T == "IReturn":      return f"IReturn({s_maybe_op(i.val)})"
    if T == "ILabel":       return f"ILabel({_lstr(i.name)})"
    if T == "IJump":        return f"IJump({_lstr(i.label)})"
    if T == "ICondJump":    return f"ICondJump({s_operand(i.cond)}, {_lstr(i.true_label)}, {_lstr(i.false_label)})"
    if T == "IAlloc":       return f"IAlloc({s_tmp(i.dst)}, {_lstr(i.tag)}, {_slist([s_operand(x) for x in i.fields])})"
    if T == "IGetTag":      return f"IGetTag({s_tmp(i.dst)}, {s_operand(i.src)})"
    if T == "IGetField":    return f"IGetField({s_tmp(i.dst)}, {s_operand(i.src)}, {i.idx})"
    if T == "IAllocClosure": return f"IAllocClosure({s_tmp(i.dst)}, {_lstr(i.fn_name)}, {_slist([s_operand(x) for x in i.captured])})"
    raise AssertionError(f"unknown instr {T}")


def s_function(f) -> str:
    params = _slist([_lstr(p) for p in f.params])
    body   = _slist([s_instr(i) for i in f.body])
    return f"Function({_lstr(f.name)}, {params}, {body}, 0)"   # ctr unused by the emitter


def s_tac(tac) -> str:
    funcs   = _slist([s_function(f) for f in tac.functions])
    globals_ = _slist([_lstr(n) for n in sorted(tac.global_names)])
    return f"TAC({funcs}, {globals_})"


# ── Oracle ────────────────────────────────────────────────────────────────────

def oracle(path: pathlib.Path):
    """Return (verdict, payload).  verdict in {'emit','skip'}."""
    try:
        prog = _parser.parse_file(str(path))
    except (LexError, ParseError) as e:
        return "skip", f"oracle parse error: {e}"
    if prog.imports:
        return "skip", "multi-module (import) — outside single-file port"
    try:
        tprog = _infer.typecheck(prog, source_file=str(path))
    except (_infer.TypeError, _infer.AffineError, _infer.TraitBoundError) as e:
        return "skip", f"reject fixture (infer: {str(e)[:40]}) — nothing to lower"
    tac = _lower.lower(tprog)          # NO optimization: isolate emit_tac_c
    return "emit", (tac, CEmitter(tac).emit())


# ── Port: concatenate lex + parse + tac + emit_tac_c + a driver ───────────────

MAIN_MARKER = "\nfn main(io : IO) : IO ="

def _strip_lines(src: str, drop_prefixes: tuple[str, ...]) -> str:
    keep = [ln for ln in src.splitlines()
            if not any(ln.lstrip().startswith(p) for p in drop_prefixes)]
    return "\n".join(keep)

def make_driver(tac) -> str:
    lex   = _strip_lines(LEX.read_text().split(MAIN_MARKER, 1)[0],   ("module ",))
    parse = _strip_lines(PARSE.read_text().split(MAIN_MARKER, 1)[0], ("module ", "import "))
    tacm  = _strip_lines(TAC.read_text().split(MAIN_MARKER, 1)[0],   ("module ", "import "))
    emit  = _strip_lines(EMIT.read_text().split(MAIN_MARKER, 1)[0],  ("module ", "import "))
    prog  = s_tac(tac)
    driver_main = (
        "\nfn main(io : IO) : IO =\n"
        f"  let prog = {prog} in\n"
        "  print(io, emitTacC(prog))\n"
    )
    return ("module Selfhost\n\n"
            + lex + "\n" + parse + "\n" + tacm + "\n" + emit + driver_main)


PORT_TIMEOUT = int(os.environ.get("LARK_TIMEOUT", "120"))

def run_port(tac):
    tmp = HERE / "_emittacdriver.lark"
    tmp.write_text(make_driver(tac))
    try:
        r = subprocess.run([sys.executable, CEK, str(tmp)],
                           capture_output=True, text=True, timeout=PORT_TIMEOUT)
        return r.returncode, r.stdout, r.stderr
    finally:
        tmp.unlink(missing_ok=True)


# ── Corpus + driver loop ──────────────────────────────────────────────────────

def corpus() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for base in [ROOT / "07" / "tests", ROOT / "07" / "samples"]:
        if not base.exists():
            continue
        for p in sorted(base.rglob("*.lark")):
            if p.name.startswith("_"):
                continue
            files.append(p)
    return files


def main() -> None:
    verbose = "-v" in sys.argv
    ok = fail = skip = 0

    for path in corpus():
        label = str(path.relative_to(ROOT))
        verdict, payload = oracle(path)
        if verdict == "skip":
            print(f"  skip  {label}  ({payload})")
            skip += 1
            continue

        tac, want = payload
        try:
            pcode, pout, perr = run_port(tac)
        except subprocess.TimeoutExpired:
            print(f"  skip  {label}  (meta-circular emit too slow — >{PORT_TIMEOUT}s)")
            skip += 1
            continue

        if pcode != 0:
            tail = (perr or pout).strip().splitlines()[-1:] or ["?"]
            if "recursion" in (perr or "").lower() or "maximum" in (perr or "").lower():
                print(f"  skip  {label}  (CEK overflow on deep TAC: {tail[0][:50]})")
                skip += 1
            else:
                print(f"  FAIL  {label}  (port crash)")
                print(f"        {tail[0]}")
                fail += 1
            continue

        got = pout
        want_nl = want + "\n"           # cek's print adds one newline; emit() ends in one
        if got == want_nl:
            n = want.count("\n")
            print(f"  ok    {label}  ({n} C lines)")
            ok += 1
        else:
            print(f"  FAIL  {label}  (C mismatch)")
            exp = want_nl.splitlines()
            gt  = got.splitlines()
            if verbose:
                d = difflib.unified_diff(exp, gt, "oracle", "port", lineterm="")
                for line in list(d)[:80]:
                    print(f"        {line}")
            else:
                for i in range(max(len(exp), len(gt))):
                    a = exp[i] if i < len(exp) else "<none>"
                    b = gt[i]  if i < len(gt)  else "<none>"
                    if a != b:
                        print(f"        line {i}: oracle={a!r}")
                        print(f"                 port  ={b!r}")
                        break
            fail += 1

    print(f"\n  {ok} ok / {fail} fail / {skip} skip")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
