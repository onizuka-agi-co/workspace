# 2026-02-23

## 完了
- [x] Claude Code + GLM設定
- [x] X API スキル作成（x-read / x-write / x-community）
- [x] X OAuth 2.0 認証フロー完成
- [x] UV インストール
- [x] X コミュニティ投稿機能実装

## 気づき
- X OAuth 2.0 のscopeには `tweet.read` が必須
- PKCE verifierは `+` と `/` を削除して生成
- X API: `community_id` と `quote_tweet_id` の併用は403エラー
- コミュニティ投稿は `share_with_followers: true` が推奨

## 詳細

### [Claude Code + GLM 設定](./claude-code-glm)
GLM (z.ai) 経由でClaude Codeを使用するための設定。`~/.bashrc` に永続化済み。`pty:true` 必須、Gitディレクトリ必須などの重要なパターンを記録。

### [X API スキル作成](./x-api-skills)
OpenClaw用のX APIスキルを作成。x-read（読み込み専用）、x-write（書き込み専用）を配置。UVを使用して実行。

### [X OAuth 2.0 認証](./x-oauth2)
X OAuth 2.0 の認証フロー。PKCE生成方法、scope設定、トークン有効期限などを記録。Pythonスクリプトで確実に認証成功。

### [UV インストール](./uv-install)
PythonパッケージマネージャーUVをインストール。`~/.local/bin/` に配置。

### [X コミュニティ投稿スキル](./x-community)
コミュニティ投稿専用スキル。`community_id` と `quote_tweet_id` の併用は403エラーになる重要な制限を発見。テンプレート機能あり。

### [テスト済み一覧](./tested)
Claude Code、GLM接続、X OAuth認証、X投稿、コミュニティ投稿などのテスト完了項目。
