#!/bin/zsh
# O5' / Claim 2 self-application fixpoint on the OPTIMIZING compiler (baked -O3).
set -e
cd /Users/setlonnert/Documents/GitHub/ai/stack/lark
T=$(mktemp -d)
export PYTHONPATH=self/tests:07/src
HEAP=$((12000*1024*1024))
SRC=$T/optc_O3.lark

echo "=== assemble optc_O3.lark (baked -O3 optimizing compiler) ==="
python3 -c "from bootstrap_opt import assemble_compiler; open('$SRC','w').write(assemble_compiler(3))"
echo "compiler source: $(wc -l < $SRC) lines, $(wc -c < $SRC) bytes"

run_stage () {  # $1=binary  $2=out.c  $3=err
  ( ulimit -s 65520; $1 < $SRC > $2 2>$3 )
}

echo "=== stage0: Python-hosted emit_tac_c.py -O0 -> c0.c -> clang -> stage1 ==="
python3 07/src/emit_tac_c.py $SRC -O0 > $T/L_c0.c 2>$T/L_s0.err
echo "c0.c: $(wc -c < $T/L_c0.c) bytes  err=[$(cat $T/L_s0.err)]"
cc -O2 -fwrapv -DLARK_HEAP_BYTES=$HEAP $T/L_c0.c -o $T/L_stage1 -lm
echo "built L_stage1: $(wc -c < $T/L_stage1) bytes"

echo "=== stage1: compiler(-O3) compiles its own source -> c1.c ==="
t0=$SECONDS; run_stage $T/L_stage1 $T/L_c1.c $T/L_c1.err; echo "  stage1 exit=$? wall=$((SECONDS-t0))s"
echo "c1.c: $(wc -c < $T/L_c1.c) bytes  err=[$(cat $T/L_c1.err)]"
cc -O2 -fwrapv -DLARK_HEAP_BYTES=$HEAP $T/L_c1.c -o $T/L_stage2 -lm
echo "built L_stage2: $(wc -c < $T/L_stage2) bytes"

echo "=== stage2: self-built compiler compiles its own source -> c2.c ==="
t0=$SECONDS; run_stage $T/L_stage2 $T/L_c2.c $T/L_c2.err; echo "  stage2 exit=$? wall=$((SECONDS-t0))s"
echo "c2.c: $(wc -c < $T/L_c2.c) bytes  err=[$(cat $T/L_c2.err)]"
cc -O2 -fwrapv -DLARK_HEAP_BYTES=$HEAP $T/L_c2.c -o $T/L_stage3 -lm
echo "built L_stage3: $(wc -c < $T/L_stage3) bytes"

echo "=== stage3: compiles its own source -> c3.c ==="
t0=$SECONDS; run_stage $T/L_stage3 $T/L_c3.c $T/L_c3.err; echo "  stage3 exit=$? wall=$((SECONDS-t0))s"
echo "c3.c: $(wc -c < $T/L_c3.c) bytes  err=[$(cat $T/L_c3.err)]"

echo "=== FIXPOINT CHECK ==="
shasum -a 256 $T/L_c0.c $T/L_c1.c $T/L_c2.c $T/L_c3.c
if cmp -s $T/L_c1.c $T/L_c2.c && cmp -s $T/L_c2.c $T/L_c3.c; then
  echo "CLAIM2_OK: C1 == C2 == C3 byte-identical (optimizing self-hosting fixpoint)"
else
  echo "CLAIM2_FAIL: fixpoint not reached"
fi
echo "=== THE WIN (compiling the SAME source optc_O3.lark) ==="
echo "emitted C:  -O0 (c0) $(wc -c < $T/L_c0.c)  vs  -O3 (c1) $(wc -c < $T/L_c1.c) bytes"
echo "binary:     -O0-src (stage1) $(wc -c < $T/L_stage1)  vs  -O3-src (stage2) $(wc -c < $T/L_stage2) bytes"
echo "LADDER_DONE"
