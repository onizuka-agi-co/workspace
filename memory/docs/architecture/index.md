# アーキテクチャ

## 位置づけ

**ONUZUKA** は `README.md` で定義されているワークスペース（FUTODAMA の AI エージェント実行基盤）上に設立された AGI カンパニーであり、この memory は知見を蓄積するナレッジ基盤として運用する。

## 設計方針

1. 人間と AI の両方が読める Markdown を唯一の記録フォーマットにする
2. 日次の実行記録とトピック別ドキュメントを分離して検索性を高める
3. ワークスペースの実行環境（Docker + Ubuntu + noVNC）と知識層（VitePress）を分離して保守性を確保する
4. スキルや自動化ジョブの改善内容を記録し、再現可能な運用にする

## レイヤ構成

### 1. Workspace Layer（実行基盤）
- `README.md` に定義された FUTODAMA ワークスペース
- Docker コンテナ上の Ubuntu/XFCE、ブラウザ操作、ファイル操作基盤

### 2. Operation Layer（運用・自動化）
- OpenClaw のタスク運用、s6 サービス、cron などの運用コンポーネント
- 日々の改善を日報に反映し、運用知識を更新

### 3. Knowledge Layer（記録・共有）
- `futodama-config/.openclaw/workspace/memory/docs` 配下の Markdown 群
- VitePress による公開・検索・ナビゲーション

## 情報フロー

1. ワークスペース上で実装・検証を実施
2. 日次 `index.md` に結果を要約
3. 詳細はトピック別ページへ分割
4. 月次・年次ページで成果を集約
