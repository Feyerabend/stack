/*
 * Lark runtime — platform-independent implementation.
 *
 * Heap: bump-pointer allocator over a static array.  No GC.
 * Strings: [uint32_t len][UTF-8 bytes]['\0'][4-byte alignment pad].
 * Floats: passed as uint32_t bit patterns (IEEE 754 float32).
 *         On RV32IMAC (no FPU) the compiler emits softfloat calls automatically.
 */

#include "runtime.h"
#include <string.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

/* ── Heap ─────────────────────────────────────────────────────────────────── */

#ifndef LARK_HEAP_BYTES
#  define LARK_HEAP_BYTES (64 * 1024)   /* 64 KB — adjust for target */
#endif

/* aligned(8): the bump allocator hands out 4-byte-multiple offsets, but a bare
 * uint8_t[] has alignment 1 — a misaligned base makes every word write (p[0]=...)
 * trap on real RISC-V though the byte-indexed Python VM tolerates it. */
static uint8_t  _heap[LARK_HEAP_BYTES] __attribute__((aligned(8)));
static uint32_t _heap_ptr = 0;

lark_ptr __heap_alloc(int n_words) {
    uint32_t bytes = (uint32_t)n_words * 4u;
    bytes = (bytes + 3u) & ~3u;          /* 4-byte align */
    if (_heap_ptr + bytes > LARK_HEAP_BYTES) {
        __lark_match_fail();             /* reuse the fatal-error path */
    }
    lark_ptr p = (lark_ptr)(_heap + _heap_ptr);
    _heap_ptr += bytes;
    return p;
}

lark_ptr lark_alloc_string(const char* text) {
    uint32_t len    = (uint32_t)strlen(text);
    uint32_t data_words = (len + 1u + 3u) / 4u;  /* ceil((len+1)/4) words */
    lark_ptr p = __heap_alloc(1 + (int)data_words);
    p[0] = len;
    memcpy((char*)(p + 1), text, len + 1);        /* +1 for '\0' */
    return p;
}


/* ── String operations ───────────────────────────────────────────────────── */

lark_ptr __str_concat(lark_ptr a, lark_ptr b) {
    uint32_t la = a[0], lb = b[0];
    uint32_t total      = la + lb;
    uint32_t data_words = (total + 1u + 3u) / 4u;
    lark_ptr result     = __heap_alloc(1 + (int)data_words);
    result[0] = total;
    char* dst = (char*)(result + 1);
    memcpy(dst,      lark_str_data(a), la);
    memcpy(dst + la, lark_str_data(b), lb);
    dst[total] = '\0';
    return result;
}

int string_length(lark_ptr s) {
    return (int)s[0];
}


/* ── Show / conversion ───────────────────────────────────────────────────── */

lark_ptr show(int n) {
    char buf[24];
    snprintf(buf, sizeof(buf), "%d", n);
    return lark_alloc_string(buf);
}

lark_ptr __show_float(uint32_t bits) {
    float f;
    memcpy(&f, &bits, 4);
    char buf[32];
    snprintf(buf, sizeof(buf), "%.7g", f);
    /* The Pico SDK printf does not trim trailing zeros from %g ("8.500000");
     * host libc does ("8.5").  Trim here so hardware matches the other backends. */
    {
        char *dot = strchr(buf, '.');
        if (dot && !strpbrk(buf, "eEni")) {
            char *end = buf + strlen(buf) - 1;
            while (end > dot + 1 && *end == '0') *end-- = '\0';
        }
    }
    /* Ensure a decimal point is present so the value reads as a float. */
    if (!strchr(buf, '.') && !strchr(buf, 'e') && !strchr(buf, 'n') && !strchr(buf, 'i')) {
        size_t n = strlen(buf);
        buf[n]   = '.';
        buf[n+1] = '0';
        buf[n+2] = '\0';
    }
    return lark_alloc_string(buf);
}

lark_ptr __show_bool(int b) {
    return lark_alloc_string(b ? "true" : "false");
}

uint32_t int_to_float(int n) {
    float f = (float)n;
    uint32_t bits;
    memcpy(&bits, &f, 4);
    return bits;
}

int float_to_int(uint32_t bits) {
    float f;
    memcpy(&f, &bits, 4);
    return (int)f;   /* truncate toward zero */
}

lark_ptr int_to_string(int n) {
    return show(n);
}

lark_ptr float_to_string(uint32_t bits) {
    return __show_float(bits);
}


/* ── Float arithmetic ────────────────────────────────────────────────────── */

/* On RV32IMAC (no FPU) the compiler turns float operations into softfloat
 * calls (__addsf3 etc.).  pico_float overrides those with optimised versions.
 * We just write plain C float arithmetic and let the toolchain handle it. */

#define FLOAT_BINOP(name, op) \
    uint32_t name(uint32_t a_bits, uint32_t b_bits) { \
        float a, b, r;                    \
        memcpy(&a, &a_bits, 4);           \
        memcpy(&b, &b_bits, 4);           \
        r = a op b;                       \
        uint32_t r_bits;                  \
        memcpy(&r_bits, &r, 4);           \
        return r_bits;                    \
    }

FLOAT_BINOP(__float_add, +)
FLOAT_BINOP(__float_sub, -)
FLOAT_BINOP(__float_mul, *)

uint32_t __float_div(uint32_t a_bits, uint32_t b_bits) {
    float a, b, r;
    memcpy(&a, &a_bits, 4);
    memcpy(&b, &b_bits, 4);
    r = (b == 0.0f) ? __builtin_nanf("") : a / b;
    uint32_t r_bits;
    memcpy(&r_bits, &r, 4);
    return r_bits;
}


/* ── Float comparisons ───────────────────────────────────────────────────── */

#define FLOAT_CMP(name, op) \
    int name(uint32_t a_bits, uint32_t b_bits) { \
        float a, b;                       \
        memcpy(&a, &a_bits, 4);           \
        memcpy(&b, &b_bits, 4);           \
        return (a op b) ? 1 : 0;          \
    }

FLOAT_CMP(__float_lt, <)
FLOAT_CMP(__float_le, <=)
FLOAT_CMP(__float_gt, >)
FLOAT_CMP(__float_ge, >=)


/* ── Math built-ins ──────────────────────────────────────────────────────── */

int int_abs(int n) {
    return n < 0 ? -n : n;
}

uint32_t float_abs(uint32_t bits) {
    return bits & 0x7FFFFFFFu;   /* clear IEEE 754 sign bit */
}

uint32_t float_sqrt(uint32_t bits) {
    float f, r;
    memcpy(&f, &bits, 4);
    r = sqrtf(f);                /* NaN for negative inputs — correct behaviour */
    uint32_t r_bits;
    memcpy(&r_bits, &r, 4);
    return r_bits;
}

uint32_t float_floor(uint32_t bits) {
    float f, r;
    memcpy(&f, &bits, 4);
    r = floorf(f);
    uint32_t r_bits;
    memcpy(&r_bits, &r, 4);
    return r_bits;
}

uint32_t float_ceil(uint32_t bits) {
    float f, r;
    memcpy(&f, &bits, 4);
    r = ceilf(f);
    uint32_t r_bits;
    memcpy(&r_bits, &r, 4);
    return r_bits;
}


/* ── Runtime error ───────────────────────────────────────────────────────── */

void __lark_match_fail(void) {
    /* Platform I/O may not be ready yet (called from heap overflow too).
     * Write directly to stderr; on bare-metal this may be a no-op. */
    fputs("lark: non-exhaustive pattern match\n", stderr);
    abort();
}
