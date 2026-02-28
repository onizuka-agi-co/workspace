# OpenClaw Skills 調査

## 概要

OpenClawのSkills機能について調査・検証。

## 調査内容

### Skillsとは
- エージェントに「ツールの使い方」を教える仕組み
- AgentSkills仕様に準拠
- SKILL.mdファイルで定義

### 配置場所と優先順位
| 場所 | 優先度 |
|------|--------|
| `<workspace>/skills` | 最高 |
| `~/.openclaw/skills` | 中 |
| bundled skills | 最低 |

### スラッシュコマンド登録
- `user-invocable: true`（デフォルト）で自動登録
- `command-dispatch: tool` でモデルをバイパス
- Discord/Telegramで自動有効

### ClawHub
- スキルマーケットプレイス: https://clawhub.ai
- `clawhub install <slug>` でインストール
- `clawhub publish` で公開

## 検証結果

### 成功
- `/gemini_vision` コマンド動作確認
- `/daily_memory` コマンド動作確認
- `daily-memory` / `idea-dev` を Discord スラッシュコマンドから実行可能に修正
- `openclaw gateway restart` のコンテナ環境フォールバックで再起動確認

### 発見した問題
- Discordスキルコマンド名はハイフンではなくアンダースコアに正規化される
- DiscordのGlobal command反映に時間差がある（Guild commandではなくGlobal登録）
- `/tmp/jiti` にroot所有キャッシュが混在すると、Gatewayのプラグイン読み込みが `EACCES` で失敗し、Discordで「アプリケーションが応答しませんでした」になる
- DM pairingで許可されても、Guild slash認可は `channels.discord.allowFrom` を参照するため、通常チャットでは `You are not authorized to use this command.` になることがある
- 追加の `@openclaw/discord` プラグインを入れると bundled `discord` と重複して warning が出る

## Discord スラッシュコマンド障害対応ログ

### 1. スキルが見えない（`daily-memory` / `idea-dev`）

#### 原因
- OpenClaw内部では正常にスキル認識・コマンド生成されていた
- Discord向けコマンド名は `-` → `_` に変換されるため、`/daily-memory` ではなく `/daily_memory`
- 実際には Discord API の Global commands に登録済みだった（クライアント表示の反映遅延もあり）

#### 確認したこと
- `openclaw skills list --json` で対象スキルは `eligible: true`
- OpenClaw内部のコマンド生成で `daily_memory`, `idea_dev` が出力される
- Discord API上でも `daily_memory`, `idea_dev`, `glm_code`, `gemini_vision` が登録済み

### 2. Discordで「アプリケーションが応答しませんでした」

#### 原因
- Gateway 内の `/tmp/jiti` キャッシュに root 所有ファイルが混在
- `abc` ユーザーで動く OpenClaw Gateway がプラグイン読込時に `EACCES`
- `discord` / `memory-core` などのプラグイン読み込み失敗で slash interaction がタイムアウト

#### 対応
- `/tmp/jiti` を削除して `abc:abc` で再作成
- 追加インストールされていた `discord` プラグインを削除（bundled版に統一）
- Gateway再起動（コンテナフォールバック）

#### 結果
- `EACCES` 消失
- Discord provider の再接続成功
- slash command が応答可能に復旧

### 3. DMでは成功するが通常チャットで `not authorized`

#### 原因
- DMのpairingで許可されたIDは `credentials/discord-allowFrom.json` に保存される
- Guildのslash認可は `channels.discord.allowFrom` を参照していた
- そのため DM は通るが Guild は拒否される状態になっていた

#### 対応
- `discord-allowFrom.json` のIDを `openclaw.json` の `channels.discord.allowFrom` に反映
- Gateway再起動

#### 結果
- 通常チャットの `/daily_memory` / `/skill daily-memory` 実行成功

## 関連リンク

- 公式ドキュメント: https://docs.openclaw.ai/tools/skills
- ClawHub: https://clawhub.ai
- Discord Application Commands: https://docs.discord.com/developers/interactions/application-commands
