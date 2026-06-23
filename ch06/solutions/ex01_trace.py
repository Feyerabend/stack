"""
Chapter 6, Exercise 1 — solution code.

The recursive evaluator and the CEK machine must agree on every program that does
not overflow the host stack. For `let x = 2 + 3 in x * x`: (a) trace the
recursive eval; (b) trace the CEK machine (state, value/expr, full kont) at every
step; (c) identify where LetF is pushed and popped, and what plays that role in
the recursive version.

How to run:   python3 ex01_trace.py
Expected:     a CEK trace ending in 25, then a line confirming the LetF push/pop.

(a) RECURSIVE eval (Section 6.1), env shown in force:
    eval(let x = 2+3 in x*x, {})            # env = {}
      eval(2 + 3, {})                        # to bind x
        eval(2, {}) -> 2 ; eval(3, {}) -> 3 ; binop + -> 5
      eval(x * x, {x:5})                      # env extended with x=5
        eval(x, {x:5}) -> 5 ; eval(x, {x:5}) -> 5 ; binop * -> 25
    => 25
    The recursive version holds "multiply the result by x, then this is the let
    body's value" implicitly on the PYTHON call stack — the activation record of
    the `eval(let ...)` call that is suspended while `eval(2+3)` runs. That
    suspended frame is exactly what the CEK machine reifies as `LetF`.

(b)/(c) The CEK trace is printed below; LetF is pushed when the let's value
    sub-expression begins evaluating and popped when that value is delivered (so
    the body is evaluated with x bound).
"""

from _harness import setup, run_states, snapshot, cek

SRC = "module M\nfn main(io : IO) : Int = let x = 2 + 3 in x * x"


if __name__ == "__main__":
    env, m = setup(SRC)
    states, result = run_states(env, m)

    print(f"  {'#':>2}  {'state':7} {'expr/value':14} kont (top..bottom)")
    push = pop = None
    prev_has = False
    for i, s in enumerate(states):
        kind, payload, konts, n = snapshot(s)
        has_letf = "LetF" in konts
        if has_letf and not prev_has and push is None:
            push = i
        if prev_has and not has_letf and pop is None:
            pop = i
        prev_has = has_letf
        print(f"  {i:>2}  {kind:7} {payload:14} {konts}")

    assert isinstance(result, cek.VInt) and result.n == 25, result
    assert push is not None and pop is not None and pop > push
    print(f"\nresult = {result}  |  LetF pushed at step {push}, popped at step {pop}")
    print("In the recursive eval, the suspended activation record of "
          "eval(let ...) plays the role of LetF.")
