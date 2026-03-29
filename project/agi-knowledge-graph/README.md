# AGI Knowledge Graph

> 🧠 AGI論文ナレッジグラフ構築プロジェクト

## 概要

HuggingFace Papers APIから最新のAGI関連論文を自動収集し、著者・機関・引用関係をナレッジグラフとして構築。

## 目的

- AGI研究の知見を体系的に整理
- 最新トレンドを視覚的に把握
- 研究者・機関の関係性を可視化

## 技術スタック

| レイヤー | 技術 |
|---------|------|
| データ収集 | Python + HuggingFace Papers API |
| グラフDB | Neo4j (Aura Free) |
| 可視化 | React + D3.js / Cytoscape.js |
| 自動化 | s6サービス |

## セットアップ

### 1. Neo4j Aura（無料）

1. https://neo4j.com/product/auradb/ にアクセス
2. 「Start Free」をクリック
3. プロジェクトを作成し、接続情報を取得

```bash
# 認証情報を保存
cat > ../../data/neo4j-credentials.json << 'EOF'
{
  "uri": "neo4j+s://xxxxx.databases.neo4j.io",
  "username": "neo4j",
  "password": "your-password"
}
EOF
```

### 2. Pythonパッケージ

```bash
pip install neo4j
```

## 使い方

```bash
# HuggingFaceから論文を取得
python paper_collector.py --fetch --limit 100

# キャッシュから読み込み
python paper_collector.py --cache

# Neo4jに同期
python paper_collector.py --fetch --sync
```

## 実装フェーズ

### Phase 1: 基盤構築
- [x] プロジェクトフォルダ作成
- [x] スキーマ定義
- [x] paper_collector.py実装
- [ ] Neo4j Aura環境構築
- [ ] Neo4jへのデータ投入

### Phase 2: データ収集
- [x] HuggingFace Papers API統合
- [x] 論文情報の抽出・変換
- [ ] グラフデータ投入スクリプト

### Phase 3: 可視化
- [ ] グラフ可視化UI実装
- [ ] インタラクティブ探索機能

### Phase 4: 検索・分析
- [ ] キーワード検索
- [ ] 著者・機関検索
- [ ] トレンド分析

### Phase 5: 自動化
- [ ] 日次収集のs6サービス化
- [ ] 週次レポート生成
- [ ] Discord通知

## 関連Issue

- https://github.com/onizuka-agi-co/onizuka-agi-co/issues/18

## 開始日

2026-03-26
