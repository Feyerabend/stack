.PHONY: all run run-py run-c clean

PYTHON := python3
CC     ?= cc
CFLAGS ?= -O2 -Wall -Wextra

# Python demos, in section order.
PY := \
  02_recursive/parse.py 02_recursive/parse2.py \
  03_ll1/LL1.py \
  04_pushdown/pda.py \
  05_bottomup/aabb.py 05_bottomup/brackets.py 05_bottomup/precedence.py \
  06_alternatives/combinator/combinator.py \
  06_alternatives/earley/earley.py \
  06_alternatives/lr1/LR1.py \
  06_alternatives/packrat/packrat.py \
  06_alternatives/slr1/SLR1.py \
  07_ast/tree.py 07_ast/expr_ast.py 07_ast/recursive_ast.py 07_ast/combinator_ast.py

# C demos (binary sits next to its source).
CSRC := 02_recursive/arith.c 04_pushdown/pda.c 07_ast/packrat_ast.c
CBIN := $(CSRC:.c=)

all: run

run: run-py run-c

run-py:
	@for f in $(PY); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

run-c: $(CBIN)
	@for b in $(CBIN); do echo "== $$b =="; ./$$b || exit 1; echo; done

# Build each C demo from its .c source.
%: %.c
	$(CC) $(CFLAGS) -o $@ $<

clean:
	@rm -f $(CBIN)
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
