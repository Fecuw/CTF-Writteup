#!/usr/bin/env python3
"""Generate a CTF event index from top-level event directories and CTFtime URLs.

No third-party dependencies. Only edits the marked section of root README.md.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

START = '<!-- CTF-INDEX:START -->'
END = '<!-- CTF-INDEX:END -->'
URL_RE = re.compile(r'https?://(?:www\.)?ctftime\.org/event/(\d+)(?:/|\b)', re.I)
YEAR_RE = re.compile(r'\b(?:19|20)\d{2}\b')
SKIP = {'.git', '.github', 'scripts', 'assets', 'images', 'img', 'node_modules', '.venv', 'venv'}


def parse_timestamp(value):
    if not value:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc)
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def fetch_event(event_id, timeout):
    req = urllib.request.Request(
        f'https://ctftime.org/api/v1/events/{event_id}/',
        headers={'User-Agent': 'CTF-Writeup-Index/1.0 (GitHub Actions; public event metadata)', 'Accept': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.load(response)
    if not isinstance(data, dict) or not parse_timestamp(data.get('start')):
        raise ValueError('CTFtime API returned no valid start timestamp')
    return {'start': data['start'], 'title': data.get('title', '')}


def event_dirs(root):
    """Support current flat layout plus optional YYYY/event layout."""
    for item in sorted(root.iterdir()):
        if not item.is_dir() or item.name in SKIP or item.name.startswith('.'):
            continue
        if re.fullmatch(r'20\d{2}', item.name):
            for sub in sorted(item.iterdir()):
                if sub.is_dir() and not sub.name.startswith('.') and (sub / 'README.md').is_file():
                    yield sub
        elif (item / 'README.md').is_file():
            yield item


def escape_cell(s):
    return str(s).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ').replace('[', '\\[').replace(']', '\\]')


def make_link(path, root):
    relative = path.relative_to(root)
    return './' + '/'.join(quote(p, safe='') for p in relative.parts) + '/'


def render_time(dt):
    if not dt:
        return 'Unknown'
    iso = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    fallback = dt.strftime('%Y-%m-%d %H:%M UTC')
    return (f'<local-time datetime="{iso}" year="numeric" month="2-digit" '
            f'day="2-digit" hour="2-digit" minute="2-digit" time-zone-name="short">'
            f'{fallback}</local-time>')


def generate(root, cache, refresh, timeout):
    rows = []
    for folder in event_dirs(root):
        content = (folder / 'README.md').read_text(encoding='utf-8', errors='replace')
        match = URL_RE.search(content)
        event_id = match.group(1) if match else None
        dt = None
        if event_id:
            if refresh or event_id not in cache:
                try:
                    cache[event_id] = fetch_event(event_id, timeout)
                    print(f'[OK] {folder.name}: CTFtime event {event_id}', file=sys.stderr)
                except (urllib.error.URLError, TimeoutError, ValueError, OSError, json.JSONDecodeError) as exc:
                    print(f'[WARN] {folder.name}: API failed: {exc}', file=sys.stderr)
            dt = parse_timestamp(cache.get(event_id, {}).get('start'))
        else:
            continue  # No CTFtime URL: opt out silently.
        if dt is None:
            print(f'[WARN] {folder.name}: no usable CTFtime date; skipping', file=sys.stderr)
            continue
        rows.append({'name': folder.name, 'folder': folder, 'date': dt, 'event_id': event_id})

    rows.sort(key=lambda r: (r['date'] is not None, r['date'] or datetime.min.replace(tzinfo=timezone.utc), r['name'].casefold()), reverse=True)
    out = ['## Events', '', f'{len(rows)} events · Sorted by CTFtime start time (newest first).', '',
           '| Event | Start (local time) | Writeup |', '| --- | --- | --- |']
    for r in rows:
        name = escape_cell(r['name'])
        if r['event_id']:
            event = f'[{name}](https://ctftime.org/event/{r["event_id"]})'
        else:
            event = name
        out.append(f'| {event} | {render_time(r["date"])} | [View]({make_link(r["folder"], root)}) |')
    out += ['', '> Start times are sourced from CTFtime. Events without a CTFtime URL are omitted.']
    return '\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--refresh', action='store_true', help='Re-fetch already cached event IDs')
    parser.add_argument('--timeout', type=int, default=12)
    args = parser.parse_args()
    root = args.root.resolve()
    readme = root / 'README.md'
    cache_file = root / 'scripts' / 'ctftime-cache.json'
    try:
        cache = json.loads(cache_file.read_text(encoding='utf-8')) if cache_file.exists() else {}
        if not isinstance(cache, dict):
            raise ValueError('cache must be an object')
    except (ValueError, json.JSONDecodeError) as exc:
        print(f'[ERROR] Invalid cache: {exc}', file=sys.stderr)
        return 1

    block = generate(root, cache, args.refresh, args.timeout)
    old = readme.read_text(encoding='utf-8') if readme.exists() else '# CTF Writeups\n'
    if START in old and END in old:
        if old.index(START) > old.index(END):
            print('[ERROR] Invalid index marker order', file=sys.stderr)
            return 1
        before = old.split(START, 1)[0]
        after = old.split(END, 1)[1]
        new = before + START + '\n\n' + block + '\n' + END + after
    elif START not in old and END not in old:
        new = old.rstrip() + '\n\n' + START + '\n\n' + block + '\n' + END + '\n'
    else:
        print('[ERROR] Only one index marker found; refusing to overwrite README', file=sys.stderr)
        return 1

    if new != old:
        readme.write_text(new, encoding='utf-8')
        print('[UPDATED] README.md')
    else:
        print('[UNCHANGED] README.md')
    serialized = json.dumps(cache, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    if not cache_file.exists() or cache_file.read_text(encoding='utf-8') != serialized:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(serialized, encoding='utf-8')
        print('[UPDATED] scripts/ctftime-cache.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
