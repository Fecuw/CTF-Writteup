#!/usr/bin/env python3
"""
CSI-HASH (GlacierCTF) solver.

The hash of a 32-byte message m is  [l_1^m_1 * ... * l_32^m_32] * E_0,
i.e. the CSIDH class-group action with the message bytes as exponents.
Two exponent vectors give the same curve iff their difference lies in the
relation lattice  L = { v in Z^32 : prod l_i^v_i is principal in Z[sqrt(-p)] }.

L was precomputed once with PARI (see Writeup.md / precompute.sage) and
LLL-reduced; its basis is embedded below.  For a challenge c we solve a small
CVP: find v in L with c + v inside the printable range, v != 0.

usage:  python3 solver.py [HOST PORT]      (default challs.glacierctf.com 13378)
        python3 solver.py --test <32-letter string>
"""
import random
import socket
import sys
from fractions import Fraction

LO, HI = 33, 126           # printable ASCII, no space / newline

BASIS = [
    [0, -4, 2, -1, -1, -1, 1, -2, 0, 0, -4, 1, -2, 2, 0, 1, 0, -1, -1, 3, -1, 3, -2, -1, 4, 3, 5, 1, 1, -1, -2, -4],
    [3, 1, 0, -1, -2, -3, 1, 2, 0, -6, 1, -1, 0, 4, 3, -2, -1, -2, -4, 0, -1, 2, 2, 0, 1, 2, -2, 1, 3, -1, -3, 1],
    [3, -2, 4, -2, -3, -1, 0, 2, 1, -4, 0, -2, -1, -4, -1, -1, 3, -4, -2, 0, 2, 2, 3, 0, 4, 3, -1, 0, -1, 0, -2, -1],
    [0, 1, 3, -2, -1, 0, 3, 3, 1, 4, 0, -1, 0, -5, -3, 1, -1, -4, 1, 1, -3, -2, 1, 2, 1, 1, 0, -3, -1, -2, 2, 1],
    [5, -3, 0, -2, -3, -2, 3, 1, -1, -2, -3, 3, 0, -1, -3, -3, -2, -2, -2, 1, 0, 0, 4, 4, 4, 3, 2, -1, 1, -3, -4, -1],
    [-5, -3, 0, -1, 3, -1, -3, 1, 1, 0, 4, 0, 3, -2, -2, 1, 5, 1, 3, -2, 5, -1, 3, 2, 2, -2, 1, -2, -1, 2, 0, -1],
    [-2, -1, 1, -3, -1, -2, 0, 2, 2, 3, -1, 0, 1, 2, 0, -2, 3, -3, -2, 2, -3, 0, 2, 5, -2, 0, 3, -2, 0, 2, -2, -2],
    [2, -1, 0, -1, 3, 2, -1, 1, -5, -4, 0, 5, -2, 3, 0, 1, -2, 4, -4, 0, 4, -1, -2, -2, 0, 2, 1, 1, 2, -1, -2, 2],
    [0, -4, -1, -1, 0, 1, -1, 2, 1, 1, 0, 5, -2, -2, -3, -2, -3, -1, 0, 2, 1, 1, -1, -2, 3, 5, -1, 3, 2, -3, 0, 2],
    [0, 5, -1, -2, 1, 1, 2, -2, 1, 2, -5, 2, 0, -3, -1, -1, -1, 2, 2, -3, -1, -6, 1, 3, -3, -4, 3, -1, -1, 4, 1, 0],
    [-1, 1, -2, 3, 0, 1, 1, 1, -3, 0, 0, 3, 3, 5, 0, 1, -2, -1, -4, 0, -5, 1, 4, 3, -1, -2, 1, -3, 0, 1, -4, 0],
    [0, 1, -5, 3, 0, 4, -2, 0, 3, 0, 0, 3, 2, -3, -2, -1, 0, -2, 1, -5, 3, -2, -1, -1, -2, -2, 0, 1, 2, 2, -2, 1],
    [-3, 1, -1, 0, 0, 0, -1, 0, 4, 2, 0, 2, 0, 3, 2, 1, -1, -2, 2, 2, -5, 3, -1, 3, -3, 0, 1, -2, 3, -5, -1, -3],
    [1, -3, 2, 0, -2, 0, 2, -1, 6, 1, -1, 1, -4, 0, 2, -2, 2, -2, -2, 0, -2, -3, -3, 2, -1, 1, 2, 1, 4, 0, 0, -1],
    [-3, 4, 1, 0, 2, -1, -2, 1, 0, 1, -2, -1, -1, -5, -2, 1, -4, 0, 4, 1, -3, 2, 2, 3, 3, -1, 1, 3, -1, -2, 1, -1],
    [-4, -1, 4, -1, 3, 4, -1, -2, 2, 2, -1, 1, -1, -3, -3, 1, 0, 2, -2, 1, 3, -1, -1, 1, 1, 1, 0, 2, 3, 1, 3, -2],
    [-4, -4, 1, 2, -3, 0, 4, 2, 0, -2, 1, 0, -1, 4, 3, 2, -2, -2, -6, 5, -1, 3, -3, -1, 0, 3, 0, 1, 4, -2, 2, 1],
    [0, 1, 0, 2, -2, 0, -1, 2, 0, 0, -1, -1, 2, -1, 1, 4, -1, 0, 2, -1, 5, -2, 1, -2, -1, 1, -3, -4, -1, 0, 2, 2],
    [0, 2, 0, 0, -3, 3, -1, 1, 3, -1, 3, 4, 1, -3, 0, -1, 3, -1, -6, -1, -1, 0, -3, 1, -5, -1, -4, 3, 2, 1, 2, 2],
    [1, -1, -5, 1, -4, 2, 2, 2, -1, 0, -3, 3, -2, -1, 1, -4, -3, -2, 2, 3, -5, 3, 0, 1, 0, 3, 3, 1, 0, 1, -1, -3],
    [-3, -3, 0, 5, 0, -1, -3, -2, 3, -4, 0, -2, 0, -1, 0, 0, 3, -1, 2, 1, 4, 0, 1, 4, 1, 0, 1, -1, 3, -2, -5, 1],
    [0, -1, -2, 0, -3, 0, 2, -2, 1, -1, 1, 1, -7, 1, 1, 0, -1, 2, 1, 3, 0, 2, -5, -3, 0, 3, 0, 0, 0, -6, -1, 3],
    [-4, 0, -4, -4, 2, 1, 3, 0, 0, 2, 3, 0, 0, 1, -1, 2, 0, 2, 1, 1, 2, -3, 1, -1, -6, -3, 0, 0, -1, 0, 1, 0],
    [-1, -1, 1, -3, -1, -2, 1, 1, 1, 4, -4, -1, -1, 0, 0, -2, 0, -3, -4, 0, -1, 5, -2, -1, -3, 1, 1, 2, 3, 0, 3, 1],
    [-1, 0, 1, 0, 0, 5, -1, 1, -1, -1, -3, 2, -2, 1, -1, 3, 2, 2, 2, 0, 4, -2, -1, -3, -2, 1, 0, 0, -4, 0, 4, -2],
    [0, 5, 0, -5, 0, -4, -3, 1, 2, 1, 4, -1, 3, 0, -2, -3, -2, -2, -3, 2, -1, -3, 1, -1, -1, 3, -4, -2, 1, 1, 1, 4],
    [3, -1, 0, 2, -1, 0, 1, 0, 3, -1, 0, -1, 0, 3, 3, -1, -1, -1, 0, 4, -3, 4, 0, -2, 3, 3, 1, 5, 4, 0, -1, 0],
    [2, -4, -3, 1, -1, 5, -4, -1, 2, 0, 2, 1, -3, -5, -4, 2, 0, 1, 0, -1, 5, 0, -1, 2, 1, -1, -3, 0, -2, -3, 2, -1],
    [-2, -6, -3, -2, -2, -1, -1, 1, 4, 2, -2, -2, 2, -1, -2, -4, -1, 0, 1, 4, 3, 0, 1, 2, 1, -1, 4, -2, 2, -3, -1, 1],
    [2, 2, 3, 0, -1, 0, -1, -2, -3, -5, 4, 3, 1, 1, -3, 0, -3, 1, -2, 1, 2, 4, 1, 1, 0, 1, 0, -1, -2, -2, -2, 2],
    [2, 3, -1, 0, -1, 3, 2, 4, 0, -3, 0, -2, 4, 0, -1, 2, -2, -3, -3, -3, -1, 0, 1, 0, -5, 3, -4, -2, -1, -1, 1, -3],
    [-4, -1, 3, -2, 5, -1, 1, 0, 2, 0, 0, -1, -3, 1, -3, 7, 2, 4, 2, 2, 6, 3, -3, 0, -1, 0, 2, 0, 1, -1, 1, -3],
]

# ----------------------------------------------------------------- lattice ---
def gso(B):
    n = len(B)
    Bs, mu = [], [[Fraction(0)] * n for _ in range(n)]
    for i in range(n):
        v = [Fraction(x) for x in B[i]]
        for j in range(i):
            d = sum(a * b for a, b in zip(Bs[j], Bs[j]))
            mu[i][j] = sum(Fraction(a) * b for a, b in zip(B[i], Bs[j])) / d
            v = [a - mu[i][j] * b for a, b in zip(v, Bs[j])]
        Bs.append(v)
    return Bs


def babai(B, Bs, t):
    """nearest-plane: lattice vector close to target t"""
    b = [Fraction(x) for x in t]
    res = [0] * len(t)
    for i in reversed(range(len(B))):
        d = sum(x * x for x in Bs[i])
        c = round(sum(x * y for x, y in zip(b, Bs[i])) / d)
        if c:
            b = [x - c * y for x, y in zip(b, B[i])]
            res = [x + c * y for x, y in zip(res, B[i])]
    return res


def ok(c, v):
    return any(v) and all(LO <= a + b <= HI for a, b in zip(c, v))


def find_collision(chal: bytes) -> bytes:
    c = list(chal)
    B = BASIS
    Bs = gso(B)
    mid = (LO + HI) / 2
    rng = random.Random(1)
    for it in range(20000):
        # aim for a random point inside the allowed box
        tgt = [Fraction(rng.uniform(LO + 8, HI - 8)) - a if it else Fraction(mid) - a
               for a in c]
        v = babai(B, Bs, tgt)
        if not any(v):
            v = list(B[rng.randrange(len(B))])
        if ok(c, v):
            return bytes(a + b for a, b in zip(c, v))
        # local search: add/subtract single basis vectors
        for r in B:
            for s in (1, -1):
                w = [a + s * b for a, b in zip(v, r)]
                if ok(c, w):
                    return bytes(a + b for a, b in zip(c, w))
    raise RuntimeError("no collision found")


# ------------------------------------------------------------------ remote ---
def recvuntil(s, tok):
    buf = b""
    while tok not in buf:
        d = s.recv(4096)
        if not d:
            break
        buf += d
    return buf


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--test":
        m = find_collision(sys.argv[2].encode())
        print(m.decode())
        return
    host = sys.argv[1] if len(sys.argv) > 1 else "challs.glacierctf.com"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 13378
    s = socket.create_connection((host, port))
    data = recvuntil(s, b"> ").decode()
    print(data, end="")
    chal = data.split("Here is your challenge: ")[1].split()[0].encode()
    msg = find_collision(chal)
    print(msg.decode())
    s.sendall(msg + b"\n")
    s.settimeout(300)
    out = b""
    try:
        while True:
            d = s.recv(4096)
            if not d:
                break
            out += d
            print(d.decode(errors="replace"), end="", flush=True)
    except socket.timeout:
        pass


if __name__ == "__main__":
    main()
