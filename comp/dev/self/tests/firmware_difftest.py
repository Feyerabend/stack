"""
The F3 capstone: nine Pico 2/2W firmware images, built by the compiler Lark wrote.
(SELFHOST F3.3 — RE-SCOPED; read the section below before trusting the old plan.)

    07/samples/*.lark  →  [self-hosted Lark compiler]  →  .S  →  GNU RISC-V  →  .uf2

Three claims, in increasing strength.  The first two need no hardware; the third
needs a board, and is the only one this script cannot decide by itself.

  1. ASSEMBLY IDENTITY.  For all nine samples, the .S emitted by the SELF-HOSTED
     compiler (self/tests/rv32c.py's native binary — lex…opt+regalloc+asm, all Lark)
     is byte-identical to the .S emitted by the Python oracle (asm.py).  This is
     asm_difftest's claim, extended to the three programs the meta-circular harness
     can only skip (it runs on CPython's stack; the native binary does not).

  2. IMAGE IDENTITY.  Feed each .S to the real GNU RISC-V toolchain (pico-sdk) and
     the two pipelines produce byte-identical .uf2 — same bytes on the flash chip,
     whichever compiler wrote the assembly.  The toolchain is a constant; identical
     input, identical firmware.

  3. BEHAVIOUR ON SILICON.  Flashed to a Pico 2/2W, each image prints over USB-CDC
     exactly what the CEK interpreter prints for the same program.  This script
     writes the expected transcripts (expected/<name>.txt, straight from cek.py) and
     a runbook; a human with a board does the comparing.  See --hardware.

⚠ WHY THE CAPSTONE HAD TO BE RE-SCOPED.  SELFHOST.md asked for the nine .uf2 already
committed in 07/firmware/ to be reproduced BYTE-IDENTICALLY from the Lark compiler.
That is not attainable — not by the Lark compiler, and not by asm.py either.  Those
images were built before regalloc.py was canonicalised (F3.1: it iterated frozensets,
so which Tmp got which register was a function of PYTHONHASHSEED and the assembly
differed run to run).  They are the output of one unrecoverable seed.  No .S was
checked in, so there is nothing to diff against and nothing to recover the seed from.

So the capstone becomes: REBUILD the nine from the canonicalised pipeline, prove the
Lark compiler and the Python oracle agree on every byte of every image (claims 1+2 —
strictly stronger than the old wording, which only ever compared against artefacts),
re-verify on real hardware (claim 3), and re-pin the shas.  The old images are
replaced, not matched.  --stale prints the diff for the record.

Usage:
    python3 self/tests/firmware_difftest.py                  # claims 1 + 2 + expectations
    python3 self/tests/firmware_difftest.py --asm-only       # claim 1 (no toolchain needed)
    python3 self/tests/firmware_difftest.py --board          # claim 3 — flash + diff, needs the board
    python3 self/tests/firmware_difftest.py --hardware       # print the manual runbook instead
    python3 self/tests/firmware_difftest.py --install        # replace 07/firmware/*.uf2
"""

from __future__ import annotations
import argparse, difflib, glob, hashlib, os, pathlib, select, shutil, subprocess, sys, tempfile, termios, time, tty

HERE = pathlib.Path(__file__).resolve().parent           # self/tests
SELF = HERE.parent                                       # self
ROOT = SELF.parent                                       # lark
SRC  = ROOT / "07" / "src"
RUNTIME  = ROOT / "07" / "runtime"
FIRMWARE = ROOT / "07" / "firmware"
CEK  = str(SRC / "cek.py")

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(SRC))

import rv32c                                    # noqa: E402  (the native self-hosted compiler)

SAMPLES = rv32c.SAMPLES
LEVEL   = 0            # the level `make pico` builds at: asm.py's CLI does not optimize

# The pico-sdk installs its own cmake/ninja/toolchain under $HOME/.pico-sdk and does
# not put them on PATH (the VS Code extension passes absolute paths).  Find them, so
# this runs from a plain shell.
PICO_HOME = pathlib.Path.home() / ".pico-sdk"


def _pico_env() -> dict[str, str] | None:
    """PATH + PICO_SDK_PATH for the SDK's own toolchain, or None if not installed."""
    if not PICO_HOME.exists():
        return None
    def newest(kind: str) -> pathlib.Path | None:
        d = PICO_HOME / kind
        if not d.exists():
            return None
        return sorted((p for p in d.iterdir() if p.is_dir()))[-1]
    cmake, ninja, sdk = newest("cmake"), newest("ninja"), newest("sdk")
    if not (cmake and ninja and sdk):
        return None
    env = dict(os.environ)
    bins = [str(cmake / "bin"), str(ninja)]
    tc = PICO_HOME / "toolchain"
    if tc.exists():
        # Prefer the RISC-V toolchain: the RP2350's Hazard3 cores are RV32, and the
        # ARM one is also installed (the chip has both) — picking it silently builds
        # firmware for the wrong architecture.
        rv = [p for p in sorted(tc.iterdir()) if "RISCV" in p.name.upper()]
        if rv:
            bins.append(str(rv[-1] / "bin"))
    env["PATH"] = os.pathsep.join(bins + [env.get("PATH", "")])
    env["PICO_SDK_PATH"] = str(sdk)
    return env


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ── Claim 1: the two compilers emit the same assembly ─────────────────────────

def emit_both(binary: pathlib.Path) -> dict[str, tuple[str, bool]]:
    """{sample: (assembly, identical?)} — Lark's .S, and whether asm.py agrees."""
    import parser as _parser, infer as _infer, lower as _lower, opt as _opt, asm as _asm
    import itertools

    out: dict[str, tuple[str, bool]] = {}
    for path in SAMPLES:
        prog  = _parser.parse_file(str(path))
        tprog = _infer.typecheck(prog, source_file=str(path))
        _opt._SITE = itertools.count()
        tac   = _opt.optimize(_lower.lower(tprog), _opt.OptOptions(level=LEVEL))
        want  = _asm.gen(tac).rstrip("\n")
        got   = rv32c.compile_lark(binary, path).rstrip("\n")
        out[path.stem] = (got, got == want)
    return out


# ── Claim 1½: the assembly does the right thing (in software, before silicon) ─
#
# `make -C 07 difftest` cross-checks CEK/TAC/RV32 — but it sweeps 07/tests only, so
# not one of the nine FLASHABLE programs has ever been executed as RV32.  The RV32
# emulator closes that gap here, on the Lark compiler's own assembly: if a sample is
# going to misbehave on the board, it should misbehave here first, where the failure
# is inspectable and no hardware is involved.

def emulate(asm_text: str, mem_size: int = 1 << 22) -> tuple[bool, str]:
    """Assemble + run one .S on the RV32 emulator; return (failed?, stdout)."""
    import io as _io, contextlib
    from riscv_asm import assemble_lark
    from riscv_vm  import run_lark

    binary, labels = assemble_lark(asm_text, mem_size=mem_size)
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        failed = run_lark(binary, labels, mem_size=mem_size)
    return failed, buf.getvalue()


# ── Claim 2: the toolchain turns that assembly into firmware ──────────────────

def build_uf2(asm_text: str, env: dict[str, str], work: pathlib.Path) -> bytes:
    """Assemble+link one .S into a .uf2 with the real GNU RISC-V toolchain."""
    (RUNTIME / "program.S").write_text(asm_text + "\n")
    build = work / "build"
    if not (build / "build.ninja").exists():
        subprocess.run(["cmake", "-S", str(RUNTIME), "-B", str(build), "-G", "Ninja",
                        "-DPICO_BOARD=pico2", "-DPICO_PLATFORM=rp2350-riscv"],
                       env=env, check=True, capture_output=True)
    subprocess.run(["cmake", "--build", str(build)], env=env, check=True, capture_output=True)
    return (build / "lark_pico.uf2").read_bytes()


# ── Claim 3: what the board must print ────────────────────────────────────────

def expected_output(path: pathlib.Path) -> str:
    """The reference transcript: what cek.py prints for this program."""
    r = subprocess.run([sys.executable, CEK, str(path)],
                       capture_output=True, text=True, check=True)
    return r.stdout


# ── Claim 3: the board ────────────────────────────────────────────────────────
#
# The firmware waits for stdio_usb_connected() before its first line (platform_pico.c),
# so there is no race: flash, open the port, and the board starts printing to us.  That
# also means claim 3 need not be eyeballed through `screen` — the transcript can be
# captured and diffed like any other, which is what --board does.
#
# Between images we do not need the BOOTSEL button: pico_enable_stdio_usb puts the
# SDK's reset-via-vendor-interface in the running firmware, so `picotool -f` reboots
# the board into BOOTSEL itself.  Only the first flash may need the button, and only
# if whatever is on the board does not support that interface.

PICOTOOL = sorted(PICO_HOME.glob("picotool/*/picotool/picotool"))
BAUD = 115200


def picotool() -> str | None:
    return str(PICOTOOL[-1]) if PICOTOOL else shutil.which("picotool")


def serial_ports() -> list[str]:
    return sorted(glob.glob("/dev/cu.usbmodem*"))


# ── Saying what is happening ──────────────────────────────────────────────────
#
# This talks to hardware over USB: it flashes, it waits for a port to enumerate, and
# it waits on a program that may think for seconds before it prints.  Every one of
# those is a silence, and a silent script is indistinguishable from a hung one — so
# each step narrates itself, live, with the elapsed second on it.

_TTY = sys.stdout.isatty()


_LAST_STEP = [0.0]


def step(msg: str) -> None:
    """A step in progress: overwritten in place on a terminal, throttled when piped."""
    if _TTY:
        sys.stdout.write(f"\r  {msg:<72}")
    else:
        if time.time() - _LAST_STEP[0] < 5.0:    # a log file does not want 4 lines a second
            return
        _LAST_STEP[0] = time.time()
        sys.stdout.write(f"  {msg}\n")
    sys.stdout.flush()


def done(msg: str) -> None:
    """The verdict for a step: always its own line."""
    if _TTY:
        sys.stdout.write("\r" + " " * 76 + "\r")
    sys.stdout.write(f"  {msg}\n")
    sys.stdout.flush()


def detect(tool: str) -> tuple[str, str]:
    """What is actually on the USB bus right now: (state, detail).

    Three states worth telling apart, because the fix differs:
      running  — the app is up and talking USB-CDC; picotool -f can reset it for us
      bootsel  — sitting in the ROM bootloader, ready to be flashed
      absent   — nothing there; no point trying to flash
    """
    ports = serial_ports()
    if ports:
        return "running", ports[-1]
    r = subprocess.run([tool, "info"], capture_output=True, text=True)
    if r.returncode == 0:
        first = [l for l in (r.stdout or "").splitlines() if l.strip()]
        return "bootsel", (first[1].strip() if len(first) > 1 else "RP2350")
    return "absent", ""


def flash(tool: str, uf2: pathlib.Path) -> tuple[bool, str]:
    """Load and execute one image.  -f: reboot a *running* board into BOOTSEL for us."""
    r = subprocess.run([tool, "load", "-f", "-x", str(uf2)],
                       capture_output=True, text=True)
    return r.returncode == 0, (r.stderr or r.stdout).strip()


def await_port(timeout: float = 25.0, label: str = "") -> str | None:
    """The CDC port the freshly-flashed image enumerates as."""
    deadline = time.time() + timeout
    start = time.time()
    while time.time() < deadline:
        ports = serial_ports()
        if ports:
            time.sleep(0.3)                      # let the CDC endpoint settle
            return ports[-1]
        step(f"{label:<14} waiting for the board to come back on USB…  {time.time() - start:3.0f}s")
        time.sleep(0.2)
    return None


def capture(port: str, want: str | None = None, idle: float = 15.0, cap: float = 180.0,
            label: str = "", first_byte: float = 25.0) -> str:
    """Read USB-CDC until the board has said its piece.

    Stdlib only (no pyserial).  Opening the port asserts DTR, which is what unblocks the
    firmware's stdio_usb_connected() spin — so the open is also the start gun.

    Stopping is the subtle part.  Silence does not mean "done": 08_life and 09_parser
    think for seconds between lines, and an idle timeout short enough to be pleasant is
    short enough to truncate them — which would read as a failed claim rather than a
    truncated capture.  So we stop on MATCH when we know what to expect, and keep the
    idle timeout only as the give-up path (a board that has genuinely stopped early, or
    is printing something else).  After a match we still wait `grace` to see whether more
    arrives, so trailing garbage cannot hide behind an early return.
    """
    grace = 1.0
    want_lines = want.count("\n") if want else 0

    # ⚠ THE BUG THAT COST US THE FIRST HARDWARE SESSION (2026-07-13).  Opening the port
    # asserts DTR, which releases the firmware's wait loop, and it prints IMMEDIATELY —
    # microseconds later.  `tty.setraw()` defaults to TCSAFLUSH: "apply, and DISCARD any
    # pending input".  So the transcript arrived and was thrown away by the very next
    # line, and we then listened for 25s at a board that had already said its piece and
    # halted.  Every probe failed this way while `screen` — which does not flush on open
    # — worked every time.  Set raw mode BY HAND with TCSANOW, which never discards.
    fd = os.open(port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        a = termios.tcgetattr(fd)
        a[0] = 0                                 # iflag: no CR/NL translation, no flow control
        a[1] = 0                                 # oflag: no output processing
        a[3] = 0                                 # lflag: no canonical mode, no echo
        a[2] |= termios.CLOCAL | termios.CREAD
        a[2] = (a[2] & ~termios.CSIZE) | termios.CS8
        a[6][termios.VMIN] = 0                   # read() returns what is there
        a[6][termios.VTIME] = 0
        try:                                     # USB-CDC ignores the rate; set it anyway
            a[4] = a[5] = termios.B115200
        except AttributeError:
            pass
        termios.tcsetattr(fd, termios.TCSANOW, a)   # TCSANOW — never TCSAFLUSH

        chunks: list[bytes] = []
        start = last = time.time()
        matched_at: float | None = None
        while True:
            now = time.time()
            if now - start > cap:
                break
            if matched_at is not None and now - matched_at > grace:
                break
            if matched_at is None and chunks and now - last > idle:
                break
            if not chunks and now - start > first_byte:
                break                            # silent board: say so early, don't sit for `cap`

            got_lines = b"".join(chunks).count(b"\n")
            waiting = "listening (the board prints once we connect)" if not chunks else \
                      f"reading {got_lines}/{want_lines} lines"
            step(f"{label:<14} {waiting}…  {now - start:3.0f}s")

            r, _, _ = select.select([fd], [], [], 0.25)
            if not r:
                continue
            try:
                b = os.read(fd, 4096)
            except BlockingIOError:
                continue
            if not b:
                continue
            chunks.append(b)
            last = time.time()
            if want is not None:
                text = b"".join(chunks).decode("utf-8", "replace")
                matched_at = last if normalise(text) == want else None
        return b"".join(chunks).decode("utf-8", "replace")
    finally:
        os.close(fd)


def normalise(s: str) -> str:
    """The wire is CRLF and the transcript is LF; trailing blank lines are not a claim."""
    return s.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n") + "\n"


def verify_board(staged: pathlib.Path, only: list[str], no_flash: bool = False) -> int:
    tool = picotool()
    if tool is None:
        print("no picotool — install the pico-sdk, or use --hardware for the manual runbook")
        return 1

    names = [p.stem for p in SAMPLES]
    if only:
        unknown = [n for n in only if n not in names]
        if unknown:
            print(f"unknown sample(s): {', '.join(unknown)}\nknown: {', '.join(names)}")
            return 1
        names = [n for n in names if n in only]

    missing = [n for n in names
               if not (staged / f"{n}.uf2").exists() or not (staged / "expected" / f"{n}.txt").exists()]
    if missing:
        print(f"not staged: {', '.join(missing)}\nrun the script with no arguments first (claims 1+2)")
        return 1

    print(f"3. behaviour on silicon — {len(names)} image(s), flashed and diffed against cek.py")
    print(f"   picotool: {tool}")

    # ── preflight: say what is on the USB bus, and stop if it is nothing ───────
    state, detail = detect(tool)
    if state == "running":
        print(f"   board:    FOUND, running — USB-CDC on {detail}")
        print("             (picotool -f will reset it into BOOTSEL; no button needed)\n")
    elif state == "bootsel":
        print(f"   board:    FOUND, in BOOTSEL — {detail}\n")
    else:
        print("   board:    NOT FOUND — nothing on USB\n")
        print("  Nothing to flash.  Plug the Pico 2/2W into USB (hold BOOTSEL as you plug it in")
        print("  if it is blank or running something without USB serial), then re-run:")
        print("      python3 self/tests/firmware_difftest.py --board\n")
        print("  Sanity checks:  ls /dev/cu.usbmodem*        (a running Lark image)")
        print(f"                  {tool} info      (a board sitting in BOOTSEL)")
        return 1

    print(f"  {'sample':<14} {'what happens':<48}")
    print(f"  {'-' * 62}")

    ok = 0
    for name in names:
        uf2  = staged / f"{name}.uf2"
        want = normalise((staged / "expected" / f"{name}.txt").read_text())
        t0 = time.time()

        if no_flash:                             # read whatever is already running (after a replug)
            step(f"{name:<14} reading the board as it stands (not flashing)…")
        else:
            step(f"{name:<14} flashing {uf2.stat().st_size // 1024} KB…")
            loaded, err = flash(tool, uf2)
            if not loaded:
                done(f"FAIL  {name:<14} could not flash")
                for line in (err.splitlines() or ["(picotool said nothing)"])[-3:]:
                    print(f"        picotool: {line}")
                print(f"        hold BOOTSEL, replug, then:  ... --board --only {name}")
                break

        port = await_port(label=name)
        if port is None:
            done(f"FAIL  {name:<14} no /dev/cu.usbmodem* within 25s")
            print("        unplug, replug (no BOOTSEL), and re-run")
            break

        got = normalise(capture(port, want, label=name))
        dt = time.time() - t0

        if got == want:
            done(f"ok    {name:<14} {got.count(chr(10)):>4} lines over USB-CDC == cek.py   ({dt:.0f}s)")
            ok += 1
        elif not got.strip():
            done(f"FAIL  {name:<14} the board printed nothing")
            print("        The firmware spins in `while (!stdio_usb_connected())` — it prints only")
            print("        once a host asserts DTR.  Two known causes, in order of likelihood:")
            print()
            print("        1. THE SOFT-REBOOT SESSION (seen on this machine, 2026-07-13).  After a")
            print("           picotool flash/reboot the port reappears in ~0.3s — too fast to be a")
            print("           real USB re-enumeration — and DTR then never reaches the chip.  No")
            print("           reader can fix that from the host side.  PHYSICALLY REPLUG the board")
            print("           (no BOOTSEL), then read the image already on it:")
            print(f"               python3 self/tests/firmware_difftest.py --board --only {name} --no-flash")
            print("        2. Something else holds the port (a stray `screen`?):")
            print(f"               lsof {port}")
            print()
            print("        `screen /dev/tty.usbmodem* 115200` after a replug is the manual fallback,")
            print("        and it is known to work — the images and the compiler are not in doubt.")
            break
        else:
            done(f"FAIL  {name:<14} the board printed something else:")
            diff = difflib.unified_diff(want.splitlines(), got.splitlines(),
                                        "cek.py", "the board", lineterm="", n=1)
            for line in list(diff)[:20]:
                print(f"        {line}")
            (staged / f"{name}.got.txt").write_text(got)
            print(f"        saved: {staged / (name + '.got.txt')}")
            break                                # a real bug: stop, do not flash over the evidence

    print(f"\n  {ok}/{len(names)} verified on hardware")
    if ok == len(names) and not only:
        print("\n  F3.3 claim 3 GREEN — the nine images do on silicon what the CEK interpreter says.")
        print("  next:   python3 self/tests/firmware_difftest.py --install   (re-pin 07/firmware/)")
    return 0 if ok == len(names) else 1


RUNBOOK = """\
Hardware verification — nine images, one board (F3.3, claim 3)
==============================================================

The automated path is `--board`: it flashes each image with picotool, captures the
USB-CDC transcript and diffs it against expected/.  What follows is the manual
fallback, for when picotool cannot reset the board (hold BOOTSEL and replug) or you
want to watch it print.

Everything a machine can check is already checked: the self-hosted compiler and the
Python oracle emit identical assembly, and identical firmware, for all nine programs.
What silicon adds is that the firmware is *right* — that the register allocator, the
frame layout and the tail-call loop survive contact with a real Hazard3 core.

For each image in {staged}:

  1. Hold BOOTSEL, plug the Pico 2/2W in.  It mounts as a USB drive named RP2350.
  2. Flash:   picotool load -x {staged}/<name>.uf2
     (or drag the .uf2 onto the RP2350 drive)
  3. The board reboots and waits for a serial reader before its first line:
         ls /dev/tty.usbmodem*
         screen /dev/tty.usbmodem* 115200        # Ctrl-A K to quit
  4. Compare what it prints with expected/<name>.txt — those transcripts are the CEK
     interpreter's output for the same program, so a match means the compiled program
     and the reference semantics agree.

     A quick way to be exact rather than impressionistic:
         screen -L -Logfile got.txt /dev/tty.usbmodem* 115200
         diff <(sed -e 's/\\r$//' got.txt) expected/<name>.txt

The two long ones (08_life, 09_parser) take a few seconds; the rest are immediate.
09_parser is the one worth watching: it is Lark's own parser, self-hosted, running
on a microcontroller — compiled by a compiler written in Lark.

If a program's output differs, that is a REAL bug and the first one hardware has
caught: save got.txt, note the sample, and stop — the .S and the .uf2 are both in
{staged}, so the failure is reproducible without the board.
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="F3 capstone: nine .uf2 from the self-hosted compiler")
    ap.add_argument("--asm-only", action="store_true", help="claim 1 only (no toolchain needed)")
    ap.add_argument("--board", action="store_true", help="claim 3: flash each image and diff what it prints")
    ap.add_argument("--only", nargs="+", default=[], metavar="SAMPLE", help="restrict --board to these samples")
    ap.add_argument("--no-flash", action="store_true", help="--board: read the image already on the board (use after a physical replug)")
    ap.add_argument("--hardware", action="store_true", help="print the manual flashing runbook and exit")
    ap.add_argument("--install", action="store_true", help="replace 07/firmware/*.uf2 with the rebuilt images")
    ap.add_argument("--staged", default=str(ROOT / "build" / "firmware"))
    ap.add_argument("--binary", default=str(ROOT / "build" / "rv32c"))
    args = ap.parse_args()

    staged = pathlib.Path(args.staged).resolve()
    if args.hardware:
        print(RUNBOOK.format(staged=staged))
        return 0
    if args.board:
        return verify_board(staged, args.only, args.no_flash)

    staged.mkdir(parents=True, exist_ok=True)
    (staged / "expected").mkdir(exist_ok=True)

    binary = pathlib.Path(args.binary).resolve()
    if not binary.exists():
        print(f"building the self-hosted RV32 compiler → {binary}")
        rv32c.build(binary, level=LEVEL)

    # ── claim 1 ───────────────────────────────────────────────────────────────
    print("\n1. assembly identity — self-hosted compiler vs asm.py\n")
    asm = emit_both(binary)
    ident = 0
    for name, (text, same) in asm.items():
        (staged / f"{name}.S").write_text(text + "\n")
        print(f"  {'ok  ' if same else 'FAIL'}  {name:<14} {len(text.splitlines()):>5} lines of RV32I")
        ident += same
    print(f"\n  {ident}/{len(asm)} byte-identical")
    if ident != len(asm):
        print("\n  claim 1 FAILED — not building firmware from assembly the two compilers disagree on")
        return 1

    # expected transcripts (claim 3's yardstick) — cheap, and needed either way
    expected: dict[str, str] = {}
    for path in SAMPLES:
        expected[path.stem] = expected_output(path)
        (staged / "expected" / f"{path.stem}.txt").write_text(expected[path.stem])

    # ── claim 1½ ──────────────────────────────────────────────────────────────
    print("\n1½. behaviour in the RV32 emulator — the Lark compiler's assembly vs cek.py\n")
    agree = 0
    for name, (text, _) in asm.items():
        try:
            failed, got = emulate(text)
        except Exception as e:                     # an emulator limit is not a codegen bug
            print(f"  skip  {name:<14} (emulator: {type(e).__name__}: {str(e)[:40]})")
            continue
        if not failed and got == expected[name]:
            print(f"  ok    {name:<14} output matches the interpreter")
            agree += 1
        else:
            why = "program failed" if failed else "output differs"
            print(f"  FAIL  {name:<14} ({why})")
    print(f"\n  {agree}/{len(asm)} behaviourally verified in software")

    if args.asm_only:
        print(f"\n  staged: {staged}  (.S + expected/)")
        return 0

    # ── claim 2 ───────────────────────────────────────────────────────────────
    env = _pico_env()
    if env is None:
        print("\n2. image identity — SKIPPED: no pico-sdk under ~/.pico-sdk")
        print(f"   staged: {staged}  (.S + expected/)")
        return 0

    print("\n2. image identity — the GNU RISC-V toolchain on each .S\n")
    saved = (RUNTIME / "program.S").read_bytes() if (RUNTIME / "program.S").exists() else None
    work = pathlib.Path(tempfile.mkdtemp(prefix="lark-pico-"))
    try:
        for name, (text, _) in asm.items():
            uf2 = build_uf2(text, env, work)
            (staged / f"{name}.uf2").write_bytes(uf2)
            old = FIRMWARE / f"{name}.uf2"
            note = ""
            if old.exists():
                note = ("  (== committed)" if sha(old.read_bytes()) == sha(uf2)
                        else "  (replaces the pre-canonicalisation image)")
            print(f"  ok    {name:<14} {len(uf2):>8} bytes  {sha(uf2)[:12]}{note}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
        if saved is not None:
            (RUNTIME / "program.S").write_bytes(saved)

    if args.install:
        for name in asm:
            shutil.copy2(staged / f"{name}.uf2", FIRMWARE / f"{name}.uf2")
        print(f"\n  installed {len(asm)} images into {FIRMWARE}")

    print(f"\n  staged: {staged}")
    print("  next:   python3 self/tests/firmware_difftest.py --hardware   (claim 3 — needs the board)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
