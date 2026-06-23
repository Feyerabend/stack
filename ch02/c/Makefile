# C parallel of the Chapter 2 stack VM.
CC      ?= cc
CFLAGS  ?= -O2 -Wall -Wextra -std=gnu11

stack_vm: stack_vm.c
	$(CC) $(CFLAGS) -o stack_vm stack_vm.c

.PHONY: run bench check diff clean

# samples + benchmark at the default N (20,000,000)
run: stack_vm
	./stack_vm

# benchmark at a larger N
bench: stack_vm
	./stack_vm 50000000

# correctness gate: nonzero exit on any mismatch
check: stack_vm
	@./stack_vm 1000000 >/dev/null && \
	  echo "OK: C VM correct; cascade == switch == goto"

# differential oracle: the C VM and the Python VM must agree on the same sum
diff: stack_vm
	@echo "C:     $$(./stack_vm 300000 | grep '^sum')"
	@echo "Python: $$(python3 ../solutions/ex05_dispatch.py 300000 | grep '^sum')"

clean:
	rm -f stack_vm
