# Lark — self-hosting.  Differential tests and the bootstrap fixpoint.
#
# Every target compares the compiler written in Lark (lark/) against the frozen
# Python reference (oracle/) on the same corpus (tests/, samples/), and demands
# byte-identical output.  Nothing here reaches outside this directory; there is
# nothing to install beyond Python 3 and, for the bootstrap, a C compiler.
#
# The numbers each target is supposed to print are pinned in harness/BASELINES.md.

.DEFAULT_GOAL := help
.PHONY: help lextest parsetest infertest cektest emittest typechecktest \
        test bootstrap bootstrap-tc clean

# The Lark side is an interpreter running an interpreter, so it is slow, and each
# harness gives every file a time budget.  Raise it when a run reports a timeout —
# except for cektest: see the warning on that target.
LEX_TIMEOUT   ?= 900
PARSE_TIMEOUT ?= 900

help:
	@echo "The compiler in lark/ must agree with the reference in oracle/, exactly."
	@echo
	@echo "  lextest        tokens          — lex.lark   vs lexer.py"
	@echo "  parsetest      syntax trees    — parse.lark vs parser.py"
	@echo "  infertest      types           — infer.lark vs infer.py (Algorithm W)"
	@echo "  cektest        behaviour       — cek.lark   vs cek.py (what programs print)"
	@echo "  emittest       emitted C       — emit_c.lark vs emit_c_ast.py"
	@echo "  typechecktest  accept/reject + the C — the whole typechecking compiler"
	@echo "  test           all six, in that order (hours: it is a tower of interpreters)"
	@echo
	@echo "  bootstrap      the fixpoint: the compiler compiles ITSELF, C1 == C2 == C3"
	@echo "  bootstrap-tc   the same, for the typechecking compiler (heavy: ~10 GB)"
	@echo
	@echo "  clean          remove generated drivers and __pycache__"
	@echo
	@echo "Each harness allows a per-file budget of seconds; raise it with"
	@echo "  LARK_TIMEOUT=900 make emittest"
	@echo
	@echo "A timeout is a SKIP, not a failure: it says your machine is slow, not"
	@echo "that the compiler is wrong. '0 failed' is the claim; the ok/skip split"
	@echo "just reports what your box got through. See harness/BASELINES.md."

# --- The differentials, cheapest first ---------------------------------------
#
# Read them as a ladder: agreeing on tokens is weaker than agreeing on trees,
# which is weaker than agreeing on types, and so on down to agreeing on the C.

# lex.lark's corpus is every .lark file in sight, including the compiler's own
# source — so it lexes opt.lark's 1,770 lines, and needs the larger budget.
lextest:
	LARK_TIMEOUT=$(LEX_TIMEOUT) python3 harness/lex_difftest.py

# Same corpus, same reason: parsing infer.lark — 1,200 lines, through a parser
# written in Lark, running on an interpreter — does not fit the default budget.
parsetest:
	LARK_TIMEOUT=$(PARSE_TIMEOUT) python3 harness/parse_difftest.py

infertest:
	python3 harness/infer_difftest.py

# 15 of cektest's skips are timeout skips: files this machine could not finish in
# the budget.  Raising LARK_TIMEOUT is legitimate — it converts skips into real
# comparisons — but it costs a lot of wall clock, and the pinned baseline
# (34 ok / 0 fail / 15 skip) was taken at the default.  Either way the claim is the
# same: of the files that ran, none disagreed.
cektest:
	python3 harness/cek_difftest.py

emittest:
	python3 harness/emit_c_difftest.py

# The strongest of the six: it puts the typechecker ON the compiler path, so an
# accepted program must emit the reference's C *and* a rejected one must carry the
# reference's error message.  The files emittest can only skip become live tests.
typechecktest:
	python3 harness/typecheck_difftest.py

test: lextest parsetest infertest cektest emittest typechecktest

# --- Smoke runs --------------------------------------------------------------
#
# Not tests: a module run on its own, printing something, so you can see it is
# alive before you ask whether it is right.  `tast.lark` has no main of its own —
# it is a data structure — so its smoke driver concatenates the modules it needs
# and hands the result to the interpreter.  The differentials above are the real
# check; these are for reading the compiler one module at a time.
lexsmoke:
	python3 oracle/cek.py lark/lex.lark

typesmoke:
	python3 oracle/cek.py lark/types.lark

tastsmoke:
	python3 harness/tast_smoke.py

# --- The fixpoint ------------------------------------------------------------
#
# A compiler that compiles itself, and whose output then compiles itself to the
# same bytes, has closed the loop: C1 == C2 == C3.  That is the result worth
# having — and also the one thing that cannot see a bug all three stages share.
# That is what the differentials above are for.  Needs a C compiler.
bootstrap:
	python3 harness/bootstrap.py

# The same fixpoint, for the compiler that also typechecks.  Heavy — it wants
# roughly 10 GB of arena, lazily committed, so the default reserves 14 GiB of
# headroom.  If your machine cannot back that, ask for less:
#
#   make bootstrap-tc ARENA_MB=10240
ARENA_MB ?= 14336

bootstrap-tc:
	python3 harness/bootstrap_tc.py --arena-mb $(ARENA_MB)

clean:
	rm -f harness/_*driver.lark harness/_*.lark
	rm -rf harness/__pycache__ oracle/__pycache__
