"""A small Warren Abstract Machine.

This is a teaching-sized WAM: it compiles a Horn-clause program (facts, rules,
and queries) into a flat list of instructions and executes them with the WAM's
characteristic machinery -- argument registers, unification against clause heads,
choice points for backtracking, a trail for undoing bindings, and a cut barrier.

The instruction set follows Warren's split between the two sides of a call:

  * a goal/query loads the *argument registers* with ``put_*`` instructions and
    then CALLs the predicate;
  * a clause *head* unifies those argument registers against its own arguments
    with ``get_*`` instructions.

Terms here are only variables and atomic constants (no compound structures), which
is enough for the family-relations program at the bottom of the file.
"""


class WAM:
    def __init__(self, debug=False):
        self.debug = debug
        self.registers = {
            'IP': 0,    # instruction pointer
            'CP': 0,    # current predicate (unused in this miniature)
            'HP': 0,    # heap pointer
        }
        self.heap = []          # variable cells (and fresh anonymous vars)
        self.argregs = [None] * 8   # argument registers A0, A1, ...
        self.call_stack = []    # entries: (return_ip, cut_barrier)
        self.choice_points = [] # backtrack points
        self.trail = []         # records bindings so they can be undone
        self.instructions = []  # loaded program
        self.predicates = {}    # (name, arity) -> entry address
        self.constants = {}     # index -> name
        self.variables = {}     # name -> index
        self.query_vars = []    # (name, index) reported in a solution
        self.solutions = []     # bindings found for the current query

    def load(self, compiler):
        self.instructions = compiler.instructions
        self.predicates = compiler.predicates
        self.constants = {v: k for k, v in compiler.constants.items()}
        self.variables = compiler.vars
        # One heap cell per program variable, each initially unbound (self-ref).
        self.heap = [('REF', i) for i in range(len(compiler.vars))]
        self.registers['HP'] = len(self.heap)

    # ---- term operations -------------------------------------------------

    def new_var(self):
        """Allocate a fresh unbound variable cell and return a reference to it."""
        addr = len(self.heap)
        self.heap.append(('REF', addr))
        self.registers['HP'] = len(self.heap)
        return ('REF', addr)

    def deref(self, term):
        """Follow the reference chain to a constant or an unbound variable."""
        while isinstance(term, tuple) and term[0] == 'REF':
            addr = term[1]
            cell = self.heap[addr]
            if isinstance(cell, tuple) and cell[0] == 'REF' and cell[1] == addr:
                return term  # unbound: points to itself
            term = cell
        return term

    def bind(self, var_addr, value):
        """Bind a variable cell to a value, recording the old value on the trail."""
        self.trail.append((var_addr, self.heap[var_addr]))
        self.heap[var_addr] = value

    def unify(self, term1, term2):
        t1 = self.deref(term1)
        t2 = self.deref(term2)

        if t1[0] == 'REF' and t2[0] == 'REF':
            if t1[1] == t2[1]:
                return True
            self.bind(t1[1], t2)
            return True
        if t1[0] == 'REF':
            self.bind(t1[1], t2)
            return True
        if t2[0] == 'REF':
            self.bind(t2[1], t1)
            return True
        if t1[0] == 'CONST' and t2[0] == 'CONST':
            return t1[1] == t2[1]
        return False

    # ---- choice points and backtracking ---------------------------------

    def push_choice_point(self, next_addr):
        """Snapshot the machine so a later failure can resume at next_addr."""
        self.choice_points.append({
            'next': next_addr,
            'heap': self.heap.copy(),
            'argregs': self.argregs.copy(),
            'trail': self.trail.copy(),
            'call_stack': self.call_stack.copy(),
        })

    def backtrack(self):
        """Restore the most recent choice point and resume at its alternative."""
        if not self.choice_points:
            return False
        cp = self.choice_points[-1]
        self.heap = cp['heap'].copy()
        self.argregs = cp['argregs'].copy()
        self.trail = cp['trail'].copy()
        self.call_stack = cp['call_stack'].copy()
        self.registers['IP'] = cp['next']
        return True

    # ---- the fetch/execute cycle ----------------------------------------

    def run(self, find_all=True):
        try:
            while 0 <= self.registers['IP'] < len(self.instructions):
                instr = self.instructions[self.registers['IP']]
                op, arg1, arg2 = instr
                current_ip = self.registers['IP']
                self.registers['IP'] += 1

                if self.debug:
                    print(f"[{current_ip:3d}] {op} {arg1} {arg2}  "
                          f"A={self.argregs[:3]} cp={len(self.choice_points)}")

                if op == 'PUT_CONST':
                    self.argregs[arg1] = ('CONST', self.constants[arg2])
                elif op == 'PUT_VAR':
                    self.argregs[arg1] = ('REF', arg2)
                elif op == 'PUT_VOID':
                    self.argregs[arg1] = self.new_var()
                elif op == 'GET_CONST':
                    if not self.unify(self.argregs[arg1], ('CONST', self.constants[arg2])):
                        if not self.backtrack():
                            return
                elif op == 'GET_VAR':
                    if not self.unify(self.argregs[arg1], ('REF', arg2)):
                        if not self.backtrack():
                            return
                elif op == 'GET_VOID':
                    pass  # an anonymous head argument unifies with anything
                elif op == 'CALL':
                    if arg1 in self.predicates:
                        cut_barrier = len(self.choice_points)
                        self.call_stack.append((self.registers['IP'], cut_barrier))
                        self.registers['IP'] = self.predicates[arg1]
                    else:
                        if not self.backtrack():
                            return
                elif op == 'PROCEED':
                    if self.call_stack:
                        self.registers['IP'] = self.call_stack.pop()[0]
                    else:
                        return
                elif op == 'TRY_ME_ELSE':
                    self.push_choice_point(arg1)
                elif op == 'RETRY_ME_ELSE':
                    if self.choice_points:
                        self.choice_points[-1]['next'] = arg1
                elif op == 'TRUST_ME':
                    if self.choice_points:
                        self.choice_points.pop()
                elif op == 'CUT':
                    barrier = self.call_stack[-1][1] if self.call_stack else 0
                    del self.choice_points[barrier:]
                elif op == 'BUILTIN':
                    if not self.execute_builtin(arg1):
                        if not self.backtrack():
                            return
                elif op == 'HALT':
                    # The query goal succeeded: record bindings, then look for more.
                    self.save_solution()
                    if find_all:
                        if not self.backtrack():
                            return
                    else:
                        return
                else:
                    raise ValueError(f"Unknown instruction: {op}")
        except Exception as e:
            print(f"\nERROR AT [{current_ip}] {instr}: {e}")
            raise

    def execute_builtin(self, builtin):
        if builtin == r'\=':
            left = self.deref(self.argregs[0])
            right = self.deref(self.argregs[1])
            if left[0] == 'REF' or right[0] == 'REF':
                # Not enough is known to prove they differ; treat as failure.
                return False
            return left != right
        raise ValueError(f"Unknown built-in predicate: {builtin}")

    # ---- reporting -------------------------------------------------------

    def save_solution(self):
        solution = {name: self.pretty_print_term(('REF', idx))
                    for name, idx in self.query_vars}
        self.solutions.append(solution)

    def pretty_print_term(self, term):
        term_val = self.deref(term)
        if term_val[0] == 'REF':
            return f"_{term_val[1]}"   # still unbound
        return term_val[1]            # a constant's name


class Compiler:
    def __init__(self, debug=False):
        self.debug = debug
        self.vars = {}          # variable name -> index
        self.constants = {}     # constant name -> index
        self.predicates = {}    # (name, arity) -> entry address
        self.instructions = []
        self.pred_clauses = {}  # (name, arity) -> [clause, ...]
        self.query_addrs = []   # [(query_term, query_vars, start_address), ...]

        self.builtins = {r'\=': self.compile_inequality}

    # ---- symbol tables ---------------------------------------------------

    def intern_const(self, name):
        if name not in self.constants:
            self.constants[name] = len(self.constants)
        return self.constants[name]

    def intern_var(self, name):
        if name not in self.vars:
            self.vars[name] = len(self.vars)
        return self.vars[name]

    @staticmethod
    def is_var(token):
        return isinstance(token, str) and token != '_' and token[0].isupper()

    # ---- emitting head and goal arguments --------------------------------

    def compile_head(self, head):
        """A clause head unifies its arguments against the argument registers."""
        for i, arg in enumerate(head[1:]):
            if arg == '_':
                self.instructions.append(('GET_VOID', i, 0))
            elif self.is_var(arg):
                self.instructions.append(('GET_VAR', i, self.intern_var(arg)))
            else:
                self.instructions.append(('GET_CONST', i, self.intern_const(arg)))

    def compile_goal(self, goal):
        """A goal loads the argument registers, then calls the predicate."""
        name, args = goal[0], goal[1:]
        for i, arg in enumerate(args):
            if arg == '_':
                self.instructions.append(('PUT_VOID', i, 0))
            elif self.is_var(arg):
                self.instructions.append(('PUT_VAR', i, self.intern_var(arg)))
            else:
                self.instructions.append(('PUT_CONST', i, self.intern_const(arg)))
        self.instructions.append(('CALL', (name, len(args)), 0))

    def compile_inequality(self, args):
        left, right = args
        for i, arg in enumerate((left, right)):
            if self.is_var(arg):
                self.instructions.append(('PUT_VAR', i, self.intern_var(arg)))
            else:
                self.instructions.append(('PUT_CONST', i, self.intern_const(arg)))
        self.instructions.append(('BUILTIN', r'\=', 0))

    def compile_body(self, body):
        for goal in body:
            if goal == '!':
                self.instructions.append(('CUT', 0, 0))
            elif isinstance(goal, list) and goal[0] in self.builtins:
                self.builtins[goal[0]](goal[1:])
            else:
                self.compile_goal(goal)

    def compile_clause(self, clause):
        """Compile one clause's head + body (no predicate-entry bookkeeping)."""
        if clause[0] == ':-':
            head, body = clause[1], clause[2:]
        else:
            head, body = clause, []
        # Register every variable first so indices are stable across the clause.
        for token in self._clause_tokens(head, body):
            if self.is_var(token):
                self.intern_var(token)
        self.compile_head(head)
        self.compile_body(body)
        self.instructions.append(('PROCEED', 0, 0))

    @staticmethod
    def _clause_tokens(head, body):
        yield from head[1:]
        for goal in body:
            if isinstance(goal, list):
                yield from goal[1:]

    # ---- top-level compilation ------------------------------------------

    def compile(self, clauses):
        # First pass: group facts and rules by predicate.
        for clause in clauses:
            if clause[0] == '?-':
                continue
            head = clause[1] if clause[0] == ':-' else clause
            key = (head[0], len(head) - 1)
            self.pred_clauses.setdefault(key, []).append(clause)

        # Second pass: emit each predicate's clauses.
        for key, clauses_for_pred in self.pred_clauses.items():
            if len(clauses_for_pred) > 1:
                self.compile_multi_clause(key, clauses_for_pred)
            else:
                self.predicates[key] = len(self.instructions)
                self.compile_clause(clauses_for_pred[0])

        # Queries last: each gets its own entry point and a trailing HALT.
        for clause in clauses:
            if clause[0] == '?-':
                self.compile_query(clause[1])

    def compile_multi_clause(self, key, clauses):
        """Lay out clauses with TRY_ME_ELSE / RETRY_ME_ELSE / TRUST_ME."""
        self.predicates[key] = len(self.instructions)
        for i, clause in enumerate(clauses):
            control_addr = len(self.instructions)
            if i == 0:
                self.instructions.append(['TRY_ME_ELSE', None, 0])
            elif i < len(clauses) - 1:
                self.instructions.append(['RETRY_ME_ELSE', None, 0])
            else:
                self.instructions.append(['TRUST_ME', 0, 0])
            self.compile_clause(clause)
            # Patch the control instruction to point at the next clause.
            if i < len(clauses) - 1:
                self.instructions[control_addr][1] = len(self.instructions)
        # Freeze the control instructions back into tuples.
        for addr, instr in enumerate(self.instructions):
            if isinstance(instr, list):
                self.instructions[addr] = tuple(instr)

    def compile_query(self, query):
        query_vars = []
        for arg in query[1:]:
            if self.is_var(arg) and arg not in dict(query_vars):
                query_vars.append((arg, self.intern_var(arg)))
        start = len(self.instructions)
        self.compile_goal(query)
        self.instructions.append(('HALT', 0, 0))
        self.query_addrs.append((query, query_vars, start))


def format_query(query):
    name, args = query[0], query[1:]
    return f"{name}({', '.join(args)})"


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
    ['?-', ['sibling', 'john', 'Sibling']],
]


if __name__ == '__main__':
    print("=== COMPILATION ===")
    compiler = Compiler()
    compiler.compile(program)

    print(f"Variables:  {compiler.vars}")
    print(f"Constants:  {compiler.constants}")
    print(f"Predicates: {compiler.predicates}")
    print("\nGenerated code:")
    for addr, instr in enumerate(compiler.instructions):
        print(f"{addr:3d}: {instr}")

    print("\n=== EXECUTION ===")
    for query, query_vars, start in compiler.query_addrs:
        vm = WAM()
        vm.load(compiler)
        vm.query_vars = query_vars
        vm.registers['IP'] = start
        vm.run(find_all=True)

        print(f"\n?- {format_query(query)}.")
        if not vm.solutions:
            print("   false.")
        elif not query_vars:
            print("   true.")
        else:
            for sol in vm.solutions:
                print("   " + ",  ".join(f"{name} = {val}" for name, val in sol.items()))
