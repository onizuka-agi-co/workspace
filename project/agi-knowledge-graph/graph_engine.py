#!/usr/bin/env python3
"""
AGI Knowledge Graph - Local Graph Engine

Neo4jなしで動作するローカルナレッジグラフエンジン。
NetworkX + JSON でグラフを構築・検索し、後からNeo4jに移行可能。

Usage:
    python graph_engine.py build   - キャッシュからグラフを構築
    python graph_engine.py stats   - グラフ統計を表示
    python graph_engine.py search <query> - キャッシュ内を検索
    python graph_engine.py coauthors <author> - 共著者ネットワーク
    python graph_engine.py topics  - トピックランキング
    python graph_engine.py export  - JSON形式でエクスポート
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Optional: NetworkX for graph operations
try:
    import networkx as nx
    NX_AVAILABLE = True
except ImportError:
    NX_AVAILABLE = False
    print("Warning: networkx not installed. Run: pip install networkx")

PROJECT_ROOT = Path(__file__).parent
CACHE_FILE = PROJECT_ROOT / "papers_cache.json"
GRAPH_FILE = PROJECT_ROOT / "knowledge_graph.json"


class KnowledgeGraph:
    """ローカルナレッジグラフエンジン"""

    def __init__(self):
        self.papers: list[dict] = []
        self.author_papers: dict[str, list[str]] = defaultdict(list)
        self.author_collabs: dict[str, Counter] = defaultdict(Counter)
        self.topic_papers: dict[str, list[str]] = defaultdict(list)
        self.paper_map: dict[str, dict] = {}
        self.graph = None

    def load_from_cache(self) -> bool:
        """papers_cache.jsonから論文データを読み込み"""
        if not CACHE_FILE.exists():
            print(f"Cache file not found: {CACHE_FILE}")
            return False

        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.papers = data.get("papers", [])
        for p in self.papers:
            self.paper_map[p.get("id", p.get("title", ""))] = p

        print(f"Loaded {len(self.papers)} papers from cache")
        return True

    def build_graph(self) -> bool:
        """キャッシュからグラフ構造を構築"""
        if not self.papers:
            print("No papers loaded. Run load_from_cache() first.")
            return False

        # Build indexes
        for paper in self.papers:
            pid = paper.get("id", paper.get("title", ""))

            # Author -> Paper mapping
            for author in paper.get("authors", []):
                name = author.get("name", "").strip()
                if name:
                    self.author_papers[name].append(pid)

            # Topic -> Paper mapping
            for tag in paper.get("tags", []):
                if tag:
                    self.topic_papers[tag].append(pid)

        # Build co-author network
        for paper in self.papers:
            authors = [a.get("name", "").strip() for a in paper.get("authors", []) if a.get("name", "").strip()]
            for i, a1 in enumerate(authors):
                for j, a2 in enumerate(authors):
                    if i != j:
                        self.author_collabs[a1][a2] += 1

        # Build NetworkX graph if available
        if NX_AVAILABLE:
            self.graph = nx.Graph()
            for paper in self.papers:
                pid = paper.get("id", paper.get("title", ""))
                self.graph.add_node(pid, type="paper", title=paper.get("title", ""))

            for author_name, paper_ids in self.author_papers.items():
                self.graph.add_node(author_name, type="author")
                for pid in paper_ids:
                    self.graph.add_edge(author_name, pid, type="AUTHOR_OF")

        return True

    def get_stats(self) -> dict:
        """グラフ統計を取得"""
        stats = {
            "papers": len(self.papers),
            "authors": len(self.author_papers),
            "topics": len(self.topic_papers),
            "collaborations": sum(sum(c.values()) for c in self.author_collabs.values()) // 2,
        }

        if self.graph and NX_AVAILABLE:
            stats["nodes"] = self.graph.number_of_nodes()
            stats["edges"] = self.graph.number_of_edges()
            if nx.is_connected(self.graph) if self.graph.number_of_nodes() > 0 else False:
                stats["avg_path_length"] = round(nx.average_shortest_path_length(self.graph), 2)
            stats["components"] = nx.number_connected_components(self.graph)

        # Top authors
        top_authors = sorted(
            self.author_papers.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        stats["top_authors"] = [(name, len(pids)) for name, pids in top_authors]

        # Top topics
        top_topics = sorted(
            self.topic_papers.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:10]
        stats["top_topics"] = [(topic, len(pids)) for topic, pids in top_topics]

        return stats

    def search_papers(self, query: str, limit: int = 10) -> list[dict]:
        """論文をキーワードで検索"""
        query_lower = query.lower()
        results = []

        for paper in self.papers:
            title = paper.get("title", "").lower()
            abstract = paper.get("abstract", "").lower()
            tags = " ".join(paper.get("tags", [])).lower()

            score = 0
            if query_lower in title:
                score += 3
            if query_lower in abstract:
                score += 1
            if query_lower in tags:
                score += 2

            if score > 0:
                results.append({**paper, "_score": score})

        results.sort(key=lambda x: x["_score"], reverse=True)
        return results[:limit]

    def get_coauthors(self, author_name: str, min_collabs: int = 1) -> list[tuple]:
        """指定著者の共著者一覧"""
        collabs = self.author_collabs.get(author_name, Counter())
        return [(name, count) for name, count in collabs.most_common() if count >= min_collabs]

    def export_json(self, output_path: str = None) -> str:
        """グラフデータをJSONでエクスポート"""
        output = {
            "exportedAt": datetime.utcnow().isoformat() + "Z",
            "stats": self.get_stats(),
            "papers": self.papers,
            "author_papers": {k: v for k, v in self.author_papers.items()},
            "author_collaborations": {
                author: dict(collabs)
                for author, collabs in self.author_collabs.items()
                if collabs
            },
            "topic_papers": {k: v for k, v in self.topic_papers.items()},
        }

        path = Path(output_path) if output_path else GRAPH_FILE
        with open(path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2, default=str)

        print(f"Exported graph to {path}")
        return str(path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AGI Knowledge Graph Engine")
    parser.add_argument("command", choices=["build", "stats", "search", "coauthors", "topics", "export"])
    parser.add_argument("--query", "-q", type=str, help="Search query")
    parser.add_argument("--author", "-a", type=str, help="Author name")
    parser.add_argument("--output", "-o", type=str, help="Output file path")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Result limit")
    args = parser.parse_args()

    kg = KnowledgeGraph()

    if not kg.load_from_cache():
        print("Run paper_collector.py --fetch first to populate cache")
        sys.exit(1)

    kg.build_graph()

    if args.command == "build":
        print("✅ Graph built successfully")
        print(f"   Papers: {len(kg.papers)}")
        print(f"   Authors: {len(kg.author_papers)}")
        print(f"   Topics: {len(kg.topic_papers)}")

    elif args.command == "stats":
        stats = kg.get_stats()
        print("\n📊 Knowledge Graph Statistics")
        print("=" * 40)
        print(f"  Papers: {stats['papers']}")
        print(f"  Authors: {stats['authors']}")
        print(f"  Topics: {stats['topics']}")
        print(f"  Collaborations: {stats['collaborations']}")
        if "nodes" in stats:
            print(f"  Graph Nodes: {stats['nodes']}")
            print(f"  Graph Edges: {stats['edges']}")
            print(f"  Components: {stats['components']}")

        print("\n🏆 Top Authors:")
        for name, count in stats.get("top_authors", []):
            print(f"  {name}: {count} papers")

        print("\n🏷️ Top Topics:")
        for topic, count in stats.get("top_topics", []):
            print(f"  {topic}: {count} papers")

    elif args.command == "search":
        if not args.query:
            print("--query required for search")
            sys.exit(1)
        results = kg.search_papers(args.query, args.limit)
        print(f"\n🔍 Search results for '{args.query}' ({len(results)} hits):")
        for r in results:
            print(f"  • {r['title'][:80]}... (score: {r['_score']})")

    elif args.command == "coauthors":
        if not args.author:
            print("--author required for coauthors")
            sys.exit(1)
        collabs = kg.get_coauthors(args.author)
        print(f"\n🤝 Co-authors of '{args.author}' ({len(collabs)} found):")
        for name, count in collabs:
            print(f"  • {name} ({count} collaborations)")

    elif args.command == "topics":
        topic_counts = {t: len(pids) for t, pids in kg.topic_papers.items()}
        sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:args.limit]
        print(f"\n🏷️ Topic Rankings (top {args.limit}):")
        for topic, count in sorted_topics:
            print(f"  {topic}: {count} papers")

    elif args.command == "export":
        path = kg.export_json(args.output)
        print(f"✅ Exported to {path}")


if __name__ == "__main__":
    main()
