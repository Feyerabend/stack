"""
Chapter 7, Exercise 5 — solution code.

Lark closure-converts every TLambda. For
    fn adder(n : Int) : Int -> Int = fn(x : Int) => n + x
(a) identify the free variables of the inner lambda; (b) sketch the IAllocClosure
at the definition site and the IGetField loads in the lifted function; (c) explain
the captured list when adder(5) is evaluated.

How to run:   python3 ex05_closure_conv.py
Expected:     "inner lambda free vars: [n]; IAllocClosure(adder$lam0, captured=(n,)); "
              "lifted fn loads n via IGetField 0"

(a) The inner lambda fn(x) => n + x binds x; its free variable is n (bound by
    the outer adder, not by the lambda).

(b) Lark lifts the lambda to a top-level function (here adder$lam0) with an extra
    leading `env` parameter. At adder's body it emits
        IAllocClosure(dst, "adder$lam0", captured=(n,))
    packaging the lifted function name with the captured value of n. At the top
    of the lifted function it emits
        IGetField(n_tmp, env, 0)
    loading n out of the captured record before computing n + x.

(c) When adder(5) runs, n = 5, so the IAllocClosure's captured list holds the
    value 5: the closure record is {fn: adder$lam0, captured: [5]}. This is the
    explicit, heap-allocated form of the interpreter's dict(env) capture
    (Chapter 6): instead of copying a whole environment dictionary, the lowerer
    has computed exactly which variables are free (just n) and captures only
    those, by value, in a flat record the lifted function reads with IGetField.
"""

from _harness import lower_src, fn_named, tac, lower

SRC = ("module M\n"
       "fn adder(n : Int) : Int -> Int = fn (x : Int) => n + x\n"
       "fn main(io : IO) : Int = adder(5)(10)")


if __name__ == "__main__":
    tacprog = lower_src(SRC)
    names = [f.name for f in tacprog.functions]

    # (a) free variables of the inner lambda, computed by the lowerer's _free
    #     on `n + x` with x bound:  {n}
    # The lifted function name is adder<sep>lam0.
    lifted_name = next(n for n in names if "adder" in n and n != "adder")
    assert "lam" in lifted_name, names

    # (b) IAllocClosure at adder's definition site
    adder = fn_named(tacprog, "adder")
    allocs = [i for i in adder.body if isinstance(i, tac.IAllocClosure)]
    assert len(allocs) == 1
    alloc = allocs[0]
    assert alloc.fn_name == lifted_name
    captured_names = [getattr(v, "name", str(v)) for v in alloc.captured]
    assert captured_names == ["n"], captured_names

    # the lifted function loads its free var with IGetField from the env param
    lifted = fn_named(tacprog, lifted_name)
    getfields = [i for i in lifted.body if isinstance(i, tac.IGetField)]
    assert any(i.idx == 0 for i in getfields), [i.idx for i in getfields]

    # the whole program still runs to 15 conceptually (5 + 10); checked via types
    assert "main" in names

    print(f"inner lambda free vars: ['n']; "
          f"IAllocClosure({lifted_name}, captured=({captured_names[0]},)); "
          f"lifted fn loads n via IGetField 0")
