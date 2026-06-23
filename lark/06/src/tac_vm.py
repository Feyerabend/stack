"""
Lark TAC VM — interpreter for the three-address code IR.

Purpose: validate that lower.py is semantically correct before we build the
RISC-V backend.  The VM runs the same acceptance tests as the CEK machine and
should produce identical output.

Design
──────
Execution uses an explicit call stack — not Python's call stack.  This means
even a million-step tail-recursive program does not overflow.

  call_stack  : list[(Frame, Tmp | None)]
                The Tmp is where to write the return value in the *caller*
                frame.  None means the return value is discarded (main).

Each Frame contains:

  fn          : Function          — the function being executed
  pc          : int               — index into fn.body
  regs        : dict[str, Value]  — temporaries and parameters
  label_map   : dict[str, int]    — label name → body index

Heap values
───────────
ADT / tuple   {"__tag__": str,      "fields": list}
Closure       {"__fn__": str,       "caps":   list}   fn is a user function name
Built-in      {"__fn__": Callable,  "caps":   list}   fn is a Python function
String        plain Python str
Int / Float   plain Python int / float
Bool          plain Python bool
Unit          None
"""

from __future__ import annotations
import sys, os, struct

def _f32(x: float) -> float:
    """Round a Python float to float32 precision (matches RV32 VM register width)."""
    return struct.unpack('f', struct.pack('f', float(x)))[0]
sys.path.insert(0, os.path.dirname(__file__))

from tac import (
    TAC, Function, Val, Tmp, Const,
    IAssign, IBinOp, IUnary, ICall, IClosureCall,
    IReturn, ILabel, IJump, ICondJump,
    IAlloc, IGetTag, IGetField, IAllocClosure,
    Instr,
)

Value = object


# ── Heap value helpers ────────────────────────────────────────────────────────

def _mk_adt(tag: str, fields: list) -> dict:
    return {"__tag__": tag, "fields": list(fields)}

def _mk_closure(fn_name: str, caps: list) -> dict:
    return {"__fn__": fn_name, "caps": list(caps)}

def _mk_builtin(fn) -> dict:
    return {"__fn__": fn, "caps": []}

def _is_closure(v) -> bool:
    return isinstance(v, dict) and "__fn__" in v

def _is_adt(v) -> bool:
    return isinstance(v, dict) and "__tag__" in v


# ── Show ──────────────────────────────────────────────────────────────────────

def _show(v: Value) -> str:
    if isinstance(v, bool):    return "true" if v else "false"
    if isinstance(v, int):     return str(v)
    if isinstance(v, float):    return str(v)
    if isinstance(v, str):     return v
    if v is None:              return "()"
    if isinstance(v, tuple):
        return "(" + ", ".join(_show(e) for e in v) + ")"
    if _is_adt(v):
        tag  = v["__tag__"]
        flds = v["fields"]
        if not flds:  return tag
        return f"{tag}({', '.join(_show(f) for f in flds)})"
    if _is_closure(v):
        fn = v["__fn__"]
        nm = fn.__name__ if callable(fn) else str(fn)
        return f"<closure:{nm}>"
    return repr(v)


# ── Built-in functions ────────────────────────────────────────────────────────

def _builtin_print(io, s: str):
    print(s)
    return io

def _builtin_show(v):
    return _show(v)

def _builtin_read(io):
    line = input()
    return _mk_adt("()", [io, line])

def _builtin_int_to_float(n):    return float(n)
def _builtin_float_to_int(f):    return int(f)
def _builtin_int_to_string(n):   return str(n)
def _builtin_float_to_string(f):
    f32 = _f32(f)
    s = f"{f32:.7g}"
    return s if '.' in s or 'e' in s else s + '.0'

def _builtin_str_concat(a, b): return a + b

def _builtin_show_float(f):
    f32 = _f32(f)
    s = f"{f32:.7g}"
    return s if '.' in s or 'e' in s else s + '.0'

def _builtin_show_bool(b):     return "true" if b else "false"

def _builtin_float_add(a, b):  return _f32(_f32(a) + _f32(b))
def _builtin_float_sub(a, b):  return _f32(_f32(a) - _f32(b))
def _builtin_float_mul(a, b):  return _f32(_f32(a) * _f32(b))
def _builtin_float_div(a, b):
    fb = _f32(b)
    return _f32(_f32(a) / fb) if fb else float('nan')
def _builtin_float_lt(a, b):   return _f32(a) < _f32(b)
def _builtin_float_le(a, b):   return _f32(a) <= _f32(b)
def _builtin_float_gt(a, b):   return _f32(a) > _f32(b)
def _builtin_float_ge(a, b):   return _f32(a) >= _f32(b)

import math as _math
def _builtin_string_length(s):    return len(s)
def _builtin_int_abs(n):          return abs(n)
def _builtin_float_abs(f):        return abs(f)
def _builtin_float_sqrt(f):       return _math.sqrt(f) if f >= 0.0 else float('nan')
def _builtin_float_floor(f):      return float(_math.floor(f))
def _builtin_float_ceil(f):       return float(_math.ceil(f))


_BUILTINS: dict[str, Value] = {
    "print":           _mk_builtin(_builtin_print),
    "show":            _mk_builtin(_builtin_show),
    "read":            _mk_builtin(_builtin_read),
    "int_to_float":    _mk_builtin(_builtin_int_to_float),
    "float_to_int":    _mk_builtin(_builtin_float_to_int),
    "int_to_string":   _mk_builtin(_builtin_int_to_string),
    "float_to_string": _mk_builtin(_builtin_float_to_string),
    "__str_concat":    _mk_builtin(_builtin_str_concat),
    "__show_float":    _mk_builtin(_builtin_show_float),
    "__show_bool":     _mk_builtin(_builtin_show_bool),
    "__float_add":     _mk_builtin(_builtin_float_add),
    "__float_sub":     _mk_builtin(_builtin_float_sub),
    "__float_mul":     _mk_builtin(_builtin_float_mul),
    "__float_div":     _mk_builtin(_builtin_float_div),
    "__float_lt":      _mk_builtin(_builtin_float_lt),
    "__float_le":      _mk_builtin(_builtin_float_le),
    "__float_gt":      _mk_builtin(_builtin_float_gt),
    "__float_ge":      _mk_builtin(_builtin_float_ge),
    "string_length":   _mk_builtin(_builtin_string_length),
    "int_abs":         _mk_builtin(_builtin_int_abs),
    "float_abs":       _mk_builtin(_builtin_float_abs),
    "float_sqrt":      _mk_builtin(_builtin_float_sqrt),
    "float_floor":     _mk_builtin(_builtin_float_floor),
    "float_ceil":      _mk_builtin(_builtin_float_ceil),
}


# ── Frame ─────────────────────────────────────────────────────────────────────

class Frame:
    __slots__ = ("fn", "pc", "regs", "_labels", "_globals")

    def __init__(
        self, fn: Function, params: dict[str, Value],
        globals_: dict[str, Value] | None = None,
    ) -> None:
        self.fn       = fn
        self.pc       = 0
        self.regs: dict[str, Value] = dict(params)
        self._globals = globals_ or {}
        self._labels: dict[str, int] = {
            instr.name: i
            for i, instr in enumerate(fn.body)
            if isinstance(instr, ILabel)
        }

    def read(self, v: Val) -> Value:
        match v:
            case Const(value=x): return x
            case Tmp(name=n):
                if n in self.regs:     return self.regs[n]
                if n in self._globals: return self._globals[n]
                raise KeyError(n)

    def write(self, dst: Tmp, val: Value) -> None:
        self.regs[dst.name] = val

    def jump(self, label: str) -> None:
        self.pc = self._labels[label]


# ── Binary operators ──────────────────────────────────────────────────────────

def _binop(op: str, l: Value, r: Value) -> Value:
    match op:
        case "+":
            return l + r           # works for int, float, and str
        case "-":  return l - r
        case "*":  return l * r
        case "/":
            if isinstance(l, int) and isinstance(r, int):
                return int(l / r)  # truncate toward zero (matches C)
            return l / r
        case "%":
            if isinstance(l, int) and isinstance(r, int):
                return l - int(l / r) * r   # truncate-toward-zero (matches RV32 rem)
            return l % r
        case "==": return l == r
        case "!=": return l != r
        case "<":  return l < r
        case ">":  return l > r
        case "<=": return l <= r
        case ">=": return l >= r
        case "&&": return bool(l) and bool(r)
        case "||": return bool(l) or bool(r)
        case _:    raise RuntimeError(f"unknown binary op: {op!r}")


# ── VM ────────────────────────────────────────────────────────────────────────

class VM:
    """Iterative TAC interpreter with an explicit call stack."""

    def __init__(self, tac: TAC) -> None:
        self._fns: dict[str, Function] = {fn.name: fn for fn in tac.functions}
        self._globals: dict[str, Value] = {}   # populated by __global_init__

    def run(self, io_val: Value = None) -> None:
        # Run global initializer first if present.
        init = self._fns.get("__global_init__")
        if init is not None:
            self._run_fn(init, {}, capture_globals=True)

        main = self._fns.get("main")
        if main is None:
            raise RuntimeError("no main function in TAC program")
        self._run_fn(main, {"io": io_val})

    def _run_fn(
        self, fn: Function, param_dict: dict,
        capture_globals: bool = False,
    ) -> None:
        """Build a Frame for fn, then drive the iterative loop."""
        regs: dict[str, Value] = {}
        for p in fn.params:
            regs[p] = param_dict.get(p)
        frame0 = Frame(fn, regs, self._globals)

        # call_stack entries: (Frame, dst_in_caller | None)
        # dst is where to write the return value when this frame finishes.
        call_stack: list[tuple[Frame, Tmp | None]] = [(frame0, None)]

        while call_stack:
            frame, _ = call_stack[-1]

            if frame.pc >= len(frame.fn.body):
                raise RuntimeError(
                    f"function {frame.fn.name!r} fell off end without return"
                )

            instr = frame.fn.body[frame.pc]

            # -- Control flow / call / return --------------------------------

            if isinstance(instr, ILabel):
                frame.pc += 1
                continue

            if isinstance(instr, IJump):
                frame.jump(instr.label)
                frame.pc += 1   # advance past the ILabel we just jumped to
                continue

            if isinstance(instr, ICondJump):
                cond = frame.read(instr.cond)
                frame.jump(instr.true_label if cond else instr.false_label)
                frame.pc += 1   # advance past the ILabel
                continue

            if isinstance(instr, IReturn):
                ret_val = frame.read(instr.val) if instr.val is not None else None
                finished_frame, dst = call_stack.pop()
                # Capture globals from __global_init__ before discarding its frame.
                if capture_globals and finished_frame.fn.name == "__global_init__":
                    self._globals.update(finished_frame.regs)
                if call_stack:
                    caller, _ = call_stack[-1]
                    if dst is not None:
                        caller.write(dst, ret_val)
                    caller.pc += 1
                continue

            if isinstance(instr, ICall):
                callee_name = instr.fn
                arg_vals    = [frame.read(a) for a in instr.args]

                if callee_name == "__lark_match_fail":
                    raise RuntimeError("non-exhaustive match")

                if callee_name in _BUILTINS:
                    result = _BUILTINS[callee_name]["__fn__"](*arg_vals)
                    if instr.dst is not None:
                        frame.write(instr.dst, result)
                    frame.pc += 1
                    continue

                callee_fn = self._fns.get(callee_name)
                if callee_fn is None:
                    raise RuntimeError(f"unknown function: {callee_name!r}")
                callee_regs = {p: v for p, v in zip(callee_fn.params, arg_vals)}
                callee_frame = Frame(callee_fn, callee_regs, self._globals)
                call_stack.append((callee_frame, instr.dst))
                continue   # don't advance caller; will advance when callee returns

            if isinstance(instr, IClosureCall):
                clos = frame.read(instr.fn)
                arg  = frame.read(instr.arg)

                if not _is_closure(clos):
                    raise RuntimeError(f"IClosureCall on non-closure: {clos!r}")

                fn_ref = clos["__fn__"]
                caps   = clos["caps"]

                if callable(fn_ref):
                    # Built-in closure variant (shouldn't normally arise).
                    result = fn_ref(*caps, arg)
                    frame.write(instr.dst, result)
                    frame.pc += 1
                    continue

                callee_fn = self._fns.get(fn_ref)
                if callee_fn is None:
                    raise RuntimeError(f"unknown closure function: {fn_ref!r}")
                # Convention: (env=closure_record, arg)
                callee_regs = {
                    callee_fn.params[0]: clos,
                    callee_fn.params[1]: arg,
                }
                callee_frame = Frame(callee_fn, callee_regs, self._globals)
                call_stack.append((callee_frame, instr.dst))
                continue

            # -- Ordinary instructions (no control flow) ---------------------

            match instr:

                case IAssign(dst=dst, src=src):
                    frame.write(dst, frame.read(src))

                case IBinOp(dst=dst, op=op, l=l, r=r):
                    frame.write(dst, _binop(op, frame.read(l), frame.read(r)))

                case IUnary(dst=dst, op=op, src=src):
                    v = frame.read(src)
                    match op:
                        case "-":   frame.write(dst, -v)
                        case "not": frame.write(dst, not v)
                        case _:     raise RuntimeError(f"unknown unary op: {op!r}")

                case IAlloc(dst=dst, tag=tag, fields=fields):
                    flds = [frame.read(f) for f in fields]
                    frame.write(dst, _mk_adt(tag, flds))

                case IGetTag(dst=dst, src=src):
                    rec = frame.read(src)
                    frame.write(dst, rec["__tag__"])

                case IGetField(dst=dst, src=src, idx=idx):
                    rec = frame.read(src)
                    # Closure records store captured values in "caps";
                    # ADT/tuple records store them in "fields".
                    if _is_closure(rec):
                        frame.write(dst, rec["caps"][idx])
                    else:
                        frame.write(dst, rec["fields"][idx])

                case IAllocClosure(dst=dst, fn_name=fn_name, captured=caps):
                    cap_vals = [frame.read(c) for c in caps]
                    frame.write(dst, _mk_closure(fn_name, cap_vals))

                case _:
                    raise RuntimeError(f"unhandled instruction: {instr!r}")

            frame.pc += 1


# ── Entry point ───────────────────────────────────────────────────────────────

def run_tac(tac: TAC) -> None:
    VM(tac).run(io_val=None)


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: tac_vm.py <file.lark>", file=sys.stderr)
        sys.exit(1)

    import parser as _parser
    import infer  as _infer
    from lower import lower

    path  = sys.argv[1]
    prog  = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac   = lower(tprog)

    try:
        run_tac(tac)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
