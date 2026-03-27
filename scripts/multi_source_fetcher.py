#!/usr/bin/env python3
"""
Multi-Source Fetcher - 複数ソースからのコンテンツ取得

HuggingFace Papers, arXiv, AI ニュースサイト等からコンテンツを取得
"""

import json
try:
    import feedparser
except ImportError:
    feedparser = None
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import sys

# Workspace root
WORKSPACE_ROOT = Path(__file__).parent.parent
SKILLS_DIR = WORKSPACE_ROOT / "skills"
CACHE_DIR = WORKSPACE_ROOT / "data" / "cache"

# Import hf_papers module
sys.path.insert(0, str(SKILLS_DIR / "hf-papers" / "scripts"))


class MultiSourceFetcher:
    """Fetch content from multiple sources."""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def fetch_hf_papers(self, limit: int = 5) -> List[Dict]:
        """Fetch from HuggingFace Daily Papers."""
        try:
            import hf_papers
            papers = hf_papers.fetch_papers(limit=limit, use_cache=True)
            
            items = []
            for paper in papers:
                p = paper.get("paper", paper)
                items.append({
                    "source": "huggingface",
                    "id": p.get("id", ""),
                    "title": p.get("title", ""),
                    "summary": p.get("ai_summary", p.get("summary", ""))[:500],
                    "url": f"https://huggingface.co/papers/{p.get('id', '')}",
                    "published": p.get("published", ""),
                    "upvotes": p.get("upvotes", 0),
                    "keywords": p.get("ai_keywords", []),
                    "authors": p.get("authors", []),
                    "metadata": {
                        "arxiv_id": p.get("id", ""),
                        "upvotes": p.get("upvotes", 0)
                    }
                })
            
            return items
        except Exception as e:
            print(f"Error fetching HF Papers: {e}")
            return []
    
    def fetch_arxiv(self, categories: List[str] = None, limit: int = 5) -> List[Dict]:
        """Fetch from arXiv API."""
        if feedparser is None:
            print("⚠️ feedparser not installed, skipping arXiv")
            return []
        
        if categories is None:
            categories = ["cs.AI", "cs.LG", "cs.CL"]
        
        items = []
        
        for category in categories:
            try:
                url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&start=0&max_results={limit}&sortBy=submittedDate&sortOrder=descending"
                
                response = requests.get(url, timeout=30)
                feed = feedparser.parse(response.text)
                
                for entry in feed.entries:
                    # Extract arXiv ID
                    arxiv_id = entry.id.split("/")[-1]
                    
                    items.append({
                        "source": "arxiv",
                        "id": arxiv_id,
                        "title": entry.title,
                        "summary": entry.summary[:500],
                        "url": entry.id,
                        "published": entry.published if hasattr(entry, "published") else "",
                        "authors": [a.name for a in entry.authors] if hasattr(entry, "authors") else [],
                        "keywords": [tag.term for tag in entry.tags] if hasattr(entry, "tags") else [],
                        "metadata": {
                            "arxiv_id": arxiv_id,
                            "category": category
                        }
                    })
                
            except Exception as e:
                print(f"Error fetching arXiv {category}: {e}")
        
        return items
    
    def fetch_ai_news(self, limit: int = 5) -> List[Dict]:
        """Fetch from AI news sources (placeholder for RSS feeds)."""
        # This would integrate with RSS feeds from AI news sites
        # For now, return empty list
        return []
    
    def fetch_all(self, sources: List[str] = None, limit_per_source: int = 5) -> List[Dict]:
        """Fetch from all configured sources."""
        if sources is None:
            sources = ["huggingface", "arxiv"]
        
        all_items = []
        
        if "huggingface" in sources:
            print("📄 Fetching HuggingFace Papers...")
            hf_items = self.fetch_hf_papers(limit=limit_per_source)
            all_items.extend(hf_items)
            print(f"   ✅ {len(hf_items)} items")
        
        if "arxiv" in sources:
            print("📄 Fetching arXiv...")
            arxiv_items = self.fetch_arxiv(limit=limit_per_source)
            all_items.extend(arxiv_items)
            print(f"   ✅ {len(arxiv_items)} items")
        
        if "ai_news" in sources:
            print("📄 Fetching AI News...")
            news_items = self.fetch_ai_news(limit=limit_per_source)
            all_items.extend(news_items)
            print(f"   ✅ {len(news_items)} items")
        
        # Sort by relevance (upvotes for HF, date for others)
        all_items.sort(key=lambda x: x.get("upvotes", 0) or 0, reverse=True)
        
        return all_items
    
    def get_top_item(self, sources: List[str] = None) -> Optional[Dict]:
        """Get the top item across all sources."""
        items = self.fetch_all(sources=sources, limit_per_source=10)
        return items[0] if items else None
    
    def deduplicate(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate items based on ID."""
        seen_ids = set()
        unique_items = []
        
        for item in items:
            item_id = f"{item['source']}:{item['id']}"
            if item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_items.append(item)
        
        return unique_items


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Source Fetcher - 複数ソースからのコンテンツ取得"
    )
    
    parser.add_argument("--sources", nargs="+", default=["huggingface", "arxiv"],
                       help="Sources to fetch from")
    parser.add_argument("--limit", type=int, default=5,
                       help="Limit per source")
    parser.add_argument("--top", action="store_true",
                       help="Get only top item")
    parser.add_argument("--output", type=str,
                       help="Output JSON file")
    
    args = parser.parse_args()
    
    fetcher = MultiSourceFetcher()
    
    if args.top:
        print("🔍 Fetching top item...")
        item = fetcher.get_top_item(sources=args.sources)
        if item:
            print(f"\n📄 Top Item:")
            print(f"   Source: {item['source']}")
            print(f"   Title: {item['title']}")
            print(f"   ID: {item['id']}")
            if args.output:
                with open(args.output, "w") as f:
                    json.dump(item, f, indent=2, ensure_ascii=False)
                print(f"\n✅ Saved to {args.output}")
        else:
            print("❌ No items found")
    else:
        print("🔍 Fetching from multiple sources...")
        items = fetcher.fetch_all(sources=args.sources, limit_per_source=args.limit)
        items = fetcher.deduplicate(items)
        
        print(f"\n✅ Fetched {len(items)} items")
        
        for i, item in enumerate(items[:10], 1):
            print(f"\n{i}. [{item['source']}] {item['title'][:60]}")
            print(f"   ID: {item['id']}")
            if item.get("upvotes"):
                print(f"   Upvotes: {item['upvotes']}")
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(items, f, indent=2, ensure_ascii=False)
            print(f"\n✅ Saved to {args.output}")


if __name__ == "__main__":
    main()
