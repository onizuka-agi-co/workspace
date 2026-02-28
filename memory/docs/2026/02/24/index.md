# 2026-02-24

## 完了
- [x] タスク管理についてスレッドで議論
- [x] VitePressで日報リポジトリ構築開始
- [x] GitHubリポジトリ `onizuka-agi-co/memory` 作成
- [x] GitHub Pages有効化
- [x] pre-commitフック導入（機密情報検出）
- [x] .gitignore強化（トークンファイル除外）
- [x] 日付フォルダ構造への移行

## 気づき
- Markdown + VitePress = 人間もAIも使いやすい
- シンプルな構造が続けやすい
- pre-commitフックで事故防止

## 詳細

### [タスク管理議論](./task-management)
日々の実施内容をマークダウン形式で記録し、記憶装置として使う仕組みを検討。1日1ファイル vs 日付フォルダ+トピック別ファイルの比較。最終的にハイブリッド構造を採用。

### [VitePressセットアップ](./vitepress-setup)
GitHubリポジトリ作成からVitePressインストール、ディレクトリ構造、GitHub Actions設定まで。`package.json` に `"type": "module"` が必須（ESM only対応）。`base: "/memory/"` の設定も重要。

### [GitHub Pages有効化](./github-pages)
`gh api` コマンドでGitHub Pagesを有効化。`build_type: workflow` でGitHub Actionsによる自動デプロイを設定。

### [セキュリティ対策](./security)
APIトークン漏洩インシデント対応。`git filter-repo` で履歴から削除。pre-commitフック導入で差分を表示し機密情報を検出。.gitignore強化。

### [構造変更](./restructure)
1日1ファイルから日付フォルダ+トピック別ファイル構造へ移行。各トピックを独立したファイルに分割し、index.mdで概要を管理。
