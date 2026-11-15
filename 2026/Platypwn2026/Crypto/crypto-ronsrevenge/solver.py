#!/usr/bin/env python3
# Ron's Revenge - RC4 weak IV attack
# pip install pwntools

import json
import os
import random
import time
from collections import Counter
from pwn import remote, context

# add definition
HOST = '10.83.25.89'
PORT = 1337
SAMPLES = 2048
TIMEOUT = 15
CACHE_FILE = 'rc4_samples.json'
N = 2048
KEY_LENGTH = 8
FLAG_START = b'PP{'

context.log_level = 'error'

# saved ciphertexts, so we don't need to ask the server again
cache = {}
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, 'r') as f:
        old = json.load(f)
    for name, value in old.items():
        cache[tuple(int(x) for x in name.split(','))] = bytes.fromhex(value)
    print('[+] Loaded', len(cache), 'cached ciphertexts')

connection = None
new_queries = 0

def save_cache():
    data = {}
    for iv, ct in cache.items():
        data[','.join(str(x) for x in iv)] = ct.hex()
    with open(CACHE_FILE + '.tmp', 'w') as f:
        json.dump(data, f)
    os.replace(CACHE_FILE + '.tmp', CACHE_FILE)


def get_ciphertext(iv):
    global connection, new_queries
    iv = tuple(iv)
    if iv in cache:
        return cache[iv]

    for attempt in range(5):
        try:
            if connection is None:
                connection = remote(HOST, PORT, timeout=TIMEOUT)
                connection.recvuntil(b'IV: ', timeout=TIMEOUT)
            message = ','.join(format(x, 'x') for x in iv)
            connection.sendline(message.encode())
            line = connection.recvline(timeout=TIMEOUT)
            if not line:
                raise ValueError('No ciphertext received')
            ct = bytes.fromhex(line.strip().decode())
            connection.recvuntil(b'IV: ', timeout=TIMEOUT)
            cache[iv] = ct
            new_queries += 1
            if new_queries % 100 == 0:
                save_cache()
            return ct
        except (OSError, EOFError, ValueError) as error:
            print('[!] retry', attempt + 1, '/5:', error)
            if connection is not None:
                connection.close()
            connection = None
            time.sleep(0.3)
    raise RuntimeError('Failed to get ciphertext for ' + str(iv))


# RC4 with 2048 states and 11-bit outputs
def rc4(key, size):
    s = list(range(N))
    j = 0
    for i in range(N):
        j = (j + s[i] + key[i % len(key)]) % N
        s[i], s[j] = s[j], s[i]

    i = 0
    j = 0
    number = 0
    bits = 0
    result = bytearray()
    while len(result) < size:
        i = (i + 1) % N
        j = (j + s[i]) % N
        s[i], s[j] = s[j], s[i]
        z = s[(s[i] + s[j]) % N]
        number = (number << 11) | z
        bits += 11
        while bits >= 8 and len(result) < size:
            bits -= 8
            result.append((number >> bits) & 255)
            number &= (1 << bits) - 1
    return bytes(result)


# first 11-bit keystream value from known PP{ prefix
def first_z(ct):
    known = bytes(ct[i] ^ FLAG_START[i] for i in range(3))
    value = int.from_bytes(known, 'big')
    return value >> 13


def get_votes(key, samples):
    position = 3 + len(key)
    votes = Counter()
    xs = list(range(N))
    random.Random(12345 + position).shuffle(xs)

    for count, x in enumerate(xs[:samples], 1):
        iv = (position, N - 1, x)
        ct = get_ciphertext(iv)
        z = first_z(ct)
        prefix = list(iv) + key

        s = list(range(N))
        j = 0
        for i in range(position):
            j = (j + s[i] + prefix[i]) % N
            s[i], s[j] = s[j], s[i]

        inverse = [0] * N
        for i, value in enumerate(s):
            inverse[value] = i

        guess = (inverse[z] - j - s[position]) % N
        votes[guess] += 1
        if count % 256 == 0:
            print('    IV', count, '/', samples, 'top:', votes.most_common(3), flush=True)
    return votes


def check_key(key):
    flag = None
    for iv in [(0, 0, 0), (1, 2, 3), (2047, 2046, 2045)]:
        ct = get_ciphertext(iv)
        stream = rc4(list(iv) + key, len(ct))
        plain = bytes(a ^ b for a, b in zip(ct, stream))
        if not plain.startswith(FLAG_START):
            return None
        if flag is not None and flag != plain:
            return None
        flag = plain
    return flag


try:
    print('[+] Getting baseline ciphertext')
    baseline = get_ciphertext((0, 0, 0))
    print('[+] Ciphertext bytes:', len(baseline))

    key = []
    for i in range(KEY_LENGTH):
        print('[+] Finding key[' + str(i) + ']')
        votes = get_votes(key, SAMPLES)
        print('[+] candidates:', votes.most_common(10))
        key.append(votes.most_common(1)[0][0])
        print('[+] Current key:', key)
        save_cache()

    print('[+] Candidate long-term key:', key)
    result = check_key(key)
    if result is not None:
        print('[SUCCESS] FLAG:', result.decode(errors='replace'))
    else:
        print('[!] Key did not verify. More samples or another attack may be needed.')
finally:
    save_cache()
    if connection is not None:
        connection.close()
