#!/usr/bin/env python3
"""
Quote Retweet to Community - シンプル版
指定したポストを引用して、解説付きでコミュニティに投稿

使い方:
    uv run scripts/quote_to_community.py <ポストURL> "解説文"

例:
    uv run scripts/quote_to_community.py https://x.com/user/status/123 "これは面白い記事です！"
"""

import json
import urllib.request
import urllib.parse
import urllib.error
import base64
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# 設定
COMMUNITY_ID = "2010195061309587967"  # Sunwood AI OSS Hub
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "x"
TOKEN_FILE = DATA_DIR / "x-tokens.json"
CLIENT_CREDENTIALS_FILE = DATA_DIR / "x-client-credentials.json"
LOG_DIR = Path(__file__).parent.parent / "logs"


def extract_tweet_id(url_or_id):
    """ポストURLからIDを抽出"""
    if url_or_id.isdigit():
        return url_or_id
    match = re.search(r'(?:x\.com|twitter\.com)/\w+/status/(\d+)', url_or_id)
    return match.group(1) if match else None


def save_log(original_tweet_id, original_text, post_id, post_text):
    """投稿ログを保存"""
    # 日付フォルダ作成
    today = datetime.now().strftime("%Y-%m-%d")
    date_dir = LOG_DIR / today
    date_dir.mkdir(parents=True, exist_ok=True)
    
    # タイムスタンプ付きファイル名
    timestamp = datetime.now().strftime("%H-%M-%S")
    log_file = date_dir / f"{timestamp}_{original_tweet_id}.json"
    
    # ログデータ
    log_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_tweet": {
            "id": original_tweet_id,
            "text": original_text,
            "url": f"https://x.com/i/status/{original_tweet_id}"
        },
        "community_post": {
            "id": post_id,
            "text": post_text,
            "url": f"https://x.com/i/status/{post_id}"
        }
    }
    
    # 保存
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    return log_file


class Client:
    def __init__(self):
        self._load_tokens()
        self._load_credentials()
    
    def _load_tokens(self):
        with open(TOKEN_FILE, 'r') as f:
            data = json.load(f)
            self.access_token = data.get('access_token')
            self.refresh_token = data.get('refresh_token')
            self.expires_at = datetime.now(timezone.utc).timestamp() + data.get('expires_in', 0) if 'expires_in' in data else None
    
    def _load_credentials(self):
        with open(CLIENT_CREDENTIALS_FILE, 'r') as f:
            data = json.load(f)
            self.client_id = data.get('client_id')
            self.client_secret = data.get('client_secret')
    
    def _refresh_token(self):
        basic_auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        body = urllib.parse.urlencode({'grant_type': 'refresh_token', 'refresh_token': self.refresh_token})
        req = urllib.request.Request(
            "https://api.x.com/2/oauth2/token",
            data=body.encode(),
            headers={'Authorization': f'Basic {basic_auth}', 'Content-Type': 'application/x-www-form-urlencoded'},
            method='POST'
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            with open(TOKEN_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            self.access_token = data['access_token']
            self.refresh_token = data['refresh_token']
    
    def _ensure_token(self):
        if self.expires_at and datetime.now(timezone.utc).timestamp() > (self.expires_at - 300):
            self._refresh_token()
        return self.access_token
    
    def _api(self, method, endpoint, data=None):
        token = self._ensure_token()
        headers = {'Authorization': f'Bearer {token}'}
        body = json.dumps(data).encode() if data else None
        if body:
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(f"https://api.x.com{endpoint}", data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"API error {e.code}: {e.read().decode()}")
    
    def get_tweet(self, tweet_id):
        """ツイート情報を取得"""
        return self._api('GET', f'/2/tweets/{tweet_id}?tweet.fields=author_id,created_at,text')
    
    def post_to_community(self, text):
        """コミュニティに投稿"""
        return self._api('POST', '/2/tweets', {
            'text': text,
            'community_id': COMMUNITY_ID,
            'share_with_followers': True
        })


def main():
    if len(sys.argv) < 3:
        print("Quote Retweet to Community")
        print()
        print("使い方:")
        print("  uv run scripts/quote_to_community.py <ポストURL> \"解説文\"")
        print()
        print("例:")
        print("  uv run scripts/quote_to_community.py https://x.com/user/status/123 \"解説文\"")
        sys.exit(1)
    
    post_url = sys.argv[1]
    commentary = sys.argv[2]
    
    # ID抽出
    tweet_id = extract_tweet_id(post_url)
    if not tweet_id:
        print(f"エラー: 無効なポストURL: {post_url}")
        sys.exit(1)
    
    # 投稿テキスト作成
    full_url = f"https://x.com/i/status/{tweet_id}"
    post_text = f"{commentary}\n\n{full_url}"
    
    # 投稿
    client = Client()
    
    # 元ツイート情報を取得
    try:
        tweet_info = client.get_tweet(tweet_id)
        original_text = tweet_info.get('data', {}).get('text', '')
    except:
        original_text = "(取得エラー)"
    
    result = client.post_to_community(post_text)
    
    print(json.dumps(result, indent=2))
    
    # ログ保存
    if 'data' in result:
        post_id = result['data']['id']
        log_file = save_log(tweet_id, original_text, post_id, post_text)
        
        print()
        print(f"✅ 投稿完了: https://x.com/i/status/{post_id}")
        print(f"📝 ログ保存: {log_file}")


if __name__ == "__main__":
    main()
