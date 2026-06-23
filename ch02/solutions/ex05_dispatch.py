"""
Chapter 2, Exercise 5 — solution code.

Implement two dispatch strategies for the stack VM -- the if/elif chain shown in
the chapter and a dictionary mapping each opcode to a handler function -- and
time both on the sum-to-one-million loop. Which is faster under CPython? Does the
ordering match the C intuition from Section 2.x, and if not, why might the host
interpreter change the answer?

How to run:   python3 ex05_dispatch.py [N]        (default N = 300000)
Expected:     a timing table; both strategies print the same checksum.

Finding: the two are CLOSE -- within ~10% either way -- and which one wins
depends on the CPython version. The C intuition is that a dense switch compiles
to a jump table (O(1)) and clearly beats an O(n) comparison chain (computed goto
faster still). That large win does NOT transfer to Python, and the *sign* even
changes across releases:

  - Older lore: the if/elif chain often beat dict-of-functions, because each
    dict-dispatched opcode pays a real Python-level FUNCTION CALL (frame setup),
    which outweighed the chain's few integer comparisons.
  - Measured here on CPython 3.14: dict dispatch is ~1.1x FASTER. Since 3.11,
    method calls are much cheaper (adaptive interpreter, specialised CALL) and
    dict lookups are specialised, so the call overhead no longer dominates and
    the O(1) lookup edges ahead.

The lesson is the chapter's: don't assume -- measure. And dispatch is usually
not the bottleneck at all (operand-stack memory traffic is), which is why the
gap stays small whichever way it falls. This script reports whichever wins on
your interpreter rather than hard-coding an answer.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stack_vm import (  # noqa: E402
    StackVM, HALT, PUSH, ADD, SUB, LT, JMPZ, JMP, LOAD, STORE,
)


def sum_loop_bytecode(n):
    """Bytecode summing 1 + 2 + ... + n.  locals[0]=n (counter), locals[1]=acc."""
    # init n = <low byte trick not needed: we set locals directly>, acc = 0
    # We set locals[0] before run() (n may exceed one byte), and start acc = 0.
    #
    #  loop @ 0: while 0 < n
    #    PUSH 0 ; LOAD 0 ; LT ; JMPZ end
    #    LOAD 1 ; LOAD 0 ; ADD ; STORE 1     acc += n
    #    LOAD 0 ; PUSH 1 ; SUB ; STORE 0     n  -= 1
    #    JMP loop
    #  end: LOAD 1 ; HALT
    return [
        # loop @ 0
        PUSH, 0, LOAD, 0, LT,          # 0-4
        JMPZ, 0, 25,                   # 5-7  -> end @ 25
        LOAD, 1, LOAD, 0, ADD, STORE, 1,   # 8-14
        LOAD, 0, PUSH, 1, SUB, STORE, 0,   # 15-21
        JMP, 0, 0,                     # 22-24 -> loop
        # end @ 25
        LOAD, 1, HALT,                 # 25-27
    ]
    # NOTE: addresses verified in __main__ via the checksum assertion.


class DictStackVM(StackVM):
    """StackVM whose dispatch is a dict {opcode: handler method}."""

    def __init__(self, code):
        super().__init__(code)
        self.running = True
        self.result = None
        self.table = {
            HALT:  self._halt,  PUSH: self._push, ADD: self._add,
            SUB:   self._sub,   LT:   self._lt,   JMPZ: self._jmpz,
            JMP:   self._jmp,   LOAD: self._load, STORE: self._store,
        }

    def _halt(self):
        self.result = self.stack[-1] if self.stack else None
        self.running = False

    def _push(self):  self.stack.append(self.code[self.pc]); self.pc += 1
    def _add(self):   b = self.stack.pop(); self.stack[-1] += b
    def _sub(self):   b = self.stack.pop(); self.stack[-1] -= b
    def _lt(self):    b = self.stack.pop(); self.stack[-1] = int(self.stack[-1] < b)
    def _jmp(self):   self.pc = self._u16()

    def _jmpz(self):
        target = self._u16()
        if not self.stack.pop():
            self.pc = target

    def _load(self):
        s = self.code[self.pc]; self.pc += 1
        self.stack.append(self.locals[s])

    def _store(self):
        s = self.code[self.pc]; self.pc += 1
        self.locals[s] = self.stack.pop()

    def run(self):
        code = self.code
        table = self.table
        while self.running:
            op = code[self.pc]; self.pc += 1
            table[op]()
        return self.result


def time_run(vm_class, code, n):
    vm = vm_class(code)
    vm.locals[0] = n        # counter starts at n; acc (locals[1]) starts 0
    t0 = time.perf_counter()
    result = vm.run()
    return result, time.perf_counter() - t0


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300_000
    code = sum_loop_bytecode(n)
    expected = n * (n + 1) // 2

    r_chain, t_chain = time_run(StackVM, code, n)
    r_dict,  t_dict  = time_run(DictStackVM, code, n)

    assert r_chain == expected, f"if/elif: {r_chain} != {expected}"
    assert r_dict == expected, f"dict: {r_dict} != {expected}"

    print(f"sum 1..{n} = {expected}  (both strategies agree)")
    print(f"  {'strategy':<18}{'seconds':>10}")
    print(f"  {'if/elif chain':<18}{t_chain:>10.3f}")
    print(f"  {'dict dispatch':<18}{t_dict:>10.3f}")
    faster = "if/elif chain" if t_chain < t_dict else "dict dispatch"
    ratio = max(t_chain, t_dict) / min(t_chain, t_dict)
    print(f"  faster: {faster}  ({ratio:.2f}x)")
