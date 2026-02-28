---
layout: home

hero:
  name: "Memory"
  text: "Daily Reports & Memory"
  tagline: ONIZUKA AGI Co. - Democratizing AGI knowledge
  actions:
    - theme: brand
      text: 2026年の記録
      link: /2026/
    - theme: alt
      text: GitHub
      link: https://github.com/onizuka-agi-co/memory
---

## About

日々の記録・気づき・進捗をまとめたリポジトリ。

**ONIZUKA AGI Co.** の活動を記録し、知見を蓄積・共有する。
**ONUZUKA** は `README.md` のワークスペース上に設立された AGI カンパニー。

---

## Features

### 📝 人間が読みやすい
VitePressで美しいドキュメントサイトを生成。検索機能、サイドバー、ダークモード対応。

### 🤖 AIが読み書きしやすい
Markdownベース。AIが直接読み込み・編集・要約可能。

### 🔍 検索可能
全文検索で過去の記録をすぐに見つけられる。

### 🔒 セキュア
pre-commitフックで機密情報の漏洩を防止。

---

## Structure

```
docs/
├── 2026/                    # 年単位
│   ├── 02/                  # 月単位
│   │   ├── 23/              # 日単位
│   │   │   ├── index.md     # 概要
│   │   │   ├── topic-a.md   # トピック別詳細
│   │   │   └── topic-b.md
│   │   ├── 24/
│   │   └── index.md
│   └── index.md
├── notes/                   # 技術メモ
└── index.md
```

---

## Quick Links

| リンク | 説明 |
|--------|------|
| [2026年2月](/2026/02/) | 最新の記録 |
| [アーキテクチャ](/architecture/) | ONIZUKA/ONUZUKA の設計方針 |
| [GitHub](https://github.com/onizuka-agi-co/memory) | リポジトリ |
| [ONIZUKA AGI](https://github.com/onizuka-agi-co) | 組織 |

---

## How to Use

### 新しい日の記録を追加

1. `docs/2026/MM/DD/` フォルダを作成
2. `index.md` に概要を記載
3. トピック別に `.md` ファイルを作成
4. `config.ts` のサイドバーを更新
5. commit & push

### ローカルで確認

```bash
cd memory
npm run docs:dev
# http://localhost:5173/memory/
```

### ビルド

```bash
npm run docs:build
```
