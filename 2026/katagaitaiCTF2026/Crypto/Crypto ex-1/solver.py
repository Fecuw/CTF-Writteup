from math import isqrt
from Crypto.Util.number import long_to_bytes

v = dict(map(lambda x: (x[0].strip(), int(x[1])), (line.split("=") for line in open("output.txt"))))

N, e, c, s = (v[k] for k in ("N", "e", "c", "p_plus_q"))
t = isqrt(s*s - 4*N)
p, q = (s+t)//2, (s-t)//2
d = pow(e, -1, (p-1)*(q-1))
print(long_to_bytes(pow(c, d, N)).decode())
