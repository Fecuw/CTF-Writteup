# Unholy Trinity - Writeup

## Overview

This challenge is an RSA-based authentication service. It has two flags, and we need to break two different parts of the implementation.

- **FLAG0:** Make two different passwords with the same RSA hash.
- **FLAG1:** Recover the admin password from its public hash, then pass the authentication protocol.

We don't need to factor the RSA modulus. Both attacks are much simpler than that.
![alt](./Unholy%20Trinity.png)

## FLAG0 - RSA hash collision

The server uses this function for password hashing:

```python
def hash_pw(pw: bytes) -> int:
    return pow(bytes_to_long(pw), e, N)
```

Here, `e = 17`, and `N` is the RSA modulus shown when we connect.

The problem is that RSA works modulo `N`. So, if we choose two integers `x` and `x + N`, their hashes are exactly the same:

```text
x^e mod N = (x + N)^e mod N
```

The server checks whether a new password has the same hash as a previously registered password. If it finds a collision, it prints `FLAG0`.

```python
if pw_hash == old_pw_hash:
    print(flag0)
```

So we just create two different passwords from `x` and `x + N`, then register them with different usernames.

There is one small thing to care about: both passwords must be exactly `NLEN` bytes long and pass the password policy. The policy actually checks `str(password)` instead of the raw password bytes, so we can reproduce that check locally and generate valid candidates.

The important part of the solver is:

```python
limit = 1 << (8 * nlen)
max_x = limit - N - 1

while True:
    x = secrets.randbelow(max_x) + 1
    pw1 = x.to_bytes(nlen, "big")
    pw2 = (x + N).to_bytes(nlen, "big")

    if password_valid(pw1, nlen) and password_valid(pw2, nlen):
        break
```

After registering `pw1` and `pw2`, the server detects the collision and gives us `FLAG0`. Nice.

## FLAG1 - Low exponent attack

Next is the admin login. At first, the authentication looks like a zero-knowledge identification protocol.

The server creates the admin password like this:

```python
admin_secret = get_random_bytes(19)
users["admin"] = hash_pw(admin_secret)
```

And when we try to log in, it prints the admin's password hash:

```python
print(f"Authenticating {username!r} with committed pw_hash {pw_hash}...")
```

This is a big problem because the secret is only **19 bytes (152 bits)**, and the public exponent is **17**.

Let the admin password integer be `s`. The hash is:

```text
h = s^17 mod N
```

But `s < 2^152`, so:

```text
s^17 < 2^2584
```

Meanwhile, the RSA modulus in this challenge is about 2674 bits. This means `s^17 < N`, so the modulo operation does nothing!

```text
h = s^17
```

We can recover `s` by calculating the exact integer 17th root of `h`. No RSA factoring needed.

```python
from gmpy2 import iroot

secret, exact = iroot(admin_hash, 17)
assert exact
secret = int(secret)
```

By the way, if `s^17` had been larger than `N`, I was thinking about trying **Coppersmith's method** next, like in [Re:Small e on AlpacaHack](https://alpacahack.com/daily-bside/challenges/re-small-e?lang=en). Of course, just having `s^17 > N` does not mean Coppersmith will automatically work. We would need some extra structure or a sufficiently small unknown root. Luckily, this challenge was much simpler, and taking the integer root was enough lol.

Now we know the admin password. We still need to complete the authentication rounds.

## Passing the authentication

For each round, the server checks:

```text
response^e = announcement * pw_hash^challenge (mod N)
```

Since we know the secret `s`, we can answer correctly for any challenge.

First, choose a random integer `t` that is coprime to `N`, and send:

```text
announcement = t^e mod N
```

After receiving the challenge `c`, send:

```text
response = t * s^c mod N
```

This works because:

```text
response^e
= (t * s^c)^e
= t^e * (s^e)^c
= announcement * pw_hash^c  (mod N)
```

The server uses 52 rounds, so we repeat this 52 times. After the last round, we are logged in as admin and get `FLAG1`.

The core code is pretty short:

```python
for _ in range(52):
    while True:
        t = secrets.randbelow(N - 2) + 2
        if gcd(t, N) == 1:
            break

    announcement = pow(t, e, N)
    # Send announcement, then receive challenge c.
    response = t * pow(secret, c, N) % N
    # Send response.
```

## Solve

I ran the solver against the challenge server. Both attacks worked on the same connection.

```bash
$ python3 solver.py
[*] Connecting to challenge server
[+] Opening connection to 10.83.23.77 on port 1337: Done
[+] Connected: 10.83.23.77:1337
[+] N bits: 2674
[+] e: 17
[+] NLEN: 335

========== SOLVING FLAG0 ==========
[*] Constructing RSA hash collision
[+] Collision constructed
[+] Password length: 335
[+] Hash: 0x4dba402b8917770b...392fc994e9c5207dd1
[*] Registering 'attacker1'
Registered 'attacker1'.
[*] Registering 'attacker2'
ERROR: Something happened. It was probably a pentest. Have this for now:
PP{modulo_hashing_is_not_collision_resistant::Gn7KMhyEXCaq}
Registered 'attacker2'.
[+] FLAG0 collision triggered!
[FLAG0] PP{modulo_hashing_is_not_collision_resistant::Gn7KMhyEXCaq}

========== SOLVING FLAG1 ==========
[*] Starting admin authentication
[+] Admin hash: 0x2dc34b329e92d412...a1c20000
[*] Recovering admin secret using integer root
[+] Admin secret recovered!
[+] Secret hex: 267842c993a40a3ce30f307f6fd619b81205c2
[*] Completing 52 authentication rounds
[+] Round 01/52: challenge=15, verified
[+] Round 02/52: challenge=13, verified
[+] Round 03/52: challenge=13, verified
...
[+] Round 50/52: challenge=14, verified
[+] Round 51/52: challenge=4, verified
[+] Round 52/52: challenge=16, verified

========== FLAG1 RESULT ==========
Welcome, admin!
Here is your flag: PP{rsa_messages_need_to_be_sufficiently_large::OXmoSKqN3RR-}
[FLAG1] PP{rsa_messages_need_to_be_sufficiently_large::OXmoSKqN3RR-}

============================================================
                     FINAL RESULTS
============================================================
FLAG0: PP{modulo_hashing_is_not_collision_resistant::Gn7KMhyEXCaq}
FLAG1: PP{rsa_messages_need_to_be_sufficiently_large::OXmoSKqN3RR-}
============================================================
[*] Closed connection to 10.83.23.77 port 1337
```

I shortened the long RSA hashes and the middle rounds in this log. The actual solver completed all 52 rounds successfully.

## Result

Got both flags!

- **FLAG0:** `PP{modulo_hashing_is_not_collision_resistant::Gn7KMhyEXCaq}`
- **FLAG1:** `PP{rsa_messages_need_to_be_sufficiently_large::OXmoSKqN3RR-}`

The first flag is about modulo hashing not being collision resistant. The second one is about using a message that is too small with raw RSA. The flag names explain the bugs pretty well, lol.

## What I learned

The interesting point is that RSA itself is not broken here. The implementation uses raw RSA without hashing or padding, and the admin secret is too small for the public exponent.

Also, using `pow(password, e, N)` directly as a password hash is dangerous because different integers can have the same residue modulo `N`.

This was a fun challenge. Two flags, two different RSA mistakes, and no need for heavy crypto attacks :)
