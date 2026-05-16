#!/usr/bin/env python3
"""
🔗 Citation Sentinel - Discord Webhook通知スクリプト

Citation SentinelのレポートをDiscord WebhookにEmbed形式で通知する。

Usage:
  python3 citation_webhook.py --report   # Send latest report via webhook
  python3 citation_webhook.py --daily    # Run report + send webhook
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# --- Config ---
DATA_DIR = Path(__file__).parent / "data"
REPORT_FILE = DATA_DIR / "latest_report.json"
BASELINE_FILE = DATA_DIR / "citation_baseline.json"

# Discord webhook from env or file
def get_webhook_url():
    url = os.environ.get("DISCORD_WEBHOOK_URL", "")
    if url:
        return url
    webhook_file = Path(__file__).parent.parent.parent / "data" / "x" / "x-discord-webhook.json"
    if webhook_file.exists():
        data = json.loads(webhook_file.read_text())
        return data.get("webhook_url", "")
    return ""

# Colors
COLOR_CITATION_SPIKE = 0xC41E3A  # 朱 - 急増
COLOR_TRENDING = 0x2196F3        # 青 - 注目
COLOR_NORMAL = 0x4CAF50          # 緑 - 通常

def send_webhook(webhook_url, payload):
    """Send embed payload to Discord webhook."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "CitationSentinel/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 204
    except urllib.error.HTTPError as e:
        print(f"Webhook error {e.code}: {e.reason}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Webhook error: {e}", file=sys.stderr)
        return False

def build_spike_embed(spike):
    """Build embed for a citation spike."""
    pct = f"+{spike['pctChange']}%" if spike.get("pctChange") else ""
    delta = f"+{spike['delta']}" if spike.get("delta") else ""
    return {
        "title": f"🔥 {spike['title'][:80]}",
        "color": COLOR_CITATION_SPIKE,
        "fields": [
            {"name": "引用数", "value": f"**{spike['citationCount']}** ({delta})", "inline": True},
            {"name": "変化率", "value": pct, "inline": True},
            {"name": "前回", "value": str(spike.get("previousCount", "?")), "inline": True},
        ],
        "footer": {"text": "🔗 Citation Sentinel"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def build_summary_embed(report):
    """Build summary embed for daily report."""
    spike_count = len(report.get("spikes", []))
    total = report.get("total_papers", 0)
    
    color = COLOR_CITATION_SPIKE if spike_count > 0 else COLOR_NORMAL
    
    top_lines = []
    for i, p in enumerate(report.get("top_cited", [])[:5], 1):
        title = p.get("title", "N/A")[:45]
        top_lines.append(f"{i}. {p.get('citations', 0):>5} cites | {title}")
    top_text = "\n".join(top_lines) if top_lines else "No data"

    spike_text = f"**{spike_count}件のスパイク検知**" if spike_count > 0 else "スパイクなし"

    return {
        "title": "📊 Citation Sentinel 日次レポート",
        "color": color,
        "fields": [
            {"name": "分析論文数", "value": str(total), "inline": True},
            {"name": "スパイク検知", "value": spike_text, "inline": True},
        ],
        "description": f"**Top Cited:**\n```\n{top_text}\n```",
        "footer": {"text": "🔗 Citation Sentinel | ONIZUKA AGI Co."},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

def send_report(args):
    """Send the latest report via webhook."""
    webhook_url = get_webhook_url()
    if not webhook_url:
        print("ERROR: No webhook URL configured", file=sys.stderr)
        sys.exit(1)

    if not REPORT_FILE.exists():
        print("No report file found. Run `report` command first.", file=sys.stderr)
        sys.exit(1)

    report = json.loads(REPORT_FILE.read_text())
    embeds = [build_summary_embed(report)]

    for spike in report.get("spikes", [])[:3]:
        embeds.append(build_spike_embed(spike))

    payload = {
        "username": "🔗 Citation Sentinel",
        "embeds": embeds,
        "allowed_mentions": {"parse": []},
    }

    if send_webhook(webhook_url, payload):
        print(f"✅ Sent webhook: {len(embeds)} embeds")
    else:
        print("❌ Failed to send webhook", file=sys.stderr)
        sys.exit(1)

def run_daily(args):
    """Run report generation + webhook notification."""
    from citation_sentinel import cmd_report

    print("📋 Running daily citation report...")
    report = cmd_report(argparse.Namespace())

    # Save report
    webhook_url = get_webhook_url()
    if webhook_url:
        embeds = [build_summary_embed(report)]
        for spike in report.get("spikes", [])[:3]:
            embeds.append(build_spike_embed(spike))

        payload = {
            "username": "🔗 Citation Sentinel",
            "embeds": embeds,
            "allowed_mentions": {"parse": []},
        }
        send_webhook(webhook_url, payload)
        print(f"✅ Webhook sent: {len(embeds)} embeds")
    else:
        print("⚠️ No webhook URL configured, skipping notification")

def main():
    parser = argparse.ArgumentParser(description="🔗 Citation Sentinel - Discord通知")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("report", help="Send latest report via webhook")
    sub.add_parser("daily", help="Run report + send webhook")

    args = parser.parse_args()
    if args.command == "report":
        send_report(args)
    elif args.command == "daily":
        run_daily(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
