"""
Chapter 7, Exercise 4 — solution code.

The TLetExpr case extends the env with {**env, n: v} and lowers the body in it,
emitting NO instruction for the binding. (a) why does a let need no TAC
instruction? (b) contrast with the recursive evaluator, which built a new env
dict at run time per let — where did that cost go?

How to run:   python3 ex04_let_no_instr.py
Expected:     "let x = a + b in x * x : no instruction for the binding (3 instrs)"

(a) A `let x = e in body` does not denote a computation of its own — it just
    gives the value of `e` a NAME for use in `body`. The lowerer already produced
    a Val (a temporary or constant) for `e`; binding `x` to that Val is a
    COMPILE-TIME map update ({**env, x: v}), not a run-time action. The body's
    instructions then refer to that same Val directly. So no IAssign/copy is
    emitted for the binding itself — only the instructions for `e` and for
    `body`. (A copy would be pure overhead; register allocation/coalescing in
    Chapter 9 removes even the moves that do survive.)

(b) The recursive evaluator (Chapter 6) allocated a fresh environment dictionary
    at RUN time for every let, on every execution. Lowering performs that
    environment threading ONCE, at COMPILE time, collapsing each name to the Val
    it stands for. The run-time dictionary cost disappears entirely: at run time
    there is no environment object at all, only temporaries (and, later,
    registers). The cost moved from every execution to a single compile pass.
"""

from _harness import lower_src, tac

# let x = a + b in x * x  — the binding `x` should add no instruction beyond the
# add (for a+b) and the multiply (x*x) and the return.
SRC = "module M\nfn g(a : Int, b : Int) : Int = let x = a + b in x * x"


if __name__ == "__main__":
    fn = lower_src(SRC).functions[0]
    body = fn.body

    binops = [i for i in body if isinstance(i, tac.IBinOp)]
    assigns = [i for i in body if isinstance(i, tac.IAssign)]
    returns = [i for i in body if isinstance(i, tac.IReturn)]

    # exactly two arithmetic ops (the + and the *), no copy for the binding,
    # and one return — three instructions total.
    assert len(binops) == 2 and [i.op for i in binops] == ["+", "*"]
    assert len(assigns) == 0, "a let binding must emit no copy/assign"
    assert len(returns) == 1
    assert len(body) == 3, [type(i).__name__ for i in body]

    # the multiply reads the SAME temp the add produced — x is just that temp
    add, mul = binops
    assert mul.l == add.dst and mul.r == add.dst

    print(f"let x = a + b in x * x : no instruction for the binding "
          f"({len(body)} instrs)")
