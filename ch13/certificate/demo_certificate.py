"""
demo_certificate.py — the certifying register allocator, lied to, live.

Chapter 13 (section 13.4) replaces the allocator's correlated verify() with
an independent certificate (lark/09/src/regcheck.py) that re-derives
liveness from scratch and refuses any allocation that fails checks R1-R5.
This demo runs the REAL pipeline (parse -> typecheck -> lower -> allocate)
on a real sample program, then applies the chapter's boxed principle to the
certificate itself, in both directions:

  1. the honest allocation passes (the checker is not paranoid);
  2. a planted mutation -- every temporary forced into one register, the
     "everything-in-one-register bug" of section 13.4 -- is caught, with
     the clobbering instruction named.

How to run:   python3 demo_certificate.py
Expected:     "certificate PASSES" for the honest allocation, then a named
              R3 violation for the corrupted one.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _c in (os.path.join(_HERE, "..", "..", "lark"),
           os.path.join(_HERE, "..", "..", "..")):
    if os.path.exists(os.path.join(_c, "09", "src", "infer.py")):
        _LARK = os.path.abspath(_c)
        break
else:
    raise SystemExit("error: cannot find the lark tree (lark/09/)")

sys.path.insert(0, os.path.join(_LARK, "09", "src"))

import parser as _parser            # noqa: E402  (lark/09/src)
import infer as _infer              # noqa: E402
from lower import lower             # noqa: E402
from regalloc import allocate_tac   # noqa: E402
from regcheck import check_tac, RegAllocCertificateError  # noqa: E402

SAMPLE = os.path.join(_LARK, "09", "samples", "01_mergesort.lark")


def main() -> None:
    print(f"program under compilation: {os.path.relpath(SAMPLE, _LARK)}")
    prog = _parser.parse_file(SAMPLE)
    tac = lower(_infer.typecheck(prog, source_file=SAMPLE))
    allocs = allocate_tac(tac)

    # Direction one: the honest allocation must pass. A checker that flags
    # safe output is merely paranoid, and paranoid checkers get disabled.
    check_tac(tac, allocs)
    n_fns = len(tac.functions)
    print(f"honest allocation:    certificate PASSES ({n_fns} functions checked)")

    # Direction two: plant the everything-in-one-register bug in the first
    # function that actually uses two registers, and watch R3 fire.
    for fn, alloc in zip(tac.functions, allocs):
        regs = sorted(set(alloc.reg.values()))
        if len(regs) >= 2:
            for tmp in alloc.reg:
                alloc.reg[tmp] = regs[0]
            print(f"planted mutation:     every temp of '{fn.name}' -> {regs[0]}")
            break

    try:
        check_tac(tac, allocs)
    except RegAllocCertificateError as e:
        first = str(e).splitlines()
        print("certificate CATCHES:  " + first[0])
        print("                      " + first[1].strip())
        print()
        print("Both directions held: quiet on safe output, loud on the lie,")
        print("with the clobbering instruction named. asm.gen() runs this on")
        print("every compilation, so the fuzzer stress-tests it for free.")
        return
    raise SystemExit("BUG: the planted mutation was NOT caught")


if __name__ == "__main__":
    main()
