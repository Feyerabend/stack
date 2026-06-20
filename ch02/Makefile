.PHONY: all run clean

PYTHON := python3
SRCS   := stack_vm.py reg_vm.py assembler.py

all: run

run: $(SRCS)
	@$(PYTHON) stack_vm.py
	@$(PYTHON) reg_vm.py
	@$(PYTHON) assembler.py

clean:
	@rm -rf __pycache__
