#!/usr/bin/env python3
"""
AGI Papers Collector - 自動論文収集・図解生成
"""

import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# パス設定
WORKSPACE = Path("/config/.openclaw/workspace")
SKILLS_DIR = WORKSPACE / "skills"
PAPERS_DIR = WORKSPACE / "memory/docs/papers"
LOG_FILE = WORKSPACE / ".local/state/papers-collector.log"


def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def run_hf_papers_fetch(limit: int = 3) -> list[dict]:
    """HuggingFace Papersからトップ論文を取得"""
    log(f"Fetching top {limit} papers from HuggingFace...")
    try:
        # top コマンドでトップ論文を取得
        result = subprocess.run(
            ["uv", "run", str(SKILLS_DIR / "hf-papers/scripts/hf_papers.py"), "top", "--limit", str(limit)],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            # 出力をパースして論文IDを抽出
            output = result.stdout
            papers = []
            # arXiv ID形式を抽出 (YYMM.NNNNN)
            ids = re.findall(r'(\d{4}\.\d{4,5})', output)
            for paper_id in ids[:limit]:
                papers.append({"id": paper_id})
            log(f"Fetched {len(papers)} papers: {[p['id'] for p in papers]}")
            return papers
        else:
            log(f"Error fetching papers: {result.stderr}")
            return []
    except Exception as e:
        log(f"Exception: {e}")
        return []


def generate_explanation(paper_id: str) -> bool:
    """論文の図解を生成"""
    log(f"Generating explanation for {paper_id}...")
    try:
        result = subprocess.run(
            ["uv", "run", str(SKILLS_DIR / "hf-papers/scripts/hf_papers.py"), "explain", paper_id],
            cwd=WORKSPACE,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            log(f"Generated explanation for {paper_id}")
            return True
        else:
            log(f"Error generating explanation: {result.stderr[:200]}")
            return False
    except Exception as e:
        log(f"Exception: {e}")
        return False


def main():
    """メイン処理"""
    log("=== Papers Collector Started ===")

    # 1. トップ論文を取得
    papers = run_hf_papers_fetch(limit=3)

    if not papers:
        log("No papers fetched, exiting")
        return 1

    # 2. 各論文の図解を生成
    success_count = 0
    for paper in papers:
        paper_id = paper.get("id", "")
        if paper_id:
            if generate_explanation(paper_id):
                success_count += 1

    log(f"=== Papers Collector Completed: {success_count}/{len(papers)} papers processed ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
