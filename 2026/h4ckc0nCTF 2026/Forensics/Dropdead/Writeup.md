# Drop Dead — writeup

| | |
|---|---|
| Challenge | Drop Dead |
| Points | 100 |
| Author | paramveer504 |
| Given | `dead_drop.zip` → `dead_drop.jpg` (4,532,884 B) |
| Hint | *"Hmmm.. I have heard of a foreign six, travelers call it 6^2"* |

**Answer**

```
https://hljuqfqgsdycotnhdndt.supabase.co/storage/v1/object/public/image/Screenshot%20from%202026-11-09%2017-32-54.png
```

`sha256` = `9f2bce0edb56e82e2e5ecf5e9585f9fb19495c6767f1dd1920742986119ca0f8`, matching `/home/agent/README` in the recovered filesystem.

---

## 0. The hint says 36 twice

`6^2 = 36`, and it is used **twice**, which is what makes the hint worth more than one sentence:

1. `36` is the literal **steghide passphrase**.
2. **Base36** is the encoding of the payload that comes out.

"foreign six" / "travelers" is flavour; the only operative content is 36.

## 1. Ruling out the obvious (and ruling it out properly)

Before steghide, everything cheap was checked, because a 4.5 MB JPEG invites a lot of guesses:

* **`strings`** — the only readable output is `JFIF` and the two standard Huffman-table byte runs (`%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz`). These appear in essentially every JPEG. The rest is entropy-coded noise that happens to land in the ASCII range.
* **Container** — last `FFD9` is the final two bytes; zero appended data. `binwalk` agrees ("total size: 4532884 bytes").
* **Segments** — `SOI, APP0, DQT×2, SOF0, DHT×4, SOS`. No `APP1`/EXIF, no `COM`.
* **Quantisation tables** — both match IJG quality 89 scaling **64/64 exactly**, so nothing is hidden there.
* **DCT coefficients** — a hand-written baseline JPEG decoder pulled all 5.9 M non-zero AC coefficients. Pair χ² = 462,536 against dof 20 (no JSteg/OutGuess equalisation) and |1|/|2| ≈ 3.2 (no F5 shrinkage).

That last test is worth a caveat: **it cannot see steghide.** steghide swaps coefficient values via graph matching specifically to preserve the first-order histogram, so a clean χ² means nothing against it. The same is largely true of OutGuess, which reserves coefficients to repair its own statistics. The DCT test only eliminated JSteg and F5.

The ZIP container was also fully accounted for — local header 43 B, data 4,532,884 B, central directory 95 B, EOCD 22 B, zero gap, one entry. One useful artefact fell out: the NTFS extra field gives a UTC mtime of `2026-11-09 13:12:40`, while the DOS field gives local `18:42:42`. The difference is exactly **+5:30**, i.e. the packaging machine ran on IST — consistent with the author's handle.

## 2. steghide

```
steghide extract -sf dead_drop.jpg -p 36
```

```
embedded file "laptop.txt":
  size: 208.4 KB
  encrypted: rijndael-128, cbc
  compressed: yes
```

`laptop.txt` is 213,426 characters drawn only from `0-9A-Z` — the Base36 alphabet, as the hint promised.

## 3. Base36 → XZ → ext4

Treat the whole thing as one big base-36 integer and convert to bytes. `int(s, 36)` is quadratic in CPython and would be painful at 213 k digits, so `solver.py` does a divide-and-conquer recombination.

```
137,924 bytes, magic fd 37 7a 58 5a   -> XZ
xz -d                                  -> 33,554,432 bytes
file                                   -> Linux rev 1.0 ext4 filesystem data
```

`laptop.txt` was never a text file — it is a 32 MiB disk image of a laptop.

## 4. The filesystem

macOS cannot mount ext4, but `debugfs` reads it without mounting and without privileges:

```
debugfs -R "rdump / ./out" laptop.ext4.img
```

```
/etc/krb5.keytab                         856 B
/var/backups/backup.keytab              7343 B
/home/agent/README                        90 B   <- the SHA-256 target
/home/agent/notes.txt                    103 B
/home/agent/.bash_history                261 B   <- the URL template
/home/agent/Documents/report.pdf         603 B
/home/agent/Pictures/photo.png          7831 B
/home/agent/prints/old_bracket.gcode    3590 B
/home/agent/research/session_0427.nwb  271352 B
/usr/share/fonts/misc/term.fon          1181 B
/usr/share/fonts/misc/vga8.fon           229 B
```

`.bash_history` gives the shape of the answer and names two files that are gone:

```sh
cat bracket.gcode | head -n 20
klist -k /etc/krb5.keytab
sudo cp /etc/krb5.keytab /var/backups/backup.keytab
python3 -c "print('https://example.com/storage/v1/object/public/image/test.png')"
rm bracket.gcode
cd ~/Music
rm tune.mid
history -c
```

`debugfs -R lsdel` finds both as orphaned inodes, still fully intact:

```
inode 20  1898 B  -> tune.mid
inode 26  4749 B  -> bracket.gcode
```

**`history -c` does not erase the file**, `rm` does not erase the blocks, and `lost+found` and the journal are both empty — the deleted files are recovered with `debugfs -R "dump <20> tune.mid"`.

## 5. Five fragments, each in a different esolang

`README` states the goal:

```
sha256 of the final url:
9f2bce0edb56e82e2e5ecf5e9585f9fb19495c6767f1dd1920742986119ca0f8
```

Each carrier emits a `<n>:<text>` fragment. Fragments 1, 3 and 5 each have **two** carriers — one real, one decoy — so the final step is a small brute force verified by the hash.

### 1 — Kerberos keytabs → Brainfuck and Ook!

The program is sliced across the **key material** of the keytab entries. The catch: entries are stored in **descending kvno order** (8→1, 67→1), and the short final chunk sits first. Sort by kvno before concatenating or the output is scrambled.

* `/etc/krb5.keytab` (realm `D4RKC0DE.LOCAL`) — Brainfuck restricted to `+ - .`: one cell, no loops.
  → `1:https://hljuqfqgsdycotnhdndt`
* `/var/backups/backup.keytab` (realm `BACKUP.LOCAL`) — **Ook!**, 813 tokens → 406 Brainfuck ops.
  → `1:https://xqzvbnmplkjhgfdsaytr`

`xqzvbnmplkjhgfdsaytr` is keyboard-mash (`vbnm`, `plkjhgfdsa`, `ytr`) — a tell for the decoy, though the hash is what actually decides.

### 3 — Bitmap fonts → Befunge-93 and Deadfish

Both `.fon` files hide their program after the `VGA8\0` marker.

* `vga8.fon` — `0"/cilbup/tcejbo/1v/egarots/:3">:#,_@`
  This is not "reversed text", it is **Befunge-93**: `0` pushes the terminator, `"…"` pushes the string, and `>:#,_@` is the standard print-until-zero idiom. Because a stack reverses what it is given, the string is stored backwards on purpose.
  → `3:/storage/v1/object/public/`
* `term.fon` — 581 characters of `i`, `d`, `s`, `o` only. That is **Deadfish**: `i`ncrement, `d`ecrement, `s`quare, `o`utput, with the accumulator resetting to 0 at −1 and 256. (The challenge title is the tell.)
  → `3:/storage/v1/object/sign/`

A nice touch: inside the long `d` runs an `s` appears after exactly **36** decrements — the hint echoed in the data.

Supabase serves public buckets from `/object/public/`; `/object/sign/` requires a token that is nowhere to be found, so `public` is the live one.

### 4 — NWB / HDF5 → Piet

`session_0427.nwb` is a plausible neuroscience file. `/acquisition/calcium_frame/data` is `(8, 5504, 3)` uint8 with the attribute **`codel_size = 8`** — "codel" is the Piet unit, so this is a 1 × 688 codel Piet program.

It uses exactly the 18 Piet hues, no white or black, in a single row, so control flow is just "walk right" and a tiny interpreter suffices. The program is the simplest possible idiom — each block's **size is the ASCII code**:

```
push 52  outc -> '4'    push 58  outc -> ':'    push 105 outc -> 'i'
push 109 outc -> 'm'    push 97  outc -> 'a'    push 103 outc -> 'g'
push 101 outc -> 'e'    push 47  outc -> '/'
```

→ `4:image/`

The other two datasets are chaff: `timestamps` is `0.00, 0.01, 0.02 …` exactly, `roi_traces` is Gaussian noise.

### 5 — G-code → ArnoldC and a marker-triplet scheme

Data rides in the **third decimal of the extruder `E` value**; the X/Y coordinates are noise.

* `old_bracket.gcode` (kept) — the fractions read **forward** are an **ArnoldC** program:
  ```
  IT'S SHOWTIME
  TALK TO THE HUMAN "5:Screenshot%20from%202026-11-09%2017-32-45.png"
  YOU HAVE BEEN TERMINATED
  ```
* `bracket.gcode` (deleted, inode 26) — 142 fractions in `(96, 46, data)` triplets, i.e. `` `.`` as a marker before every payload byte, and the payload **reversed**:
  ```
  gnp.45-23-7102%90-11-620202%morf02%tohsneercS:5
  -> 5:Screenshot%20from%202026-11-09%2017-32-54.png
  ```

The two differ only in the timestamp — `17-32-45` versus `17-32-54`. **This is where the challenge bites.** Transposing those four digits by hand is extremely easy and costs you the flag with no feedback other than a hash mismatch. Reverse the sequence programmatically (`fr[2::3][::-1]`), never by eye.

The deleted file wins.

### 2 — the hostname suffix

`.supabase.co`, forced by the Supabase URL shape and confirmed by the hash.

`tune.mid` (deleted, inode 20) is the only carrier left unaccounted for and is presumably the intended source, but its encoding was never cracked and it is not needed. What is known about it, for anyone who wants to finish it:

* 209 note-on events, channel 0, every note exactly 30 ticks long, note-off velocity always 0.
* `note[i] % 4 == i % 4` for **all** i, with notes in `[48, 83]` — so each position draws from one of four augmented triads and carries 9 free values (3 pitch classes × 3 octaves).
* `velocity[i] % 2 == (i+1) % 2` for **all** i, with velocities in `[50, 119]` — 35 free values.
* Inter-onset gaps in `[150, 268]`, no periodic structure at any period from 2 to 30.

Both locked relations hold across all 209 events, so they are deliberate, not chance. Ruled out: raw ASCII, Base36 big-integer (forward and reversed), Deadfish under all 4⁹ digit→command maps, Brainfuck and Ook! (**no** choice of two digits balances brackets at all), affine maps of note/velocity/gap, and marker layouts at every period up to 30. A MIDI esolang such as Velato is the obvious remaining candidate.

### Pure decoys

* `photo.png` — a 64×64 gradient that is exactly `R = 4x, G = 4y, B = 128`. Bilinear fit residual is **0.00 everywhere**, all 64 PNG row filters are 0, LSB planes are all zero, no ancillary chunks. Zero information content.
* `report.pdf` — 603 bytes, every one of them ordinary PDF structure.
* `notes.txt` — a to-do list that is really a map: *print bracket* → `prints/`, *calcium data* → the NWB, *renew kerberos tickets* → the keytabs, *clean up old files* → the deleted inodes.

## 6. Assembly

```
1  https://hljuqfqgsdycotnhdndt
2  .supabase.co
3  /storage/v1/object/public/
4  image/
5  Screenshot%20from%202026-11-09%2017-32-54.png
```

```
https://hljuqfqgsdycotnhdndt.supabase.co/storage/v1/object/public/image/Screenshot%20from%202026-11-09%2017-32-54.png
sha256 = 9f2bce0edb56e82e2e5ecf5e9585f9fb19495c6767f1dd1920742986119ca0f8   ✓
```

It takes me a flag!

## 7. flag
Get a Screenshot from 2026-11-09 17-32-54.png, it looks like a flag!

```
d4rk{f0r31gn_s1x?}
```

---

## Reproducing

```sh
python3 solver.py --jpg dead_drop.jpg --work work     # full chain
python3 solver.py --fs 04_filesystem                  # from the extracted fs
```

`solver.py` is pure Python apart from two steps that shell out:

* **steghide** — not in Homebrew and not in conda-forge; the solver builds a throwaway `debian:stable-slim` container with the Debian package.
* **debugfs** (e2fsprogs) — same approach; reads ext4 without mounting, so no `--privileged` and no macOS ext4 driver.

`zsteg` is PNG/BMP only and crashes on a JPEG (`undefined method 'alpha_used?' for ZPNG::JPEG::SOF0`) — that is a wrong-tool error, not a negative result. `npiet` is not packaged in Debian, hence the hand-written Piet interpreter.

## Layout

```
01_steghide/laptop.txt                 Base36 blob from steghide
02_base36/laptop_decoded.xz            after Base36 decode
03_ext4/laptop.ext4.img                after xz -d  (32 MiB)
04_filesystem/                         debugfs rdump output
05_recovered/{tune.mid,bracket.gcode}  deleted inodes 20 and 26
06_derived/                            Piet images, keytab payloads, preview
tools/{jdct.py,b36.py,piet.py}         DCT analyser, base36, Piet
solver.py                              full chain
```

## Takeaways

1. A clean DCT histogram does **not** clear steghide — it is built to preserve exactly that statistic. Only JSteg and F5 were actually excluded.
2. `history -c` leaves the file, `rm` leaves the blocks. `lsdel` plus `dump <inode>` recovered two of the five fragments, including the one that is actually correct.
3. Decoys were pixel-perfect-deterministic (`photo.png`) rather than merely plausible, which is a usable signal: zero residual means zero payload.
4. Reverse strings in code. A four-digit transposition read by eye (`17-23-54` for `17-32-54`) is invisible and the only feedback is a hash that does not match.
