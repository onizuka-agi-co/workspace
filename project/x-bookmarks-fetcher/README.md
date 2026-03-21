# X Bookmarks Fetcher

X のブックマークを取得するための小さい Python CLI です。

- OAuth 2.0 PKCE でユーザーアクセストークンを発行して取得
- OAuth 1.0a の `API Key/Secret + Access Token/Secret` が揃っている場合も取得可能
- ページネーションを辿って JSON に保存可能
- フォルダ一覧と特定ブックマークフォルダの中身も取得可能
- ブックマーク削除も可能
- 監視して Discord Webhook へ通知可能

## 置き場所

```text
futodama-config/.openclaw/workspace/project/x-bookmarks-fetcher
```

## ファイル

- `bookmarks_cli.py`: CLI 本体
- `config.env.example`: 設定テンプレート
- `config.env`: ローカル設定ファイル（Git 追跡外）
- `.x-user-token.json`: OAuth 2.0 の取得済みトークン（Git 追跡外）
- `.bookmark-monitor-state.json`: 監視用のスナップショット state（Git 追跡外）

## セットアップ

```bash
cd /prj/ai-agent-desktop-ubuntu/futodama-config/.openclaw/workspace/project/x-bookmarks-fetcher
cp config.env.example config.env
# config.env を編集
```

依存関係は `pyproject.toml` に入れてあるので、`uv` があればそのまま実行できます。

## 重要な前提

ブックマーク取得は app-only の Bearer Token ではなく、ユーザー文脈の認証が必要です。
そのため、次のどちらかで実行します。

1. OAuth 2.0 PKCE
   - 必要: `X_CLIENT_ID`
   - 推奨: `X_CLIENT_SECRET`
   - 必要: Developer Console に登録済みの Redirect URI
   - 必要スコープ: `tweet.read users.read bookmark.read`（`offline.access` は自動更新用）
2. OAuth 1.0a
   - 必要: `X_API_KEY`
   - 必要: `X_API_KEY_SECRET`
   - 必要: `X_OAUTH1_ACCESS_TOKEN`
   - 必要: `X_OAUTH1_ACCESS_TOKEN_SECRET`

アプリ権限は少なくとも `読む` が必要です。OAuth 1.0a で投稿系も使うなら `読み取りと書き込み` 以上にしてください。

## OAuth 2.0 でログインしてから取得

Redirect URI は X Developer Console に登録してあるものと完全一致させてください。

```bash
uv run python bookmarks_cli.py login --redirect-uri http://localhost:8080/callback
uv run python bookmarks_cli.py fetch --output bookmarks.json
```

件数制限を付ける例:

```bash
uv run python bookmarks_cli.py fetch --limit 200 --output output/bookmarks.json
```

フォルダ一覧:

```bash
uv run python bookmarks_cli.py list-folders --output output/bookmark-folders.json
```

特定フォルダの中身:

```bash
uv run python bookmarks_cli.py fetch-folder --folder-id 2026593501866242363 --output output/folder-2026593501866242363.json
```

ブックマーク削除:

```bash
uv run python bookmarks_cli.py delete-bookmark --tweet-id 2026418435408986423 --output output/delete-2026418435408986423.json
```

全ブックマーク監視:

```bash
uv run python bookmarks_cli.py watch --once
uv run python bookmarks_cli.py watch --interval 300
```

特定フォルダだけ監視:

```bash
uv run python bookmarks_cli.py watch --folder-id 2026593501866242363 --interval 300
```

既定の監視対象フォルダを固定したい場合は `config.env` に以下を入れます。

```dotenv
X_BOOKMARKS_MONITOR_FOLDER_ID=2026593501866242363
```

初回から既存ブックマークも通知したい場合:

```bash
uv run python bookmarks_cli.py watch --notify-existing --once
```

## すでに OAuth 2.0 ユーザートークンがある場合

`config.env` に以下を入れれば `login` を飛ばせます。

```dotenv
X_USER_ACCESS_TOKEN=...
X_USER_REFRESH_TOKEN=...
```

そのまま実行します。

```bash
uv run python bookmarks_cli.py fetch --output bookmarks.json
```

## OAuth 1.0a で直接取得する場合

```dotenv
X_API_KEY=...
X_API_KEY_SECRET=...
X_OAUTH1_ACCESS_TOKEN=...
X_OAUTH1_ACCESS_TOKEN_SECRET=...
```

```bash
uv run python bookmarks_cli.py fetch --output bookmarks.json
```

## 出力形式

`fetch` と `fetch-folder` は次のような JSON を返します。

- `user`: 認証されたユーザー情報
- `count`: 取得したブックマーク件数
- `pages_fetched`: API から取得したページ数
- `bookmarks`: 投稿一覧
- `includes`: 展開されたユーザー・メディア情報
- `rate_limit`: 最終レスポンス時点のレート制限情報

`list-folders` は `folders` 配列を返します。

`watch` は state file に前回の bookmark ID 一覧を保存し、新規 ID だけ Discord Webhook に投稿します。
初回実行は既定で通知せず、スナップショットだけ保存します。

## 補足

- `config.env` と `.x-user-token.json` は `.gitignore` に入れてあります。
- `DISCORD_WEBHOOK_URL` は `config.env` にだけ保存してください。
- `X_BEARER_TOKEN` は public な読み取り用途には使えますが、ブックマーク取得には使いません。
