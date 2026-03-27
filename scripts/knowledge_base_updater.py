#!/usr/bin/env python3
"""
AGI Knowledge Base 定期更新スクリプト

memory/docs/ からハッシュタグ別に知見を集約し、KNOWLEDGE.mdを更新する。
data/papers/ から論文情報を集約する。
毎日09:00にs6サービスとして実行される。

Issue #193: AGI Knowledge Base 定期更新自動化
"""

import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import json
import requests

# パス設定
WORKSPACE = Path("/config/.openclaw/workspace")
MEMORY_DOCS = WORKSPACE / "memory" / "docs"
PAPERS_DIR = WORKSPACE / "data" / "papers"
KNOWLEDGE_MD = WORKSPACE / "memory" / "KNOWLEDGE.md"
STATE_FILE = WORKSPACE / "data" / "knowledge-base-state.json"
WEBHOOK_FILE = WORKSPACE / "data" / "x" / "x-discord-webhook.json"


def extract_hashtags(content: str) -> list[str]:
    """Markdownからハッシュタグを抽出"""
    return re.findall(r'#(\w+)', content)


def extract_frontmatter(content: str) -> dict:
    """YAMLフロントマターを抽出"""
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = {}
            for line in parts[1].strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    frontmatter[key.strip()] = value.strip()
            return frontmatter
    return {}


def get_last_run_time() -> datetime:
    """前回実行時刻を取得"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
            return datetime.fromisoformat(state.get('last_run', '2026-01-01'))
    return datetime(2026, 1, 1)


def save_run_time():
    """実行時刻を保存"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump({'last_run': datetime.now().isoformat()}, f)


def scan_daily_reports(since: datetime) -> list[dict]:
    """指定日時以降の日報をスキャン"""
    reports = []
    
    for year_dir in MEMORY_DOCS.iterdir():
        if not year_dir.is_dir() or not year_dir.name.isdigit():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir() or not month_dir.name.isdigit():
                continue
            for day_dir in month_dir.iterdir():
                if not day_dir.is_dir() or not day_dir.name.isdigit():
                    continue
                
                index_file = day_dir / "index.md"
                if not index_file.exists():
                    continue
                
                # ファイル更新時刻をチェック
                mtime = datetime.fromtimestamp(index_file.stat().st_mtime)
                if mtime < since:
                    continue
                
                with open(index_file) as f:
                    content = f.read()
                
                frontmatter = extract_frontmatter(content)
                hashtags = extract_hashtags(content)
                
                reports.append({
                    'path': str(index_file.relative_to(MEMORY_DOCS)),
                    'date': f"{year_dir.name}-{month_dir.name}-{day_dir.name}",
                    'title': frontmatter.get('title', f'{year_dir.name}-{month_dir.name}-{day_dir.name} 日報'),
                    'hashtags': hashtags,
                    'mtime': mtime.isoformat()
                })
    
    return reports


def generate_knowledge_md(reports: list[dict]) -> str:
    """KNOWLEDGE.mdを生成"""
    # ハッシュタグ別にグループ化
    by_tag = defaultdict(list)
    for report in reports:
        for tag in report['hashtags']:
            by_tag[tag].append(report)
    
    # Markdown生成
    lines = [
        "# 📚 AGI Knowledge Base",
        "",
        f"_最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        "## 📊 統計",
        "",
        f"- 日報数: {len(reports)}",
        f"- ハッシュタグ数: {len(by_tag)}",
        "",
        "## 🏷️ ハッシュタグ別一覧",
        "",
    ]
    
    # タグ別セクション（出現数順）
    for tag, tag_reports in sorted(by_tag.items(), key=lambda x: -len(x[1])):
        lines.append(f"### #{tag}")
        lines.append("")
        for report in tag_reports[:10]:  # 最大10件
            lines.append(f"- [{report['date']}]({report['path']})")
        if len(tag_reports) > 10:
            lines.append(f"- _他 {len(tag_reports) - 10} 件_")
        lines.append("")
    
    # 最近の日報
    lines.extend([
        "## 📅 最近の日報",
        "",
    ])
    for report in sorted(reports, key=lambda x: x['date'], reverse=True)[:20]:
        lines.append(f"- [{report['date']}]({report['path']})")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("_このファイルは自動生成されています。_")
    
    return '\n'.join(lines)


def scan_papers(since: datetime) -> list[dict]:
    """data/papers/から論文情報をスキャン"""
    papers = []
    
    if not PAPERS_DIR.exists():
        return papers
    
    for paper_file in PAPERS_DIR.glob("**/*.md"):
        if paper_file.name == "index.md":
            continue
        
        mtime = datetime.fromtimestamp(paper_file.stat().st_mtime)
        if mtime < since:
            continue
        
        with open(paper_file) as f:
            content = f.read()
        
        frontmatter = extract_frontmatter(content)
        papers.append({
            'path': str(paper_file.relative_to(WORKSPACE)),
            'title': frontmatter.get('title', paper_file.stem),
            'mtime': mtime.isoformat()
        })
    
    return papers


def send_discord_notification(reports_count: int, papers_count: int, total_reports: int):
    """Discordに更新通知を送信"""
    if not WEBHOOK_FILE.exists():
        print("  Webhook file not found, skipping notification")
        return
    
    with open(WEBHOOK_FILE) as f:
        webhook_data = json.load(f)
    
    webhook_url = webhook_data.get('webhook_url')
    if not webhook_url:
        print("  Webhook URL not found, skipping notification")
        return
    
    embed = {
        "title": "📊 AGI Knowledge Base 更新完了",
        "color": 0x4CAF50,
        "fields": [
            {"name": "新規日報", "value": f"{reports_count}件", "inline": True},
            {"name": "新規論文", "value": f"{papers_count}件", "inline": True},
            {"name": "総日報数", "value": f"{total_reports}件", "inline": True},
        ],
        "footer": {"text": f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M')}"},
    }
    
    payload = {
        "username": "朱燈烏 🔔",
        "embeds": [embed]
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 204:
            print("  Discord通知: 送信完了")
        else:
            print(f"  Discord通知: エラー ({response.status_code})")
    except Exception as e:
        print(f"  Discord通知: エラー ({e})")


def main():
    """メイン処理"""
    print("🎋 AGI Knowledge Base 更新開始")
    
    # 前回実行時刻を取得
    since = get_last_run_time()
    print(f"  前回実行: {since.strftime('%Y-%m-%d %H:%M')}")
    
    # 日報をスキャン
    reports = scan_daily_reports(since)
    print(f"  対象日報: {len(reports)}件")
    
    # 論文をスキャン
    papers = scan_papers(since)
    print(f"  対象論文: {len(papers)}件")
    
    # 全日報も含めてKNOWLEDGE.mdを生成
    all_reports = scan_daily_reports(datetime(2026, 1, 1))
    print(f"  全日報: {len(all_reports)}件")
    
    # KNOWLEDGE.mdを生成
    content = generate_knowledge_md(all_reports)
    with open(KNOWLEDGE_MD, 'w') as f:
        f.write(content)
    print(f"  生成完了: {KNOWLEDGE_MD}")
    
    # 実行時刻を保存
    save_run_time()
    
    # Discord通知
    send_discord_notification(len(reports), len(papers), len(all_reports))
    
    print("🎋 完了")


if __name__ == "__main__":
    main()
