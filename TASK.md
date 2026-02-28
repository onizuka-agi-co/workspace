# TASK.md - 進行中タスク

> **GitHub Project に移行しました**
> 📋 https://github.com/orgs/onizuka-agi-co/projects/1

---

## 🔧 リポジトリ展開

### 概要
ONIZUKA AGI Co. のリソースをGitHubリポジトリとして公開・管理する。

---

## 📁 リポジトリ構成

### 1. `onizuka-agi-co/skills`
現在の `workspace/skills/` をそのままリポジトリ化

**追跡対象:** `*.md` ファイルのみ

**含まれるスキル:**
- `x-read/` — X API読み込み
- `x-write/` — X API書き込み
- `x-community/` — コミュニティ投稿
- `x-stream/` — Filtered Stream監視
- `gemini-vision/` — Gemini Vision API
- `glm-code/` — Claude Code via GLM
- `google-browse/` — Google検索・ブラウズ
- `idea-dev/` — 新規企画開発
- `sunwood-community/` — Sunwood Community投稿
- `daily-memory/` — 日報管理
- `futodama-s6-service/` — Futodama S6 Service

---

### 2. `onizuka-agi-co/workspace`
現在の `workspace/` をそのままリポジトリ化

**追跡対象:** `*.md` ファイルのみ

**含まれるファイル:**
- `AGENTS.md` — エージェント設定
- `SOUL.md` — 魂・人格設定
- `IDENTITY.md` — アイデンティティ
- `MEMORY.md` — 長期記憶
- `USER.md` — ユーザー情報
- `HEARTBEAT.md` — 定期タスク指示
- `TOOLS.md` — ツール設定
- `memory/` — 日次ログ

---

## 🔒 .gitignore 設定

```gitignore
# 基本すべて無視
*

# ただし md ファイルは追跡
!*.md
!**/*.md

# ディレクトリ構造を維持
!*/
```

---

## ⚠️ 重要な注意点

**コミット前に必ず確認:**
1. `*-tokens.json` — アクセストークン
2. `*-credentials.json` — client_id/secret
3. `.env` 系ファイル
4. APIキーを含むスクリプト
5. 個人情報・機密データ

**確認コマンド:**
```bash
git diff --staged  # ステージングされた変更を確認
git log -p         # コミット履歴を確認
```

---

_タスク管理は GitHub Project に移行しました_

_更新日: 2026-02-27_
