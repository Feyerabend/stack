# Lark — top-level orchestration.
#
# Two trees live here.  You EDIT the dev tree under dev/; a generator derives the
# reader tree under repo/ (what the book cites and what goes public).  The whole
# story is two commands: regenerate, then check that nothing drifted.
#
#   dev/     07/ 08/ self/ prove/ formal/   edit here
#   repo/    self/ optimize/ prove/         GENERATED from dev/ — never hand-edit
#   book/    the LaTeX book                 cites repo/ paths only
#   tools/   mkrepo.py (the generator), oracle_drift.sh (the frozen-oracle audit)

PY := python3

.DEFAULT_GOAL := help
.PHONY: help repo check drift book prove formal test view clean

help:
	@echo "Lark — edit dev/, regenerate repo/, keep the two in sync."
	@echo
	@echo "  repo    regenerate the reader tree repo/ from dev/   (tools/mkrepo.py)"
	@echo "  check   fail if repo/ drifted from dev/, then run the book path & ref lints"
	@echo "  drift   audit the frozen oracle (dev/07/src) against its pristine baseline"
	@echo "  book    build the book PDF (its recipe runs the lints, then tectonic)"
	@echo "  prove   run the refinement checker over all 75 fixtures (repo/prove)"
	@echo "  formal  check the Lark soundness proof (dev/formal/proof)"
	@echo "  test    check + prove + formal"
	@echo "  view    build & open the offline Lark source viewer   (tools/larkview.py)"
	@echo "  clean   remove the book's build artifacts"

# ── The two-command story ─────────────────────────────────────────────────────

repo:
	@$(PY) tools/mkrepo.py

# `mkrepo.py --check` exits non-zero if repo/ has drifted; the two book lints exit
# non-zero on a dead path citation or a typed chapter numeral.  Any one of them
# failing fails the target.
check:
	@$(PY) tools/mkrepo.py --check
	@$(PY) book/tools/checkpaths.py
	@$(PY) book/tools/checkrefs.py

# Informational: prints the oracle's added/modified/deleted ledger since PRISTINE.
# Read it against ORACLE.md — a longer list than that one means the ledger is stale.
drift:
	@bash tools/oracle_drift.sh

# ── Build / run the strands ───────────────────────────────────────────────────

book:
	@$(MAKE) -C book book

prove:
	@$(MAKE) -C repo/prove prove

formal:
	@$(MAKE) -C dev/formal/proof check

test: check prove formal

# Bundle every repo/ .lark file into one standalone HTML page and open it. The
# page runs from file:// — no server, no network — and also accepts drag-dropped
# .lark files. Re-run to refresh the bundled list.
view:
	@$(PY) tools/larkview.py

clean:
	@$(MAKE) -C book clean
