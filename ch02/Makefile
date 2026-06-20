.PHONY: all run clean

PYTHON := python3

all: run

SRCS   := stack_vm.py reg_vm.py assembler.py control_flow.py

run: $(SRCS)
	@$(PYTHON) stack_vm.py
	@$(PYTHON) reg_vm.py
	@$(PYTHON) assembler.py
	@$(PYTHON) control_flow.py

clean:
	@rm -rf __pycache__
