/*
 * Lark runtime — POSIX platform layer (Linux, macOS, etc.)
 *
 * Use this file when building for testing on a host machine.
 * Do NOT include this in the Pico SDK build.
 */

#include "runtime.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

void lark_platform_init(void) {
    /* Nothing to do on POSIX. */
}

lark_ptr print(lark_ptr io, lark_ptr s) {
    puts(lark_str_data(s));
    return io;
}

lark_ptr read(lark_ptr io) {
    char buf[1024];
    if (fgets(buf, sizeof(buf), stdin) == NULL) {
        buf[0] = '\0';
    } else {
        size_t n = strlen(buf);
        if (n > 0 && buf[n - 1] == '\n') buf[n - 1] = '\0';
    }
    lark_ptr str  = lark_alloc_string(buf);
    lark_ptr tup  = __heap_alloc(3);
    tup[0] = 0;
    tup[1] = (uint32_t)(uintptr_t)io;
    tup[2] = (uint32_t)(uintptr_t)str;
    return tup;
}
