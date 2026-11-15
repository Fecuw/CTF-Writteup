#!/usr/bin/env python3
"""RSA accumulator membership forgery for the provided CTF service."""
import re
from math import prod
from pwn import remote, context
from sympy import factorint, isprime

HOST = 'crypto.katagaitai-ctf.net'
PORT = 9013
context.log_level = 'info'


def extract_int(data, name):
    match = re.search(rb'(?m)^' + re.escape(name.encode()) + rb'\s*=\s*(\d+)\s*$', data)
    if not match:
        raise ValueError(f'Missing {name} in server banner: {data[-1500:]!r}')
    return int(match.group(1))


def main():
    io = remote(HOST, PORT)
    try:
        banner = io.recvuntil(b'choice> ', timeout=30)
        n = extract_int(banner, 'n')
        initial = extract_int(banner, 'initial_accumulator')
        admin = extract_int(banner, 'administrator_representative')

        factorization = factorint(admin)
        primes = list(factorization.keys())
        print(f'[+] admin representative: {admin}')
        print(f'[+] factors: {factorization}')
        if len(primes) != 3 or any(e != 1 for e in factorization.values()):
            raise ValueError('Unexpected administrator representative factorization')
        if any(not isprime(p) or not 1 < p < (1 << 20) for p in primes):
            raise ValueError('One or more factors cannot be registered')
        assert prod(primes) == admin

        accumulator = initial
        for p in primes:
            io.sendline(b'1')
            io.recvuntil('登録する代表値>'.encode(), timeout=10)
            io.sendline(str(p).encode())
            response = io.recvuntil(b'choice> ', timeout=10)
            if '一時資格を登録しました'.encode() not in response:
                raise RuntimeError(f'Registration failed for {p}: {response!r}')
            accumulator = pow(accumulator, p, n)
            print(f'[+] Registered prime {p}')

        witness = initial
        assert pow(witness, admin, n) == accumulator
        print('[+] Verified forged witness locally')
        io.sendline(b'4')
        io.recvuntil('管理者のmembership witness>'.encode(), timeout=10)
        io.sendline(str(witness).encode())
        result = io.recvall(timeout=15)
        print(result.decode('utf-8', errors='replace'))
    finally:
        io.close()


if __name__ == '__main__':
    main()
