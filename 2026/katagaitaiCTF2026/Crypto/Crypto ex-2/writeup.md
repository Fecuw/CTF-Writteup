# Writeup
pqが近いのでフェルマー法が使える
```python
from math import isqrt
from Crypto.Util.number import long_to_bytes

v = dict(line.strip().split(" = ") for line in open("output.txt"))
N, e, c = (int(v[k]) for k in ("N", "e", "c"))

a = isqrt(N)
if a*a < N:
    a += 1

while True:
    b = isqrt(a*a - N)
    if b*b == a*a - N:
        break
    a += 1

p, q = a+b, a-b
d = pow(e, -1, (p-1)*(q-1))
print(long_to_bytes(pow(c, d, N)).decode())
```
# flag
```
katagaitai-CTF{f3rm47s_f4c70r1z4710n_m37h0d}
```