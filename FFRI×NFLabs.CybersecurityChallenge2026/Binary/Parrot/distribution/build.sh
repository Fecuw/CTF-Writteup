#!/usr/bin/env bash
gcc -m32 parrot.c -o parrot -O0 -no-pie -fno-omit-frame-pointer -fstack-protector-all -Wl,-z,relro,-z,now