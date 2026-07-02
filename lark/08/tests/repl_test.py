"""
Lark REPL smoke test — pipes a fixed input sequence and checks output.

Runs non-interactively: stdin is a pipe, so readline line-editing is
inactive but the REPL loop still works correctly.
"""
from __future__ import annotations
import subprocess, sys, pathlib

SRC  = pathlib.Path(__file__).parent.parent / "src"
REPL = str(SRC / "repl.py")

PASS = 0
FAIL = 0


def run_repl(input_text: str) -> str:
    r = subprocess.run(
        [sys.executable, REPL],
        input=input_text, capture_output=True, text=True, timeout=30,
    )
    return r.stdout + r.stderr


def check(label: str, got: str, want: str) -> None:
    global PASS, FAIL
    if want in got:
        print(f"  ok    {label}")
        PASS += 1
    else:
        print(f"  FAIL  {label}")
        print(f"          want: {want!r}")
        print(f"          got:  {got!r}")
        FAIL += 1


# ── Test 1: basic expressions and declarations ───────────────────────────────

SESSION1 = "\n".join([
    "fn double(n : Int) : Int = n * 2",
    "double(21)",
    'let greeting = "hello"',
    "greeting",
    "1 + 1",
    "true",
    "show(42)",
    "3.14",
    ":type 42",
    ":type double",
    ":quit",
])

out1 = run_repl(SESSION1)

print("── basic ──────────────────────────────────────────────────────────────")
check("fn shows type",        out1, "fn double : Int -> Int")
check("function call",        out1, "42 : Int")
check("let declaration",      out1, "let greeting : String = hello")
check("string expression",    out1, "hello : String")
check("arithmetic",           out1, "2 : Int")
check("boolean",              out1, "true : Bool")
check("show(42) is String",   out1, "42 : String")
check("float literal",        out1, "3.14 : Float")
check(":type Int literal",    out1, "Int")
check(":type fn",             out1, "Int -> Int")

# ── Test 2: ADTs and pattern matching ────────────────────────────────────────

SESSION2 = "\n".join([
    "type Color = | Red | Green | Blue",
    "Red",
    "let c = Green",
    "fn color_str(c : Color) : String = match c with | Red => \"red\" | Green => \"green\" | Blue => \"blue\" end",
    'color_str(Blue)',
    ":quit",
])

out2 = run_repl(SESSION2)

print("── ADT ────────────────────────────────────────────────────────────────")
check("type registration",    out2, "type Color registered")
check("constructor value",    out2, "Red : Color")
check("let ADT binding",      out2, "let c : Color = Green")
check("fn on ADT",            out2, "fn color_str : Color -> String")
check("pattern match call",   out2, "blue : String")

# ── Test 3: impl Show and dispatch ───────────────────────────────────────────

SESSION3 = "\n".join([
    "type Shape = | Circle of Float | Square of Float",
    "impl Show for Shape = { fn show(s) = match s with | Circle(r) => \"circle\" | Square(w) => \"square\" end }",
    "show(Circle(3.0))",
    "show(42)",
    ":quit",
])

out3 = run_repl(SESSION3)

print("── impl Show ──────────────────────────────────────────────────────────")
check("impl registration",    out3, "impl Show for Shape registered")
check("user show dispatch",   out3, "circle : String")
check("primitive show after", out3, "42 : String")

# ── Test 4: error recovery ───────────────────────────────────────────────────

SESSION4 = "\n".join([
    "1 / 0",
    "bad name",
    "42",
    ":reset",
    "42",
    ":quit",
])

out4 = run_repl(SESSION4)

print("── errors ─────────────────────────────────────────────────────────────")
check("division by zero is caught",   out4, "error:")
check("still works after error",      out4, "42 : Int")
check("reset clears env",             out4, "-- environment cleared")
check("works after reset",            out4, "42 : Int")

# ── Test 5: recursion ────────────────────────────────────────────────────────

SESSION5 = "\n".join([
    "fn fact(n : Int) : Int = if n == 0 then 1 else n * fact(n - 1)",
    "fact(10)",
    ":quit",
])

out5 = run_repl(SESSION5)

print("── recursion ──────────────────────────────────────────────────────────")
check("recursive fn type",    out5, "fn fact : Int -> Int")
check("fact(10) = 3628800",   out5, "3628800 : Int")

# ── Test 6: polymorphic functions ────────────────────────────────────────────

SESSION6 = "\n".join([
    "fn id(x) = x",
    ":type id",
    ":quit",
])

out6 = run_repl(SESSION6)

print("── polymorphism ───────────────────────────────────────────────────────")
check("id has polymorphic type",  out6, "α -> α")

# ── Test 7: edge cases and commands ─────────────────────────────────────────

SESSION7 = "\n".join([
    ":help",
    ":type",
    ":foo",
    "(1, 2)",
    ":quit",
])

out7 = run_repl(SESSION7)

print("── edge cases ─────────────────────────────────────────────────────────")
check(":help shows commands",        out7, "Commands:")
check(":type no arg gives usage",    out7, "usage: :type <expr>")
check("unknown command message",     out7, ":help for commands")
check("tuple expression display",    out7, "(1, 2) : (Int, Int)")

# ── Test 8: lex error recovery ───────────────────────────────────────────────

SESSION8 = "\n".join([
    "fn bad(x : Int) : Int = x",
    "42",
    ":quit",
])

out8 = run_repl(SESSION8)

print("── lex error recovery ─────────────────────────────────────────────────")
check("valid fn after session start",  out8, "fn bad : Int -> Int")
check("expression still works",        out8, "42 : Int")

# ── Summary ──────────────────────────────────────────────────────────────────

total = PASS + FAIL
print(f"\n  {PASS} passed, {FAIL} failed  ({total} total)")
if FAIL:
    sys.exit(1)
