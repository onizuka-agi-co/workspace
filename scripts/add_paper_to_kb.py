#!/usr/bin/env python3
"""
Add Paper to Knowledge Base - papers/フォルダに論文ページを追加する

HuggingFace PapersのデータをVitePressのpapers/フォルダに追加し、
index.mdを自動更新する。
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths
WORKSPACE_ROOT = Path(__file__).parent.parent
PAPERS_DIR = WORKSPACE_ROOT / "memory" / "docs" / "papers"
TEMPLATE_PATH = PAPERS_DIR / "paper-template.md"
INDEX_PATH = PAPERS_DIR / "index.md"

# Category mapping
CATEGORY_MAP = {
    "cs.AI": "agi",
    "cs.CL": "agi",
    "cs.LG": "agi",
    "cs.CV": "general",
    "cs.RO": "general",
    "cs.SE": "general",
    "cs.NE": "general",
    "cs.HC": "general",
}


def slugify(text: str) -> str:
    """Convert text to URL-safe slug."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def get_category(categories: list[str]) -> str:
    """Determine paper category from arXiv categories."""
    for cat in categories:
        if cat in CATEGORY_MAP:
            return CATEGORY_MAP[cat]
    return "general"


def create_paper_page(paper_data: dict, image_url: Optional[str] = None) -> Path:
    """Create a paper page in the appropriate category folder."""
    paper = paper_data.get("paper", paper_data)
    
    arxiv_id = paper.get("id", "")
    title = paper.get("title", "Untitled")
    summary = paper.get("ai_summary", paper.get("summary", ""))[:500]
    keywords = paper.get("ai_keywords", [])
    categories = paper.get("categories", ["general"])
    published = paper.get("publishedAt", datetime.now().isoformat())
    
    # Determine category
    category = get_category(categories)
    category_dir = PAPERS_DIR / category
    category_dir.mkdir(parents=True, exist_ok=True)
    
    # Create paper file
    paper_file = category_dir / f"{arxiv_id}.md"
    
    # Format date
    pub_date = datetime.fromisoformat(published.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    
    # Format tags
    tags = " ".join(f"#{kw.replace(' ', '')}" for kw in keywords[:5]) if keywords else "#AGI"
    
    # Image section
    image_section = ""
    if image_url:
        image_section = f"""
## 🎨 図解

![{title}の図解]({image_url})

*この図解は nano-banana-2 で生成された概念図です。*
"""
    
    # Create content
    content = f"""---
title: 📄 {title}
---

# 📄 {title}

## メタデータ

| 項目 | 値 |
|------|-----|
| **arXiv ID** | {arxiv_id} |
| **公開日** | {pub_date} |
| **カテゴリ** | {category.upper()} |
| **タグ** | {tags} |

## リンク

- [arXiv](https://arxiv.org/abs/{arxiv_id})
- [HuggingFace Papers](https://huggingface.co/papers/{arxiv_id})

---

## 📝 要約

{summary}

{image_section}

---

## 💡 解説

### 背景
（自動生成予定）

### 貢献
（自動生成予定）

### 技術的詳細
（自動生成予定）

### 意義
（自動生成予定）

---

## 🔗 関連論文

（自動生成予定）

---

## タグ

{tags}
"""
    
    # Write file
    with open(paper_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Created: {paper_file}")
    return paper_file


def update_index():
    """Update papers/index.md with current paper counts."""
    # Count papers in each category
    categories = {}
    total = 0
    
    for cat_dir in PAPERS_DIR.iterdir():
        if cat_dir.is_dir() and cat_dir.name not in [".", "..", "category"]:
            count = len(list(cat_dir.glob("*.md")))
            if count > 0:
                categories[cat_dir.name.upper()] = count
                total += count
    
    # Create index content
    content = """---
layout: doc
---

# 📚 Papers Knowledge Base

AGI関連論文の図解・解説を蓄積するナレッジベース。

## カテゴリ

"""
    
    # Add category sections
    for cat, count in sorted(categories.items()):
        cat_lower = cat.lower()
        content += f"### {cat}\n\n"
        
        # List papers in this category
        cat_dir = PAPERS_DIR / cat_lower
        if cat_dir.exists():
            for paper_file in sorted(cat_dir.glob("*.md")):
                # Read title from file
                with open(paper_file, "r", encoding="utf-8") as f:
                    first_line = f.readline()
                    title = first_line.replace("title: 📄 ", "").strip()
                    if title.startswith("---"):
                        # Skip frontmatter, find title
                        for line in f:
                            if line.startswith("title:"):
                                title = line.replace("title: 📄 ", "").strip()
                                break
                
                arxiv_id = paper_file.stem
                content += f"- [{title}](/{cat_lower}/{arxiv_id})\n"
        
        content += "\n"
    
    content += f"""---

## 統計

- 総論文数: {total}
- カテゴリ数: {len(categories)}

---

*このナレッジベースは自動的に更新されます。*
"""
    
    # Write index
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ Updated: {INDEX_PATH}")
    print(f"   Total papers: {total}, Categories: {len(categories)}")


def add_paper(paper_data: dict, image_url: Optional[str] = None, update_index_flag: bool = True) -> Path:
    """Add a paper to the knowledge base."""
    paper_file = create_paper_page(paper_data, image_url)
    
    if update_index_flag:
        update_index()
    
    return paper_file


def main():
    parser = argparse.ArgumentParser(
        description="Add paper to Knowledge Base"
    )
    parser.add_argument("--arxiv-id", type=str, help="arXiv paper ID")
    parser.add_argument("--title", type=str, help="Paper title")
    parser.add_argument("--summary", type=str, help="Paper summary")
    parser.add_argument("--image-url", type=str, help="Image URL")
    parser.add_argument("--json", type=str, help="Paper data as JSON file")
    parser.add_argument("--no-update-index", action="store_true",
                       help="Skip index update")
    
    args = parser.parse_args()
    
    # Load paper data
    if args.json:
        with open(args.json, "r") as f:
            paper_data = json.load(f)
    elif args.arxiv_id:
        paper_data = {
            "paper": {
                "id": args.arxiv_id,
                "title": args.title or f"Paper {args.arxiv_id}",
                "summary": args.summary or "",
                "categories": ["general"]
            }
        }
    else:
        print("Error: Either --arxiv-id or --json is required", file=sys.stderr)
        return 1
    
    # Add paper
    paper_file = add_paper(
        paper_data,
        image_url=args.image_url,
        update_index_flag=not args.no_update_index
    )
    
    print(f"\n✅ Paper added to Knowledge Base: {paper_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
