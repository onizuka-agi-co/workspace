#!/usr/bin/env python3
"""
AGI Papers Collector - 自動論文収集（HuggingFace + arXiv）

HuggingFace Daily PapersとarXivからAGI関連論文を自動収集し、
ローカルに保存するクローラー。
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# パス設定
WORKSPACE = Path("/config/.openclaw/workspace")
SKILLS_DIR = WORKSPACE / "skills"
PAPERS_DIR = WORKSPACE / "memory/docs/papers"
HF_SCRIPT = SKILLS_DIR / "hf-papers/scripts/hf_papers.py"
ARXIV_SCRIPT = SKILLS_DIR / "hf-papers/scripts/arxiv_papers.py"
LOG_FILE = WORKSPACE / ".local/state/papers-collector.log"

# AGI関連キーワード
AGI_KEYWORDS = [
    "AGI", "artificial general intelligence",
    "reasoning", "planning", "world model",
    "autonomous agent", "multi-agent", "tool use",
    "meta-learning", "few-shot", "in-context learning",
    "foundation model", "scaling law", "large language model",
    "chain-of-thought", "self-play", "reward model",
    "RLHF", "alignment", "embodied",
]


def log(message: str):
    """ログ出力"""
    timestamp = datetime.now().isoformat()
    line = f"[{timestamp}] {message}"
    print(line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_cmd(args: list[str], timeout: int = 120) -> tuple[bool, str]:
    """コマンド実行"""
    try:
        result = subprocess.run(
            args, cwd=WORKSPACE,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def fetch_hf_papers(limit: int = 5) -> list[dict]:
    """HuggingFace Daily Papersからトップ論文を取得"""
    log(f"Fetching top {limit} papers from HuggingFace...")
    ok, output = run_cmd(
        ["uv", "run", str(HF_SCRIPT), "top", "--limit", str(limit)],
        timeout=60,
    )
    if not ok:
        log(f"HF fetch error: {output[:200]}")
        return []

    # arXiv ID抽出
    ids = list(dict.fromkeys(re.findall(r'(\d{4}\.\d{4,5})', output)))
    papers = [{"id": pid, "source": "huggingface"} for pid in ids[:limit]]
    log(f"HF: fetched {len(papers)} papers: {[p['id'] for p in papers]}")
    return papers


def fetch_arxiv_papers(limit: int = 10) -> list[dict]:
    """arXivからAGI関連論文を取得"""
    log(f"Fetching {limit} papers from arXiv...")
    ok, output = run_cmd(
        ["uv", "run", str(ARXIV_SCRIPT), "fetch",
         "--query", "cat:cs.AI OR cat:cs.LG OR cat:cs.CL",
         "--limit", str(limit), "--json"],
        timeout=120,
    )
    if not ok:
        log(f"arXiv fetch error: {output[:200]}")
        return []

    try:
        papers = json.loads(output)
    except json.JSONDecodeError:
        # JSONが混ざっている場合を考慮
        json_match = re.search(r'\[.*\]', output, re.DOTALL)
        if json_match:
            papers = json.loads(json_match.group())
        else:
            log("arXiv: failed to parse JSON output")
            return []

    for p in papers:
        p["source"] = "arxiv"
    log(f"arXiv: fetched {len(papers)} papers")
    return papers


def score_agi_relevance(paper: dict) -> float:
    """AGI関連度をスコアリング"""
    text = f"{paper.get('title', '')} {paper.get('summary', '')}".lower()
    score = 0.0
    for kw in AGI_KEYWORDS:
        if kw.lower() in text:
            score += 1.0
    return score


def save_papers(papers: list[dict], output_dir: Path):
    """論文をローカルに保存"""
    output_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    outfile = output_dir / f"collected-{today}.json"

    # 既存ファイルがあればマージ
    existing = []
    if outfile.exists():
        try:
            with open(outfile) as f:
                existing = json.load(f)
        except Exception:
            pass

    existing_ids = {p.get("id") for p in existing}
    new_papers = [p for p in papers if p.get("id") not in existing_ids]

    all_papers = existing + new_papers
    with open(outfile, "w") as f:
        json.dump(all_papers, f, indent=2, ensure_ascii=False)

    log(f"Saved {len(new_papers)} new papers to {outfile} (total: {len(all_papers)})")
    return new_papers


def main():
    log("=== Papers Collector Started ===")

    # 1. HuggingFace Papers
    hf_papers = fetch_hf_papers(limit=5)

    # 2. arXiv Papers
    arxiv_papers = fetch_arxiv_papers(limit=10)

    # 3. 統合
    all_papers = hf_papers + arxiv_papers
    if not all_papers:
        log("No papers fetched, exiting")
        return 1

    # 4. AGI関連度スコアリング
    for p in all_papers:
        p["agi_score"] = score_agi_relevance(p)
    all_papers.sort(key=lambda x: x.get("agi_score", 0), reverse=True)

    # 5. 保存
    new = save_papers(all_papers, PAPERS_DIR)

    log(f"=== Papers Collector Completed: {len(new)} new, {len(all_papers)} total ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
