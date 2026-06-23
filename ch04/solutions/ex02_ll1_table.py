"""
Chapter 4, Exercise 2 — solution code.

Compute the LL(1) parse table for the right-recursive variant of G0:
    E -> T (+ T)*,  T -> F (* F)*,  F -> num | ( E )
First rewrite without EBNF shorthands, compute FIRST and FOLLOW, fill the table,
and compare with the chapter's Table (tab:parse-table). Are there differences?

How to run:   python3 ex02_ll1_table.py
Expected:     a printed table, then
              "LL(1) table OK; matches tab:parse-table (chapter omits the $ column)"

DE-EBNF'd GRAMMAR (right recursion replaces each ( ... )* loop):
    E  -> T E'
    E' -> + T E' | eps
    T  -> F T'
    T' -> * F T' | eps
    F  -> num | ( E )

This is exactly the grammar the chapter builds in its left-recursion-elimination
step, so the table should match tab:parse-table. The script computes FIRST/FOLLOW
from scratch and checks every cell.
"""

EPS = "eps"
END = "$"

# productions: nonterminal -> list of right-hand sides (each a tuple of symbols)
GRAMMAR = {
    "E":  [("T", "E'")],
    "E'": [("+", "T", "E'"), (EPS,)],
    "T":  [("F", "T'")],
    "T'": [("*", "F", "T'"), (EPS,)],
    "F":  [("num",), ("(", "E", ")")],
}
START = "E"
NONTERMS = set(GRAMMAR)
TERMS = {"num", "+", "*", "(", ")"}


def first_of_symbol(sym, first):
    if sym in TERMS:
        return {sym}
    if sym == EPS:
        return {EPS}
    return set(first[sym])


def first_of_seq(seq, first):
    """FIRST of a sequence of symbols."""
    result = set()
    for sym in seq:
        f = first_of_symbol(sym, first)
        result |= (f - {EPS})
        if EPS not in f:
            return result
    result.add(EPS)
    return result


def compute_first():
    first = {nt: set() for nt in NONTERMS}
    changed = True
    while changed:
        changed = False
        for nt, rhss in GRAMMAR.items():
            for rhs in rhss:
                add = first_of_seq(rhs, first)
                if not add <= first[nt]:
                    first[nt] |= add
                    changed = True
    return first


def compute_follow(first):
    follow = {nt: set() for nt in NONTERMS}
    follow[START].add(END)
    changed = True
    while changed:
        changed = False
        for nt, rhss in GRAMMAR.items():
            for rhs in rhss:
                for i, sym in enumerate(rhs):
                    if sym not in NONTERMS:
                        continue
                    rest = rhs[i + 1:]
                    f_rest = first_of_seq(rest, first) if rest else {EPS}
                    add = f_rest - {EPS}
                    if EPS in f_rest:
                        add |= follow[nt]
                    if not add <= follow[sym]:
                        follow[sym] |= add
                        changed = True
    return follow


def build_table(first, follow):
    table = {nt: {} for nt in NONTERMS}
    conflicts = []
    for nt, rhss in GRAMMAR.items():
        for rhs in rhss:
            f = first_of_seq(rhs, first)
            targets = f - {EPS}
            if EPS in f:
                targets |= follow[nt]
            for t in targets:
                if t in table[nt]:
                    conflicts.append((nt, t))
                table[nt][t] = rhs
    return table, conflicts


def show(rhs):
    return "eps" if rhs == (EPS,) else " ".join(rhs)


if __name__ == "__main__":
    first = compute_first()
    follow = compute_follow(first)
    table, conflicts = build_table(first, follow)

    cols = ["num", "(", ")", "+", "*", END]
    print("LL(1) parse table:")
    print(f"  {'':4}" + "".join(f"{c:>9}" for c in cols))
    for nt in ["E", "E'", "T", "T'", "F"]:
        row = "".join(f"{show(table[nt][c]) if c in table[nt] else '':>9}"
                      for c in cols)
        print(f"  {nt:4}{row}")

    # LL(1) iff no cell has two entries
    assert not conflicts, f"grammar is not LL(1): conflicts {conflicts}"

    # Spot-check FIRST / FOLLOW
    assert first["E"] == {"num", "("}
    assert first["E'"] == {"+", EPS}
    assert first["T'"] == {"*", EPS}
    assert follow["E"] == {END, ")"}
    assert follow["T"] == {"+", ")", END}
    assert follow["F"] == {"*", "+", ")", END}

    # Match the chapter's tab:parse-table (which omits the $ column).
    expected = {
        ("E", "num"): ("T", "E'"),   ("E", "("): ("T", "E'"),
        ("E'", ")"): (EPS,),         ("E'", "+"): ("+", "T", "E'"),
        ("T", "num"): ("F", "T'"),   ("T", "("): ("F", "T'"),
        ("T'", ")"): (EPS,),         ("T'", "+"): (EPS,), ("T'", "*"): ("*", "F", "T'"),
        ("F", "num"): ("num",),      ("F", "("): ("(", "E", ")"),
    }
    for (nt, t), rhs in expected.items():
        assert table[nt].get(t) == rhs, f"cell M[{nt},{t}] mismatch"

    # The ONLY difference: the $ column the chapter leaves out — both nullable
    # nonterminals reduce to eps there, because $ in FOLLOW(E'), FOLLOW(T').
    assert table["E'"][END] == (EPS,)
    assert table["T'"][END] == (EPS,)

    print("LL(1) table OK; matches tab:parse-table "
          "(chapter omits the $ column)")
