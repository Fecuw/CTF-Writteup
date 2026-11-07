from Crypto.Util.number import getPrime, isPrime
from Crypto.Util.number import bytes_to_long

flag = b"katagaitai-CTF{****************}"
m = bytes_to_long(flag)

def next_prime(n):
    while True:
        n += 1
        if isPrime(n):
            return n

bit_length = 1024
p = getPrime(bit_length)
q = next_prime(p)
N = p*q
e = 0x10001
c = pow(m,e,N)

print("N =", N)
print("e =", e)
print("c =", c)
