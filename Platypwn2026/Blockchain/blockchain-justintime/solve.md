# solve
```bash
─ /Users/mionorn124
╰─ (*'-') < nc 10.83.0.212 31337
1 - launch new instance
2 - kill instance
3 - get flag
action? 1
1
deploying setup

your private blockchain has been deployed
it will automatically terminate in 30 minutes
here's some useful information
uuid:           9a676093-b62f-4054-ba6a-fb484e5ccbed
rpc endpoint:   http://10.83.0.212:8545/9a676093-b62f-4054-ba6a-fb484e5ccbed
private key:    0x6845027a2c10ce77ddc8306c8df0efeece39a6614f474ee8841055e571bce45f
your address:   0x275adCE5791A61e30503bCBF60db9c2068AA131c
setup contract: 0x4574719d7F8BEEa05A8F7E79094e1041E08434eC

╭─ /Users/mionorn124
╰─ (*'-') < cd Downloads/blockchain-justintime
╭─ /Users/mionorn124
╰─ (*'-') < rm -rf solver.py
╭─ /Users/mionorn124
╰─ (*'-') < vim solver.sage
╭─ /Users/mionorn124
╰─ (*'-') < cd Downloads/blockchain-justintime
╭─ /Users/mionorn124/Downloads/blockchain-justintime
╰─ (*'-') < rm -rf solver.py
╭─ /Users/mionorn124/Downloads/blockchain-justintime
╰─ (*'-') < vim solver.py
╭─ /Users/mionorn124/Downloads/blockchain-justintime
╰─ (*'-') < conda acto
usage: conda [-h] [-v] [--no-plugins] [-V] COMMAND ...
conda: error: argument COMMAND: invalid choice: 'acto' (choose from activate, build, clean, commands, compare, config, content-trust, convert, create, deactivate, debug, develop, doctor, env, export, index, info, init, inspect, install, list, menuinst, metapackage, notices, pack, package, remove, rename, render, repo, repoquery, run, search, server, skeleton, token, tos, uninstall, update, upgrade)
╭─ /Users/mionorn124/Downloads/blockchain-justintime
╰─ (*'-') <
╭─ /Users/mionorn124/Downloads/blockchain-justintime
╰─ (*'-') < conda activate pwn
╭─ /Users/mionorn124/Downloads/blockchain-justintime(pwn)
╰─ (*'-') < python3 solver.py
[+] Player: 0x275adCE5791A61e30503bCBF60db9c2068AA131c
[+] Setup: 0x4574719d7F8BEEa05A8F7E79094e1041E08434eC
[+] Chal: 0xe95b308EC293F861D9e0B22cf33cBF4D774bdc83
[+] Balance: 100 ETH
[+] Deployment block: 2
[+] Timestamp: 1794589785
[+] Password: 52635545700545010668511226670600577053473789290140292979744023357912244776494
[+] Password verified
[+] Transaction: 41ebb700069664ed56ed3b045335c5b1c2a39575bcfc59b2c317b1f03c8bdce9
[+] Receipt status: 1
[+] Solved: True
[+] Remaining balance: 0 ETH
╭─ /Users/mionorn124/Downloads/blockchain-justintime(pwn)
╰─ (*'-') < nc 10.83.0.212 31337
1 - launch new instance
2 - kill instance
3 - get flag
action? 3
3
PP{t1m3_15_n0t_4_s3cr3t::-xyKhdTOyOB3}
```
