"""
Lark parser — hand-written recursive descent.

Consumes a token list from the lexer and produces a Program AST node.
The grammar is LL(1) throughout; no backtracking is needed.

Operator precedence (low → high):
    or  →  and  →  ==  !=  <  <=  >  >=  →  +  -  →  *  /  →  unary  →  apply

Entry point:
    Parser(tokens, filename).parse() -> Program
    ParseError                         raised on syntax error, carries location
"""

from __future__ import annotations
import sys
import os
import pprint
sys.path.insert(0, os.path.dirname(__file__))

from lexer import Token, TK
from tree import (
    # Types
    Type, TName, TApply, TFn, TUnit, TTuple,
    # Patterns
    Pat, PWild, PVar, PLit, PCon, PTuple,
    # Expressions
    Expr, Lit, Var, Con, TupleExpr, Apply, BinOp, UnaryOp,
    LetExpr, IfExpr, MatchExpr, Lambda,
    # Supporting
    Param, Bound, Variant, TraitMethod, ImplMethod,
    # Declarations
    Decl, FnDecl, LetDecl, TypeDecl, TraitDecl, ImplDecl,
    # Top-level
    ImportDecl, Program,
)


# ── Error ─────────────────────────────────────────────────────────────────────

class ParseError(Exception):
    def __init__(self, msg: str, filename: str, line: int, col: int) -> None:
        self.msg      = msg
        self.filename = filename
        self.line     = line
        self.col      = col
        super().__init__(f"{filename}:{line}:{col}: {msg}")


# ── Parser ────────────────────────────────────────────────────────────────────

class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<stdin>") -> None:
        self.tokens   = tokens
        self.filename = filename
        self.pos      = 0

    # ── Core helpers ──────────────────────────────────────────────

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.kind != TK.EOF:
            self.pos += 1
        return tok

    def _at(self, *kinds: TK) -> bool:
        return self._peek().kind in kinds

    def _expect(self, kind: TK) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            raise self._error(
                f"expected {kind.name}, got {tok.kind.name} ({tok.text!r})")
        return self._advance()

    def _match(self, *kinds: TK) -> Token | None:
        if self._at(*kinds):
            return self._advance()
        return None

    def _error(self, msg: str, tok: Token | None = None) -> ParseError:
        t = tok or self._peek()
        return ParseError(msg, self.filename, t.line, t.col)

    # ── Program ───────────────────────────────────────────────────

    def parse(self) -> Program:
        module  = self._parse_module_decl()
        imports = self._parse_imports()
        decls   = self._parse_decls()
        self._expect(TK.EOF)
        return Program(module, tuple(imports), tuple(decls))

    def _parse_module_decl(self) -> str:
        self._expect(TK.MODULE)
        return self._expect(TK.UPPER).text

    # ── Imports ───────────────────────────────────────────────────

    def _parse_imports(self) -> list[ImportDecl]:
        imports = []
        while self._at(TK.IMPORT):
            imports.append(self._parse_import())
        return imports

    def _parse_import(self) -> ImportDecl:
        self._expect(TK.IMPORT)
        module   = self._expect(TK.UPPER).text
        exposing = None
        if self._match(TK.EXPOSING):
            self._expect(TK.LPAREN)
            names = [self._parse_export_name()]
            while self._match(TK.COMMA):
                names.append(self._parse_export_name())
            self._expect(TK.RPAREN)
            exposing = tuple(names)
        return ImportDecl(module, exposing)

    def _parse_export_name(self) -> str:
        tok = self._peek()
        if tok.kind in (TK.NAME, TK.UPPER):
            return self._advance().text
        raise self._error("expected name or type name in exposing list")

    # ── Top-level declarations ────────────────────────────────────

    def _parse_decls(self) -> list[Decl]:
        decls = []
        while not self._at(TK.EOF):
            decls.append(self._parse_top_decl())
        return decls

    def _parse_top_decl(self) -> Decl:
        exported = bool(self._match(TK.EXPORT))
        tok = self._peek()
        if tok.kind == TK.FN:    return self._parse_fn_decl(exported)
        if tok.kind == TK.LET:   return self._parse_let_decl(exported)
        if tok.kind == TK.TYPE:  return self._parse_type_decl(exported)
        if tok.kind == TK.TRAIT: return self._parse_trait_decl(exported)
        if tok.kind == TK.IMPL:  return self._parse_impl_decl()
        raise self._error(f"expected declaration (fn/let/type/trait/impl), "
                          f"got {tok.kind.name} ({tok.text!r})")

    # ── fn declaration ────────────────────────────────────────────

    def _parse_fn_decl(self, exported: bool) -> FnDecl:
        self._expect(TK.FN)
        name   = self._expect(TK.NAME).text
        bounds = self._parse_bounds() if self._at(TK.LBRACKET) else ()
        self._expect(TK.LPAREN)
        params = self._parse_params()
        self._expect(TK.RPAREN)
        ret = None
        if self._match(TK.COLON):
            ret = self._parse_type()
        self._expect(TK.ASSIGN)
        body = self._parse_expr()
        return FnDecl(name, bounds, params, ret, body, exported)

    # ── let declaration ───────────────────────────────────────────

    def _parse_let_decl(self, exported: bool) -> LetDecl:
        self._expect(TK.LET)
        name = self._expect(TK.NAME).text
        ann  = None
        if self._match(TK.COLON):
            ann = self._parse_type()
        self._expect(TK.ASSIGN)
        value = self._parse_expr()
        return LetDecl(name, ann, value, exported)

    # ── type declaration ──────────────────────────────────────────

    def _parse_type_decl(self, exported: bool) -> TypeDecl:
        self._expect(TK.TYPE)
        name   = self._expect(TK.UPPER).text
        params: list[str] = []
        while self._at(TK.NAME):
            params.append(self._advance().text)
        self._expect(TK.ASSIGN)
        if self._at(TK.PIPE):
            body: Type | tuple[Variant, ...] = self._parse_variants()
        else:
            body = self._parse_type()
        return TypeDecl(name, tuple(params), body, exported)

    def _parse_variants(self) -> tuple[Variant, ...]:
        variants: list[Variant] = []
        while self._match(TK.PIPE):
            vname   = self._expect(TK.UPPER).text
            payload = self._parse_variant_payload()
            variants.append(Variant(vname, payload))
        return tuple(variants)

    def _parse_variant_payload(self) -> Type | None:
        """Parse [ 'of' type {',' type} ] — comma-separated fields become TTuple."""
        if not self._match(TK.OF):
            return None
        types = [self._parse_type()]
        while self._match(TK.COMMA):
            types.append(self._parse_type())
        return types[0] if len(types) == 1 else TTuple(tuple(types))

    # ── trait declaration ─────────────────────────────────────────

    def _parse_trait_decl(self, exported: bool) -> TraitDecl:
        self._expect(TK.TRAIT)
        name: str = self._expect(TK.UPPER).text
        params: list[str] = []
        while self._at(TK.NAME):
            params.append(self._advance().text)
        self._expect(TK.ASSIGN)
        self._expect(TK.LBRACE)
        methods: list[TraitMethod] = []
        while not self._at(TK.RBRACE, TK.EOF):
            methods.append(self._parse_trait_method())
        self._expect(TK.RBRACE)
        return TraitDecl(name, tuple(params), tuple(methods), exported)

    def _parse_trait_method(self) -> TraitMethod:
        self._expect(TK.FN)
        name = self._expect(TK.NAME).text
        self._expect(TK.COLON)
        typ  = self._parse_type()
        return TraitMethod(name, typ)

    # ── impl declaration ──────────────────────────────────────────

    def _parse_impl_decl(self) -> ImplDecl:
        self._expect(TK.IMPL)
        trait_name = self._expect(TK.UPPER).text
        # Collect extra type args before 'for': e.g. impl Convert Int for Float
        trait_args: list[Type] = []
        while not self._at(TK.FOR, TK.EOF):
            trait_args.append(self._parse_atom_type())
        self._expect(TK.FOR)
        for_type = self._parse_atom_type()
        self._expect(TK.ASSIGN)
        self._expect(TK.LBRACE)
        methods: list[ImplMethod] = []
        while not self._at(TK.RBRACE, TK.EOF):
            methods.append(self._parse_impl_method())
        self._expect(TK.RBRACE)
        return ImplDecl(trait_name, tuple(trait_args), for_type, tuple(methods))

    def _parse_impl_method(self) -> ImplMethod:
        self._expect(TK.FN)
        name = self._expect(TK.NAME).text
        self._expect(TK.LPAREN)
        params = self._parse_params()
        self._expect(TK.RPAREN)
        self._expect(TK.ASSIGN)
        body = self._parse_expr()
        return ImplMethod(name, params, body)

    # ── Parameters and bounds ─────────────────────────────────────

    def _parse_params(self) -> tuple[Param, ...]:
        if self._at(TK.RPAREN):
            return ()
        params = [self._parse_param()]
        while self._match(TK.COMMA):
            params.append(self._parse_param())
        return tuple(params)

    def _parse_param(self) -> Param:
        if self._at(TK.WILDCARD):
            self._advance()
            return Param("_", None)   # ignored parameter
        name = self._expect(TK.NAME).text
        ann  = None
        if self._match(TK.COLON):
            ann = self._parse_type()
        return Param(name, ann)

    def _parse_bounds(self) -> tuple[Bound, ...]:
        self._expect(TK.LBRACKET)
        bounds = [self._parse_bound()]
        while self._match(TK.COMMA):
            bounds.append(self._parse_bound())
        self._expect(TK.RBRACKET)
        return tuple(bounds)

    def _parse_bound(self) -> Bound:
        trait = self._expect(TK.UPPER).text
        var   = self._expect(TK.NAME).text
        return Bound(trait, var)

    # ── Expressions ───────────────────────────────────────────────

    def _parse_expr(self) -> Expr:
        if self._at(TK.LET):   return self._parse_let_expr()
        if self._at(TK.IF):    return self._parse_if_expr()
        if self._at(TK.MATCH): return self._parse_match_expr()
        if self._at(TK.FN):    return self._parse_lambda()
        return self._parse_or()

    def _parse_let_expr(self) -> LetExpr:
        self._expect(TK.LET)
        name = self._expect(TK.NAME).text
        ann  = None
        if self._match(TK.COLON):
            ann = self._parse_type()
        self._expect(TK.ASSIGN)
        value = self._parse_expr()
        self._expect(TK.IN)
        body  = self._parse_expr()
        return LetExpr(name, ann, value, body)

    def _parse_if_expr(self) -> IfExpr:
        self._expect(TK.IF)
        cond  = self._parse_expr()
        self._expect(TK.THEN)
        then_ = self._parse_expr()
        self._expect(TK.ELSE)
        else_ = self._parse_expr()
        return IfExpr(cond, then_, else_)

    def _parse_match_expr(self) -> MatchExpr:
        self._expect(TK.MATCH)
        scrutinee = self._parse_expr()
        self._expect(TK.WITH)
        arms: list[tuple[Pat, Expr]] = []
        while self._match(TK.PIPE):
            pat  = self._parse_pattern()
            self._expect(TK.FAT_ARROW)
            expr = self._parse_expr()
            arms.append((pat, expr))
        self._expect(TK.END)
        return MatchExpr(scrutinee, tuple(arms))

    def _parse_lambda(self) -> Lambda:
        self._expect(TK.FN)
        self._expect(TK.LPAREN)
        params = self._parse_params()
        self._expect(TK.RPAREN)
        self._expect(TK.FAT_ARROW)
        body = self._parse_expr()
        return Lambda(params, body)

    # Precedence levels: or < and < compare < add < mul < unary < apply

    def _parse_or(self) -> Expr:
        left = self._parse_and()
        while self._at(TK.OR):
            op = self._advance().text
            left = BinOp(op, left, self._parse_and())
        return left

    def _parse_and(self) -> Expr:
        left = self._parse_compare()
        while self._at(TK.AND):
            op = self._advance().text
            left = BinOp(op, left, self._parse_compare())
        return left

    def _parse_compare(self) -> Expr:
        left = self._parse_add()
        while self._at(TK.EQEQ, TK.NEQ, TK.LT, TK.LE, TK.GT, TK.GE):
            op = self._advance().text
            left = BinOp(op, left, self._parse_add())
        return left

    def _parse_add(self) -> Expr:
        left = self._parse_mul()
        while self._at(TK.PLUS, TK.MINUS):
            op = self._advance().text
            left = BinOp(op, left, self._parse_mul())
        return left

    def _parse_mul(self) -> Expr:
        left = self._parse_unary()
        while self._at(TK.STAR, TK.SLASH):
            op = self._advance().text
            left = BinOp(op, left, self._parse_unary())
        return left

    def _parse_unary(self) -> Expr:
        if self._at(TK.MINUS, TK.NOT):
            op = self._advance().text
            return UnaryOp(op, self._parse_unary())
        return self._parse_apply()

    def _parse_apply(self) -> Expr:
        expr = self._parse_atom()
        while self._at(TK.LPAREN):
            self._advance()
            args = self._parse_args()
            self._expect(TK.RPAREN)
            expr = Apply(expr, tuple(args))
        return expr

    def _parse_args(self) -> list[Expr]:
        if self._at(TK.RPAREN):
            return []
        args = [self._parse_expr()]
        while self._match(TK.COMMA):
            args.append(self._parse_expr())
        return args

    def _parse_atom(self) -> Expr:
        tok = self._peek()

        if tok.kind == TK.INT:      self._advance(); return Lit(tok.value)
        if tok.kind == TK.FLOAT:    self._advance(); return Lit(tok.value)
        if tok.kind == TK.STRING:   self._advance(); return Lit(tok.value)
        if tok.kind == TK.TRUE:     self._advance(); return Lit(True)
        if tok.kind == TK.FALSE:    self._advance(); return Lit(False)
        if tok.kind == TK.UNIT:     self._advance(); return Lit(None)
        if tok.kind == TK.NAME:     self._advance(); return Var(tok.text)
        if tok.kind == TK.UPPER:    self._advance(); return Con(tok.text)

        if tok.kind == TK.LPAREN:
            self._advance()
            first = self._parse_expr()
            if self._at(TK.COMMA):
                elems = [first]
                while self._match(TK.COMMA):
                    elems.append(self._parse_expr())
                self._expect(TK.RPAREN)
                return TupleExpr(tuple(elems))
            self._expect(TK.RPAREN)
            return first

        raise self._error(
            f"unexpected token {tok.kind.name} ({tok.text!r}) in expression")

    # ── Types ─────────────────────────────────────────────────────

    def _parse_type(self) -> Type:
        return self._parse_fn_type()

    def _parse_fn_type(self) -> Type:
        left = self._parse_atom_type()
        if self._match(TK.ARROW):
            right = self._parse_fn_type()   # right-associative recursion
            return TFn(left, right)
        return left

    def _parse_atom_type(self) -> Type:
        tok = self._peek()

        if tok.kind == TK.UNIT:
            self._advance(); return TUnit()

        if tok.kind == TK.UPPER:
            self._advance()
            name = tok.text
            if self._match(TK.LPAREN):
                args = [self._parse_type()]
                while self._match(TK.COMMA):
                    args.append(self._parse_type())
                self._expect(TK.RPAREN)
                return TApply(name, tuple(args))
            return TName(name)

        if tok.kind == TK.NAME:
            self._advance(); return TName(tok.text)

        if tok.kind == TK.LPAREN:
            self._advance()
            first = self._parse_type()
            if self._at(TK.COMMA):
                elems = [first]
                while self._match(TK.COMMA):
                    elems.append(self._parse_type())
                self._expect(TK.RPAREN)
                return TTuple(tuple(elems))
            self._expect(TK.RPAREN)
            return first

        raise self._error(
            f"unexpected token {tok.kind.name} ({tok.text!r}) in type")

    # ── Patterns ──────────────────────────────────────────────────

    def _parse_pattern(self) -> Pat:
        tok = self._peek()

        if tok.kind == TK.WILDCARD: self._advance(); return PWild()
        if tok.kind == TK.NAME:     self._advance(); return PVar(tok.text)
        if tok.kind == TK.INT:      self._advance(); return PLit(tok.value)
        if tok.kind == TK.FLOAT:    self._advance(); return PLit(tok.value)
        if tok.kind == TK.STRING:   self._advance(); return PLit(tok.value)
        if tok.kind == TK.TRUE:     self._advance(); return PLit(True)
        if tok.kind == TK.FALSE:    self._advance(); return PLit(False)
        if tok.kind == TK.UNIT:     self._advance(); return PLit(None)

        if tok.kind == TK.MINUS:
            self._advance()
            num = self._peek()
            if num.kind == TK.INT:   self._advance(); return PLit(-num.value)
            if num.kind == TK.FLOAT: self._advance(); return PLit(-num.value)
            raise self._error("expected number after '-' in pattern")

        if tok.kind == TK.UPPER:
            self._advance()
            name = tok.text
            args: tuple[Pat, ...] = ()
            if self._match(TK.LPAREN):
                pats = [self._parse_pattern()]
                while self._match(TK.COMMA):
                    pats.append(self._parse_pattern())
                self._expect(TK.RPAREN)
                args = tuple(pats)
            return PCon(name, args)

        if tok.kind == TK.LPAREN:
            self._advance()
            first = self._parse_pattern()
            elems = [first]
            while self._match(TK.COMMA):
                elems.append(self._parse_pattern())
            self._expect(TK.RPAREN)
            return elems[0] if len(elems) == 1 else PTuple(tuple(elems))

        raise self._error(
            f"unexpected token {tok.kind.name} ({tok.text!r}) in pattern")


# ── Convenience function ──────────────────────────────────────────────────────

def parse_file(path: str) -> Program:
    from lexer import Lexer
    with open(path) as f:
        source = f.read()
    tokens = Lexer(source, path).tokenize()
    return Parser(tokens, path).parse()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python parser.py <file.lark>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        program = parse_file(path)
        pprint.pprint(program, width=80)
        print(f"\n{len(program.decls)} declaration(s)")
    except (ParseError, Exception) as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)
