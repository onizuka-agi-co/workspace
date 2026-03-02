# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

---

## Secretary Bot - 定期タスク管理

定期タスクは **secretary-bot** がYAMLファイルで管理しています。

**設定ファイル:**
- `/config/.openclaw/workspace/project/secretary-bot/config/schedule-tasks.yaml` - スケジュール定義
- `/config/.openclaw/workspace/project/secretary-bot/config/tasks/` - 個別タスク定義

**現在のタスク:**

| タスク名 | スケジュール | チャンネル | 定義ファイル |
|---------|-------------|-----------|-------------|
| タスク確認 | 毎時 | #機能開発室 | task-check.yaml |
| 朝のアイデア提案 | 毎日 09:00 | #新規企画開発 | morning-idea.yaml |
| 夜の振り返り | 毎日 21:00 | #機能開発室 | evening-review.yaml |

**タスク定義の変更方法:**
1. `config/tasks/*.yaml` を編集
2. `config/schedule-tasks.yaml` でスケジュール調整
3. コミットして変更を保存

**GitHub:** https://github.com/onizuka-agi-co/secretary-bot
