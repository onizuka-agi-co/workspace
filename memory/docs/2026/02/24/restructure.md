# 構造変更

## 変更内容

1日1ファイル → 日付フォルダ + トピック別ファイル

## Before

```
docs/2026/02/
├── 2026-02-23.md   ← 全ての情報が1ファイル
└── 2026-02-24.md
```

## After

```
docs/2026/02/
├── 23/
│   ├── index.md           ← 概要・リンク集
│   ├── claude-code-glm.md
│   ├── x-api-skills.md
│   ├── x-oauth2.md
│   ├── uv-install.md
│   ├── x-community.md
│   └── tested.md
└── 24/
    ├── index.md
    ├── task-management.md
    ├── vitepress-setup.md
    ├── github-pages.md
    ├── security.md
    └── restructure.md     ← このファイル
```

## 利点

- トピックごとに詳細を書ける
- 後で特定の話題だけ見返しやすい
- ファイルサイズが大きくならない
- VitePressのサイドバーで階層表示可能

## VitePress sidebar設定

```typescript
{
  text: '2026-02-23',
  collapsed: true,
  items: [
    { text: 'Overview', link: '/2026/02/23/' },
    { text: 'Claude Code + GLM', link: '/2026/02/23/claude-code-glm' },
    // ...
  ]
}
```

[← 戻る](./)
