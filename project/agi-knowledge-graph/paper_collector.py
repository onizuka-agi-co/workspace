#!/usr/bin/env python3
"""
AGI Knowledge Graph - Paper Collector

HuggingFace Papers APIから論文情報を収集し、Neo4jに投入するスクリプト。
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT.parent.parent / "data"
CREDENTIALS_FILE = DATA_DIR / "neo4j-credentials.json"
OUTPUT_FILE = PROJECT_ROOT / "papers_cache.json"

# Neo4jドライバー（オプション）
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("Warning: neo4j package not installed. Run: pip install neo4j")


class PaperCollector:
    """論文情報収集クラス"""

    HF_API_URL = "https://huggingface.co/api/daily_papers"

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

    def fetch_papers_from_hf(self, limit: int = 100) -> list[dict]:
        """
        HuggingFace Papers APIから論文を取得

        Returns:
            論文データのリスト
        """
        print(f"Fetching papers from HuggingFace (limit: {limit})...")

        try:
            req = urllib.request.Request(
                self.HF_API_URL,
                headers={"User-Agent": "ONIZUKA-AGI-PaperCollector/1.0"}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            papers = []
            for item in data[:limit]:
                paper_info = item.get("paper", {})
                paper = {
                    "id": paper_info.get("id", ""),
                    "title": paper_info.get("title", ""),
                    "abstract": paper_info.get("summary", ""),
                    "publishedAt": paper_info.get("publishedAt", ""),
                    "arxivId": paper_info.get("id", ""),
                    "url": f"https://arxiv.org/abs/{paper_info.get('id', '')}",
                    "authors": [
                        {"name": a.get("name", ""), "id": a.get("_id", "")}
                        for a in paper_info.get("authors", [])
                    ],
                    "tags": paper_info.get("ai_keywords", []),
                    "citationCount": paper_info.get("upvotes", 0),
                    "githubRepo": paper_info.get("githubRepo", ""),
                    "organization": paper_info.get("organization", {}).get("fullname", ""),
                }
                papers.append(paper)

            print(f"Fetched {len(papers)} papers")
            return papers

        except urllib.error.URLError as e:
            print(f"Failed to fetch papers: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"Failed to parse JSON: {e}")
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


    def save_to_cache(self, papers: list[dict]) -> bool:
        """論文データをキャッシュファイルに保存"""
        try:
            cache_data = {
                "fetchedAt": datetime.utcnow().isoformat() + "Z",
                "count": len(papers),
                "papers": papers
            }
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(papers)} papers to {OUTPUT_FILE}")
            return True
        except Exception as e:
            print(f"Failed to save cache: {e}")
            return False

    def load_from_cache(self) -> list[dict]:
        """キャッシュから論文データを読み込み"""
        if not OUTPUT_FILE.exists():
            return []

        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded {data.get('count', 0)} papers from cache (fetched: {data.get('fetchedAt', 'unknown')})")
            return data.get("papers", [])
        except Exception as e:
            print(f"Failed to load cache: {e}")
            return []

    def close(self):
        """接続を閉じる"""
        if self.neo4j_driver:
            self.neo4j_driver.close()


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="AGI Knowledge Graph Paper Collector")
    parser.add_argument("--fetch", "-f", action="store_true", help="Fetch papers from HuggingFace")
    parser.add_argument("--limit", "-l", type=int, default=100, help="Number of papers to fetch")
    parser.add_argument("--cache", "-c", action="store_true", help="Load from cache")
    parser.add_argument("--sync", "-s", action="store_true", help="Sync to Neo4j")
    args = parser.parse_args()

    collector = PaperCollector()

    # Neo4j接続（オプション）
    if args.sync:
        if not collector.connect_neo4j():
            print("Warning: Neo4j not available, skipping sync")

    print("=" * 50)
    print("AGI Knowledge Graph - Paper Collector")
    print("=" * 50)

    if args.fetch:
        # HuggingFaceから論文を取得
        papers = collector.fetch_papers_from_hf(limit=args.limit)
        if papers:
            collector.save_to_cache(papers)
    elif args.cache:
        # キャッシュから読み込み
        papers = collector.load_from_cache()
    else:
        # デフォルト: キャッシュがあれば読み込み、なければ取得
        papers = collector.load_from_cache()
        if not papers:
            print("\nNo cache found. Fetching from HuggingFace...")
            papers = collector.fetch_papers_from_hf(limit=args.limit)
            if papers:
                collector.save_to_cache(papers)

    if papers:
        print(f"\n📊 Total papers: {len(papers)}")
        print("\n📝 Sample papers:")
        for p in papers[:3]:
            print(f"  • {p['title'][:60]}... ({p.get('citationCount', 0)} upvotes)")

    collector.close()
    print("\n✅ Done")


if __name__ == "__main__":
    main()
