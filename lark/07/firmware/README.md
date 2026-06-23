# Prebuilt firmware — Lark samples on the Pico 2 / 2W

Each `.uf2` here is a sample from [`../samples/`](../samples/) compiled all the way
down to a **Raspberry Pi Pico 2 / 2W (RP2350, RISC-V)** image. They let you run the
programs on real hardware **without installing any toolchain** — just flash and watch.

They are built by the `Lark → RV32 → .uf2` pipeline (`make pico FILE=…` in `../`)
and have been verified on a Pico 2/2W: every program's output matches the Lark
interpreter exactly.

## Flash one

Hold **BOOTSEL**, plug the board in (or tap RESET). It mounts as a USB drive
named `RP2350`. Then either:

- **Drag-and-drop:** copy the `.uf2` onto the `RP2350` drive, or
- **picotool:** `picotool load -x 03_primes.uf2`

The board reboots and runs the program.

## See the output

The program prints over **USB-CDC serial** and waits for you to connect before its
first line, so open a terminal after it boots:

```sh
ls /dev/tty.usbmodem*              # find the port (macOS/Linux)
screen /dev/tty.usbmodem* 115200   # Ctrl-A K to quit
```

(Baud rate is ignored over USB-CDC; any value works.)

## What each one does

| Firmware | Sample | Expected output |
|---|---|---|
| `01_mergesort.uf2` | Merge sort | `1 2 3 4 5 6 7 8 9` |
| `02_bst.uf2` | Binary search tree | in-order `1 3 4 5 7 9`, membership `true`/`false`, `height: 3` |
| `03_primes.uf2` | Sieve of primes ≤ 50 | `2 3 5 … 47` then `15 primes up to 50` |
| `04_queens.uf2` | N-queens count | `N=6: 4`, `N=8: 92` |
| `05_expr.uf2` | Expression evaluator | e.g. `((3 + 4) * (10 - 3)) = 49` |
| `06_rle.uf2` | Run-length encoding | `3x1 1x2 2x3 4x4` (round-trips the list) |
| `07_hanoi.uf2` | Towers of Hanoi (4 disks) | the move list, then `15 moves total` |
| `08_life.uf2` | Conway's Game of Life | a glider over 5 generations on a 10×6 grid |
| `09_parser.uf2` | Recursive-descent calculator | parses & evaluates, e.g. `1 + 2 * 3 => (1+(2*3)) = 7` |

To rebuild any of these from source: from `../`, run `make pico FILE=samples/03_primes.lark`
(needs the Pico SDK + RISC-V toolchain under `~/.pico-sdk`).
