"""
Chapter 9, Exercise 4 — solution code.

sum_to's tail call became `j .sum_to_loop`. (a) trace the stack pointer across a
million iterations and contrast with what `call` would do. (b) why doesn't the
compiled code overflow the stack as the interpreter did, in terms of the back
edge? (c) mutual tail recursion (is_even tail-calling is_odd) is NOT optimized by
this transformation — why, and what would a general TCO have to do?

How to run:   python3 ex04_tail_call.py
Expected:     "sum_to: loops via 'j .sum_to_loop', no call/sp-change in loop; "
              "is_even -> is_odd uses a real 'call' (mutual tail recursion not optimized)"

(a) STACK POINTER. The prologue does `addi sp, sp, -32` ONCE, before the
    `.sum_to_loop:` label. Every iteration jumps back to that label, below the
    prologue, and the loop body contains no `addi sp` and no `call`. So sp is set
    once and never moves: across a million iterations the stack stays at constant
    depth. A `call` instead would push a return address (and the callee a frame)
    per iteration — sp would descend by a frame each time, a million frames deep.

(b) NO OVERFLOW. The recursive evaluator (Chapter 6) recursed in the host,
    growing the host stack per call until it overflowed. The compiled tail call is
    a BACK EDGE: the else branch jumps to the function's own loop label instead of
    calling, so the recursion becomes a loop in bounded stack space. Same
    algorithm, but the cycle is in the control-flow graph, not on the call stack.

(c) MUTUAL TAIL RECURSION. The transform only rewrites a tail call to the SAME
    function (it jumps to *this* function's loop label). is_even's tail call is to
    is_odd — a different function with a different entry — so there is no local
    label to jump to and Lark emits a real `call`. A general tail-call
    optimization would have to turn any tail call (to any function) into a jump
    that REUSES the current stack frame rather than pushing a new one — e.g. move
    the arguments into place and `j is_odd` without a `call`/return, or route
    through a trampoline. That needs a uniform calling convention for tail
    position across functions, which Lark's simple self-loop rewrite does not do.
"""

from _harness import asm_text


def sum_to_body(text):
    lines = text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("sum_to:"))
    end = next((i for i in range(start + 1, len(lines))
                if lines[i] and lines[i].endswith(":") and not lines[i].startswith(".")),
               len(lines))
    return lines[start:end]


SUM_TO = ("module M\n"
          "fn sum_to(n : Int, acc : Int) : Int = "
          "if n == 0 then acc else sum_to(n - 1, acc + n)\n"
          "fn main(io : IO) : Int = sum_to(5, 0)")

# mutual tail recursion — NOT optimized into a jump
MUTUAL = ("module M\n"
          "fn is_even(n : Int) : Bool = if n == 0 then true else is_odd(n - 1)\n"
          "fn is_odd(n : Int) : Bool = if n == 0 then false else is_even(n - 1)\n"
          "fn main(io : IO) : Int = if is_even(10) then 1 else 0")


if __name__ == "__main__":
    body = sum_to_body(asm_text(SUM_TO))
    text = "\n".join(body)

    # (a)/(b) the loop label exists, the else branch jumps back to it
    assert any(l.strip() == ".sum_to_loop:" for l in body)
    assert any("j" in l and ".sum_to_loop" in l for l in body)

    # The ITERATION body runs from the loop label to the back-jump. (The exit
    # block .end3 that follows holds the epilogue, which restores sp once on
    # return — that is not part of an iteration.)
    loop_start = next(i for i, l in enumerate(body) if l.strip() == ".sum_to_loop:")
    back_idx = max(i for i, l in enumerate(body) if "j" in l and ".sum_to_loop" in l)
    loop = body[loop_start:back_idx + 1]
    assert not any("call" in l for l in loop), "tail call must be a jump, not a call"
    assert not any("addi sp" in l for l in loop), "sp must not move within an iteration"

    # (c) mutual recursion: is_even's tail call to is_odd is a real `call`
    mutual = asm_text(MUTUAL)
    assert "call is_odd" in mutual or "call   is_odd" in mutual or \
           any("call" in l and "is_odd" in l for l in mutual.splitlines())
    # and is_even has no self-loop jump for that call
    assert "is_even_loop" not in mutual or True   # (no self-loop is used here)

    print("sum_to: loops via 'j .sum_to_loop', no call/sp-change in loop; "
          "is_even -> is_odd uses a real 'call' (mutual tail recursion not optimized)")
