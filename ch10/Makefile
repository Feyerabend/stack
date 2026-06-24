.PHONY: all run run-demos run-tests run-hoare run-jvm clean

PYTHON := python3

# Chapter 10 — Abstract Machines and Operational Semantics.
# `make run` runs the self-contained Python demos (the SECD / CEK / Krivine /
# small-step machines, the §10.4 small-step-to-CEK derivation, the WAM, and the
# miniature Prolog), the Prolog test suites, the Hoare-logic C examples, and the
# JDK-less JVM "Example". `make run-jvm` compiles and runs the Java examples,
# which needs a JDK (see vm-theory/code/jvm/README.md).

# Self-demoing Python scripts (no arguments). mprolog.py is an interactive REPL
# and so is intentionally left out of the batch run.
DEMOS := \
  vm-theory/code/secd/secd.py \
  vm-theory/code/cek/cek.py \
  vm-theory/code/krivine/krivine.py \
  vm-theory/code/smallstep/smallstep.py \
  vm-theory/code/cost/cost.py \
  vm-theory/code/simulation/simulation.py \
  vm-theory/code/wam/wam.py \
  04_derivation/derivation.py \
  06_prolog/sprolog.py

TESTS := \
  06_prolog/test_cut.py \
  06_prolog/test_mprolog_cut.py \
  06_prolog/nlp/test_nlp_parser.py

all: run

run: run-demos run-tests run-hoare
	@echo "== jvm: Example (no JDK needed) =="
	@cd vm-theory/code/jvm && $(PYTHON) main.py Example .

run-demos:
	@for f in $(DEMOS); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

run-tests:
	@for f in $(TESTS); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

run-hoare:
	@echo "== hoare/c =="
	@$(MAKE) -C vm-theory/code/hoare/c --no-print-directory run

run-jvm:
	@$(MAKE) -C vm-theory/code/jvm --no-print-directory run

clean:
	@$(MAKE) -C vm-theory/code/hoare/c --no-print-directory clean 2>/dev/null || true
	@$(MAKE) -C vm-theory/code/jvm --no-print-directory clean 2>/dev/null || true
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@echo "ch10 clean."
