#!/usr/bin/env python3
"""Discord Webhook投稿テスト"""

import urllib.request
import urllib.error
import json

WEBHOOK_URL = "https://discord.com/api/webhooks/1476205310162243760/7oDPhSJ6JHWPCScHKhJWM0XzcZCtZTUjpnq8peMgNIN93303wZmH21xS2Fg9b1VrkEq0"

def send_webhook(message: str):
    """Webhookでメッセージを送信"""
    payload = {
        "content": message,
        "username": "朱燈烏",
        "avatar_url": "https://raw.githubusercontent.com/onizuka-agi-co/.github/main/profile/onizuka-icon.png"
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

if __name__ == "__main__":
    status, body = send_webhook("🎋 Webhook接続テスト完了 — 朱燈烏より")
    print(f"Status: {status}")
    print(f"Response: {body if body else '(empty - success)'}")
