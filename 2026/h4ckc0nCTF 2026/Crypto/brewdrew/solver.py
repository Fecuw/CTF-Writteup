#!/usr/bin/env python3
"""
brewdrew  --  solver

The logged "conversation" is six huge integers.  Each one is a bitmap of the
message rendered as pixel art:

  * n is always divisible by 17.  17 = 0b10001, so multiplying by 17 overlays
    the bitmap with a ghost copy of itself shifted by 4 pixels.  Divide by 17
    to get the clean image.  (That is the "weird crypto-scheme".)
  * the pixels are stored COLUMN-MAJOR with a column height of 17 px,
    MSB first, bottom row first (the image is stored upside down).

So: n // 17 -> bits -> chop into 17-bit columns -> transpose -> flip
vertically -> ASCII art.

Usage:  python3 solver.py [path/to/logged_convo.txt]
"""

import re
import sys

HEIGHT = 17            # pixel height of one stored column
GHOST  = 17            # 0b10001 -> the x+(x<<4) ghost overlay


# --------------------------------------------------------------------------
# 1. load
# --------------------------------------------------------------------------
def load(path):
    text = open(path).read()
    return [(who, int(num))
            for who, num in re.findall(r'(brew|drew)\s*:\s*(\d+)', text)]


# --------------------------------------------------------------------------
# 2. integer -> bitmap
# --------------------------------------------------------------------------
def to_image(n):
    """Return the message bitmap as a list of '0'/'1' strings (top row first)."""
    assert n % GHOST == 0, "expected the x*17 ghost overlay"
    bits = bin(n // GHOST)[2:]

    best = None
    for shift in range(HEIGHT):                 # recover the column phase
        s = '0' * shift + bits
        s += '0' * (-len(s) % HEIGHT)
        cols = [s[i:i + HEIGHT] for i in range(0, len(s), HEIGHT)]
        img = [''.join(c[r] for c in cols) for r in range(HEIGHT)]

        blank = 0                               # the real image sits on a baseline
        for row in reversed(img):
            if '1' in row:
                break
            blank += 1
        if best is None or blank > best[0]:
            best = (blank, img)

    img = best[1][::-1]                         # stored upside down
    while img and '1' not in img[0]:
        img.pop(0)
    while img and '1' not in img[-1]:
        img.pop()

    right = max(r.rfind('1') for r in img) + 1   # trim the blank right margin
    return [r[:right] for r in img]


def show(img):
    return '\n'.join(r.replace('0', ' ').replace('1', '#') for r in img)


# --------------------------------------------------------------------------
# 3. bitmap -> text
# --------------------------------------------------------------------------
def glyphs(img):
    """Split the bitmap on blank columns."""
    width = len(img[0])
    blank = [all(row[c] == '0' for row in img) for c in range(width)]
    out, c = [], 0
    while c < width:
        if blank[c]:
            c += 1
            continue
        start = c
        while c < width and not blank[c]:
            c += 1
        g = [row[start:c] for row in img]
        while g and '1' not in g[0]:
            g.pop(0)
        while g and '1' not in g[-1]:
            g.pop()
        out.append(g)
    return out


def canonical(g):
    """Collapse the per-message vertical/horizontal stretch of the font."""
    rows = []
    for r in g:
        if not rows or rows[-1] != r:
            rows.append(r)
    cols = []
    for c in range(len(rows[0])):
        col = ''.join(r[c] for r in rows)
        if not cols or cols[-1] != col:
            cols.append(col)
    return tuple(''.join(col[j] for col in cols).replace('0', '.').replace('1', '#')
                 for j in range(len(rows)))


# canonical shape -> character (read off the rendered art)
FONT = {
    ('#.#', '###', '#.#'): 'H',
    ('#', '.', '#'): 'i!',                               # see disambiguate()
    ('..#..', '.#.#.', '#...#', '.#.#.', '..#..'): 'O',
    ('#.....#', '#..#..#', '#.#.#.#', '.#...#.'): 'W',
    ('#.....#', '#..#..#', '#.#.#.#', '##...##'): 'W',
    ('..#..', '.#.#.', '#...#', '#####', '#...#'): 'A',
    ('###.', '#..#', '###.', '##..', '#.#.', '#..#'): 'R',
    ('###', '#..', '##.', '#..', '###'): 'E',
    ('#...#', '.#.#.', '..#..'): 'UVY',                  # see disambiguate()
    ('..##..', '.#..#.', '#....#', '....#.', '...#..', '......', '...#..'): '?',
    ('###', '.#.', '###'): 'I',
    ('#...#', '##.##', '#.#.#', '#...#'): 'M',
    ('.#.', '#.#', '#..', '.#.', '..#', '#.#', '.#.'): 'S',
    ('..#', '.#.', '#..', '.#.', '..#'): 'C',
    ('##..', '#.#.', '#..#', '###.'): 'D',
    ('..#####..', '.#.....#.', '#.#.#...#', '#.......#',
     '#..##...#', '#.#..#..#', '.#.....#.', '..#####..'): ':(',
    ('###.', '...#', '.##.', '.#..', '....', '.#..'): '?',
    ('###...', '.#.#..', '.#.###', '.#.#.#'): 'Th',      # T and h touch
    ('.##.', '#..#', '#...', '.#..', '..#.', '...#', '#..#', '.##.'): 'S',
    ('.#.', '#.#', '###', '#.#'): 'a',
    ('###', '#..', '##.', '#..'): 'F',
    ('.###.', '#...#', '....#', '..##.', '..#..', '.....', '..#..'): '?',
    ('..#', '.##', '#.#', '.#.'): 'd',
    ('#...', '#.#.', '####', '..#.'): '4',
    ('#.#', '##.', '#..'): 'r',
    ('#...', '#..#', '#.#.', '##..', '#.#.', '#..#'): 'k',
    ('...#.', '..#.#', '..#..', '.#...', '#....',
     '.#...', '..#..', '..#.#', '...#.'): '{',
    ('..#..', '.#.#.', '##..#', '#.#.#', '#..##', '.#.#.', '..#..'): '0',
    ('#..', '##.', '#.#', '##.'): 'b',
    ('#',): '_',
    ('##.', '#.#', '##.'): 'D',
    ('..##..', '.#..#.', '#....#', '.....#', '...##.', '...#..',
     '......', '...#..'): '?',
    ('.#...', '#.#..', '..#..', '...#.', '....#',
     '...#.', '..#..', '#.#..', '.#...'): '}',
    ('#..', '#.#', '##.', '#.#'): 'K',
    ('###...', '.#.#..', '.#.##.', '.#.#.#'): 'Th',
    ('.#..', '#.#.', '..#.', '.##.', '#.#.', '.#.#'): 'a',
    ('#...', '#.##', '##.#', '#..#'): 'n',
    ('..#.#..', '.......', '...#...', '#.....#', '.#...#.', '..###..'): ':)',
}


def disambiguate(choice, g):
    """Shapes that only differ by their proportions, not their outline."""
    runs = []                                   # row run-lengths
    for r in g:
        if runs and runs[-1][0] == r:
            runs[-1][1] += 1
        else:
            runs.append([r, 1])

    if choice == 'i!':                          # '!' = long bar then dot,
        return '!' if runs[0][1] > runs[-1][1] else 'i'   # 'i' = dot then stem

    if choice == 'UVY':
        if g[-1].count('1') > 1:                # 'U' ends on a flat bottom
            return 'U'
        stem = sum(n for row, n in runs if row.count('1') == 1)
        return 'Y' if stem >= 0.3 * len(g) else 'V'       # 'Y' has a long stem

    return choice


def transcribe(img):
    gs = glyphs(img)
    cap = max(len(g) for g in gs)                # cap height of this message
    out = []
    for g in gs:
        ch = FONT.get(canonical(g))
        if ch is None:
            out.append('?')                      # unknown glyph
            continue
        if ch in ('i!', 'UVY'):
            ch = disambiguate(ch, g)
        if len(g) <= 0.75 * cap:                 # x-height -> lower case
            ch = ch.lower()
        out.append(ch)
    return ''.join(out)


# --------------------------------------------------------------------------
def main():
    path = sys.argv[1] if len(sys.argv) > 1 else 'logged_convo.txt'
    lines = []
    for who, n in load(path):
        img = to_image(n)
        print('=' * 72)
        print('%s:' % who)
        print(show(img))
        text = transcribe(img)
        print('  -> %s' % text)
        lines.append((who, text))

    print('=' * 72)
    print('\ntranscript:')
    for who, text in lines:
        print('  %-5s %s' % (who + ':', text))

    flag = next((t for _, t in lines if 'd4rk{' in t), None)
    print('\nflag: %s' % (flag or 'not found'))


if __name__ == '__main__':
    main()
