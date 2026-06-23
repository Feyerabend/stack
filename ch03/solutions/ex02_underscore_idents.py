"""
Chapter 3, Exercise 2 — solution code.

Lark forbids identifiers that begin with an underscore. Suppose instead they
were allowed. Which method in Section 3.x (sec:build) would change, which case in
the main dispatch would become ambiguous, and how would you resolve the
ambiguity?

How to run:   python3 ex02_underscore_idents.py
Expected:     "underscore identifiers OK; bare _ still WILDCARD"

ANSWERS.
  - Method that changes: `_read_wildcard`. Today it consumes a lone '_' and
    raises if an identifier character follows. To allow `_foo`, it must instead
    fall through to identifier scanning when an identifier character follows.
    (`_read_name` is reused unchanged — it already accepts '_' in the body and
    the keyword table is all-lowercase, so `_foo`/`_if` are plain NAMEs.)
  - Ambiguous dispatch case: the `ch == "_"` arm of `_next`. With leading
    underscores allowed, a '_' could begin EITHER the wildcard token OR an
    identifier.
  - Resolution: one character of lookahead. If the character after '_' is an
    identifier character (alnum or '_'), scan an identifier; otherwise emit the
    bare WILDCARD. This is the same maximal-munch tie-break the lexer uses
    everywhere (e.g. '<' vs '<=').
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH03 = os.path.dirname(_HERE)
_LANG = os.path.dirname(_CH03)
sys.path.insert(0, os.path.join(_LANG, "lark", "01", "src"))

from lexer import Lexer, TK, LexError  # noqa: E402


class UnderscoreLexer(Lexer):
    """Lexer that allows identifiers to begin with '_' (bare '_' stays WILDCARD)."""

    def _read_wildcard(self, line, col):
        # Resolve the '_' ambiguity by lookahead.
        if self._peek(1).isalnum() or self._peek(1) == "_":
            return self._read_name(line, col)        # '_foo' is an identifier
        self._advance()                              # bare '_'
        return self._tok(TK.WILDCARD, "_", None, line, col)


def pairs(lexer_cls, src):
    return [(t.kind.name, t.value)
            for t in lexer_cls(src).tokenize() if t.kind != TK.EOF]


if __name__ == "__main__":
    got = pairs(UnderscoreLexer, "_foo bar _ _x1 _if")
    assert got == [
        ("NAME", "_foo"),
        ("NAME", "bar"),
        ("WILDCARD", None),
        ("NAME", "_x1"),
        ("NAME", "_if"),       # all-lowercase keywords don't match '_if'
    ], got

    # The stock lexer still rejects a leading underscore.
    try:
        pairs(Lexer, "_foo")
        rejected = False
    except LexError:
        rejected = True
    assert rejected, "stock lexer should reject '_foo'"

    print("underscore identifiers OK; bare _ still WILDCARD")
