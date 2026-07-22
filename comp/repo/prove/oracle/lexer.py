"""
Lark lexer — hand-written, single-pass.

Produces a flat list of Token objects from source text.
Handles: keywords, identifiers, int/float/string literals,
         all operators and punctuation, nested block comments (* ... *).

Entry points:
    Lexer(source, filename).tokenize()  -> list[Token]
    LexError                            raised on bad input, carries location
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto


# -- Token kinds --

class TK(Enum):
    # Literals
    INT       = auto()
    FLOAT     = auto()
    STRING    = auto()
    TRUE      = auto()
    FALSE     = auto()
    UNIT      = auto()    # ()

    # Identifiers
    NAME      = auto()    # starts lowercase  — variables, fn names
    UPPER     = auto()    # starts uppercase  — types, constructors, modules

    # Keywords (all lowercase — resolved from NAME during scanning)
    AND       = auto()
    ELSE      = auto()
    END       = auto()
    EXPORT    = auto()
    EXPOSING  = auto()
    FN        = auto()
    FOR       = auto()
    IF        = auto()
    IMPL      = auto()
    IMPORT    = auto()
    IN        = auto()
    LET       = auto()
    MATCH     = auto()
    MODULE    = auto()
    NOT       = auto()
    OF        = auto()
    OR        = auto()
    THEN      = auto()
    TRAIT     = auto()
    TYPE      = auto()
    WITH      = auto()

    # Arithmetic operators
    PLUS      = auto()    # +
    MINUS     = auto()    # -
    STAR      = auto()    # *
    SLASH     = auto()    # /

    # Comparison operators
    EQEQ      = auto()    # ==
    NEQ       = auto()    # !=
    LT        = auto()    # <
    LE        = auto()    # <=
    GT        = auto()    # >
    GE        = auto()    # >=

    # Punctuation
    ARROW     = auto()    # ->
    FAT_ARROW = auto()    # =>
    ASSIGN    = auto()    # =
    PIPE      = auto()    # |
    COLON     = auto()    # :
    COMMA     = auto()    # ,
    LPAREN    = auto()    # (
    RPAREN    = auto()    # )
    LBRACKET  = auto()    # [
    RBRACKET  = auto()    # ]
    LBRACE    = auto()    # {
    RBRACE    = auto()    # }
    WILDCARD  = auto()    # _   (standalone only — names may not start with _)

    EOF       = auto()


# Maps lowercase keyword text -> TK variant
_KEYWORDS: dict[str, TK] = {
    "and":      TK.AND,
    "else":     TK.ELSE,
    "end":      TK.END,
    "export":   TK.EXPORT,
    "exposing": TK.EXPOSING,
    "false":    TK.FALSE,
    "fn":       TK.FN,
    "for":      TK.FOR,
    "if":       TK.IF,
    "impl":     TK.IMPL,
    "import":   TK.IMPORT,
    "in":       TK.IN,
    "let":      TK.LET,
    "match":    TK.MATCH,
    "module":   TK.MODULE,
    "not":      TK.NOT,
    "of":       TK.OF,
    "or":       TK.OR,
    "then":     TK.THEN,
    "trait":    TK.TRAIT,
    "true":     TK.TRUE,
    "type":     TK.TYPE,
    "with":     TK.WITH,
}


# -- Token --

@dataclass(frozen=True)
class Token:
    kind:  TK
    text:  str      # raw source text for this token
    value: object   # processed value: int, float, str, bool, or None
    line:  int
    col:   int

    def __repr__(self) -> str:
        return f"Token({self.kind.name:<12} {self.value!r:<20} {self.line}:{self.col})"


# -- Error --

class LexError(Exception):
    def __init__(self, msg: str, filename: str, line: int, col: int) -> None:
        self.msg      = msg
        self.filename = filename
        self.line     = line
        self.col      = col
        super().__init__(f"{filename}:{line}:{col}: {msg}")


# -- Lexer --

class Lexer:
    def __init__(self, source: str, filename: str = "<stdin>") -> None:
        self.source   = source
        self.filename = filename
        self.pos      = 0
        self.line     = 1
        self.col      = 1

    # -- Public --

    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while True:
            tok = self._next()
            tokens.append(tok)
            if tok.kind == TK.EOF:
                break
        return tokens

    # -- Helpers --

    def _peek(self, offset: int = 0) -> str:
        i = self.pos + offset
        return self.source[i] if i < len(self.source) else ""

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            # A column is a BYTE offset, not a codepoint offset.  The port
            # (lex.lark) reads its source as a Lark String, and a Lark String
            # is UTF-8 bytes; it therefore counts bytes, and so must we, or the
            # two lexers disagree about every column after a non-ASCII
            # character.  On the ASCII the corpus is mostly made of, this is
            # the `+= 1` it replaces.
            self.col += len(ch.encode("utf-8"))
        return ch

    def _error(self, msg: str, line: int | None = None,
               col: int | None = None) -> LexError:
        return LexError(msg, self.filename,
                        line if line is not None else self.line,
                        col  if col  is not None else self.col)

    def _tok(self, kind: TK, text: str, value: object,
             line: int, col: int) -> Token:
        return Token(kind, text, value, line, col)

    # -- Skip whitespace and nested block comments (* ... *) --

    def _skip(self) -> None:
        while self.pos < len(self.source):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "(" and self._peek(1) == "*":
                self._skip_comment()
            else:
                break

    def _skip_comment(self) -> None:
        line, col = self.line, self.col
        self._advance()   # (
        self._advance()   # *
        depth = 1
        while self.pos < len(self.source):
            if self._peek() == "(" and self._peek(1) == "*":
                self._advance(); self._advance()
                depth += 1
            elif self._peek() == "*" and self._peek(1) == ")":
                self._advance(); self._advance()
                depth -= 1
                if depth == 0:
                    return
            else:
                self._advance()
        raise self._error("unterminated comment", line, col)

    # -- Main dispatch --

    def _next(self) -> Token:
        self._skip()

        if self.pos >= len(self.source):
            return Token(TK.EOF, "", None, self.line, self.col)

        line, col = self.line, self.col
        ch = self._peek()

        if ch.isdigit():          return self._read_number(line, col)
        if ch == '"':             return self._read_string(line, col)
        if ch.islower():          return self._read_name(line, col)
        if ch.isupper():          return self._read_upper(line, col)
        if ch == "_":             return self._read_wildcard(line, col)
        return                           self._read_symbol(line, col)

    # -- Numbers --

    def _read_number(self, line: int, col: int) -> Token:
        start = self.pos
        while self._peek().isdigit():
            self._advance()
        if self._peek() == "." and self._peek(1).isdigit():
            self._advance()                       # consume .
            while self._peek().isdigit():
                self._advance()
            text = self.source[start:self.pos]
            return self._tok(TK.FLOAT, text, float(text), line, col)
        text = self.source[start:self.pos]
        return self._tok(TK.INT, text, int(text), line, col)

    # -- Strings --

    _ESCAPES: dict[str, str] = {
        '"': '"', "\\": "\\",
        "n": "\n", "t": "\t", "r": "\r",
    }

    def _read_string(self, line: int, col: int) -> Token:
        start = self.pos
        self._advance()              # opening "
        chars: list[str] = []
        while True:
            if self.pos >= len(self.source):
                raise self._error("unterminated string", line, col)
            ch = self._advance()
            if ch == '"':
                break
            if ch == "\\":
                esc = self._advance()
                chars.append(self._ESCAPES.get(esc, esc))
            else:
                chars.append(ch)
        text  = self.source[start:self.pos]
        value = "".join(chars)
        return self._tok(TK.STRING, text, value, line, col)

    # -- Names and keywords --

    def _read_name(self, line: int, col: int) -> Token:
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text  = self.source[start:self.pos]
        kind  = _KEYWORDS.get(text, TK.NAME)
        value: object = (True  if kind == TK.TRUE  else
                         False if kind == TK.FALSE else
                         text)
        return self._tok(kind, text, value, line, col)

    def _read_upper(self, line: int, col: int) -> Token:
        start = self.pos
        while self._peek().isalnum() or self._peek() == "_":
            self._advance()
        text = self.source[start:self.pos]
        return self._tok(TK.UPPER, text, text, line, col)

    # -- Wildcard --

    def _read_wildcard(self, line: int, col: int) -> Token:
        self._advance()              # consume _
        if self._peek().isalnum() or self._peek() == "_":
            raise self._error("identifiers may not start with '_'", line, col)
        return self._tok(TK.WILDCARD, "_", None, line, col)

    # -- Symbols and operators --

    def _read_symbol(self, line: int, col: int) -> Token:
        ch = self._advance()

        # Single-character unambiguous tokens
        _single: dict[str, TK] = {
            "+": TK.PLUS, "*": TK.STAR, "/": TK.SLASH,
            "|": TK.PIPE, ":": TK.COLON, ",": TK.COMMA,
            "[": TK.LBRACKET, "]": TK.RBRACKET,
            "{": TK.LBRACE,   "}": TK.RBRACE,
            ")": TK.RPAREN,
        }
        if ch in _single:
            return self._tok(_single[ch], ch, ch, line, col)

        # ( or ()
        if ch == "(":
            if self._peek() == ")":
                self._advance()
                return self._tok(TK.UNIT, "()", None, line, col)
            return self._tok(TK.LPAREN, "(", "(", line, col)

        # - or ->
        if ch == "-":
            if self._peek() == ">":
                self._advance()
                return self._tok(TK.ARROW, "->", "->", line, col)
            return self._tok(TK.MINUS, "-", "-", line, col)

        # = or == or =>
        if ch == "=":
            if self._peek() == "=":
                self._advance()
                return self._tok(TK.EQEQ, "==", "==", line, col)
            if self._peek() == ">":
                self._advance()
                return self._tok(TK.FAT_ARROW, "=>", "=>", line, col)
            return self._tok(TK.ASSIGN, "=", "=", line, col)

        # ! must be !=
        if ch == "!":
            if self._peek() == "=":
                self._advance()
                return self._tok(TK.NEQ, "!=", "!=", line, col)
            raise self._error("expected '=' after '!'", line, col)

        # < or <=
        if ch == "<":
            if self._peek() == "=":
                self._advance()
                return self._tok(TK.LE, "<=", "<=", line, col)
            return self._tok(TK.LT, "<", "<", line, col)

        # > or >=
        if ch == ">":
            if self._peek() == "=":
                self._advance()
                return self._tok(TK.GE, ">=", ">=", line, col)
            return self._tok(TK.GT, ">", ">", line, col)

        raise self._error(f"unexpected character {ch!r}", line, col)


# -- CLI — run lexer on a file and print tokens --

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python lexer.py <file.lark>")
        sys.exit(1)

    path = sys.argv[1]
    try:
        with open(path) as f:
            source = f.read()
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        tokens = Lexer(source, path).tokenize()
        for tok in tokens:
            if tok.kind != TK.EOF:
                print(tok)
        print(f"\n{len(tokens) - 1} tokens (excluding EOF)")
    except LexError as e:
        print(f"lex error: {e}", file=sys.stderr)
        sys.exit(1)
