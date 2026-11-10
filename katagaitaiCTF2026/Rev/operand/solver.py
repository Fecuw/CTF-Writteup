#!/usr/bin/env python3
"""Recover Operand's flag from the encrypted constants in main()."""

import argparse
from pathlib import Path


def recover_flag(binary: Path) -> str:
    data = binary.read_bytes()
    if data[:6] != b"\x7fELF\x02\x01":
        raise ValueError("Expected a 64-bit little-endian ELF binary")

    # main() builds the expected bytes with four movabs instructions and
    # one 16-bit mov. Immediates appear in memory order in the ELF file.
    constants = (
        (0x1254, b"\x48\xb8", 8),
        (0x125E, b"\x48\xba", 8),
        (0x1270, b"\x48\xb8", 8),
        (0x127A, b"\x48\xba", 8),
        (0x128C, b"\x66\xc7\x45\xa0", 2),
    )
    encrypted = bytearray()
    for offset, opcode, size in constants:
        start = offset + len(opcode)
        if data[offset:start] != opcode or len(data[start:start + size]) != size:
            raise ValueError(f"Unexpected instruction at offset {offset:#x}")
        encrypted.extend(data[start:start + size])

    # xor() takes the input pointer from xmm3 and XORs each byte with 0xAA.
    flag = bytes(value ^ 0xAA for value in encrypted)
    return flag.decode("ascii")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "binary", nargs="?", type=Path,
        default=Path(__file__).resolve().with_name("operand"),
        help="path to operand (default: next to this script)",
    )
    args = parser.parse_args()
    try:
        print(recover_flag(args.binary))
    except (OSError, ValueError) as error:
        parser.exit(1, f"error: {error}\n")


if __name__ == "__main__":
    main()
