# formal/proof — build the lcore kernel and check the Lark metatheory + V3 proofs.
#
#   make            build lcore, run all proof files, fail on any error   (= make check)
#   make check      same
#   make meta       the four Phase-5b metatheory files only
#   make repl       build lcore and drop into its REPL
#
# lcore is a REPL: it prints "type error: ..." and KEEPS GOING with exit 0,
# so a bare pipe would go green on a broken proof. The check target greps
# the transcript for error lines and fails loudly on any.

LCORE     = code/core/lcore

META      = lark/lark-typing.lcore \
            lark/lark-subst.lcore \
            lark/lark-step.lcore \
            lark/lark-preservation.lcore

FILES     = $(META) \
            lark/lark-refine.lcore

# Anything lcore says when a definition does not check.
ERRPAT    = error|failed|cannot|not a function

check: lcore-build
	@$(call run-pipe,$(FILES))

meta: lcore-build
	@$(call run-pipe,$(META))

# strands/ — exploratory climbs past the V3 summit (see strands/README.md).
# Each keeps its own green bar so it never pollutes the main 5/0 check.
denot: lcore-build
	@$(call run-pipe,$(FILES) strands/denot/lark-denot.lcore)

# The denot strand's negative controls: every :let is a lie, so a PASS here
# means exactly 8 error lines (4 controls × 2 lines). Inverts run-pipe.
denot-controls: lcore-build
	@out=$$(cat $(FILES) strands/denot/lark-denot.lcore strands/denot/controls.lcore | grep -v '^--' | grep -v '^[[:space:]]*$$' | $(LCORE) 2>&1); \
	errs=$$(printf '%s\n' "$$out" | grep -icE 'type error|failed'); \
	if [ "$$errs" -eq 8 ]; then \
	  echo "OK: 4/4 denot controls refused"; \
	else \
	  echo "FAIL: expected 8 control error lines, got $$errs"; exit 1; \
	fi

solver: lcore-build
	@$(call run-pipe,$(FILES) strands/solver/lark-solver.lcore)

# Solver strand controls: 8 lies (4 interval + 4 congruence-closure) → 16 error lines.
solver-controls: lcore-build
	@out=$$(cat $(FILES) strands/solver/lark-solver.lcore strands/solver/controls.lcore | grep -v '^--' | grep -v '^[[:space:]]*$$' | $(LCORE) 2>&1); \
	errs=$$(printf '%s\n' "$$out" | grep -icE 'type error|failed'); \
	if [ "$$errs" -eq 16 ]; then \
	  echo "OK: 8/8 solver controls refused"; \
	else \
	  echo "FAIL: expected 16 control error lines, got $$errs"; exit 1; \
	fi

vdeep: lcore-build
	@$(call run-pipe,$(FILES) strands/vdeep/lark-vdeep.lcore)

# Vdeep strand controls: 4 lies → expect exactly 8 error lines.
vdeep-controls: lcore-build
	@out=$$(cat $(FILES) strands/vdeep/lark-vdeep.lcore strands/vdeep/controls.lcore | grep -v '^--' | grep -v '^[[:space:]]*$$' | $(LCORE) 2>&1); \
	errs=$$(printf '%s\n' "$$out" | grep -icE 'type error|failed'); \
	if [ "$$errs" -eq 8 ]; then \
	  echo "OK: 4/4 vdeep controls refused"; \
	else \
	  echo "FAIL: expected 8 control error lines, got $$errs"; exit 1; \
	fi

# affine strand: the A in "Lambda Affine Resource Kernel" — resource soundness,
# independent of the refinement layer (reuses only Ty from lark-typing.lcore).
affine: lcore-build
	@$(call run-pipe,lark/lark-typing.lcore strands/affine/lark-affine.lcore)

# Affine strand controls: 4 lies (double-use, non-consuming var, resurrection,
# threaded reuse) → expect exactly 8 error lines.
affine-controls: lcore-build
	@out=$$(cat lark/lark-typing.lcore strands/affine/lark-affine.lcore strands/affine/controls.lcore | grep -v '^--' | grep -v '^[[:space:]]*$$' | $(LCORE) 2>&1); \
	errs=$$(printf '%s\n' "$$out" | grep -icE 'type error|failed'); \
	if [ "$$errs" -eq 8 ]; then \
	  echo "OK: 4/4 affine controls refused"; \
	else \
	  echo "FAIL: expected 8 control error lines, got $$errs"; exit 1; \
	fi

repl: lcore-build
	cd code/core && ./lcore

lcore-build:
	@$(MAKE) -C code/core

# $(1) = list of .lcore files. Strips comment/blank lines, pipes to lcore,
# fails (exit 1) with the offending lines if the transcript mentions an error.
define run-pipe
	out=$$(cat $(1) | grep -v '^--' | grep -v '^[[:space:]]*$$' | $(LCORE) 2>&1); \
	errs=$$(printf '%s\n' "$$out" | grep -icE '$(ERRPAT)'); \
	if [ "$$errs" -ne 0 ]; then \
	  printf '%s\n' "$$out" | grep -inE -A2 '$(ERRPAT)'; \
	  echo "FAIL: $$errs error line(s) across $(words $(1)) file(s)"; \
	  exit 1; \
	else \
	  echo "OK: $(words $(1)) files, 0 errors"; \
	fi
endef

.PHONY: check meta repl lcore-build denot denot-controls solver solver-controls vdeep vdeep-controls affine affine-controls
