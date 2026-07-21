# Self-hosting Lark — build & differential test targets.
# The Python toolchain in ../07/src is the frozen oracle; each self-host module
# is validated differentially against its Python twin.  See ../SELFHOST.md.

CEK := ../07/src/cek.py

.PHONY: help lexsmoke lextest parsetest typesmoke tastsmoke tacsmoke infersmoke infertest cektest emittest typechecktest lowertest emittactest opttest optcompilertest regalloctest asmtest fuzz fuzzfast bootstrap bootstrap-tc test repo drift

help:
	@echo "Targets:"
	@echo "  lexsmoke   — run lex.lark's smoke main through the CEK interpreter"
	@echo "  lextest    — differential: lex.lark vs lexer.py over the corpus (M1)"
	@echo "  parsetest  — differential: parse.lark vs parser.py over the corpus (M2)"
	@echo "  typesmoke  — run types.lark's smoke main (ty.py port, M3 slice 1)"
	@echo "  tastsmoke  — run tast.lark's smoke (typed_tree.py port, M3 slice 2)"
	@echo "  tacsmoke   — run tac.lark's smoke (tac.py IR port, M7 slice 1)"
	@echo "  infersmoke — run infer.lark's smoke (Algorithm W, M3 slice 3)"
	@echo "  infertest  — differential: infer.lark vs infer.py over the corpus (M3)"
	@echo "  cektest    — differential: cek.lark vs cek.py over the corpus (M4)"
	@echo "  emittest   — differential: emit_c.lark vs emit_c_ast.py over the corpus (M5)"
	@echo "  typechecktest — differential: the TYPECHECKING self-host compiler (M5.5/F2⁺)"
	@echo "  lowertest  — differential: lower.lark vs lower.py, TAC serialised via tac.lark (M7.2)"
	@echo "  emittactest — differential: emit_tac_c.lark vs emit_tac_c.py, TAC → C (M7.3)"
	@echo "  opttest    — differential: opt.lark vs opt.py, optimized TAC at -O0..-O3 (M7.4)"
	@echo "  regalloctest — differential: regalloc.lark vs regalloc.py, linear-scan allocation (F3.1a)"
	@echo "  asmtest    — differential: asm.lark vs asm.py, TAC → RV32I assembly (F3.1b)"
	@echo "  fuzz       — property differential: random well-typed programs, port==oracle lex→parse→infer→emit"
	@echo "  fuzzfast   — same, front-end only (lex+parse), many programs, cheap"
	@echo "  bootstrap  — F2 fixpoint: self-hosted compiler reproduces its own C (heavy)"
	@echo "  bootstrap-tc — F2⁺ NATIVE fixpoint of the typechecking compiler (C1==C2==C3; heavy, ~10 GB arena)"
	@echo "  test       — all self-host differential tests"
	@echo "  repo       — regenerate the book's companion tree ../repo from this one"
	@echo "  drift      — check ../repo still matches this tree (and that the pins agree)"

lexsmoke:
	python3 $(CEK) lex.lark

lextest:
	python3 tests/lex_difftest.py

# parse.lark is a component (imports Lex); the harness concatenates lex+parse
# into one module before running — see the note in parse_difftest.py.
parsetest:
	python3 tests/parse_difftest.py

# M3 first slice: the ty.py port (monotypes, subst, unify, pretty, Copy).
# Smoke-validated for now; the corpus-wide differential arrives with infer.lark.
typesmoke:
	python3 $(CEK) types.lark

# M3 slice 2: the typed_tree.py port (typed AST + top-level signature printer).
# Concatenates lex+parse+types+tast and runs tast.lark's smoke main; no Python
# twin to diff (the typed AST's differential is inferred types, needs infer.lark).
tastsmoke:
	python3 tests/tast_smoke.py

# M7 slice 1: the tac.py port (three-address-code IR + byte-faithful pretty).
# tac.lark HAS a Python twin, so this smoke is a true differential: it builds
# the same program in tac.py and demands tac.lark's pretty output match byte for
# byte (concatenates lex+parse+tac; parse supplies Maybe for ICall/IReturn).
tacsmoke:
	python3 tests/tac_smoke.py

# M3 slice 3: the infer.py port (Algorithm W + affine + trait bounds).  The
# smoke checks a tiny program; infertest runs the corpus-wide differential —
# for every single-file test the inferred top-level types and the accept/reject
# verdict must match infer.py, including the error suite.  Meta-circular, so
# slow; a per-file timeout counts as skip-with-reason, and the two `import`
# files are skipped (the port has no import mechanism).
infersmoke:
	python3 tests/infer_smoke.py

infertest:
	python3 tests/infer_difftest.py

# M4: the cek.py evaluator port.  Concatenates lex+parse+cek and evaluates each
# corpus file's source, comparing stdout vs cek.py.  Slow (meta-circular): a
# per-file timeout counts as skip-with-reason, not failure — see the difftest.
cektest:
	python3 tests/cek_difftest.py

# M5: the emit_c_ast.py port (typed AST → C source).  emit_c.lark emits straight
# from parse.lark's syntactic Prog (the emitter reads structure/names/literals,
# never inferred types), so the harness concatenates lex+parse+emit_c.  The
# oracle renames wildcard params via a nondeterministic id(); that one token is
# canonicalised on both sides — see emit_c_difftest.py.  Meta-circular, so slow.
emittest:
	python3 tests/emit_c_difftest.py

# M5.5 / F2⁺: the *typechecking* self-hosted compiler.  Drives the GATED compiler
# (lex+parse+types+tast+infer+emit_c + a typecheck→reject|emit gate) over the
# corpus: an accepted program must emit the oracle-identical C, a rejected one
# must carry the oracle-identical "type error:" message.  The 7 error-suite files
# emittest can only SKIP become live acceptance tests here.  Meta-circular (a
# ~3500-line driver per file), so slow — run alone.
typechecktest:
	python3 tests/typecheck_difftest.py

# M7.2: the lower.py port (typed AST → TAC).  The oracle typechecks with infer.py,
# lowers with lower.py, and pretty-prints the TAC; the port concatenates
# lex+parse+types+tast+tac+lower and runs `tacPretty(lowerProgram(<serialised
# TProgram>))`, demanding byte-identical TAC.  Reject fixtures (infer raises) and
# import programs are skipped, as is a CEK stack overflow on a deep serialised AST.
# Meta-circular, so slow — a per-file timeout counts as skip-with-reason.
lowertest:
	python3 tests/lower_difftest.py

# M7.3: the emit_tac_c.py port (TAC → C on the *optimizing* backend path).  The
# oracle typechecks (infer.py) + lowers (lower.py) each program to a TAC value
# WITH NO optimization (opt.lark is M7.4, not yet ported), emits C via CEmitter,
# and the port serialises that same TAC into tac.lark ctors and runs
# lex+parse+tac+emit_tac_c + `emitTacC(<TAC>)`, demanding byte-identical C.  Reject
# fixtures (infer raises) and import programs are skipped, as is a CEK overflow on
# a deep serialised TAC.  Meta-circular, so slow.
emittactest:
	python3 tests/emit_tac_c_difftest.py

# M7.4: the opt.py port (TAC → TAC optimization passes on the *optimizing* path).
# For every corpus file AND every level -O0..-O3, the oracle lowers (lower.py) then
# optimizes (opt.py `optimize` at that level) and pretty-prints the TAC; the port
# serialises the SAME unoptimized TAC and runs lex+parse+tac+opt +
# `tacPretty(optimizeProg(<TAC>, level))`, demanding byte-identical optimized TAC.
# The harness resets opt._SITE per oracle call so the inline/closure site counters
# line up with the port's fresh-subprocess counter, and re-lowers per level (opt.py
# mutates fn.body in place).  Reject fixtures + import programs are skipped, as is a
# CEK overflow on a deep serialised TAC (the optimizer walks far more list structure
# than the emitter).  Meta-circular (4 runs per file), so slow — run alone.
opttest:
	python3 tests/opt_difftest.py

# The whole optimizing pipeline, self-hosted: all nine modules concatenated
# (lex → emit_tac_c) compile each corpus file and must reproduce the oracle's
# optimized C byte-for-byte at every level, -O0 through -O3.  Strictly stronger
# than lowertest/emittactest/opttest, each of which isolates a single stage.
#
# This harness existed for days with no target and no baseline, and quietly held
# 25 failures (all of them harness bugs).  That is what an unwatched differential
# is worth.  Its numbers are pinned in tests/BASELINES.md; keep them there.
optcompilertest:
	python3 tests/optcompiler_difftest.py

# F3.1a: the regalloc.py port (CFG + liveness → live intervals → linear scan).
# The oracle lowers each program to an UNOPTIMIZED TAC, allocates, and prints each
# Allocation with pretty_allocation(); the port serialises the same TAC and runs
# lex+parse+tac+opt+regalloc + `raPrettyTac(<TAC>)` — regalloc.lark reuses opt.lark's
# CFG and liveness rather than re-porting them.  Every register and spill slot must
# match.
#
# THE ORACLE HAD TO BE CANONICALISED FIRST.  regalloc.py's _compute_intervals
# iterated frozensets, so the interval table's insertion order — the tiebreak of the
# stable sort in the scan, hence which Tmp got which register — was a function of
# PYTHONHASHSEED, and asm.py emitted different assembly on every run (10 of the 45
# corpus files; 09_parser gave 5 distinct outputs in 5 runs).  There was no byte
# identity for this test, or asmtest, to test against.  It now iterates sorted.
regalloctest:
	python3 tests/regalloc_difftest.py

# F3.1b: the asm.py port (TAC → RV32I assembly text).  The last stage of the pipeline
# on a SECOND backend: lex → parse → infer → lower → opt now feeds either
# emit_tac_c.lark (→ C) or asm.lark (→ RV32I).  Same isolation as emittactest — the
# oracle's unoptimized TAC is serialised in, and the two .S texts must be byte-identical,
# every immediate, label and column of mnemonic padding.  gen() is called in-process:
# asm.py's CLI writes <src>.S next to its input, which would litter the corpus.
asmtest:
	python3 tests/asm_difftest.py

# Property/fuzz differential (SELFHOST hardening before F2).  Generates random
# well-typed programs (tests/fuzz_gen.py) the fixed corpus never wrote and pushes
# each through lex→parse→infer→emit, demanding port==oracle at every stage.
# `fuzz` runs the full (slow, meta-circular) pipeline on a small batch; `fuzzfast`
# runs only the cheap front-end on many programs.  See tests/AUDIT.md.
fuzz:
	python3 tests/fuzz_difftest.py -n 8

fuzzfast:
	python3 tests/fuzz_difftest.py -n 40 --stages lex,parse

# F2 (true self-hosting).  Assembles lex+parse+emit_c into a stdin-driven
# compiler, then runs the two-stage bootstrap: the Python oracle builds stage1,
# stage1 compiles the compiler's own source to C1, a stage2 built from C1 emits
# C2, stage3 emits C3 — and C1==C2==C3 (byte-identical) is the fixpoint.  Since
# OPTIMIZE §8a (balanced emitter join) the arena peak is ~177 MB and the fixpoint
# closes at a 512 MB arena; the harness still defaults large — pass LARK_ARENA_SIZE
# to run it small.  `bootstrap` asserts C1==C2==C3; `--stages 2` for cheaper C1==C2.
bootstrap:
	python3 tests/bootstrap.py

# F2⁺ NATIVE fixpoint: the *typechecking* compiler (6 modules + tcGate + stdin
# main) reproducing its own C.  CLOSED (OPTIMIZE §8b, 2026-07-08): the §8b
# applyScheme closed-scheme short-circuit in types.lark cut the infer pass's
# self-compile from a >12 GB overflow to a 10.15 GB completing peak, so the ladder
# reaches C1==C2==C3 byte-identical (sha 34a07692, 18549 lines).  Heavy (~10 GB
# arena; runs at 14 GiB for headroom, lazily committed).  See tests/bootstrap_tc.py.
bootstrap-tc:
	python3 tests/bootstrap_tc.py

# ── The book's companion repository ───────────────────────────────────────────
#
# ../repo is the tree that ships with the book, laid out by strand (self /
# optimize / prove) so that each strand is self-contained.  It is GENERATED from
# this one: the Lark modules and the oracle are copied, the harnesses are copied
# with their paths rewritten (a comment that says `07/src/lexer.py` here has to
# say `oracle/lexer.py` there, because that is where the reader's copy lives).
#
# So: edit the module or the harness HERE, then `make repo`.  Never edit ../repo
# by hand — `make drift` exists to catch it if you do.  It was hand-maintained
# until 2026-07-12, by which point all thirteen harnesses had diverged from their
# twins and the two BASELINES.md disagreed about `cektest`.  A file that must be
# edited in two places gets edited in one.
repo:
	python3 ../tools/mkrepo.py

drift:
	python3 ../tools/mkrepo.py --check

# Every target with a row in tests/BASELINES.md, and nothing else — `make repo` fails
# the build if the two lists drift apart.  They did: five modules landed after this
# rule was written, were pinned, and were never added here, so `make test` quietly
# meant "five of the ten".  A pin that `make test` cannot contradict is a souvenir.
test: lextest parsetest infertest cektest emittest typechecktest \
      lowertest emittactest opttest optcompilertest regalloctest asmtest
