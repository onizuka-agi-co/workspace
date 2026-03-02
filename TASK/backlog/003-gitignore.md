# .gitignore 設定

## ステータス
- [ ] 未着手

## 概要
両リポジトリで `*.md` ファイルのみを追跡するよう .gitignore を設定する。

## 詳細
```gitignore
# 基本すべて無視
*

# ただし md ファイルは追跡
!*.md
!**/*.md

# ディレクトリ構造を維持
!*/
```

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

## 関連
- タスク 001-skills-repo.md
- タスク 002-workspace-repo.md
