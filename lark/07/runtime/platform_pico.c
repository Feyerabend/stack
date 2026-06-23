/*
 * Lark runtime — Raspberry Pi Pico / RP2350 platform layer.
 *
 * Provides I/O via Pico SDK stdio (USB CDC by default; configure in
 * CMakeLists.txt via pico_enable_stdio_usb / pico_enable_stdio_uart).
 *
 * To build: include this file instead of platform_posix.c in CMakeLists.txt.
 */

#include "runtime.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>

void lark_platform_init(void) {
    stdio_init_all();
    /* Wait until the USB CDC host connects so the first print() is visible.
     * Remove this if you are using UART or do not need to wait. */
    while (!stdio_usb_connected()) {
        tight_loop_contents();
    }
}

lark_ptr print(lark_ptr io, lark_ptr s) {
    puts(lark_str_data(s));
    stdio_flush();
    return io;
}

lark_ptr read(lark_ptr io) {
    char buf[256];
    if (fgets(buf, sizeof(buf), stdin) == NULL) {
        buf[0] = '\0';
    } else {
        /* Strip trailing newline. */
        size_t n = strlen(buf);
        if (n > 0 && buf[n - 1] == '\n') buf[n - 1] = '\0';
    }
    lark_ptr str  = lark_alloc_string(buf);
    /* Return a 3-word tuple: [tag=0, io, str_ptr]. */
    lark_ptr tup  = __heap_alloc(3);
    tup[0] = 0;
    tup[1] = (uint32_t)(uintptr_t)io;
    tup[2] = (uint32_t)(uintptr_t)str;
    return tup;
}
