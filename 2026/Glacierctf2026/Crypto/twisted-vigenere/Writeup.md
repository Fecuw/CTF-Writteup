# Twisted Vigenere — Writeup

## flag

```
gctf{from_rand0m_!mpor+_n0+_s0_r4nd0m_af+3r_al1}
```

## 問題

```python
vigenere = Vigenere(flag)          # key = flag の繰り返し XOR
pt = random.randbytes(2536)        # Python の random（MT19937）
ct = vigenere.encrypt(pt)
```

`base64(ct)` だけが渡される。鍵が flag そのもの。

## 最初に考えたこと

普通の Vigenère なら平文の頻度分析で鍵長→鍵を当てるが、平文が **ランダムバイト** なので頻度分析は使えない。

じゃあ平文側に何か構造はないか？と見ると、`random.randbytes` は **Mersenne Twister**。
MT19937 は内部状態の更新も出力の tempering も **GF(2) 上で線形**。
「平文が線形な関係式を満たす」→「暗号文 XOR 鍵 が線形な関係を満たす」→ **鍵ビットについての連立一次方程式** が立つのでは？と考えた。

## 方程式を立てる

### randbytes の中身

`randbytes(n)` は `getrandbits(8n).to_bytes(n, 'little')` なので、
2536 バイト = **32bit 出力 634 個**（リトルエンディアン）。

### MT の漸化式

MT の状態は 624 ワード。625 個目以降の出力は、untemper した値 `x[i]` に対して必ず

```
x[n+624] = x[n+397] ^ (z >> 1) ^ (MAG if z & 1 else 0)
z        = (x[n] & 0x80000000) | (x[n+1] & 0x7fffffff)
```

を満たす。untemper・シフト・マスク・「下位ビットが 1 なら MAG を XOR」はどれも GF(2) 線形。

### 鍵だけの式にする

`y[j] = ct_word[j] ^ key_word[j]` を代入すると、MT の状態は消えて **未知数は鍵のビットだけ** になる。
634 − 624 = 10 本の関係 × 32bit = **320 本の式**。

### 追加の拘束

- flag なので `gctf{` で始まり `}` で終わる
- 各バイトは ASCII なので最上位ビットは 0

## 鍵長が分からない問題

鍵長 `L` は総当たりする。各 `L` で `8L` ビットの未知数に対してガウスの消去法をかけ、

- 矛盾したら → その `L` は違う
- 矛盾しなければ → 自由変数を列挙

とすれば良い。実際やってみると `L ≤ 47` は全部矛盾、**`L = 48` だけ解がある**。

…が、この時点では自由変数が 21bit 残って、末尾 3 バイト（`af+3r_???`）が決まらなかった。

## もう一押し：最初の twist

あと 31 本くらい式が欲しい。どこから持ってくるか考えた。

`os.urandom` で seed した直後の `Random()` は、最初の出力時にちょうど twist する。
最初の twist で最後のワードを作るときは、**更新後の** `x[0]` を使う:

```
x[623] = x[396] ^ f( top(old_mt[623]) | low31(x[0]) )
```

未知なのは `old_mt[623]` の最上位 1bit だけで、これは結果の bit 30 にしか効かない。
→ 残り **31 本の式** が追加で取れる。
（19937bit の状態から 19968bit 出すので、余次元 31 の拘束がある、という話とも合う）

これを加えると `L = 48` で **自由変数 0、解が一意** に決まった。

```
[+] key length 48 consistent, 0 free bits
    gctf{from_rand0m_!mpor+_n0+_s0_r4nd0m_af+3r_al1}
```

## 検証

暗号文を復元した鍵で XOR → 最初の 624 ワードを untemper → `random.Random().setstate(...)` に流し込み、
624〜633 ワード目を予測すると、10 個すべて復号結果と一致した。

## 振り返り

- 「平文がランダム」でも、そのランダムが **線形な PRNG** なら構造として使える
- MT の漸化式に `ct ^ key` を代入すると状態が消えて鍵だけの線形系になる
- 足りない式は「seed 直後は twist 境界から始まる」という細かい性質から拾えた

ソルバ: [`solver.py`](./solver.py)（`python3 solver.py [output.txt]`）
