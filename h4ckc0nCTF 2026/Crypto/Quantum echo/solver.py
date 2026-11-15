#!/usr/bin/env python3
"""Solver for "Echo Register: Quantum Echo".

Chain of reasoning
------------------
1. The controller's two diagnostic words are recovered from the calibration
   probes by brute force:
       fold_word(x) = x ^ (rotl(x, a) & rotl(x, b))      (a < b, unknown)
       walk_word(x) = rotl(x, r)                         (r unknown)
2. Each register row obeys
       z_i = parity(fold_mask & fold_word(x_i))
             ^ echo_i
             ^ pad[contact(i)]
   with the echo bit toggling on every walk-mask parity:
       echo_i = e0 ^ parity(walk_mask & C_i),  C_i = XOR of walk_word(x_j), j<=i
   Because parity(m&u) ^ parity(m&v) == parity(m&(u^v)), every term is linear
   over GF(2) in the 81 unknown bits (32 fold-mask + 32 walk-mask + e0 + 16 pad).
   160 observations -> solve by Gaussian elimination.
3. e0 and the whole pad are confounded (flipping all 17 bits is a symmetry).
   The transcript's audit_tap on sample 0 ("register_seed_contact_A",
   reported_bit = 1) pins pad[A] and makes the solution unique.
4. The "refreshed key" is a lie: the seal material is the register state
   "fold:walk:e0:pad", and the keystream is
       SHA256(material_ascii || counter_u32_be), counter = 0, 1, 2, ...
   (confirmed against the published compatibility vectors).
   flag = sealed_flag XOR keystream.
"""

import binascii
import hashlib
import json
import os
import sys

MASK32 = 0xFFFFFFFF


def rotl(x, n):
    n %= 32
    return ((x << n) | (x >> (32 - n))) & MASK32 if n else x & MASK32


def parity(x):
    return bin(x).count("1") & 1


# --- step 1: recover the rotation distances from the calibration probes -----

def recover_rotations(probes):
    P = [(int(p["input"], 16), int(p["fold_word"], 16), int(p["walk_word"], 16))
         for p in probes]

    walk = [r for r in range(32) if all(rotl(x, r) == w for x, _, w in P)]
    fold = [(a, b) for a in range(32) for b in range(a + 1, 32)
            if all(x ^ (rotl(x, a) & rotl(x, b)) == f for x, f, _ in P)]

    if len(walk) != 1 or len(fold) != 1:
        raise SystemExit(f"rotations not unique: walk={walk} fold={fold}")
    return fold[0], walk[0]


# --- step 2/3: solve the GF(2) system ---------------------------------------

N_UNK = 32 + 32 + 1 + 16          # fold mask | walk mask | e0 | pad[0..15]
I_WALK, I_E0, I_PAD = 32, 64, 65


def build_equations(observations, fold_rots, walk_rot, contact_of):
    (a, b), r = fold_rots, walk_rot
    eqs = []
    acc = 0
    for i, o in enumerate(observations):
        x = o["x"]
        fold_word = x ^ (rotl(x, a) & rotl(x, b))
        acc ^= rotl(x, r)                      # running XOR of walk words
        row = fold_word | (acc << I_WALK)      # mask bits enter directly
        row |= 1 << I_E0
        row |= 1 << (I_PAD + contact_of(i))
        eqs.append((row, o["z"]))
    return eqs


def solve_gf2(eqs, n):
    pivots = {}
    for row, rhs in eqs:
        for col in range(n):
            if not (row >> col) & 1:
                continue
            if col in pivots:
                prow, prhs = pivots[col]
                row ^= prow
                rhs ^= prhs
            else:
                pivots[col] = (row, rhs)
                break
        else:
            if rhs:
                raise SystemExit("inconsistent system - model assumption wrong")
    if len(pivots) != n:
        raise SystemExit(f"underdetermined: rank {len(pivots)} of {n}")

    sol = [0] * n
    for col in sorted(pivots, reverse=True):
        row, rhs = pivots[col]
        bit = rhs
        for c2 in range(col + 1, n):
            if (row >> c2) & 1:
                bit ^= sol[c2]
        sol[col] = bit
    return sol


def check(observations, fold_rots, walk_rot, fold_mask, walk_mask, e0, pad,
          contact_of):
    (a, b), r = fold_rots, walk_rot
    acc, echo = 0, e0
    for i, o in enumerate(observations):
        x = o["x"]
        acc ^= rotl(x, r)
        echo = e0 ^ parity(walk_mask & acc)    # toggle, then record
        z = parity(fold_mask & (x ^ (rotl(x, a) & rotl(x, b)))) ^ echo \
            ^ pad[i % 16]
        if z != o["z"]:
            return False
    return True


# --- step 4: the seal --------------------------------------------------------

def keystream(material, n):
    out = b""
    counter = 0
    while len(out) < n:
        out += hashlib.sha256(material.encode() + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:n]


def verify_seal_scheme(vectors):
    for v in vectors:
        want = v["digest_hex"]
        got = hashlib.sha256(
            v["material_ascii"].encode() + v["counter_u32"].to_bytes(4, "big")
        ).hexdigest()
        if got != want:
            raise SystemExit("compatibility vector mismatch - wrong seal scheme")


def main(path):
    with open(path) as fh:
        data = json.load(fh)

    reg = data["register"]
    fold_rots, walk_rot = recover_rotations(reg["controller_calibration"]["probes"])
    print(f"[+] fold word : x ^ (rotl(x,{fold_rots[0]}) & rotl(x,{fold_rots[1]}))")
    print(f"[+] walk word : rotl(x,{walk_rot})")

    # The contact trace lists 32 rows; the A..P cycle repeats for all 160.
    trace = {r["observation_index"]: ord(r["contact"]) - ord("A")
             for r in reg["pad_contact_trace"]["rows"]}
    for idx, contact in trace.items():
        assert contact == idx % 16, "contact trace is not the A..P cycle"
    contact_of = lambda i: trace.get(i, i % 16)

    obs = reg["observations"]
    eqs = build_equations(obs, fold_rots, walk_rot, contact_of)

    # audit_tap on sample 0 reports the contact-A pad bit: breaks the
    # e0 <-> pad global-flip symmetry.
    for ev in data["quantum_transcript"]["event_log"]:
        if ev["event"] == "audit_tap" and ev.get("source", "").startswith("register_seed_contact_"):
            k = ord(ev["source"][-1]) - ord("A")
            eqs.append((1 << (I_PAD + k), ev["reported_bit"]))
            print(f"[+] audit tap pins pad[{ev['source'][-1]}] = {ev['reported_bit']}")

    sol = solve_gf2(eqs, N_UNK)
    fold_mask = sum(sol[i] << i for i in range(32))
    walk_mask = sum(sol[I_WALK + i] << i for i in range(32))
    e0 = sol[I_E0]
    pad = sol[I_PAD:I_PAD + 16]

    if not check(obs, fold_rots, walk_rot, fold_mask, walk_mask, e0, pad, contact_of):
        raise SystemExit("solution does not reproduce the observations")
    print(f"[+] all {len(obs)} register rows reproduced")

    pad_str = "".join(str(b) for b in pad)
    print(f"[+] fold_mask = {fold_mask:08x}")
    print(f"[+] walk_mask = {walk_mask:08x}")
    print(f"[+] e0        = {e0}")
    print(f"[+] pad (sifted key, 16 bits) = {pad_str}")

    verify_seal_scheme(data["seal_record"]["compatibility_vectors"])
    print("[+] seal scheme confirmed: SHA256(material || counter_be32)")

    order = {"s": f"{fold_mask:08x}", "t": f"{walk_mask:08x}",
             "e0": str(e0), "q": pad_str}
    material = ":".join(order[f] for f in data["seal_record"]["field_order"])
    print(f"[+] material = {material}")

    ct = binascii.unhexlify(data["sealed_flag"])
    flag = bytes(a ^ b for a, b in zip(ct, keystream(material, len(ct))))
    print()
    print("FLAG:", flag.decode())
    return flag


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1
         else os.path.join(os.path.dirname(os.path.abspath(__file__)), "challenge.json"))
