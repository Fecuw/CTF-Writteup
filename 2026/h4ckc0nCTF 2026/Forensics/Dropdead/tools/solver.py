#!/usr/bin/env python3
"""
Drop Dead  (100 pts, author: paramveer504)  -- solver

Chain:
  dead_drop.zip -> dead_drop.jpg
    -> steghide (passphrase "36")        -> laptop.txt   (Base36 blob)
    -> Base36 big-integer decode         -> XZ stream
    -> xz decompress                     -> 32 MiB ext4 image
    -> ext4 extract (+ deleted inodes)   -> a fake laptop filesystem
    -> 5 numbered URL fragments, each hidden in a different esolang
    -> concatenate, SHA-256 must equal the digest in /home/agent/README

Everything except the steghide step and the ext4 extraction is pure Python.
Those two shell out; see --help for how to point the solver at pre-extracted data.

Status: SOLVED.  Fragments 1, 3, 4 and 5 come out of the filesystem with two
        candidates each for 1/3/5 (one real, one decoy); fragment 2 is the
        Supabase hostname suffix ".supabase.co", which the SHA-256 confirms.
        tune.mid presumably carries fragment 2 as well, but its encoding was
        never cracked and it is not needed -- see Writeup.md.

Answer:
  https://hljuqfqgsdycotnhdndt.supabase.co/storage/v1/object/public/image/
  Screenshot%20from%202026-11-09%2017-32-54.png      (joined, no line break)
"""

import argparse
import hashlib
import itertools
import lzma
import os
import re
import string
import struct
import subprocess
import sys

B36 = string.digits + string.ascii_uppercase
TARGET_SHA256 = "9f2bce0edb56e82e2e5ecf5e9585f9fb19495c6767f1dd1920742986119ca0f8"


# --------------------------------------------------------------------------
# stage 1 -- steghide
# --------------------------------------------------------------------------
# The hint "I have heard of a foreign six, travelers call it 6^2" gives 6^2 = 36.
# "36" is literally the steghide passphrase; the Base36 reading applies to the
# payload that comes out.
STEG_PASSPHRASE = "36"


def steghide_extract(jpg, out_path, docker_image="stegbox"):
    """Extract the embedded laptop.txt.  Uses a local steghide if present,
    otherwise a throwaway Debian container (steghide is not in Homebrew)."""
    if _have("steghide"):
        cmd = ["steghide", "extract", "-sf", jpg, "-p", STEG_PASSPHRASE,
               "-xf", out_path, "-f"]
        subprocess.run(cmd, check=True)
    else:
        _ensure_docker_image(docker_image, "steghide")
        jpg = os.path.abspath(jpg)
        out_dir = os.path.abspath(os.path.dirname(out_path))
        subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{jpg}:/data/in.jpg:ro",
            "-v", f"{out_dir}:/out",
            docker_image,
            "steghide", "extract", "-sf", "/data/in.jpg",
            "-p", STEG_PASSPHRASE,
            "-xf", "/out/" + os.path.basename(out_path), "-f",
        ], check=True)
    return open(out_path, "rb").read()


def _have(prog):
    return subprocess.run(["which", prog], capture_output=True).returncode == 0


def _ensure_docker_image(tag, *packages):
    have = subprocess.run(["docker", "image", "inspect", tag],
                          capture_output=True).returncode == 0
    if have:
        return
    dockerfile = (
        "FROM debian:stable-slim\n"
        "RUN apt-get update -qq && apt-get install -y -qq "
        "--no-install-recommends " + " ".join(packages) +
        " && rm -rf /var/lib/apt/lists/*\n"
    )
    subprocess.run(["docker", "build", "-q", "-t", tag, "-"],
                   input=dockerfile.encode(), check=True)


# --------------------------------------------------------------------------
# stage 2 -- Base36
# --------------------------------------------------------------------------
def base36_decode(text, chunk=2000):
    """Whole string as one big base-36 integer -> bytes.

    int(s, 36) is quadratic in CPython and the blob is ~213k digits, so do a
    divide-and-conquer recombination instead (and dodge the int/str digit
    limit on Python >= 3.11)."""
    s = text.strip()
    if not set(s) <= set(B36):
        raise ValueError("not a base36 string")
    pad = (-len(s)) % chunk
    s = "0" * pad + s
    chunks = [int(s[i:i + chunk], 36) for i in range(0, len(s), chunk)]
    base = 36 ** chunk

    def conv(cs, b):
        if len(cs) == 1:
            return cs[0], b
        mid = len(cs) // 2
        hi, bh = conv(cs[:mid], b)
        lo, bl = conv(cs[mid:], b)
        return hi * bl + lo, bh * bl

    n, _ = conv(chunks, base)
    return n.to_bytes((n.bit_length() + 7) // 8, "big")


# --------------------------------------------------------------------------
# stage 4 -- ext4
# --------------------------------------------------------------------------
# Two of the payload files were rm'd (see .bash_history) and survive only as
# orphaned inodes 20 (tune.mid) and 26 (bracket.gcode).
DELETED_INODES = {20: "tune.mid", 26: "bracket.gcode"}


def ext4_extract(img, out_dir, docker_image="fsbox"):
    """debugfs reads ext4 without mounting, so this needs no privileges and
    works on macOS."""
    os.makedirs(out_dir, exist_ok=True)
    img = os.path.abspath(img)
    out_dir = os.path.abspath(out_dir)
    if _have("debugfs"):
        run = lambda c: subprocess.run(["debugfs", "-R", c, img],
                                       capture_output=True)
    else:
        _ensure_docker_image(docker_image, "e2fsprogs")
        def run(c):
            return subprocess.run([
                "docker", "run", "--rm",
                "-v", f"{img}:/img:ro", "-v", f"{out_dir}:/out",
                docker_image, "debugfs", "-R", c, "/img",
            ], capture_output=True)
    run(f"rdump / {'/out' if not _have('debugfs') else out_dir}")
    for ino, name in DELETED_INODES.items():
        dest = ("/out/" if not _have("debugfs") else out_dir + "/") + name
        run(f"dump <{ino}> {dest}")
    return out_dir


# --------------------------------------------------------------------------
# esolang interpreters
# --------------------------------------------------------------------------
def brainfuck_linear(prog):
    """The keytab payload uses only + - . : one cell, no loops."""
    cell, out = 0, []
    for c in prog:
        if c == "+":
            cell = (cell + 1) % 256
        elif c == "-":
            cell = (cell - 1) % 256
        elif c == ".":
            out.append(chr(cell))
    return "".join(out)


OOK_PAIRS = {
    ("Ook.", "Ook?"): ">", ("Ook?", "Ook."): "<",
    ("Ook.", "Ook."): "+", ("Ook!", "Ook!"): "-",
    ("Ook!", "Ook."): ".", ("Ook.", "Ook!"): ",",
    ("Ook!", "Ook?"): "[", ("Ook?", "Ook!"): "]",
}


def ook_to_bf(text):
    toks = re.findall(r"Ook[.!?]", text)
    return "".join(OOK_PAIRS[(toks[i], toks[i + 1])]
                   for i in range(0, len(toks) - 1, 2))


def deadfish(prog):
    """i = increment, d = decrement, s = square, o = output.
    Accumulator resets to 0 when it hits -1 or 256."""
    x, out = 0, []
    for c in prog:
        if c == "i":
            x += 1
        elif c == "d":
            x -= 1
        elif c == "s":
            x *= x
        elif c == "o":
            out.append(chr(x))
        if x == -1 or x == 256:
            x = 0
    return "".join(out)


def befunge93(src, max_steps=100000):
    """Only enough of Befunge-93 for the one-line `0"..."​>:#,_@` idiom."""
    grid = [list(line) for line in src.split("\n")]
    w = max(len(r) for r in grid)
    for r in grid:
        r.extend(" " * (w - len(r)))
    x = y = 0
    dx, dy = 1, 0
    stack, out, strmode = [], [], False
    for _ in range(max_steps):
        c = grid[y][x]
        if strmode:
            if c == '"':
                strmode = False
            else:
                stack.append(ord(c))
        elif c == '"':
            strmode = True
        elif c.isdigit():
            stack.append(int(c))
        elif c == ">":
            dx, dy = 1, 0
        elif c == "<":
            dx, dy = -1, 0
        elif c == "^":
            dx, dy = 0, -1
        elif c == "v":
            dx, dy = 0, 1
        elif c == ":":
            stack.append(stack[-1] if stack else 0)
        elif c == "\\":
            if len(stack) > 1:
                stack[-1], stack[-2] = stack[-2], stack[-1]
        elif c == "$":
            stack and stack.pop()
        elif c == ",":
            out.append(chr(stack.pop() if stack else 0))
        elif c == ".":
            out.append(str(stack.pop() if stack else 0))
        elif c == "#":
            x = (x + dx) % w
            y = (y + dy) % len(grid)
        elif c == "_":
            dx, dy = (1, 0) if (stack.pop() if stack else 0) == 0 else (-1, 0)
        elif c == "|":
            dx, dy = (0, 1) if (stack.pop() if stack else 0) == 0 else (0, -1)
        elif c == "@":
            break
        x = (x + dx) % w
        y = (y + dy) % len(grid)
    return "".join(out)


# -- Piet -------------------------------------------------------------------
_LIGHT = [(255, 192, 192), (255, 255, 192), (192, 255, 192),
          (192, 255, 255), (192, 192, 255), (255, 192, 255)]
_NORMAL = [(255, 0, 0), (255, 255, 0), (0, 255, 0),
           (0, 255, 255), (0, 0, 255), (255, 0, 255)]
_DARK = [(192, 0, 0), (192, 192, 0), (0, 192, 0),
         (0, 192, 192), (0, 0, 192), (192, 0, 192)]
PIET_COLORS = {}
for _li, _row in enumerate([_LIGHT, _NORMAL, _DARK]):
    for _hi, _c in enumerate(_row):
        PIET_COLORS[_c] = (_hi, _li)

PIET_CMDS = [["nop", "push", "pop"], ["add", "sub", "mul"],
             ["div", "mod", "not"], ["gt", "ptr", "swi"],
             ["dup", "roll", "inn"], ["inc", "outn", "outc"]]


def piet_linear(pixels):
    """Interpreter for a single-row Piet program containing no white/black
    codels -- which is exactly what the NWB file carries.  Control flow is
    then just 'walk right', so no DP/CC bookkeeping is needed."""
    runs = []
    for c in pixels:
        if runs and runs[-1][0] == c:
            runs[-1][1] += 1
        else:
            runs.append([c, 1])
    stack, out = [], []
    for i in range(len(runs) - 1):
        h1, l1 = PIET_COLORS[runs[i][0]]
        h2, l2 = PIET_COLORS[runs[i + 1][0]]
        cmd = PIET_CMDS[(h2 - h1) % 6][(l2 - l1) % 3]
        size = runs[i][1]
        try:
            if cmd == "push":
                stack.append(size)
            elif cmd == "pop":
                stack.pop()
            elif cmd == "dup":
                stack.append(stack[-1])
            elif cmd == "add":
                b, a = stack.pop(), stack.pop(); stack.append(a + b)
            elif cmd == "sub":
                b, a = stack.pop(), stack.pop(); stack.append(a - b)
            elif cmd == "mul":
                b, a = stack.pop(), stack.pop(); stack.append(a * b)
            elif cmd == "outc":
                out.append(chr(stack.pop() % 0x110000))
            elif cmd == "outn":
                out.append(str(stack.pop()))
        except IndexError:
            pass
    return "".join(out)


# --------------------------------------------------------------------------
# payload carriers
# --------------------------------------------------------------------------
def keytab_payload(path):
    """MIT keytab.  The program is sliced across the key material of the
    entries, and the entries are stored in DESCENDING kvno order -- sort by
    kvno before concatenating or the program is scrambled."""
    d = open(path, "rb").read()
    off, entries = 2, []
    while off + 4 <= len(d):
        (size,) = struct.unpack(">i", d[off:off + 4])
        off += 4
        if size == 0:
            break
        if size < 0:
            off += -size
            continue
        e = d[off:off + size]
        off += size
        q = 0
        (ncomp,) = struct.unpack(">H", e[q:q + 2]); q += 2

        def counted():
            nonlocal q
            (ln,) = struct.unpack(">H", e[q:q + 2]); q += 2
            v = e[q:q + ln]; q += ln
            return v

        counted()                      # realm
        [counted() for _ in range(ncomp)]
        q += 4 + 4                     # name_type, timestamp
        kvno = e[q]; q += 1
        q += 2                         # enctype
        entries.append((kvno, counted()))
    entries.sort(key=lambda kv: kv[0])
    return b"".join(k for _, k in entries).decode("latin1")


def fon_payload(path):
    """Both .fon files hide their program after the "VGA8\\0" marker."""
    d = open(path, "rb").read()
    tail = d.split(b"VGA8\x00", 1)[1]
    return tail.rstrip(b" ").decode("latin1")


def nwb_piet_pixels(path, docker_image="h5box"):
    """/acquisition/calcium_frame/data is (8, 5504, 3) uint8 with an attribute
    'codel_size' = 8 -- a 1x688 codel Piet program."""
    try:
        import h5py                                    # noqa
        import numpy as np
        with h5py.File(path, "r") as f:
            arr = f["/acquisition/calcium_frame/data"][...]
    except ImportError:
        import numpy as np
        _ensure_docker_image(docker_image, "hdf5-tools")
        path = os.path.abspath(path)
        out = os.path.dirname(path)
        subprocess.run([
            "docker", "run", "--rm", "-v", f"{path}:/f.nwb:ro",
            "-v", f"{out}:/out", docker_image,
            "h5dump", "-d", "/acquisition/calcium_frame/data",
            "-b", "LE", "-o", "/out/piet_raw.bin", "/f.nwb",
        ], capture_output=True)
        arr = np.fromfile(os.path.join(out, "piet_raw.bin"),
                          dtype="u1").reshape(8, 5504, 3)
    codels = arr[::8, ::8, :][0]
    return [tuple(int(v) for v in px) for px in codels]


def gcode_e_fractions(path):
    """Data rides in the third decimal of the extruder (E) value."""
    txt = open(path).read()
    e = [m.group(1) for m in
         re.finditer(r"G1 X[\d.]+ Y[\d.]+ E([\d.]+)", txt)]
    return [int(round((float(v) % 1) * 1000)) for v in e]


def arnoldc(src):
    """Only the one statement this challenge uses."""
    out = []
    for line in src.split("\n"):
        m = re.match(r'\s*TALK TO THE HUMAN\s+"(.*)"\s*$', line)
        if m:
            out.append(m.group(1))
    return "".join(out)


# --------------------------------------------------------------------------
# fragment recovery
# --------------------------------------------------------------------------
def recover_fragments(fs):
    """fs = directory holding the extracted filesystem (plus the two
    recovered deleted files at its root)."""
    frags = {}

    # 1a -- /etc/krb5.keytab : Brainfuck restricted to + - .
    frags["1a"] = brainfuck_linear(keytab_payload(f"{fs}/etc/krb5.keytab"))

    # 1b -- /var/backups/backup.keytab : Ook!
    frags["1b"] = brainfuck_linear(
        ook_to_bf(keytab_payload(f"{fs}/var/backups/backup.keytab")))

    # 3a -- vga8.fon : Befunge-93
    frags["3a"] = befunge93(fon_payload(f"{fs}/usr/share/fonts/misc/vga8.fon"))

    # 3b -- term.fon : Deadfish
    frags["3b"] = deadfish(fon_payload(f"{fs}/usr/share/fonts/misc/term.fon"))

    # 4  -- session_0427.nwb : Piet
    frags["4"] = piet_linear(
        nwb_piet_pixels(f"{fs}/home/agent/research/session_0427.nwb"))

    # 5a -- old_bracket.gcode : ArnoldC in the E fractions, read forward
    src = "".join(chr(x) for x in
                  gcode_e_fractions(f"{fs}/home/agent/prints/old_bracket.gcode"))
    frags["5a"] = arnoldc(src)

    # 5b -- deleted bracket.gcode : (0x60, 0x2e, data) triplets, reversed
    fr = gcode_e_fractions(f"{fs}/bracket.gcode")
    frags["5b"] = "".join(chr(x) for x in fr[2::3])[::-1]

    # 2  -- the Supabase hostname suffix.  tune.mid (deleted, inode 20) is the
    #       only carrier left unaccounted for and almost certainly holds this,
    #       but its encoding was never cracked; the value is forced by the
    #       Supabase URL format and confirmed by the SHA-256 check.
    frags["2"] = "2:.supabase.co"

    return frags


def midi_structure(path):
    """What is known about tune.mid.  Not a decoding -- just the invariants,
    kept here because they are the entry point for whoever finishes this.

      * 209 note-on events, channel 0, every note exactly 30 ticks long
      * note[i] % 4 == i % 4 for all i, note in [48, 83]
            -> 9 free values per note (3 pitch classes x 3 octaves);
               each position draws from one of four augmented triads
      * velocity[i] % 2 == (i + 1) % 2, velocity in [50, 119]
            -> 35 free values per event
      * inter-onset gaps in [150, 268], no periodic structure found

    Ruled out: raw ASCII, Base36 big-int, Deadfish (all 4^9 digit maps),
    Brainfuck and Ook! (no digit pair balances brackets at all), affine maps
    of note/velocity/gap, and period-2..30 marker layouts.
    """
    d = open(path, "rb").read()
    p = 14 + 8
    def vlq():
        nonlocal p
        v = 0
        while True:
            b = d[p]; p += 1
            v = (v << 7) | (b & 0x7F)
            if not b & 0x80:
                return v
    ons, status = [], 0
    while p < len(d) - 3:
        dt = vlq()
        b = d[p]
        if b & 0x80:
            status = b; p += 1
        if status == 0xFF:
            p += 1; ln = vlq(); p += ln; continue
        ev = status & 0xF0
        if ev in (0x80, 0x90):
            n, v = d[p], d[p + 1]; p += 2
            if ev == 0x90 and v > 0:
                ons.append((dt, n, v))
        elif ev in (0xA0, 0xB0, 0xE0):
            p += 2
        elif ev in (0xC0, 0xD0):
            p += 1
        else:
            break
    notes = [n for _, n, _ in ons]
    vels = [v for _, _, v in ons]
    return {
        "events": len(ons),
        "note_mod4_locked": all(notes[i] % 4 == i % 4 for i in range(len(notes))),
        "vel_parity_locked": all(vels[i] % 2 == (i + 1) % 2 for i in range(len(vels))),
        "note_digits": [(notes[i] - 48 - (i % 4)) // 4 for i in range(len(notes))],
        "vel_digits": [(vels[i] - 50 - ((i + 1) % 2)) // 2 for i in range(len(vels))],
    }


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------
def strip_label(frag):
    """Fragments are shipped as "<n>:<text>"."""
    return frag.split(":", 1)[1] if frag and re.match(r"^\d:", frag) else frag


def solve_url(frags, part2_candidates):
    p1 = [strip_label(frags["1a"]), strip_label(frags["1b"])]
    p3 = [strip_label(frags["3a"]), strip_label(frags["3b"])]
    p4 = [strip_label(frags["4"])]
    p5 = [strip_label(frags["5a"]), strip_label(frags["5b"])]
    tried = 0
    for a, b, c, d, e in itertools.product(p1, part2_candidates, p3, p4, p5):
        url = a + b + c + d + e
        tried += 1
        if hashlib.sha256(url.encode()).hexdigest() == TARGET_SHA256:
            return url, tried
    return None, tried


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jpg", default="dead_drop.jpg")
    ap.add_argument("--work", default="work", help="scratch directory")
    ap.add_argument("--fs", help="skip stages 1-4 and use this already "
                                 "extracted filesystem directory")
    ap.add_argument("--part2", action="append", default=[],
                    help="candidate for the unrecovered fragment 2 "
                         "(repeatable); defaults to a few guesses")
    args = ap.parse_args()

    if args.fs:
        fs = args.fs
    else:
        os.makedirs(args.work, exist_ok=True)
        print("[1] steghide (passphrase %r) ..." % STEG_PASSPHRASE)
        blob = steghide_extract(args.jpg, os.path.join(args.work, "laptop.txt"))
        print("    laptop.txt: %d bytes, alphabet=%s"
              % (len(blob), "base36" if set(blob.decode()) <= set(B36) else "?"))

        print("[2] base36 decode ...")
        xz = base36_decode(blob.decode())
        open(os.path.join(args.work, "laptop.xz"), "wb").write(xz)
        print("    %d bytes, magic=%s" % (len(xz), xz[:6].hex()))

        print("[3] xz decompress ...")
        img = lzma.decompress(xz)
        img_path = os.path.join(args.work, "laptop.ext4.img")
        open(img_path, "wb").write(img)
        print("    %d bytes ext4 image" % len(img))

        print("[4] ext4 extract (incl. deleted inodes 20 and 26) ...")
        fs = ext4_extract(img_path, os.path.join(args.work, "fs"))

    print("[5] decoding fragments ...")
    frags = recover_fragments(fs)
    for k in sorted(frags):
        print("    %-3s %s" % (k, repr(frags[k])))

    mid = os.path.join(fs, "tune.mid")
    if os.path.exists(mid):
        info = midi_structure(mid)
        print("    (tune.mid not decoded: %d events, note%%4 locked=%s, "
              "vel parity locked=%s -- unused, see Writeup.md)"
              % (info["events"], info["note_mod4_locked"],
                 info["vel_parity_locked"]))

    cands = args.part2 or [strip_label(frags["2"]), ".supabase.in",
                           ".supabase.io"]
    print("[6] assembling (part 2 candidates: %s) ..." % cands)
    url, tried = solve_url(frags, cands)
    if url:
        print("    SOLVED after %d combinations:\n    %s" % (tried, url))
        return 0
    print("    no combination of %d matched sha256 %s" % (tried, TARGET_SHA256))
    print("    -> fragment 2 is still wrong/missing; see Writeup.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())
