/*
 * m6502.h  --  MOS 6502 CPU emulator
 * ANSI C99, no external dependencies
 *
 * Usage:
 *   1. Implement read/write callbacks for your memory map.
 *   2. Call m6502_init(), then m6502_reset().
 *   3. Call m6502_step() in a loop; it returns the cycles consumed.
 *   4. Call m6502_nmi() / m6502_irq() to signal interrupts.
 */
#ifndef M6502_H
#define M6502_H

#include <stdint.h>
#include <stddef.h>

typedef uint8_t (*m6502_read_fn) (void *ctx, uint16_t addr);
typedef void    (*m6502_write_fn)(void *ctx, uint16_t addr, uint8_t val);

typedef struct {
    uint16_t pc;
    uint8_t  sp, a, x, y;
    /* flags stored as individual bytes (0 or 1) for speed */
    uint8_t  c, z, i, d, v, n;
    /* cumulative cycle count since last reset */
    uint64_t cycles;
    /* bus interface -- must be set before any step/reset call */
    m6502_read_fn  read;
    m6502_write_fn write;
    void          *ctx;
} M6502;

void    m6502_init  (M6502 *cpu,
                     m6502_read_fn read, m6502_write_fn write, void *ctx);
int     m6502_reset (M6502 *cpu);   /* 7 cycles; reads RESET vector $FFFC */
int     m6502_step  (M6502 *cpu);   /* execute one instruction; return cycles */
int     m6502_nmi   (M6502 *cpu);   /* 7 cycles; reads NMI vector $FFFA */
int     m6502_irq   (M6502 *cpu);   /* 7 cycles; no-op if I flag is set */

uint8_t m6502_getP  (const M6502 *cpu);  /* pack flags into P byte */
void    m6502_setP  (M6502 *cpu, uint8_t p);

/* disassemble one instruction at addr into buf; returns byte length */
int m6502_disasm(m6502_read_fn read, void *ctx,
                 uint16_t addr, char *buf, size_t sz);

#endif /* M6502_H */
