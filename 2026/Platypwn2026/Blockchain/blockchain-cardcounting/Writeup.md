# Card Counting — Writeup

## First impression

When I opened the challenge files, the first things that caught my eye were `dealer.py` and `import random`.

This might be a bit of meta-reading, but they reminded me of **Gambler's Fallacy** from UofTCTF 2026. I had seen a similar idea in Crypto before, so I started wondering whether this was another Python PRNG prediction challenge, just with a blockchain frontend.

Reference: [UofTCTF 2026 — Gambler's Fallacy (solution.py)](https://github.com/UofTCTF/uoftctf-2026-chals-public/blob/main/gamblers-fallacy/solution/solution.py)

Then I checked the Solidity contracts. The goal was not to win a normal blackjack game, but to drain the dealer's casino balance:

```solidity
function isSolved() public view returns (bool) {
    return address(TARGET).balance < 10 ether;
}
```

The casino starts with 100 ETH. Considering this win condition and the Python `random` usage, predicting future PRNG outputs using **MT19937** seemed like a pretty reasonable attack path.

## Where the randomness leaks

The backend uses one `random.Random()` instance for both blackjack and roulette:

```python
rng = random.Random()

def deal_hand():
    number = rng.getrandbits(32)
    cards = []
    for _ in range(6):
        number, card = divmod(number, 52)
        cards.append(card)
    return cards

def spin_wheel():
    return rng.randrange(37)
```

This is the important part. Every blackjack hand consumes **one full 32-bit MT19937 output**, and then encodes it as six base-52 digits. The six cards look like game data, but actually leak the whole random number.

In `Chal.sol`, the cards are publicly accessible through `getHand(id)`, and also emitted in `HandDealt` events:

```solidity
event HandDealt(uint256 indexed id, address indexed player, uint8[6] cards, uint256 payout);
```

We can reconstruct the original number by reversing the base-52 conversion:

```python
def reconstruct(cards):
    n = 0
    for c in reversed(cards):
        n = n * 52 + int(c)
    return n
```

Python's MT19937 can be cloned from 624 consecutive 32-bit outputs. So I just needed to play 624 blackjack hands, collect the cards in order, and submit the reconstructed numbers to `randcrack`.

```python
from randcrack import RandCrack

rc = RandCrack()
for i in range(624):
    rc.submit(samples[i])
```

Once the state is recovered, the roulette is predictable too, because the dealer uses the **same RNG instance** for both games.

## Predicting roulette

One small detail: `randrange(37)` is not simply `getrandbits(32) % 37`. Python uses rejection sampling with six random bits here. We need to reproduce that behavior:

```python
def next_roulette(rc):
    while True:
        n = rc.predict_getrandbits(6)
        if n < 37:
            return n
```

The roulette contract accepts a bet on a number from 0 to 36, with a maximum bet of 0.5 ETH. A correct guess pays `36 * bet`, so a 0.5 ETH winning bet credits 18 ETH. We can call `cashOut()` to actually remove those funds from the casino. Just increasing `winnings` is not enough for the solve condition; the contract's ETH balance must go below 10 ETH.

Six correct spins were enough in my run.

## The annoying part: RPC performance

The first solver was painfully slow. It called `getHand(idx)` separately for every hand, and after only 80 recovered outputs I got:

```text
Recovered 16/624 PRNG outputs
Recovered 32/624 PRNG outputs
Recovered 48/624 PRNG outputs
Recovered 64/624 PRNG outputs
Recovered 80/624 PRNG outputs
ConnectionResetError: [Errno 54] Connection reset by peer
```

Not great when the instance only lives for 30 minutes, lol.

I changed the solver to queue hands in batches of 16 and collect the results using `HandDealt` logs instead of making hundreds of individual `getHand()` calls. I also added RPC retries and support for continuing from hands already queued in the same instance.

After that, it worked much better:

```text
02:58:14 INFO Queued 16 hands; total queued 624/624
02:58:15 INFO Fetching 624 outputs via HandDealt logs
02:58:47 INFO MT state recovered. Roulette begins
02:58:50 INFO WIN #1 number=2
02:59:00 INFO WIN #2 number=22
02:59:05 INFO WIN #3 number=5
02:59:10 INFO WIN #4 number=35
02:59:17 INFO WIN #5 number=33
02:59:23 INFO WIN #6 number=14
02:59:27 INFO isSolved=True balance=0.0 ETH
```

Finally, I selected option 3 in the challenge service and got the flag.

## Flag

```text
PP{c0unt1ng_tw1st3d_c4rds::DcgFauy-cfLb}
```

## Thoughts

I had solved MT19937 prediction problems in Crypto before, so the PRNG part itself was familiar. But I had never really written this kind of exploit against a Solidity contract, and that made it a bit tough for me. I had to deal with contract calls, transaction signing, events, the dealer's asynchronous settlement, and slow RPC communication at the same time.

In the end, the vulnerability was quite simple: **one game leaks the internal state of a PRNG, and another game trusts its future outputs**. The blockchain part did not make the randomness secure. It just made the exploit a little more troublesome to implement :)
