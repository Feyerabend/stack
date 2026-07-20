/*
 * Lark runtime — C entry point.
 *
 * Links with the Lark-compiled assembly, which provides:
 *   lark_ptr lark_main(lark_ptr io)  — the user's main function
 *   void __global_init__(void)       — optional; initialises top-level lets
 *
 * __global_init__ is declared weak so builds without top-level let variables
 * link cleanly without an explicit definition.
 */

#include "runtime.h"
#ifdef PICO_BUILD
#  include "pico/stdlib.h"
#endif

extern lark_ptr lark_main(lark_ptr io);

void __attribute__((weak)) __global_init__(void) {}

int main(void) {
    lark_platform_init();
    __global_init__();
    lark_main(/*io=*/0);
    /* Keep the device alive so USB CDC stays connected after the program ends.
     * Without this the Pico resets before the terminal reads buffered output.
     * tight_loop_contents() is a Pico SDK no-op that keeps the IRQ scheduler
     * running, so picotool can still reboot the device without BOOTSEL. */
    for (;;) {
#ifdef PICO_BUILD
        tight_loop_contents();
#endif
    }
    return 0;
}
