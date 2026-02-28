# HEARTBEAT.md

# Keep this file empty (or with only comments) to skip heartbeat API calls.

# Add tasks below when you want the agent to check something periodically.

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

---

## System Event: IDEA_PROPOSAL_REQUEST

このイベントを受け取ったら、日付ごとのスレッドを作成してアイデアを提案する。

**手順:**
1. 今日の日付（YYYY-MM-DD）を取得
2. `🎋 YYYY-MM-DD アイデア提案` という名前のスレッドを作成
   - 同じ名前のスレッドが既にある場合は、そのスレッドに追記
3. スレッドに以下のアイデアを投稿：

**【短期アイデア】**（1-3個）
- 数時間〜1日で完了可能
- 形式：アイデア名 + 一文説明

**【中期アイデア】**（1-2個）
- 1-2週間で完了可能
- 形式：アイデア名 + 概要（2-3文）

**【長期アイデア】**（1個）
- 1-3ヶ月で完了可能
- 形式：プロジェクト名 + ビジョン

**現在の状況：**
- X API スキル完成（x-read, x-write, x-community）
- コミュニティ投稿可能
- Claude Code + GLM連携済み

**活動領域：**
- 📜 @hAru_mAki_ch の投稿を深掘り・補足解説
- 📰 最新AGI論文の要約・解説
- 🔓 知見を整理して公開

**チャンネル:** #新規企画開発 (channel:1475861389984796702)
