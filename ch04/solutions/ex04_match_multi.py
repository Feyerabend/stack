"""
Chapter 4, Exercise 4 — solution code.

Lark's match expression currently requires one pattern per arm. Extend
_parse_match_expr to allow multiple patterns separated by | (e.g. | A | B => e).
(a) revised EBNF for an arm; (b) the code change to _parse_match_expr;
(c) the MatchExpr change in tree.py.

How to run:   python3 ex04_match_multi.py
Expected:     "multi-pattern match OK"

(a) REVISED EBNF. An arm now has one-or-more |-separated patterns before =>:

      arm ::= "|" pattern ( "|" pattern )* "=>" expr

    The leading "|" opens the arm; each extra "|" separates another pattern.
    Because the arm-opener and the pattern-separator are the same token, the
    loop structure below reads naturally.

(b) CODE CHANGE to _parse_match_expr (the override below). The single
    `pat = self._parse_pattern()` becomes a one-or-more loop:

        while self._match(TK.PIPE):           # opens an arm
            pats = [self._parse_pattern()]
            while self._match(TK.PIPE):       # extra patterns for this arm
                pats.append(self._parse_pattern())
            self._expect(TK.FAT_ARROW)
            expr = self._parse_expr()
            arms.append((tuple(pats), expr))

(c) MatchExpr CHANGE in tree.py — each arm stores a TUPLE of patterns:

        arms: tuple[tuple[tuple[Pat, ...], Expr], ...]
        #                 ^^^^^^^^^^^^^^^ was just Pat

    The interpreter then tries each pattern in the tuple and runs the arm on the
    first that matches (an OR-pattern). This script reuses the existing MatchExpr
    node (a plain dataclass) to hold the new arm shape, so it runs unmodified.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH04 = os.path.dirname(_HERE)
_LANG = os.path.dirname(_CH04)
sys.path.insert(0, os.path.join(_LANG, "lark", "02", "src"))

from lexer import Lexer            # noqa: E402
from parser import Parser         # noqa: E402
from tree import MatchExpr, PCon  # noqa: E402


class MultiPatternParser(Parser):
    """Parser whose match arms accept one-or-more |-separated patterns."""

    def _parse_match_expr(self):
        from lexer import TK
        self._expect(TK.MATCH)
        scrutinee = self._parse_expr()
        self._expect(TK.WITH)
        arms = []
        while self._match(TK.PIPE):
            pats = [self._parse_pattern()]
            while self._match(TK.PIPE):
                pats.append(self._parse_pattern())
            self._expect(TK.FAT_ARROW)
            expr = self._parse_expr()
            arms.append((tuple(pats), expr))
        self._expect(TK.END)
        return MatchExpr(scrutinee, tuple(arms))


def parse_match(src):
    tokens = Lexer(src).tokenize()
    return MultiPatternParser(tokens)._parse_expr()


if __name__ == "__main__":
    expr = parse_match("match x with | A | B => 1 | C => 2 end")
    assert isinstance(expr, MatchExpr)
    assert len(expr.arms) == 2

    pats0, _body0 = expr.arms[0]
    pats1, _body1 = expr.arms[1]

    # arm 0 groups two patterns A | B; arm 1 has a single pattern C
    assert len(pats0) == 2 and len(pats1) == 1
    assert all(isinstance(p, PCon) for p in pats0 + pats1)
    assert [p.name for p in pats0] == ["A", "B"]
    assert [p.name for p in pats1] == ["C"]

    # a plain single-pattern arm still parses (now as a 1-tuple)
    expr2 = parse_match("match x with | A => 0 end")
    assert len(expr2.arms) == 1 and len(expr2.arms[0][0]) == 1
    assert expr2.arms[0][0][0].name == "A"

    print("multi-pattern match OK")
