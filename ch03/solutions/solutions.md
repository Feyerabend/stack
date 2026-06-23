
## Chapter 3 — Solutions

Solutions to the exercises in Chapter 3, *Lexical Analysis*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|-||--|
| 1 (number exponent) | `ex01_number_exponent.py` | `python3 ex01_number_exponent.py` |
| 2 (underscore identifiers) | `ex02_underscore_idents.py` | `python3 ex02_underscore_idents.py` |
| 3 (comparison-operator DFA) | `ex03_cmp_dfa.py` | `python3 ex03_cmp_dfa.py` |
| 4 (single-line comments) | `ex04_line_comments.py` | `python3 ex04_line_comments.py` |
| 5 (pumping lemma) | proof below | — |

Exercises 1, 2, 4 subclass the real Lark lexer ([lark/01/src/lexer.py](./../../lark/01/src/lexer.py));
Exercise 3 reuses the `DFA` class from `ch03/dfa.py`.



### Exercise 1 — Exponent suffix in `_read_number`

> Extend `_read_number` to accept an exponent suffix, so that `1.5e10` and `3e8`
> scan as floats. State precisely the new lookahead your change requires, and
> give an input on which a naive version would misclassify the dot.

`ex01_number_exponent.py` adds the exponent (see `ExpLexer`).

*The new lookahead.* To commit to an exponent you must look *past an optional
sign to a digit* before consuming the `e`. From the `e`:

- `_peek(1)` is a digit → exponent (`3e8`); or
- `_peek(1)` is `+`/`-` *and* `_peek(2)` is a digit → exponent (`3e+8`).

Otherwise the `e` is not part of the number. So the change needs *two
characters of lookahead beyond the `e`* (the sign and the digit after it). This
is the same discipline the lexer already applies to the dot: it consumes `.`
only when `_peek(1)` is a digit, never on one character alone.

*The dot a naive version misclassifies: `1.foo`.* A reader that checks only
`_peek() == "."` (one-character lookahead) treats the dot as a decimal point and
scans `FLOAT 1.0` then `NAME foo`. The correct two-character rule keeps `INT 1`
and lets the `.` be reported as an unexpected character (Lark has no `.` token).
The script asserts both behaviours.

```
$ python3 ex01_number_exponent.py
exponent scanning OK; naive dot misclassification demonstrated
```



### Exercise 2 — Allowing underscore-leading identifiers

> Lark forbids identifiers that begin with an underscore. Suppose instead they
> were allowed. Which method in Section 3.x would change, which case in the main
> dispatch would become ambiguous, and how would you resolve the ambiguity?

- *Method that changes: `_read_wildcard`.* Today it consumes a lone `_` and
  raises if an identifier character follows. To allow `_foo`, it falls through to
  identifier scanning when an identifier character follows. `_read_name` is
  reused *unchanged* — it already accepts `_` in the body, and since the keyword
  table is all-lowercase, `_foo` and even `_if` are plain `NAME`s, never keywords.
- *Dispatch case that becomes ambiguous: the `ch == "_"` arm of `_next`.* A `_`
  can now begin either the `WILDCARD` token or an identifier.
- *Resolution: one character of lookahead.* If the character after `_` is an
  identifier character (alnum or `_`), scan an identifier; otherwise emit the
  bare `WILDCARD`. This is the same maximal-munch tie-break used for `<` vs `<=`.

`ex02_underscore_idents.py` implements it and checks that `_foo`, `_x1`, `_if`
become `NAME`s while a lone `_` stays `WILDCARD` (and the stock lexer still
rejects `_foo`).



### Exercise 3 — A DFA for the comparison operators

> Draw a DFA that accepts the comparison operators `<`, `<=`, `>`, `>=`, `==`,
> `!=`, and no other strings. How many accepting states does it need, and why
> can it not be merged into fewer?

The natural recognizer (built in `ex03_cmp_dfa.py` as `build_recognizer`):

```
       '<'        '='
   S ──────► LT ───────► LE         (LT, LE  accepting)
   │ '>'       '='
   ├───────► GT ───────► GE         (GT, GE  accepting)
   │ '='       '='
   ├───────► EQ1 ──────► EQEQ       (EQ1 non-accepting; EQEQ accepting)
   │ '!'       '='
   └───────► BANG ─────► NEQ        (BANG non-accepting; NEQ accepting)
```

`EQ1` and `BANG` are non-accepting because a lone `=` is *assignment* and a lone
`!` is not an operator.

*How many accepting states — two honest answers.*

- *As a recognizer of the six-string set:* the natural DFA has *6* accepting
  states, but it *minimizes to 2*. The four two-character operators all end in
  an indistinguishable accept-sink (accept now, reject on any further input), so
  `<=`, `>=`, `==`, `!=` merge into one state; and `LT` and `GT` have identical
  futures (accept now, accept on `=`, reject otherwise) so they merge too.
  `ex03_cmp_dfa.py` builds this minimized DFA and confirms it accepts exactly the
  same six strings.
- *As a lexer:* the accepting states *cannot* be merged — each must emit a
  *distinct token* (`LT`, `LE`, `GT`, `GE`, `EQEQ`, `NEQ`). A lexer is a
  transducer, not a recognizer; once a state carries an output, two states with
  different outputs are distinguishable by definition, so 6 are required. This is
  why the chapter's scanner keeps them apart.

So the precise answer to "why can it not be merged into fewer" is: *as a plain
recognizer it can (down to 2); as the lexer the chapter actually needs, it
cannot, because the six states differ in the token they emit.*

```
$ python3 ex03_cmp_dfa.py
recognizer OK (6 accepting); minimized OK (2 accepting)
```



### Exercise 4 — Single-line comments in `_skip`

> Add single-line comments (`--` to end of line) to `_skip`. Unlike block
> comments, these are a regular pattern. Explain why, and confirm that your
> addition needs no depth counter.

`ex04_line_comments.py` adds one branch to `_skip`: on `--`, run to (not past)
the newline; the loop then skips the newline as ordinary whitespace.

*Why regular.* A single-line comment is exactly the regular expression
`--[^\n]*\n`: the delimiter `--`, any run of non-newline characters, then a
newline. A four-state DFA recognises it (in-code → saw-dash → in-comment →
in-code on newline). There is nothing to balance: a `--` inside the body is just
more body text, so line comments *do not nest*.

*No depth counter.* Block comments need `depth` because `(* … *)` nest, and
counting nesting needs unbounded memory (Exercise 5). A line comment ends
unconditionally at the first newline however many `--` it contains — the script's
`src2` case (`1 -- a -- b -- c\n+ 2`) proves it: three `--` behave like one. A
counter would be dead code.

One consequence worth noting: with `--` as a comment, `a--b` (no spaces) now
lexes as `NAME a` followed by a comment, not `a - (-b)`. That is the usual
trade-off (the same one Haskell makes), and the script confirms `->` and a lone
`-` are untouched.



### Exercise 5 — Nested block comments are not regular

> Using the pumping lemma, prove that the set of correctly nested Lark block
> comments is not regular. Identify, in the proof, exactly where the
> finite-memory limitation bites — and relate that point to the depth counter the
> scanner already uses.

Write `O` for the opening delimiter `(*` and `C` for the closing `*)`, and let
`L` be the set of correctly nested block comments.

*Reduce to the clean case.* Regular languages are closed under intersection,
so if `L` were regular then `L ∩ O*C*` would be too. A string `Oⁱ Cʲ` is a
correctly nested comment iff every opener is matched and the depth never goes
negative — and with all openers first, that holds iff `i = j`. Hence
`L ∩ O*C* = { Oⁿ Cⁿ : n ≥ 1 }`, the classic non-regular language. (This already
settles it, but the exercise asks for the pumping lemma directly, so:)

*Pumping argument.* Suppose `L` is regular with pumping length `p`. Choose

$$ s = O^{p}\, C^{p} \in L, \qquad |s| = 2p \ge p. $$

The pumping lemma gives `s = xyz` with `|xy| ≤ p` and `|y| ≥ 1`. Because
`|xy| ≤ p`, the prefix `xy` lies entirely within the opening run `Oᵖ`, so
`y = Oᵏ` for some `k ≥ 1`. Pump once:

$$ x y^{2} z = O^{p+k}\, C^{p}, \qquad p + k \neq p, $$

which has more openers than closers and is therefore *not* correctly nested:
`xy²z ∉ L`. This contradicts the pumping lemma, so `L` is not regular. ∎

*Where finite memory bites.* The decisive step is "`y` lies in the opening run,
so pumping changes the opener count *independently of* the closer count." Behind
it is the pigeonhole fact the pumping lemma packages: a DFA with `p` states,
reading `Oᵖ`, must revisit some state — two different prefixes `Oᵃ` and `Oᵇ`
(`a ≠ b`) land in the *same* state `q`. From `q` the machine behaves identically,
so it accepts `Oᵃ Cᵃ` and `Oᵇ Cᵃ` alike, even though only one is balanced. The
state `q` has *forgotten the exact nesting depth*. That is precisely the
limitation: a finite state set cannot record an unbounded count.

*Relation to the scanner's counter.* `_skip_comment` keeps an integer `depth`,
incrementing on each `(*` and decrementing on each `*)`, returning only when it
hits zero. That counter is the unbounded memory a DFA lacks — it can reach any
value, distinguishing every nesting depth. The proof shows the counter is a
*necessity*, not a convenience: no finite automaton could replace it, which is
exactly why nested comments are handled in the scanner's imperative body rather
than by the regular machinery that suffices for everything else (identifiers,
numbers, operators, and the line comments of Exercise 4).
