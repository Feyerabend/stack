# Lark — the optimizing back end.  Differential tests and the self-application fixpoint.
#
# Same discipline as the self-hosting strand: every target runs the Lark
# implementation (lark/)
# and the frozen Python reference (oracle/) on the same input and demands
# byte-identical output.  Here the input is TAC — the three-address code the
# compiler optimizes — so both sides are fed the SAME lowered program and must
# agree on what comes out.
#
# Expected numbers: harness/BASELINES.md.

.DEFAULT_GOAL := help
.PHONY: help lowertest emittactest opttest optcompilertest test fixpoint clean

help:
	@echo "An optimizer earns its name only if the program still means the same thing."
	@echo
	@echo "  lowertest        typed AST -> TAC     — lower.lark      vs lower.py"
	@echo "  emittactest      TAC -> C             — emit_tac_c.lark vs emit_tac_c.py"
	@echo "  opttest          TAC -> TAC           — opt.lark        vs opt.py,"
	@echo "                                          at EVERY level -O0 .. -O3"
	@echo "  optcompilertest  end to end           — the optimized compiler still"
	@echo "                                          prints what the reference prints"
	@echo "  test             all four"
	@echo
	@echo "  fixpoint         the optimizing compiler optimizes ITSELF to a fixed"
	@echo "                   point: C1 == C2 == C3 (heavy; wants ~15 GB of arena,"
	@echo "                   lazily committed, and a C compiler)"
	@echo
	@echo "  clean            remove generated drivers and __pycache__"
	@echo
	@echo "Per-file budget: LARK_TIMEOUT=900 make opttest"

# --- The differentials -------------------------------------------------------
#
# lowertest and emittactest feed both sides the UNOPTIMIZED TAC, which isolates
# the one module under test.  opttest is the pass that puts the optimizer itself
# on the differential: both sides run the passes, at every level, and the
# optimized TAC must come out byte for byte the same.

# The optimizer lowers a *typed* AST, so the whole front end is on this strand's path
# too — and it is checked here, against the same oracle the `self` strand uses.  A
# strand you can only half-check is not self-contained.
#
# lex/parse sweep every .lark file in sight, including the compiler's own source, so
# they need the larger budget: opt.lark alone is 1,770 lines.
LEX_TIMEOUT   ?= 900
PARSE_TIMEOUT ?= 900

lextest:
	LARK_TIMEOUT=$(LEX_TIMEOUT) python3 harness/lex_difftest.py

parsetest:
	LARK_TIMEOUT=$(PARSE_TIMEOUT) python3 harness/parse_difftest.py

infertest:
	python3 harness/infer_difftest.py

lowertest:
	python3 harness/lower_difftest.py

emittactest:
	python3 harness/emit_tac_c_difftest.py

opttest:
	python3 harness/opt_difftest.py

# The behavioural claim, which is the one that matters to a user: whatever the
# optimizer did, the program still prints exactly what it printed before.
optcompilertest:
	python3 harness/optcompiler_difftest.py

test: lextest parsetest infertest lowertest emittactest opttest optcompilertest

# --- Smoke runs --------------------------------------------------------------
#
# Not tests: a module run on its own so you can watch it work.  `tac.lark` and
# `tast.lark` are data structures with no main of their own, so each smoke driver
# concatenates the modules it needs and hands the result to the interpreter —
# `tacsmoke` builds a small TAC program by hand and pretty-prints it, which is the
# quickest way to see the IR this whole strand is about.
tacsmoke:
	python3 harness/tac_smoke.py

tastsmoke:
	python3 harness/tast_smoke.py

# --- The self-application fixpoint -------------------------------------------
#
# The optimizing compiler, at -O3, compiling its own ~7,500 lines — and the C it
# emits, rebuilt and run again, emits the same C.  Bake a different level in with
#   make fixpoint LEVEL=1
LEVEL ?= 3
ARENA_MB ?= 15000

fixpoint:
	python3 harness/bootstrap_opt.py --level $(LEVEL) --arena-mb $(ARENA_MB)

clean:
	rm -f harness/_*driver.lark harness/_*.lark
	rm -rf harness/__pycache__ oracle/__pycache__
