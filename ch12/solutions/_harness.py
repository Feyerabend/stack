"""Shared helper for the Chapter 12 solutions.

Drives the dependent-type kernel `lcore` (ch12/kernel/code/core), the readable
sibling of the `lcore` that checked Lark's soundness proof. The kernel uses
unicode notation (Π, λ, →, Σ) and the REPL form `:let name = (term : Type)`,
which type-checks the term against the annotation (success prints `name : <type>`;
failure prints `definition of 'name' failed`). Because the type checker *is* the
proof checker, "checks" == "is a proof".
"""

import os
import subprocess

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(os.path.dirname(_HERE), "kernel", "code", "core")
_LCORE = os.path.join(_CORE, "lcore")


def ensure_built():
    if not os.path.exists(_LCORE):
        subprocess.run(["make"], cwd=_CORE, check=True,
                       capture_output=True, text=True)


def run(src: str) -> str:
    """Feed `src` to lcore on stdin; return combined stdout+stderr."""
    ensure_built()
    r = subprocess.run([_LCORE], input=src, capture_output=True, text=True)
    return r.stdout + r.stderr


def defined(out: str, name: str) -> bool:
    """True if lcore accepted `name` (printed `name : <type>`, no failure line).
    lcore prefixes REPL lines with '> ', so match the `name : ` substring."""
    return (f"definition of '{name}' failed" not in out
            and f"{name} : " in out)


def failed(out: str, name: str) -> bool:
    return f"definition of '{name}' failed" in out
