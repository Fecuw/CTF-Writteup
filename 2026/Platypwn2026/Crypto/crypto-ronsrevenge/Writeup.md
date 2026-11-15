# Ron's Revenge - Writeup

## Overview

This was a crypto challenge using a modified version of RC4. At first I thought the unusual state size might be the main problem, but the useful part was actually the weak IVs. We can choose IVs and get ciphertexts from the server, so I tried an FMS-style attack to recover the secret key one element at a time.

The final flag was:

```text
PP{st4t3s1z3_w4s_n0t_th3_m41n_pr0bl3m::n8sh76rXJZiG}
```

## Looking at the cipher

In the provided solver, the RC4 state has **2048 entries**, not the usual 256. Each PRGA output is therefore an 11-bit number, and the outputs are packed into bytes before XORing with the plaintext.

The long-term key has eight elements. The full KSA key is the three-element IV followed by these eight secret elements.

```python
N = 2048
KEYLEN = 8
PREFIX = b'PP{'
```

We know that the flag starts with `PP{`. This gives us the first 24 bits of keystream from the first three ciphertext bytes:

```python
raw = int.from_bytes(
    bytes(a ^ b for a, b in zip(ct[:3], b'PP{')),
    'big'
)
z1 = raw >> 13
```

So we can recover the first 11-bit output `z1` without knowing the rest of the plaintext.

## Trying weak IVs

I used a generalized FMS-style idea. For the secret key element at position `k`, I set:

```python
i = 3 + k
iv = (i, 2047, x)
```

Here `x` changes from 0 to 2047. For every IV, the server returns a ciphertext. We use the known `PP{` prefix to recover `z1`, and simulate the first `i` steps of the RC4 key scheduling algorithm with the IV and the secret elements already recovered.

The guess for the next secret element is:

```python
guess = (inverse_s[z1] - j - s[i]) % 2048
```

This is a statistical guess, not something that works for every ciphertext. So I counted how often each candidate appeared. The correct candidate should get noticeably more votes than the random ones.

I used **2048 samples per key element** and selected the most common candidate. I also cached the ciphertexts in a JSON file, because asking the server again for the same IV would be a waste of time. There were a few connection timeouts, but retrying the query worked.

## Recovering the key

The voting results were pretty clear. For example, the first candidate got 130 votes, while the next candidates only got around 5. The same pattern appeared for the other positions.

| Position | Recovered value | Votes |
| --- | ---: | ---: |
| `key[0]` | 1375 | 130 |
| `key[1]` | 1120 | 98 |
| `key[2]` | 1003 | 87 |
| `key[3]` | 1739 | 105 |
| `key[4]` | 921 | 111 |
| `key[5]` | 507 | 105 |
| `key[6]` | 436 | 112 |
| `key[7]` | 162 | 104 |

So the recovered long-term key was:

```python
key = [1375, 1120, 1003, 1739, 921, 507, 436, 162]
```

## Checking the result

I didn't want to trust the votes alone. After recovering all eight values, the solver runs the modified RC4 algorithm locally and decrypts ciphertexts from several different IVs.

```python
stream = rc4_bytes(list(iv) + key, len(ct))
plaintext = bytes(a ^ b for a, b in zip(ct, stream))
```

The checks make sure that the plaintext starts with `PP{` and that different IVs decrypt to the same message. This is important because a candidate with the highest number of votes is still only a guess until it is verified.

The solver printed:

```text
[+] Candidate long-term key: [1375, 1120, 1003, 1739, 921, 507, 436, 162]
[SUCCESS] FLAG: PP{st4t3s1z3_w4s_n0t_th3_m41n_pr0bl3m::n8sh76rXJZiG}
```

## Flag

```text
PP{st4t3s1z3_w4s_n0t_th3_m41n_pr0bl3m::n8sh76rXJZiG}
```

## Conclusion

The state size was different from normal RC4, but that didn't fix the weak-IV problem. By choosing IVs and using only the known `PP{` prefix, I could recover the key elements through voting.

Basically, the unusual 2048-state RC4 made the implementation look different, but the same kind of key scheduling weakness was still useful. This was a nice reminder that changing parameters does not automatically make a cipher secure.
