#!/usr/bin/env python3
"""
Solver for "twisted-vigenere".

pt = random.randbytes(2536)  (MT19937 output, 634 words)
ct = pt XOR flag (repeating key)

The MT19937 recurrence
    x[n+624] = x[n+397] ^ ((x[n] & UPPER) | (x[n+1] & LOWER)) >> 1 ^ (MAG if x[n+1] & 1)
on *untempered* outputs is linear over GF(2). Untempering is linear too.
With 634 words we get 10 such relations = 320 GF(2) equations whose only
unknowns are the key bits (MT state cancels out). Solve for every key length.
"""
import base64
import string
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("output.txt")
ct = base64.b64decode(OUT.read_text().replace("\n", ""))
NWORDS = len(ct) // 4
MAG = 0x9908B0DF


def temper(y):
    y ^= y >> 11
    y ^= (y << 7) & 0x9D2C5680
    y ^= (y << 15) & 0xEFC60000
    y ^= y >> 18
    return y & 0xFFFFFFFF


# Build untemper as a GF(2) 32x32 matrix by inverting temper's matrix.
def mat_of(f):
    cols = [f(1 << j) for j in range(32)]
    return [sum(((cols[j] >> i) & 1) << j for j in range(32)) for i in range(32)]  # rows


def mat_inv(rows):
    n = 32
    a = [(rows[i], 1 << i) for i in range(n)]
    for c in range(n):
        p = next(r for r in range(c, n) if (a[r][0] >> c) & 1)
        a[c], a[p] = a[p], a[c]
        for r in range(n):
            if r != c and (a[r][0] >> c) & 1:
                a[r] = (a[r][0] ^ a[c][0], a[r][1] ^ a[c][1])
    return [a[i][1] for i in range(n)]


U = mat_inv(mat_of(temper))  # U[i] = bitmask of y-bits giving untempered bit i


def solve_len(L):
    nv = 8 * L
    # word j bit b (little-endian) = ct bit ^ key var
    def ybit(j, b):
        p = 4 * j + b // 8
        var = 1 << (8 * (p % L) + b % 8)
        const = (ct[p] >> (b % 8)) & 1
        return var, const

    def xbit(j, i):  # untempered bit i of word j: affine expr (mask, const)
        m = c = 0
        row = U[i]
        for b in range(32):
            if (row >> b) & 1:
                v, k = ybit(j, b)
                m ^= v; c ^= k
        return m, c

    eqs = []
    for n in range(NWORDS - 624):
        for k in range(32):
            m, c = xbit(n + 624, k)
            for (mm, cc) in [xbit(n + 397, k)]:
                m ^= mm; c ^= cc
            src = k + 1  # bit of y that shifts into position k
            if src == 31:
                mm, cc = xbit(n, 31)
                m ^= mm; c ^= cc
            elif src < 31:
                mm, cc = xbit(n + 1, src)
                m ^= mm; c ^= cc
            if (MAG >> k) & 1:
                mm, cc = xbit(n + 1, 0)
                m ^= mm; c ^= cc
            eqs.append((m, c))

    # Extra 31 equations from the *first* twist (the stream starts on a fresh
    # twist boundary because Random() was never used before randbytes):
    #   x[623] = x[396] ^ f( top(old_mt[623]) | low31(x[0]) )
    # top(old_mt[623]) is unknown, so only bit 30 of the result is unconstrained.
    for k in range(32):
        if k == 30:
            continue
        m, c = xbit(623, k)
        mm, cc = xbit(396, k); m ^= mm; c ^= cc
        if k < 30:
            mm, cc = xbit(0, k + 1); m ^= mm; c ^= cc
        if (MAG >> k) & 1:
            mm, cc = xbit(0, 0); m ^= mm; c ^= cc
        eqs.append((m, c))

    # known plaintext constraints: "gctf{" ... "}"  and ASCII top bit 0
    def fix(pos, val):
        for b in range(8):
            eqs.append((1 << (8 * pos + b), (val >> b) & 1))
    for i, ch in enumerate(b"gctf{"):
        fix(i, ch)
    fix(L - 1, ord("}"))
    for i in range(L):
        eqs.append((1 << (8 * i + 7), 0))

    # Gaussian elimination
    piv = {}
    for m, c in eqs:
        for p, (pm, pc) in piv.items():
            if (m >> p) & 1:
                m ^= pm; c ^= pc
        if m == 0:
            if c:
                return None  # inconsistent
            continue
        p = m.bit_length() - 1
        for q in list(piv):
            if (piv[q][0] >> p) & 1:
                piv[q] = (piv[q][0] ^ m, piv[q][1] ^ c)
        piv[p] = (m, c)
    free = [v for v in range(nv) if v not in piv]
    return piv, free


def assemble(L, piv, free, assign):
    val = 0
    for v, bit in zip(free, assign):
        val |= bit << v
    for p, (m, c) in piv.items():
        bit = c ^ (bin((m & ~(1 << p)) & val).count("1") & 1)
        val |= bit << p
    return val.to_bytes(L, "little")


for L in range(6, 60):
    r = solve_len(L)
    if r is None:
        continue
    piv, free = r
    print(f"[+] key length {L} consistent, {len(free)} free bits")
    if len(free) <= 16:
        for a in range(1 << len(free)):
            key = assemble(L, piv, free, [(a >> i) & 1 for i in range(len(free))])
            if all(chr(x) in string.printable for x in key):
                print("   ", key.decode())
