# TinyClaw調査

## 概要

GitHub: https://github.com/TinyAGI/tinyclaw
License: MIT
Status: Experimental

**キャッチコピー:** "Tiny but mighty! 🦞✨"

OpenClawにインスパイアされたマルチエージェント・マルチチーム・マルチチャンネルのAIアシスタント。

## 主な機能

- **Multi-agent** - 複数の隔離されたAIエージェント
- **Multi-team** - エージェント間の協調・チェーン実行
- **Multi-channel** - Discord, WhatsApp, Telegram
- **Web Portal (TinyOffice)** - ブラウザベースのダッシュボード
- **Team Observation** - チーム会話の可視化
- **SQLite Queue** - 原子トランザクション、リトライ、デッドレター管理
- **24/7 operation** - tmuxで常時稼働

## OpenClawとの比較

| 機能 | OpenClaw | TinyClaw |
|------|----------|----------|
| **ライセンス** | 商用（オープンコア） | MIT |
| **開発言語** | TypeScript/Node | TypeScript/Node |
| **AI CLI** | Claude Code | Claude Code + Codex |
| **キュー** | 内蔵 | SQLite |
| **マルチエージェント** | ○ (bindings) | ○ (agents) |
| **チーム協調** | Sub-Agents | Teams + Chain |
| **チャンネル** | 20+ | 3 (Discord, WA, TG) |
| **Web UI** | Dashboard/TUI | TinyOffice |
| **スキルシステム** | Skills (ClawHub) | なし（AGENTS.md） |

## Teams機能

### Chain Execution
```
@dev fix the auth bug
  → Routes to team leader (@coder)
  → Coder fixes bug, mentions @reviewer
  → Reviewer automatically invoked
  → Combined response sent back
```

### Fan-out
```
@coder Review and fix bugs in auth.ts
@writer Document the changes
@reviewer Check the documentation
  → 並列実行 → 統合レスポンス
```

## OpenClawへの応用アイデア

### 1. agent-toolkit スキル
統合コマンドセット:
- `/status` - システム状態表示
- `/plugins` - プラグイン管理
- `/skills` - スキル一覧・管理
- `/agents` - エージェント一覧
- `/teams` - チーム管理（新規）

### 2. OpenClaw Teams 機能
- Chain Execution: リーダー → メンバー → 統合レスポンス
- Fan-out: 複数エージェントへの並列指示
- 可視化: TUIダッシュボード

### 3. SQLite キュー検討
- 透明性の高いメッセージ管理
- デッドレターキュー
- リトライロジック

## 技術スタック

- **言語:** TypeScript, Node.js
- **AI CLI:** Claude Code CLI, Codex CLI
- **キュー:** SQLite (WAL mode)
- **セッション管理:** tmux
- **Web Portal:** Next.js (TinyOffice)
- **チャンネル:** discord.js, whatsapp-web.js, node-telegram-bot-api

## リンク

- GitHub: https://github.com/TinyAGI/tinyclaw
- Discord: https://discord.gg/jH6AcEChuD
