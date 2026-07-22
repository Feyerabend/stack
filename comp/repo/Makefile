# The Lark companion code — three strands, one question each.
#
#   self/      Can a compiler compile itself?          (and how do you know it did?)
#   optimize/  Can it make the code faster             (without changing what it means?)
#   prove/     Can it promise the program cannot fail  (before ever running it?)
#
# Each strand stands alone: `cd self && make` works, and nothing reaches outside
# its own directory. This file is only a way in. Run `make help` in any strand
# for its own targets.
#
# You need Python 3, a C compiler, and — for prove's typeset account — tectonic.
# Nothing to install, nothing to configure.

.DEFAULT_GOAL := help
.PHONY: help self optimize prove test clean

help:
	@echo "The Lark companion code. Three strands, each runnable on its own:"
	@echo
	@echo "  self/       the compiler, written in itself, checked against a Python"
	@echo "              reference at every stage — tokens, trees, types, behaviour,"
	@echo "              emitted C — and then compiling itself to a fixpoint"
	@echo "  optimize/   the optimizing back end, held to the rule that optimized"
	@echo "              code must still mean what it meant"
	@echo "  prove/      a proof checker in 4,000 lines of C, and Lark's soundness"
	@echo "              proof checked by it"
	@echo
	@echo "Targets here:"
	@echo "  make self       run self/'s differentials      (slow: hours)"
	@echo "  make optimize   run optimize/'s differentials  (slow)"
	@echo "  make prove      check the proofs               (fast: seconds)"
	@echo "  make test       all three"
	@echo "  make clean      clean all three"
	@echo
	@echo "Or go into a strand and ask it directly:"
	@echo "  cd self && make help"
	@echo
	@echo "Start with 'make prove' — it is the only one that finishes while you watch."

self:
	$(MAKE) -C self test

optimize:
	$(MAKE) -C optimize test

prove:
	$(MAKE) -C prove test

test: prove self optimize

clean:
	$(MAKE) -C self clean
	$(MAKE) -C optimize clean
	$(MAKE) -C prove clean
