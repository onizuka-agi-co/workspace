# X API スキル作成

## スキル配置

OpenClawがスキルを認識する場所（優先順位）:
1. `<workspace>/skills/` - 最高優先
2. `~/.openclaw/skills/` - 中
3. bundled skills - 最低

## 作成したスキル

```
skills/
├── x-read/   # X API読み込み専用
│   ├── SKILL.md
│   └── scripts/x_read.py
├── x-write/  # X API書き込み専用
│   ├── SKILL.md
│   └── scripts/x_write.py
└── google-browse/   # Google検索・ブラウズ
```

## 実行方法

```bash
# UVを使用（推奨）
uv run skills/x-read/scripts/x_read.py me
uv run skills/x-write/scripts/x_write.py post "テキスト"
```

## トークンファイルのパス設定

```python
# skills/x-read/scripts/x_read.py の場合
TOKEN_FILE = Path(__file__).parent.parent.parent.parent / "x-tokens.json"
#                                              ↑ skills/ ↑ x-read/ ↑ scripts/
```

[← 戻る](./)
