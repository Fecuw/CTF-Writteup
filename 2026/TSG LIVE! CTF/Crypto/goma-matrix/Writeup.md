# Goma Matrix !?

N, e = 65537 とかいういつものRSAかと思ったら、平文が行列に埋め込まれてる

```python
M = [[m, 1], [0, m]]
C = mat_modpow(M, e, N)
```

N は 2048 bit だし素因数分解は無理そう

これ mの対角行列 + [[0, 1], [0, 0]] に分けられるんじゃね
ジョルダンのなんとかで二乗すると0

```
M^e = m^e·I + e·m^(e-1)·J
    = [[m^e, e·m^(e-1)], [0, m^e]]
```

C[0][0] = m^e と C[0][1] = e·m^(e-1) が両方見えてるので、割ったら m/e が出てくる

```
m = e · C[0][0] · C[0][1]^(-1)  (mod N)
```

gcd(m, N) = 1 と gcd(e, N) = 1 は assert されてるから逆元は取れる

貼った数値の末尾に `JS:Infinity` とかいうゴミが付いててガバ 消してから計算した

```python
N = ...
e = 65537
C00 = ...
C01 = ...

m = e * C00 * pow(C01, -1, N) % N
assert pow(m, e, N) == C00
print(m.to_bytes((m.bit_length() + 7) // 8, 'big'))
```

```bash
b'TSGLIVE{1_n071c3d_7h47_j0rd4n_n0rm4l_f0rm_15_4l50_g0m4m4y0_d30500b050bdb4f2}'
```

# flag
```
TSGLIVE{1_n071c3d_7h47_j0rd4n_n0rm4l_f0rm_15_4l50_g0m4m4y0_d30500b050bdb4f2}
```
