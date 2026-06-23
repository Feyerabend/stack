GRAMMAR  = docs/grammar.ebnf
SRC      = src
TESTS    = tests
PYTHON   = python3
CC       = cc
CFLAGS   = -std=c11 -O2 -Wall -Wextra -Wno-unused-parameter

# Intermediate files produced by the C CEK build
CEK_PROG_C = /tmp/lark_prog.c
CEK_BIN    = /tmp/larkrun
CEK_SRCS   = $(SRC)/cek.c $(SRC)/larkrun.c

.PHONY: help check lex parse typecheck lower tac_vm asm lint test \
        difftest proptest cekbuild cektest repl repltest samples run clean

help:
	@echo "Lark build targets"
	@echo "  make check              — verify expected files are present"
	@echo "  make lex                — lex all acceptance tests, report token counts"
	@echo "  make lex FILE=f         — lex a single file and print tokens"
	@echo "  make parse              — parse all acceptance tests, report decl counts"
	@echo "  make parse FILE=f       — parse a single file and print AST"
	@echo "  make typecheck          — type-check all acceptance tests"
	@echo "  make typecheck FILE=f   — type-check a single file and print typed AST"
	@echo "  make lower FILE=f       — lower a single file and print TAC"
	@echo "  make tac_vm FILE=f      — run a single file through the TAC VM"
	@echo "  make asm FILE=f [OUT=o] — compile a single file to RISC-V assembly (.S)"
	@echo "  make lint               — check grammar and source (coming)"
	@echo "  make test               — run test suite (per-backend, checks expected output)"
	@echo "  make difftest           — cross-backend diff: assert all backends agree"
	@echo "  make proptest           — property-based tests via Hypothesis (type checker)"
	@echo "  make cekbuild FILE=f    — emit C AST, compile, and run a single file via C CEK"
	@echo "  make cektest            — run all corpus files through C CEK, diff vs Python CEK"
	@echo "  make repl               — start interactive REPL"
	@echo "  make repltest           — run REPL smoke tests (31 piped checks)"
	@echo "  make samples            — run all samples/ programs and print output"
	@echo "  make clean              — remove build artefacts"

check:
	@test -f $(GRAMMAR) \
		&& echo "  ok  $(GRAMMAR)" \
		|| echo "  missing  $(GRAMMAR)"
	@test -d $(SRC) \
		&& echo "  ok  $(SRC)/" \
		|| echo "  missing  $(SRC)/"
	@test -d $(TESTS) \
		&& echo "  ok  $(TESTS)/" \
		|| echo "  missing  $(TESTS)/"

lex:
ifdef FILE
	$(PYTHON) $(SRC)/lexer.py $(FILE)
else
	@for f in $(TESTS)/0*.lark $(TESTS)/09_modules/*.lark; do \
		printf "  %-40s " "$$f"; \
		$(PYTHON) $(SRC)/lexer.py "$$f" 2>&1 | tail -1; \
	done
endif

parse:
ifdef FILE
	$(PYTHON) $(SRC)/parser.py $(FILE)
else
	@for f in $(TESTS)/0*.lark $(TESTS)/09_modules/*.lark; do \
		printf "  %-42s " "$$f"; \
		$(PYTHON) $(SRC)/parser.py "$$f" 2>&1 | tail -1; \
	done
endif

typecheck:
ifdef FILE
	$(PYTHON) $(SRC)/infer.py $(FILE)
else
	@ok=0; fail=0; \
	for f in $(TESTS)/0*.lark $(TESTS)/09_modules/*.lark; do \
		printf "  %-42s " "$$f"; \
		if $(PYTHON) $(SRC)/infer.py "$$f" > /dev/null 2>&1; then \
			echo "ok"; ok=$$((ok+1)); \
		else \
			$(PYTHON) $(SRC)/infer.py "$$f" 2>&1 | head -1; fail=$$((fail+1)); \
		fi; \
	done; \
	echo ""; echo "  $$ok passed, $$fail failed"
endif

lower:
ifdef FILE
	$(PYTHON) $(SRC)/lower.py $(FILE)
else
	@echo "usage: make lower FILE=<path>"
endif

tac_vm:
ifdef FILE
	$(PYTHON) $(SRC)/tac_vm.py $(FILE)
else
	@echo "usage: make tac_vm FILE=<path>"
endif

asm:
ifdef FILE
	$(PYTHON) $(SRC)/asm.py $(FILE) $(if $(OUT),$(OUT),)
else
	@echo "usage: make asm FILE=<path> [OUT=<output.S>]"
endif

lint:
	@echo "EBNF linter: not yet implemented"
# $(PYTHON) src/lint_grammar.py $(GRAMMAR)

test:
	$(PYTHON) $(TESTS)/run_tests.py

difftest:
	$(PYTHON) $(TESTS)/diff_test.py

proptest:
	$(PYTHON) -m pytest $(TESTS)/gen.py -v

# ── C CEK targets ──────────────────────────────────────────────────────────

# Emit C AST for FILE, compile it with cek.c + larkrun.c, and run.
cekbuild:
ifdef FILE
	$(PYTHON) $(SRC)/emit_c_ast.py $(FILE) $(CEK_PROG_C)
	$(CC) $(CFLAGS) -I$(SRC) $(CEK_SRCS) $(CEK_PROG_C) -o $(CEK_BIN) -lm
	$(CEK_BIN)
else
	@echo "usage: make cekbuild FILE=<path.lark>"
endif

# Run all corpus files through the C CEK and diff output against the Python CEK.
cektest:
	$(PYTHON) $(TESTS)/cek_test.py

repl:
	$(PYTHON) $(SRC)/repl.py

repltest:
	$(PYTHON) $(TESTS)/repl_test.py

samples:
	@for f in samples/*.lark; do \
		echo "=== $$f ==="; \
		$(PYTHON) $(SRC)/tac_vm.py "$$f"; \
		echo; \
	done

run: repl

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	@echo "clean"
