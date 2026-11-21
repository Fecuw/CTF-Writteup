#!/usr/bin/env sage -python
"""Cold Echo solver.  Run:  sage -python solver.py [archive.json]"""
import sys, json, base64, hashlib
from sage.all import GF, PolynomialRing, matrix, vector, EllipticCurve, Integer, prod

A = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "archive.json"))
p, d = A["prime"], A["degree"]
F = GF(p)
R = PolynomialRing(F, "x")
x = R.gen()
t0, fwd = A["forward"]

# 1. Q(x) = x^d P(x) P(1/x) is palindromic of degree 2d -> d+1 unknowns.
#    Trace gives Q(u) = reading * u^d (d points), and Q(1) = P(1)^2 = 1.
def row(v):
    v = F(v)
    return [v**i + v**(2 * d - i) for i in range(d)] + [v**d]

rows = [row(u) for u, _ in A["trace"]] + [row(1)]
rhs = [F(r) * F(u)**d for u, r in A["trace"]] + [F(1)]
q = matrix(F, rows).solve_right(vector(F, rhs))
Q = R(list(q) + [q[d - 1 - j] for j in range(d)])
assert Q.degree() == 2 * d

# 2. Roots of Q come in reciprocal pairs {r, 1/r}; P takes one from each.
roots = [r for r, e in Q.roots() for _ in range(e)]
assert len(roots) == 2 * d, "Q does not split; general case not handled"
pairs, used = [], set()
for r in roots:
    if r in used:
        continue
    s = 1 / r
    used.update([r, s])
    pairs.append((r, s))
assert len(pairs) == d

# 3. With P(1)=1:  P(t) = prod (t - s_i)/(1 - s_i).  Choosing s_i = 1/r_i instead
#    of r_i multiplies P(t) by w_i.  Need prod_{i in S} w_i = P(t)/base.
f = lambda s: (F(t0) - s) / (1 - s)
base = prod(f(a) for a, _ in pairs)
w = [f(b) / f(a) for a, b in pairs]
target = F(fwd) / base

g = F.multiplicative_generator()
n = p - 1
lw = [int(wi.log(g)) for wi in w]          # p-1 is smooth -> fast DLP
lt = int(target.log(g))

# 4. Meet-in-the-middle subset sum mod n.
h = d // 2
def sums(ls):
    out = {0: [0]}
    for k, v in enumerate(ls):
        new = {}
        for sm, masks in out.items():
            for key, add in ((sm, 0), ((sm + v) % n, 1 << k)):
                new.setdefault(key, []).extend(m | add for m in masks)
        out = new
    return out

L = sums(lw[:h])
Rs = sums(lw[h:])
sols = []
for sm, masks in Rs.items():
    for lm in L.get((lt - sm) % n, []):
        for rm in masks:
            sols.append(lm | (rm << h))
print(f"[+] {len(sols)} candidate root selections satisfy P({t0})")

# 5. ECDSA P-256 / SHA-256 verify, done by hand in Sage.
pq = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
E = EllipticCurve(GF(pq), [-3, 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b])
G = E(0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296,
      0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5)
N = G.order()
der = base64.b64decode("".join(A["public_key_pem"].strip().splitlines()[1:-1]))
pub = E(int.from_bytes(der[-64:-32], "big"), int.from_bytes(der[-32:], "big"))
sig = base64.b64decode(A["receipt_der_b64"])
i = 2
rl = sig[i + 1]; r_sig = int.from_bytes(sig[i + 2:i + 2 + rl], "big"); i += 2 + rl
sl = sig[i + 1]; s_sig = int.from_bytes(sig[i + 2:i + 2 + sl], "big")

def verify(msg):
    e = int.from_bytes(hashlib.sha256(msg).digest(), "big")
    si = Integer(s_sig).inverse_mod(N)
    X = (e * si % N) * G + (r_sig * si % N) * pub
    return not X.is_zero() and int(X[0]) % N == r_sig

head = ["GLACIER-COLD-ECHO-v1", A["batch"], f"{p} {d}"]
head += [f"{u} {r}" for u, r in A["trace"]] + [f"{t0} {fwd}"]

for mask in sols:
    P = prod(x - (b if mask >> k & 1 else a) for k, (a, b) in enumerate(pairs))
    P = P / P(1)
    assert P(t0) == fwd
    coeffs = [int(c) for c in P.list()]
    msg = ("\n".join(head + [" ".join(map(str, coeffs))]) + "\n").encode()
    if verify(msg):
        mask_b = base64.b64decode(A["flag_mask_b64"])
        pad = hashlib.sha256(b"cold-echo-flag-pad-v1\n" + msg).digest()
        body = bytes(a ^ b for a, b in zip(mask_b, pad))
        print("[+] P coefficients:", coeffs)
        print("gctf{" + base64.urlsafe_b64encode(body).rstrip(b"=").decode() + "}")
        break
else:
    print("[-] no candidate verified")
