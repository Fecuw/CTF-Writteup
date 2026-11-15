#!/usr/bin/env python3

# Ghidraで確認した比較文字列
expected = b"*$*)C7EP\\]erto"

# 検証関数 FUN_00401176 の逆演算
password = bytes(
    (((value - 7 * i - 11) & 0xff) ^ 0x5d)
    for i, value in enumerate(expected)
)

print("[+] Length:", len(password))
print("[+] Password (raw):", repr(password))
print("[+] Password (hex):", password.hex())
print("[+] Password (text):", password.decode("ascii", errors="replace"))

# 元の検証関数と一致するか確認
assert len(password) == 14
assert all(
    ((7 * i + (password[i] ^ 0x5d) + 11) & 0xff)
    == expected[i]
    for i in range(14)
)

print("[+] Verification passed")

# 入力ファイルに保存
with open("solution.bin", "wb") as f:
    f.write(password + b"\n")

print("[+] Saved: solution.bin")

