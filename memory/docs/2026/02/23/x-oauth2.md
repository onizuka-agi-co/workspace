# X OAuth 2.0 認証

## 重要なポイント

1. **scopeに `tweet.read` が必須** - ないと `/2/users/me` が403
2. **verifier生成方法** - `+` と `/` を**削除**（空文字に置換）、長さ調整
3. **Pythonスクリプトで確実** - bashのcurlで何度も失敗したがPythonでは一発成功

## scope

```
tweet.read users.read tweet.write offline.access
```

## トークンファイル

- `x-tokens.json` - access_token, refresh_token
- `x-client-credentials.json` - client_id, client_secret

## トークン有効期限

- access_token: 2時間
- refresh_token: 6ヶ月

## 認証フロー（Python版）

```python
# PKCE生成
bytes_rand = secrets.token_bytes(48)
verifier = base64.b64encode(bytes_rand).decode('ascii').rstrip('=').replace('+', '').replace('/', '')
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')

# 認可URL
auth_url = f"https://x.com/i/oauth2/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}&state={STATE}&code_challenge={challenge}&code_challenge_method=S256"

# トークン交換
body = urllib.parse.urlencode({
    'grant_type': 'authorization_code',
    'code': code,
    'redirect_uri': REDIRECT_URI,
    'code_verifier': verifier
})
```

[← 戻る](./)
