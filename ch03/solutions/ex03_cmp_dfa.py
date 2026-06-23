"""
Chapter 3, Exercise 3 — solution code.

Draw a DFA that accepts the comparison operators <, <=, >, >=, ==, != and no
other strings. How many accepting states does it need, and why can it not be
merged into fewer?

How to run:   python3 ex03_cmp_dfa.py
Expected:     "recognizer OK (6 accepting); minimized OK (2 accepting)"

ANSWER (the count has two honest readings):

  As a pure RECOGNIZER of the six-string set, the natural DFA has 6 accepting
  states (one per operator), but it MINIMIZES to 2: every two-character operator
  ends in an indistinguishable accept-sink, so <=, >=, ==, != merge; and the
  bare-< and bare-> states have identical futures (accept now, accept on '=',
  reject otherwise) so they merge too. Both DFAs below accept exactly the six
  strings.

  As a LEXER, the accepting states cannot be merged: each must emit a DISTINCT
  token (LT, LE, GT, GE, EQEQ, NEQ). Once a state carries an output, two states
  with different outputs are distinguishable by definition, so 6 accepting states
  are required. The chapter's lexer is a transducer, not a recognizer, which is
  why it keeps them apart. (The repo's dfa.py `_build_cmp_dfa` is a third,
  lexer-flavoured variant that also accepts a bare '<' followed by a non-'='
  via maximal munch; that is a different language, on purpose.)

Diagram of the natural recognizer:

        '<'        '='
   S ───────► LT ───────► LE        (LT, LE accepting)
   │ '>'       '='
   ├───────► GT ───────► GE         (GT, GE accepting)
   │ '='       '='
   ├───────► EQ1 ──────► EQEQ       (EQ1 NON-accepting; EQEQ accepting)
   │ '!'       '='
   └───────► BANG ─────► NEQ        (BANG NON-accepting; NEQ accepting)

EQ1 and BANG are non-accepting because a lone '=' is assignment and a lone '!'
is not an operator at all.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_CH03 = os.path.dirname(_HERE)
sys.path.insert(0, _CH03)

from dfa import DFA  # noqa: E402

OPERATORS = ["<", "<=", ">", ">=", "==", "!="]
NON_OPERATORS = ["", "=", "!", "<<", "<>", "><", "<=>", "===", "=!", "!!", " "]


def build_recognizer():
    """Natural DFA: 6 accepting states, one per operator. Accepts only the six."""
    return DFA(
        states={"S", "LT", "GT", "EQ1", "BANG", "LE", "GE", "EQEQ", "NEQ"},
        alphabet={"<", ">", "=", "!"},
        delta={
            ("S", "<"): "LT", ("S", ">"): "GT",
            ("S", "="): "EQ1", ("S", "!"): "BANG",
            ("LT", "="): "LE", ("GT", "="): "GE",
            ("EQ1", "="): "EQEQ", ("BANG", "="): "NEQ",
        },
        start="S",
        accepting={"LT", "GT", "LE", "GE", "EQEQ", "NEQ"},
    )


def build_minimized():
    """Minimal recognizer of the same language: only 2 accepting states.

    A = after '<' or '>'   (accepting; on '=' -> sink, else dead)
    B = after '=' or '!'   (non-accepting; on '=' -> sink, else dead)
    F = accept-sink for the four two-character operators
    """
    return DFA(
        states={"S", "A", "B", "F"},
        alphabet={"<", ">", "=", "!"},
        delta={
            ("S", "<"): "A", ("S", ">"): "A",
            ("S", "="): "B", ("S", "!"): "B",
            ("A", "="): "F", ("B", "="): "F",
        },
        start="S",
        accepting={"A", "F"},
    )


def check(dfa):
    for op in OPERATORS:
        assert dfa.accepts(op), f"should accept {op!r}"
    for s in NON_OPERATORS:
        assert not dfa.accepts(s), f"should reject {s!r}"


if __name__ == "__main__":
    rec = build_recognizer()
    mini = build_minimized()
    check(rec)
    check(mini)
    assert len(rec.accepting) == 6
    assert len(mini.accepting) == 2
    print(f"recognizer OK ({len(rec.accepting)} accepting); "
          f"minimized OK ({len(mini.accepting)} accepting)")
