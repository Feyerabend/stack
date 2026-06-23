GRAMMAR  = docs/grammar.ebnf
SRC      = src
TESTS    = tests
PYTHON   = python3

.PHONY: help check lex parse typecheck lower tac_vm asm lint test run clean

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
	@echo "  make test               — run test suite"
	@echo "  make run                — start REPL (coming)"
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

run:
	@echo "REPL: not yet implemented"
# $(PYTHON) $(SRC)/repl.py

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	@echo "clean"
