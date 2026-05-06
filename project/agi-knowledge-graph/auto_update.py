#!/usr/bin/env python3
"""
AGI Knowledge Graph Auto-Update Pipeline

HuggingFace Papers / arXiv から最新論文を取得し、
ナレッジグラフ (knowledge_graph.json) を自動更新する。

Usage:
    python auto_update.py          - 全パイプライン実行
    python auto_update.py --fetch  - 論文取得のみ
    python auto_update.py --build  - グラフ再構築のみ
    python auto_update.py --stats  - 統計表示

#510 定期ミーティング / AGI Knowledge Graph 自動更新パイプライン
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CACHE_FILE = PROJECT_ROOT / "papers_cache.json"
GRAPH_FILE = PROJECT_ROOT / "knowledge_graph.json"
STATE_FILE = PROJECT_ROOT / "update_state.json"

# ワークスペースのHF/arXivパス
WORKSPACE = Path("/config/.openclaw/workspace")
HF_SCRIPT = WORKSPACE / "skills/hf-papers/scripts/hf_papers.py"
ARXIV_SCRIPT = WORKSPACE / "skills/hf-papers/scripts/arxiv_papers.py"


def load_cache() -> dict:
    """論文キャッシュを読み込み"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"papers": []}


def save_cache(data: dict):
    """論文キャッシュを保存"""
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_state() -> dict:
    """更新状態を読み込み"""
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"last_fetch": None, "last_build": None, "total_fetches": 0, "total_papers_added": 0}


def save_state(state: dict):
    """更新状態を保存"""
    state["last_run"] = datetime.now().isoformat()
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_papers(max_papers: int = 10) -> list[dict]:
    """HuggingFace Papersから最新論文を取得"""
    import subprocess
    papers = []
    
    cmd = ["uv", "run", str(HF_SCRIPT), "fetch", "--top", str(max_papers)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE))
        if result.returncode == 0:
            # JSON出力をパース
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.startswith("{") or line.startswith("["):
                    try:
                        data = json.loads(line)
                        if isinstance(data, list):
                            papers.extend(data)
                        elif isinstance(data, dict):
                            papers.append(data)
                    except json.JSONDecodeError:
                        pass
            print(f"  HF Papers: {len(papers)}件取得")
        else:
            print(f"  HF Papers: エラー - {result.stderr[:200]}")
    except Exception as e:
        print(f"  HF Papers: 例外 - {e}")
    
    return papers


def fetch_arxiv(categories: str = "cs.AI,cs.LG", max_papers: int = 10) -> list[dict]:
    """arXivから最新論文を取得"""
    import subprocess
    papers = []
    
    cmd = ["uv", "run", str(ARXIV_SCRIPT), "fetch", "--categories", categories, "--max", str(max_papers)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE))
        if result.returncode == 0:
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.startswith("{") or line.startswith("["):
                    try:
                        data = json.loads(line)
                        if isinstance(data, list):
                            papers.extend(data)
                        elif isinstance(data, dict):
                            papers.append(data)
                    except json.JSONDecodeError:
                        pass
            print(f"  arXiv: {len(papers)}件取得")
        else:
            print(f"  arXiv: エラー - {result.stderr[:200]}")
    except Exception as e:
        print(f"  arXiv: 例外 - {e}")
    
    return papers


def merge_papers(existing: list[dict], new_papers: list[dict]) -> tuple[list[dict], int]:
    """新規論文を既存キャッシュにマージ（重複排除）"""
    existing_ids = set()
    existing_titles = set()
    
    for p in existing:
        pid = p.get("id", p.get("arxiv_id", p.get("title", "")))
        existing_ids.add(pid)
        existing_titles.add(p.get("title", "").lower().strip())
    
    added = 0
    for paper in new_papers:
        pid = paper.get("id", paper.get("arxiv_id", paper.get("title", "")))
        title = paper.get("title", "").lower().strip()
        
        if pid not in existing_ids and title not in existing_titles:
            paper["_fetched_at"] = datetime.now().isoformat()
            existing.append(paper)
            existing_ids.add(pid)
            existing_titles.add(title)
            added += 1
    
    return existing, added


def rebuild_graph():
    """graph_engine.pyを使ってグラフを再構築"""
    import subprocess
    
    cmd = [sys.executable, str(PROJECT_ROOT / "graph_engine.py"), "build"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.stderr:
            print(result.stderr[:500])
    except Exception as e:
        print(f"  グラフ構築エラー: {e}")


def run_pipeline(max_papers: int = 10):
    """全パイプライン実行"""
    state = load_state()
    cache = load_cache()
    
    print(f"=== AGI Knowledge Graph Auto-Update ===")
    print(f"既存論文数: {len(cache.get('papers', []))}")
    
    # 1. 論文取得
    print("\n📖 論文取得中...")
    hf_papers = fetch_papers(max_papers)
    arxiv_papers = fetch_arxiv(max_papers=max_papers)
    
    all_new = hf_papers + arxiv_papers
    print(f"  取得合計: {len(all_new)}件")
    
    # 2. マージ
    print("\n🔄 マージ中...")
    papers, added = merge_papers(cache.get("papers", []), all_new)
    cache["papers"] = papers
    print(f"  新規追加: {added}件")
    print(f"  総論文数: {len(papers)}件")
    
    # 3. キャッシュ保存
    save_cache(cache)
    
    # 4. グラフ再構築
    if added > 0:
        print("\n🏗️ グラフ再構築中...")
        rebuild_graph()
    else:
        print("\n✅ 新規論文なし。グラフ更新不要。")
    
    # 5. 状態保存
    state["last_fetch"] = datetime.now().isoformat()
    state["last_build"] = datetime.now().isoformat()
    state["total_fetches"] = state.get("total_fetches", 0) + 1
    state["total_papers_added"] = state.get("total_papers_added", 0) + added
    save_state(state)
    
    print(f"\n=== 完了 ===")
    print(f"新規追加: {added}件 / 総論文数: {len(papers)}件")
    
    return {"added": added, "total": len(papers), "hf": len(hf_papers), "arxiv": len(arxiv_papers)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AGI Knowledge Graph Auto-Update")
    parser.add_argument("--fetch", action="store_true", help="論文取得のみ")
    parser.add_argument("--build", action="store_true", help="グラフ再構築のみ")
    parser.add_argument("--stats", action="store_true", help="統計表示")
    parser.add_argument("--max", type=int, default=10, help="取得最大数")
    args = parser.parse_args()
    
    if args.stats:
        cache = load_cache()
        state = load_state()
        print(f"総論文数: {len(cache.get('papers', []))}")
        print(f"総取得回数: {state.get('total_fetches', 0)}")
        print(f"総追加論文数: {state.get('total_papers_added', 0)}")
        print(f"最終取得: {state.get('last_fetch', 'N/A')}")
        print(f"最終構築: {state.get('last_build', 'N/A')}")
    elif args.build:
        rebuild_graph()
    elif args.fetch:
        state = load_state()
        cache = load_cache()
        hf = fetch_papers(args.max)
        arxiv = fetch_arxiv(max_papers=args.max)
        papers, added = merge_papers(cache.get("papers", []), hf + arxiv)
        cache["papers"] = papers
        save_cache(cache)
        state["last_fetch"] = datetime.now().isoformat()
        save_state(state)
        print(f"新規追加: {added} / 総: {len(papers)}")
    else:
        run_pipeline(args.max)
