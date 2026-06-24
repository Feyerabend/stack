.PHONY: all run repl bridge clean

# Chapter 12 — Types as Proofs.
# `make run` builds the lcore kernel and the llang graph reducer, runs the
# kernel's test suite, exercises llang on the standard library and a sample, and
# runs the Lark <-> MLTT bridge. `make repl` starts the lcore REPL; `make bridge`
# runs just the bridge (it uses the kernel committed under lark/formal/proof/).

CORE := kernel/code/core
LANG := kernel/code/lang

all: run

run:
	@echo "== build + test the lcore kernel =="
	@$(MAKE) -C $(CORE) --no-print-directory
	@$(CORE)/lcore --test 2>/dev/null | tail -1   # negative tests print expected errors to stderr
	@echo
	@echo "== build llang, load the stdlib, reduce plus_comm 2 3 =="
	@$(MAKE) -C $(LANG) --no-print-directory
	@printf ':load "lib/prelude.lam"\nplus_comm (succ (succ zero)) (succ (succ (succ zero)))\n' \
	  | ( cd $(LANG) && ./llang ) | grep -E 'loaded|normal' | tail -6
	@echo
	@echo "== llang sample: samples/factorial.lam =="
	@printf ':load "samples/factorial.lam"\n' | ( cd $(LANG) && ./llang ) | grep -E 'loaded|normal' | tail -5
	@echo
	@echo "== Lark <-> MLTT bridge =="
	@sh bridge/run_bridge.sh | grep -E 'id_bool|ite_int|apply_f|inferred:|expected:|one activity'

repl:
	@$(MAKE) -C $(CORE) --no-print-directory && $(CORE)/lcore

bridge:
	@sh bridge/run_bridge.sh

clean:
	@$(MAKE) -C $(LANG) --no-print-directory clean 2>/dev/null || true
	@find . -name '*.dSYM' -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name '.DS_Store' -delete 2>/dev/null || true
	@echo "ch12 clean. (kept the committed kernel binary $(CORE)/lcore)"
