GRAMMAR  = docs/grammar.ebnf
SRC      = src
TESTS    = tests
PYTHON   = python3

.PHONY: help check lex lint test run clean

help:
	@echo "Lark build targets"
	@echo "  make check        — verify expected files are present"
	@echo "  make lex          — lex all acceptance tests, report token counts"
	@echo "  make lex FILE=f   — lex a single file and print tokens"
	@echo "  make lint         — check grammar and source (coming)"
	@echo "  make test         — run test suite (coming)"
	@echo "  make run          — start REPL (coming)"
	@echo "  make clean        — remove build artefacts"

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

lint:
	@echo "EBNF linter: not yet implemented"
# $(PYTHON) src/lint_grammar.py $(GRAMMAR)

test:
	@echo "Test suite: not yet implemented"
# $(PYTHON) -m pytest $(TESTS)/

run:
	@echo "REPL: not yet implemented"
# $(PYTHON) $(SRC)/repl.py

clean:
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	@echo "clean"
