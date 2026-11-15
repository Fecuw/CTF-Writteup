```
How it breaks

1. Calibration probes → rotation distances. Brute force over the 8 probes gives a unique fit: fold_word(x) = x ^ (rotl(x,5) & rotl(x,11)), walk_word(x) = rotl(x,7) (the "single rotation" is by 7, not 1).
2. The register is linear over GF(2). Each row is
   z_i = parity(fold_mask & fold_word(x_i)) ^ echo_i ^ pad[i mod 16],
   and since parity(m&u) ^ parity(m&v) = parity(m&(u^v)), the toggling echo collapses to echo_i = e0 ^ parity(walk_mask & C_i) with C_i the running XOR of walk words. That makes all 81 unknowns (32 + 32 + 1 + 16) linear in 160 equations — straight Gaussian elimination, no search.
3. The one ambiguity is resolved by the transcript. Flipping e0 and all 16 pad bits leaves every z unchanged, so the system is rank 80 on its own. The audit_tap at sample 0 (register_seed_contact_A, reported_bit: 1) pins pad[A] and makes the solve unique: rank 81, and the recovered state reproduces all 160 rows exactly.
4. The "refreshed key" claim is false. The 16 pad bits are the sifted key from the 16 key_tap samples, and they are what went into the seal. Material 1d0cc456:ccc78639:0:1010010010100001, keystream SHA256(material || counter_be32) for counter 0,1,… (verified against all three published compatibility vectors), XORed into sealed_flag.

The samples 16–23 (X/X basis with test_detector audits) and 24–39 (basis mismatch, discarded) are sifting noise — none of them contribute key bits.
```
