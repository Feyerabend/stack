"""
Chapter 10, Exercise 4 — solution code.

In the miniature Prolog, grandparent(john, W) succeeds with W = ann. (a) draw the
search tree; (b) add a second grandchild and show how depth-first search orders
the solutions; (c) where would a cut go to commit to the first grandparent found,
and which choice points would it discard?

How to run:   python3 ex04_prolog.py
Expected:     "W = ann; with a 2nd grandchild DFS gives [ann, dave]; "
              "cut commits to [ann]"

Uses the chapter's companion interpreter, ch10/06_prolog/sprolog.py.

(a) SEARCH TREE for grandparent(john, W) with
        parent(john, bob).  parent(bob, ann).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
        grandparent(john, W)
        └─ unify head: X=john, Y=W   → goals: parent(john, Z), parent(Z, W)
           └─ parent(john, Z): unify parent(john, bob) → Z=bob          [unify]
              └─ parent(bob, W): unify parent(bob, ann) → W=ann         [unify]
                 └─ SUCCESS  W = ann
    (No backtracking is needed; there is one parent fact for john and one for bob.)

(b) DEPTH-FIRST ORDER. Adding  parent(john, carol). parent(carol, dave).  gives a
    second path. DFS tries clauses/facts in source order: parent(john, bob) comes
    before parent(john, carol), so it finds W = ann first (via bob), then on
    backtracking explores Z = carol and finds W = dave. Order: [ann, dave].

(c) CUT. To commit to the first grandparent found, put a cut after the
    grandparent goal:
        first_gc(X, Y) :- grandparent(X, Y), !.
    The cut discards the choice points created while solving grandparent — here
    the alternative Z = carol / W = dave branch — so first_gc(john, W) yields only
    W = ann. (Working this exercise turned up two bugs in the companion sprolog —
    a query/rule variable-id collision and a cut that did not prune choice points
    inside a called rule; both were fixed, with a regression suite in
    ch10/06_prolog/test_cut.py.)
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "06_prolog"))

from sprolog import PrologInterpreter  # noqa: E402


def values(interp, q):
    return [str(v) for s in interp.query(q) for v in s.values()]


if __name__ == "__main__":
    # (a) base case: one grandchild
    p = PrologInterpreter()
    p.add_rules('''
        parent(john, bob).
        parent(bob, ann).
        grandparent(X, Y) :- parent(X, Z), parent(Z, Y).
    ''')
    base = values(p, "grandparent(john, W)")
    assert base == ["ann"], base

    # (b) add a second grandchild; depth-first follows source order
    p.add_rules('''
        parent(john, carol).
        parent(carol, dave).
    ''')
    dfs = values(p, "grandparent(john, W)")
    assert dfs == ["ann", "dave"], dfs        # bob-branch before carol-branch

    # (c) cut commits to the first grandparent, discarding the carol/dave branch
    p.add_rules('first_gc(X, Y) :- grandparent(X, Y), !.')
    committed = values(p, "first_gc(john, W)")
    assert committed == ["ann"], committed

    print(f"W = {base[0]}; with a 2nd grandchild DFS gives {dfs}; "
          f"cut commits to {committed}")
