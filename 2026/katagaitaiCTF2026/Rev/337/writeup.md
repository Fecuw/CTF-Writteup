# Writeup
We get the encryption binary `chal` and the ciphertext `encrypted_20260726.txt`. We don't have the key, so we have to recover the flag somehow.

First I read `chal`. The flow of `main` is roughly like this.

```
strlen(input)
time()                      <- used as the seed
key_generator(key, len, time)
enc(input, key, out)
write_hex_file("encrypted_%Y%m%d.txt", out, len, time)
write_hex_file("key_%Y%m%d.txt",       key, len, time)
```

`enc` is just a XOR.

```
out[i] = input[i] ^ key[i]
```

`key_generator` is the real logic. It takes a fixed 16-byte string and XORs it again with `rand()` after `srand(time)`.

```
const = "9f2341d86a0cb755"   // embedded as movabs immediates
srand(seed);                 // seed = time()  <- 3rd argument
for i in range(len):
    r = rand() & 0xff
    key[i] = const[i % 16] ^ r
```

So in the end:

```
ct[i] = pt[i] ^ const[i%16] ^ rand_i
```

The key depends only on the `time()` seed. And the file name is `encrypted_20260726.txt`, which means it was encrypted on 2026-07-26. So we can just brute force the seconds of that day (86400 patterns) to find the seed.

I reproduce glibc's `rand()` and spin it for one day. On mac there is no `libc.so.6`, so I implemented glibc's PRNG in Python.

```python
import datetime
ct = bytes.fromhex("bc2f31d85aec8626388074084492e073369263944656d4209ca91e8a3d00c95cc6d5e6b8fb704757b1")
const = b"9f2341d86a0cb755"
n = len(ct)

def glibc_rand_seq(seed, cnt):
    r = [0]*(344+cnt)
    r[0] = seed & 0xffffffff
    for i in range(1, 31):
        r[i] = (16807*r[i-1]) % 2147483647
    for i in range(31, 34):
        r[i] = r[i-31] & 0xffffffff
    for i in range(34, 344+cnt):
        r[i] = (r[i-31] + r[i-3]) & 0xffffffff
    return [r[i] >> 1 for i in range(344, 344+cnt)]

start = int(datetime.datetime(2026,7,24,tzinfo=datetime.timezone.utc).timestamp())
end   = int(datetime.datetime(2026,7,28,tzinfo=datetime.timezone.utc).timestamp())
for seed in range(start, end):
    seq = glibc_rand_seq(seed, n)
    out = bytes(ct[i] ^ const[i%16] ^ (seq[i] & 0xff) for i in range(n))
    if out.startswith(b"katagaitai"):
        print(seed, out.decode()); break
```

It hits at seed=1785071507 (2026-07-26 13:11:47).
Classic "don't use a predictable seed" lesson challenge.

# flag
```
katagaitai-CTF{d0nT-uS3-pR3D1Ct4bL3-s33D}
```
