"""
Lark TAC → C emitter (the oracle).

This is the Python reference implementation of a TAC-to-C backend.  It is the
oracle against which the eventual self-hosted `lark/emit_tac_c.lark` port will be
differentially checked.

Unlike `emit_c_ast.py` (which emits C from the *syntactic* AST and links against
runtime/runtime.c to feed the CEK C backend), this emitter consumes the *TAC*
produced by lower.py + opt.py — i.e. it sits on the OPTIMIZING backend path:

    parse → typecheck → lower → optimize(OptOptions.O(level)) → emit_tac_c → C

so an optimized program can be compiled to native code through a portable C
target instead of the RV32 assembler.  That is the missing "true self-optimizing
fixpoint" leg (the optimizer and the C fixpoint live on the same backend).

Design — a SELF-CONTAINED C file
--------------------------------
Everything (bump heap, string ops, float ops, show, I/O) is emitted inline, so
the output compiles with a bare `clang out.c -o out` — no runtime/ link step.

The machine word is `intptr_t` (`lkw`), 8 bytes on a 64-bit host.  This is the
one deliberate departure from runtime.c's `uint32_t` word: heap words here must
hold both boxed pointers AND raw function pointers (closure record word 0), and a
32-bit slot truncates a 64-bit code address under ASLR.  Using a full-width word
also makes Int arbitrary-precision *up to 64 bits*, which matches the CEK oracle
for corpus-sized values (RV32's 32-bit wrap is what makes 04_tailrec/19_intoverflow
diverge; this backend does not share that limit).

Value representation (all packed into one `lkw`):
    Unit/False   0
    True         1
    Int          the signed value
    Float        the IEEE-754 float32 bit pattern (zero-extended)
    String/ADT/Closure/tuple   a heap pointer

Heap layout (word = lkw):
    ADT / tuple   [tag_id, field0, field1, ...]
    Closure       [fn_ptr, cap0, cap1, ...]
    String        [len, ...utf8 bytes, '\\0']

Usage:
    python3 emit_tac_c.py FILE.lark [-O0|-O1|-O2|-O3]   # C to stdout
"""

from __future__ import annotations
import struct
from tac import (
    TAC, Function, Instr, Val, Tmp, Const,
    IAssign, IBinOp, IUnary, ICall, IClosureCall, IReturn,
    ILabel, IJump, ICondJump, IAlloc, IGetTag, IGetField, IAllocClosure,
)


# ── Name mangling ────────────────────────────────────────────────────────────
#
# Lark identifiers may contain characters (notably `$` from lifted lambdas and
# `$`-joined impl-method names) that are not portable C identifier characters.
# Encode any non-[A-Za-z0-9_] byte as `_hhh_` so the mapping is injective, and
# prefix by role so the result is always a valid, non-keyword C identifier.

def _mang(s: str) -> str:
    out = []
    for c in s:
        if c.isalnum() or c == "_":
            out.append(c)
        else:
            out.append(f"_{ord(c):x}_")
    return "".join(out)


class CEmitter:
    def __init__(self, tac: TAC) -> None:
        self.tac = tac
        # Constructor tag ids — assigned exactly as asm._collect_tags does, so
        # an IAlloc tag word and an `== <ctor>` tag test agree internally.
        tags: set[str] = set()
        for fn in tac.functions:
            for ins in fn.body:
                if isinstance(ins, IAlloc) and ins.tag != "()":
                    tags.add(ins.tag)
        self.tag_ids: dict[str, int] = {t: i for i, t in enumerate(sorted(tags))}
        self.defined: set[str] = {fn.name for fn in tac.functions}
        self.globals: set[str] = set(tac.global_names)
        # Interned string literals (value → index), filled during emission.
        self.strlits: dict[str, int] = {}
        # Per-function set of tmp names that hold an *integer constructor tag*
        # (the dst of an IGetTag).  An `==`/`!=` against a string Const whose LHS
        # is one of these is a constructor-tag test; otherwise the LHS is a genuine
        # string and the comparison is a content compare (__lark_streq).  Reset by
        # _emit_fn per function.
        self._tag_tmps: set[str] = set()

    # -- names --

    def cfn(self, name: str) -> str:
        """C name for a call/def target."""
        if name == "main":
            return "lark_main"
        if name in self.defined:
            return "lk_" + _mang(name)
        return name          # a runtime builtin — must match the preamble symbol

    def vname(self, name: str) -> str:
        if name in self.globals:
            return "g_" + _mang(name)
        return "v_" + _mang(name)

    def _strlit(self, s: str) -> int:
        if s not in self.strlits:
            self.strlits[s] = len(self.strlits)
        return self.strlits[s]

    # -- value expressions --

    def vref(self, v: Val) -> str:
        if isinstance(v, Tmp):
            return self.vname(v.name)
        # Const
        val = v.value
        if val is None:
            return "(lkw)0"
        if val is True:
            return "(lkw)1"
        if val is False:
            return "(lkw)0"
        if isinstance(val, bool):        # (already handled, but keep explicit)
            return "(lkw)1" if val else "(lkw)0"
        if isinstance(val, int):
            return f"(lkw)({val}LL)"
        if isinstance(val, float):
            bits = struct.unpack("<I", struct.pack("<f", val))[0]
            return f"(lkw){bits}uLL"
        if isinstance(val, str):
            return f"((lkw)STR[{self._strlit(val)}])"
        raise NotImplementedError(f"Const value {val!r}")

    # -- instruction emission --

    def emit_instr(self, ins: Instr, out: list[str]) -> None:
        p = out.append
        match ins:
            case ILabel(name=lbl):
                p(f"  L_{_mang(lbl)}: ;")
            case IJump(label=lbl):
                p(f"  goto L_{_mang(lbl)};")
            case ICondJump(cond=c, true_label=t, false_label=f):
                p(f"  if ({self.vref(c)}) goto L_{_mang(t)}; else goto L_{_mang(f)};")
            case IAssign(dst=dst, src=src):
                p(f"  {self.vname(dst.name)} = {self.vref(src)};")
            case IBinOp(dst=dst, op=op, l=l, r=r):
                p(f"  {self.vname(dst.name)} = {self._binop(op, l, r)};")
            case IUnary(dst=dst, op=op, src=src):
                s = self.vref(src)
                if op == "-":
                    e = f"(-{s})"
                elif op == "not":
                    e = f"({s} ^ 1)"
                else:
                    raise NotImplementedError(f"unary {op}")
                p(f"  {self.vname(dst.name)} = {e};")
            case ICall(dst=dst, fn=callee, args=args):
                argv = ", ".join(self.vref(a) for a in args)
                call = f"{self.cfn(callee)}({argv})"
                if dst is None:
                    p(f"  {call};")
                else:
                    p(f"  {self.vname(dst.name)} = {call};")
            case IClosureCall(dst=dst, fn=fn_val, arg=arg):
                c = self.vref(fn_val)
                a = self.vref(arg)
                d = self.vname(dst.name)
                p(f"  {{ lark_ptr _c = (lark_ptr){c};")
                p(f"    lkw (*_f)(lkw, lkw) = (lkw (*)(lkw, lkw))_c[0];")
                p(f"    {d} = _f((lkw)_c, {a}); }}")
            case IReturn(val=val):
                p(f"  return {self.vref(val) if val is not None else '(lkw)0'};")
            case IAlloc(dst=dst, tag=tag, fields=fields):
                n = 1 + len(fields)
                tag_id = 0 if tag == "()" else self.tag_ids.get(tag, 0)
                p(f"  {{ lark_ptr _p = __heap_alloc({n});")
                p(f"    _p[0] = {tag_id};")
                for i, fld in enumerate(fields):
                    p(f"    _p[{i + 1}] = {self.vref(fld)};")
                p(f"    {self.vname(dst.name)} = (lkw)_p; }}")
            case IGetTag(dst=dst, src=src):
                p(f"  {self.vname(dst.name)} = ((lark_ptr){self.vref(src)})[0];")
            case IGetField(dst=dst, src=src, idx=idx):
                p(f"  {self.vname(dst.name)} = ((lark_ptr){self.vref(src)})[{idx + 1}];")
            case IAllocClosure(dst=dst, fn_name=callee, captured=caps):
                n = 1 + len(caps)
                p(f"  {{ lark_ptr _p = __heap_alloc({n});")
                p(f"    _p[0] = (lkw)&{self.cfn(callee)};")
                for i, cap in enumerate(caps):
                    p(f"    _p[{i + 1}] = {self.vref(cap)};")
                p(f"    {self.vname(dst.name)} = (lkw)_p; }}")
            case _:
                raise NotImplementedError(f"instr {ins!r}")

    def _binop(self, op: str, l: Val, r: Val) -> str:
        L = self.vref(l)
        # Integer / bool arithmetic (compiled with -fwrapv → 2's-complement wrap).
        if op in ("+", "-", "*", "/", "%"):
            return f"({L} {op} {self.vref(r)})"
        if op == "&&":
            return f"({L} & {self.vref(r)})"
        if op == "||":
            return f"({L} | {self.vref(r)})"
        if op in ("<", ">", "<=", ">="):
            return f"({L} {op} {self.vref(r)})"
        if op in ("==", "!="):
            # An `==`/`!=` whose RHS is a string Const is either a constructor-tag
            # test (LHS is an integer tag from IGetTag, RHS names the constructor)
            # or a genuine string-literal comparison (e.g. lexer keyword_kind's
            # `match text with | "fn" => …`).  Distinguish by the LHS: a tag test's
            # LHS is always an IGetTag dst (tracked in self._tag_tmps).
            if isinstance(r, Const) and isinstance(r.value, str):
                if isinstance(l, Tmp) and l.name in self._tag_tmps:
                    # Constructor-tag test — mirror asm._instr: `tag_ids.get(name,
                    # -1)`, so a constructor never *constructed* (absent from the
                    # allocation-derived tag set, e.g. `Green` in 08_traits) maps to
                    # the impossible id -1 and its arm is correctly unreachable.
                    tid = self.tag_ids.get(r.value, -1)
                    return f"({L} {op} {tid})   /* tag {r.value} */"
                # Genuine string comparison — compare contents, not heap pointers.
                eq = f"__lark_streq({L}, {self.vref(r)})"
                return eq if op == "==" else f"(!{eq})"
            return f"({L} {op} {self.vref(r)})"
        raise NotImplementedError(f"binop {op}")

    # -- whole-program assembly --

    def _functions(self) -> list[Function]:
        """The functions to emit, one per name.  A program may bind the same
        top-level name twice (e.g. an imported Stdlib `length` shadowed by a
        local `length`).  tac_vm resolves calls through `{fn.name: fn}`, i.e.
        LAST definition wins; CEK agrees.  Emit only the winning body so the C
        has no duplicate definitions and calls bind exactly as the VMs do."""
        by_name: dict[str, Function] = {}
        for fn in self.tac.functions:
            by_name[fn.name] = fn          # last-wins, first-seen key order
        return list(by_name.values())

    def emit(self) -> str:
        funcs = self._functions()
        bodies: list[str] = []
        for fn in funcs:
            bodies.extend(self._emit_fn(fn))
            bodies.append("")

        protos: list[str] = []
        for fn in funcs:
            params = ", ".join("lkw " + self.vname(p) for p in fn.params) or "void"
            protos.append(f"static lkw {self.cfn(fn.name)}({params});")

        gdecls = [f"static lkw g_{_mang(n)} = 0;" for n in sorted(self.globals)]

        # String-literal table (built during emission above).
        strs = sorted(self.strlits.items(), key=lambda kv: kv[1])
        str_arr = (f"static lark_ptr STR[{len(strs)}];" if strs
                   else "static lark_ptr STR[1];")
        strinit = ["static void __strlit_init(void) {"]
        for s, i in strs:
            strinit.append(f'  STR[{i}] = lark_alloc_string({_cstr(s)});')
        strinit.append("}")

        has_ginit = "__global_init__" in self.defined
        main_lines = [
            "int main(void) {",
            "  __strlit_init();",
            ("  lk___global_init__();" if has_ginit else "  /* no top-level lets */"),
            "  lark_main((lkw)0);",
            "  return 0;",
            "}",
        ]

        parts = [_PREAMBLE, str_arr, ""]
        parts += gdecls + [""]
        parts += protos + [""]
        parts += strinit + [""]
        parts += bodies
        parts += main_lines
        return "\n".join(parts) + "\n"

    def _emit_fn(self, fn: Function) -> list[str]:
        params = ", ".join("lkw " + self.vname(p) for p in fn.params) or "void"
        out = [f"static lkw {self.cfn(fn.name)}({params}) {{"]
        # Declare every temp (any Tmp that is *written*) as a local lkw.  Params
        # and globals are excluded (params are in the signature, globals are file
        # scope).  Reads of an undeclared name can only be a param or a global.
        locals_: list[str] = []
        seen: set[str] = set(fn.params)
        for ins in fn.body:
            for d in _defs(ins):
                if d in seen or d in self.globals:
                    continue
                seen.add(d)
                locals_.append(d)
        if locals_:
            decl = "; ".join("lkw " + self.vname(n) + " = 0" for n in locals_)
            out.append(f"  {decl};")
        self._tag_tmps = {ins.dst.name for ins in fn.body
                          if isinstance(ins, IGetTag) and isinstance(ins.dst, Tmp)}
        for ins in fn.body:
            self.emit_instr(ins, out)
        out.append("  return (lkw)0;")   # fall-through safety net
        out.append("}")
        return out


def _defs(ins: Instr) -> tuple[str, ...]:
    """The Tmp name(s) an instruction writes (its destination), if any."""
    d = getattr(ins, "dst", None)
    if isinstance(d, Tmp):
        return (d.name,)
    return ()


def _cstr(s: str) -> str:
    """A C string literal for `s` (UTF-8, octal-escaped bytes)."""
    out = ['"']
    for b in s.encode("utf-8"):
        c = chr(b)
        if c == '"':
            out.append('\\"')
        elif c == "\\":
            out.append("\\\\")
        elif c == "\n":
            out.append("\\n")
        elif c == "\t":
            out.append("\\t")
        elif c == "\r":
            out.append("\\r")
        elif 32 <= b < 127:
            out.append(c)
        else:
            out.append(f"\\{b:03o}")
    out.append('"')
    return "".join(out)


# ── The self-contained C preamble (heap + builtins, lkw word) ────────────────

_PREAMBLE = r"""/* Generated by emit_tac_c.py — self-contained; compile with:
 *   clang -O2 -fwrapv out.c -o out
 * (-fwrapv makes signed Int overflow wrap two's-complement, matching the VM.) */
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <math.h>

typedef intptr_t lkw;      /* machine word: holds ints, float-bits, or pointers */
typedef lkw*     lark_ptr;

/* ── Bump heap (no GC) ─────────────────────────────────────────────────────── */
#ifndef LARK_HEAP_BYTES
#  define LARK_HEAP_BYTES (256u * 1024u * 1024u)
#endif
static char*  _heap = 0;
static size_t _hp   = 0;

__attribute__((noreturn)) void __lark_match_fail(void) {
    fputs("lark: non-exhaustive pattern match\n", stderr);
    abort();
}

lark_ptr __heap_alloc(long n_words) {
    if (!_heap) { _heap = (char*)malloc(LARK_HEAP_BYTES);
                  if (!_heap) { fputs("lark: heap oom\n", stderr); abort(); } }
    size_t bytes = (size_t)n_words * sizeof(lkw);
    bytes = (bytes + (sizeof(lkw) - 1)) & ~((size_t)sizeof(lkw) - 1);
    if (_hp + bytes > LARK_HEAP_BYTES) { fputs("lark: heap overflow\n", stderr); abort(); }
    lark_ptr p = (lark_ptr)(_heap + _hp);
    _hp += bytes;
    return p;
}

static const char* lark_str_data(lkw s) { return (const char*)(((lark_ptr)s) + 1); }

lark_ptr lark_alloc_string(const char* text) {
    size_t len = strlen(text);
    size_t data_words = (len + 1 + sizeof(lkw) - 1) / sizeof(lkw);
    lark_ptr p = __heap_alloc(1 + (long)data_words);
    p[0] = (lkw)len;
    memcpy((char*)(p + 1), text, len + 1);
    return p;
}

/* ── Strings ───────────────────────────────────────────────────────────────── */
static lkw __str_concat(lkw a, lkw b) {
    lark_ptr pa = (lark_ptr)a, pb = (lark_ptr)b;
    size_t la = (size_t)pa[0], lb = (size_t)pb[0], total = la + lb;
    size_t data_words = (total + 1 + sizeof(lkw) - 1) / sizeof(lkw);
    lark_ptr r = __heap_alloc(1 + (long)data_words);
    r[0] = (lkw)total;
    char* dst = (char*)(r + 1);
    memcpy(dst, lark_str_data(a), la);
    memcpy(dst + la, lark_str_data(b), lb);
    dst[total] = '\0';
    return (lkw)r;
}
static lkw string_length(lkw s) { return ((lark_ptr)s)[0]; }
static int __lark_streq(lkw a, lkw b) {
    return strcmp(lark_str_data(a), lark_str_data(b)) == 0;
}

/* ── Float helpers (float32 bits packed in an lkw) ─────────────────────────── */
static float  _lf(lkw b) { uint32_t u = (uint32_t)b; float f; memcpy(&f, &u, 4); return f; }
static lkw    _fl(float f) { uint32_t u; memcpy(&u, &f, 4); return (lkw)u; }

static lkw __float_add(lkw a, lkw b) { return _fl(_lf(a) + _lf(b)); }
static lkw __float_sub(lkw a, lkw b) { return _fl(_lf(a) - _lf(b)); }
static lkw __float_mul(lkw a, lkw b) { return _fl(_lf(a) * _lf(b)); }
static lkw __float_div(lkw a, lkw b) {
    float d = _lf(b);
    return _fl(d == 0.0f ? __builtin_nanf("") : _lf(a) / d);
}
static lkw __float_lt(lkw a, lkw b) { return _lf(a) <  _lf(b) ? 1 : 0; }
static lkw __float_le(lkw a, lkw b) { return _lf(a) <= _lf(b) ? 1 : 0; }
static lkw __float_gt(lkw a, lkw b) { return _lf(a) >  _lf(b) ? 1 : 0; }
static lkw __float_ge(lkw a, lkw b) { return _lf(a) >= _lf(b) ? 1 : 0; }

/* ── Show / conversion ─────────────────────────────────────────────────────── */
static lkw show(lkw n) {
    char buf[32];
    snprintf(buf, sizeof(buf), "%lld", (long long)n);
    return (lkw)lark_alloc_string(buf);
}
static lkw __show_float(lkw bits) {
    float f = _lf(bits);
    char buf[40];
    snprintf(buf, sizeof(buf), "%.7g", (double)f);
    char* dot = strchr(buf, '.');
    if (dot && !strpbrk(buf, "eEni")) {
        char* end = buf + strlen(buf) - 1;
        while (end > dot + 1 && *end == '0') *end-- = '\0';
    }
    if (!strchr(buf, '.') && !strchr(buf, 'e') && !strchr(buf, 'n') && !strchr(buf, 'i')) {
        size_t n = strlen(buf);
        buf[n] = '.'; buf[n+1] = '0'; buf[n+2] = '\0';
    }
    return (lkw)lark_alloc_string(buf);
}
static lkw __show_bool(lkw b) { return (lkw)lark_alloc_string(b ? "true" : "false"); }
static lkw int_to_float(lkw n)   { return _fl((float)(long long)n); }
static lkw float_to_int(lkw b)   { return (lkw)(long long)_lf(b); }   /* trunc toward zero */
static lkw int_to_string(lkw n)  { return show(n); }
static lkw float_to_string(lkw b){ return __show_float(b); }
static lkw float_to_bits(lkw b)  { return (lkw)(uint32_t)b; }

/* ── Math ──────────────────────────────────────────────────────────────────── */
static lkw int_abs(lkw n)    { return n < 0 ? -n : n; }
static lkw float_abs(lkw b)  { return (lkw)((uint32_t)b & 0x7FFFFFFFu); }
static lkw float_sqrt(lkw b) { return _fl(sqrtf(_lf(b))); }
static lkw float_floor(lkw b){ return _fl(floorf(_lf(b))); }
static lkw float_ceil(lkw b) { return _fl(ceilf(_lf(b))); }

/* ── String primitives ─────────────────────────────────────────────────────── */
static lkw string_index(lkw s, lkw idx) {
    const char* d = lark_str_data(s);
    long n = (long)((lark_ptr)s)[0], i = (long)idx;
    return (i >= 0 && i < n) ? (lkw)(unsigned char)d[i] : (lkw)-1;
}
static lkw string_slice(lkw s, lkw lo, lkw hi) {
    const char* d = lark_str_data(s);
    long n = (long)((lark_ptr)s)[0];
    long a = (long)lo, b = (long)hi;
    if (a < 0) a = 0; if (a > n) a = n;
    if (b < 0) b = 0; if (b > n) b = n;
    long m = (a < b) ? (b - a) : 0;
    size_t data_words = ((size_t)m + 1 + sizeof(lkw) - 1) / sizeof(lkw);
    lark_ptr p = __heap_alloc(1 + (long)data_words);
    p[0] = (lkw)m;
    if (m > 0) memcpy((char*)(p + 1), d + a, (size_t)m);
    ((char*)(p + 1))[m] = '\0';
    return (lkw)p;
}
static lkw char_to_string(lkw cp) {
    char buf[2]; buf[0] = (char)((unsigned)cp & 0xFF); buf[1] = '\0';
    return (lkw)lark_alloc_string(buf);
}

/* string_to_int/float → 3-word record [tag-slot, flag@1, payload@2] (see
 * lower._lower_string_to_result: it reads flag via IGetField idx 0 → word1,
 * payload via idx 1 → word2, then wraps into Ok/Err). */
static lkw __string_to_int_raw(lkw s) {
    const char* d = lark_str_data(s);
    lark_ptr rec = __heap_alloc(3); rec[0] = 0;
    size_t n = strlen(d); int ok = (n > 0); long long val = 0; size_t i = 0;
    int neg = 0;
    if (ok && (d[0] == '+' || d[0] == '-')) { neg = (d[0] == '-'); i = 1; if (i == n) ok = 0; }
    for (; ok && i < n; i++) {
        if (d[i] < '0' || d[i] > '9') { ok = 0; break; }
        val = val * 10 + (d[i] - '0');
    }
    if (ok) {
        long long r = neg ? -val : val;
        r = (long long)((int32_t)r);        /* wrap to i32, matching the VM */
        rec[1] = 1; rec[2] = (lkw)r;
    } else {
        rec[1] = 0; rec[2] = (lkw)lark_alloc_string("string_to_int: not an integer");
    }
    return (lkw)rec;
}
static lkw __string_to_float_raw(lkw s) {
    const char* d = lark_str_data(s);
    lark_ptr rec = __heap_alloc(3); rec[0] = 0;
    size_t n = strlen(d), i = 0, before = 0, after = 0; int ok = (n > 0);
    if (ok && (d[0] == '+' || d[0] == '-')) i = 1;
    while (i < n && d[i] >= '0' && d[i] <= '9') { i++; before++; }
    if (before == 0 || i >= n || d[i] != '.') ok = 0;
    else {
        i++;
        while (i < n && d[i] >= '0' && d[i] <= '9') { i++; after++; }
        if (after == 0 || i != n) ok = 0;
    }
    if (ok) { rec[1] = 1; rec[2] = _fl((float)atof(d)); }
    else    { rec[1] = 0; rec[2] = (lkw)lark_alloc_string("string_to_float: not a float"); }
    return (lkw)rec;
}

/* ── I/O ───────────────────────────────────────────────────────────────────── */
static lkw print(lkw io, lkw s) { puts(lark_str_data(s)); return io; }
static lkw read(lkw io) {
    char buf[4096];
    if (!fgets(buf, sizeof(buf), stdin)) buf[0] = '\0';
    else { size_t n = strlen(buf); if (n && buf[n-1] == '\n') buf[n-1] = '\0'; }
    lark_ptr str = lark_alloc_string(buf);
    lark_ptr tup = __heap_alloc(3);
    tup[0] = 0; tup[1] = io; tup[2] = (lkw)str;
    return (lkw)tup;
}
static lkw read_all(lkw io) {
    size_t cap = 65536, len = 0;
    char* tmp = (char*)malloc(cap);
    if (!tmp) { fputs("lark: read_all oom\n", stderr); abort(); }
    size_t r; char chunk[65536];
    while ((r = fread(chunk, 1, sizeof(chunk), stdin)) > 0) {
        if (len + r + 1 > cap) {
            while (len + r + 1 > cap) cap *= 2;
            char* grown = (char*)realloc(tmp, cap);
            if (!grown) { fputs("lark: read_all oom\n", stderr); abort(); }
            tmp = grown;
        }
        memcpy(tmp + len, chunk, r);
        len += r;
    }
    tmp[len] = '\0';
    lark_ptr str = lark_alloc_string(tmp);
    free(tmp);
    lark_ptr tup = __heap_alloc(3);
    tup[0] = 0; tup[1] = io; tup[2] = (lkw)str;
    return (lkw)tup;
}
"""


def _build(path: str, level: int) -> str:
    import parser as _parser
    import infer as _infer
    from lower import lower
    from opt import optimize, OptOptions
    prog = _parser.parse_file(path)
    tprog = _infer.typecheck(prog, source_file=path)
    tac = lower(tprog)
    tac = optimize(tac, OptOptions.O(level))
    return CEmitter(tac).emit()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("usage: emit_tac_c.py <file.lark> [-O0|-O1|-O2|-O3]", file=sys.stderr)
        sys.exit(1)
    level = 0
    args = [a for a in sys.argv[1:]]
    files = []
    for a in args:
        if a.startswith("-O") and a[2:].isdigit():
            level = int(a[2:])
        else:
            files.append(a)
    sys.stdout.write(_build(files[0], level))
