#!/usr/bin/env python3
import re
import secrets
from math import gcd

from pwn import remote, context
from gmpy2 import iroot

HOST = "10.83.23.77"
PORT = 1337

context.log_level = "info"


def password_valid(pw: bytes, nlen: int) -> bool:
    """
    Reproduce the server's password policy exactly.

    Note:
        The server checks str(password), not the raw bytes.
    """
    s = str(pw)

    return (
        len(pw) == nlen
        and any(c.islower() for c in s)
        and any(c.isupper() for c in s)
        and any(c.isdigit() for c in s)
        and any(c in "!@#$%^&*()-+" for c in s)
    )


def make_collision(N: int, e: int, nlen: int):
    """
    Construct two different passwords with identical RSA hashes.

        pw2 = pw1 + N

    Therefore:

        pw1^e mod N == pw2^e mod N
    """
    limit = 1 << (8 * nlen)
    max_x = limit - N - 1

    if max_x <= 0:
        raise RuntimeError("No room for x + N")

    for _ in range(100000):
        x = secrets.randbelow(max_x) + 1

        pw1 = x.to_bytes(nlen, "big")
        pw2 = (x + N).to_bytes(nlen, "big")

        if not password_valid(pw1, nlen):
            continue

        if not password_valid(pw2, nlen):
            continue

        if pw1 == pw2:
            continue

        h1 = pow(int.from_bytes(pw1, "big"), e, N)
        h2 = pow(int.from_bytes(pw2, "big"), e, N)

        assert h1 == h2

        return pw1, pw2

    raise RuntimeError("Could not construct RSA hash collision")


def register(io, username: str, password: bytes):
    """
    Register a user.

    Protocol invariant:
        The previous operation has already consumed the menu prompt.

    At the end, consume the next menu prompt exactly once.
    """
    print(f"[*] Registering {username!r}")

    # Do not use sendlineafter(b"> ", ...).
    # The menu prompt was already consumed.
    io.sendline(b"1")

    io.sendlineafter(
        b"Username: ",
        username.encode()
    )

    io.sendlineafter(
        b"Password(hex): ",
        password.hex().encode()
    )

    result = io.recvuntil(b"> ", timeout=15)

    if not result.endswith(b"> "):
        raise RuntimeError(
            "Registration timed out:\n"
            + result.decode(errors="replace")
        )

    print(result.decode(errors="replace"))

    return result


def solve_flag0(io, N: int, e: int, nlen: int):
    print("\n========== SOLVING FLAG0 ==========")

    print("[*] Constructing RSA hash collision")

    pw1, pw2 = make_collision(N, e, nlen)

    print("[+] Collision constructed")
    print("[+] Password length:", len(pw1))
    print("[+] Hash:", hex(pow(int.from_bytes(pw1, "big"), e, N)))

    result1 = register(io, "attacker1", pw1)

    if b"Registered 'attacker1'." not in result1:
        raise RuntimeError("First registration failed")

    result2 = register(io, "attacker2", pw2)

    if b"pentest" not in result2:
        raise RuntimeError(
            "FLAG0 collision was not triggered:\n"
            + result2.decode(errors="replace")
        )

    print("[+] FLAG0 collision triggered!")

    match = re.search(
        rb"Have this for now:\s*\r?\n([^\r\n]+)",
        result2
    )

    if match:
        flag0 = match.group(1).decode(errors="replace")
        print(f"\n[FLAG0] {flag0}\n")
        return flag0

    print("[!] Collision triggered, but FLAG0 could not be parsed")
    return None


def solve_flag1(io, N: int, e: int):
    print("\n========== SOLVING FLAG1 ==========")

    print("[*] Starting admin authentication")

    # The previous registration already consumed the menu prompt.
    io.sendline(b"2")

    io.sendlineafter(
        b"Username: ",
        b"admin"
    )

    # The server reveals the admin password hash before round 1.
    banner = io.recvuntil(
        b"Announcement(hex): ",
        timeout=15
    )

    if not banner.endswith(b"Announcement(hex): "):
        raise RuntimeError(
            "Failed to receive first announcement prompt:\n"
            + banner.decode(errors="replace")
        )

    match = re.search(
        rb"committed pw_hash\s+(\d+)",
        banner
    )

    if not match:
        raise RuntimeError(
            "Admin hash not found:\n"
            + banner.decode(errors="replace")
        )

    admin_hash = int(match.group(1))

    print("[+] Admin hash:", hex(admin_hash))
    print("[*] Recovering admin secret using integer root")

    # admin_secret = get_random_bytes(19)
    #
    # secret < 2^152
    # secret^17 < 2^2584
    #
    # N is approximately 2674 bits.
    #
    # Thus:
    #     admin_hash = secret^17
    #
    # without modular reduction.

    secret, exact = iroot(admin_hash, e)

    if not exact:
        raise RuntimeError(
            "Integer root is not exact. "
            "The low-exponent attack did not succeed."
        )

    secret = int(secret)

    assert pow(secret, e, N) == admin_hash

    if gcd(secret, N) != 1:
        raise RuntimeError("Recovered secret is not invertible modulo N")

    secret_bytes = secret.to_bytes(19, "big")

    print("[+] Admin secret recovered!")
    print("[+] Secret hex:", secret_bytes.hex())

    rounds = 256 // e.bit_length() + 1

    print(f"[*] Completing {rounds} authentication rounds")

    for rnd in range(rounds):

        # Choose random t in Z_N^*
        while True:
            t = secrets.randbelow(N - 2) + 2

            if gcd(t, N) == 1:
                break

        # Announcement:
        #
        # a = t^e mod N

        announcement = pow(t, e, N)

        io.sendline(
            format(announcement, "x").encode()
        )

        # Receive challenge and response prompt.
        challenge_data = io.recvuntil(
            b"Response(hex): ",
            timeout=15
        )

        if not challenge_data.endswith(b"Response(hex): "):
            raise RuntimeError(
                f"Round {rnd + 1}: response prompt timed out:\n"
                + challenge_data.decode(errors="replace")
            )

        match = re.search(
            rb"Challenge:\s*(\d+)",
            challenge_data
        )

        if not match:
            raise RuntimeError(
                f"Round {rnd + 1}: challenge missing:\n"
                + challenge_data.decode(errors="replace")
            )

        c = int(match.group(1))

        if not (0 <= c < e):
            raise RuntimeError(f"Unexpected challenge: {c}")

        # Response:
        #
        # r = t * secret^c mod N
        #
        # Verification:
        #
        # r^e = a * admin_hash^c mod N

        response = (
            t * pow(secret, c, N)
        ) % N

        assert response != 0
        assert gcd(response, N) == 1

        expected = (
            announcement * pow(admin_hash, c, N)
        ) % N

        actual = pow(response, e, N)

        assert actual == expected

        io.sendline(
            format(response, "x").encode()
        )

        print(
            f"[+] Round {rnd + 1:02d}/{rounds}: "
            f"challenge={c}, verified"
        )

        # For every round except the last, wait for the next
        # announcement prompt.
        if rnd < rounds - 1:
            next_prompt = io.recvuntil(
                b"Announcement(hex): ",
                timeout=15
            )

            if not next_prompt.endswith(b"Announcement(hex): "):
                raise RuntimeError(
                    f"Round {rnd + 1}: authentication failed:\n"
                    + next_prompt.decode(errors="replace")
                )

    # The server prints the welcome message and flag after
    # the final successful response, then returns to the menu.
    result = io.recvuntil(
        b"> ",
        timeout=15
    )

    print("\n========== FLAG1 RESULT ==========")
    print(result.decode(errors="replace"))

    match = re.search(
        rb"Here is your flag:\s*([^\r\n]+)",
        result
    )

    if match:
        flag1 = match.group(1).decode(errors="replace")
        print(f"\n[FLAG1] {flag1}\n")
        return flag1

    raise RuntimeError(
        "Admin authentication did not return FLAG1:\n"
        + result.decode(errors="replace")
    )


def main():
    print("[*] Connecting to challenge server")

    io = remote(
        HOST,
        PORT,
        timeout=15
    )

    flag0 = None
    flag1 = None

    try:
        # Receive initial banner and consume the first menu prompt.
        banner = io.recvuntil(
            b"> ",
            timeout=15
        )

        if not banner.endswith(b"> "):
            raise RuntimeError("Initial menu prompt timed out")

        match = re.search(
            rb"Parameters:\s*N=(0x[0-9a-fA-F]+),\s*e=(0x[0-9a-fA-F]+)",
            banner
        )

        if not match:
            raise RuntimeError(
                "Failed to parse RSA parameters:\n"
                + banner.decode(errors="replace")
            )

        N = int(match.group(1), 16)
        e = int(match.group(2), 16)

        nlen = (N.bit_length() + 7) // 8

        print(f"[+] Connected: {HOST}:{PORT}")
        print(f"[+] N bits: {N.bit_length()}")
        print(f"[+] e: {e}")
        print(f"[+] NLEN: {nlen}")

        if e != 17:
            raise RuntimeError(
                f"Unexpected RSA exponent: {e}"
            )

        # FLAG0
        flag0 = solve_flag0(
            io,
            N,
            e,
            nlen
        )

        # FLAG1
        flag1 = solve_flag1(
            io,
            N,
            e
        )

        print("\n" + "=" * 60)
        print("                  FINAL RESULTS")
        print("=" * 60)

        print(f"FLAG0: {flag0}")
        print(f"FLAG1: {flag1}")

        print("=" * 60)

        # Exit cleanly.
        io.sendline(b"3")

    except EOFError:
        print("[!] Server closed the connection unexpectedly")
        raise

    except KeyboardInterrupt:
        print("\n[!] Interrupted by user")

    finally:
        io.close()


if __name__ == "__main__":
    main()
