# Writeup
"main function not found!!" is the whole vibe. The binary is stripped, so IDA/objdump won't give us a nice `main` symbol.

But `main` isn't actually gone. In `_start`, the pointer passed to `__libc_start_main` is the real main. Just check what `_start` loads into `rdi`:

```
10f8:   lea rdi, [rip+0x2d7]   # 0x13d6   <- this is main
```

So the real main is the function at `0x13d6`. Inside it, the flag is built on the stack from a bunch of `movabs` immediates, then it reads our input, transforms it, and `strcmp`s it against the built string.

The stored constant (little-endian from the immediates) is:

```
xngntnvgnv-PGS{z74a_3s_80e4cc6q_o74a7el_48_678l_03_s4aq}
```

Looks like ROT13-ish garbage. The transform at `0x11c9` is applied to the *input* before compare:

- digits `0-9`: `+3 mod 10`
- letters: ROT13
- other chars: unchanged

So `transform(flag) == stored`, which means `flag = inverse_transform(stored)`: ROT13 is its own inverse for letters, and digits need `-3 mod 10`.

```python
import struct
consts=[0x67766e746e676e78,0x7a7b5347502d766e,0x385f73335f613437,
        0x5f71366363346530,0x5f6c65376134376f,0x5f6c3837365f3834,
        0x7d716134735f3330]
S=b"".join(struct.pack("<Q",c) for c in consts).split(b"\x00")[0]

def inv(c):
    c=chr(c)
    if c.isdigit(): return chr((int(c)-3)%10+ord('0'))
    if 'a'<=c<='z': return chr((ord(c)-97-13)%26+97)
    if 'A'<=c<='Z': return chr((ord(c)-65-13)%26+65)
    return c
print("".join(inv(b) for b in S))
```

Output:

```
katagaitai-CTF{m41n_0f_57r1pp3d_b41n4ry_15_345y_70_f1nd}
```

The flag literally says it: finding the main of a stripped binary is easy (just look at `_start`).

# flag
```
katagaitai-CTF{m41n_0f_57r1pp3d_b41n4ry_15_345y_70_f1nd}
```
