from Crypto.Util.number import getPrime
from Crypto.Util.number import bytes_to_long

flag = b"katagaitai-CTF{****************}"
m = bytes_to_long(flag)

bit_length = 1024
p = getPrime(bit_length)
q = getPrime(bit_length)
N = p*q
e = 0x10001
c = pow(m,e,N)
p_plus_q = p+q
print("N =", N)
print("e =", e)
print("c =", c)
print("p_plus_q =", p_plus_q)