# Quantum Echo — Writeup

**Category:** Crypto

The handout is a single `challenge.json` — a "forensic export from a simulated quantum-inspired telemetry bench." The story says the key was *refreshed* before sealing, the firmware source is gone, and all that survives of the sealing scheme is "a 32-byte block size and a counter that starts at zero."

The file has four parts:

| Key | What's in it |
|---|---|
| `quantum_transcript` | 80 events over 40 samples: basis records, key taps, discard notices, audit taps |
| `register` | 160 `(x, z)` rows, a prose description of the controller, 8 calibration probes, a pad-contact trace |
| `sealed_flag` | 39 bytes of hex |
| `seal_record` | field order `s:t:e0:q` and three SHA-256 "compatibility vectors" |

No code anywhere. The controller is described in English, which is the whole point — you have to turn the prose into equations.

## The transcript is mostly theatre

The BB84-looking part sorts itself out in one pass:

```
samples  0–15   Z/Z   key_tap -> register_seed      <- the 16 key bits
samples 16–23   X/X   audit_tap -> test_detector    <- error-check sacrifices
samples 24–39   Z/X   discard_notice               <- basis mismatch, thrown away
```

So of 40 samples only **16** survive sifting, and they all feed a sink called `register_seed`. That's the first real hint: the "key" is 16 bits, and it goes into the register.

The one event that isn't noise is at sample 0:

```json
{"sample": 0, "event": "audit_tap", "sink": "error_check",
 "reported_bit": 1, "source": "register_seed_contact_A"}
```

Note the `source`. Every other audit tap says `test_detector`; this one names a *contact*. Hold on to it — it's the only thing that makes the solve unique, and I didn't realise that until the linear algebra came back one rank short.

## Reading the controller out of the prose

`register.controller_model` describes the machine in words:

> The diagnostic fold word is input XOR the bitwise AND of two cyclically rotated copies of the input. The two rotation distances are distinct; the smaller distance is listed first.

> The diagnostic walk word is a single cyclic left rotation of the input.

> The one-bit echo state toggles when the walk-mask parity is one. Update the state before recording the row output. The row output is fold-mask parity XOR updated echo state XOR the selected calibration-pad bit.

"A single cyclic left rotation" reads like rotate-by-one, but it isn't — it means *one* rotation, by an unknown distance. The 8 calibration probes give `(input, fold_word, walk_word)` triples, so both distances are just a brute force over at most 32 × C(32,2) = 15,872 candidates, and 8 probes is far more than enough to pin them:

```python
walk = [r for r in range(32) if all(rotl(x, r) == w for x, _, w in P)]
fold = [(a, b) for a in range(32) for b in range(a+1, 32)
        if all(x ^ (rotl(x, a) & rotl(x, b)) == f for x, f, _ in P)]
```

Both come back with exactly one survivor:

```
fold_word(x) = x ^ (rotl(x, 5) & rotl(x, 11))
walk_word(x) = rotl(x, 7)
```

The pad contact is the easy one — `pad_contact_trace` lists 32 rows and it's just `A, B, …, P` repeating, i.e. `contact(i) = i mod 16`. Sixteen contacts for sixteen sifted key bits.

## The register is linear, so there is nothing to search

Writing out one row with the unknowns named — `S` the fold mask, `T` the walk mask, `e0` the initial echo, `pad[0..15]` the contacts:

```
z_i = parity(S & fold_word(x_i)) ^ echo_i ^ pad[i mod 16]
```

The echo looks stateful and sequential, which is what makes it feel like you need to guess. You don't. The echo toggles on `parity(T & walk_word(x_i))`, so after `i` rows it has flipped once per set parity:

```
echo_i = e0 ^ parity(T & walk_word(x_0)) ^ ... ^ parity(T & walk_word(x_i))
```

and because `parity(m & u) ^ parity(m & v) == parity(m & (u ^ v))`, the whole history collapses into a single running XOR:

```
echo_i = e0 ^ parity(T & C_i),    C_i = walk_word(x_0) ^ ... ^ walk_word(x_i)
```

That's the trick of the challenge. Every row is now **linear over GF(2)** in 81 unknowns:

| Unknown | Bits | Coefficient in row `i` |
|---|---|---|
| `S` (fold mask) | 32 | `fold_word(x_i)` |
| `T` (walk mask) | 32 | `C_i` (running XOR) |
| `e0` | 1 | always 1 |
| `pad[0..15]` | 16 | 1 at `i mod 16` |

160 observations, 81 unknowns, one Gaussian elimination. No brute force over the masks, no guessing the echo.

## One bit short

Running the elimination on the 160 rows gives **rank 80 of 81** — underdetermined by exactly one bit. The reason is a symmetry in the model: flipping `e0` *and* all 16 pad bits changes nothing, because every row contains `e0` once and exactly one pad bit, so the two flips cancel in every single equation. The system can never tell those two solutions apart.

This is where that odd audit tap pays off. `register_seed_contact_A` with `reported_bit: 1` is one more equation —

```
pad[A] = 1
```

— added to the system it takes the rank to 81 and the solution is unique. Back-substituting and replaying the recovered state against all 160 rows reproduces every `z`:

```
[+] fold word : x ^ (rotl(x,5) & rotl(x,11))
[+] walk word : rotl(x,7)
[+] audit tap pins pad[A] = 1
[+] all 160 register rows reproduced
[+] fold_mask = 1d0cc456
[+] walk_mask = ccc78639
[+] e0        = 0
[+] pad (sifted key, 16 bits) = 1010010010100001
```

## The seal, and the lie in the brief

`seal_record` gives `field_order: ["s", "t", "e0", "q"]` and three compatibility vectors — `(material_ascii, counter_u32, digest_hex)` triples with material strings shaped like `5a3c91e7:0f2b7d64:1:0110101100011101`. That's the field order spelled out: fold mask hex, walk mask hex, echo bit, pad bits. The vectors also tell you the construction without the firmware. The README's "32-byte block size, counter starts at zero" plus a SHA-256 digest per block is enough to guess:

```python
block = sha256(material_ascii.encode() + counter.to_bytes(4, "big")).digest()
```

All three published vectors match that exactly, including the two that differ only in counter, which confirms the counter is a big-endian `u32` appended to the material.

So the keystream is `SHA256(material || counter_be32)` for `counter = 0, 1, …` concatenated, XORed into `sealed_flag`:

```
material = 1d0cc456:ccc78639:0:1010010010100001
```

And this is what the story was actually about. The brief claims the key was *refreshed* before sealing. It wasn't. The 16 pad bits in the register — the ones every one of those 160 masked telemetry rows leaks a linear equation about — **are** the sifted key from the 16 `key_tap` samples, and they went straight into the seal material unchanged. The telemetry readings you were handed as "noise" are a full algebraic description of the key protecting them.

## Flag

`d4rk{quantum_echo_reuse_breaks_the_pad}`

## Notes

- "A single cyclic left rotation" cost me a detour. It means one rotation of unknown distance, not rotate-by-1 — and the calibration probes exist precisely so you can pin it. If a challenge hands you input/output pairs for a primitive it just described, it's telling you the description is incomplete.
- Stateful-looking doesn't mean nonlinear. `parity(m&u) ^ parity(m&v) = parity(m&(u^v))` turns the entire echo history into one accumulator and the whole thing falls to linear algebra.
- When a GF(2) solve comes back exactly one rank short, look for a symmetry rather than more data. Here it was the `e0` ↔ pad global flip, and the fix was already sitting in the transcript as the single audit tap that named a contact instead of the test detector.
- Samples 16–39 contribute nothing. They're there so the transcript looks like a real BB84 run.

## Solver

```bash
python3 solver.py challenge.json
```

Runs in well under a second — rotation brute force, Gaussian elimination, replay check against all 160 rows, seal-scheme verification against the compatibility vectors, then the XOR.

| File | Purpose |
|---|---|
| `challenge.json` | the handout |
| `solver.py` | full chain: calibration → GF(2) solve → seal → flag |
| `solve.md` | short notes written during the solve |
| `Writeup.md` | this document |
