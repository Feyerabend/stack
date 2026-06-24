
## WAM

The Warren Abstract Machine (WAM) is a highly influential virtual machine designed
specifically for implementing the logic programming language Prolog. Developed by
David H. D. Warren in the early 1980s, it provides an efficient execution model by
transforming Prolog's high-level logic into lower-level operations tailored to a virtual
machine architecture.


### High-Level Purpose

The WAM efficiently executes Horn clause logic by compiling Prolog programs into a
sequence of low-level instructions. These instructions are interpreted or executed
by the WAM, leveraging Prolog’s core features like unification, backtracking, and
logical variables.

*Core Features of WAM*

1. *Unification*: Central to Prolog, unification matches terms (variables, constants,
   or structures). The WAM includes optimised instructions for unification, handling
   variable bindings and logical constraints.
2. *Backtracking*: Prolog uses backtracking to explore alternative solutions when a
   computation fails. The WAM implements this via a stack-based structure with choice
   points for efficient state restoration.
3. *Efficient Term Representation*: Terms (variables, constants, lists, structures)
   are compactly stored in memory using tagged cells to differentiate types.


### Components of the WAM

#### 1. Registers

The WAM employs registers to manage execution state:
- *Instruction Pointer (IP)*: Points to the next instruction.
- *Heap Pointer (HP)*: Tracks dynamic term allocation.
- *Current Predicate (CP)*: Manages the current predicate context.

In the Python implementation:

```python
self.registers = {
    'IP': 0,    # instruction pointer
    'CP': 0,    # current predicate
    'HP': 0,    # heap pointer
}
```

#### 2. Memory Areas

The WAM organises memory into distinct areas:
- *Heap*: Stores variable cells (and fresh anonymous variables).
  
```python
self.heap = []  # variable cells
```

- *Argument registers*: Hold the arguments of the goal currently being called.
  A goal loads them with `put_*`; the called clause's head reads them with `get_*`.

```python
self.argregs = [None] * 8  # A0, A1, ...
```

- *Call Stack*: Tracks, for each active call, the return address and the cut
  barrier (the choice-point height to cut back to).

```python
self.call_stack = []  # entries: (return_ip, cut_barrier)
```

- *Choice Points*: Stores execution state snapshots for backtracking.

```python
self.choice_points = []  # backtrack points
```

- *Trail*: Records variable bindings for undoing during backtracking.

```python
self.trail = []  # trail for variable bindings
```

These areas enable unification, recursion, and nondeterministic execution.

#### 3. Instructions

The WAM uses a specialized instruction set for Prolog operations, stored as:

```python
self.instructions = []  # loaded program
```

Instructions are tuples, e.g.:

```python
('CALL', ('child', 1), 0)  # Invokes child/1 predicate
```

The instructions split along the two sides of a call. A *goal* loads the argument
registers and calls; a clause *head* unifies those registers against its own
arguments.

Goal side (`put_*`, building a call):
- *PUT_CONST*: Loads a constant into an argument register.
- *PUT_VAR*: Loads a variable reference into an argument register.
- *PUT_VOID*: Loads a fresh anonymous variable.
- *CALL*: Invokes a predicate, saving the return address and cut barrier.

Head side (`get_*`, matching a clause head):
- *GET_CONST*: Unifies an argument register with a constant.
- *GET_VAR*: Unifies an argument register with a (head) variable.
- *GET_VOID*: An anonymous head argument; unifies with anything.
- *PROCEED*: Completes a clause and returns to the caller.

Control and the rest:
- *CUT*: Discards choice points back to the clause's cut barrier.
- *TRY_ME_ELSE*, *RETRY_ME_ELSE*, *TRUST_ME*: Manage multiple clauses for backtracking.
- *BUILTIN*: Executes built-in predicates like `\=` (inequality).
- *HALT*: Marks query success (a solution is recorded, then the machine
  backtracks to look for more).

The `run` method drives execution by fetching, decoding, and executing
instructions, updating registers and memory.


#### 4. Compilation

Prolog programs are compiled into WAM instructions via the `Compiler` class. It
transforms facts, rules, and queries into low-level instructions, managing:
- *Variables*: Mapped to indices (`self.vars`).
- *Constants*: Indexed for efficient access (`self.constants`).
- *Predicates*: Mapped to instruction addresses (`self.predicates`).

For example, a fact:

```prolog
parent(zeb, john).
```

Compiles to a clause head that unifies the incoming argument registers against
its constants:

```python
[
    ('GET_CONST', 0, 0),  # unify A0 with 'zeb'
    ('GET_CONST', 1, 1),  # unify A1 with 'john'
    ('PROCEED', 0, 0)     # return to caller
]
```

A query loads the argument registers and calls:

```prolog
?- child(X).
```

Compiles to:

```python
[
    ('PUT_VAR', 0, 0),         # A0 := variable 'X'
    ('CALL', ('child', 1), 0), # call child/1
    ('HALT', 0, 0)             # query goal succeeded
]
```

Multi-clause predicates use `TRY_ME_ELSE`, `RETRY_ME_ELSE`, and `TRUST_ME` to
handle backtracking across clauses.

#### 5. Execution

Execution begins by loading compiled instructions:

```python
vm.load(compiler)
```

Each query is compiled with its own entry address (recorded in
`compiler.query_addrs`); the machine starts there, runs the goal, and reports the
bindings of the query's variables:

```python
for query, query_vars, start in compiler.query_addrs:
    vm = WAM()
    vm.load(compiler)
    vm.query_vars = query_vars
    vm.registers['IP'] = start
    vm.run(find_all=True)
```

The `run` method cycles through:
- *Unification*: Matches terms using `unify` and `deref`.
- *Predicate Calls*: Invokes predicates via `CALL` and `PROCEED`.
- *Backtracking*: Restores state using `backtrack` and choice points.
- *Solution Storage*: Saves variable bindings in `self.solutions`.

For example, the query `?- child(X)` finds all `X` where `child(X)` holds, using
backtracking to explore multiple solutions.


#### 6. Built-in Predicates

The WAM supports built-in predicates like `\=` (inequality), compiled and executed via:

```python
self.builtins = {r'\=': self.compile_inequality}
```


#### 7. Example Program

The provided program includes facts, rules, and queries:

```python
program = [
    ['parent', 'zeb', 'john'],
    ['parent', 'zeb', 'jane'],
    ['parent', 'john', 'jim'],
    ['parent', 'jane', 'alice'],
    [':-', ['child', 'X'], ['parent', 'X', '_'], '!'],
    [':-', ['grandparent', 'X', 'Z'], ['parent', 'X', 'Y'], ['parent', 'Y', 'Z']],
    [':-', ['sibling', 'X', 'Y'], ['parent', 'Z', 'X'], ['parent', 'Z', 'Y'], [r'\=', 'X', 'Y']],
    ['?-', ['child', 'X']],
    ['?-', ['grandparent', 'zeb', 'Who']],
    ['?-', ['sibling', 'john', 'Sibling']]
]
```

This program defines family relationships and queries children, grandparents, and siblings, demonstrating
unification, backtracking, and cuts.

### Conclusion

The Python implementation in `wam.py` is a simplified yet functional abstraction of the WAM. It replicates
core components—registers, memory areas, instructions, and backtracking—while supporting Prolog’s unification
and predicate execution. The `Compiler` and `WAM` classes work together to compile and execute Prolog programs,
simulating the WAM’s model.

The WAM remains a cornerstone of logic programming, influencing modern Prolog systems like SWI-Prolog and
SICStus Prolog[. Its design has also impacted constraint logic programming and theorem proving systems,
underscoring its lasting significance.
