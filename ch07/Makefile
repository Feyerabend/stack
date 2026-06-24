.PHONY: all run clean \
        run-ir run-tac run-cfg run-ssa run-dag

PYTHON := python3

# Chapter 7 — Intermediate Representations.
# `make run` runs one self-contained, non-interactive demo per section,
# delegating to each section's own Makefile where one exists. The interactive
# demos (02_tac/demo/tac_generator.py and tac_interpreter.py) are left out of
# `run` on purpose; run them by hand to step through their prompts.

all: run

run: run-ir run-tac run-cfg run-ssa run-dag

# §7.1 — AST -> ILOC -> RISC-V -> binary, then execute (prints 8, 30, 38).
run-ir:
	@echo "== 01_ir: ILOC -> RISC-V pipeline =="
	@$(MAKE) -C 01_ir/iloc --no-print-directory run

# §7.2 — TAC: the C generator, the lambda->TAC compiler + tests, constant folding.
run-tac:
	@echo "== 02_tac/demo: TAC generator (C) =="
	@$(MAKE) -C 02_tac/demo --no-print-directory run-c
	@echo "== 02_tac/lambda: lambda -> TAC tests =="
	@$(PYTHON) 02_tac/lambda/tests.py
	@echo "== 02_tac/optimise: constant folding over TAC =="
	@$(PYTHON) 02_tac/optimise/folding.py

# §7.3 — Control-flow graphs: build CFGs and run the compiled test programs.
run-cfg:
	@echo "== 03_cfg/compiler: tiny C compiler, all tests =="
	@$(MAKE) -C 03_cfg/compiler --no-print-directory all-tests

# §7.4 — SSA: build the SSA compiler and run its test suite.
run-ssa:
	@echo "== 04_ssa/compiler: SSA compiler test suite =="
	@$(MAKE) -C 04_ssa/compiler --no-print-directory test
	@echo "== 04_ssa/demo: SSA pipeline in Python =="
	@$(PYTHON) 04_ssa/demo/compiler.py >/dev/null && echo "  ok"

# §7.5 — DAG / common-subexpression elimination (naive vs DAG, verified equal).
run-dag:
	@echo "== 05_dag/compiler: CSE via DAG (naive vs DAG) =="
	@$(PYTHON) 05_dag/compiler/compiler.py | tail -12

clean:
	@$(MAKE) -C 01_ir/iloc --no-print-directory clean 2>/dev/null || true
	@$(MAKE) -C 02_tac/demo --no-print-directory clean 2>/dev/null || true
	@$(MAKE) -C 03_cfg/compiler --no-print-directory clean 2>/dev/null || true
	@$(MAKE) -C 04_ssa/compiler --no-print-directory clean 2>/dev/null || true
	@rm -f 02_tac/simple/tac 03_cfg/demo/mini_cfg
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@echo "ch07 clean."
