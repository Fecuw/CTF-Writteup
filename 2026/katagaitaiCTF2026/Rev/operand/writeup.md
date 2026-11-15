# Writeup
The challenge says "it's a program that shouldn't work, but it works...".
Disassembling `operand`, you can see `main` building the flag string and XORing it.

The point is here: it puts immediates into registers 8 bytes at a time with four `movabs`, then adds 2 more bytes with a 16-bit `mov`. That is the encrypted flag. Decryption is just XORing each byte with `0xAA` inside `xor()`. The immediates sit in the file in the same byte order, so we can just pull them out from those offsets and `^ 0xAA` to get it back.

```python
constants = (
    (0x1254, b"\x48\xb8", 8),  # movabs rax, imm64
    (0x125E, b"\x48\xba", 8),  # movabs rdx, imm64
    (0x1270, b"\x48\xb8", 8),
    (0x127A, b"\x48\xba", 8),
    (0x128C, b"\x66\xc7\x45\xa0", 2),  # mov word [rbp-0x60], imm16
)
data = open("operand","rb").read()
enc = bytearray()
for off, opcode, size in constants:
    s = off + len(opcode)
    enc += data[s:s+size]
print(bytes(b ^ 0xAA for b in enc).decode())
```

Running it decrypts the flag (the bundled `solver.py` does the same).

```bash
╰─ (*'-') < python3 solver.py operand
katagaitai-CTF{0p3rand_15_xmm3_Qa}
```

Just like the title, you grab the operand (the immediates) and strip the XOR.

# flag
```
katagaitai-CTF{0p3rand_15_xmm3_Qa}
```
