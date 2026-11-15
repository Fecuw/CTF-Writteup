# i am scared — Writeup

**Category:** Misc / Crypto  
**Points:** 100  
**Author:** pr4njal

## Solve

We were given a bunch of numbers like `839[6]`, `479[8]`, and `317[1]`, with `<cant_find_letter>` between some groups.

The format looked like an index cipher: find entry number `839`, then take the character at index `6`. Since the flag format is `d4rk{...}`, the first four entries should probably decode to `d4rk`.

But what are these numbers indexing? The challenge title was **i am scared**, and the numbers went up to around 1000. I couldn't really identify the source just from that. But from the hint of emoji, it looked like SCP Foundations, since SCPs are horror-related and identified by numbers.

I checked the SCP Series 1 titles using zero-based character indexes, and the first four entries gave `d4rk`. That confirmed the idea. Applying the same method to the rest gave the flag. The `<cant_find_letter>` markers were the `{`, `}`, and `_` separators.


## Flag

`d4rk{SCpS_Ar3_sCary_0r_th3y_JuST_w4nna_l1ve?}`
