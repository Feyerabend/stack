/*
 * stack_vm.c — a C parallel of ch02/stack_vm.py.
 *
 * The same fifteen-instruction stack machine, implemented THREE ways so the
 * dispatch discussion of Section 2.4 (sec:vm-dispatch) can be measured rather
 * than asserted:
 *
 *   run_cascade  — an if/else-if comparison chain   (the C analogue of Python's
 *                  if/elif; O(n) comparisons per opcode)
 *   run_switch   — a dense switch, which the compiler turns into a jump table
 *   run_goto     — computed goto (a GCC/Clang extension): each handler ends with
 *                  its own indirect branch, giving the branch predictor more to
 *                  work with
 *
 * All three share one set of operation macros, so their semantics are identical
 * by construction — including Python's floor division for DIV, so this VM is a
 * faithful differential twin of stack_vm.py: the same bytecode yields the same
 * result in both. See solutions.md (Exercise 5) for the cross-check.
 *
 * Build & run:   make run            (samples + benchmark at N = 20,000,000)
 *                ./stack_vm 1000000  (choose N)
 *                make check          (asserts correctness, all dispatchers agree)
 */

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Opcodes — identical numbering to stack_vm.py (HALT = 0 … RET = 14). */
enum {
    HALT, PUSH, ADD, SUB, MUL, DIV, EQ, LT, NOT,
    JMP, JMPZ, LOAD, STORE, CALL, RET
};

#define STACK_MAX 65536
#define FRAME_MAX 4096

typedef struct { int64_t locals[16]; int ret_pc; } Frame;

/* Python's // rounds toward negative infinity; C's / truncates toward zero.
 * Match Python so the two VMs agree on mixed-sign division (the chapter's
 * "one simplification to flag"). */
static inline int64_t floordiv(int64_t a, int64_t b) {
    int64_t q = a / b, r = a % b;
    if (r != 0 && ((r < 0) != (b < 0))) q--;
    return q;
}

/* One definition of each opcode's effect, shared by all three dispatchers.
 * They read/write the locals declared in each run_* function: code, pc, sp,
 * stack, locals, frames, fp. */
#define RD_U16()  ((uint16_t)((code[pc] << 8) | code[pc + 1]))

#define DO_PUSH   (stack[++sp] = code[pc++])
#define DO_ADD    do { int64_t b = stack[sp--]; stack[sp] += b; } while (0)
#define DO_SUB    do { int64_t b = stack[sp--]; stack[sp] -= b; } while (0)
#define DO_MUL    do { int64_t b = stack[sp--]; stack[sp] *= b; } while (0)
#define DO_DIV    do { int64_t b = stack[sp--]; stack[sp] = floordiv(stack[sp], b); } while (0)
#define DO_EQ     do { int64_t b = stack[sp--]; stack[sp] = (stack[sp] == b); } while (0)
#define DO_LT     do { int64_t b = stack[sp--]; stack[sp] = (stack[sp] <  b); } while (0)
#define DO_NOT    (stack[sp] = !stack[sp])
#define DO_JMP    do { pc = RD_U16(); } while (0)
#define DO_JMPZ   do { uint16_t t = RD_U16(); pc += 2; if (stack[sp--] == 0) pc = t; } while (0)
#define DO_LOAD   do { uint8_t s = code[pc++]; stack[++sp] = locals[s]; } while (0)
#define DO_STORE  do { uint8_t s = code[pc++]; locals[s] = stack[sp--]; } while (0)
#define DO_CALL   do { uint16_t t = RD_U16(); pc += 2;                     \
                       memcpy(frames[fp].locals, locals, sizeof locals);   \
                       frames[fp].ret_pc = pc; fp++;                       \
                       memset(locals, 0, sizeof locals); pc = t; } while (0)
#define DO_RET    do { int64_t v = stack[sp--]; fp--;                      \
                       memcpy(locals, frames[fp].locals, sizeof locals);   \
                       pc = frames[fp].ret_pc; stack[++sp] = v; } while (0)

#define DECLARE_STATE                                  \
    int64_t stack[STACK_MAX]; int sp = -1;             \
    int64_t locals[16] = {0}; locals[0] = init0;       \
    Frame frames[FRAME_MAX]; int fp = 0;               \
    int pc = 0

/* ── 1. comparison cascade ──────────────────────────────────────────────── */
static int64_t run_cascade(const uint8_t *code, int64_t init0) {
    DECLARE_STATE;
    for (;;) {
        uint8_t op = code[pc++];
        if      (op == HALT)  return sp >= 0 ? stack[sp] : 0;
        else if (op == PUSH)  DO_PUSH;
        else if (op == ADD)   DO_ADD;
        else if (op == SUB)   DO_SUB;
        else if (op == MUL)   DO_MUL;
        else if (op == DIV)   DO_DIV;
        else if (op == EQ)    DO_EQ;
        else if (op == LT)    DO_LT;
        else if (op == NOT)   DO_NOT;
        else if (op == JMP)   DO_JMP;
        else if (op == JMPZ)  DO_JMPZ;
        else if (op == LOAD)  DO_LOAD;
        else if (op == STORE) DO_STORE;
        else if (op == CALL)  DO_CALL;
        else if (op == RET)   DO_RET;
        else { fprintf(stderr, "bad op %d at pc=%d\n", op, pc - 1); exit(1); }
    }
}

/* ── 2. switch (compiler builds a jump table) ───────────────────────────── */
static int64_t run_switch(const uint8_t *code, int64_t init0) {
    DECLARE_STATE;
    for (;;) {
        uint8_t op = code[pc++];
        switch (op) {
            case HALT:  return sp >= 0 ? stack[sp] : 0;
            case PUSH:  DO_PUSH;  break;
            case ADD:   DO_ADD;   break;
            case SUB:   DO_SUB;   break;
            case MUL:   DO_MUL;   break;
            case DIV:   DO_DIV;   break;
            case EQ:    DO_EQ;    break;
            case LT:    DO_LT;    break;
            case NOT:   DO_NOT;   break;
            case JMP:   DO_JMP;   break;
            case JMPZ:  DO_JMPZ;  break;
            case LOAD:  DO_LOAD;  break;
            case STORE: DO_STORE; break;
            case CALL:  DO_CALL;  break;
            case RET:   DO_RET;   break;
            default: fprintf(stderr, "bad op %d at pc=%d\n", op, pc - 1); exit(1);
        }
    }
}

/* ── 3. computed goto (GCC/Clang) ───────────────────────────────────────── */
#if defined(__GNUC__)
#define HAVE_COMPUTED_GOTO 1
static int64_t run_goto(const uint8_t *code, int64_t init0) {
    DECLARE_STATE;
    void *table[] = {
        &&do_halt, &&do_push, &&do_add, &&do_sub, &&do_mul, &&do_div,
        &&do_eq, &&do_lt, &&do_not, &&do_jmp, &&do_jmpz, &&do_load,
        &&do_store, &&do_call, &&do_ret
    };
    #define NEXT() goto *table[code[pc++]]
    NEXT();
    do_halt:  return sp >= 0 ? stack[sp] : 0;
    do_push:  DO_PUSH;  NEXT();
    do_add:   DO_ADD;   NEXT();
    do_sub:   DO_SUB;   NEXT();
    do_mul:   DO_MUL;   NEXT();
    do_div:   DO_DIV;   NEXT();
    do_eq:    DO_EQ;    NEXT();
    do_lt:    DO_LT;    NEXT();
    do_not:   DO_NOT;   NEXT();
    do_jmp:   DO_JMP;   NEXT();
    do_jmpz:  DO_JMPZ;  NEXT();
    do_load:  DO_LOAD;  NEXT();
    do_store: DO_STORE; NEXT();
    do_call:  DO_CALL;  NEXT();
    do_ret:   DO_RET;   NEXT();
    #undef NEXT
}
#else
#define HAVE_COMPUTED_GOTO 0
static int64_t run_goto(const uint8_t *code, int64_t init0) {
    return run_switch(code, init0);   /* fallback where the extension is absent */
}
#endif

/* ── Sample programs (same bytecode the Python VM runs) ──────────────────── */

/* 3 * (4 + 5) = 27 */
static const uint8_t prog_mul[] = {
    PUSH, 3, PUSH, 4, PUSH, 5, ADD, MUL, HALT
};

/* factorial(5) = 120 (identical layout to stack_vm.py's `fact`) */
static const uint8_t prog_fact[] = {
    PUSH, 5, CALL, 0, 6, HALT,
    STORE, 0, LOAD, 0, PUSH, 1, LT, NOT, JMPZ, 0, 29,
    LOAD, 0, LOAD, 0, PUSH, 1, SUB, CALL, 0, 6, MUL, RET,
    PUSH, 1, RET
};

/* sum 1..N : locals[0] = N (preset via init0), locals[1] = acc.
 * Same bytecode as solutions/ex05_dispatch.py (end @ 25). */
static const uint8_t prog_sum[] = {
    /* 0  loop */ PUSH, 0, LOAD, 0, LT,
    /* 5  */      JMPZ, 0, 25,
    /* 8  */      LOAD, 1, LOAD, 0, ADD, STORE, 1,
    /* 15 */      LOAD, 0, PUSH, 1, SUB, STORE, 0,
    /* 22 */      JMP, 0, 0,
    /* 25 end */  LOAD, 1, HALT
};

/* ── Benchmark helper ───────────────────────────────────────────────────── */
typedef int64_t (*run_fn)(const uint8_t *, int64_t);

static double bench(run_fn fn, const uint8_t *code, int64_t N, int reps) {
    double best = 1e30;
    for (int i = 0; i < reps; i++) {
        struct timespec a, b;
        clock_gettime(CLOCK_MONOTONIC, &a);
        volatile int64_t r = fn(code, N); (void) r;
        clock_gettime(CLOCK_MONOTONIC, &b);
        double t = (b.tv_sec - a.tv_sec) + (b.tv_nsec - a.tv_nsec) / 1e9;
        if (t < best) best = t;
    }
    return best;
}

int main(int argc, char **argv) {
    long N = argc > 1 ? atol(argv[1]) : 20000000L;

    /* correctness — these must match stack_vm.py exactly */
    int64_t r_mul  = run_switch(prog_mul, 0);
    int64_t r_fact = run_switch(prog_fact, 0);
    if (r_mul != 27 || r_fact != 120) {
        fprintf(stderr, "FAIL samples: %lld %lld\n",
                (long long) r_mul, (long long) r_fact);
        return 1;
    }
    printf("3 * (4 + 5)  = %lld\n", (long long) r_mul);
    printf("factorial(5) = %lld\n", (long long) r_fact);

    /* all three dispatchers must agree on the sum (differential within C) */
    int64_t expected = (int64_t) N * (N + 1) / 2;
    int64_t s_casc = run_cascade(prog_sum, N);
    int64_t s_sw   = run_switch(prog_sum, N);
    int64_t s_go   = run_goto(prog_sum, N);
    if (s_casc != expected || s_sw != expected || s_go != expected) {
        fprintf(stderr, "FAIL sum: cascade=%lld switch=%lld goto=%lld expected=%lld\n",
                (long long) s_casc, (long long) s_sw,
                (long long) s_go, (long long) expected);
        return 1;
    }
    printf("sum 1..%ld = %lld  (cascade == switch == goto)\n",
           N, (long long) expected);

    /* benchmark: best of 3 */
    double t_casc = bench(run_cascade, prog_sum, N, 3);
    double t_sw   = bench(run_switch,  prog_sum, N, 3);
    double t_go   = bench(run_goto,    prog_sum, N, 3);

    printf("\ndispatch on sum 1..%ld (best of 3, lower is better):\n", N);
    printf("  %-20s%10s\n", "strategy", "seconds");
    printf("  %-20s%10.3f\n", "comparison cascade", t_casc);
    printf("  %-20s%10.3f\n", "switch", t_sw);
    printf("  %-20s%10.3f%s\n", "computed goto", t_go,
           HAVE_COMPUTED_GOTO ? "" : "  (fell back to switch)");
    return 0;
}
