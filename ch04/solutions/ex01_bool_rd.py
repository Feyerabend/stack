"""
Chapter 4, Exercise 1 — solution code.

Write a recursive descent parser for Boolean expressions built from variables
(a, b, ...), not, and, or (standard precedence: not highest, or lowest). State
the grammar in EBNF first, verify it is LL(1) by computing FIRST for each
nonterminal, then implement one function per nonterminal.

How to run:   python3 ex01_bool_rd.py
Expected:     "boolean recursive-descent OK"

EBNF (precedence baked into the rule hierarchy, lowest binding outermost):

    expr   ::= term   ( "or"  term   )*
    term   ::= factor ( "and" factor )*
    factor ::= "not" factor | atom
    atom   ::= VAR | "(" expr ")"

FIRST sets (VAR = any variable name):

    FIRST(atom)   = { VAR, "(" }
    FIRST(factor) = { "not", VAR, "(" }
    FIRST(term)   = FIRST(factor) = { "not", VAR, "(" }
    FIRST(expr)   = FIRST(factor) = { "not", VAR, "(" }

Why it is LL(1): every choice is decided by one lookahead token.
  - factor: "not" selects the unary rule, anything in FIRST(atom) selects atom;
    the two sets are disjoint.
  - the ( ... )* loops in expr/term continue iff the lookahead is exactly "or"
    / "and" respectively, and stop otherwise — no overlap.
So no nonterminal has two productions whose FIRST sets share a token.
"""

import re

KEYWORDS = {"not", "and", "or"}


def tokenize(s):
    toks = re.findall(r"[A-Za-z]+|[()]", s)
    return toks


class BoolParser:
    """One method per nonterminal; builds a nested-tuple AST."""

    def __init__(self, tokens):
        self.toks = tokens
        self.pos = 0

    def _peek(self):
        return self.toks[self.pos] if self.pos < len(self.toks) else None

    def _advance(self):
        tok = self.toks[self.pos]
        self.pos += 1
        return tok

    def parse(self):
        node = self.expr()
        if self.pos != len(self.toks):
            raise SyntaxError(f"trailing input at {self.toks[self.pos:]}")
        return node

    def expr(self):                       # expr ::= term ("or" term)*
        node = self.term()
        while self._peek() == "or":
            self._advance()
            node = ("or", node, self.term())
        return node

    def term(self):                       # term ::= factor ("and" factor)*
        node = self.factor()
        while self._peek() == "and":
            self._advance()
            node = ("and", node, self.factor())
        return node

    def factor(self):                     # factor ::= "not" factor | atom
        if self._peek() == "not":
            self._advance()
            return ("not", self.factor())
        return self.atom()

    def atom(self):                       # atom ::= VAR | "(" expr ")"
        tok = self._peek()
        if tok == "(":
            self._advance()
            node = self.expr()
            if self._peek() != ")":
                raise SyntaxError("expected ')'")
            self._advance()
            return node
        if tok is None or tok in KEYWORDS or tok in "()":
            raise SyntaxError(f"expected a variable, got {tok!r}")
        return ("var", self._advance())


def evaluate(node, env):
    tag = node[0]
    if tag == "var":  return env[node[1]]
    if tag == "not":  return not evaluate(node[1], env)
    if tag == "and":  return evaluate(node[1], env) and evaluate(node[2], env)
    if tag == "or":   return evaluate(node[1], env) or evaluate(node[2], env)
    raise ValueError(node)


def parse(s):
    return BoolParser(tokenize(s)).parse()


if __name__ == "__main__":
    env = {"a": True, "b": True, "c": False}

    # precedence: not > and > or, so this is ((a and (not b)) or c)
    ast = parse("a and not b or c")
    assert ast == ("or", ("and", ("var", "a"), ("not", ("var", "b"))),
                   ("var", "c")), ast
    assert evaluate(ast, env) is False        # (T and F) or F = F

    # parentheses override precedence: a and (not b or c) = T and (F or F) = F
    assert evaluate(parse("a and (not b or c)"), env) is False
    # not binds tighter than and: not a and b = (not a) and b = F and T = F
    assert evaluate(parse("not a and b"), env) is False
    # or is lowest: a or b and c = a or (b and c) = T or (T and F) = T
    assert evaluate(parse("a or b and c"), env) is True
    # double negation
    assert evaluate(parse("not not a"), env) is True

    # malformed input is rejected
    for bad in ["a and", "and a", "a b", "(a or b", "not"]:
        try:
            parse(bad); ok = False
        except SyntaxError:
            ok = True
        assert ok, f"should reject {bad!r}"

    print("boolean recursive-descent OK")
