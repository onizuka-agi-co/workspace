#!/usr/bin/env python3
"""
AGI Knowledge Graph - Paper Collector

HuggingFace Papers APIから論文情報を収集し、Neo4jに投入するスクリプト。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT.parent.parent / "data"
CREDENTIALS_FILE = DATA_DIR / "neo4j-credentials.json"

# Neo4jドライバー（オプション）
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not installed. Run: pip install neo4j")


class PaperCollector:
    """論文情報収集クラス"""

    def __init__(self):
        self.papers = []
        self.neo4j_driver = None

    def connect_neo4j(self):
        """Neo4jに接続"""
        if not NEO4J_AVAILABLE:
            print("Neo4j driver not available")
            return False

        if not CREDENTIALS_FILE.exists():
            print(f"Credentials file not found: {CREDENTIALS_FILE}")
            return False

        with open(CREDENTIALS_FILE) as f:
            creds = json.load(f)

        try:
            self.neo4j_driver = GraphDatabase.driver(
                creds["uri"],
                auth=(creds["username"], creds["password"])
            )
            print("Connected to Neo4j")
            return True
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")
            return False

    def fetch_papers_from_hf(self, query: str = "AGI", limit: int = 100) -> list[dict]:
        """
        HuggingFace Papers APIから論文を取得

        Note: HuggingFace Papers APIは直接HTTPアクセスが必要
        このメソッドはモックデータを返す（実装はweb_fetch等で行う）
        """
        # TODO: 実際のAPI実装
        # 現在はモックデータを返す
        print(f"Fetching papers with query: {query} (limit: {limit})")
        return []

    def parse_paper_data(self, raw_data: dict) -> dict:
        """論文データをパースして正規化"""
        return {
            "id": raw_data.get("id", ""),
            "title": raw_data.get("title", ""),
            "abstract": raw_data.get("abstract", ""),
            "publishedAt": raw_data.get("publishedAt"),
            "arxivId": raw_data.get("arxivId"),
            "url": raw_data.get("url", ""),
            "authors": raw_data.get("authors", []),
            "tags": raw_data.get("tags", []),
            "citationCount": raw_data.get("citationCount", 0),
        }

    def create_paper_node(self, paper: dict) -> bool:
        """論文ノードを作成"""
        if not self.neo4j_driver:
            return False

        query = """
        MERGE (p:Paper {id: $id})
        SET p.title = $title,
            p.abstract = $abstract,
            p.publishedAt = datetime($publishedAt),
            p.arxivId = $arxivId,
            p.url = $url,
            p.citationCount = $citationCount,
            p.tags = $tags
        RETURN p
        """

        try:
            with self.neo4j_driver.session() as session:
                result = session.run(query, **paper)
                return result.single() is not None
        except Exception as e:
            print(f"Failed to create paper node: {e}")
            return False

    def create_author_nodes(self, paper_id: str, authors: list[dict]) -> bool:
        """著者ノードとリレーションを作成"""
        if not self.neo4j_driver:
            return False

        query = """
        MATCH (p:Paper {id: $paper_id})
        WITH p
        UNWIND $authors AS author_data
        MERGE (a:Author {name: author_data.name})
        ON CREATE SET a.id = randomUUID()
        MERGE (a)-[r:AUTHOR_OF]->(p)
        SET r.order = author_data.order
        """

        try:
            with self.neo4j_driver.session() as session:
                session.run(query, paper_id=paper_id, authors=authors)
                return True
        except Exception as e:
            print(f"Failed to create author nodes: {e}")
            return False

    def close(self):
        """接続を閉じる"""
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    """メイン処理"""
    collector = PaperCollector()

    # Neo4j接続（オプション）
    if CREDENTIALS_FILE.exists():
        collector.connect_neo4j()

    print("AGI Knowledge Graph - Paper Collector")
    print("=" * 40)

    # TODO: 実際のデータ収集処理
    print("\nPhase 1: Setup complete")
    print("Next: Implement HuggingFace Papers API integration")

    collector.close()


if __name__ == "__main__":
    main()
