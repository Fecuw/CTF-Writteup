# Writeup
とりあえずcurlしてみる
```bash
╭─ /Users/mionorn124/Desktop/CTF-Writteup
╰─ (*'-') < curl http://web.katagaitai-ctf.net/http/step2.php                                            
<!DOCTYPE html>
<html>

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HTTP World Pt.2</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>

<body class="bg-black min-h-screen flex items-center justify-center">
    <div class="text-center p-8 bg-gray-900 rounded-lg shadow-xl border border-green-500 max-w-2xl w-full mx-4">
        <h1 class="text-4xl font-mono text-green-500 mb-8">
            Welcome to the HTTP World! ...again
        </h1>
        <p class="text-gray-300 text-xl font-mono">
            The flag is missing, again.
        </p>
    </div>
</body>

</html>


```
ない \
こういうときはじっちゃんがヘッダー見たほうがいいっていってた

```bash
╭─ /Users/mionorn124/Desktop/CTF-Writteup
╰─ (*'-') < curl -I http://web.katagaitai-ctf.net/http/step2.php
HTTP/1.1 200 OK
Server: nginx/1.27.3
Date: Sat, 07 Nov 2026 09:25:27 GMT
Content-Type: text/html; charset=UTF-8
Connection: keep-alive
X-Powered-By: PHP/8.5.12
X-Katagaitai-Flag: katagaitai-CTF{head_header_headest}
```
あった

# flag
```
katagaitai-CTF{head_header_headest}
```