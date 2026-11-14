# Not My Type - Writeup

## Overview

This was a blockchain challenge about a payment service. The contract had 100 ETH, and the goal was to make its balance less than 80 ETH.

At first, the payment system looked normal. Users can deposit ETH, request transfers with strings like `"0.5"`, and withdraw their balance. The actual transfer is checked by a Python backend.

But I found a problem with how the backend converts numbers. Basically, it checks the amount using `int()` but actually transfers the money using `float()`. So we can create money from nothing.

## Looking at the code

In `Setup.sol`, the contract starts with 100 ETH:

```solidity
TARGET = new Chal{value: 100 ether}(msg.sender);
```

The solve condition is:

```solidity
return address(TARGET).balance < 80 ether;
```

So I needed to withdraw more than 20 ETH.

In `Chal.sol`, anyone can submit a transfer request:

```solidity
function transfer(address to, string calldata amount) external returns (uint256 id) {
    id = nextTransferId++;
    transfers[id] = Transfer(msg.sender, to, amount, false);
    emit TransferRequested(id, msg.sender, to, amount);
}
```

The backend later calls `settle()`. If it accepts the transfer, the contract subtracts the amount from the sender and adds it to the receiver.

```solidity
if (accepted) {
    balanceOf[t.from] -= int256(amountWei);
    balanceOf[t.to] += int256(amountWei);
}
```

The important part is that `balanceOf` uses `int256`, so it can also become negative.

## Finding the bug

I checked `payment_backend.py` and found this function:

```python
def check_transfer(balance: float, amount: str):
    try:
        value = float(amount)
    except ValueError:
        return None
    if not value > 0:
        return None
    try:
        if balance < int(value):
            return None
    except (ValueError, OverflowError):
        return None
    return value
```

The strange part is `int(value)`. For example:

```python
value = float('0.9999999999999999')
print(int(value))  # 0
```

Even if the sender has 0 ETH, the balance check becomes `0 < 0`, which is false. So the transfer is accepted.

Then the backend does this:

```python
amount_wei = int(value * 10**18) if accepted else 0
```

This converts our value into almost 1 ETH. So the sender gets a negative balance, but the receiver gets almost 1 ETH. There is no real deposit needed for that transfer.

## Exploit idea

I used the following amount:

```python
amount = '0.9999999999999999'
```

I created fresh accounts and sent a transfer request from each one to my main account. Each new account starts with zero balance in the contract, but the backend still accepts the request because `int(value)` is zero.

After the backend processes the requests, my main account gets almost 1 ETH each time. I can then call `withdraw()` to take real ETH from the contract.

I used 22 requests to get safely past the 20 ETH requirement. The fresh accounts needed a small amount of ETH for gas, so the solver funded them before submitting their requests.

## Running the solver

I wrote a Python script using `web3.py` and `eth_account`. It gets the challenge address from `Setup.TARGET()`, creates new accounts, submits the transfer requests, waits for the backend, and withdraws the balance.

There was also a small problem during the exploit. The RPC connection sometimes disconnected, so my first runs stopped in the middle. I changed the script to count already submitted transfers and continue from there, instead of starting everything again.

For example, after some transfers were already processed, the script showed:

```text
Contract ETH: 100; already withdrawn: 0
Existing: balance=6.999999999999999104 ETH, pending=0, processed=7
Additional transfer requests needed: 15
```

It then submitted the remaining 15 requests. So in total, there were 22 requests.

After that, I connected to the challenge service again and selected option `3`. The service returned the flag, so the exploit worked.

## Flag

```text
PP{n0t_my_typ3_0f_m0n3y::BKPBU2BiLgZi}
```

## Conclusion

The bug was not really in the Solidity transfer function alone. The bigger problem was the mismatch between the Python backend's balance check and the actual amount it sends to the contract.

Using `int(value)` for validation but `int(value * 10**18)` for settlement lets a value below 1 ETH pass the zero-balance check. And because the contract allows negative internal balances, the backend can credit our account without any deposit.

Basically, mixing `float`, `int`, and money was a bad idea here. A pretty simple type conversion mistake, but it was enough to drain ETH from the contract.
