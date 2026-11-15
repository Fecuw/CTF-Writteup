# Weighty Words

The PDF was only five pages, but somehow around 117 MB. Way too big for that much text, so I figured something was hidden in it.

I started with `exiftool`, `strings`, and `ttx` on the font. Nothing useful came up. I didn't really want to dig through all the glyphs, so I went back to the PDF and checked its embedded font instead.

That font had a weird `GSUX` table taking up about 122 MB. Well, there's the file size. Its header didn't look familiar, so I checked simple byte shifts against known file signatures. Subtracting 3 from every byte gave an XZ header.

```python
xz_data = bytes((b - 3) & 0xff for b in font.getTableData('GSUX'))
```

Decompressing it gave me a FITS file. Didn't expect an astronomy format inside a font, but okay.

The FITS contained a small `PREVIEW` image and a much larger `SCI` image. I checked the preview first because it was easier, and got:

`d4rk{n1c3_try_but_n0}`

It literally says "nice try, but no," but I submitted it anyway. **Incorrect.** Fair enough.

So the preview was bait. Same string shows up again as a base64 `COMMENT` on the `SCI` header, in case I missed it the first time:

```
COMMENT ZDRya3tuMWMzX3RyeV9idXRfbjB9    -> d4rk{n1c3_try_but_n0}
COMMENT The pilgrims carried only bread.
```

That second comment is a line lifted straight out of the paper, and the paper is almost entirely decoys — every chapter describes a real stego technique and then says it wasn't used here. Kerning, XMP metadata, incremental updates, LSBs, chi-square, packet captures, registry hives. The base64 / Caesar / hex ciphers in chapter VIII decode to "The scribe laughs at thee", "Not here, good reader", and "not here, not yet". The whole document is there to burn your time. The only thing I took from it was the title of chapter V, about raising a sunken vessel whole and working on a copy.

## The part that actually mattered

There's a fourth HDU at the very end of the file that I nearly scrolled past — a tiny `LOG` binary table:

```
debias       ok
flatfield    ok
stack        ok
calibrate    skipped
```

`calibrate` **skipped**. That's the hint for the whole challenge.

The `SCI` header says `BAYERPAT = 'GRBG'`, so I did the obvious thing and split the four Bayer planes. That was wrong, and it wasted the most time — demosaicing and background-subtracting gave me nothing but grey static. The giveaway is trivial once you just print the ranges:

```
plane G1: min=1.061208 max=12.476406
plane R : min=-0.036000 max=0.006251
plane B : min=-0.036000 max=0.006251
plane G2: min=-0.035453 max=0.031177
```

R, B and G2 are flat zero across the entire 16512×9288 frame. Every photon is on the even-row/even-column plane. The Bayer pattern is a lie, and the real image is just `raw[0::2, 0::2]` — 8256×4644.

## Weighty Words

With the right plane the static turned into recognisable text, but still buried in noise. Then I counted distinct values and it fell apart immediately:

```
total 48000 px in crop, 59 distinct values

1.061208  x3592     1.501124  x183
1.157625  x3509     1.622235  x164
1.259712  x3482     1.749690  x151
1.367631  x3487     1.883653  x173
1.481544  x3532     2.024285  x164
   ...                 ...
2.628072  x3461     3.408863  x169
```

Two interleaved ladders of exactly 13 levels each. The sky background only ever takes the 13 high-count values, the painted text only ever takes the 13 low-count ones, and actual stars sit off-ladder with unique values. That's the "calibration" that was skipped — the pixels were never flattened into a continuous scale, so the discrete levels are still sitting there in the open.

So there's no denoising to do at all. You just ask which ladder each pixel is on:

```python
background = values[counts > sample.size / 200]   # 13 levels
mask = ~np.isin(plane, background)                # text + stars
```

That gives a clean starfield with one string painted into it. Splitting text from stars is the same trick one level down — the text levels repeat about 150–200 times each, stars are one-offs, and the gap between 150 and 5 is wide enough that any threshold works:

```python
values, counts = np.unique(plane[mask], return_counts=True)
text_levels = values[counts >= 50]                # 13 levels, 2262 px
```

Bounding box lands at rows 2992:3047, columns 6102:6434 of the G1 plane — a 332×55 strip in a 38-megapixel frame, which is why nothing turned up until I stopped looking at averages.

`d4rk{1t5_n0t_r8b?}`

Which is the challenge telling me, after the fact, exactly what cost me the afternoon. **Correct.**

The full path:

`PDF → embedded font → GSUX → byte shift (-3) → XZ → FITS → SCI → G1 plane → value ladder → flag`

## Notes

- The two decoys both announce themselves (`n1c3_try_but_n0`), and the real flag is also a sentence about the solve. The challenge is consistent about taunting you.
- `BAYERPAT`, `ROWORDER` and `OBJECT` in the header are all set to make you reach for a demosaic pipeline. Check whether the planes actually contain anything before trusting a header.
- The `LOG` table is the only honest thing in the file. Read the small HDUs first — it's four rows and it tells you what was done to the data.
- Don't `gaussian_filter` quantised data. Smoothing is what destroyed the signal on my first pass; the levels were readable the whole time.

## Solver

```bash
python3 -m pip install fonttools numpy pillow
python3 solver.py --pdf paper.pdf --out recovered
```

Runs the whole chain in about 7 seconds. No PDF library needed — the font is the `/FontFile2` stream of object 19, so the solver just takes `/Length` bytes after `stream` and inflates them. Slice on `/Length` rather than hunting for `endstream`; 122 MB of deflate output contains that word by accident.

Writes `recovered/flag.png` (the string above), `recovered/starfield.png`, and `recovered/preview_recovered.png` (the decoy). Add `--skip-sci` to stop after the FITS, or `--font embedded_font.ttf` to skip the PDF step if you already pulled the font out.

Note that it drops a 614 MB `gsux_decoded.bin` next to the images, which is the inflated FITS. Delete it when you're done.

| File | Purpose |
|---|---|
| `solver.py` | full chain: font extraction, GSUX de-obfuscation, FITS walk, SCI ladder reveal |
| `Writeup.md` | this document |
