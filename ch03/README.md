
## Chapter 03 — Lexical Analysis

Companion code for Chapter 3 of *The Language Stack: From Silicon to Semantics*.

The scanner turns a flat stream of characters into a stream of *tokens* — the
units the parser works with. This chapter develops the idea from its formal core
(finite automata) up to a working scanner, and shows where the model's limits
lie. The code here is pedagogical; Lark's production scanner is the Lark snapshot
linked at the bottom.

| File / Folder | Section | What it shows |
|---------------|---------|---------------|
| `dfa.py` | §3.2 | A formal `DFA` class (`.accepts` / `.run`) plus `tokenize_simple` reproduced verbatim from the book. Demos: the identifier DFA from Figure 3.1, an integer DFA, and a comparison-operator DFA covering `<  <=  >  >=  ==  !=` (Exercise 3.3). |
| `tokenizer/` | §3.4–§3.5 | Extended scanners: a regexp-based tokenizer (`regexp.py`), a hand-written state-machine driver (`state.py`), a PL/0 token set (`tokens.py`), and a tokenizer with line/column error reporting (`tokenerrors.py`). See [`tokenizer/README.md`](./tokenizer/README.md) and [`tokenizer/STATE.md`](./tokenizer/STATE.md). |
| `finite_automata/` | §3.2–§3.3 | Generic DFA / NFA / ε-NFA implementations in Python (`dfa.py`) and a DFA in C (`dfa.c`), with a standalone theory guide ([`finite_automata/README.md`](./finite_automata/README.md)) covering minimisation, closure properties, and the pumping lemma. |
| `Makefile` | — | `make run` executes `dfa.py`. |

### Running

```sh
make run                          # the chapter's dfa.py demos

python3 tokenizer/regexp.py       # regexp tokenizer
python3 tokenizer/state.py        # state-machine tokenizer
python3 tokenizer/tokens.py       # PL/0 token set
python3 tokenizer/tokenerrors.py  # tokenizer with error reporting

python3 finite_automata/dfa.py    # DFA/NFA test framework (Python)
cd finite_automata && cc -o dfa dfa.c && ./dfa   # DFA in C
```

### Things worth noticing

- **The DFA is the model, not just an example.** `dfa.py` gives the formal
  five-tuple `(states, alphabet, δ, start, accepting)` and then shows the
  identifier, integer, and comparison-operator scanners as instances of it —
  the same object the book uses to *define* what a token is in §3.2.
- **Longest match (maximal munch).** A scanner must prefer `<=` over `<`. The
  regexp tokenizers list the longer operator before its prefix so the combined
  pattern matches greedily; the book's hand-written scanner does the same with
  explicit one-character lookahead.
- **Where regular languages stop.** §3.3 marks the boundary: a finite automaton
  cannot match nested brackets or `{aⁿbⁿ}`. The `finite_automata/` guide proves
  this with the pumping lemma — which is exactly why the *parser* (Chapter 4)
  needs a stack the scanner does not have.
- **Errors are the scanner's first job after recognition.** `tokenerrors.py`
  records line and column for every token and reports unexpected characters
  (`!!`, a stray `\`) precisely, the topic of §3.5.

Solutions to the chapter exercises live in `solutions/` (not part of the build).

The Lark snapshot for this chapter is [lark/01/src/lexer.py](./../lark/01/src/lexer.py).
