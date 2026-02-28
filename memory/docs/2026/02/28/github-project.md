## GitHub Project スキルの作成

### 背景
- GitHub Project の操作方法を文書化し、再利用可能にする

### 作成したスキル
**パス:** `skills/github-project/`

**含まれるファイル:**
- `SKILL.md` - スキル本体（コマンドリファレンス、ワークフローテンプレート）
- `references/field_ids.md` - ONIZUKA AGI Co. Prj のフィールドID一覧
- `scripts/add_tasks.py` - タスク一括追加スクリプト
- `scripts/update_status.py` - ステータス更新スクリプト

### 主な機能
- GitHub CLI (gh) によるProject操作
- カスタムフィールドの設定方法
- アイテムの追加・編集
- Start/Target dateの設定
- Priority/Sizeの設定
- Board View/Table Viewの活用
- 運用のベストプラクティス

### 使用方法
```bash
# Project一覧
gh project list --owner onizuka-agi-co

# アイテム一覧
gh project item-list 1 --owner onizuka-agi-co

# タスク一括追加
python3 skills/github-project/scripts/add_tasks.py \
  --project 1 --owner onizuka-agi-co --file tasks.json
```