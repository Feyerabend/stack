"""
Chapter 6, Exercise 2 — solution code.

For `adder` and `let add5 = adder(5) in add5(10)`: (a) show the VClosure produced
by adder(5) — param, body, captured env; (b) explain what breaks if the closure
captured the caller's env at call time instead of the defining env at creation
time; (c) construct a program where the two strategies differ.

How to run:   python3 ex02_closure.py
Expected:     "adder(5): VClosure(param=x, env has n=5); add5(10)=15; "
              "lexical capture gives 1 (dynamic would give 100)"

(b) WHAT BREAKS with call-time (dynamic) capture. The returned function's free
    variable `n` would be resolved against whatever `n` happens to exist where
    the function is CALLED, not where it was written. adder has already returned
    by then, so `n` might be gone entirely, or — worse — silently bound to an
    unrelated `n` at the call site. Lexical capture is what makes `adder(5)`
    mean "+5" forever, independent of the caller. It is also what the type
    checker assumed: a closure's free variables were checked in its defining
    scope (Chapter 5).
"""

from _harness import setup, cek

ADDER = """module M
fn adder(n : Int) : Int -> Int = fn (x : Int) => n + x
fn main(io : IO) : Int = let add5 = adder(5) in add5(10)
"""

# (c) lexical vs dynamic differ here: f captures n = 1 at creation; a later
# `let n = 100` shadows n, but lexical scope keeps f's n = 1.
CAPTURE = """module M
fn main(io : IO) : Int =
  let n = 1 in
  let f = fn (x : Int) => n + x in
  let n = 100 in
  f(0)
"""


if __name__ == "__main__":
    env, m = setup(ADDER)

    # (a) the VClosure that adder(5) produces
    clo = cek.run(cek.apply(env["adder"], cek.VInt(5), [], m), m)
    assert isinstance(clo, cek.VClosure)
    assert clo.param == "x"
    assert isinstance(clo.env.get("n"), cek.VInt) and clo.env["n"].n == 5
    # its body is the inner `n + x` (a TBinOp)
    assert type(clo.body).__name__ == "TBinOp"

    # the whole program: add5(10) = 15
    _, _m2 = setup(ADDER)
    add5_result = cek.run(cek.apply(env["main"], cek.VIO(), [], m), m)
    assert isinstance(add5_result, cek.VInt) and add5_result.n == 15

    # (c) lexical capture: result is 1 (dynamic capture would give 100)
    env2, m2 = setup(CAPTURE)
    cap = cek.run(cek.apply(env2["main"], cek.VIO(), [], m2), m2)
    assert isinstance(cap, cek.VInt) and cap.n == 1, cap

    print(f"adder(5): VClosure(param={clo.param}, env has n={clo.env['n']}); "
          f"add5(10)={add5_result}; lexical capture gives {cap} "
          f"(dynamic would give 100)")
