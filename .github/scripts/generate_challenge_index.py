#!/usr/bin/env python3
"""Update each CTF event README with challenge links grouped by category."""
import argparse
import re
import subprocess
from pathlib import Path
from urllib.parse import quote

START = '<!-- CHALLENGE-INDEX:START -->'
END = '<!-- CHALLENGE-INDEX:END -->'
YEAR = re.compile(r'20\d{2}')
SKIP = {'.git', '.github', '__pycache__', 'node_modules', '.venv', 'venv'}


def ignored(path: Path, root: Path) -> bool:
    """Respect gitignore, including ignored but untracked folders."""
    rel = path.relative_to(root).as_posix()
    result = subprocess.run(
        ['git', '-C', str(root), 'check-ignore', '-q', '--', rel],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    return result.returncode == 0


def visible_dirs(folder: Path, root: Path):
    return sorted(
        (p for p in folder.iterdir()
         if p.is_dir() and not p.name.startswith('.')
         and p.name not in SKIP and not ignored(p, root)),
        key=lambda p: p.name.casefold(),
    )


def events(root: Path):
    for year in sorted(root.iterdir()):
        if not year.is_dir() or not YEAR.fullmatch(year.name) or ignored(year, root):
            continue
        for event in visible_dirs(year, root):
            if (event / 'README.md').is_file():
                yield event


def link(path: Path, event: Path) -> str:
    return './' + '/'.join(quote(part, safe='') for part in path.relative_to(event).parts) + '/'


def label(name: str) -> str:
    return name.replace('\\', '\\\\').replace('[', '\\[').replace(']', '\\]').replace('|', '\\|').replace('\n', ' ')


def make_index(event: Path, root: Path) -> str:
    lines = ['## Challenges', '']
    count = 0
    for category in visible_dirs(event, root):
        problems = [p for p in visible_dirs(category, root)
                    if (p / 'README.md').is_file() or (p / 'Writeup.md').is_file()
                    or (p / 'writeup.md').is_file()]
        if not problems:
            continue
        lines += [f'### {label(category.name)}', '']
        for problem in problems:
            lines.append(f'- [{label(problem.name)}]({link(problem, event)})')
            count += 1
        lines.append('')
    if count == 0:
        lines.append('No challenges listed yet.\n')
    return '\n'.join(lines).rstrip() + '\n'


def update(event: Path, root: Path) -> bool:
    readme = event / 'README.md'
    old = readme.read_text(encoding='utf-8')
    index = make_index(event, root)
    block = START + '\n\n' + index + '\n' + END
    if START in old and END in old:
        a = old.index(START)
        b = old.index(END)
        if a >= b:
            raise ValueError(f'Marker order invalid: {readme}')
        new = old[:a] + block + old[b + len(END):]
    elif START not in old and END not in old:
        new = old.rstrip() + '\n\n' + block + '\n'
    else:
        raise ValueError(f'Only one marker present: {readme}')
    if new == old:
        return False
    readme.write_text(new, encoding='utf-8')
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.root.resolve()
    changed = 0
    for event in events(root):
        if update(event, root):
            print(f'[UPDATED] {event.relative_to(root)}/README.md')
            changed += 1
    print(f'[DONE] {changed} event README(s) updated')


if __name__ == '__main__':
    main()
