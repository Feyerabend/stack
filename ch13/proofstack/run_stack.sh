#!/bin/sh
# run_stack.sh — the seven-file proof stack, green, then lied to twice.
#
# Chapter 13 grew the proof stack of Chapter 12 from four files to seven
# (adding the graded affine model, the weaken discharge, and the erasure
# functor), and made the kernel strict: every line is type-checked before
# it is normalised, and any failure turns the whole run's exit code red
# (Sec. 13.6). This script demonstrates all three facts on the REAL kernel
# and the REAL proof files in lark/formal/proof/ (nothing is duplicated):
#
#   1. the full stack checks -- exit 0, machine-checkably green;
#   2. a planted bare claim, (star : Empty), turns the run red (the
#      "front door" failure of Sec. 13.6, now closed);
#   3. a planted fix-"proof" of Empty is refused at the gate (the
#      inconsistency of Sec. 13.6, now walled off).

set -e
HERE=$(cd "$(dirname "$0")" && pwd)
PROOF=""
for c in "$HERE/../../lark/formal/proof" "$HERE/../../../formal/proof"; do
  if [ -f "$c/lark/lark-erase.lcore" ]; then PROOF=$(cd "$c" && pwd); break; fi
done
[ -n "$PROOF" ] || { echo "error: cannot find lark/formal/proof/"; exit 1; }
CORE="$PROOF/code/core"

if [ ! -x "$CORE/lcore" ]; then
  echo "building lcore kernel..."
  ( cd "$CORE" && make >/dev/null 2>&1 )
fi

STACK=$(mktemp)
trap 'rm -f "$STACK"' EXIT
for f in lark-typing lark-affine lark-weaken lark-subst lark-step \
         lark-preservation lark-erase; do
  grep -v '^--' "$PROOF/lark/$f.lcore" | grep -v '^[[:space:]]*$'
done > "$STACK"

echo "============================================================"
echo " 1. The seven-file stack: typing, affine, weaken, subst,"
echo "    step, preservation, erase"
echo "============================================================"
if "$CORE/lcore" < "$STACK" > /tmp/lcore_stack_out.$$ 2>&1; then
  N=$(grep -c ' : ' /tmp/lcore_stack_out.$$)
  echo "exit 0 -- every claim checked ($N accepted lines), among them:"
  for name in weaken_l no_second_use capture_rejected \
              eval_produces_val graded_eval_sound; do
    grep -oE "^>? *$name : .{0,48}" /tmp/lcore_stack_out.$$ | head -1
  done
else
  echo "STACK FAILED -- this should not happen"; exit 1
fi
rm -f /tmp/lcore_stack_out.$$
echo

echo "============================================================"
echo " 2. Planted lie #1: a bare claim of falsehood"
echo "============================================================"
echo "    (star : Empty)     -- once normalised on faith (Sec. 13.6)"
if { cat "$STACK"; echo '(star : Empty)'; } | "$CORE/lcore" >/dev/null 2>&1; then
  echo "NOT CAUGHT -- this should not happen"; exit 1
else
  echo "exit 1 -- the kernel type-checks bare terms now; the lie is refused."
fi
echo

echo "============================================================"
echo " 3. Planted lie #2: a fix-'proof' of Empty"
echo "============================================================"
echo "    :let bad = (fix (\\x. x) : Empty)   -- once accepted (Sec. 13.6)"
if { cat "$STACK"; echo ':let bad = (fix (\x. x) : Empty)'; } \
     | "$CORE/lcore" >/dev/null 2>&1; then
  echo "NOT CAUGHT -- this should not happen"; exit 1
else
  { cat "$STACK"; echo ':let bad = (fix (\x. x) : Empty)'; } \
    | "$CORE/lcore" 2>&1 | grep -m1 "'fix'" || true
  echo "exit 1 -- general recursion is gated out of the proof kernel."
fi
echo
echo "------------------------------------------------------------"
echo "Green because it was checked; red because it was lied to and"
echo "noticed. Both verdicts are exit codes -- a build script can"
echo "hold the kernel to them, which is Sec. 13.6's whole repair."
