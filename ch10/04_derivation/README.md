# §10.4 — From Small-Step Semantics to the CEK Machine

`derivation.py` — the chapter's central claim, mechanised. It runs one
call-by-value program two ways and shows they agree:

- **Stage 1, reduction semantics:** to take a step, *decompose* the whole term
  into an evaluation context and a redex, *contract* the redex, and *plug* the
  result back — rediscovering the context by re-traversing the term each step.
- **Stage 2, the CEK machine:** carry the context as an explicit *continuation*
  (a stack of frames) instead of rediscovering it.

```
python3 derivation.py
```

Both reduce `((λx. x + x) (1 + 2))` to `6`. The derivation is the correspondence
the output ends on — each evaluation context of Stage 1 is one continuation frame
of Stage 2:

```
[] a  -> AppFn      v []  -> AppArg
[]+r  -> AddL       v+[]  -> AddR
```

The machine does not approximate the semantics; it is the same definition with
the context turned into data. (`vm-theory/code/smallstep/` and
`vm-theory/code/cek/` give the two endpoints on their own.)
