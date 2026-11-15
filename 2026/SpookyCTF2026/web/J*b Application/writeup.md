# Writeup
配布ファイルを読むと制限は最初の文字列を見て判定してるらしい
```python
if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        address = request.form.get("address", "").strip()
        position = request.form.get("position", "").strip()
        coverletter = request.form.get("coverletter", "").strip()
        resume = request.files.get("resume")
```   
```python
valid_letter = re.match(
            r"^[A-Za-z0-9 .,!?'-]{1,40}",
            coverletter
        )

        if not valid_letter:
            flash("Your cover letter contains invalid characters.")
            return redirect(url_for("index"))

        if "[[AI-REVIEW: ACCEPT]]" in coverletter:
            session["accepted"] = True
            return redirect(url_for("accepted"))
```   
```python
@app.route("/accepted")
def accepted():
    if not session.get("accepted"):
        return redirect(url_for("rejected"))

    return render_template("application-accepted.html", flag=FLAG)
```

最初に入れるcoverletterに[[AI-REVIEW: ACCEPT]]があればflagが取れることがわかる

ここでvalid_letterをみると、rematchで先頭判定をしているため、最初に文字列として適当なものを入れればこのマッチ判定はパスできる

```
例: A[[AI-REVIEW: ACCEPT]]
```

ということでこれを入れる
![alt](./img/スクリーンショット%202026-11-07%2013.44.13.png)
![alt](./img/スクリーンショット%202026-11-07%2013.43.23.png)

flagが得られた
# flag
```
spooky{10v3_ai&job_4pplic4t10ns}
```