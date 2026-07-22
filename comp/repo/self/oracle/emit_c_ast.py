"""
emit_c_ast.py — Emit a Lark typed AST as a C source file for the C CEK machine.

Usage:
    python3 emit_c_ast.py <file.lark> [output.c]

The output file defines `LkProg lk_program` (and all the static AST nodes it
references), which can be compiled together with cek.c and larkrun.c to produce
a standalone binary.

Design
------
The typed AST (TProgram) is traversed in post-order: every node is emitted after
all the nodes it points to.  Each node gets a unique C identifier (e.g. e0, p3,
d1) based on its type and a counter.  The id() of the Python object is used for
memoisation so shared subtrees (if any) produce a single C variable.

Multi-param lambdas (TLambda with len(params) > 1) and multi-param functions
(TFnDecl with len(params) > 1) are desugared to nested single-param EXPR_LAMBDA
nodes here, so cek.c only needs to handle the single-param form.

Imports are resolved statically: the imported module is parsed and type-checked,
and its declarations are prepended to the emitted program (same approach as
lower.py).  Only the names listed in `exposing` are registered in top_env at
runtime; all are included in the C output since unused decls are harmless.
"""

from __future__ import annotations
import os, sys, struct, pathlib
sys.path.insert(0, os.path.dirname(__file__))

import parser  as _parser
import infer   as _infer
from typed_tree import (
    TProgram, TFnDecl, TLetDecl, TTypeDecl, TImplDecl,
    TExpr, TLit, TVar, TCon, TTupleExpr, TApply, TBinOp, TUnaryOp,
    TLetExpr, TIfExpr, TMatchExpr, TLambda,
    TPat, TPWild, TPVar, TPLit, TPCon, TPTuple,
    TVariant,
)
from tree import ImportDecl


# -- C string escaping --

def _c_str(s: str) -> str:
    out = ['"']
    for ch in s:
        if   ch == '\\': out.append('\\\\')
        elif ch == '"':  out.append('\\"')
        elif ch == '\n': out.append('\\n')
        elif ch == '\r': out.append('\\r')
        elif ch == '\t': out.append('\\t')
        elif ord(ch) < 32:
            out.append(f'\\x{ord(ch):02x}')
        else:
            out.append(ch)
    out.append('"')
    return ''.join(out)


# -- Float bits --

def _f32_bits(f: float) -> int:
    """Return the IEEE 754 float32 bit pattern as an unsigned 32-bit integer."""
    return struct.unpack('I', struct.pack('f', float(f)))[0]


# -- Emitter --

class Emitter:
    def __init__(self) -> None:
        self._lines:     list[str]       = []
        self._seen:      dict[int, str]  = {}   # id(node) → c_name
        self._synthetic: list            = []   # keep synthetic TLambda alive; prevents CPython id reuse
        self._ec = self._pc = self._dc = self._ac = 0   # counters

    # -- Name allocation --

    def _expr_name(self) -> str:
        n = f"_e{self._ec}"; self._ec += 1; return n

    def _pat_name(self) -> str:
        n = f"_p{self._pc}"; self._pc += 1; return n

    def _decl_name(self) -> str:
        n = f"_d{self._dc}"; self._dc += 1; return n

    def _arr_name(self) -> str:
        n = f"_a{self._ac}"; self._ac += 1; return n

    # -- Output helpers --

    def _line(self, s: str) -> None:
        self._lines.append(s)

    def _pointer_array(self, element_type: str, elements: list[str]) -> str:
        """Emit a static array of pointers; return the array name."""
        arr = self._arr_name()
        inner = ', '.join(f'&{e}' for e in elements)
        self._line(f'static const {element_type}* {arr}[] = {{ {inner} }};')
        return arr

    # -- Expressions --

    def emit_expr(self, node: TExpr) -> str:
        """Emit (if not already emitted) and return the C name for node."""
        nid = id(node)
        if nid in self._seen:
            return self._seen[nid]

        name = self._emit_expr_inner(node)
        self._seen[nid] = name
        return name

    def _emit_expr_inner(self, node: TExpr) -> str:  # noqa: C901
        name = self._expr_name()

        if isinstance(node, TLit):
            lit_c = self._lit_init(node.value)
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_LIT, .lit={{{lit_c}}} }};')

        elif isinstance(node, TVar):
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_VAR, .name={_c_str(node.name)} }};')

        elif isinstance(node, TCon):
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_CON, .name={_c_str(node.name)} }};')

        elif isinstance(node, TTupleExpr):
            if not node.elems:
                self._line(f'static const LkExpr {name} = '
                           f'{{ .kind=EXPR_TUPLE, .tup={{NULL, 0}} }};')
            else:
                child_names = [self.emit_expr(e) for e in node.elems]
                arr = self._pointer_array('LkExpr', child_names)
                self._line(f'static const LkExpr {name} = '
                           f'{{ .kind=EXPR_TUPLE, .tup={{{arr}, {len(node.elems)}}} }};')

        elif isinstance(node, TApply):
            fn_name  = self.emit_expr(node.fn)
            arg_names = [self.emit_expr(a) for a in node.args]
            arr = self._pointer_array('LkExpr', arg_names)
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_APPLY, '
                       f'.app={{&{fn_name}, {arr}, {len(node.args)}}} }};')

        elif isinstance(node, TBinOp):
            l = self.emit_expr(node.left)
            r = self.emit_expr(node.right)
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_BINOP, '
                       f'.binop={{{_c_str(node.op)}, &{l}, &{r}}} }};')

        elif isinstance(node, TUnaryOp):
            operand = self.emit_expr(node.operand)
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_UNARY, '
                       f'.unary={{{_c_str(node.op)}, &{operand}}} }};')

        elif isinstance(node, TLetExpr):
            val  = self.emit_expr(node.value)
            body = self.emit_expr(node.body)
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_LET, '
                       f'.let={{{_c_str(node.name)}, &{val}, &{body}}} }};')

        elif isinstance(node, TIfExpr):
            cond  = self.emit_expr(node.cond)
            then_ = self.emit_expr(node.then_)
            else_ = self.emit_expr(node.else_)
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_IF, '
                       f'.if_={{&{cond}, &{then_}, &{else_}}} }};')

        elif isinstance(node, TMatchExpr):
            scrut = self.emit_expr(node.scrutinee)
            arm_names = []
            for pat, body in node.arms:
                pn = self.emit_pat(pat)
                bn = self.emit_expr(body)
                an = self._arr_name()
                self._line(f'static const LkArm {an} = {{ &{pn}, &{bn} }};')
                arm_names.append(an)
            # Arms are an array of LkArm (not pointers to LkArm)
            arr = self._arr_name()
            inner = ', '.join(arm_names)
            self._line(f'static const LkArm {arr}[] = {{ {inner} }};')
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_MATCH, '
                       f'.match={{&{scrut}, {arr}, {len(node.arms)}}} }};')

        elif isinstance(node, TLambda):
            # Desugar multi-param to nested single-param lambdas.
            # Emit in dependency order: innermost wrapping first, outermost last.
            # e.g. λx.λy.body → emit λy.body first, then λx.(λy.body) as `name`.
            params = node.params
            curr_body = self.emit_expr(node.body)
            for param_name, _ in reversed(params[1:]):
                inner = self._expr_name()
                self._line(f'static const LkExpr {inner} = '
                           f'{{ .kind=EXPR_LAMBDA, '
                           f'.lam={{{_c_str(param_name)}, &{curr_body}}} }};')
                curr_body = inner
            self._line(f'static const LkExpr {name} = '
                       f'{{ .kind=EXPR_LAMBDA, '
                       f'.lam={{{_c_str(params[0][0])}, &{curr_body}}} }};')

        else:
            raise NotImplementedError(f'emit_expr: {type(node).__name__}')

        return name

    # -- Literal initialiser --

    def _lit_init(self, value: object) -> str:
        """Return a C brace-initialiser for LkLit."""
        if value is None:
            return 'LIT_UNIT'
        if isinstance(value, bool):
            return f'LIT_BOOL, .b={int(value)}'
        if isinstance(value, int):
            return f'LIT_INT, .i={value}'
        if isinstance(value, float):
            return f'LIT_FLOAT, .f=0x{_f32_bits(value):08X}u'
        if isinstance(value, str):
            return f'LIT_STR, .s={_c_str(value)}'
        raise TypeError(f'_lit_init: unknown literal type {type(value).__name__}')

    # -- Patterns --

    def emit_pat(self, node: TPat) -> str:
        nid = id(node)
        if nid in self._seen:
            return self._seen[nid]
        name = self._emit_pat_inner(node)
        self._seen[nid] = name
        return name

    def _emit_pat_inner(self, node: TPat) -> str:
        name = self._pat_name()

        if isinstance(node, TPWild):
            self._line(f'static const LkPat {name} = {{ .kind=PAT_WILD }};')

        elif isinstance(node, TPVar):
            self._line(f'static const LkPat {name} = '
                       f'{{ .kind=PAT_VAR, .var={_c_str(node.name)} }};')

        elif isinstance(node, TPLit):
            lit_c = self._lit_init(node.value)
            self._line(f'static const LkPat {name} = '
                       f'{{ .kind=PAT_LIT, .lit={{{lit_c}}} }};')

        elif isinstance(node, TPCon):
            if not node.args:
                self._line(f'static const LkPat {name} = '
                           f'{{ .kind=PAT_CON, '
                           f'.con={{{_c_str(node.name)}, NULL, 0}} }};')
            else:
                child_names = [self.emit_pat(p) for p in node.args]
                arr = self._pointer_array('LkPat', child_names)
                self._line(f'static const LkPat {name} = '
                           f'{{ .kind=PAT_CON, '
                           f'.con={{{_c_str(node.name)}, {arr}, {len(node.args)}}} }};')

        elif isinstance(node, TPTuple):
            child_names = [self.emit_pat(p) for p in node.elems]
            arr = self._pointer_array('LkPat', child_names)
            self._line(f'static const LkPat {name} = '
                       f'{{ .kind=PAT_TUPLE, '
                       f'.tup={{{arr}, {len(node.elems)}}} }};')

        else:
            raise NotImplementedError(f'emit_pat: {type(node).__name__}')

        return name

    # -- Declarations --

    def emit_decls(self, decls: list) -> list[str]:
        """Emit all declarations and return list of C LkDecl variable names."""
        names = []
        for d in decls:
            names.extend(self._emit_decl(d))
        return names

    def _emit_decl(self, decl) -> list[str]:  # noqa: C901
        """Emit one declaration; may produce multiple DECL_FN names (for impls)."""
        if isinstance(decl, TFnDecl):
            return [self._emit_fn_decl(decl.name, decl.params, decl.body)]

        if isinstance(decl, TLetDecl):
            val_name = self.emit_expr(decl.value)
            dname = self._decl_name()
            self._line(f'static const LkDecl {dname} = '
                       f'{{ .kind=DECL_LET, .name={_c_str(decl.name)}, '
                       f'.let_val=&{val_name} }};')
            return [dname]

        if isinstance(decl, TTypeDecl):
            if not decl.variants:
                return []   # type alias — no runtime representation
            var_arr = self._arr_name()
            var_inits = []
            for v in decl.variants:
                var_inits.append(f'{{ {_c_str(v.name)}, {len(v.payload)} }}')
            self._line(f'static const LkVariant {var_arr}[] = '
                       f'{{ {", ".join(var_inits)} }};')
            dname = self._decl_name()
            self._line(f'static const LkDecl {dname} = '
                       f'{{ .kind=DECL_TYPE, .name={_c_str(decl.name)}, '
                       f'.type_={{{var_arr}, {len(decl.variants)}}} }};')
            return [dname]

        if isinstance(decl, TImplDecl):
            method_inits = []
            for m in decl.methods:
                # Desugar multi-param methods to nested lambdas; first param
                # stays as the DECL_FN param, rest wrapped as lambdas.
                params = m.params
                if not params:
                    continue
                body_with_remaining = self._wrap_lambdas(params[1:], m.body)
                body_name = self.emit_expr(body_with_remaining)
                method_inits.append(
                    f'{{ {_c_str(m.name)}, {_c_str(params[0][0])}, &{body_name} }}'
                )
            if not method_inits:
                return []
            meth_arr = self._arr_name()
            self._line(f'static const LkMethod {meth_arr}[] = '
                       f'{{ {", ".join(method_inits)} }};')
            dname = self._decl_name()
            self._line(f'static const LkDecl {dname} = '
                       f'{{ .kind=DECL_IMPL, .name={_c_str(decl.for_type)}, '
                       f'.impl={{{_c_str(decl.trait_name)}, {meth_arr}, '
                       f'{len(method_inits)}}} }};')
            return [dname]

        raise NotImplementedError(f'_emit_decl: {type(decl).__name__}')

    def _emit_fn_decl(self, fn_name: str, params: tuple, body) -> str:
        """Emit a DECL_FN; desugar extra params into nested lambdas."""
        if not params:
            raise ValueError(f'function {fn_name!r} has no parameters')
        body_expr = self._wrap_lambdas(params[1:], body)
        body_name = self.emit_expr(body_expr)
        param0 = params[0][0]
        dname  = self._decl_name()
        self._line(f'static const LkDecl {dname} = '
                   f'{{ .kind=DECL_FN, .name={_c_str(fn_name)}, '
                   f'.fn={{{_c_str(param0)}, &{body_name}}} }};')
        return dname

    # -- Lambda desugaring --

    def _wrap_lambdas(self, params: tuple, body: TExpr) -> TExpr:
        """Wrap body in nested TLambda for each remaining param (innermost first)."""
        from ty import T_UNIT
        result = body
        for pname, pty in reversed(params):
            result = TLambda(params=((pname, pty),), body=result, typ=T_UNIT)
            self._synthetic.append(result)   # prevent CPython from recycling id()
        return result

    # -- Top-level output --------------------------------------------------

    def render(self, source_path: str, decl_names: list[str]) -> str:
        """Build the final C source string."""
        header = [
            f'/* Auto-generated from {os.path.basename(source_path)} */',
            '/* Do not edit — regenerate with emit_c_ast.py */',
            '',
            '#include "cek.h"',
            '#include <stddef.h>',
            '',
        ]
        prog_entries = ', '.join(f'&{n}' for n in decl_names)
        self._lines.append('')
        self._lines.append(
            f'static const LkDecl* _prog_decls[] = {{ {prog_entries} }};')
        self._lines.append('')
        self._lines.append(
            f'LkProg lk_program = '
            f'{{ .decls = _prog_decls, .n_decls = {len(decl_names)} }};')
        return '\n'.join(header) + '\n'.join(self._lines)


# -- Import resolution --

def _load_imports(prog, src_dir: str) -> list:
    """
    Resolve imports depth-first.  Return a flat list of TDecl from all
    imported modules, in dependency order, followed by the main program's
    decls.  Each module is loaded at most once.
    """
    loaded: set[str] = set()
    result: list     = []

    def load(p, directory):
        for imp in p.imports:
            mod = imp.module
            if mod in loaded:
                continue
            loaded.add(mod)
            candidates = [
                pathlib.Path(directory) / f'{mod.lower()}.lark',
                pathlib.Path(directory) / f'{mod}.lark',
            ]
            path = next((c for c in candidates if c.exists()), None)
            if path is None:
                continue
            abs_path     = str(path.resolve())
            imp_prog     = _parser.parse_file(abs_path)
            imp_tp       = _infer.typecheck(imp_prog, source_file=abs_path)
            imp_dir      = str(path.parent)
            load(imp_prog, imp_dir)
            result.extend(imp_tp.decls)

    load(prog, src_dir)
    return result


# -- Main --

def emit(source_path: str, out_path: str | None = None) -> str:
    """
    Parse, type-check, and emit `source_path` as a C AST file.
    Returns the generated C source as a string.
    If `out_path` is given, also writes to that file.
    """
    prog    = _parser.parse_file(source_path)
    tprog   = _infer.typecheck(prog, source_file=source_path)
    src_dir = os.path.dirname(os.path.abspath(source_path))

    import_decls = _load_imports(prog, src_dir)
    all_decls    = list(import_decls) + list(tprog.decls)

    em = Emitter()
    decl_names = em.emit_decls(all_decls)
    c_src = em.render(source_path, decl_names)

    if out_path:
        with open(out_path, 'w') as f:
            f.write(c_src)

    return c_src


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('usage: emit_c_ast.py <file.lark> [output.c]', file=sys.stderr)
        sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    src_out = emit(src, out)
    if not out:
        print(src_out)
