# MEMORY.md - 長期記憶（概要）

詳細は各日付のVitePressドキュメントを参照してください。

---

## 2026-02-28

### 🔗 生ログ
→ [memory/docs/2026/02/28/](memory/docs/2026/02/28/)

### 概要
- **nano-banana-2 スキル作成** - fal.ai画像生成スキル
- **GitHub Project スキル作成** - gh CLIでProject操作
- **タスク管理移行** - TASK.md → GitHub Project
- **secret scan導入検討** - gitleaksで15個のリーク検出

### 作成したスキル
- `skills/nano-banana-2/` - fal.ai画像生成
- `skills/github-project/` - GitHub Project管理

### 修正内容
- `generate.py` のバグ修正（`/status` エンドポイント使用、202ステータス対応）
- コミット: `0017194`, `da3500e`

### 重要な学び
- gitleaksでワークスペースをスキャン → 15個の機密情報リーク検出
  - X API認証情報、Gemini APIキーなど
  - `.gitignore`で機密ファイルを除外する必要がある
- OpenClawのcronよりs6サービスの方が安定動作

---

## 2026-02-25

### 🔗 生ログ
→ [memory/docs/2026/02/25/](memory/docs/2026/02/25/)

### 概要
- **定期アイデア提案システム構築** - cron + system-event + main session
- **idea-dev スキル作成** - メンション時の現状把握用
- **Discord Webhook設定** - Secretary 🔔 朱燈烏
- **X Filtered Stream + Discord Webhook統合** - ツイート検知→通知→解説の自動化

### 作成したスキル
- `skills/idea-dev/` - 新規企画開発コンサルティング
- `skills/x-stream/` - X Filtered Stream監視

### cronジョブ
- `日次アイデア提案（朝・夜）` - 毎日 0:00 / 12:00 (Asia/Tokyo)
- system-event: `IDEA_PROPOSAL_REQUEST`
- HEARTBEAT.mdに処理手順を記載

### 重要な学び
- Discord WebhookからのメッセージはBotとして扱われる → `allowBots: true` が必要
- X Filtered StreamはBasic Tierで最大1接続、Pro Tierで最大5接続

---

## 2026-02-23

### 🔗 生ログ
→ [memory/docs/2026/02/23/](memory/docs/2026/02/23/)

### 概要
- **Claude Code + GLM設定** - GLM経由でClaude Codeを使用可能に
- **X API スキル作成** - x-read / x-write / x-community / x-community-quote スキル作成
- **X OAuth 2.0 認証** - Pythonスクリプトで認証フロー完成
- **UV インストール** - Pythonパッケージマネージャー導入
- **X コミュニティ投稿機能** - community_id パラメータでコミュニティに投稿

### 作成したスキル
- `skills/x-read/` - X API読み込み専用
- `skills/x-write/` - X API書き込み専用
- `skills/x-community/` - コミュニティ投稿専用
- `skills/x-community-quote/` - 引用解説コミュニティ投稿

### 重要な学び
- X OAuth 2.0 のscopeには `tweet.read` が必須
- PKCE verifierは `+` と `/` を削除して生成
- スキルは `<workspace>/skills/` に配置（最高優先）
- **X API制限:** `community_id` と `quote_tweet_id` の併用は403エラー
  - 引用リツイートしたい場合は URL をテキストに含める形で対応
- コミュニティ投稿は `share_with_followers: true` が推奨（フォロワーにも表示）

### コミュニティID
- デフォルト: `2010195061309587967`

---

## 📁 メモリーシステム構造

```
memory/
├── README.md
├── docs/
│   ├── YYYY/MM/DD/
│   │   ├── index.md      # 日報サマリー
│   │   └── topic.md      # トピック別詳細
│   └── notes/            # 随時メモ
```

---

_定期的に見直して、古い情報は削除・更新すること_
