# 2026-02-25

## 完了
- [x] daily-memoryスキルのテスト
- [x] OpenClaw Skills調査
- [x] Discordスラッシュコマンドの表示・認可・タイムアウト問題を解消
- [x] Kimi CLI が非rootユーザーで使えない問題を修正
- [x] Nested Sub-Agents（オーケストレーターパターン）実験
- [x] X Filtered Stream + Discord Webhook統合システム構築
- [x] X Read Skill改良 - メディア保存機能追加

## 進行中
- [ ] 

## 気づき
- Discordのスキルコマンド名は `-` が `_` に正規化される（例: `daily-memory` → `/daily_memory`）
- DM pairingで通っても、Guild slash認可は `channels.discord.allowFrom` を別参照している
- `/tmp/jiti` のroot所有キャッシュ混在で OpenClaw Gateway のプラグイン読み込みが `EACCES` になることがある
- Kimi CLI を `/root/.local` 配下に入れると非rootユーザーでは実行できない
- Discord WebhookからのメッセージはBotとして扱われるため、`allowBots: true` が必要
- X Filtered StreamはBasic Tierで最大1接続、Pro Tierで最大5接続
- `tweet` コマンドで画像・動画を自動保存するように改良（APIのexpansionsパラメータが必要）

## 詳細

- [テスト](./test)
- [OpenClaw Skills 調査](./openclaw-skills)
- [Kimi CLI 修正](./kimi-cli)
- [Nested Sub-Agents 実験](./nested-sub-agents-experiment)
- [X Filtered Stream 構築](./x-filtered-stream)
- [X Read Skill 改良](./x-read-skill)

[← 戻る](../)
