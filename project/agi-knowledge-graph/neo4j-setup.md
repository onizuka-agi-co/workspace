# Neo4j Aura 設定ガイド

## 1. Neo4j Aura 無料アカウント作成

1. https://neo4j.com/cloud/aura/ にアクセス
2. 「Start for free」をクリック
3. Google/GitHub/Microsoft アカウントでサインアップ
4. 無料インスタンスを作成（AuraDB Free）

## 2. 接続情報の取得

作成後に以下の情報が表示される：

- **Connection URL**: `neo4j+s://xxxxx.databases.neo4j.io`
- **Username**: `neo4j`（デフォルト）
- **Password**: 自動生成されたもの

## 3. 接続情報の保存

```bash
# 設定ファイルを作成
cat > /config/.openclaw/workspace/data/neo4j-credentials.json <<EOF
{
  "uri": "neo4j+s://xxxxx.databases.neo4j.io",
  "username": "neo4j",
  "password": "YOUR_PASSWORD_HERE"
}
EOF

# パーミッション設定
chmod 600 /config/.openclaw/workspace/data/neo4j-credentials.json
```

## 4. Pythonドライバーインストール

```bash
pip install neo4j
```

## 5. 接続テスト

```python
from neo4j import GraphDatabase

uri = "neo4j+s://xxxxx.databases.neo4j.io"
username = "neo4j"
password = "YOUR_PASSWORD"

driver = GraphDatabase.driver(uri, auth=(username, password))

with driver.session() as session:
    result = session.run("RETURN 1 AS num")
    print(result.single()["num"])  # 1

driver.close()
```

## 無料枠の制限

- **ストレージ**: 200MB
- **同時接続数**: 5
- **インスタンス数**: 1
- **停止**: 3日間非アクティブで自動停止

## 次のステップ

1. Neo4j Aura アカウント作成
2. 接続情報を `data/neo4j-credentials.json` に保存
3. スキーマ初期化スクリプトを実行
