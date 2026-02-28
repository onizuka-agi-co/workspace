<p align="center">
  <img src="docs/public/hero-bg.jpg" alt="Memory" width="100%">
</p>

<h1 align="center">Memory</h1>

<p align="center">
  日々の記録・気づき・進捗をまとめたリポジトリ<br>
  VitePressで人間が見やすく、MarkdownでAIが読み書きしやすい
</p>

<p align="center">
  <a href="https://onizuka-agi-co.github.io/memory/">🌐 Site</a>
  •
  <a href="https://github.com/onizuka-agi-co/memory">📦 Repository</a>
</p>

---

## 使い方

### 開発サーバー起動

```bash
npm run docs:dev
```

### ビルド

```bash
npm run docs:build
```

## 構造

```
docs/
├── .vitepress/
│   └── config.ts
├── 2026/
│   ├── 02/
│   │   ├── 23/
│   │   │   ├── index.md
│   │   │   └── *.md
│   │   ├── 24/
│   │   │   ├── index.md
│   │   │   └── *.md
│   │   └── index.md
│   └── index.md
├── public/
│   └── hero-bg.jpg
├── notes/
└── index.md
```

## 日報フォーマット

```markdown
# YYYY-MM-DD

## 完了
- [x] タスクA
- [x] タスクB

## 進行中
- [ ] タスクC（進捗%）

## 気づき
- 〜について〜だと分かった

## 詳細
- [トピックA](./topic-a)
- [トピックB](./topic-b)
```

## Features

- 📝 人間が読みやすい - VitePressで美しいドキュメントサイト
- 🤖 AIが読み書きしやすい - Markdownベース
- 🔍 検索可能 - 全文検索機能
- 🔒 セキュア - pre-commitフックで機密情報防止

## License

ISC
