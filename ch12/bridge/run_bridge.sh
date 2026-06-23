#!/bin/sh
# run_bridge.sh — the Lark <-> MLTT bridge, run live.
#
# Demonstrates Chapter 12's central claim (Sec. 12.1, 12.4): type-checking IS
# proof-checking. Each well-typed Lark program corresponds to an intrinsically
# typed term `Expr g t` in Martin-Lof type theory; building that term IS the
# typing derivation; and the lcore kernel CHECKS the derivation by assigning the
# term its type. An ill-typed Lark program corresponds to a non-inhabitant --
# there is no proof to build, and the kernel says so.
#
# This script runs the REAL proof in lark/formal/proof/ (it does not duplicate
# it). It only feeds the kernel and reads back its verdict.

set -e
HERE=$(cd "$(dirname "$0")" && pwd)
PROOF="$HERE/../../lark/formal/proof"
CORE="$PROOF/code/core"
TYPING="$PROOF/lark/lark-typing.lcore"

if [ ! -x "$CORE/lcore" ]; then
  echo "building lcore kernel..."
  ( cd "$CORE" && make >/dev/null 2>&1 )
fi

strip() { grep -v '^--' | grep -v '^[[:space:]]*$'; }
run()   { ( cd "$CORE" && ./lcore ) ; }

echo "============================================================"
echo " The Lark <-> MLTT bridge"
echo "============================================================"
echo
echo "Three well-typed Lark programs, each lifted to an lcore term."
echo "The kernel reports the type it assigns -- i.e. the proposition"
echo "the term proves. That report IS the type checker of Chapter 5,"
echo "viewed as the proof checker of Chapter 12."
echo
echo "  Lark:  fn f(x : Bool) : Bool = x"
echo "  lcore: id_bool : Expr empty (TFn TBool TBool)"
echo "  Lark:  if true then 1 else 2"
echo "  lcore: ite_int : Expr empty TInt"
echo "  Lark:  fn app(f : Int -> Int, x : Int) : Int = f x"
echo "  lcore: apply_f : Expr (ext TInt (ext (TFn TInt TInt) empty)) TInt"
echo
echo "kernel verdict (the assigned types):"
echo "------------------------------------------------------------"
strip < "$TYPING" | run | grep -E ' (id_bool|ite_int|apply_f) : '
echo

echo "============================================================"
echo " The other direction: an ill-typed program has no proof"
echo "============================================================"
echo
echo "  Lark (rejected):  (42)(true)    -- apply an Int as a function"
echo "  lcore:  EApp empty TBool TBool (ELitInt empty) (ELitBool empty true)"
echo
echo "There is no term of this type, so the kernel refuses it:"
echo "------------------------------------------------------------"
BAD=':let bad = (EApp empty TBool TBool (ELitInt empty) (ELitBool empty true) : Expr empty TBool)'
{ strip < "$TYPING"; printf '%s\n' "$BAD"; } | run | grep -A2 'type error' || true
echo
echo "------------------------------------------------------------"
echo "type-checking the Lark program = checking the MLTT proof."
echo "They are one activity in two vocabularies."
