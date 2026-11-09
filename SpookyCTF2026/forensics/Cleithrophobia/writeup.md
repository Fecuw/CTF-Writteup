# Writeup
We get a pcap (`Cleithrophobia.pcap`). Open it in Wireshark and follow the HTTP stream.

There's an HTTP `200 OK` response whose custom headers carry the flag, split into three base64 parts:

```
Content-Type: text/plain
X-Bridge-Telemetry: deflector_part1=U3Bvb2t5e0JlMA==
X-Deflector-Status: deflector_part2=bV9NZV9VcF9TYw==
X-Warp-Core-Reading: deflector_part3=MHR0eV8yMjY2fQ==

IGNITION AUTHORIZED - WARP CORE PREPARING
```

Just concatenate part1 + part2 + part3 and base64-decode the whole thing (CyberChef "From Base64" works too):

```python
import base64
parts = ["U3Bvb2t5e0JlMA==","bV9NZV9VcF9TYw==","MHR0eV8yMjY2fQ=="]
print(b"".join(base64.b64decode(p) for p in parts).decode())
# Spooky{Be0m_Me_Up_Sc0tty_2266}
```

# flag
```
Spooky{Be0m_Me_Up_Sc0tty_2266}
```
