
#!/usr/bin/env python3
from pwn import *
from math import gcd
from Crypto.Util.number import long_to_bytes
import gmpy2
import re

HOST = "crypto.katagaitai-ctf.net"
PORT = 9012

context.log_level = "info"

def extract(name, data):
    pattern = rb"\b" + name.encode() + rb"\s*=\s*(\d+)"
    match = re.search(pattern, data)
    if not match:
        raise ValueError(f"{name} not found")
    return int(match.group(1))

def egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x, y = egcd(b, a % b)
    return g, y, x - (a // b) * y

def modpow_signed(a, e, n):
    if e < 0:
        return pow(pow(a, -1, n), -e, n)
    return pow(a, e, n)

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

    # Recover m^gcd(ea, eb) mod n
    g, x, y = egcd(ea, eb)
    log.info(f"gcd = {g}")

    mg = (
        modpow_signed(ca, x, n)
        * modpow_signed(cb, y, n)
    ) % n

    # Since m^3 < n, recover exact integer cube root
    assert g == 3
    m, exact = gmpy2.iroot(mg, g)

    if not exact:
        raise ValueError("Cube root is not exact")

    m = int(m)

    # Verify both ciphertexts
    assert pow(m, ea, n) == ca
    assert pow(m, eb, n) == cb

    secret = long_to_bytes(m, 32)
    log.success(f"Recovered secret: {secret.hex()}")

    io.sendline(b"3")
    io.recvuntil("機密情報（16進数）>".encode())
    io.sendline(secret.hex().encode())

    result = io.recvall(timeout=5)
    print(result.decode(errors="replace"))

    io.close()

if __name__ == "__main__":
    main()

