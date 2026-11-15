#!/usr/bin/env python3
"""Weighty Words: PDF embedded font -> GSUX -> subtract 3 -> XZ -> FITS -> SCI G1.
Dependencies: pip install fonttools numpy pillow
"""
import argparse
import base64
import io
import lzma
import re
import zlib
from pathlib import Path

B64_ONLY = re.compile(r'[A-Za-z0-9+/]+={0,2}\Z')
# /Length is the stored (compressed) size; /Length1 is the inflated size.
LENGTH = re.compile(rb'/Length(?!1)\s+(\d+)')


def extract_font(pdf_path, output):
    """Pull the embedded font out of the PDF by walking its stream objects.

    The font is the /FontFile2 stream, Flate-compressed. No PDF library is
    needed: take /Length bytes after 'stream' and inflate them. Slicing on
    /Length rather than searching for 'endstream' matters here, because the
    compressed bytes can contain that word by chance.
    """
    data = pdf_path.read_bytes()
    targets = {int(m.group(1)) for m in
               re.finditer(rb'/FontFile2\s+(\d+)\s+\d+\s+R', data)}
    print(f'[+] /FontFile2 objects: {sorted(targets) or "none, scanning all"}')
    for m in re.finditer(rb'(\d+)\s+0\s+obj(.{0,600}?)stream\r?\n', data, re.S):
        num, header = int(m.group(1)), m.group(2)
        if targets and num not in targets:
            continue
        size = LENGTH.search(header)
        if not size:
            print(f'[!] object {num} has no /Length, skipping')
            continue
        blob = data[m.end():m.end() + int(size.group(1))]
        if b'FlateDecode' in header:
            blob = zlib.decompress(blob)
        if b'GSUX' in blob[:2048]:
            output.write_bytes(blob)
            print(f'[+] Embedded font: object {num}, {len(blob)} bytes')
            return
    raise RuntimeError('No embedded font with GSUX found')


def recover(font_path, xz_path, fits_path, keep_xz=False):
    from fontTools.ttLib import TTFont
    font = TTFont(str(font_path))
    blob = font.getTableData('GSUX')
    print(f'[+] GSUX size: {len(blob)} bytes')
    # Reverse the byte-wise +3 obfuscation, wrapping at 256.
    decoded = bytes((x - 3) & 255 for x in blob)
    assert decoded.startswith(b'\xfd7zXZ\x00'), 'XZ signature not found'
    if keep_xz:
        xz_path.write_bytes(decoded)
    with lzma.open(io.BytesIO(decoded), 'rb') as source, fits_path.open('wb') as dest:
        while chunk := source.read(4 * 1024 * 1024):
            dest.write(chunk)
    print(f'[+] FITS recovered: {fits_path} ({fits_path.stat().st_size} bytes)')


def read_hdus(path):
    """Read FITS headers without loading image arrays (2880-byte blocks)."""
    size = path.stat().st_size
    with path.open('rb') as f:
        while f.tell() < size:
            start = f.tell()
            cards = []
            while True:
                card = f.read(80)
                if len(card) != 80:
                    return
                line = card.decode('ascii', 'replace')
                cards.append(line)
                if line.startswith('END '):
                    break
            header_bytes = ((len(cards) * 80 + 2879) // 2880) * 2880
            data_offset = start + header_bytes
            d = {}
            for line in cards:
                if line[8:10] == '= ':
                    d[line[:8].strip()] = line[10:80].split('/')[0].strip().strip("'").strip()
            ndim = int(d.get('NAXIS', 0))
            count = 0 if ndim == 0 else 1
            for i in range(1, ndim + 1):
                count *= int(d[f'NAXIS{i}'])
            data_bytes = (count * abs(int(d.get('BITPIX', '8'))) // 8 + int(d.get('PCOUNT', 0))) * int(d.get('GCOUNT', 1))
            yield d, cards, data_offset, data_bytes
            next_pos = data_offset + ((data_bytes + 2879) // 2880) * 2880
            if next_pos <= start:
                return
            f.seek(next_pos)


def ladders(plane, sample_rows=4000):
    """Find the quantised value ladders in the SCI plane.

    The sky background only ever takes 13 distinct float values, and the
    painted text only ever takes 13 *other* ones. Stars are off-ladder and
    almost always unique, so counting values separates all three cleanly.
    """
    import numpy as np
    sample = np.asarray(plane[:sample_rows], dtype=np.float32).ravel()
    values, counts = np.unique(sample, return_counts=True)
    background = np.sort(values[counts > sample.size / 200])
    print(f'[+] Background ladder: {background.size} levels, '
          f'{background[0]:.6f} .. {background[-1]:.6f}')
    return background


def reveal(plane, background, outdir):
    """Mask off the background ladder, then split text from stars."""
    import numpy as np
    from PIL import Image
    height, width = plane.shape
    ys, xs, vs = [], [], []
    for start in range(0, height, 200):
        block = np.asarray(plane[start:start + 200], dtype=np.float32)
        hit = ~np.isin(block, background)
        y, x = np.nonzero(hit)
        ys.append(y + start)
        xs.append(x)
        vs.append(block[hit])
    ys, xs, vs = np.concatenate(ys), np.concatenate(xs), np.concatenate(vs)
    print(f'[+] Off-background pixels: {ys.size}')

    # The text ladder repeats; stars are one-offs. The gap between the two is
    # enormous (about 150 hits versus 5), so any threshold in between works.
    values, counts = np.unique(vs, return_counts=True)
    text_levels = values[counts >= 50]
    print(f'[+] Text ladder: {text_levels.size} levels, '
          f'{counts[counts >= 50].sum()} pixels')

    is_text = np.isin(vs, text_levels)
    starfield = np.zeros((height, width), dtype=np.uint8)
    starfield[ys, xs] = 255
    Image.fromarray(starfield).save(outdir / 'starfield.png')

    ty, tx = ys[is_text], xs[is_text]
    pad = 12
    y0, y1 = max(ty.min() - pad, 0), min(ty.max() + pad + 1, height)
    x0, x1 = max(tx.min() - pad, 0), min(tx.max() + pad + 1, width)
    print(f'[+] Text bounding box: rows {y0}:{y1}, columns {x0}:{x1}')

    flag = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
    flag[ty - y0, tx - x0] = 255
    out = outdir / 'flag.png'
    Image.fromarray(flag).resize(
        (flag.shape[1] * 3, flag.shape[0] * 3), Image.NEAREST).save(out)
    print(f'[+] Flag image: {out}')


def save_images(fits_path, outdir, skip_sci=False):
    import numpy as np
    from PIL import Image
    for hdr, cards, offset, nbytes in read_hdus(fits_path):
        name = hdr.get('EXTNAME', 'PRIMARY')
        print(f'[+] HDU {name}: BITPIX={hdr.get("BITPIX")}, dimensions={hdr.get("NAXIS1")}x{hdr.get("NAXIS2")}, offset={offset}')
        for line in cards:
            if line.startswith('COMMENT'):
                value = line[8:].strip()
                print('    COMMENT:', value)
                # Only one of the comments is base64; the other is prose.
                if B64_ONLY.match(value) and len(value) % 4 == 0:
                    decoded = base64.b64decode(value).decode('utf-8', 'replace')
                    print('    base64:', decoded, '(decoy)')
        if hdr.get('BITPIX') != '-32' or hdr.get('NAXIS') != '2':
            continue
        shape = (int(hdr['NAXIS2']), int(hdr['NAXIS1']))
        raw = np.memmap(fits_path, dtype='>f4', mode='r', offset=offset, shape=shape)
        if name == 'PREVIEW':
            a = np.asarray(raw, dtype=np.float32)
            lo, hi = np.nanpercentile(a, [1, 99])
            img = np.uint8(np.clip((a - lo) / max(hi-lo, 1e-6), 0, 1) * 255)
            Image.fromarray(img).save(outdir / 'preview_recovered.png')
            print('    -> preview_recovered.png (decoy flag)')
            continue
        if name == 'SCI' and not skip_sci:
            # BAYERPAT='GRBG' is a lie: R, B and G2 are flat zero and every
            # photon sits on the even-row/even-column plane.
            for key, (ro, co) in {'G1': (0, 0), 'R': (0, 1),
                                  'B': (1, 0), 'G2': (1, 1)}.items():
                probe = np.asarray(raw[ro::32, co::32], dtype=np.float32)
                print(f'    plane {key}: min={probe.min():.6f} max={probe.max():.6f}')
            plane = raw[0::2, 0::2]
            print(f'[+] Using G1 plane only: {plane.shape[1]}x{plane.shape[0]}')
            reveal(plane, ladders(plane), outdir)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pdf', default='paper.pdf')
    p.add_argument('--font', help='Existing extracted embedded_font.ttf (skip PDF extraction)')
    p.add_argument('--out', default='recovered')
    p.add_argument('--skip-sci', action='store_true', help='Only extract the FITS and preview; skip the SCI reveal')
    p.add_argument('--keep-xz', action='store_true', help='Keep the intermediate XZ file (about 117 MB)')
    args = p.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    font_path = Path(args.font) if args.font else out / 'embedded_font.ttf'
    if not args.font:
        extract_font(Path(args.pdf), font_path)
    fits_path = out / 'gsux_decoded.bin'
    recover(font_path, out / 'gsux.xz', fits_path, args.keep_xz)
    save_images(fits_path, out, args.skip_sci)
    print('[+] Finished. The flag is painted in recovered/flag.png.')


if __name__ == '__main__':
    main()
