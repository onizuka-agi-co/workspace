# GitHub Pages有効化

## ghコマンドで有効化

```bash
gh api -X POST repos/onizuka-agi-co/memory/pages --input - <<EOF
{
  "build_type": "workflow",
  "source": {
    "branch": "master",
    "path": "/docs"
  }
}
EOF
```

## 結果

```json
{
  "html_url": "https://onizuka-agi-co.github.io/memory/",
  "build_type": "workflow"
}
```

## サイトURL

https://onizuka-agi-co.github.io/memory/

GitHub Actionsが自動的にVitePressをビルドしてデプロイする。

[← 戻る](./)
