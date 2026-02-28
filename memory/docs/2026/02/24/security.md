# セキュリティ対策

## インシデント

`2026-02-23.md` にAPIトークンが含まれていた。

## 対応

### 1. 履歴から削除

```bash
git filter-repo --replace-text replacements.txt --force
git push --force --all
```

### 2. pre-commitフック導入

`.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "📋 Checking staged changes for secrets..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 差分を表示（色付き）
git diff --cached --color=always | head -100

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 機密情報パターンを検出
PATTERNS='(api[_-]?key|token|secret|password|auth|credential).*=.*["\x27]?[a-zA-Z0-9_\-]{20,}["\x27]?'

if git diff --cached | grep -qiE "$PATTERNS"; then
    echo ""
    echo "⚠️  WARNING: Possible secret detected!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    git diff --cached | grep -niE "$PATTERNS" | head -10
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Continue anyway? [y/N]"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo "❌ Commit aborted."
        exit 1
    fi
    echo "✅ Proceeding with commit..."
fi

exit 0
```

### 3. .gitignore強化

```gitignore
# Secrets - never commit these
*-tokens.json
*-credentials.json
*-secrets.json
.env
.env.*
*.env
*_token*
*_secret*
*_apikey*
*_password*
credentials*.json
secrets*.json
```

## テスト結果

| パターン | 結果 |
|---------|------|
| `API_KEY="sk-..."` | ✅ 検出・ブロック |
| `api_token = AbCdEf...` | ✅ 検出・ブロック |
| `SECRET_KEY='...'` | ✅ 検出・ブロック |
| 通常のマークダウン | ✅ 通過 |

## 教訓

- トークンは環境変数へ
- ドキュメントには `<YOUR_TOKEN>` と書く
- pre-commitフックで事故防止

[← 戻る](./)
