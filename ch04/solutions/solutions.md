
## Chapter 4 — Solutions

Solutions to the exercises in Chapter 4, *Parsing*, of
*The Language Stack: From Silicon to Semantics*.

| Exercise | Code | Run |
|-||--|
| 1 (Boolean recursive descent) | `ex01_bool_rd.py` | `python3 ex01_bool_rd.py` |
| 2 (LL(1) table for right-recursive G0) | `ex02_ll1_table.py` | `python3 ex02_ll1_table.py` |
| 3 (LL(1) for `aⁿbⁿ` + pumping) | `ex03_anbn.py` | `python3 ex03_anbn.py` |
| 4 (multi-pattern `match` arms) | `ex04_match_multi.py` | `python3 ex04_match_multi.py` |
| 5 (shift-reduce trace) | `ex05_sr_trace.py` | `python3 ex05_sr_trace.py` |

Exercise 4 extends the real Lark parser
([lark/02/src/parser.py](./../../lark/02/src/parser.py),
`tree.py`).



### Exercise 1 — Recursive descent for Boolean expressions

> Write a recursive descent parser for Boolean expressions from variables, `not`,
> `and`, `or` (precedence: `not` highest, `or` lowest). State the grammar in EBNF,
> verify it is LL(1) with FIRST, implement one function per nonterminal.

*EBNF* (precedence baked into the rule hierarchy — lowest binding outermost):

```
expr   ::= term   ( "or"  term   )*
term   ::= factor ( "and" factor )*
factor ::= "not" factor | atom
atom   ::= VAR | "(" expr ")"
```

*FIRST sets* (`VAR` = any variable):

```
FIRST(atom)   = { VAR, "(" }
FIRST(factor) = { "not", VAR, "(" }
FIRST(term)   = { "not", VAR, "(" }
FIRST(expr)   = { "not", VAR, "(" }
```

*Why LL(1).* Every decision uses one lookahead token: `factor` picks the unary
rule on `not` and `atom` otherwise (disjoint sets); the `( … )*` loops in `expr`
and `term` continue only on exactly `or` / `and`. No nonterminal has two
productions whose FIRST sets overlap.

`ex01_bool_rd.py` implements one method per nonterminal, builds a nested-tuple
AST, and evaluates it. It checks precedence (`a and not b or c` parses as
`(a ∧ ¬b) ∨ c`), parenthesised overrides, and rejects malformed inputs.



### Exercise 2 — LL(1) table for the right-recursive G0

> Compute the LL(1) parse table for `E → T (+ T)*`, `T → F (* F)*`,
> `F → num | ( E )`. De-EBNF first, compute FIRST/FOLLOW, fill the table, and
> compare with `tab:parse-table`. Any differences?

*De-EBNF'd grammar* (right recursion replaces each `( … )*`):

```
E  -> T E'
E' -> + T E' | ε
T  -> F T'
T' -> * F T' | ε
F  -> num | ( E )
```

*FIRST / FOLLOW* (computed from scratch in the script):

```
FIRST(E)=FIRST(T)=FIRST(F) = { num, ( }      FOLLOW(E)=FOLLOW(E') = { $, ) }
FIRST(E') = { +, ε }                          FOLLOW(T)=FOLLOW(T') = { +, ), $ }
FIRST(T') = { *, ε }                          FOLLOW(F) = { *, +, ), $ }
```

*Table* (every cell ≤ 1 entry, so LL(1)):

```
      num     (       )       +        *        $
E    T E'   T E'
E'                   ε      + T E'              ε
T    F T'   F T'
T'                   ε        ε      * F T'     ε
F    num   ( E )
```

*Comparison with `tab:parse-table`.* This *is* the grammar the chapter builds
when it eliminates G0's left recursion, so the table is the same. The only
difference is that the chapter's table omits the end-marker column; a complete
table adds the `$` column, where `E' → ε` and `T' → ε` (because `$ ∈ FOLLOW(E')`
and `$ ∈ FOLLOW(T')`). The script asserts every shared cell matches and that the
`$` column holds exactly those two ε-entries.



### Exercise 3 — `aⁿbⁿ` is LL(1) but not regular

> `S → a S b | ε` generates `{aⁿbⁿ}`. Show it is LL(1), implement a recursive
> descent parser, then explain with the pumping lemma why no finite automaton
> accepts `{aⁿbⁿ}`.

*FIRST / FOLLOW and table:*

```
FIRST(S)  = { a, ε }
FOLLOW(S) = { b, $ }

        a            b          $
S       S -> a S b   S -> ε     S -> ε
```

`M[S,a]` takes the `a`-production (`a ∈ FIRST`); `M[S,b]` and `M[S,$]` take `ε`
(`b, $ ∈ FOLLOW(S)` and `ε ∈ FIRST(S)`). Each cell has one entry → *LL(1)*.
`ex03_anbn.py` implements the recursive descent recogniser and checks it accepts
`aⁿbⁿ` and rejects `a`, `b`, `ba`, `aab`, `abb`, `aba`, ….

*Why no finite automaton accepts `{aⁿbⁿ}` (pumping lemma, Chapter 3).* Suppose
some DFA accepts `L = {aⁿbⁿ}` with `p` states. Take `s = aᵖbᵖ ∈ L`, `|s| ≥ p`.
The pumping lemma gives `s = xyz` with `|xy| ≤ p` and `|y| ≥ 1`. Since `|xy| ≤ p`,
`xy` lies in the leading run of `a`s, so `y = aᵏ` with `k ≥ 1`. Then
`xy²z = a^{p+k} bᵖ` has more `a`s than `b`s, so `xy²z ∉ L` — contradicting the
lemma. Hence `L` is not regular.

The reason is the same finite-memory limit as the nested comments of Chapter 3:
to match `b`s against `a`s the machine must *count* how many `a`s it saw, and a
finite state set cannot hold an unbounded count. A pushdown automaton can — it
pushes a symbol per `a` and pops one per `b` — which is exactly why this language
needs the recursive (stack-using) parser of this chapter, not the regular
machinery of the lexer. Recursive descent gets the stack for free: it is the call
stack of `_S`.



### Exercise 4 — Multiple patterns per `match` arm

> Extend `_parse_match_expr` to allow `| A | B => expr`. (a) revised EBNF for an
> arm; (b) the code change; (c) the `MatchExpr` change in `tree.py`.

*(a) EBNF.* An arm becomes one-or-more `|`-separated patterns before `=>`:

```
arm ::= "|" pattern ( "|" pattern )* "=>" expr
```

The arm-opener and the pattern-separator are the same `|` token, so the parser
reads them with a nested loop.

*(b) Code change* (`ex04_match_multi.py` overrides `_parse_match_expr`). The
single `pat = self._parse_pattern()` becomes:

```python
while self._match(TK.PIPE):                ## opens an arm
    pats = [self._parse_pattern()]
    while self._match(TK.PIPE):            ## extra patterns for this arm
        pats.append(self._parse_pattern())
    self._expect(TK.FAT_ARROW)
    expr = self._parse_expr()
    arms.append((tuple(pats), expr))
```

*(c) `tree.py` change.* Each arm stores a *tuple* of patterns:

```python
@dataclass(frozen=True)
class MatchExpr:
    scrutinee: Expr
    arms: tuple[tuple[tuple[Pat, ...], Expr], ...]   ## was tuple[tuple[Pat, Expr], ...]
```

The interpreter then matches the scrutinee against each pattern in the tuple and
runs the arm on the first hit (an OR-pattern). The script parses
`match x with | A | B => 1 | C => 2 end` and confirms arm 0 groups patterns
`A, B` while arm 1 holds `C`, and that an ordinary single-pattern arm still
parses (now as a 1-tuple).



### Exercise 5 — Shift-reduce trace of `(1 + 2) * 3`

> Trace the shift-reduce parse of `(1 + 2) * 3` under G0. At the step where the
> stack is `$ ( E` and the input begins with `)`, what action is taken? Why no
> reduce there, and which production consumes the `)`?

`ex05_sr_trace.py` prints and *validates* the full trace (each reduce must find
its exact handle on the stack):

```
  Stack            Remaining input    Action
  $                ( num + num ) * num $   shift
  $ (              num + num ) * num $     shift
  $ ( num          + num ) * num $         reduce F -> num
  $ ( F            + num ) * num $         reduce T -> F
  $ ( T            + num ) * num $         reduce E -> T
  $ ( E            + num ) * num $         shift
  $ ( E +          num ) * num $           shift
  $ ( E + num      ) * num $               reduce F -> num
  $ ( E + F        ) * num $               reduce T -> F
  $ ( E + T        ) * num $               reduce E -> E + T
  $ ( E            ) * num $               shift          <-- the ')' step
  $ ( E )          * num $                 reduce F -> ( E )
  $ F              * num $                 reduce T -> F
  $ T              * num $                 shift
  $ T *            num $                   shift
  $ T * num        $                       reduce F -> num
  $ T * F          $                       reduce T -> T * F
  $ T              $                       reduce E -> T
  $ E              $                       accept
```

*At `$ ( E` with `)` next, the parser shifts the `)`.* It does not reduce
because no complete handle sits on top of the stack. The reduce `E → E + T` has
already fired (it ran one step earlier, on lookahead `)`, which *is* in
`FOLLOW(E)`), leaving `( E` on the stack. Now `E` alone is not the right-hand
side of any reduction that should apply, and the only production mentioning `)`
is `F → ( E )` — whose handle `( E )` is *not yet complete*, because the `)`
has not been shifted. So the parser shifts `)` to finish the handle; the
production that then consumes it is `F → ( E )` (the next step:
`$ ( E ) → reduce F → ( E )`). This is the bottom-up mirror of how the
parenthesised subexpression in recursive descent only returns once `atom` has
matched the closing `)`.
