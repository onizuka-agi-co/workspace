## 背景
メンションで定期的にミッションに基づいたアイデアを提案してほしいという要望。

## 検討した方法
1. **OpenClaw cron (isolated session)** — スレッド作成の権限で失敗
2. **OpenClaw cron (main session + system-event)** — 動作確認済み
3. **Webhook + メンション** — テスト済み

## 最終構成
- OpenClaw cron → system-event → main session
- main session → 日付ごとのスレッド作成・アイデア投稿
- スケジュール: 毎日 0:00 / 12:00 (Asia/Tokyo)

## 提案されたアイデア
- 短期: arXiv日本語要約Bot, 投稿タグ付けシステム
- 中期: 週刊AGIダイジェスト, arXiv論文要約パイプライン
- 長期: AGI Knowledge Hub, AGIタイムライン