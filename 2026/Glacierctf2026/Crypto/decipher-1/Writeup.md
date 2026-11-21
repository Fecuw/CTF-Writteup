# Decipher (Stage 1 & 2) — Writeup

## flag

```
Stage 1: gctf{who_need5_th3_k3y_if_y0u_c4n_g3t_th3_pla1n73x7}
Stage 2: gctf{gaus5_and_g41oi5_to_7h3_re5cue}
```

## 問題の概要

AES もどきのブロック暗号 `decipher.py` と、生成スクリプトが2つ。

- `gen_stage1.py`：ランダムな平文 16 個を暗号化し、さらに `flag_key` を同じ暗号で暗号化（wrap）。flag は `flag_key` で AES-GCM
- `gen_stage2.py`：同じく 16 組の平文・暗号文。ただし flag の鍵は `sha256(round_keys)` なので、**本当に鍵を復元する必要がある**

`output_stageN.npz` には `plaintexts`, `ciphertexts`, `proofs`, `flag`（stage1 は `wrapped_key` も）が入っている。

暗号自体は AES-128 から

- **S-box が独自**（ラウンドでも鍵スケジュールでも使う）
- 全ラウンドで `AddRoundKey → SubBytes → ShiftRows → MixColumns`（最終ラウンドの特別扱いなし）、最後にラウンド鍵を XOR

に変えたもの。

Stage 2 で鍵が必要になるので、最初から **鍵復元** を目標にした（そうすれば両方解ける）。

## 着眼点① proofs が何を漏らしているか

暗号化中、各ラウンドの前の内部状態が保存されていて、

```python
second_order_proofs = proofs[:, None] ^ proofs[None, :]
```

が公開されている。つまり `proofs[i, j, r]` は「暗号化 i と j のラウンド r での状態の XOR」。

状態そのものは見えないが差分は見える。これが結構強い。

- `proofs[0, j, r]` は ラウンド r の S-box 層への **入力差分**（鍵は XOR で消える）
- `proofs[0, j, r+1]` から MixColumns と ShiftRows を逆にかけると、同じ S-box 層の **出力差分**

なので各ラウンド・各バイトで `S(u) ^ S(u ^ δ_j) = Δ_j` という式が 15 本ずつ手に入る（`u` は暗号化 0 の未知バイト）。

## 着眼点② S-box がほぼ線形

S-box が独自な時点で怪しいので、差分特性を眺めた。
「全ての x で `S(x) ^ S(x ^ a)` が一定になる a」を数えると

```python
V = [0] + [a for a in range(1, 256)
           if len({SBOX[x] ^ SBOX[x ^ a] for x in range(256)}) == 1]
assert len(V) == 64
```

**64 個**あり、しかも GF(2)^8 の 6 次元部分空間になっていた。
つまりこの S-box は V 方向には線形で、非線形性は商空間 GF(2)^8 / V の **2bit 分しかない**。

V に直交するマスク `m1, m2` を取って 2bit の射影

```
π(x) = (parity(m1 & x), parity(m2 & x))
```

を定義すると、

```
S(x) = L(x) ^ T[π(x)]     （L は 8×8 線形写像、T は 4 要素の表）
```

と分解できる（ソルバ内で全 x について assert 済み）。

→ **全 S-box 入力の π さえ分かれば、暗号全体が鍵について affine になる**。

## π をどう知るか

着眼点①の差分の式を使う。各ラウンド・各バイトで u を 256 通り試して、15 本の差分と矛盾しないものを残す。

```python
cs = [u for u in range(256)
      if all(SBOX[u ^ pr[0, j, r, b]] ^ SBOX[u] == Ds[j][b] for j in range(1, 16))]
```

候補は1つに絞れない（`u ^ v`, `v ∈ V` も同じ差分になる）が、`π(v) = 0` なので **候補全部で π(u) は同じ**。欲しいのは π だけなのでこれで十分。

暗号化 n の S-box 入力は `u ^ proofs[0, n, r, b]` なので、その π も分かる。
→ 16 本全ての暗号化の全 S-box について π が判明。

## GF(2) の連立方程式にする

未知数:

- 元の鍵 128bit
- 鍵スケジュールの S-box（10 回の SubWord で 40 個）は π が分からないので、それぞれ `p1, p2, q = p1·p2` を変数にする。`T[π]` は

  ```
  T[p1,p2] = T[0,0] ^ p1·(T[1,0]^T[0,0]) ^ p2·(T[0,1]^T[0,0]) ^ q·(T[0,0]^T[1,0]^T[0,1]^T[1,1])
  ```

  と線形に書ける

合計 `128 + 40·3 = 248` 変数。

式:

1. 鍵スケジュール：各 S-box で `π(入力) = (p1, p2)`
2. 暗号化：各ラウンド・各バイトで `π(state ^ rk) = 既知の値`、S-box 出力は `L(state ^ rk) ^ T[既知のπ]` で affine。ShiftRows/MixColumns も線形なので状態はずっと affine のまま
3. 最後の状態 ^ `rk[10]` = 実際の暗号文（1 組あたり 128 本）

式は Python の int をビットマスクとして持ち、ガウスの消去法をかけると

```
rank 248 of 248
```

**フルランク → 鍵が一意に決まる**。

## flag を取る

- Stage 1：復元した鍵で `wrapped_key` を復号 → `flag_key` → AES-GCM 復号
- Stage 2：ラウンド鍵を作り直して `sha256(round_keys)` で AES-GCM 復号

```
$ python solve.py .
decomposition ok
rank 248 of 248
stage 1 key fc417d0d233a97a57521f12792672e88
gctf{who_need5_th3_k3y_if_y0u_c4n_g3t_th3_pla1n73x7}
rank 248 of 248
stage 2 key 2f3762f3f277d89957613a661802dd5c
gctf{gaus5_and_g41oi5_to_7h3_re5cue}
```

念のため 16 組の平文を再暗号化して一致することも確認した。

（Stage 1 は wrap された鍵も「平文が知りたい暗号化の1つ」なので、鍵なしでも解けたかもしれない。ただ鍵復元すれば両方一気に解ける）

## 振り返り

- 独自 S-box が出てきたらまず差分分布・線形構造を確認する
- この S-box は「差分が一定になる 64 元の部分空間」を持っていて、実質 1 バイトあたり 2bit しか非線形じゃなかった
- proofs がちょうどその 2bit を漏らしているので、AES が GF(2) の線形方程式に落ちる。Stage 2 の flag 通り「Gauss と Galois が助けてくれる」

ソルバ: [`solve.py`](./solve.py)（`python solve.py <challenge_dir>`、`numpy` と `cryptography` が必要）
