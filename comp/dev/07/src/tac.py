"""
Lark TAC — three-address code intermediate representation.

Every Lark function is lowered to a flat sequence of Instructions.
Values are either named temporaries (Tmp) or compile-time constants (Const).

Pipeline position:
    typed_tree.py  →  lower.py  →  tac.py  →  asm.py  →  RISC-V text

Design choices
--------------
• Temporaries are strings, not integers, so pretty-printed TAC is readable.
• Multi-argument static calls (ICall) use the standard function name directly.
  Closure calls (IClosureCall) pass one argument at a time (closures are curried).
• ADT values and tuples are heap-allocated via IAlloc; fields are accessed by
  index via IGetField. Tags are read via IGetTag (used in pattern matching).
• IAllocClosure packages a lifted function name with its captured values.
  The closure calling convention is (env_ptr, arg) → result.
"""

from __future__ import annotations
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dataclasses import dataclass, field
from typing import Union


# -- Values --

@dataclass(frozen=True)
class Tmp:
    """A named temporary — result of every computation."""
    name: str
    def __str__(self) -> str: return self.name

@dataclass(frozen=True)
class Const:
    """A compile-time constant (int, float, bool, str, or None for unit)."""
    value: int | float | bool | str | None
    def __str__(self) -> str:
        if self.value is None:  return "()"
        if self.value is True:  return "true"
        if self.value is False: return "false"
        return repr(self.value)

Val = Union[Tmp, Const]


# -- Instructions --

@dataclass(frozen=True)
class IAssign:
    """dst = src"""
    dst: Tmp
    src: Val

@dataclass(frozen=True)
class IBinOp:
    """dst = l op r"""
    dst: Tmp
    op:  str
    l:   Val
    r:   Val

@dataclass(frozen=True)
class IUnary:
    """dst = op src"""
    dst: Tmp
    op:  str
    src: Val

@dataclass(frozen=True)
class ICall:
    """dst = fn(args)  — static call to a known named function."""
    dst:  Tmp | None   # None when result is unused
    fn:   str          # callee name (resolved at link time)
    args: tuple[Val, ...]

@dataclass(frozen=True)
class IClosureCall:
    """dst = closure_val(arg)  — indirect call through a closure (curried)."""
    dst: Tmp
    fn:  Val           # Tmp holding the closure
    arg: Val

@dataclass(frozen=True)
class IReturn:
    """return val"""
    val: Val | None    # None for functions returning unit

@dataclass(frozen=True)
class ILabel:
    """label:"""
    name: str

@dataclass(frozen=True)
class IJump:
    """goto label"""
    label: str

@dataclass(frozen=True)
class ICondJump:
    """if cond goto true_label else false_label"""
    cond:        Val
    true_label:  str
    false_label: str

@dataclass(frozen=True)
class IAlloc:
    """dst = alloc tag(fields...)  — heap-allocate a tagged record."""
    dst:    Tmp
    tag:    str
    fields: tuple[Val, ...]

@dataclass(frozen=True)
class IGetTag:
    """dst = tag(src)  — read the constructor tag of a heap record."""
    dst: Tmp
    src: Val

@dataclass(frozen=True)
class IGetField:
    """dst = src[idx]  — read one field from a heap record."""
    dst: Tmp
    src: Val
    idx: int

@dataclass(frozen=True)
class IAllocClosure:
    """dst = closure(fn_name; captured...)  — build a closure record."""
    dst:      Tmp
    fn_name:  str          # the lifted top-level function
    captured: tuple[Val, ...]

Instr = Union[
    IAssign, IBinOp, IUnary,
    ICall, IClosureCall,
    IReturn, ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
]


# -- Function and module --

@dataclass
class Function:
    """A flat sequence of instructions with named parameters."""
    name:   str
    params: tuple[str, ...]
    body:   list[Instr] = field(default_factory=list)
    _ctr:   int         = field(default=0, repr=False)

    def fresh(self, hint: str = "t") -> Tmp:
        t = Tmp(f"{hint}{self._ctr}")
        self._ctr += 1
        return t

    def label(self, hint: str = "L") -> str:
        lbl = f".{hint}{self._ctr}"
        self._ctr += 1
        return lbl

    def emit(self, instr: Instr) -> None:
        self.body.append(instr)


@dataclass
class TAC:
    """The full TAC program — a list of functions in definition order."""
    functions:    list[Function]  = field(default_factory=list)
    global_names: frozenset[str]  = field(default_factory=frozenset)

    def add(self, fn: Function) -> None:
        self.functions.append(fn)


# -- Pretty printer --

def _v(v: Val) -> str:
    return str(v)

def _instr_str(i: Instr) -> str:
    match i:
        case ILabel(name=n):
            return f"{n}:"
        case IAssign(dst=d, src=s):
            return f"    {d} = {_v(s)}"
        case IBinOp(dst=d, op=op, l=l, r=r):
            return f"    {d} = {_v(l)} {op} {_v(r)}"
        case IUnary(dst=d, op=op, src=s):
            return f"    {d} = {op}{_v(s)}"
        case ICall(dst=None, fn=f, args=args):
            return f"    call {f}({', '.join(_v(a) for a in args)})"
        case ICall(dst=d, fn=f, args=args):
            return f"    {d} = call {f}({', '.join(_v(a) for a in args)})"
        case IClosureCall(dst=d, fn=fv, arg=a):
            return f"    {d} = {_v(fv)}({_v(a)})"
        case IReturn(val=None):
            return "    return"
        case IReturn(val=v):
            return f"    return {_v(v)}"
        case IJump(label=l):
            return f"    jump {l}"
        case ICondJump(cond=c, true_label=t, false_label=f):
            return f"    if {_v(c)} jump {t} else {f}"
        case IAlloc(dst=d, tag=tag, fields=()):
            return f"    {d} = alloc {tag}"
        case IAlloc(dst=d, tag=tag, fields=fs):
            return f"    {d} = alloc {tag}({', '.join(_v(f) for f in fs)})"
        case IGetTag(dst=d, src=s):
            return f"    {d} = tag({_v(s)})"
        case IGetField(dst=d, src=s, idx=i):
            return f"    {d} = {_v(s)}[{i}]"
        case IAllocClosure(dst=d, fn_name=f, captured=()):
            return f"    {d} = closure({f})"
        case IAllocClosure(dst=d, fn_name=f, captured=caps):
            return f"    {d} = closure({f}; {', '.join(_v(c) for c in caps)})"
        case _:
            return f"    ??? {i!r}"


def pretty(tac: TAC) -> str:
    parts: list[str] = []
    for fn in tac.functions:
        params = ", ".join(fn.params)
        parts.append(f"fn {fn.name}({params}):")
        for instr in fn.body:
            parts.append(_instr_str(instr))
        parts.append("")
    return "\n".join(parts)
