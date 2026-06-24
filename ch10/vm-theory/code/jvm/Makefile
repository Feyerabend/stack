# Build and run the JVM interpreter demos.
#
# Compiling the examples needs a Java compiler. OpenJDK from Homebrew is keg-only,
# so either put it on PATH or point JAVAC at it:
#
#   make run JAVAC=/opt/homebrew/opt/openjdk/bin/javac
#
# The committed Example.class runs without a JDK; the examples/ sources must be
# compiled first (their .class files are build artifacts, not tracked).

PYTHON ?= python3
JAVAC  ?= javac

# Each example lives in its own folder under examples/, as <folder>/<MainClass>.
EXAMPLES := arithmetic/Arithmetic factorial/Factorial sumloop/SumLoop gcd/Gcd

.PHONY: all run examples test clean

all: run

run: examples
	@echo "== Example (committed .class) =="
	@$(PYTHON) main.py Example .
	@for e in $(EXAMPLES); do \
	  dir=examples/$${e%/*}; cls=$${e##*/}; \
	  echo; echo "== $$cls =="; \
	  $(PYTHON) main.py $$cls $$dir || exit 1; \
	done

examples:
	@for e in $(EXAMPLES); do \
	  $(JAVAC) examples/$${e%/*}/$${e##*/}.java || exit 1; \
	done

test:
	@$(PYTHON) quick_test.py

clean:
	@find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
	@find examples -name '*.class' -delete 2>/dev/null || true
	@echo "jvm clean."
