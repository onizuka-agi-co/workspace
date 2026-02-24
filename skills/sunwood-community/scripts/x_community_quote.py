#!/usr/bin/env python3
"""
X Community Quote Client for OpenClaw
Quote a tweet with commentary and post to community
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

# Token file paths (relative to workspace root)
DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "x"
TOKEN_FILE = DATA_DIR / "x-tokens.json"
CLIENT_CREDENTIALS_FILE = DATA_DIR / "x-client-credentials.json"
CONFIG_FILE = DATA_DIR / "x-community-config.json"

# Default community ID
DEFAULT_COMMUNITY_ID = "2010195061309587967"

# Templates
TEMPLATES = {
    "notable": "🔍 注目ポスト解説\n\n{commentary}\n\n{url}",
    "news": "📰 ニュース紹介\n\n{commentary}\n\n{url}",
    "tip": "💡 Tips・豆知識\n\n{commentary}\n\n{url}",
}


def extract_tweet_id(url_or_id):
    """Extract tweet ID from URL or return as-is if already an ID"""
    if url_or_id.isdigit():
        return url_or_id
    match = re.search(r'(?:x\.com|twitter\.com)/\w+/status/(\d+)', url_or_id)
    if match:
        return match.group(1)
    return None


class XCommunityQuoteClient:
    def __init__(self):
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.client_id = None
        self.client_secret = None
        self.community_id = DEFAULT_COMMUNITY_ID
        self._load_tokens()
        self._load_credentials()
        self._load_config()
    
    def _load_tokens(self):
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                data = json.load(f)
                self.access_token = data.get('access_token')
                self.refresh_token = data.get('refresh_token')
                if 'expires_in' in data:
                    self.expires_at = datetime.now(timezone.utc).timestamp() + data['expires_in']
    
    def _load_credentials(self):
        if CLIENT_CREDENTIALS_FILE.exists():
            with open(CLIENT_CREDENTIALS_FILE, 'r') as f:
                data = json.load(f)
                self.client_id = data.get('client_id')
                self.client_secret = data.get('client_secret')
    
    def _load_config(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self.community_id = data.get('community_id', DEFAULT_COMMUNITY_ID)
    
    def _save_tokens(self, data):
        with open(TOKEN_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        self._load_tokens()
    
    def _save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'community_id': self.community_id}, f, indent=2)
    
    def is_token_expired(self):
        if not self.expires_at:
            return True
        return datetime.now(timezone.utc).timestamp() > (self.expires_at - 300)
    
    def refresh_access_token(self):
        if not self.refresh_token or not self.client_id or not self.client_secret:
            raise Exception("Missing refresh token or client credentials")
        
        basic_auth = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        body = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        })
        
        req = urllib.request.Request(
            "https://api.x.com/2/oauth2/token",
            data=body.encode(),
            headers={
                'Authorization': f'Basic {basic_auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            method='POST'
        )
        
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            self._save_tokens(data)
            return data
    
    def _ensure_valid_token(self):
        if self.is_token_expired():
            self.refresh_access_token()
        return self.access_token
    
    def _api_request(self, method, endpoint, params=None, data=None):
        token = self._ensure_valid_token()
        url = f"https://api.x.com{endpoint}"
        if params:
            url += "?" + urllib.parse.urlencode(params)
        
        headers = {'Authorization': f'Bearer {token}'}
        body = None
        
        if data:
            headers['Content-Type'] = 'application/json'
            body = json.dumps(data).encode()
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            raise Exception(f"API error: {e.code} - {error_body}")
    
    def get_tweet(self, tweet_id):
        """Get a tweet by ID"""
        params = {
            'tweet.fields': 'author_id,created_at,public_metrics'
        }
        return self._api_request('GET', f'/2/tweets/{tweet_id}', params=params)
    
    def post_to_community(self, text, community_id=None, share_with_followers=True):
        """Post to a community"""
        cid = community_id or self.community_id
        data = {
            'text': text,
            'community_id': cid,
            'share_with_followers': share_with_followers
        }
        return self._api_request('POST', '/2/tweets', data=data)
    
    def quote_to_community(self, tweet_url_or_id, commentary, share_with_followers=True, template=None):
        """Quote a tweet with commentary to community"""
        # Extract tweet ID
        tweet_id = extract_tweet_id(tweet_url_or_id)
        if not tweet_id:
            raise Exception(f"Invalid tweet URL or ID: {tweet_url_or_id}")
        
        # Get original tweet info
        tweet_info = self.get_tweet(tweet_id)
        original_text = tweet_info.get('data', {}).get('text', '')
        
        # Build tweet URL
        tweet_url = f"https://x.com/i/status/{tweet_id}"
        
        # Format the post
        if template and template in TEMPLATES:
            post_text = TEMPLATES[template].format(commentary=commentary, url=tweet_url)
        else:
            post_text = f"{commentary}\n\n{tweet_url}"
        
        # Post to community
        result = self.post_to_community(post_text, share_with_followers=share_with_followers)
        
        # Return combined result
        return {
            'data': result.get('data'),
            'quoted_tweet': {
                'id': tweet_id,
                'text': original_text,
                'url': tweet_url
            }
        }
    
    def set_community(self, community_id):
        """Set default community ID"""
        self.community_id = community_id
        self._save_config()
        return {'community_id': community_id}
    
    def get_config(self):
        """Get current configuration"""
        return {
            'community_id': self.community_id,
            'community_url': f'https://x.com/i/communities/{self.community_id}'
        }


def main():
    if len(sys.argv) < 2:
        print("X Community Quote Client")
        print("\nUsage: python x_community_quote.py <command> [args...]")
        print("\nCommands:")
        print("  quote <url|id> <commentary> [--no-share] [--template <name>]")
        print("      Quote a tweet with commentary to community")
        print("  preview <url|id> <commentary> [--template <name>]")
        print("      Preview the post without actually posting")
        print("  set-community <id>")
        print("      Set default community ID")
        print("  config")
        print("      Show current configuration")
        print("  templates")
        print("      List available templates")
        print("\nExamples:")
        print("  quote https://x.com/user/status/123 'Interesting point!'")
        print("  quote https://x.com/user/status/123 'Must read!' --template notable")
        print("  preview https://x.com/user/status/123 'Check this out'")
        sys.exit(1)
    
    client = XCommunityQuoteClient()
    command = sys.argv[1]
    
    try:
        if command == "quote":
            if len(sys.argv) < 4:
                print("Usage: python x_community_quote.py quote <url|id> <commentary> [--no-share] [--template <name>]")
                sys.exit(1)
            tweet_url = sys.argv[2]
            args = sys.argv[3:]
            
            no_share = '--no-share' in args
            template = None
            if '--template' in args:
                t_idx = args.index('--template')
                if t_idx + 1 < len(args):
                    template = args[t_idx + 1]
            
            # Filter out flags from commentary
            filtered_args = []
            skip_next = False
            for i, a in enumerate(args):
                if skip_next:
                    skip_next = False
                    continue
                if a == '--template':
                    skip_next = True
                    continue
                if a == '--no-share':
                    continue
                filtered_args.append(a)
            commentary = ' '.join(filtered_args)
            
            if not commentary:
                print("Error: No commentary provided")
                sys.exit(1)
            
            result = client.quote_to_community(tweet_url, commentary, 
                                               share_with_followers=not no_share, 
                                               template=template)
            print(json.dumps(result, indent=2))
        
        elif command == "preview":
            if len(sys.argv) < 4:
                print("Usage: python x_community_quote.py preview <url|id> <commentary> [--template <name>]")
                sys.exit(1)
            tweet_url = sys.argv[2]
            args = sys.argv[3:]
            
            template = None
            if '--template' in args:
                t_idx = args.index('--template')
                if t_idx + 1 < len(args):
                    template = args[t_idx + 1]
            
            # Filter out flags from commentary
            filtered_args = []
            skip_next = False
            for i, a in enumerate(args):
                if skip_next:
                    skip_next = False
                    continue
                if a == '--template':
                    skip_next = True
                    continue
                filtered_args.append(a)
            commentary = ' '.join(filtered_args)
            
            tweet_id = extract_tweet_id(tweet_url)
            if not tweet_id:
                print(f"Error: Invalid tweet URL or ID: {tweet_url}")
                sys.exit(1)
            
            tweet_info = client.get_tweet(tweet_id)
            tweet_url_full = f"https://x.com/i/status/{tweet_id}"
            
            if template and template in TEMPLATES:
                post_text = TEMPLATES[template].format(commentary=commentary, url=tweet_url_full)
            else:
                post_text = f"{commentary}\n\n{tweet_url_full}"
            
            preview = {
                'preview': True,
                'post_text': post_text,
                'character_count': len(post_text),
                'quoted_tweet': {
                    'id': tweet_id,
                    'text': tweet_info.get('data', {}).get('text', ''),
                    'url': tweet_url_full
                }
            }
            print(json.dumps(preview, indent=2))
        
        elif command == "set-community":
            if len(sys.argv) < 3:
                print("Usage: python x_community_quote.py set-community <community_id>")
                sys.exit(1)
            community_id = sys.argv[2]
            result = client.set_community(community_id)
            print(json.dumps(result, indent=2))
        
        elif command == "config":
            result = client.get_config()
            print(json.dumps(result, indent=2))
        
        elif command == "templates":
            print("Available templates:")
            for name, template in TEMPLATES.items():
                print(f"  {name}: {template}")
        
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
