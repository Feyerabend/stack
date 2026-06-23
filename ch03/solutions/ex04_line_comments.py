"""
Chapter 3, Exercise 4 — solution code.

Add single-line comments (-- to end of line) to _skip. Unlike block comments,
these are a regular pattern. Explain why, and confirm that your addition needs no
depth counter.

How to run:   python3 ex04_line_comments.py
Expected:     "line comments OK; no depth counter needed"

WHY REGULAR. A single-line comment is exactly the pattern  --[^\\n]*\\n  : the
delimiter '--', then any run of non-newline characters, then a newline. That is a
plain regular expression, recognised by a tiny DFA (states: "in code", "saw one
dash", "in comment", back to "in code" on newline). There is nothing to balance:
'--' inside the comment body is just more body text, so comments do not nest.

NO DEPTH COUNTER. Block comments need `depth` because (* ... *) nest, and
counting nesting requires unbounded memory (Exercise 5). A line comment ends
unconditionally at the first newline regardless of how many '--' it contains, so
the scanner needs no counter — the override below has no `depth` variable, only a
loop to the next newline.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH03 = os.path.dirname(_HERE)
_LANG = os.path.dirname(_CH03)
sys.path.insert(0, os.path.join(_LANG, "lark", "01", "src"))

from lexer import Lexer, TK  # noqa: E402


class LineCommentLexer(Lexer):
    """Lexer whose _skip also drops `--` single-line comments."""

    def _skip(self):
        while self.pos < len(self.source):
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "(" and self._peek(1) == "*":
                self._skip_comment()                 # nested block comment
            elif ch == "-" and self._peek(1) == "-":
                # single-line comment: run to (not past) the newline; the loop
                # then skips the newline as ordinary whitespace. No depth counter.
                while self.pos < len(self.source) and self._peek() != "\n":
                    self._advance()
            else:
                break


def pairs(lexer_cls, src):
    return [(t.kind.name, t.value)
            for t in lexer_cls(src).tokenize() if t.kind != TK.EOF]


if __name__ == "__main__":
    # The comment and everything after '--' on its line disappears.
    src = "1 + 2 -- this is a comment\n+ 3"
    assert pairs(LineCommentLexer, src) == [
        ("INT", 1), ("PLUS", "+"), ("INT", 2), ("PLUS", "+"), ("INT", 3)
    ]

    # Extra '--' inside the body change nothing: it still ends at the newline,
    # which is what "no depth counter" buys us.
    src2 = "1 -- a -- b -- c\n+ 2"
    assert pairs(LineCommentLexer, src2) == [
        ("INT", 1), ("PLUS", "+"), ("INT", 2)
    ]

    # '->' and a lone '-' are untouched (only '--' starts a comment).
    src3 = "a -> b - c"
    assert pairs(LineCommentLexer, src3) == [
        ("NAME", "a"), ("ARROW", "->"), ("NAME", "b"),
        ("MINUS", "-"), ("NAME", "c")
    ]

    # The src2 case above is the proof that no counting happens: three '--'
    # on one line behave exactly like one, because the scanner just runs to the
    # newline. A nesting counter would be dead code here.

    print("line comments OK; no depth counter needed")
