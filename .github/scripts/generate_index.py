#!/usr/bin/env python3
"""Generate the root README CTF event index from event README files.

Events without a CTFtime URL appear first; events with a CTFtime URL
are ordered by start date descending. No third-party dependencies.
"""
import subprocess
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

START_MARKER = '<!-- CTF-INDEX:START -->'
END_MARKER = '<!-- CTF-INDEX:END -->'
CTFTIME_RE = re.compile(r'https?://(?:www\.)?ctftime\.org/event/(\d+)(?:/|\b)', re.I)
YEAR_RE = re.compile(r'20\d{2}')
SKIP_DIRS = {'.git', '.github', 'scripts', 'assets', 'images', 'img', 'node_modules', '.venv', 'venv'}

def is_gitignored(path, root):
    result = subprocess.run(
        ['git', '-C', str(root), 'check-ignore', '-q', str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False
    )
    return result.returncode == 0

def parse_timestamp(value):
    if value is None or value == '':
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc)
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def fetch_event(event_id, timeout):
    url = f'https://ctftime.org/api/v1/events/{event_id}/'
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'CTF-Writteup-Index/1.0 (GitHub Actions)',
            'Accept': 'application/json',
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, dict) or parse_timestamp(data.get('start')) is None:
        raise ValueError(f'Invalid start time for event {event_id}')
    return {'start': data['start'], 'title': data.get('title', '')}


def event_dirs(root):
    for item in sorted(root.iterdir(), key=lambda p: p.name.casefold()):
        if not item.is_dir() or item.name.startswith('.') or item.name in SKIP_DIRS:
            continue
        if YEAR_RE.fullmatch(item.name):
            for event in sorted(item.iterdir(), key=lambda p: p.name.casefold()):
                if event.is_dir() and not event.name.startswith('.') and (event / 'README.md').is_file():
                    yield event
        elif (item / 'README.md').is_file():
            yield item


def escape_cell(value):
    return (str(value).replace('\\', '\\\\').replace('|', '\\|')
            .replace('\r', ' ').replace('\n', ' ')
            .replace('[', '\\[').replace(']', '\\]'))


def folder_link(folder, root):
    relative = folder.relative_to(root)
    return './' + '/'.join(quote(part, safe='') for part in relative.parts) + '/'


def render_time(dt):
    if dt is None:
        return '—'
    # UTC is used explicitly to ensure stable rendering on GitHub Markdown.
    return dt.strftime('%Y-%m-%d %H:%M UTC')


def generate(root, cache, refresh=False, timeout=12):
    without_ctftime = []
    with_ctftime = []

    for folder in event_dirs(root):
        if is_gitignored(folder, root):
          continue
        readme_text = (folder / 'README.md').read_text(encoding='utf-8', errors='replace')
        match = CTFTIME_RE.search(readme_text)
        event_id = match.group(1) if match else None
        entry = {'name': folder.name, 'folder': folder, 'event_id': event_id, 'start': None}

        if event_id is None:
            without_ctftime.append(entry)
            continue

        if refresh or event_id not in cache or parse_timestamp(cache.get(event_id, {}).get('start')) is None:
            try:
                cache[event_id] = fetch_event(event_id, timeout)
                print(f'[OK] {folder.name}: CTFtime event {event_id}', file=sys.stderr)
            except (urllib.error.URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
                print(f'[WARN] {folder.name}: CTFtime API failed: {exc}', file=sys.stderr)

        entry['start'] = parse_timestamp(cache.get(event_id, {}).get('start'))
        with_ctftime.append(entry)

    with_ctftime.sort(
        key=lambda entry: (
            entry['start'] is not None,
            entry['start'] or datetime.min.replace(tzinfo=timezone.utc),
            entry['name'].casefold(),
        ),
        reverse=True,
    )
    entries = without_ctftime + with_ctftime
    output = [
        '## Events',
        '',
        f'{len(entries)} events · Events without CTFtime first; remaining events sorted by start time (newest first).',
        '',
        '| Event | Start (UTC) | Writeup |',
        '| --- | --- | --- |',
    ]

    for entry in entries:
        name = escape_cell(entry['name'])
        link = folder_link(entry['folder'], root)
        event_link = (f'[{name}](https://ctftime.org/event/{entry["event_id"]}/)'
                      if entry['event_id'] else f'[{name}]({link})')
        output.append(f'| {event_link} | {render_time(entry["start"])} | [View]({link}) |')

    output += ['', '> Start times are sourced from CTFtime when available.']
    return '\n'.join(output) + '\n'


def update_readme(original, generated):
    has_start = START_MARKER in original
    has_end = END_MARKER in original
    if has_start != has_end:
        raise ValueError('Only one CTF index marker was found; refusing to overwrite README')
    if has_start:
        if original.index(START_MARKER) > original.index(END_MARKER):
            raise ValueError('CTF index markers are in the wrong order')
        before = original.split(START_MARKER, 1)[0]
        after = original.split(END_MARKER, 1)[1]
        return before + START_MARKER + '\n\n' + generated + '\n' + END_MARKER + after
    return original.rstrip() + '\n\n' + START_MARKER + '\n\n' + generated + '\n' + END_MARKER + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--refresh', action='store_true', help='Re-fetch CTFtime metadata')
    parser.add_argument('--timeout', type=int, default=12)
    args = parser.parse_args()
    root = args.root.resolve()
    readme_path = root / 'README.md'
    cache_path = root / '.github' / 'scripts' / 'ctftime-cache.json'

    try:
        cache = json.loads(cache_path.read_text(encoding='utf-8')) if cache_path.exists() else {}
        if not isinstance(cache, dict):
            raise ValueError('Cache JSON must be an object')
        generated = generate(root, cache, args.refresh, args.timeout)
        original = readme_path.read_text(encoding='utf-8') if readme_path.exists() else '# CTF-Writteup\n'
        updated = update_readme(original, generated)
    except (ValueError, OSError) as exc:
        print(f'[ERROR] {exc}', file=sys.stderr)
        return 1

    if updated != original:
        readme_path.write_text(updated, encoding='utf-8')
        print('[UPDATED] README.md')
    else:
        print('[UNCHANGED] README.md')

    serialized = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if not cache_path.exists() or cache_path.read_text(encoding='utf-8') != serialized:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(serialized, encoding='utf-8')
        print('[UPDATED] .github/scripts/ctftime-cache.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

