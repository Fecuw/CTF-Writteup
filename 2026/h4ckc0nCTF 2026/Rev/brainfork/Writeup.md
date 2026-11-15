# Writeup — Esolang / Weird Code

## Challenge

> This code seems to be asking for some kind of flag. . .
>
> `nc 0.cloud.chals.io 31389`
>
> Flag format: `d4rk{...}c0de` (yes, this has a different format)

We were given a very long piece of strange-looking code (`output(1).txt`). At first I thought it might be a Brainfuck variant.

## Looking at the code

The code uses a lot of repeated patterns like:

```text
[}71][v0][^21b][}1][v0][^1a9]
[{91][v0][^7]
[{94][v0]~[{1]%~
```

It doesn't look like normal Brainfuck (`><+-.,[]`). It seems to be a custom esoteric language with a memory pointer and hexadecimal operands.

The provided output also includes `MEMORY DUMP`, `Pointer : 0`, and `Code Successful`, which suggested that the program had already been executed and we were looking at its memory state.

## Testing the interpreter

I also tested a code-input service at `h4ckc0n.centralindia.cloudapp.azure.com:31337` to get a better idea of the syntax. This is **not the same address as the challenge endpoint**, so these tests were only a hint about how the language might work.

Some results:

| Input | Result |
| --- | --- |
| `1` | `Code Successful` |
| `+`, `-`, `.` | `Its not that deep` |
| `[v41]` | `Code Successful` |
| `[v41]i` | Memory dump, first cell `-65` |
| `@`, `#` | `Code Successful` |

The useful discovery was `i`: it prints a memory dump. Also, `0x41 = 65`, and `[v41]i` gave `-65` in the first cell. This strongly suggests `[vXX]` subtracts a hexadecimal immediate from the current memory cell (starting from zero in that test).

I didn't need to fully reverse-engineer every instruction to solve the challenge.

## Extracting the flag

Instead of trying to execute or manually understand the whole program, I looked at the repeated immediate values in the code. One sequence of hexadecimal bytes was especially interesting:

```text
64 34 72 6b 7b 31 6d 61 67 31 6e 33
5f 64 30 31 6e 67 5f 74 68 34 74 5f
62 79 5f 68 34 6e 64 7d 63 30 64 65
```

Decoding those bytes as ASCII gives:

```text
d4rk{1mag1n3_d01ng_th4t_by_h4nd}c0de
```

A quick way to reproduce the ASCII conversion:

```python
hex_data = (
    "64 34 72 6b 7b 31 6d 61 67 31 6e 33 "
    "5f 64 30 31 6e 67 5f 74 68 34 74 5f "
    "62 79 5f 68 34 6e 64 7d 63 30 64 65"
)

flag = bytes.fromhex(hex_data).decode("ascii")
print(flag)
```

The message is basically *"imagine doing that by hand"*, which fits the huge obfuscated program pretty well lol.

## Small mistake

I initially submitted:

```text
d4rk{1mag1n3_d01ng_th4t_by_h4nd}
```

and got `Incorrect`. Turns out I simply forgot the extra `c0de` after the closing brace, even though the challenge explicitly said it had a different flag format. Oops :(

With the correct suffix, the flag was accepted.

## Flag

```text
d4rk{1mag1n3_d01ng_th4t_by_h4nd}c0de
```
