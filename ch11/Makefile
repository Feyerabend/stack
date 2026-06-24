.PHONY: all run run-demos run-tests run-c run-z3 clean

PYTHON := python3
CC     := cc

# Chapter 11 — Correctness.
# `make run` runs the §11.2 Hoare verification-condition generator + demo, the
# §11.5 testing-methods demo, and the supplementary verification code that needs
# no extra dependencies: the Presburger decision procedure (Python + C) and the
# CTL / VM model checkers. `make run-z3` runs the z3/ symbolic-execution demos,
# which need `pip install z3-solver` (see verification/z3/README.md).

# Self-demoing scripts that take no arguments. presburger.py defaults to an
# interactive REPL, so it is run with --demo separately below.
DEMOS := \
  02_hoare/vcgen.py \
  02_hoare/vcgen_enhanced.py \
  02_hoare/demo.py \
  05_testing/testing_methods.py \
  verification/presburger/cooper.py \
  verification/model/ctl/ctlmodel.py

all: run

run: run-demos run-tests run-c

run-demos:
	@for f in $(DEMOS); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done
	@echo "== verification/presburger/presburger.py --demo =="
	@$(PYTHON) verification/presburger/presburger.py --demo

run-tests:
	@echo "== verification/presburger/test_presburger.py =="
	@$(PYTHON) verification/presburger/test_presburger.py

run-c:
	@echo "== verification/presburger/presburger.c =="
	@$(CC) -std=c99 -o verification/presburger/presburger verification/presburger/presburger.c && verification/presburger/presburger
	@echo
	@echo "== verification/model/vmmodel.c =="
	@$(CC) -O2 -o verification/model/vmmodel verification/model/vmmodel.c && verification/model/vmmodel

run-z3:
	@for f in simple.py sym_regvm.py verify_rate_limiter.py; do \
	  echo "== verification/z3/$$f =="; \
	  ( cd verification/z3 && $(PYTHON) $$f ) || exit 1; echo; \
	done

clean:
	@rm -f verification/presburger/presburger verification/model/vmmodel
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@echo "ch11 clean."
