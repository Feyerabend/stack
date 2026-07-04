#!/bin/sh
# run_bugs.sh — Chapter 13's bugs, reproduced live.
#
# Each of the chapter's language-level bugs is pinned by an error test in
# lark/09/tests/errors/, and this script runs the real checker on each one so
# the diagnostic on the page is the diagnostic on your screen:
#
#   Sec. 13.1  the exhaustiveness witness  (10_nonexh_nested.lark)
#   Sec. 13.1  totality refuses n - 1      (12_total_int.lark)
#   Sec. 13.2  the RV32 miscompile, now an ambiguity error  (15_ambig_op.lark)
#   Sec. 13.5  the affine-capture hole, closed               (16_affine_capture.lark)
#
# This script drives the REAL Phase 9 compiler in lark/09/ (it duplicates
# nothing). Every program below is REJECTED — that is the point: each was,
# or would have been, a runtime failure or a silent miscompilation before
# the chapter's work turned it into a diagnostic.

set -e
HERE=$(cd "$(dirname "$0")" && pwd)
LARK=""
for c in "$HERE/../../lark" "$HERE/../../.."; do
  if [ -f "$c/09/src/infer.py" ]; then LARK=$(cd "$c" && pwd); break; fi
done
[ -n "$LARK" ] || { echo "error: cannot find the lark tree (lark/09/)"; exit 1; }
CEK="$LARK/09/src/cek.py"
ERR="$LARK/09/tests/errors"

show() {  # show <title> <file>  — print the program body, then its verdict
  echo "============================================================"
  echo " $1"
  echo "============================================================"
  sed -n '/^module/,$p' "$ERR/$2"
  echo "------------------------------------------------------------"
  printf 'checker verdict:  '
  python3 "$CEK" "$ERR/$2" 2>&1 || true
  echo
}

show "Sec. 13.1 -- the missing case IS the error message" \
     10_nonexh_nested.lark
show "Sec. 13.1 -- Int wraps, so n - 1 is not descent" \
     12_total_int.lark
show "Sec. 13.2 -- the program that miscompiled on RV32, now rejected" \
     15_ambig_op.lark
show "Sec. 13.5 -- the closure that duplicated the IO token, now rejected" \
     16_affine_capture.lark

echo "============================================================"
echo "Four programs, four rejections. Before Chapter 13's work these"
echo "were: a runtime trap, an infinite loop, a silent miscompilation,"
echo "and a soundness hole. A diagnostic is the cheapest place a bug"
echo "will ever be caught."
