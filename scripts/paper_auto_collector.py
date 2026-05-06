#!/usr/bin/env python3
"""
AI研究論文自動収集・要約システム

arXiv・HuggingFace Papersから最新のAI/AGI研究論文を自動収集し、
要約・図解を生成する統合パイプライン。

機能:
- HuggingFace Daily Papers API連携
- arXiv API連携（cs.AI, cs.LG, cs.CL）
- 自動要約生成
- Discord通知
- ローカル保存（memory/docs/papers/）

Usage:
    python3 scripts/paper_auto_collector.py --source hf --limit 5
    python3 scripts/paper_auto_collector.py --source arxiv --limit 3
    python3 scripts/paper_auto_collector.py --source all --limit 5
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, date
from pathlib import Path

WORKSPACE = Path("/config/.openclaw/workspace")
PAPERS_DIR = WORKSPACE / "memory/docs/papers"
HF_SCRIPT = WORKSPACE / "skills/hf-papers/scripts/hf_papers.py"
ARXIV_SCRIPT = WORKSPACE / "skills/hf-papers/scripts/arxiv_papers.py"
LOG_FILE = WORKSPACE / ".local/state/paper-auto-collector.log"

# Discord webhook
WEBHOOK_FILE = WORKSPACE / "data/x/x-discord-webhook.json"


def log(msg: str):
    ts = datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def run_py(script: str, args: list[str], timeout: int = 120) -> str:
    try:
        r = subprocess.run(
            [sys.executable, script] + args,
            cwd=WORKSPACE, capture_output=True, text=True, timeout=timeout
        )
        return r.stdout.strip()
    except Exception as e:
        log(f"Error running {script}: {e}")
        return ""


def save_collected(papers: list[dict], source: str):
    """Save collected papers to daily JSON."""
    today = date.today().isoformat()
    out_file = PAPERS_DIR / f"collected-{today}.json"

    existing = []
    if out_file.exists():
        with open(out_file) as f:
            existing = json.load(f)

    # Deduplicate by paper id
    seen = {p.get("id", p.get("paper", {}).get("id", "")) for p in existing}
    new_papers = []
    for p in papers:
        pid = p.get("id", p.get("paper", {}).get("id", ""))
        if pid and pid not in seen:
            seen.add(pid)
            p["_source"] = source
            p["_collected_at"] = datetime.now().isoformat()
            new_papers.append(p)

    all_papers = existing + new_papers
    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump(all_papers, f, indent=2, ensure_ascii=False)

    log(f"Saved {len(new_papers)} new papers ({source}) → {out_file}")
    return new_papers


def notify_discord(papers: list[dict], source: str):
    """Send summary to Discord via webhook."""
    if not WEBHOOK_FILE.exists():
        log("No Discord webhook configured, skipping notification")
        return

    with open(WEBHOOK_FILE) as f:
        webhook_data = json.load(f)
    webhook_url = webhook_data.get("url") or webhook_data.get("webhook_url")
    if not webhook_url:
        return

    if not papers:
        log("No new papers to notify")
        return

    today = date.today().isoformat()
    lines = [f"📚 **論文自動収集** ({source}) - {today}", ""]
    for i, p in enumerate(papers[:10], 1):
        title = p.get("title", p.get("paper", {}).get("title", "Unknown"))
        pid = p.get("id", p.get("paper", {}).get("id", ""))
        lines.append(f"**{i}. {title}**")
        if pid:
            lines.append(f"   ID: `{pid}`")

    content = "\n".join(lines)

    payload = {
        "username": "🎋 ONIZUKA Papers",
        "content": content[:1900],
        "allowed_mentions": {"parse": []}
    }

    payload_file = WORKSPACE / ".local/state/paper-notify-payload.json"
    with open(payload_file, "w") as f:
        json.dump(payload, f)

    webhook_script = WORKSPACE / "scripts/discord_webhook_post.py"
    if not webhook_script.exists():
        webhook_script = Path("/config/startup/discord_webhook_post.py")

    if webhook_script.exists():
        run_py(str(webhook_script), [
            "--webhook-url", webhook_url,
            "--payload-file", str(payload_file)
        ])
        log(f"Discord notification sent ({len(papers)} papers)")
    else:
        log("Webhook script not found, skipping")


def collect_hf(limit: int):
    """Collect from HuggingFace Daily Papers."""
    log(f"Collecting from HuggingFace (limit={limit})...")
    output = run_py(str(HF_SCRIPT), ["fetch", "--limit", str(limit)])
    if not output:
        log("No output from HF script")
        return []

    # Save via the save command for structured data
    run_py(str(HF_SCRIPT), [
        "save", "--limit", str(limit),
        "--output-dir", str(PAPERS_DIR),
        "--update-index"
    ])

    # Parse text output for basic paper info
    # Format: "1. [2605.00925] Title Here"
    import re
    papers = []
    for line in output.splitlines():
        m = re.match(r'\d+\.\s+\[([^\]]+)\]\s+(.+)', line.strip())
        if m:
            pid = m.group(1).strip()
            title = m.group(2).strip()
            papers.append({"id": pid, "title": title, "_source": "huggingface"})
    log(f"HF: fetched {len(papers)} papers")
    return papers


def collect_arxiv(limit: int):
    """Collect from arXiv."""
    log(f"Collecting from arXiv (limit={limit})...")
    output = run_py(str(ARXIV_SCRIPT), [
        "fetch", "--max-results", str(limit), "--json"
    ])
    if not output:
        log("No output from arXiv script")
        return []
    try:
        papers = json.loads(output)
        log(f"arXiv: fetched {len(papers)} papers")
        return papers
    except json.JSONDecodeError:
        log(f"arXiv: raw output (first 200): {output[:200]}")
        return []


def main():
    parser = argparse.ArgumentParser(description="AI研究論文自動収集・要約システム")
    parser.add_argument("--source", choices=["hf", "arxiv", "all"], default="all")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--no-notify", action="store_true")
    args = parser.parse_args()

    log(f"=== Paper Auto Collector started (source={args.source}, limit={args.limit}) ===")

    all_new = []

    if args.source in ("hf", "all"):
        papers = collect_hf(args.limit)
        new = save_collected(papers, "huggingface")
        all_new.extend(new)

    if args.source in ("arxiv", "all"):
        papers = collect_arxiv(args.limit)
        new = save_collected(papers, "arxiv")
        all_new.extend(new)

    if all_new and not args.no_notify:
        notify_discord(all_new, args.source)

    log(f"=== Done: {len(all_new)} new papers collected ===")


if __name__ == "__main__":
    main()
