.PHONY: all run bugs certificate stack fuzz clean

# Chapter 13 — The Adversary.
# `make run` reproduces the chapter's bugs as live diagnostics, plants a
# mutation in the register allocator and watches the certificate catch it,
# and runs the seven-file proof stack green — then red, twice, on planted
# lies. Everything drives the real artifacts in lark/09/ and
# lark/formal/proof/; nothing is duplicated here.

# The lark tree sits either beside this chapter (stack layout: ../lark)
# or two levels up (book layout: ../..).
LARK := $(firstword $(wildcard ../lark/09) $(wildcard ../../09))

all: run

run: bugs certificate stack

bugs:
	@sh bugs/run_bugs.sh

certificate:
	@python3 certificate/demo_certificate.py

stack:
	@sh proofstack/run_stack.sh

# A short live run of the differential fuzzer (P6 + P7 on 25 generated
# programs). Needs Hypothesis: pip install hypothesis
fuzz:
	@test -n "$(LARK)" || { echo "error: cannot find lark/09"; exit 1; }
	@$(MAKE) -C $(LARK) --no-print-directory fuzz N=25

clean:
	@find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@echo "ch13 clean."
