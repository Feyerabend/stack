"""
Chapter 4, Exercise 3 — solution code.

The grammar S -> a S b | eps generates { a^n b^n | n >= 0 }. Show it is LL(1)
(FIRST, FOLLOW, parse table, one entry per cell), and implement a recursive
descent parser for it. (The pumping-lemma argument for why no finite automaton
accepts { a^n b^n } is in solutions.md.)

How to run:   python3 ex03_anbn.py
Expected:     "a^n b^n recursive-descent OK; table is LL(1)"

FIRST(S)  = { a, eps }
FOLLOW(S) = { b, $ }      (S appears before b in 'a S b'; and S is the start)

Parse table (one entry per cell -> LL(1)):
        a            b        $
    S   S -> a S b   S -> eps S -> eps

Cell M[S,a] uses the a-production (a in FIRST); M[S,b] and M[S,$] use eps
(b, $ in FOLLOW and eps in FIRST(S)). No cell has two entries, so the grammar
is LL(1).
"""

EPS = "eps"
END = "$"

# S -> a S b | eps
FIRST_S = {"a", EPS}
FOLLOW_S = {"b", END}

PARSE_TABLE = {
    ("S", "a"): ("a", "S", "b"),
    ("S", "b"): (EPS,),
    ("S", END): (EPS,),
}


class AnBnParser:
    """Recursive descent for S -> a S b | eps, driven by one lookahead."""

    def __init__(self, s):
        self.s = s
        self.pos = 0

    def _peek(self):
        return self.s[self.pos] if self.pos < len(self.s) else END

    def parse(self):
        self._S()
        if self._peek() != END:
            raise SyntaxError(f"trailing input at index {self.pos}")

    def _S(self):
        # lookahead 'a' -> a S b ; lookahead in FOLLOW(S) -> eps
        if self._peek() == "a":
            self.pos += 1            # match 'a'
            self._S()
            if self._peek() != "b":
                raise SyntaxError(f"expected 'b' at index {self.pos}")
            self.pos += 1            # match 'b'
        elif self._peek() in ("b", END):
            return                   # eps production
        else:
            raise SyntaxError(f"unexpected {self._peek()!r} at index {self.pos}")


def accepts(s):
    try:
        AnBnParser(s).parse()
        return True
    except SyntaxError:
        return False


if __name__ == "__main__":
    # Every cell has exactly one entry -> LL(1).
    assert len(PARSE_TABLE) == 3
    assert PARSE_TABLE[("S", "a")] == ("a", "S", "b")
    assert PARSE_TABLE[("S", "b")] == (EPS,)
    assert PARSE_TABLE[("S", END)] == (EPS,)

    accept = ["", "ab", "aabb", "aaabbb", "a" * 50 + "b" * 50]
    reject = ["a", "b", "ba", "aab", "abb", "aba", "abab", "ab" + "b"]
    for s in accept:
        assert accepts(s), f"should accept {s!r}"
    for s in reject:
        assert not accepts(s), f"should reject {s!r}"

    print("a^n b^n recursive-descent OK; table is LL(1)")
