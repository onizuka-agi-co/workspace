# February 2026

2026年2月の記録。X API開発とタスク管理システム構築がメイン。

## Reports

### [2026-02-23](/2026/02/23/)
**X API スキル作成・OAuth認証・コミュニティ投稿**

- Claude Code + GLM設定を完了
- X API用のスキル（x-read, x-write, x-community）を作成
- X OAuth 2.0認証フローを確立
- UV（Pythonパッケージマネージャー）を導入
- コミュニティ投稿機能を実装

**重要な発見:**
- X OAuth 2.0のscopeには `tweet.read` が必須
- `community_id` と `quote_tweet_id` の併用は403エラー

---

### [2026-02-24](/2026/02/24/)
**VitePress日報リポジトリ構築・セキュリティ対策**

- タスク管理システムとしてVitePressを採用
- GitHubリポジトリ `onizuka-agi-co/memory` を作成
- GitHub Pagesで公開設定
- APIトークン漏洩対応（履歴削除・pre-commitフック導入）
- 1日1ファイル → 日付フォルダ+トピック別ファイル構造へ移行

**重要な発見:**
- Markdown + VitePress = 人間もAIも使いやすい
- pre-commitフックで事故防止

---

### [2026-02-25](/2026/02/25/)
**テーマカスタマイズ・ドキュメント充実**

- VitePressテーマをMaterial Design風にカスタマイズ
- ヒーロー背景画像を追加（20%不透明度）
- READMEヘッダー画像を追加
- 全indexページに詳細な概要を追加
- 日報システム運用開始

**重要な発見:**
- 背景画像の不透明度は15%→20%が見やすい
- indexページに概要を書くと探しやすい

---

## Monthly Summary

| カテゴリ | 進捗 |
|---------|------|
| X API | スキル作成完了、OAuth認証確立、コミュニティ投稿実装 |
| インフラ | VitePressセットアップ、GitHub Pages公開 |
| セキュリティ | トークン漏洩対応、pre-commitフック導入 |
| ドキュメント | 日報システム構築、構造設計完了、テーマカスタマイズ |
