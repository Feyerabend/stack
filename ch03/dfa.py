"""
Formal DFA and the tokenizer model - companion code for Chapter 3.

DFA(states, alphabet, delta, start, accepting)
    .accepts(string)   -> bool
    .run(string)       -> final state, or None if the machine fell off an edge

tokenize_simple(source) is the finite-state tokenizer from Section 3.2,
reproduced verbatim from the book.

The demos at the bottom show:
  1. The identifier DFA from Figure 3.1.
  2. An integer DFA.
  3. A comparison-operator DFA covering <, <=, >, >=, ==, != (Exercise 3.3).
  4. tokenize_simple on a small expression.
"""


# -- Formal DFA

class DFA:
    """
    A deterministic finite automaton.

    states    : set of state names (any hashable)
    alphabet  : set of input symbols (single chars, or categories as strings)
    delta     : dict mapping (state, symbol) -> next_state
    start     : starting state (must be in states)
    accepting : set of accepting states (subset of states)

    When the input character is not in delta for the current state the
    machine moves to the implicit dead state and stays there.  A string
    is accepted if the machine ends in an accepting state after reading
    every character.
    """

    _DEAD = object()   # implicit sink state

    def __init__(self, states, alphabet, delta, start, accepting):
        self.states    = set(states)
        self.alphabet  = set(alphabet)
        self.delta     = delta
        self.start     = start
        self.accepting = set(accepting)

    def step(self, state, symbol):
        """Return the state reached from state on symbol, or _DEAD."""
        return self.delta.get((state, symbol), self._DEAD)

    def run(self, string):
        """
        Simulate on string.  Return the final state, or None if the machine
        fell into the dead state before the string was consumed.
        """
        state = self.start
        for ch in string:
            state = self.step(state, ch)
            if state is self._DEAD:
                return None
        return state

    def accepts(self, string):
        return self.run(string) in self.accepting


# -- Book listing: tokenize_simple (Section 3.2)

def tokenize_simple(source):
    tokens = []
    state  = "START"
    buf    = ""
    i      = 0
    while i < len(source):
        ch = source[i]
        if state == "START":
            if ch.islower():
                state = "IDENT"
                buf = ch
            elif ch.isdigit():
                state = "INT"
                buf = ch
            elif ch.isspace():
                pass
            else:
                raise ValueError(f"unexpected: {ch!r}")
        elif state == "IDENT":
            if ch.isalnum() or ch == "_":
                buf += ch
            else:
                tokens.append(("IDENT", buf))
                buf = ""
                state = "START"
                continue                # reprocess ch from START
        elif state == "INT":
            if ch.isdigit():
                buf += ch
            else:
                tokens.append(("INT", int(buf)))
                buf = ""
                state = "START"
                continue                # reprocess ch from START
        i += 1
    if buf:
        tokens.append((state, buf))
    return tokens


# -- Demos

def _build_ident_dfa():
    """
    DFA for Lark names: [a-z][a-zA-Z0-9_]*
    States: S (start), I (inside ident, accepting), E (error sink).
    The alphabet uses two categories rather than listing every character:
      'lower'  = [a-z]
      'alnum_' = [a-zA-Z0-9_]
    For testing we accept actual characters and classify them here.
    """
    # We encode the alphabet as character classes and override accepts().
    def classify(ch):
        if ch.islower():                    return 'lower'
        if ch.isalnum() or ch == '_':       return 'alnum_'
        return 'other'

    class IdentDFA(DFA):
        def accepts(self, string):
            state = self.start
            for ch in string:
                sym = classify(ch)
                state = self.step(state, sym)
                if state is self._DEAD:
                    return False
            return state in self.accepting

    return IdentDFA(
        states    = {'S', 'I', 'E'},
        alphabet  = {'lower', 'alnum_', 'other'},
        delta     = {
            ('S', 'lower'):  'I',
            ('S', 'alnum_'): 'E',   # digit or _ at start → error
            ('S', 'other'):  'E',
            ('I', 'alnum_'): 'I',   # letters, digits, _ continue
            ('I', 'lower'):  'I',
            ('I', 'other'):  'E',
        },
        start     = 'S',
        accepting = {'I'},
    )


def _build_int_dfa():
    """
    DFA for integer literals: [0-9]+
    States: S, D (accepting).
    """
    def classify(ch):
        return 'digit' if ch.isdigit() else 'other'

    class IntDFA(DFA):
        def accepts(self, string):
            state = self.start
            for ch in string:
                state = self.step(state, classify(ch))
                if state is self._DEAD:
                    return False
            return state in self.accepting

    return IntDFA(
        states    = {'S', 'D'},
        alphabet  = {'digit', 'other'},
        delta     = {
            ('S', 'digit'): 'D',
            ('D', 'digit'): 'D',
        },
        start     = 'S',
        accepting = {'D'},
    )


def _build_cmp_dfa():
    """
    DFA for comparison operators: <  <=  >  >=  ==  !=
    (Exercise 3.3)

    States:
      S       — start
      LT, GT  — saw < or >
      EQ1     — saw first =
      BANG    — saw !
      ACC_*   — accepting states for each complete operator
    """
    return DFA(
        states = {
            'S', 'LT', 'GT', 'EQ1', 'BANG',
            'ACC_LT', 'ACC_GT', 'ACC_LE', 'ACC_GE',
            'ACC_EQ', 'ACC_NEQ',
        },
        alphabet = {'<', '>', '=', '!'},
        delta = {
            ('S',    '<'): 'LT',
            ('S',    '>'): 'GT',
            ('S',    '='): 'EQ1',
            ('S',    '!'): 'BANG',
            ('LT',   '='): 'ACC_LE',
            ('LT',   '<'): 'ACC_LT',   # any non-= ends the < token
            ('LT',   '>'): 'ACC_LT',
            ('LT',   '!'): 'ACC_LT',
            ('GT',   '='): 'ACC_GE',
            ('GT',   '<'): 'ACC_GT',
            ('GT',   '>'): 'ACC_GT',
            ('GT',   '!'): 'ACC_GT',
            ('EQ1',  '='): 'ACC_EQ',
            ('BANG', '='): 'ACC_NEQ',
        },
        start     = 'S',
        accepting = {
            'LT',     # < followed by end-of-input
            'GT',     # >
            'ACC_LT', 'ACC_GT', 'ACC_LE', 'ACC_GE', 'ACC_EQ', 'ACC_NEQ',
        },
    )


if __name__ == "__main__":
    # -- Identifier DFA
    ident = _build_ident_dfa()
    print("Identifier DFA:")
    for s in ["foo", "x1", "_bad", "123", "a_b_c", ""]:
        print(f"  {s!r:10} -> {ident.accepts(s)}")

    # -- Integer DFA
    print("\nInteger DFA:")
    int_dfa = _build_int_dfa()
    for s in ["0", "42", "007", "", "3.14", "x"]:
        print(f"  {s!r:10} -> {int_dfa.accepts(s)}")

    # -- Comparison-operator DFA (Exercise 3.3)
    print("\nComparison DFA:")
    cmp = _build_cmp_dfa()
    for s in ["<", "<=", ">", ">=", "==", "!=", "=", "!", "<="]:
        print(f"  {s!r:6} -> {cmp.accepts(s)}")

    # -- tokenize_simple
    print("\ntokenize_simple:")
    src = "foo 42 bar123 99"
    toks = tokenize_simple(src)
    for tok in toks:
        print(f"  {tok}")
