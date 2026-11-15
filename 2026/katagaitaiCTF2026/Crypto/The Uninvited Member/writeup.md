# Writeup

```python
factorization = factorint(admin)
primes = list(factorization.keys())
```
この部分から初期値 \(g\) をそのまま管理者のmembership witnessとして提出できてしまう脆弱性がある \
そのため、 \(g\)を素因数分解して再登録するだけで管理者のwitnessを偽造してflagを入手可能である

```bash
╭─ /Users/mionorn124/Desktop/katagaitaiCTF2026/Crypto/The Uninvited Member(pwn)
╰─ (*'-') < python3 solve_accumulator.py 
[+] Opening connection to crypto.katagaitai-ctf.net on port 9013: Done
[+] admin representative: 307056538685619557
[+] factors: {550441: 1, 1035427: 1, 538751: 1}
[+] Registered prime 550441
[+] Registered prime 1035427
[+] Registered prime 538751
[+] Verified forged witness locally
[+] Receiving all data: Done (115B)
[*] Closed connection to crypto.katagaitai-ctf.net port 9013
 管理者の所属証明を確認しました。
FLAG: katagaitai-CTF{composite_representatives_break_membership}
```

# flag
```
katagaitai-CTF{composite_representatives_break_membership}
```