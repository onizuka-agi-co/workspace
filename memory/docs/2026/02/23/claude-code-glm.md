# Claude Code + GLM 設定

Claude Code を GLM (z.ai) 経由で使用するための設定は `~/.bashrc` に永続化済み。

```bash
ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
ANTHROPIC_AUTH_TOKEN="<YOUR_TOKEN>"
ANTHROPIC_DEFAULT_HAIKU_MODEL="glm-4.5-air"
ANTHROPIC_DEFAULT_SONNET_MODEL="glm-5"
ANTHROPIC_DEFAULT_OPUS_MODEL="glm-5"
```

## 重要なパターン

- `pty:true` 必須 — PTYがないと出力が壊れる or ハングする
- `timeout: 300+` 推奨 — GLMは応答が遅い場合あり
- `--dangerously-skip-permissions` で確認ダイアログをスキップ
- `--print` で非インタラクティブモード
- `source` は sh で使えない → 環境変数はインライン設定
- Gitディレクトリ必須 — `mktemp -d && git init` で一時ディレクトリ作成

## 成功パターン

```bash
SCRATCH=$(mktemp -d) && cd $SCRATCH && git init -q && \
ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic" \
ANTHROPIC_AUTH_TOKEN="<YOUR_TOKEN>" \
claude --print --dangerously-skip-permissions "Your task"
```

[← 戻る](./)
