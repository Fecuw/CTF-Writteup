# Writeup
"Something strange is happening in the mirror... investigate the image, uncover what lies beneath the surface." We get `Eisoptrophobiactf.png`.

"beneath the surface" screams LSB steganography, so I throw it at `zsteg -a`:

```bash
zsteg -a Eisoptrophobiactf.png
```

One of the channels has an obvious base64 string:

```
b1,rgb,lsb,xy  .. text: "c3Bvb2t5e3RoZV9yZWZsZWN0aW9uX25ldmVyX2xpZXN9"
```

Extract that bit plane and base64-decode it:

```bash
zsteg -E 'b1,rgb,lsb,xy' Eisoptrophobiactf.png | base64 -D
# spooky{the_reflection_never_lies}
```

So the flag was hidden in the LSB of the RGB channels as base64.

# flag
```
spooky{the_reflection_never_lies}
```
