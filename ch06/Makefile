.PHONY: all run clean

PYTHON := python3

# Each entry is a self-contained, self-demoing script.
#   - naive_eval.py prints two correct results then a deliberate RecursionError
#     (handled, exit 0) — the failure that motivates the CEK machine of §6.4.
#   - 01/attribute.py self-demos; the 02 and 03 demos live in test_attribute.py.
PY := \
  01_tree_walking/naive_eval.py \
  03_attribute_grammars/01/attribute.py \
  03_attribute_grammars/02/test_attribute.py \
  03_attribute_grammars/03/test_attribute.py

all: run

run:
	@for f in $(PY); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

clean:
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
