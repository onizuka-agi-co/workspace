#!/usr/bin/env python3
"""
Clean X OAuth2 Authentication - No code_verifier mismatch
"""

import json
import base64
import hashlib
import secrets
import urllib.parse
import urllib.request
import sys
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "x"
TOKEN_FILE = DATA_DIR / "x-tokens.json"
CLIENT_CREDENTIALS_FILE = DATA_DIR / "x-client-credentials.json"
SESSION_FILE = DATA_DIR / "x-oauth-session.json"

REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "offline.access tweet.write media.write users.read tweet.read bookmark.read"


def load_credentials():
    with open(CLIENT_CREDENTIALS_FILE) as f:
        return json.load(f)


def save_code_verifier(code_verifier, state):
    # 複数のセッションを保存（上書きしない）
    sessions = {}
    if SESSION_FILE.exists():
        with open(SESSION_FILE) as f:
            sessions = json.load(f)
    
    sessions[state] = code_verifier
    
    with open(SESSION_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)


def load_code_verifier(state):
    if SESSION_FILE.exists():
        with open(SESSION_FILE) as f:
            sessions = json.load(f)
            return sessions.get(state)
    return None


def generate_auth_url(client_id):
    """Generate auth URL and save code_verifier with state"""
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    state = secrets.token_urlsafe(16)
    
    # Save code_verifier with state (複数セッション対応)
    save_code_verifier(code_verifier, state)
    
    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE,
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    auth_url = f"https://twitter.com/i/oauth2/authorize?{urllib.parse.urlencode(params)}"
    return auth_url, state


def exchange_code_for_token(code, client_id, client_secret, code_verifier):
    """Exchange authorization code for access token"""
    basic_auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    
    body = urllib.parse.urlencode({
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier
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
        return json.loads(resp.read().decode())


def save_tokens(tokens):
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python x_auth_clean.py url       - Generate auth URL")
        print("  python x_auth_clean.py token <callback_url>  - Exchange code for token")
        sys.exit(1)
    
    command = sys.argv[1]
    creds = load_credentials()
    
    if command == "url":
        auth_url, state = generate_auth_url(creds['client_id'])
        print("=== AUTH URL ===")
        print(auth_url)
        print()
        print(f"State: {state}")
        print()
        print("After authentication, paste the callback URL:")
        print("  python x_auth_clean.py token <callback_url>")
        
    elif command == "token":
        if len(sys.argv) < 3:
            print("Error: Missing callback URL")
            sys.exit(1)
        
        callback_url = sys.argv[2]
        
        # Parse callback URL
        parsed = urllib.parse.urlparse(callback_url)
        params = urllib.parse.parse_qs(parsed.query)
        
        if 'code' not in params:
            print("Error: No code in callback URL")
            sys.exit(1)
        
        code = params['code'][0]
        
        # Get state from callback
        callback_state = params.get('state', [None])[0]
        if not callback_state:
            print("Error: No state in callback URL")
            sys.exit(1)
        
        # Load code_verifier for this specific state
        code_verifier = load_code_verifier(callback_state)
        if not code_verifier:
            print(f"Error: No code_verifier found for state: {callback_state}")
            print("Run 'url' command first and use the generated URL.")
            sys.exit(1)
        
        print(f"Code: {code[:30]}...")
        print(f"Code verifier: {code_verifier[:30]}...")
        print()
        print("Exchanging code for token...")
        
        try:
            tokens = exchange_code_for_token(
                code,
                creds['client_id'],
                creds['client_secret'],
                code_verifier
            )
            
            print("SUCCESS!")
            print(json.dumps(tokens, indent=2))
            
            save_tokens(tokens)
            print(f"\nToken saved to {TOKEN_FILE}")
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"Error: {e.code}")
            print(error_body)
            sys.exit(1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
