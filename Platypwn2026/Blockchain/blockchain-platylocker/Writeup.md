# PlatyLocker - Writeup

## Overview

This was a blockchain challenge about recovering an AES key from RSA-encrypted data.

The story is a ransomware contract which asks for 1000 ETH before releasing a file key. At first, it looked like we needed to break RSA to get the AES key. But actually, the RSA private exponent was stored in the contract storage. Since Ethereum storage is public, we can just read it directly. No need to factor the RSA modulus or do any complicated crypto attack.

## Looking at the contract

After launching the instance, we got an RPC endpoint, a private key for sending transactions, and the Setup contract address.

Reading `Setup.sol`, it deploys `Chal` and provides `TARGET()` to find its address. The solve condition is simply `TARGET.filesRestored()`.

In `Chal.sol`, I found these functions:

```solidity
uint256 public constant RANSOM = 1000 ether;
bytes private privateExponent;

function payRansom() external payable returns (bytes32 key) {
    require(msg.value >= RANSOM, "Pay up");
    key = _decrypt();
    emit KeyReleased(msg.sender, key);
}

function restoreFiles(bytes32 key) external {
    require(keccak256(abi.encodePacked(key)) == keyHash, "Wrong key");
    filesRestored = true;
}
```

Normally, `payRansom()` requires 1000 ETH to release the AES key. But `restoreFiles()` only checks the key hash. There is no payment check there. So if we can recover the key by ourselves, we can just call `restoreFiles()` without paying.

I also checked `locker_operator.py`. It generates a fresh 1024-bit RSA key pair and a random 32-byte AES key for each instance, then calls:

```python
chal.functions.initialize(
    to_bytes(n), e.to_bytes(3, "big"), to_bytes(d), to_bytes(c), Web3.keccak(aes_key)
)
```

Here, `c = pow(int.from_bytes(aes_key, "big"), e, n)`. The important thing is that **the operator sends `d`, the RSA private exponent, into the contract**. In `initialize()`, the contract stores it as `privateExponent = d`.

So our goal was to find the correct 32-byte AES key and pass it to `restoreFiles()`.

So our goal was to find the correct 32-byte AES key and pass it to `restoreFiles()`.

## Reading the RSA private key

The interesting part was the Solidity storage layout. The RSA parameters and encrypted AES key were stored as `bytes` values:

| Storage slot | Value |
| --- | --- |
| `0` | RSA modulus `n` |
| `1` | RSA public exponent `e` |
| `2` | RSA private exponent `d` |
| `3` | RSA-encrypted AES key `c` |

Solidity stores long `bytes` values differently from short ones. For long values, the original slot stores `length * 2 + 1`, and the actual data starts at `keccak256(slot)`.

We can read this with `eth_getStorageAt`, which is available through `web3.py`:

```python
def read_storage_bytes(w3, address, slot):
    raw = bytes(w3.eth.get_storage_at(address, slot))
    header = int.from_bytes(raw, "big")

    if header & 1 == 0:
        length = (header & 0xff) // 2
        return raw[:length]

    length = header // 2
    base = int.from_bytes(Web3.keccak(slot.to_bytes(32, "big")), "big")

    data = bytearray()
    for i in range((length + 31) // 32):
        data.extend(w3.eth.get_storage_at(address, (base + i) % (1 << 256)))

    return bytes(data[:length])
```

The script successfully recovered the RSA parameters, including the private exponent:

```text
RSA modulus: 1024 bits
RSA public exponent: 65537
RSA private exponent: 1022 bits
RSA ciphertext: 1023 bits
```

This is the main vulnerability. The word `private` looks safe at first, but it only prevents normal Solidity code in other contracts from directly accessing that variable. It does not hide the storage from RPC reads.

Also, `initialize()` checks `msg.sender == operator`, but that only limits who can write the key data. It cannot stop us from reading it. So we do not need to bypass `only operator` or attack the RSA algorithm.

## Recovering the AES key

Now that we have `n`, `d`, and the ciphertext `c`, RSA decryption is straightforward:

```python
m = pow(c, d, n)
aes_key = m.to_bytes(32, "big")
```

The recovered key was:

```text
fb154c05165207eb4566a39e6bfd1648d9a5af1c87c045c1e5e24277710336e1
```

To make sure it was correct, I compared `keccak256(aes_key)` with the value returned by `keyHash()`.

```python
expected_hash = bytes(chal.functions.keyHash().call())
actual_hash = bytes(Web3.keccak(aes_key))
assert expected_hash == actual_hash
```

Both hashes matched, so the key recovery worked.

## Restoring the files

Since `restoreFiles()` does not require a ransom payment, I called it directly with the recovered AES key. The script built and signed the transaction using the instance's provided account.

```python
tx = chal.functions.restoreFiles(aes_key).build_transaction({
    "from": account.address,
    "nonce": w3.eth.get_transaction_count(account.address),
    "chainId": w3.eth.chain_id,
    "gas": 200000,
    "gasPrice": w3.eth.gas_price,
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
```

The transaction succeeded, and `isSolved()` returned `True`.

```text
Transaction status: 1
FILES RESTORED: True
[+] CHALLENGE SOLVED!
```

Then I connected to the challenge service again and selected option `3` to get the flag.

## Flag

```text
PP{pr1v4t3_15_n0t_s3cr3t::kR5NW_q_JwdV}
```

## Conclusion

The important thing here was not RSA itself, but how the private key was stored. `locker_operator.py` actually puts the private exponent into the contract during initialization, and `Chal.sol` keeps it in a `private bytes` variable. The contract kept the RSA private exponent in public blockchain storage, so anyone could recover it and decrypt the AES key.

Basically, `private` in Solidity only restricts access from other contracts at the language level. It does not hide data from people reading the chain. Pretty simple mistake, but it completely breaks the encryption in this challenge.
