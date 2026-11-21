# Cold Echo

![Cold Echo](./Cold%20Echo.png)

## 問題文

We lost the reactor's calibration profile after the cold-start test. We still have the test readings and the cold controller's signed receipt. Can you recover the profile that was signed?

## Archive

`archive.json` describes a polynomial `P` of exact degree `degree` over the prime field with modulus `prime`. The commissioning procedure normalized it to `P(1) = 1`.

- Each pair `[u, reading]` in `trace` records `reading = P(u) * P(u⁻¹) mod prime`, with the inverse taken in the field.
- The `forward` pair `[t, reading]` records `reading = P(t) mod prime`.
- `receipt_der_b64` is the Base64 encoding of an ASN.1 DER ECDSA signature. It uses P-256 with SHA-256 and verifies under `public_key_pem`.
- `flag_mask_b64` contains the masked flag body, encoded in Base64.

## Receipt format

Build the following ASCII message with single spaces and LF line endings. Every line, including the last, ends with LF. Write integers in decimal. Use the least nonnegative representative for each field value and omit leading zeroes. Write each trace pair as `u reading`.

Copy `batch` verbatim. Include all `degree + 1` coefficients in ascending power order, including zeros.

```text
GLACIER-COLD-ECHO-v1
<batch>
<prime> <degree>
<one line per trace pair, in file order>
<t> <forward reading>
<constant coefficient> <coefficient of X> ... <coefficient of X^degree>
```

## Flag

For the receipt message that verifies, decode `flag_mask_b64` and XOR it with the same number of bytes from the start of `SHA256(b"cold-echo-flag-pad-v1\n" + message)`. Encode the result as URL-safe Base64 without padding. Submit that string inside `gctf{...}`.
