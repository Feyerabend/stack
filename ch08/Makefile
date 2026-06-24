.PHONY: all run run-passes run-measuring lark-bench clean

PYTHON := python3
CC     := cc
CFLAGS := -O2

# Chapter 8 — Optimization.
# `make run` runs every section's companion: the section 8.1-8.5 passes (each a
# self-contained, no-argument Python script) and the section 8.6 measuring
# examples (the two C benchmarks plus the quick Python ones). The headline 8.6
# benchmark, lark_bench.py, drives the real lark/06 backends and takes ~30s, so
# it has its own target and is not part of `run`.

# §8.1-§8.5 — one self-demoing script per pass.
PASSES := \
  01_meaning/equiv_check.py \
  02_constant_folding/constant_fold.py \
  02_constant_folding/propagator.py \
  03_dead_code/dead_code.py \
  03_dead_code/reachability.py \
  04_simplification/expression_simplifier.py \
  05_licm/licm.py

# §8.6 — the quick Python benchmarks (lark_bench.py is run via `make lark-bench`).
MEASURE_PY := \
  06_measuring/io.py \
  06_measuring/strings.py \
  06_measuring/data_struct.py \
  06_measuring/network.py \
  06_measuring/parallel.py

all: run

run: run-passes run-measuring

run-passes:
	@for f in $(PASSES); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

run-measuring:
	@echo "== 06_measuring/compiler.c =="
	@$(CC) $(CFLAGS) -o 06_measuring/compiler 06_measuring/compiler.c && ./06_measuring/compiler
	@echo "== 06_measuring/memory.c =="
	@$(CC) $(CFLAGS) -o 06_measuring/memory 06_measuring/memory.c && ./06_measuring/memory
	@for f in $(MEASURE_PY); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

# §8.6 headline: sum_to through Lark's three backends (~30s).
lark-bench:
	@$(PYTHON) 06_measuring/lark_bench.py

clean:
	@rm -f 06_measuring/compiler 06_measuring/memory
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@echo "ch08 clean."
