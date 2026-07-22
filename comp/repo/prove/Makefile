# Lark — proof.  Two strengths of assurance, in one tree.
#
# The other two strands test: they run the compiler on inputs and compare. This
# one PROVES.  Two ways:
#
#   the refinement checker (oracle/, fixtures/, harness/) — checks, for every
#   input, that a program's declared conditions cannot be violated.  Python only.
#
#   the soundness proof (lcore/, lark-formal/) — states what a Lark program's type
#   *means* and checks, once and for all inputs, that a well-typed program cannot
#   go wrong.  `lcore` is the checker, about 4,000 lines of C, small enough to
#   read: everything under it is only as trustworthy as that binary.

.DEFAULT_GOAL := help
.PHONY: help prove adversary solver lcore llang selftest proofs pdf test clean

PY      := python3
LCORE   := lcore/core/lcore
LLANG   := lcore/lang/llang

# Order matters — each file uses what the ones before it defined.
PROOFS  := lark-formal/lark-typing.lcore \
           lark-formal/lark-subst.lcore \
           lark-formal/lark-step.lcore \
           lark-formal/lark-preservation.lcore

help:
	@echo "A test says the compiler got THESE inputs right. A proof says it cannot"
	@echo "get any input wrong."
	@echo
	@echo "  The refinement checker (Python only, no build):"
	@echo "  prove     check all 75 fixtures against their pinned verdicts"
	@echo "  adversary generate adversarial programs and try to fool the checker"
	@echo "  solver    fuzz the from-scratch solver against brute force"
	@echo
	@echo "  The soundness proof (builds the C kernel):"
	@echo "  lcore     build the proof checker (~4,000 lines of C)"
	@echo "  llang     build the surface language on top of it"
	@echo "  selftest  the kernel's own test suite (339 cases)"
	@echo "  proofs    CHECK THE SOUNDNESS PROOF for Lark — the typing rules, the"
	@echo "            evaluation rules, the substitution lemma, and preservation:"
	@echo "            a well-typed program that takes a step stays well-typed,"
	@echo "            so it never gets stuck"
	@echo "  pdf       typeset the written account (needs tectonic)"
	@echo
	@echo "  test      prove + selftest + proofs"
	@echo "  clean     remove the built binaries"

# ── The refinement checker ────────────────────────────────────────────────────
prove:
	@$(PY) harness/prove_difftest.py

adversary:
	@$(PY) harness/adversary.py

solver:
	@$(PY) harness/solver_fuzz.py

# ── The soundness proof ───────────────────────────────────────────────────────
lcore:
	$(MAKE) -C lcore/core

llang:
	$(MAKE) -C lcore/lang

selftest: lcore
	@$(LCORE) --test | tail -1

# lcore is a REPL: it reads definitions from stdin and reports each one it cannot
# check. It exits 0 either way, so we count the failures ourselves — a proof that
# does not check must not pass quietly.
#
# The four files are one development, in dependency order, with lcore's comment
# lines stripped (it has no comment syntax; the files carry theirs in `--` lines).
proofs: lcore
	@echo "checking: $(notdir $(PROOFS))"
	@cat $(PROOFS) | grep -v '^--' | grep -v '^$$' | $(LCORE) > .proof.out 2>&1; \
	 n=$$(grep -c 'failed' .proof.out || true); \
	 if [ "$$n" -eq 0 ]; then \
	   echo "ok — every definition checks. Lark's type soundness holds."; \
	   rm -f .proof.out; \
	 else \
	   echo "FAIL — $$n definition(s) did not check:"; \
	   grep 'failed' .proof.out; \
	   rm -f .proof.out; exit 1; \
	 fi

pdf:
	cd lark-formal && tectonic lark-formal.tex

test: prove selftest proofs

clean:
	$(MAKE) -C lcore/core clean
	$(MAKE) -C lcore/lang clean
	rm -f .proof.out
