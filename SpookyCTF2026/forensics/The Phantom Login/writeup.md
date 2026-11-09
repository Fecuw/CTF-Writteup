# Writeup
`Phantom_Login.zip` unzips to `njit_web.log`, a web access log. We have to find the phantom (attacker) in it.

Most entries are internal `10.13.x.x` IPs hitting normal paths. Scanning through, one line stands out: an external IP, a weird path, and a base64-looking query string:

```
2026-10-31T03:19:08Z src=203.0.113.77 user=evelyn.graves "GET /archives/export?note=c3Bvb2t5e3RoZV9naG9zdF9sZWZ0X2FfdHJhY2V9 HTTP/1.1" status=200
```

The `note=` value is base64, so decode it:

```python
import base64
print(base64.b64decode("c3Bvb2t5e3RoZV9naG9zdF9sZWZ0X2FfdHJhY2V9").decode())
# spooky{the_ghost_left_a_trace}
```

# flag
```
spooky{the_ghost_left_a_trace}
```
