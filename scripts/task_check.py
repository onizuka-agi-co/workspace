#!/usr/bin/env python3
"""
TASK.mdを確認して、未着手タスクをDiscordに通知するスクリプト
cronで定期実行する用
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

# 設定
TASK_FILE = Path(__file__).parent.parent / "TASK.md"
WEBHOOK_URL = "https://discord.com/api/webhooks/1476205313161039882/ScTBkb-nsuT-GRtujYjil2A-Q85uXkuhGEHXRcbmDghdZq2liCxKSkLmeoAf72gY19Zo"
AGENT_ID = "1475431819565469706"
CHANNEL_ID = "1475880463800205315"


def parse_tasks(content: str) -> dict:
    """TASK.mdからタスクを抽出"""
    tasks = {
        "high": [],
        "medium": [],
        "low": [],
        "in_progress": [],
        "completed": []
    }
    
    current_section = None
    
    for line in content.split("\n"):
        # セクション判定
        if "優先度: 高" in line or "🔴" in line:
            current_section = "high"
        elif "優先度: 中" in line or "🟡" in line:
            current_section = "medium"
        elif "優先度: 低" in line or "🟢" in line:
            current_section = "low"
        elif "進行中" in line or "🔄" in line:
            current_section = "in_progress"
        elif "完了" in line or "✅" in line:
            current_section = "completed"
        
        # 未着手タスク抽出
        if current_section and current_section != "completed":
            match = re.match(r"- \[ \] (.+)", line)
            if match:
                task_name = match.group(1).strip()
                tasks[current_section].append(task_name)
    
    return tasks


def format_message(tasks: dict) -> str:
    """Discord用メッセージを作成"""
    pending = tasks["high"] + tasks["medium"] + tasks["low"]
    
    if not pending:
        return f"<@{AGENT_ID}> 🎋 **TASK確認** ({datetime.now().strftime('%H:%M')})\n\n未着手タスク: **なし**\n\nTASK.mdに新しいタスクを追加してください。"
    
    lines = [f"<@{AGENT_ID}> 🎋 **TASK確認** ({datetime.now().strftime('%H:%M')})"]
    lines.append(f"\n未着手タスク: **{len(pending)}件**\n")
    
    if tasks["high"]:
        lines.append("🔴 **高優先度**")
        for t in tasks["high"]:
            lines.append(f"  - {t}")
    
    if tasks["medium"]:
        lines.append("🟡 **中優先度**")
        for t in tasks["medium"]:
            lines.append(f"  - {t}")
    
    if tasks["low"]:
        lines.append("🟢 **低優先度**")
        for t in tasks["low"]:
            lines.append(f"  - {t}")
    
    return "\n".join(lines)


def send_to_discord(message: str) -> bool:
    """WebhookでDiscordに送信"""
    import urllib.request
    import urllib.error
    
    # シンプルなメッセージのみ送信
    data = json.dumps({
        "content": message
    }).encode("utf-8")
    
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; OpenClaw/1.0)"
        }
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status == 204 or res.status == 200
    except urllib.error.URLError as e:
        print(f"Webhook error: {e}", file=sys.stderr)
        return False


def main():
    # TASK.md読み込み
    if not TASK_FILE.exists():
        print("TASK.md not found", file=sys.stderr)
        sys.exit(1)
    
    content = TASK_FILE.read_text(encoding="utf-8")
    tasks = parse_tasks(content)
    
    # メッセージ作成
    message = format_message(tasks)
    
    # Discord送信
    if send_to_discord(message):
        print("Sent to Discord successfully")
    else:
        print("Failed to send to Discord", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
