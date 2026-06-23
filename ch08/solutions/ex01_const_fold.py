"""
Chapter 8, Exercise 1 — solution code.

Take the naive TAC for `let x = 2 + 3 in let y = x * x in y + x`. (a) write it as
Lark lowers it (no folding). (b) apply constant folding and propagation to a fixed
point, showing each step. (c) state the property + and * must have for every step
to be meaning-preserving, and why it holds for 32-bit Int but needs care for Float.

How to run:   python3 ex01_const_fold.py
Expected:     "naive: 3 IBinOp; folded to a fixed point: return 30 (0 IBinOp, 0 IAssign)"

(a) Lark lowers (folding nothing) to:
        t0 = 2 + 3
        t1 = t0 * t0        (x reused as t0)
        t2 = t1 + t0
        return t2

(b) Fold + propagate to a fixed point (the pass below prints each step):
        t0 = 2 + 3   -> t0 = 5            (both operands constant: fold)
        t1 = t0 * t0 -> t1 = 25           (t0 known 5: propagate, then fold)
        t2 = t1 + t0 -> t2 = 30           (t1=25, t0=5: fold)
        return t2    -> return 30         (propagate the constant)
    Dead-code elimination then drops t0/t1/t2 (now unused). Result: return 30.

(c) PROPERTY: compile-time evaluation of op must give the SAME result as run-time
    evaluation — the operation must be a pure, deterministic, total function whose
    host (compiler) semantics match the target exactly. For 32-bit Int this holds:
    two's-complement + and * are exact and wrap identically at compile and run
    time, with no rounding or special values. For Float it needs care: IEEE-754
    has rounding modes, NaN, and signed zero, so the compiler's host float must
    match the target's precision/rounding bit-for-bit, or folding changes results
    (Exercise 4 shows x + 0.0).
"""

from _harness import lower_src, tac

SRC = "module M\nfn f(io : IO) : Int = let x = 2 + 3 in let y = x * x in y + x"

_OPS = {"+": lambda a, b: a + b, "-": lambda a, b: a - b,
        "*": lambda a, b: a * b, "//": lambda a, b: a // b}


def fold_propagate(body, verbose=False):
    """Constant-fold + forward-propagate + DCE over one basic block, to a fixed
    point. Returns the new instruction list."""
    consts = {}          # Tmp -> python value

    def val(v):
        if isinstance(v, tac.Tmp) and v in consts:
            return tac.Const(consts[v])
        return v

    # fold + propagate
    out = []
    for ins in body:
        if isinstance(ins, tac.IBinOp):
            l, r = val(ins.l), val(ins.r)
            if isinstance(l, tac.Const) and isinstance(r, tac.Const) and ins.op in _OPS:
                result = _OPS[ins.op](l.value, r.value)
                consts[ins.dst] = result
                out.append(tac.IAssign(ins.dst, tac.Const(result)))
                if verbose:
                    print(f"   fold  {ins.dst} = {ins.op}  -> {result}")
            else:
                out.append(tac.IBinOp(ins.dst, ins.op, l, r))
        elif isinstance(ins, tac.IAssign):
            s = val(ins.src)
            if isinstance(s, tac.Const):
                consts[ins.dst] = s.value
            out.append(tac.IAssign(ins.dst, s))
        elif isinstance(ins, tac.IReturn):
            out.append(tac.IReturn(val(ins.val) if ins.val is not None else None))
        else:
            out.append(ins)

    # dead-code elimination: drop assigns to temps never read afterwards
    used = set()
    for ins in out:
        for f in ("l", "r", "src", "val"):
            v = getattr(ins, f, None)
            if isinstance(v, tac.Tmp):
                used.add(v)
    out = [ins for ins in out
           if not (isinstance(ins, (tac.IAssign, tac.IBinOp)) and ins.dst not in used)]
    return out


if __name__ == "__main__":
    fn = lower_src(SRC).functions[0]
    naive_binops = [i for i in fn.body if isinstance(i, tac.IBinOp)]
    assert len(naive_binops) == 3, [i.op for i in naive_binops]

    print("folding steps:")
    folded = fold_propagate(fn.body, verbose=True)

    binops = [i for i in folded if isinstance(i, tac.IBinOp)]
    assigns = [i for i in folded if isinstance(i, tac.IAssign)]
    rets = [i for i in folded if isinstance(i, tac.IReturn)]
    assert len(binops) == 0 and len(assigns) == 0
    assert len(rets) == 1 and isinstance(rets[0].val, tac.Const) and rets[0].val.value == 30

    print(f"\nnaive: {len(naive_binops)} IBinOp; folded to a fixed point: "
          f"return {rets[0].val.value} (0 IBinOp, 0 IAssign)")
