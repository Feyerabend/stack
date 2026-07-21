
## `formal/` — the machine-checked metatheory

One thing lives here: [`proof/`](proof/), a small proof checker for Martin-Löf
Type Theory (with HoTT features) written in C — the **lcore** kernel — and, encoded
inside it, the **type-soundness proof of Lark itself**. Where the rest of the
repository tests the compiler against a reference, this tree *proves* a property of
the language once and for all, in a form the kernel can check.

See [`proof/README.md`](proof/README.md) for the kernel and the proof. In short:

```
proof/code/      the lcore kernel and standard library (the C source + .lcore)
proof/lark/      Lark's syntax, typing, step relation, and the soundness proof
proof/strands/   extension proofs (affine soundness, the refinement calculus V3)
proof/tools/     build and check scripts
proof/Makefile   `make check` verifies every proof file (0 errors = green)
```

Run it from the repository root with `make formal` (which is `make -C
dev/formal/proof check`).
