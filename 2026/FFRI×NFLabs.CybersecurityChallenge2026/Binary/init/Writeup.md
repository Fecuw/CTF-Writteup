# Writeup

## Overview
`init` reads a name and a favorite number, then calls `check()`. `check()` builds a local `struct Data` and only calls `print_flag()` when `foxtrot[1]` passes a weird condition. The title says it all: "don't forget to initialize data" — this is an **uninitialized stack variable** bug.

## Vuln
Look at `check()`:

```c
data.foxtrot[0] = 0xab;
if (input_num <= 100) {
    data.foxtrot[1] = 0x00;     // only set when input_num <= 100
}
data.foxtrot[2] = 0xcd;
data.foxtrot[3] = 0xef;

if (((data.foxtrot[1] & 0xfc) == 0xc8) && (data.foxtrot[1] != 0xc8)) {
    print_flag();
}
```

`foxtrot[1]` is **only initialized when `input_num <= 100`**. If we send a favorite number `> 100`, `foxtrot[1]` is never written and keeps whatever garbage is already on the stack.

The condition we need:
- `(foxtrot[1] & 0xfc) == 0xc8` and `foxtrot[1] != 0xc8`
- → `foxtrot[1]` must be one of `0xc9`, `0xca`, `0xcb`

So we need to control that uninitialized byte. `main()` calls `input()` then `check()` at the same call depth, so `input()`'s local `name[8]` buffer sits on the same stack region that `check()`'s `struct Data` later reuses. Whatever bytes we leave in `name` are still there as "garbage" when `foxtrot[1]` is read.

## Exploit
1. In `input()`, send a `name` whose byte that lands on `foxtrot[1]`'s slot is `0xc9` (any of `0xc9/0xca/0xcb`). `scanf("%7s")` happily takes raw non-whitespace bytes, and `0xc9` is fine.
2. Send a favorite number `> 100` so `foxtrot[1]` is left uninitialized (= our planted byte).

```python
from pwn import *
io = remote(HOST, PORT)
io.sendlineafter(b"Input your name: ", b"\xc9"*7)   # fill name with 0xc9
io.sendlineafter(b"Input your favorite number: ", b"200")  # > 100
io.interactive()
```

There are only 7 byte positions in `name`, so if filling it entirely doesn't work you can just test each position until `foxtrot[1]` lines up. Once it matches, `print_flag()` fires.

## flag
```
flag{D0_n0t_f0rg3t_1n1t1@l1z3_d@t@}
```
