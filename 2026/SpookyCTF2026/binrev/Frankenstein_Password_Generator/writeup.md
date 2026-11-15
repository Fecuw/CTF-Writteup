# Writeup
"A bolt at midnight gave it life." The binary is a password generator that needs an activation phrase before it starts.

Opening `frankenstein` in Ghidra, the check function compares our input (after a transform) against a hardcoded string:

```
expected = "*$*)C7EP\]erto"   // 14 bytes
```

The transform for each byte is:

```
(7*i + (password[i] ^ 0x5d) + 11) & 0xff == expected[i]
```

So to recover the password we just invert it:

```python
expected = b"*$*)C7EP\\]erto"
password = bytes((((v - 7*i - 11) & 0xff) ^ 0x5d) for i, v in enumerate(expected))
print(password)   # -> b'BOLTATMIDNIGHT'
```

Password is `BOLTATMIDNIGHT`, which matches the notebook hint perfectly.

The binary is a Linux x86-64 ELF, so on mac I just run it through Docker and feed the password:

```bash
docker run --rm --platform linux/amd64 -v "$PWD:/work" -w /work ubuntu:24.04 \
  bash -c "printf 'BOLTATMIDNIGHT\n' | ./frankenstein"
```

Output:

```
FRANKENSTEIN'S PASSWORD GENERATOR v1.0
...
Activation phrase: The laboratory lights flicker. IT'S ALIVE!
The creature whispers: spooky{its_alive_at_midnight}
```

# flag
```
spooky{its_alive_at_midnight}
```
