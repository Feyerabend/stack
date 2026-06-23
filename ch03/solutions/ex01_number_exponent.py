"""
Chapter 3, Exercise 1 — solution code.

Extend _read_number to accept an exponent suffix, so that 1.5e10 and 3e8 scan as
floats. State precisely the new lookahead your change requires, and give an input
on which a naive version would misclassify the dot.

How to run:   python3 ex01_number_exponent.py
Expected:     "exponent scanning OK; naive dot misclassification demonstrated"

THE NEW LOOKAHEAD. To commit to an exponent you must look PAST an optional sign
to a digit before consuming the 'e'. From the 'e' you peek:
    offset 1 : a digit  -> exponent (e.g. 3e8)
    offset 1 : + or -, AND offset 2 : a digit  -> exponent (e.g. 3e+8)
otherwise the 'e' is NOT part of the number. So the change needs two characters
of lookahead beyond the 'e' (the sign and the digit after it). This mirrors the
dot rule the real lexer already uses: it consumes '.' only when _peek(1) is a
digit, never on one character alone.

THE DOT MISCLASSIFICATION. A naive reader that checks only `_peek() == "."`
(one-character lookahead) treats the dot in `1.foo` as a decimal point: it scans
FLOAT 1.0 then NAME foo. The correct two-character rule leaves the int intact
(INT 1) and lets the '.' be reported as an unexpected character, as Lark intends
(there is no '.' token). Both behaviours are shown below.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH03 = os.path.dirname(_HERE)
_LANG = os.path.dirname(_CH03)
sys.path.insert(0, os.path.join(_LANG, "lark", "01", "src"))

from lexer import Lexer, TK, LexError  # noqa: E402


class ExpLexer(Lexer):
    """Lexer whose _read_number also accepts an exponent suffix."""

    def _read_number(self, line, col):
        start = self.pos
        while self._peek().isdigit():
            self._advance()

        is_float = False
        # fractional part: '.' only if a digit follows (the existing 2-char rule)
        if self._peek() == "." and self._peek(1).isdigit():
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()

        # exponent: e/E, optional sign, then digits — committed only on lookahead
        if self._peek() in ("e", "E"):
            nxt = self._peek(1)
            if nxt.isdigit() or (nxt in "+-" and self._peek(2).isdigit()):
                is_float = True
                self._advance()                 # e / E
                if self._peek() in "+-":
                    self._advance()             # sign
                while self._peek().isdigit():
                    self._advance()

        text = self.source[start:self.pos]
        if is_float:
            return self._tok(TK.FLOAT, text, float(text), line, col)
        return self._tok(TK.INT, text, int(text), line, col)


class NaiveDotLexer(Lexer):
    """A deliberately naive reader: one-character lookahead on the dot."""

    def _read_number(self, line, col):
        start = self.pos
        while self._peek().isdigit():
            self._advance()
        is_float = False
        if self._peek() == ".":                 # BUG: no digit-after check
            is_float = True
            self._advance()
            while self._peek().isdigit():
                self._advance()
        text = self.source[start:self.pos]
        if is_float:
            return self._tok(TK.FLOAT, text, float(text), line, col)
        return self._tok(TK.INT, text, int(text), line, col)


def pairs(lexer_cls, src):
    return [(t.kind.name, t.value)
            for t in lexer_cls(src).tokenize() if t.kind != TK.EOF]


if __name__ == "__main__":
    # Exponent forms scan as floats.
    assert pairs(ExpLexer, "1.5e10") == [("FLOAT", 1.5e10)]
    assert pairs(ExpLexer, "3e8")    == [("FLOAT", 3e8)]
    assert pairs(ExpLexer, "3e+8")   == [("FLOAT", 3e8)]
    assert pairs(ExpLexer, "1.5e-3") == [("FLOAT", 1.5e-3)]
    # No exponent => still an int / plain float.
    assert pairs(ExpLexer, "42")     == [("INT", 42)]
    assert pairs(ExpLexer, "3.14")   == [("FLOAT", 3.14)]

    # The dot: naive misclassifies it as a decimal point.
    assert pairs(NaiveDotLexer, "1.foo") == [("FLOAT", 1.0), ("NAME", "foo")]
    # The correct rule keeps INT 1 and rejects the stray '.' (no '.' token).
    try:
        pairs(ExpLexer, "1.foo")
        raised = False
    except LexError:
        raised = True
    assert raised, "correct lexer should reject the '.' in 1.foo"

    print("exponent scanning OK; naive dot misclassification demonstrated")
