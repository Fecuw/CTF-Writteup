#!/usr/bin/env python3
import socket
import re

HOST = "web.katagaitai-ctf.net"
PORT = 80
PATH = "/http/step5.html"

CHUNK = 3
MAX_BYTES = 8192
MARKER = b"The flag is"
TIMEOUT = 10


def request(start, end):
    payload = (
        f"GET {PATH} HTTP/1.1\r\n"
        f"Host: {HOST}\r\n"
        f"Range: bytes={start}-{end}\r\n"
        "Accept-Encoding: identity\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode()

    with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as sock:
        sock.settimeout(TIMEOUT)
        sock.sendall(payload)

        data = bytearray()
        while True:
            chunk = sock.recv(3)
            if not chunk:
                break
            data.extend(chunk)

    header, sep, body = bytes(data).partition(b"\r\n\r\n")
    if not sep:
        raise RuntimeError("Invalid HTTP response")

    status = header.split(b"\r\n", 1)[0]

    if not re.match(rb"HTTP/\d(?:\.\d)? 206\b", status):
        raise RuntimeError(f"Range rejected: {status!r}")

    match = re.search(
        rb"(?im)^Content-Range:\s*bytes\s+(\d+)-(\d+)/(\d+|\*)",
        header
    )

    if not match:
        raise RuntimeError("Missing Content-Range")

    if (int(match.group(1)), int(match.group(2))) != (start, end):
        raise RuntimeError("Unexpected Content-Range")

    if len(body) != end - start + 1:
        raise RuntimeError("Unexpected body length")

    return body


def main():
    buffer = bytearray()
    flag = bytearray()
    found = False

    for start in range(0, MAX_BYTES, CHUNK):
        end = start + CHUNK - 1
        part = request(start, end)

        if not found:
            buffer.extend(part)
            pos = buffer.find(MARKER)

            if pos == -1:
                # マーカーがチャンク境界をまたぐ場合に備える
                if len(buffer) > len(MARKER):
                    del buffer[:-len(MARKER)]
                continue

            found = True
            print(f"[+] Found marker at byte {start + len(part) - len(buffer) + pos}")

            # "The flag is" より後だけ取得
            flag.extend(buffer[pos + len(MARKER):])
            print("[+] Recovering flag...")
        else:
            flag.extend(part)

        print(f"[*] {start}-{end}: {part!r}")

        if b"}" in flag:
            flag = flag[:flag.index(b"}") + 1]
            result = flag.strip().decode(errors="replace")
            print(f"\n[+] FLAG: {result}")

            with open("flag.txt", "w") as f:
                f.write(result + "\n")
            return

    print("[!] Flag not completely recovered")
    print(flag.decode(errors="replace"))


if __name__ == "__main__":
    main()
