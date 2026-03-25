# Neo4j スキーマ定義

## ノードタイプ

### Paper（論文）
```cypher
CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:Paper) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT paper_title IF NOT EXISTS FOR (p:Paper) REQUIRE p.title IS UNIQUE;
```

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| id | String | 論文ID (HuggingFace Papers ID) |
| title | String | タイトル |
| abstract | String | アブストラクト |
| publishedAt | DateTime | 公開日 |
| arxivId | String | arXiv ID |
| url | String | 論文URL |
| citationCount | Integer | 被引用数 |
| tags | List<String> | タグ |

### Author（著者）
```cypher
CREATE CONSTRAINT author_id IF NOT EXISTS FOR (a:Author) REQUIRE a.id IS UNIQUE;
CREATE CONSTRAINT author_name IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE;
```

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| id | String | 著者ID |
| name | String | 著者名 |
| affiliation | String | 所属 |

### Institution（機関）
```cypher
CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT institution_name IF NOT EXISTS FOR (i:Institution) REQUIRE i.name IS UNIQUE;
```

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| id | String | 機関ID |
| name | String | 機関名 |
| country | String | 国 |
| type | String | 種別（University/Company/Research Lab） |

### Topic（トピック）
```cypher
CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT topic_name IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE;
```

| プロパティ | 型 | 説明 |
|-----------|-----|------|
| id | String | トピックID |
| name | String | トピック名 |
| category | String | カテゴリ |

## リレーションシップ

### AUTHOR_OF（著者が論文を執筆）
```cypher
(:Author)-[:AUTHOR_OF {order: Integer}]->(:Paper)
```
- `order`: 著者順位（1=第一著者）

### AFFILIATED_WITH（著者が機関に所属）
```cypher
(:Author)-[:AFFILIATED_WITH]->(:Institution)
```

### CITES（論文が別の論文を引用）
```cypher
(:Paper)-[:CITES]->(:Paper)
```

### HAS_TOPIC（論文がトピックを持つ）
```cypher
(:Paper)-[:HAS_TOPIC {score: Float}]->(:Topic)
```
- `score`: 関連度スコア（0.0-1.0）

### COLLABORATES（著者が共著）
```cypher
(:Author)-[:COLLABORATES {count: Integer}]->(:Author)
```
- `count`: 共著回数

## インデックス

```cypher
// 検索用インデックス
CREATE INDEX paper_title_fulltext IF NOT EXISTS FOR (p:Paper) ON EACH [p.title];
CREATE INDEX paper_abstract_fulltext IF NOT EXISTS FOR (p:Paper) ON EACH [p.abstract];
CREATE INDEX author_name_fulltext IF NOT EXISTS FOR (a:Author) ON EACH [a.name];
CREATE INDEX institution_name_fulltext IF NOT EXISTS FOR (i:Institution) ON EACH [i.name];
```

## サンプルクエリ

### 特定著者の論文一覧
```cypher
MATCH (a:Author {name: "John Smith"})-[:AUTHOR_OF]->(p:Paper)
RETURN p.title, p.publishedAt
ORDER BY p.publishedAt DESC;
```

### 論文間の引用ネットワーク
```cypher
MATCH (p1:Paper {id: "paper-123"})-[:CITES*1..3]-(p2:Paper)
RETURN p1, p2;
```

### 共著者のネットワーク
```cypher
MATCH (a1:Author {name: "John Smith"})-[:COLLABORATES]-(a2:Author)
RETURN a1, a2
ORDER BY a2.count DESC
LIMIT 10;
```

### 機関ごとの論文数
```cypher
MATCH (i:Institution)<-[:AFFILIATED_WITH]-(:Author)-[:AUTHOR_OF]->(p:Paper)
RETURN i.name, COUNT(DISTINCT p) AS paperCount
ORDER BY paperCount DESC;
```

### トピック別トレンド
```cypher
MATCH (p:Paper)-[:HAS_TOPIC]->(t:Topic)
WHERE p.publishedAt >= datetime() - duration('P30D')
RETURN t.name, COUNT(p) AS recentPapers
ORDER BY recentPapers DESC;
```
