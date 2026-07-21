PYTHON = python3
SRC    = src
TESTS  = tests

.PHONY: help test harden drift conservative prove solver robust fuzz adversary torture invariants clean

help:
	@echo "Lark 08 — the refinement fork of the frozen oracle (PROVE.md)"
	@echo "  make drift          — 08/src == 07/src except where declared (tests/drift.py)"
	@echo "  make conservative   — 07's corpus behaves identically through 08/ (infer + cek)"
	@echo "  make prove          — the verification suite: safe programs vs their mutants"
	@echo "  make solver         — the decision procedure's own self-check"
	@echo "  make robust         — the checker over 07's whole corpus: no crash, ever"
	@echo "  make fuzz           — random QF-UFLIA vs brute force: no unsound answer"
	@echo "  make adversary      — random PROGRAMS: proved ⇒ it runs. The witness."
	@echo "  make torture        — hostile programs: a crash is not a verdict, nor is a hang"
	@echo "  make invariants     — the rules, checked: every node walked, every division asked"
	@echo "  make test           — the four that pin behaviour"
	@echo "  make harden         — test, plus the five that hunt for breakage"
	@echo ""
	@echo "  07/src is FROZEN. This tree forks it; it never edits it (PROVE.md 0.1)."

# Every file in 08/src is byte-identical to its 07/src twin unless drift.py's
# EXTENDED/ADDED tables say why not.  The tables are the size of the extension.
drift:
	$(PYTHON) $(TESTS)/drift.py

# The conservative-extension baseline: a program with no refinement must answer
# the same through 08/ as through 07/.  Set LARK_TIMEOUT to change the budget.
conservative:
	$(PYTHON) $(TESTS)/conservative_difftest.py

# Safe programs must check; their mutants must be caught, each for a stated
# reason. A verifier is only as good as the programs it rejects.
prove:
	$(PYTHON) $(TESTS)/prove_difftest.py

# The solver decides QF-UFLIA on its own terms, before any Lark is involved —
# including the grey-region cases only splintering can settle.
solver:
	$(PYTHON) $(SRC)/solver.py

# Every file of 07's real corpus through the refinement checker, in-process.  The
# question is not "is it proved" but "did it survive": a crash is never a verdict.
robust:
	$(PYTHON) $(TESTS)/robust_sweep.py

# Random formulas, decided twice: once by the solver, once by brute force over a
# small box.  Only the fatal direction fails the run — a contradiction that isn't
# there, or a proof with a counterexample.  Args: [cases] [seed].
fuzz:
	$(PYTHON) $(TESTS)/solver_fuzz.py 3000 7

# Random PROGRAMS against the checker's own promise: if it says `ok`, the program
# must not crash — checked, then RUN on the CEK machine.  `fuzz` tests the solver;
# every real bug this project has had was one level up, in the checker that builds
# the obligations, and every one of them was found by hand.  Args: [cases] [seed].
adversary:
	$(PYTHON) $(TESTS)/adversary.py 150 11

# Legal programs that no one would write: 3000 terms in one expression, a 300-way
# conjunction, a constructor term 400 deep.  The other harnesses ask whether the
# checker is RIGHT; this one asks whether it ANSWERS.  A traceback is the checker
# saying nothing, at length — and a hang is the same thing, forever.  Arg: [seconds].
torture:
	$(PYTHON) $(TESTS)/torture.py 60

invariants:
	$(PYTHON) $(TESTS)/invariants.py

test: drift conservative solver prove

harden: test robust fuzz adversary torture invariants

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	@echo "clean"
