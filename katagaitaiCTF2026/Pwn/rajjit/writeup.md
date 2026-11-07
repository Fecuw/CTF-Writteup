# Writeup
方針
JITの即値領域をシェルコードとして実行させ、flagを読み取ることを考える

具体的な方針
1. 257文字の数式を入力して、entry の下位1バイトを上書きする。
2. entry をJITコードの先頭ではなく、0x2b～0x39 のいずれかに変更する。
3. mov rcx, imm64 の即値領域に、実行可能なx86-64命令を配置する。
4. JITコードの途中から実行し、flagファイルを開いて標準出力に表示する

execve("/bin//sh", NULL, NULL)を変換するまではいいが、JITコンパイラがシェルコード片の間に自動挿入する命令を飛び越える魏つ用がある。そのため末尾に即値jmp命令を置くことでそれらを飛ばして任意コード実行を試みる。

```bash
╭─ /Users/mionorn124(pwn)
╰─ (*'-') < python3 solve.py                                 
[-] Attempt 10: b'expr> compile error\n'
[-] Attempt 20: b'expr> compile error\n'
[+] Shell obtained on attempt 23
expr> __SHELL_OK__
uid=1000(ubuntu) gid=1000(ubuntu) groups=1000(ubuntu)
katagaitaiCTF{h0pp1ng_thr0ugh_j1t_c0mp1l3d_1mm3d14t3s}
/app/flag.txt
/proc/kpageflags
```
# flag
```
katagaitaiCTF{h0pp1ng_thr0ugh_j1t_c0mp1l3d_1mm3d14t3s}
```