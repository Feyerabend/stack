CC      = cc
CFLAGS  = -std=c99 -Wall -Wextra -O2 -pedantic
TARGET  = m6502/m6502
BASIC   = basic/basic.bin
ASM     = python3 a6502/asm.py

all: $(TARGET)

$(TARGET): m6502/m6502.c m6502/main.c m6502/m6502.h
	$(CC) $(CFLAGS) -o $(TARGET) m6502/m6502.c m6502/main.c

$(TEST): m6502/m6502.c m6502/test_dormann.c m6502/m6502.h
	$(CC) $(CFLAGS) -o $(TEST) m6502/m6502.c m6502/test_dormann.c

run: $(TARGET) $(BASIC)
	./$(TARGET) -r -a 800 $(BASIC)

$(BASIC): basic/basic.asm
	$(ASM) basic/basic.asm $(BASIC)

basic: $(TARGET) $(BASIC)
	@echo "Load at \$$0800.  Run with:  ./$(TARGET) -a 800 $(BASIC)"
	./$(TARGET) -a 800 $(BASIC)

assemble: $(BASIC)
	@echo "Assembled -> $(BASIC)"

clean:
	rm -f $(TARGET)

.PHONY: all run clean basic assemble
