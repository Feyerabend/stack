
## Chapter 13 — The Adversary

Companion code for Chapter 13 of *The Language Stack: From Silicon to Semantics*.

This chapter attacks everything the book built — the compiler, the tests, the
register allocator's oracle, the affine checker, and the proof kernel itself —
and reports what the attack found. The companion lets you *run* the attacks:
every bug in the chapter is reproducible, every guard demonstrable, and every
verdict read from an exit code rather than an impression.

| Section | Where |
|---------|-------|
| §13.1 Making the language attackable | `bugs/` — the exhaustiveness witness and the totality checker refusing `n - 1` |
| §13.2 Manufacturing adversaries | `bugs/` (the miscompile, now rejected) + `make fuzz` — the typed-program generator, live |
| §13.3 Validating the validator | `make fuzz`; sanitizers via `make -C <lark>/09 santest` (clang/ASan required) |
| §13.4 The certificate | `certificate/` — a mutation planted in the real allocator's output, caught by `regcheck` |
| §13.5 The hole in the affine wall | `bugs/` (the capture program) + the graded model in the proof stack below |
| §13.6 Who checks the checker | `proofstack/` — the seven-file stack green, then two planted lies turned red |
| §13.7 What the adversary leaves standing | conceptual — the trusted-base ledger |

**Everything real is referenced by path, not duplicated here.** The bug
programs and the compiler under attack live in
[`lark/09/`](./../lark/09/) (the Phase 9 snapshot: `tests/errors/`,
`tests/gen_prog.py`, `src/regcheck.py`); the machine-checked proof stack —
`lark-typing`, `lark-affine`, `lark-weaken`, `lark-subst`, `lark-step`,
`lark-preservation`, `lark-erase` — lives in
[`lark/formal/proof/lark/`](./../lark/formal/proof/lark/), checked by the
*real* kernel at `lark/formal/proof/code/core/` (the same one Chapters 11–13
stood on; the teaching sibling under `ch12/kernel/` is not used here). The
scripts only drive those artifacts and read back their verdicts.

> *Exit codes are the contract.* Section 13.6 made the kernel strict: any
> failed line makes a run exit non-zero. These companions lean on that
> everywhere — "the stack is green" and "the planted lie was caught" are
> facts a shell can check, which is the chapter's point in miniature.

## Running

```sh
make run          # the bugs, the certificate demo, and the proof stack (green + 2 planted reds)
make bugs         # just the chapter's bug programs and their diagnostics
make certificate  # just the planted-mutation certificate demo
make stack        # just the seven-file proof stack, green then red
make fuzz         # a short live run of the differential fuzzer (needs python3 + hypothesis)
```

Requires `python3` and a C compiler (`cc`) for the kernel; `make fuzz`
additionally needs the Hypothesis library (`pip install hypothesis`). The
`lark/09/` snapshot must be present next to this chapter's parent directory.

Solutions to the chapter's exercises are in `solutions/`.
