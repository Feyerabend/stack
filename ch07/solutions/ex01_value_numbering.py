"""
Chapter 7, Exercise 1 — solution code.

Lower (a + b) * (a + b) to TAC by hand, as Lark's lowerer does. (a) how many
IBinOp result? (b) apply local value numbering and give the reduced sequence.
(c) state the soundness condition and why it holds within a basic block but not
necessarily across two.

How to run:   python3 ex01_value_numbering.py
Expected:     "lowered: 3 IBinOp; after local value numbering: 2 IBinOp"

(a) Lark emits the obvious instruction per node, so (a+b)*(a+b) lowers to:
        t0 = a + b
        t1 = a + b
        t2 = t0 * t1
        return t2
    Three IBinOp (two '+', one '*') — the repeated a+b is computed twice.

(b) Local value numbering hashes each expression by (op, value-numbers of
    operands). The second `a + b` has the same value number as the first, so it
    reuses t0; t1 becomes dead and is dropped:
        t0 = a + b
        t2 = t0 * t0
        return t2
    Two IBinOp.

(c) SOUNDNESS CONDITION: reusing the earlier result for a later identical
    expression is valid only if neither operand has been reassigned between the
    two occurrences (and there is no aliasing/effect that could change their
    values). Within ONE basic block this always holds: a basic block is
    straight-line code with a single entry, and Lark's temporaries are assigned
    once, so a + b cannot silently change between the two uses. ACROSS two
    blocks it need not hold: control may enter the second block by a different
    edge on which a or b was reassigned, so a value computed in block 1 cannot be
    assumed live/valid in block 2 without a global (data-flow) analysis. That is
    why this is *local* value numbering.
"""

from _harness import lower_src, tac

SRC = "module M\nfn f(a : Int, b : Int) : Int = (a + b) * (a + b)"


def local_value_numbering(instrs):
    """Minimal LVN over a single basic block: dedupe IBinOp by value number."""
    table = {}           # (op, operand-key) -> dst Tmp
    subst = {}           # Tmp -> canonical Tmp
    out = []

    def resolve(v):
        return subst.get(v, v)

    for ins in instrs:
        if isinstance(ins, tac.IBinOp):
            l, r = resolve(ins.l), resolve(ins.r)
            operands = frozenset((l, r)) if ins.op in ("+", "*") else (l, r)
            key = (ins.op, operands)
            if key in table:
                subst[ins.dst] = table[key]      # reuse earlier result
                continue                          # drop the redundant instr
            table[key] = ins.dst
            out.append(tac.IBinOp(ins.dst, ins.op, l, r))
        elif isinstance(ins, tac.IReturn):
            out.append(tac.IReturn(resolve(ins.val) if ins.val is not None else None))
        else:
            out.append(ins)
    return out


if __name__ == "__main__":
    fn = lower_src(SRC).functions[0]
    before = [i for i in fn.body if isinstance(i, tac.IBinOp)]
    assert len(before) == 3, [i.op for i in before]

    reduced = local_value_numbering(fn.body)
    after = [i for i in reduced if isinstance(i, tac.IBinOp)]
    assert len(after) == 2, [i.op for i in after]
    # the multiply now uses the same temp twice (t0 * t0)
    mul = [i for i in after if i.op == "*"][0]
    assert mul.l == mul.r

    print(f"lowered: {len(before)} IBinOp; "
          f"after local value numbering: {len(after)} IBinOp")
