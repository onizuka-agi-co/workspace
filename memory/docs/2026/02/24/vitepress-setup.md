# VitePressセットアップ

## リポジトリ作成

```bash
gh repo create onizuka-agi-co/memory --public --description "Daily reports & memory - VitePress powered" --clone
```

## VitePressインストール

```bash
cd memory
npm init -y
npm add -D vitepress
```

## ディレクトリ構造

```
memory/
├── docs/
│   ├── .vitepress/
│   │   └── config.ts
│   ├── 2026/
│   │   ├── 02/
│   │   │   ├── 23/
│   │   │   │   ├── index.md
│   │   │   │   └── *.md
│   │   │   └── 24/
│   │   │       ├── index.md
│   │   │       └── *.md
│   │   └── index.md
│   ├── notes/
│   └── index.md
├── package.json
└── README.md
```

## package.json scripts

```json
{
  "scripts": {
    "docs:dev": "vitepress dev docs",
    "docs:build": "vitepress build docs",
    "docs:preview": "vitepress preview docs"
  }
}
```

## GitHub Actions

`.github/workflows/deploy.yml` で自動デプロイ設定。

[← 戻る](./)
