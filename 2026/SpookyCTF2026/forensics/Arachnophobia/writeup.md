# Writeup
"Something about the SpookyCTF logo feels off... like something's tangled in the webs." We get `tangled.png`.

The PNG looks normal, but the file is bigger than it should be, so something is appended after the PNG data. Checking the file signatures / looking for a ZIP header shows a `PK\x03\x04` hidden inside the file.

So I just carve out the ZIP that's appended after the real PNG and extract it:

```bash
# the ZIP starts at offset 976909
dd if=tangled.png of=hidden.zip bs=1 skip=976909
file hidden.zip          # Zip archive data
unzip hidden.zip         # -> flag.txt
cat flag.txt
```

(easier: just find the `PK\x03\x04` offset and slice from there)

```
spooky{8_l3gs_4nd_4_z1p}
```

A "zip" tangled into the image. Cute.

# flag
```
spooky{8_l3gs_4nd_4_z1p}
```
