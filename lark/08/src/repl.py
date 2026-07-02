"""
Lark REPL — interactive read-eval-print loop.

Uses the Python CEK evaluator for immediate evaluation.
Declarations accumulate across the session; :help lists commands.

Architecture:
  - ReplState tracks accumulated source text and the live CEK env/machine.
  - Each new declaration is typechecked in the full accumulated context, then
    only the new typed declaration is evaluated against the existing env.
  - Expressions are wrapped in a throwaway 'let lark_repl_it = <expr>' and
    evaluated in a temporary env so they leave no trace in the state.
  - Multi-line input: a declaration is re-read until the parser no longer
    reports an unexpected-EOF error.
"""
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    import readline  # line editing + history when running interactively
except ImportError:
    pass

import ty
from ty import pretty as _pretty_type, Scheme, Subst, TVar, apply as _ty_apply
from typed_tree import TProgram, TFnDecl, TLetDecl, TTypeDecl, TImplDecl
import infer as _infer
import parser as _parser
from parser import ParseError
from cek import (
    Machine, initial_env, eval_program,
    show as _cek_show,
    Value, VClosure, VPartialCon, VBuiltin, VDispatch, VPrintIO, VIO,
)

PROMPT = "lark> "
CONT   = "   .. "

BANNER = "Lark REPL  (:help for commands, :quit to exit)"

HELP = """\
Commands:
  :quit  :q       Exit
  :type <expr>    Show the inferred type of an expression
  :reset          Clear all accumulated declarations and restart
  :help           Show this message

Declarations (fn, let, type, trait, impl) accumulate across lines.
Expressions are evaluated and displayed as   value : type."""

_DECL_STARTERS = frozenset({"fn", "let", "type", "trait", "impl", "export"})


# -- Type pretty-printing --

def _pretty_scheme(sc: Scheme) -> str:
    """Pretty-print a type scheme, normalising quantified vars to α, β, …"""
    if sc.qs:
        rename: Subst = {q: TVar(i) for i, q in enumerate(sorted(sc.qs))}
        body = _ty_apply(rename, sc.body)
    else:
        body = sc.body
    return _pretty_type(body)


# -- Value display --

def _repl_show(v: Value) -> str:
    """Show a CEK value for REPL display."""
    if isinstance(v, VIO):
        return "<IO>"
    if isinstance(v, (VClosure, VPartialCon, VBuiltin, VDispatch, VPrintIO)):
        return "<function>"
    return _cek_show(v)


# -- Declaration display --

def _display_new(decls: tuple, env: dict) -> str:
    lines = []
    for td in decls:
        match td:
            case TFnDecl(name=name, scheme=sc):
                lines.append(f"fn {name} : {_pretty_scheme(sc)}")
            case TLetDecl(name=name, scheme=sc):
                typ = _pretty_scheme(sc)
                val = env.get(name)
                shown = _repl_show(val) if val is not None else "?"
                lines.append(f"let {name} : {typ} = {shown}")
            case TTypeDecl(name=name):
                lines.append(f"type {name} registered")
            case TImplDecl(trait_name=tr, for_type=ft):
                lines.append(f"impl {tr} for {ft} registered")
    return "\n".join(lines)


# -- REPL state --

class ReplState:
    def __init__(self) -> None:
        self.m    = Machine()
        self.env  = initial_env(self.m)
        self.decls: list[str] = []   # accumulated declaration source lines
        self.count: int       = 0    # tprog.decls already evaluated

    # -- Source construction --

    def _src(self, extra: str = "") -> str:
        parts = ["module Repl"] + self.decls
        if extra:
            parts.append(extra)
        return "\n".join(parts)

    # -- Incremental evaluation --

    def _eval_mini(self, new_decls: tuple, into_env: dict) -> None:
        """Evaluate only the given new declarations into into_env."""
        mini = TProgram("Repl", new_decls)
        eval_program(None, mini, None, self.m, into_env)

    def _global_backpatch(self) -> None:
        """Wire all top-level closures so they see each other (mutual recursion)."""
        all_closures = {n: v for n, v in self.env.items() if isinstance(v, VClosure)}
        for v in all_closures.values():
            v.env.update(all_closures)

    # -- Public interface --

    def add_decl(self, text: str) -> str:
        """Typecheck and evaluate a declaration; return display string."""
        prog  = _parser.parse_src(self._src(text))
        tprog = _infer.typecheck(prog)
        new   = tprog.decls[self.count:]
        self._eval_mini(new, self.env)
        self._global_backpatch()
        self.decls.append(text)
        self.count = len(tprog.decls)
        return _display_new(new, self.env)

    def eval_expr(self, text: str) -> str:
        """Typecheck and evaluate an expression; return 'value : type'."""
        prog  = _parser.parse_src(self._src(f"let lark_repl_it = {text}"))
        tprog = _infer.typecheck(prog)
        repl  = tprog.decls[-1]
        if not isinstance(repl, TLetDecl) or repl.name != "lark_repl_it":
            return "(internal error)"
        temp = dict(self.env)
        self._eval_mini((repl,), temp)
        val = temp["lark_repl_it"]
        typ = _pretty_scheme(repl.scheme)
        return f"{_repl_show(val)} : {typ}"

    def type_of(self, text: str) -> str:
        """Return the inferred type of an expression without evaluating."""
        prog  = _parser.parse_src(self._src(f"let lark_repl_it = {text}"))
        tprog = _infer.typecheck(prog)
        repl  = tprog.decls[-1]
        if not isinstance(repl, TLetDecl):
            return "(internal error)"
        return _pretty_scheme(repl.scheme)

    def reset(self) -> None:
        self.__init__()   # type: ignore[misc]


# -- Input loop --

def _is_decl(line: str) -> bool:
    words = line.split()
    return bool(words) and words[0] in _DECL_STARTERS


def _read_complete(state: ReplState) -> str | None:
    """Read a complete top-level item, prompting for continuation on EOF."""
    try:
        buf = input(PROMPT)
    except EOFError:
        return None

    # For declarations: keep reading lines until the parser doesn't report EOF.
    if _is_decl(buf.lstrip()):
        while True:
            try:
                _parser.parse_src(state._src(buf))
                break                        # parsed OK, done
            except ParseError as e:
                if "EOF" not in e.msg:
                    break                    # real syntax error, let caller handle it
                try:
                    buf += "\n" + input(CONT)
                except EOFError:
                    break
            except Exception:
                break                        # lex error or other — let caller handle it

    return buf


def run_repl() -> None:
    state = ReplState()
    print(BANNER)
    while True:
        raw = _read_complete(state)
        if raw is None:          # Ctrl-D
            print()
            break

        line = raw.strip()
        if not line:
            continue

        if line in (":quit", ":q"):
            break
        if line == ":help":
            print(HELP)
            continue
        if line == ":reset":
            state.reset()
            print("-- environment cleared")
            continue
        if line == ":type":
            print("usage: :type <expr>")
            continue
        if line.startswith(":type "):
            try:
                print(state.type_of(line[6:].strip()))
            except Exception as e:
                print(f"error: {e}")
            continue
        if line.startswith(":"):
            print(f"unknown command {line!r}  (:help for commands)")
            continue

        try:
            if _is_decl(line):
                out = state.add_decl(line)
                if out:
                    print(out)
            else:
                print(state.eval_expr(line))
        except Exception as e:
            print(f"error: {e}")


if __name__ == "__main__":
    run_repl()
