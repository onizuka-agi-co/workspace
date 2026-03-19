#!/usr/bin/env python3
"""
ONIZUKA OAuth2 E2E Script (Python版)
PowerShellスクリプトと同等の機能
"""

import base64
import hashlib
import http.server
import socketserver
import urllib.parse
import urllib.request
import json
import secrets
import threading
import webbrowser
import sys

# ====== 設定 ======
CLIENT_ID = "bWZwNUh6WHh6aDl4RGJ1YTlTYU46MTpjaQ"
CLIENT_SECRET = "WiaC8QwisZXwBarR3E6ymI54aFb_bcDC1ndAKnwXjv2ijoyTgj"
PORT = 8080
PATH = "callback"
REDIRECT_URI = f"http://localhost:{PORT}/{PATH}"
SCOPE = "tweet.read users.read tweet.write offline.access media.write"
STATE = "xyz789"

# ====== PKCE生成 ======
# 48バイトのランダム
bytes_rand = secrets.token_bytes(48)
# verifier（URL-safe、=と+と/を削除）
verifier = base64.b64encode(bytes_rand).decode('ascii').rstrip('=').replace('+', '').replace('/', '')
# 長さ調整
if len(verifier) > 128:
    verifier = verifier[:128]
if len(verifier) < 43:
    verifier = verifier + 'A' * (43 - len(verifier))

# challenge = base64url(sha256(verifier))
challenge_bytes = hashlib.sha256(verifier.encode('ascii')).digest()
challenge = base64.b64encode(challenge_bytes).decode('ascii').rstrip('=').replace('+', '-').replace('/', '_')

print(f"VERIFIER: {verifier}")
print(f"CHALLENGE: {challenge}")
print(f"VERIFIER length: {len(verifier)}")

# ====== 認可URL生成 ======
auth_url = (
    f"https://x.com/i/oauth2/authorize?"
    f"response_type=code&"
    f"client_id={urllib.parse.quote(CLIENT_ID)}&"
    f"redirect_uri={urllib.parse.quote(REDIRECT_URI)}&"
    f"scope={urllib.parse.quote(SCOPE)}&"
    f"state={urllib.parse.quote(STATE)}&"
    f"code_challenge={urllib.parse.quote(challenge)}&"
    f"code_challenge_method=S256"
)
print(f"\n=== AUTH URL ===\n{auth_url}\n")

# ====== localhostでcodeを受信 ======
code_received = threading.Event()
received_code = None

class CodeHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        global received_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'code' in params:
            received_code = params['code'][0]
            print(f"\n=== CODE RECEIVED ===\n{received_code}\n")
            
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"OK. You can close this tab.")
            code_received.set()
        else:
            self.send_response(400)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

with socketserver.TCPServer(("", PORT), CodeHandler) as httpd:
    print(f"Listening on http://localhost:{PORT}/{PATH}...")
    
    # ブラウザで認可URLを開く
    webbrowser.open(auth_url)
    
    # codeを待つ
    httpd.handle_request()

if not received_code:
    print("ERROR: No code received")
    sys.exit(1)

# ====== token交換 ======
print("\n=== TOKEN EXCHANGE ===")
basic_auth = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
body = urllib.parse.urlencode({
    'grant_type': 'authorization_code',
    'code': received_code,
    'redirect_uri': REDIRECT_URI,
    'code_verifier': verifier
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

try:
    with urllib.request.urlopen(req) as resp:
        token_data = json.loads(resp.read().decode())
        print(json.dumps(token_data, indent=2))
        
        # トークンを保存
        with open('x-tokens.json', 'w') as f:
            json.dump(token_data, f, indent=2)
        print("\nTokens saved to x-tokens.json")
        
        ACCESS_TOKEN = token_data.get('access_token')
        
except urllib.error.HTTPError as e:
    print(f"ERROR: {e.code}")
    print(e.read().decode())
    sys.exit(1)

# ====== /2/users/me ======
print("\n=== /2/users/me ===")
req2 = urllib.request.Request(
    "https://api.x.com/2/users/me",
    headers={'Authorization': f'Bearer {ACCESS_TOKEN}'}
)
try:
    with urllib.request.urlopen(req2) as resp:
        me = json.loads(resp.read().decode())
        print(json.dumps(me, indent=2))
except urllib.error.HTTPError as e:
    print(f"ERROR: {e.code}")
    print(e.read().decode())

# ====== 投稿テスト ======
print("\n=== POST TEST /2/tweets ===")
tweet_data = json.dumps({"text": "ONIZUKAテスト：Pythonから投稿（OAuth2）"}).encode()
req3 = urllib.request.Request(
    "https://api.x.com/2/tweets",
    data=tweet_data,
    headers={
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    },
    method='POST'
)
try:
    with urllib.request.urlopen(req3) as resp:
        result = json.loads(resp.read().decode())
        print(json.dumps(result, indent=2))
        print("\n✅ SUCCESS!")
except urllib.error.HTTPError as e:
    print(f"ERROR: {e.code}")
    print(e.read().decode())

print("\n=== DONE ===")
