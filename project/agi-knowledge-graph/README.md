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
| グラフエンジン | NetworkX + JSON（ローカル） |
| グラフDB | Neo4j Aura Free（将来対応） |
| 可視化 | React + D3.js / Cytoscape.js（将来対応） |

## 使い方

### 1. 論文収集

```bash
# HuggingFaceから最新論文を取得（最大200件）
python paper_collector.py --fetch --limit 200

# キャッシュから読み込み
python paper_collector.py --cache
```

### 2. ナレッジグラフ構築

```bash
# グラフを構築
python graph_engine.py build

# 統計を確認
python graph_engine.py stats

# キーワード検索
python graph_engine.py search -q "reinforcement learning"

# 共著者ネットワーク
python graph_engine.py coauthors -a "Author Name"

# トピックランキング
python graph_engine.py topics

# JSONエクスポート
python graph_engine.py export
```

### 3. Neo4j連携（将来対応）

```bash
# Neo4jに同期
python paper_collector.py --fetch --sync
```

## 現在のデータ（2026-05-06時点）

| 指標 | 値 |
|-----|---|
| 論文数 | 50 |
| 著者数 | 647 |
| トピック数 | 438 |
| 共著関係 | 28,361 |
| グラフノード | 697 |
| グラフエッジ | 653 |

## 実装フェーズ

### Phase 1: 基盤構築 ✅
- [x] プロジェクトフォルダ作成
- [x] スキーマ定義
- [x] paper_collector.py実装
- [x] ローカルグラフエンジン実装
- [x] NetworkXグラフ構築
- [x] キーワード検索
- [x] 共著者ネットワーク
- [x] トピックランキング
- [x] JSONエクスポート

### Phase 2: データ拡充
- [ ] arXiv API統合（引用関係の取得）
- [ ] 論文の全テキスト取得
- [ ] 自動タグ抽出（NLP）
- [ ] 機関情報の補完

### Phase 3: Neo4j移行
- [ ] Neo4j Aura環境構築
- [ ] データ移行スクリプト
- [ ] Cypherクエリ対応

### Phase 4: 可視化
- [ ] グラフ可視化UI実装
- [ ] インタラクティブ探索機能
- [ ] Webダッシュボード

### Phase 5: 自動化
- [ ] 日次収集のs6サービス化
- [ ] 週次レポート生成
- [ ] Discord通知

## 関連Issue

- https://github.com/onizuka-agi-co/onizuka-agi-co/issues/18
