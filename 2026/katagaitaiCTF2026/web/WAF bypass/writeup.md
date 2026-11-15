# Writeup
uoftCTF2026のfirewallっぽい問題 \
受け取る側を細かく刻めば良さそう
```bash
╭─ /Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/web/waf_source(pwn)
╰─ (*'-') < python3 solver.py 
[+] Found marker at byte 0
[+] Recovering flag...
[*] 9-11: b'is '
[*] 12-14: b'kat'
[*] 15-17: b'aga'
[*] 18-20: b'ita'
[*] 21-23: b'i-C'
[*] 24-26: b'TF{'
[*] 27-29: b'waf'
[*] 30-32: b'_ce'
[*] 33-35: b'nso'
[*] 36-38: b'red'
[*] 39-41: b'_th'
[*] 42-44: b'e_f'
[*] 45-47: b'lag'
[*] 48-50: b'!}\n'

[+] FLAG: katagaitai-CTF{waf_censored_the_flag!}
```

# flag
```
katagaitai-CTF{waf_censored_the_flag!}
```