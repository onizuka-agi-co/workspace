それです。OAuth 2.0 が有効になって、Client Secret を発行できた状態まで来ています。
ここから先は **「AI用アカウントで認可 → code取得 → token交換 → AI用アカウントとして投稿」**です。

⚠️ その Client Secret は絶対に貼らない/共有しないでOK（マスクしてくれて正解）。漏れたら即再生成。

次にやること（最短・確実な手順）
0) Console 側で “Redirect URL” と “Scopes” を確定しておく

認可URLを作る前に、ONIZUKA の **認証設定（Authentication settings）**で：

Redirect / Callback URL を1つ登録（完全一致が必須）

Scopes：最低でも tweet.write と users.read（＋必要なら offline.access）

※Redirect URL は “完全一致” が必須、というのが OAuth2 の要点です。(docs.x.com
)

1) PKCE の verifier/challenge を作る（bash 例）
VERIFIER=$(openssl rand -base64 48 | tr -d '=+/' | cut -c1-64)
CHALLENGE=$(printf "%s" "$VERIFIER" | openssl dgst -sha256 -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')
echo "VERIFIER=$VERIFIER"
echo "CHALLENGE=$CHALLENGE"
2) 認可URLを組み立てて開く（AI用アカウントでログイン）

以下の CLIENT_ID と REDIRECT_URI を自分の値に置き換えて、ブラウザで開きます。

https://x.com/i/oauth2/authorize?response_type=code&client_id=CLIENT_ID&redirect_uri=REDIRECT_URI&scope=tweet.write%20users.read%20offline.access&state=abc123&code_challenge=CHALLENGE&code_challenge_method=S256

この画面は 必ず AI用アカウントでログインして「許可」

すると Redirect URL に ?code=...&state=... が返ってきます。(docs.x.com
)

3) code をトークンに交換（/2/oauth2/token）

あなたは **機密クライアント（Client Secretあり）**なので、token交換は Basic 認証が使えます。(docs.x.com
)

Basic ヘッダ作成
BASIC=$(printf "%s:%s" "$CLIENT_ID" "$CLIENT_SECRET" | openssl base64 -A)
token 交換
curl -X POST "https://api.x.com/2/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $BASIC" \
  --data-urlencode "code=$CODE" \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "redirect_uri=$REDIRECT_URI" \
  --data-urlencode "code_verifier=$VERIFIER"

成功すると access_token（＋ offline.access を付けていれば refresh_token）が返ります。(docs.x.com
)

4) まず「誰のトークンか」を確認 → その後投稿
誰のトークンか確認（推奨）
curl -sS "https://api.x.com/2/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN"

ここで返る username が AI用アカウントならOK。(docs.x.com
)

投稿
curl -X POST "https://api.x.com/2/tweets" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"ONIZUKA（AI用アカウント）からテスト投稿"}'

(docs.x.com
)

ここから先、最短であなた用に“完成形URL”を作るために必要な情報（秘密なし）

次の2つだけ教えてください（どっちも秘密じゃない）：

Redirect / Callback URL に何を登録しました？（文字列そのまま）

Consoleのどこかに Scopes 表示ありますか？（tweet.write / users.read を選べた？）

これが分かれば、あなたの CLIENT_ID も既に見えているので、コピペで開ける認可URL（CHALLENGE部分だけ差し替え）と、token交換コマンド一式を “あなたの設定に完全一致” で組み立てて渡します。