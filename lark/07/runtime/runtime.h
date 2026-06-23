/*
 * Lark runtime — public API
 *
 * Every function declared here is called by names emitted in Lark-generated
 * assembly.  The names must match exactly what asm.py / lower.py produce.
 *
 * Heap layout (all words are 4 bytes, all pointers 32-bit on RV32):
 *   ADT / tuple : [uint32_t tag_id,  word field0, word field1, ...]
 *   Closure     : [uint32_t fn_ptr,  word cap0,   word cap1,   ...]
 *   String      : [uint32_t length,  char bytes..., '\0',       pad]
 *
 * "lark_ptr" is the canonical Lark heap pointer type: uint32_t* pointing
 * at the first word of any heap object.  Passing lark_ptr in a0 matches
 * the RV32 ABI (pointer = 32-bit integer register).
 */

#pragma once
#include <stdint.h>
#include <stddef.h>

typedef uint32_t* lark_ptr;


/* ── Heap ─────────────────────────────────────────────────────────────────── */

/* Allocate n_words * 4 bytes on the Lark heap; abort on overflow. */
lark_ptr __heap_alloc(int n_words);

/* Allocate and fill a Lark string [uint32_t len][bytes...]['\0'][pad]. */
lark_ptr lark_alloc_string(const char* text);

/* Return a pointer to the character data of a Lark string (skips length). */
static inline const char* lark_str_data(lark_ptr s) {
    return (const char*)(s + 1);
}


/* ── I/O — platform-specific (implemented in platform_*.c) ───────────────── */

/* print(io, s) — print string s followed by newline; return io unchanged. */
lark_ptr print(lark_ptr io, lark_ptr s);

/* read(io) — read a line from stdin; return heap tuple [tag=0, io, str_ptr]. */
lark_ptr read(lark_ptr io);

/* Called once at startup: initialise platform I/O (stdio, UART, …). */
void lark_platform_init(void);


/* ── Show / conversion ───────────────────────────────────────────────────── */

lark_ptr show(int n);
lark_ptr __show_float(uint32_t bits);
lark_ptr __show_bool(int b);

uint32_t int_to_float(int n);
int      float_to_int(uint32_t bits);
lark_ptr int_to_string(int n);
lark_ptr float_to_string(uint32_t bits);


/* ── String operations ───────────────────────────────────────────────────── */

lark_ptr __str_concat(lark_ptr a, lark_ptr b);
int      string_length(lark_ptr s);


/* ── Float arithmetic (bit-level: args and return are float32 bits) ──────── */

uint32_t __float_add(uint32_t a, uint32_t b);
uint32_t __float_sub(uint32_t a, uint32_t b);
uint32_t __float_mul(uint32_t a, uint32_t b);
uint32_t __float_div(uint32_t a, uint32_t b);


/* ── Float comparisons (return 0 or 1) ───────────────────────────────────── */

int __float_lt(uint32_t a, uint32_t b);
int __float_le(uint32_t a, uint32_t b);
int __float_gt(uint32_t a, uint32_t b);
int __float_ge(uint32_t a, uint32_t b);


/* ── Math built-ins ──────────────────────────────────────────────────────── */

int      int_abs(int n);
uint32_t float_abs(uint32_t bits);
uint32_t float_sqrt(uint32_t bits);
uint32_t float_floor(uint32_t bits);
uint32_t float_ceil(uint32_t bits);


/* ── Runtime error ───────────────────────────────────────────────────────── */

/* Non-exhaustive pattern match: print error and halt (does not return). */
void __lark_match_fail(void) __attribute__((noreturn));
