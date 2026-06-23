"""
Chapter 10, Exercise 5 — solution code.

Every implementation choice is a semantic claim. (a) call-by-name changes one of
the two congruence rules of Section 10.x — which, and how? (b) give an expression
whose result/termination differs under call-by-name, and the observable
difference. (c) why is Lark's call-by-value visible in the CEK machine's
ApplyArgF frame?

How to run:   python3 ex05_cbn_cbv.py
Expected:     "(λx.0) Ω : call-by-name -> 0; call-by-value -> diverges"

Uses the companion machines vm-theory/code/krivine (call-by-name) and
vm-theory/code/cek (call-by-value).

(a) THE CHANGED RULE. The two congruence rules say where reduction may happen in
    an application: one lets the function position step (e1 → e1'  ⟹  e1 e2 →
    e1' e2), the other lets the ARGUMENT step (e2 → e2'  ⟹  v e2 → v e2', once the
    function is a value). Call-by-value KEEPS the argument-congruence rule: the
    argument is reduced to a value before the function is entered. Call-by-name
    DROPS it: the argument is passed UNEVALUATED (as a thunk) and reduced only if
    and when the body uses it. So the operand-evaluation congruence rule is the
    one that changes — present under CBV, absent under CBN.

(b) THE OBSERVABLE DIFFERENCE. Let Ω = (λx. x x)(λx. x x) be a non-terminating
    term, and consider (λx. 0) Ω. Under CALL-BY-NAME the argument Ω is never
    used (the body is just 0), so the program returns 0. Under CALL-BY-VALUE the
    argument must be reduced first, so evaluation diverges. Same expression: one
    rule produces a value, the other never terminates — the most observable
    difference there is.

(c) CALL-BY-VALUE IN ApplyArgF. Lark's CEK pushes an ApplyArgF frame to evaluate
    each argument to a VALUE before entering the closure (it only applies the
    function once the argument has returned). That frame is the operand-congruence
    rule made into a machine step: its very existence is the commitment to
    call-by-value. A call-by-name machine (the Krivine machine) has no such
    frame — it binds the argument as an unevaluated thunk and enters the body
    immediately.
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_VM = os.path.join(_HERE, "..", "vm-theory", "code")
sys.path.insert(0, os.path.join(_VM, "krivine"))
sys.path.insert(0, os.path.join(_VM, "cek"))

import krivine as kr   # call-by-name  # noqa: E402
import cek as ck       # call-by-value # noqa: E402


def omega(M):
    """Ω = (λx. x x)(λx. x x) — diverges under CBV, harmless under CBN."""
    self_app = M.Lam("x", M.App(M.Var("x"), M.Var("x")))
    return M.App(self_app, self_app)


if __name__ == "__main__":
    # (λx. 0) Ω
    cbn_term = kr.App(kr.Lam("x", kr.Num(0)), omega(kr))
    cbv_term = ck.App(ck.Lam("x", ck.Num(0)), omega(ck))

    # call-by-name: argument never used -> returns 0 quickly
    cbn_result = kr.run(cbn_term, max_steps=1000)
    assert str(cbn_result) == "0", cbn_result

    # call-by-value: must evaluate the argument first -> diverges (step-capped)
    diverged = False
    try:
        ck.run(cbv_term, max_steps=1000)
    except RuntimeError:
        diverged = True
    assert diverged, "call-by-value should diverge on (λx.0) Ω"

    print(f"(λx.0) Ω : call-by-name -> {cbn_result}; call-by-value -> diverges")
