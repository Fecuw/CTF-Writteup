# Writeup
問題文を見る
![alt](./img/スクリーンショット%202026-11-07%2010.25.21.png)

```
marked with a 13 on the wall
```


もしかしてROT13?

```
missing and marked
```
足し引きしろとか？

```
dyslexia I think.
```
逆にしろって感じか？

書いてみる
```bash
╭─ /Users/mionorn124/Desktop/CTF-Writteup/SpookyCTF2026/Crypto/Numerophobia(pwn)
╰─ (*'-') < cat solver.py
#!/usr/bin/env python3

s = """
23 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 50 65 10 138 50 65 95 123 51 64 98 108 53 134 52 132 108 65 95 66 52 117 95 127 51 132 53 123 52 108 51 117 116 136 121 120 111 124 112 128 10 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52 63 52
"""

nums = list(map(int, s.split()))

decoded_nums = [
    n - 13 if i % 2 == 0 else n
    for i, n in enumerate(nums)
]

decoded = ''.join(chr(n) for n in decoded_nums)

reversed_text = decoded[::-1]

print("=== add/sub num ===")
print(decoded_nums)

print("\n=== to ASCII ===")
print(decoded)

print("\n=== reverse ===")
print(reversed_text)
╭─ /Users/mionorn124/Desktop/CTF-Writteup/SpookyCTF2026/Crypto/Numerophobia(pwn)
╰─ (*'-') < python3 solver.py
=== add/sub num ===
[10, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 10, 125, 50, 52, 95, 110, 51, 51, 98, 95, 53, 121, 52, 119, 108, 52, 95, 53, 52, 104, 95, 114, 51, 119, 53, 110, 52, 95, 51, 104, 116, 123, 121, 107, 111, 111, 112, 115, 10, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52, 50, 52]

=== to ASCII ===

24242424242424242424242424242424242424
}24_n33b_5y4wl4_54h_r3w5n4_3ht{ykoops
24242424242424242424242424242424242424

=== reverse ===
42424242424242424242424242424242424242
spooky{th3_4n5w3r_h45_4lw4y5_b33n_42}
42424242424242424242424242424242424242

╭─ /Users/mionorn124/Desktop/CTF-Writteup/SpookyCTF2026/Crypto/Numerophobia(pwn)
╰─ (*'-') < 

```

あってた
# flag
```
{th3_4n5w3r_h45_4lw4y5_b33n_42}
```