
#!/usr/bin/env python3
from pwn import *
import re

HOST = "crypto.katagaitai-ctf.net"
PORT = 9011

def extract(name, data):
    pattern = rb"\b" + name.encode() + rb"\s*=\s*(\d+)"
    match = re.search(pattern, data)
    if not match:
        raise ValueError(f"{name} not found")
    return int(match.group(1))

def main():
    io = remote(HOST, PORT)

    data = io.recvuntil(b"choice> ")
    n = extract("n", data)
    ea = extract("e_a", data)
    eb = extract("e_b", data)

    log.info(f"n = {n}")
    log.info(f"e_a = {ea}")
    log.info(f"e_b = {eb}")

    io.sendline(b"1")
    data = io.recvuntil(b"choice> ")
    ca = extract("ciphertext_a", data)

    io.sendline(b"2")
    data = io.recvuntil(b"choice> ")
    cb = extract("ciphertext_b", data)

    # Extended Euclidean algorithm
    from math import gcd
    assert gcd(ea, eb) == 1

    def egcd(a, b):
        if b == 0:
            return (a, 1, 0)
        g, x, y = egcd(b, a % b)
        return (g, y, x - (a // b) * y)

    _, x, y = egcd(ea, eb)

    def signed_pow(c, exponent, n):
        if exponent < 0:
            return pow(pow(c, -1, n), -exponent, n)
        return pow(c, exponent, n)

    m = (
        signed_pow(ca, x, n)
        * signed_pow(cb, y, n)
    ) % n

    log.success(f"Recovered secret: {m:064x}")

    io.sendline(b"3")
    io.recvuntil("機密情報（16進数）>".encode())
    io.sendline(format(m, "x").encode())

    result = io.recvall(timeout=5)
    print(result.decode(errors="replace"))

    io.close()

if __name__ == "__main__":
    main()

