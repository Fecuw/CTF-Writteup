# Message from miku

- **CTF:** h4ckc0nCTF 2026
- **Category:** General
- **Points:** 367
- **Author:** berrchalant_
- **URL:** http://4.187.169.60:39393/

## Description

> A fan site for a certain teal-haired virtual idol went live last night, and
> it's been broadcasting something strange ever since. Everything looks ordinary
> on the surface, but the site is hiding more than it shows. Look closer, and see
> what's been left behind. Not everything on this page is meant for visitors.
>
> Flag: `d4rk{<put the message in here>}`

## Flag

```
d4rk{M1KU_G0T_C4UGHT_US1NG_0P1UM_4ND_M3T4M3T4PH1N3}
```

## Recon

The site is a single-page Hatsune Miku "digital stage". Viewing the HTML source
turns up **three** `d4rk{...}`-looking strings, so most are decoys:

| Location | Value | Verdict |
|---|---|---|
| `#tx` readout row | `d4rk{TX_0039_A}` | decoy |
| `#site-metadata` JSON | `d4rk{d0nt_t3ll_th3_p0l1c3_p75}` | decoy (thematic red herring) |
| `data-morse` on the "Tune in" button | encoded Morse | **real payload** |

The hint *"Not everything on this page is meant for visitors"* points at the
hidden transmission wired to the **"Tune in"** button, which stores a Morse
sequence in a `data-morse` attribute and plays it back as 700 Hz beeps:

```html
<button class="tune-button" id="tune-button" type="button"
  data-morse="--.. .---- -..- .... ..--.- - ----- --. ..--.- .--. ....- ....
              - ..- --. ..--.- .... ..-. .---- .- - ..--.- ----- -.-. .---- ....
              --.. ..--.- ....- .- --.- ..--.- --.. ...-- --. ....- --.. ...--
              --. ....- -.-. ..- .---- .- ...--"
  aria-label="Play hidden Morse transmission">
```

## Step 1 — Decode the Morse

`..--.-` is the Morse code for underscore. Decoding the full sequence:

```python
m = "--.. .---- -..- .... ..--.- - ----- --. ..--.- .--. ....- .... - ..- --. ..--.- .... ..-. .---- .- - ..--.- ----- -.-. .---- .... --.. ..--.- ....- .- --.- ..--.- --.. ...-- --. ....- --.. ...-- --. ....- -.-. ..- .---- .- ...--"
# -> Z1XH_T0G_P4HTUG_HF1AT_0C1HZ_4AQ_Z3G4Z3G4CU1A3
```

Result: `Z1XH_T0G_P4HTUG_HF1AT_0C1HZ_4AQ_Z3G4Z3G4CU1A3` 
Umm... use Carsar for now　becouse it has no hint.

## Step 2 — Caesar / ROT13

Brute-forcing all 25 Caesar shifts over the letters and go with the one that makes sense :

```python
s = "Z1XH_T0G_P4HTUG_HF1AT_0C1HZ_4AQ_Z3G4Z3G4CU1A3"
# -> M1KU_G0T_C4UGHT_US1NG_0P1UM_4ND_M3T4M3T4PH1N3
```

## Step 3 — Read the leetspeak

`M1KU_G0T_C4UGHT_US1NG_0P1UM_4ND_M3T4M3T4PH1N3`
= **"MIKU GOT CAUGHT USING OPIUM AND METAMETHAMPHETAMINE"**


```
d4rk{M1KU_G0T_C4UGHT_US1NG_0P1UM_4ND_M3T4M3T4PH1N3}
```

## Takeaways

- Always read the full page source — flags hide in attributes (`data-*`),
  inline JSON, and comments, not just visible text.
- Expect decoys; verify which string is the intended flag.
- `..--.-` = `_` is a common Morse gotcha in CTFs.
- Scrambled-but-structured plaintext → try a Caesar/ROT13 sweep first.
