.PHONY: all run run-py run-c run-sub clean

PYTHON := python3
CC     ?= cc
CFLAGS ?= -std=c11 -Wall -Wextra -O2

# Standalone Python demos (each is self-contained and prints to stdout).
PY := \
  01_symtable/functional.py 01_symtable/logic.py 01_symtable/procedural.py \
  04_lambda_calculus/calculus/lambda.py \
  04_lambda_calculus/calculus/hm.py \
  04_lambda_calculus/calculus/generics.py \
  04_lambda_calculus/calculus/recur.py \
  04_lambda_calculus/typesys/type_systems.py \
  06_affine/affine/affine.py

# Standalone C demos: each source builds to a binary next to it.
CSRC := 04_lambda_calculus/typesys/type_systems.c \
        06_affine/affine/affine.c \
        06_affine/arena/arena.c
CBIN := $(CSRC:.c=)

# Subprojects with their own Makefiles (each supports `run` and `clean`).
SUBDIRS := 06_affine/arena/compiler 06_affine/arena/css 07_traits

all: run

run: run-py run-c run-sub

run-py:
	@for f in $(PY); do echo "== $$f =="; $(PYTHON) $$f || exit 1; echo; done

run-c: $(CBIN)
	@for b in $(CBIN); do echo "== $$b =="; ./$$b || exit 1; echo; done

# Build each standalone C demo from its .c source.
%: %.c
	$(CC) $(CFLAGS) -o $@ $<

run-sub:
	@for d in $(SUBDIRS); do echo "== $$d (make run) =="; $(MAKE) -C $$d run || exit 1; echo; done

clean:
	@rm -f $(CBIN)
	@for d in $(SUBDIRS); do $(MAKE) -C $$d clean >/dev/null 2>&1 || true; done
	@find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
