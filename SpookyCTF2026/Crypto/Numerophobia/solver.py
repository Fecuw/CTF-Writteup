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
