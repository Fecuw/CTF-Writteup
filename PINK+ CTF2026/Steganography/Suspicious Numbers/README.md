# Suspicious Numbers

![alt](./img/スクリーンショット%202026-11-07%203.28.01.png)

謎の数字群すぎる

一応factordbかけるか

![alt](./img/スクリーンショット%202026-11-11%200.11.30.png)
![alt](./img/スクリーンショット%202026-11-11%200.11.54.png)


もしかして大きめのGCDある？？？

![alt](./img/スクリーンショット%202026-11-11%200.13.08.png)

あっ...

```bash
╭─ /Users/mionorn124/Desktop/CTF-Writteup/PINK+ CTF2026/Steganography/Suspicious Numbers
╰─ (*'-') < cat div_leet.py
num="120330 70861 21392 70861 21392 62839 100275 113645 8022 1337 17381 5348 26740 123004 45458 52143 10696 123004 25403 136374 98938 13370 98938 120330 70861 9359 141722 9359 10696 98938"
num_split = [int(x) for x in num.split()]
result = [x // 1337 for x in num_split]
print(result)

╭─ /Users/mionorn124/Desktop/CTF-Writteup/PINK+ CTF2026/Steganography/Suspicious Numbers
╰─ (*'-') < python3 div_leet.py
[90, 53, 16, 53, 16, 47, 75, 85, 6, 1, 13, 4, 20, 92, 34, 39, 8, 92, 19, 102, 74, 10, 74, 90, 53, 7, 106, 7, 8, 74]
╭─ /Users/mionorn124/Desktop/CTF-Writteup/PINK+ CTF2026/Steganography/Suspicious Numbers
╰─ (*'-') < 
```

閾値的にはasciiっぽいけど、asciiにしては```{}```がないし、問題文の書き方的にこれ自体が意味の通る文章っぽい

となると100程度しかなくてありそうなのは元素表？

変換していく

```
ThISISAgReAtCHAlBeCaUSeYOUKNoWNeWThINSgNOW
```




# flag
```
PINK{ThISISAgReAtCHAlBeCaUSeYOUKNoWNeWThINSgNOW}
```