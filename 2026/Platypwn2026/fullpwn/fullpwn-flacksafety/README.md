# Backups — FLAG_1 Writeup

> Five backups down, one ancient remote still standing.
>
> This writeup covers **only the path to FLAG_1**. The old legacy rclone remote and FLAG_2 are not solved here.

## The idea

The challenge was basically asking us to destroy several copies of the same footage. Sounds easy until you realize the copies are spread across different storage backends, and some of them are protected by things like root permissions, append-only storage, and S3 Object Lock.

My first thought was to figure out **what was backing up what**, rather than randomly deleting files. If a cron job keeps uploading the footage every minute, deleting a repository once might not be enough. Also, the different backends clearly needed different approaches.
## 0. What's the passphrase of employee?
I saw shadow.txt. It looked like /etc/shadow
```
employee:$argon2id$v=19$m=65536,t=3,p=1$NDY5NGRkNzY0MGY3MjI2MTk5NzRjMGI0NmU5ZTI1M2E$eEtk1leqd2ihD8UXpy3T7nX1edPWc7QNsxTwQCYhVGc
```
employee's password hash is eEtk1leqd2ihD8UXpy3T7nX1edPWc7QNsxTwQCYhVGc and use salts as NDY5NGRkNzY0MGY3MjI2MTk5NzRjMGI0NmU5ZTI1M2E.

so, I cracked this using Seclist.

this is solver.
```python
#!/usr/bin/env python3
import sys
import time
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError

HASH_FILE = sys.argv[1]
WORDLIST = sys.argv[2]

with open(HASH_FILE, encoding="utf-8") as f:
    line = f.readline().strip()

hash_value = line.split(":", 1)[-1]

ph = PasswordHasher()

count = 0
start = time.time()

with open(WORDLIST, "rb") as f:
    for raw in f:
        password = raw.rstrip(b"\r\n")

        try:
            if ph.verify(hash_value, password):
                print(f"\n[+] FOUND: {password!r}")
                sys.exit(0)
        except VerifyMismatchError:
            pass
        except VerificationError as e:
            print(f"[!] Hash verification error: {e}")
            sys.exit(1)

        count += 1

        if count % 1000 == 0:
            elapsed = time.time() - start
            print(
                f"\r[*] {count:,} tested "
                f"({count / elapsed:.2f} H/s)",
                end="",
                flush=True,
            )

print("\n[-] Password not found")
```

```bash 
python3 crack.py \
  ~/Downloads/fullpwn-flacksafety/shadow.txt \
  /opt/SecLists/Passwords/Common-Credentials/10-million-password-list-top-1000000.txt

  [+] FOUND: b'iloveme'
  ```

```iloveme``` is password for employee.

## 1. Recon: where are the backups?

I started on the backup workstation and checked the resticprofile configuration:

```bash
cat /etc/resticprofile/profiles.yaml
cat /etc/crontab
ps -o pid,ppid,user,args
```

The configuration showed that all the backup profiles inherited the same source directory, `/home/employee/footage`, with the snapshot host set to `workstation`.

| Profile | Repository |
| --- | --- |
| `local-user` | `local:/home/employee/backups` |
| `local-root` | `local:/backups` |
| `offsite` | `rest:http://backups-server:8001/footage` |
| `rclone` | `rest:http://backups-server:8000/workstation/footage` |
| `s3` | `s3:http://backups-server:7070/footage` |

The repository encryption password was configured as `RESTIC_PASSWORD=flack-footage`. This is **not** the same thing as HTTP Basic Auth for the REST endpoints.

Then the cron configuration explained why the backups kept coming back:

```cron
* * * * * su -l employee -c 'resticprofile local-user.backup'
* * * * * resticprofile root.backup
```

So there were two jobs every minute: a user-level backup and a root-level backup group. The root group included the local-root, offsite, rclone, and S3 profiles. I also saw `supercronic` and running `resticprofile` / `restic` processes, so this wasn't just a stale config file.

**Takeaway:** before deleting anything, I needed to understand the scheduled jobs and the backend-specific rules.

## 2. Local backups: the tmux mistake

The user-owned backup was the straightforward part. The root-owned repository under `/backups` was more interesting, because the normal `employee` account shouldn't be able to remove it.

While checking running processes and `/tmp`, I noticed a tmux server running a shell as root, with a socket under:

```text
/tmp/tmux-1000/default
```

The tmux socket was accessible from the workstation account. Attaching to that existing session gave me a root shell — I confirmed it with `id` (`uid=0`).

That changed the local part of the challenge completely. Instead of trying to exploit restic itself, I could operate on the root-owned local backup with root privileges. I removed the relevant local repositories and checked the challenge status.

The interesting bug here wasn't some fancy memory corruption. It was a **privileged interactive session exposed through a reachable tmux socket**. A root shell is still a root shell, even if someone left it inside tmux.

## 3. Rclone Remote 1: an accessible REST repository

Next was the regular rclone REST backup:

```text
http://backups-server:8000/workstation/footage
```

The important detail was that this was the **current workstation's** repository, not the separate legacy repository. The backup process had the relevant REST credentials in its environment, and I used those to work with the accessible repository.

Once I had the correct authenticated endpoint, I deleted the files belonging to Rclone Remote 1 and verified that the checker marked it as destroyed.

At this point I deliberately kept the two rclone targets separate in my notes:

- `workstation` / Rclone Remote 1: accessible with the current workstation's credentials.
- `workstation-legacy` / Old Rclone Remote: a different, protected repository. **Not solved as part of FLAG_1.**

Having a password for one repository doesn't automatically mean you have access to another one, especially when the server is using private repositories.

## 4. Offsite: let the retention policy do the deleting

This one was my favorite part.

The offsite repository lived behind the service on port `8001`, which was configured in append-only mode. Directly deleting old backup objects was therefore not the right approach.

Instead of fighting the deletion restriction head-on, I looked at the **backup lifecycle**. The offsite side had a retention/pruning workflow using:

```bash
restic forget --keep-last 2 --prune
```

The trick was to change what the repository considered worth keeping:

1. Move the original footage out of the backed-up source path.
2. Create new, clean snapshots under the expected host, `workstation`.
3. Let the retention job keep the newest two snapshots and prune the older ones containing the original footage.
4. Check whether the offsite layer was now considered destroyed.

In other words, I didn't need permission to delete the protected backup objects directly. I could influence **which snapshots survived the server's own cleanup policy**.

That is a nice example of a security boundary that looks strong at the storage-operation level but becomes weaker when you consider the surrounding automation. Append-only upload permissions don't necessarily protect old data if the trusted server later prunes it based on attacker-influenced snapshot history.

## 5. S3 Governance: retention is not always immutable

The S3 layer was backed by an S3-compatible service on port `7070`:

```text
http://backups-server:7070/footage
```

The first thing to recognize was that this wasn't just an ordinary S3 bucket. The challenge used **Object Lock in Governance mode**. A normal delete can fail even when the caller has otherwise valid S3 credentials.

But Governance mode is not the same as Compliance mode. With sufficient permissions, a caller can explicitly request a governance-retention bypass.

The key operation was an S3 delete with:

```text
x-amz-bypass-governance-retention: true
```

Or, with a compatible S3 client, the corresponding option:

```bash
--bypass-governance-retention
```

I used the S3 credentials available to the backup process and deleted the protected objects using the governance bypass. After clearing the S3 layer, the checker reported **S3 Governance: destroyed**.

The lesson here is pretty simple: **Governance mode is an administrative safeguard, not an absolute WORM guarantee**. If the same credential set can both operate on the bucket and bypass retention, the backup can still be deleted.

## 6. Checking the result

After working through the different layers, the checker showed:

| Layer | Status |
| --- | --- |
| User Local | Destroyed |
| Root Local | Destroyed |
| Offsite Replica | Destroyed |
| Rclone Remote 1 | Destroyed |
| S3 Governance | Destroyed |
| Old Rclone Remote | Intact |

That was enough for the first flag:

```text
PP{g0v3rn4nc3_41nt_s4f3::KPYbec8oWXWd}
```

## What I learned

I initially expected a challenge about breaking one backup tool. It turned out to be more about **how several reasonable-looking backup controls interact**.

- A root-owned repository isn't safe if an accessible tmux session hands out a root shell.
- A protected REST endpoint is only as useful as its authentication and repository separation.
- Append-only storage doesn't help much if an automated retention policy can be manipulated into pruning the data.
- S3 Object Lock **Governance** mode can be bypassed by a sufficiently privileged caller; it shouldn't be confused with **Compliance** mode.
- And, seriously, check the cron jobs. Otherwise your deleted backups might just reappear a minute later.

The final legacy rclone repository was still intact, so this was **FLAG_1, not a full solve**. That last layer is a separate problem.

---

### Notes on reproducibility

This is a narrative writeup reconstructed from the investigation notes, configuration output, and observed checker results. It preserves the confirmed attack ideas and outcomes, but it is **not** a byte-for-byte terminal transcript. In particular, I have not invented exact deletion commands, object keys, or tmux interaction keystrokes where the original command history wasn't available.
