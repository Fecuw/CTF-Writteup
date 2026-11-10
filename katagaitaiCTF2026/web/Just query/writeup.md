# Writeup
"Just SELECT flag" — the `?query=` parameter runs our SQL directly on the `flags` table. So first I just try the obvious one.

```
/sqli/step1.php?query=select * from flags
```

It returns a huge list of fake flags. The annoying part is they all look almost the same but the letter case is different, like:

```
kAtagAital-ctF{lorem_ipsum_dolor}
kataGaiTAi-cTf{labore_aute_excepteur}
KatagaITAi-ctf{elit_occaecat_labore}
...
```

The real flag format is exactly `katagaitai-CTF`, with that exact case. SQL string compare is case-insensitive by default, so `where flag_text like 'katagaitai-CTF%'` still matches all the junk. So instead I just dump everything and do a **case-sensitive** search on the page.

Open the browser devtools and search the response for `katagaitai-CTF` (case sensitive). Only the real one matches:

```
katagaitai-CTF{just_random_words}
```

(You can also do it in SQL with a binary/case-sensitive compare, but ctrl+F on the raw HTML is faster.)

# flag
```
katagaitai-CTF{just_random_words}
```
