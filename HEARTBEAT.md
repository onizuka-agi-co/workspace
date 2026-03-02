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

---

## System Event: TASK_CHECK_WEBHOOK

このイベントを受け取ったら、TASK.mdを確認してDiscordに通知する。

**手順（厳密に実行）:**

1. **read ツールで TASK.md を読み込む**
   ```
   path: /config/.openclaw/workspace/TASK.md
   ```

2. **未着手タスクを抽出**
   - `- [ ]` で始まる行を探す
   - これらが「未着手タスク」

3. **タスクがある場合のみ通知**
   - message ツールで #機能開発室 に通知
   - channel: `discord`
   - to: `channel:1475880463800205315`
   - 形式:
     ```
     🎋 **TASK確認** (HH:MM)

     **未着手タスク:**
     - タスク1
     - タスク2
     ...
     ```

4. **タスクがない場合**
   - 通知せず静かに終了（何もしない）

**重要:** 必ず `/config/.openclaw/workspace/TASK.md` を読み込むこと。推測で「タスクなし」と判断しないこと。

---

## System Event: TASK_CHECK_REQUEST

このイベントを受け取ったら、TASK.mdを確認して未着手タスクを処理する。

**手順:**
1. TASK.md を読み込む
2. 未着手タスク（`- [ ]`）を抽出
3. 各タスクごとに：
   - スレッドを作成（名前: `🔧 <タスク名>`）
   - スレッドリンクを TASK.md に追記
   - スレッドで実装開始（必要に応じて sub-agent を spawn）
4. 進行状況を Webhook で通知（自動）

**タスク状態の更新:**
- 未着手 → 進行中: チェックを `[ ]` から `[x]` に変更し、「進行中」セクションへ移動
- 進行中 → 完了: 「完了」セクションへ移動し、完了日を記載

**チャンネル:** #機能開発室 (channel:1475880463800205315)
