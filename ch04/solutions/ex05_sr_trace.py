"""
Chapter 4, Exercise 5 — solution code.

Trace the shift-reduce parse of (1 + 2) * 3 under G0, in the format of
Table (tab:sr-trace). At the step where the stack is `$ ( E` and the input
begins with `)`, what action does the parser take? Why doesn't `)` trigger a
reduce there, and which production eventually consumes it?

How to run:   python3 ex05_sr_trace.py
Expected:     the full trace, then
              "shift-reduce trace OK; the `)` step is a SHIFT (consumed by F -> ( E ))"

This is a *validator*: the trace below is replayed against G0's productions. Each
`shift` must consume the next input terminal; each `reduce X -> rhs` must find
exactly `rhs` on top of the stack (so the trace cannot cheat); `accept` requires
the stack to be `$ E` with only `$` left. If the hand-trace were wrong, the
replay would raise.

ANSWER to the specific question. At `$ ( E` with `)` next, the parser SHIFTS the
`)`. It does not reduce because no complete handle sits on top of the stack:
`E` is not by itself the right-hand side of any reduce that applies here, and the
only production involving `)` is F -> ( E ), whose handle `( E )` is not yet
complete — the `)` has not been stacked. The parser must shift `)` first; the
production that then consumes it is F -> ( E ).
"""

# G0 productions (left-recursive; bottom-up handles that fine)
PRODUCTIONS = {
    ("E", "+", "T"),
    ("T",),            # E -> T
    ("T", "*", "F"),
    ("F",),            # T -> F
    ("num",),          # F -> num
    ("(", "E", ")"),
}

# (action, expected production lhs->rhs for reduces) for (1 + 2) * 3
# 'num' stands for each numeric literal 1, 2, 3.
INPUT = ["(", "num", "+", "num", ")", "*", "num"]

TRACE = [
    ("shift",  None),
    ("shift",  None),
    ("reduce", ("F", ("num",))),
    ("reduce", ("T", ("F",))),
    ("reduce", ("E", ("T",))),
    ("shift",  None),                 # +
    ("shift",  None),                 # num (2)
    ("reduce", ("F", ("num",))),
    ("reduce", ("T", ("F",))),
    ("reduce", ("E", ("E", "+", "T"))),
    ("shift",  None),                 # )  <-- the step in question
    ("reduce", ("F", ("(", "E", ")"))),
    ("reduce", ("T", ("F",))),
    ("shift",  None),                 # *
    ("shift",  None),                 # num (3)
    ("reduce", ("F", ("num",))),
    ("reduce", ("T", ("T", "*", "F"))),
    ("reduce", ("E", ("T",))),
    ("accept", None),
]


def run_trace():
    stack = ["$"]
    remaining = INPUT + ["$"]
    rows = []
    paren_shift_step = None

    for action, arg in TRACE:
        rows.append((list(stack), list(remaining), action, arg))

        if action == "shift":
            assert len(remaining) > 1, "nothing left to shift"
            # record the asked-about configuration before applying
            if stack == ["$", "(", "E"] and remaining[0] == ")":
                paren_shift_step = len(rows)
            stack.append(remaining.pop(0))

        elif action == "reduce":
            lhs, rhs = arg
            assert (lhs == "E" and rhs in {("E", "+", "T"), ("T",)}) or \
                   (lhs == "T" and rhs in {("T", "*", "F"), ("F",)}) or \
                   (lhs == "F" and rhs in {("num",), ("(", "E", ")")}), \
                   f"{lhs} -> {' '.join(rhs)} is not a G0 production"
            assert rhs in PRODUCTIONS, f"{rhs} not a production RHS"
            n = len(rhs)
            popped = tuple(stack[-n:])
            assert popped == rhs, f"reduce {lhs}->{' '.join(rhs)} but top of " \
                                  f"stack is {popped}"
            del stack[-n:]
            stack.append(lhs)

        elif action == "accept":
            assert stack == ["$", "E"] and remaining == ["$"], \
                f"accept with stack={stack} remaining={remaining}"

    return rows, paren_shift_step


def fmt(symbols):
    return " ".join(symbols)


if __name__ == "__main__":
    rows, paren_step = run_trace()

    print(f"  {'Stack':<22}{'Remaining input':<20}Action")
    for stack, remaining, action, arg in rows:
        act = action if action != "reduce" else f"reduce {arg[0]} -> {fmt(arg[1])}"
        marker = "   <-- the ')' step" if (stack == ["$", "(", "E"]
                                           and remaining and remaining[0] == ")"
                                           and action == "shift") else ""
        print(f"  {fmt(stack):<22}{fmt(remaining):<20}{act}{marker}")

    assert paren_step is not None, "the `$ ( E` / `)` configuration never occurred"
    # the action taken there was a shift (recorded only on shift)
    print("\nshift-reduce trace OK; the `)` step is a SHIFT "
          "(consumed by F -> ( E ))")
