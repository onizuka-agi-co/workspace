#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv
from requests_oauthlib import OAuth1

API_BASE_URL = "https://api.x.com/2"
AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = f"{API_BASE_URL}/oauth2/token"

DEFAULT_SCOPES = ["tweet.read", "users.read", "bookmark.read", "offline.access"]
DEFAULT_TWEET_FIELDS = [
    "attachments",
    "author_id",
    "conversation_id",
    "created_at",
    "entities",
    "lang",
    "possibly_sensitive",
    "public_metrics",
    "referenced_tweets",
    "source",
]
DEFAULT_EXPANSIONS = [
    "attachments.media_keys",
    "author_id",
    "in_reply_to_user_id",
    "referenced_tweets.id",
    "referenced_tweets.id.author_id",
]
DEFAULT_USER_FIELDS = [
    "created_at",
    "description",
    "id",
    "name",
    "profile_image_url",
    "public_metrics",
    "username",
    "verified",
]
DEFAULT_MEDIA_FIELDS = [
    "alt_text",
    "duration_ms",
    "height",
    "media_key",
    "preview_image_url",
    "public_metrics",
    "type",
    "url",
    "width",
]
DEFAULT_POLL_FIELDS = ["duration_minutes", "end_datetime", "id", "options", "voting_status"]
DEFAULT_PLACE_FIELDS = ["contained_within", "country", "country_code", "full_name", "geo", "id", "name", "place_type"]
IDENTITY_KEYS = {
    "media": "media_key",
    "places": "id",
    "polls": "id",
    "tweets": "id",
    "users": "id",
}

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_ENV_FILE = SCRIPT_DIR / "config.env"
DEFAULT_TOKEN_FILE = SCRIPT_DIR / ".x-user-token.json"
DEFAULT_MONITOR_STATE_FILE = SCRIPT_DIR / ".bookmark-monitor-state.json"
USER_AGENT = "x-bookmarks-fetcher/0.1"


class XApiError(RuntimeError):
    """Raised when the X API returns an error response."""


@dataclass
class Settings:
    client_id: str
    client_secret: str
    redirect_uri: str
    bearer_token: str
    discord_webhook_url: str
    monitor_folder_id: str
    user_access_token: str
    user_refresh_token: str
    api_key: str
    api_key_secret: str
    oauth1_access_token: str
    oauth1_access_token_secret: str

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            client_id=read_env("X_CLIENT_ID"),
            client_secret=read_env("X_CLIENT_SECRET"),
            redirect_uri=read_env("X_BOOKMARKS_REDIRECT_URI"),
            bearer_token=read_env("X_BEARER_TOKEN"),
            discord_webhook_url=read_env("DISCORD_WEBHOOK_URL"),
            monitor_folder_id=read_env("X_BOOKMARKS_MONITOR_FOLDER_ID"),
            user_access_token=read_env("X_USER_ACCESS_TOKEN"),
            user_refresh_token=read_env("X_USER_REFRESH_TOKEN"),
            api_key=read_env("X_API_KEY"),
            api_key_secret=read_env("X_API_KEY_SECRET"),
            oauth1_access_token=read_env("X_OAUTH1_ACCESS_TOKEN", "X_ACCESS_TOKEN"),
            oauth1_access_token_secret=read_env("X_OAUTH1_ACCESS_TOKEN_SECRET", "X_ACCESS_TOKEN_SECRET"),
        )


@dataclass
class AuthContext:
    mode: str
    source: str
    token: dict[str, Any] | None = None
    token_file: Path | None = None
    oauth1: OAuth1 | None = None


def read_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return default


def load_project_env(env_file: Path) -> None:
    if env_file.exists():
        load_dotenv(env_file, override=False)


def now_epoch() -> int:
    return int(time.time())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_token_payload(payload: dict[str, Any], previous: dict[str, Any] | None = None) -> dict[str, Any]:
    token = dict(payload)
    if previous:
        if not token.get("refresh_token") and previous.get("refresh_token"):
            token["refresh_token"] = previous["refresh_token"]
        if not token.get("scope") and previous.get("scope"):
            token["scope"] = previous["scope"]

    obtained_at = now_epoch()
    token["obtained_at"] = obtained_at

    expires_in = token.get("expires_in")
    if expires_in is not None:
        token["expires_at"] = obtained_at + int(expires_in)
    elif previous and previous.get("expires_at"):
        token["expires_at"] = previous["expires_at"]

    return token


def build_basic_auth_header(client_id: str, client_secret: str) -> str:
    credentials = f"{client_id}:{client_secret}".encode("utf-8")
    encoded = base64.b64encode(credentials).decode("ascii")
    return f"Basic {encoded}"


def make_code_verifier() -> str:
    verifier = secrets.token_urlsafe(72)
    if len(verifier) < 43:
        verifier = verifier + ("a" * (43 - len(verifier)))
    return verifier[:128]


def make_code_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def build_authorization_url(client_id: str, redirect_uri: str, scopes: list[str], state: str, code_challenge: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(scopes),
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{AUTHORIZE_URL}?{query}"


def parse_callback_input(raw_value: str) -> tuple[str, str | None]:
    value = raw_value.strip()
    if not value:
        raise ValueError("Empty callback URL.")

    if "://" in value:
        query = parse_qs(urlparse(value).query)
    else:
        query = parse_qs(value.lstrip("?"))

    error_value = query.get("error", [None])[0]
    if error_value:
        description = query.get("error_description", [""])[0]
        raise ValueError(f"Authorization failed: {error_value} {description}".strip())

    code = query.get("code", [None])[0]
    if not code:
        raise ValueError("Authorization code not found in callback URL.")

    state = query.get("state", [None])[0]
    return code, state


def format_response_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        body = response.text.strip()
        return body[:500] if body else f"HTTP {response.status_code}"

    errors = payload.get("errors")
    if isinstance(errors, list) and errors:
        messages = []
        for entry in errors:
            parts = [str(entry.get("title", "")).strip(), str(entry.get("detail", "")).strip()]
            message = " - ".join(part for part in parts if part)
            if message:
                messages.append(message)
        if messages:
            return " | ".join(messages)

    for key in ("error_description", "error", "detail", "title"):
        value = payload.get(key)
        if value:
            return str(value)

    return json.dumps(payload, ensure_ascii=False)[:500]


def request_x(
    auth_context: AuthContext,
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    settings: Settings | None = None,
    retry_on_401: bool = True,
) -> tuple[dict[str, Any], requests.Response]:
    url = path if path.startswith("http") else f"{API_BASE_URL}{path}"
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    auth = None

    if auth_context.mode == "oauth2":
        if not auth_context.token or not auth_context.token.get("access_token"):
            raise XApiError("OAuth 2.0 access token is missing.")
        headers["Authorization"] = f"Bearer {auth_context.token['access_token']}"
    elif auth_context.mode == "oauth1":
        auth = auth_context.oauth1
    else:
        raise XApiError(f"Unsupported auth mode: {auth_context.mode}")

    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            json=json_body,
            headers=headers,
            auth=auth,
            timeout=30,
        )
    except requests.RequestException as exc:
        raise XApiError(f"X API request could not be completed: {exc}") from exc

    if response.status_code == 401 and retry_on_401 and auth_context.mode == "oauth2" and auth_context.token and auth_context.token.get("refresh_token") and settings:
        refreshed = refresh_oauth2_token(settings, auth_context.token)
        auth_context.token = refreshed
        if auth_context.token_file:
            save_json(auth_context.token_file, refreshed)
        return request_x(
            auth_context,
            method,
            path,
            params=params,
            json_body=json_body,
            settings=settings,
            retry_on_401=False,
        )

    if not response.ok:
        raise XApiError(
            f"X API request failed ({response.status_code} {response.reason}): {format_response_error(response)}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise XApiError("X API returned a non-JSON response.") from exc

    return payload, response


def refresh_oauth2_token(settings: Settings, token: dict[str, Any]) -> dict[str, Any]:
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        raise XApiError("Refresh token is not available.")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    if settings.client_secret:
        headers["Authorization"] = build_basic_auth_header(settings.client_id, settings.client_secret)
    else:
        data["client_id"] = settings.client_id

    response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    if not response.ok:
        raise XApiError(
            f"Failed to refresh OAuth 2.0 token ({response.status_code} {response.reason}): {format_response_error(response)}"
        )

    return normalize_token_payload(response.json(), previous=token)


def ensure_oauth2_token_is_fresh(settings: Settings, token: dict[str, Any], token_file: Path | None = None) -> dict[str, Any]:
    expires_at = token.get("expires_at")
    if expires_at is None and token.get("expires_in") and token.get("obtained_at"):
        expires_at = int(token["obtained_at"]) + int(token["expires_in"])
        token["expires_at"] = expires_at

    if expires_at and int(expires_at) <= now_epoch() + 60 and token.get("refresh_token"):
        token = refresh_oauth2_token(settings, token)
        if token_file:
            save_json(token_file, token)

    return token


def exchange_code_for_token(settings: Settings, code: str, verifier: str, redirect_uri: str) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
        "code_verifier": verifier,
    }

    if settings.client_secret:
        headers["Authorization"] = build_basic_auth_header(settings.client_id, settings.client_secret)
    else:
        data["client_id"] = settings.client_id

    response = requests.post(TOKEN_URL, headers=headers, data=data, timeout=30)
    if not response.ok:
        raise XApiError(
            f"Failed to exchange authorization code ({response.status_code} {response.reason}): {format_response_error(response)}"
        )

    return normalize_token_payload(response.json())


def looks_like_oauth1_access_token(token: str) -> bool:
    return bool(token and re.match(r"^\d+-", token))


def build_auth_help(settings: Settings, token_file: Path) -> str:
    lines = ["Unable to find a bookmark-capable authentication setup."]

    if token_file.exists():
        lines.append(f"- Token file exists but could not be used: {token_file}")

    if settings.user_access_token:
        lines.append("- `X_USER_ACCESS_TOKEN` is set, but it was not accepted as a user-context bearer token.")

    if settings.client_id:
        redirect_hint = settings.redirect_uri or "<registered-redirect-uri>"
        lines.append(
            f"- OAuth 2.0 is available. Run `uv run python bookmarks_cli.py login --redirect-uri {redirect_hint}` to mint a bookmark-capable user token."
        )
    else:
        lines.append("- Missing `X_CLIENT_ID`, so the OAuth 2.0 login flow cannot start.")

    if settings.bearer_token:
        lines.append("- `X_BEARER_TOKEN` appears configured, but app-only bearer tokens cannot read private bookmarks.")

    if settings.oauth1_access_token or settings.oauth1_access_token_secret:
        if settings.api_key and settings.api_key_secret:
            lines.append("- OAuth 1.0a credentials look complete. The request failure is likely token- or permission-related.")
        else:
            lines.append(
                "- OAuth 1.0a is incomplete. Add `X_API_KEY` and `X_API_KEY_SECRET` alongside the access token pair if you want direct OAuth 1.0a calls."
            )
            if looks_like_oauth1_access_token(settings.oauth1_access_token):
                lines.append("- The provided access token format matches classic OAuth 1.0a, not an OAuth 2.0 bearer token.")

    return "\n".join(lines)


def choose_auth(settings: Settings, token_file: Path) -> AuthContext:
    token_data = load_json(token_file)
    if token_data and token_data.get("access_token"):
        token_data = ensure_oauth2_token_is_fresh(settings, token_data, token_file=token_file)
        return AuthContext(mode="oauth2", source="token_file", token=token_data, token_file=token_file)

    if settings.user_access_token:
        token_data = normalize_token_payload(
            {
                "access_token": settings.user_access_token,
                "refresh_token": settings.user_refresh_token,
                "scope": " ".join(DEFAULT_SCOPES),
            }
        )
        return AuthContext(mode="oauth2", source="env_user_token", token=token_data)

    if all(
        [
            settings.api_key,
            settings.api_key_secret,
            settings.oauth1_access_token,
            settings.oauth1_access_token_secret,
        ]
    ):
        oauth1 = OAuth1(
            settings.api_key,
            client_secret=settings.api_key_secret,
            resource_owner_key=settings.oauth1_access_token,
            resource_owner_secret=settings.oauth1_access_token_secret,
        )
        return AuthContext(mode="oauth1", source="env_oauth1", oauth1=oauth1)

    raise XApiError(build_auth_help(settings, token_file))


def parse_rate_limit(headers: requests.structures.CaseInsensitiveDict[str]) -> dict[str, Any]:
    reset = headers.get("x-rate-limit-reset")
    reset_at = None
    if reset and reset.isdigit():
        reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc).isoformat()

    return {
        "limit": headers.get("x-rate-limit-limit"),
        "remaining": headers.get("x-rate-limit-remaining"),
        "reset": reset,
        "reset_at": reset_at,
    }


def chunked(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def build_tweet_lookup_params(tweet_ids: list[str]) -> dict[str, Any]:
    return {
        "ids": ",".join(tweet_ids),
        "tweet.fields": ",".join(DEFAULT_TWEET_FIELDS),
        "expansions": ",".join(DEFAULT_EXPANSIONS),
        "user.fields": ",".join(DEFAULT_USER_FIELDS),
        "media.fields": ",".join(DEFAULT_MEDIA_FIELDS),
        "poll.fields": ",".join(DEFAULT_POLL_FIELDS),
        "place.fields": ",".join(DEFAULT_PLACE_FIELDS),
    }


def write_json_result(result: dict[str, Any], args: argparse.Namespace, success_label: str) -> None:
    output_text = json.dumps(result, indent=None if args.compact else 2, ensure_ascii=False)
    if args.output:
        output_path = Path(args.output).expanduser()
        if not output_path.is_absolute():
            output_path = Path.cwd() / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_text + "\n", encoding="utf-8")
        print(f"Saved {success_label} to {output_path}")
        return

    print(output_text)


def truncate_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 1)].rstrip() + "…"


def merge_includes(target: dict[str, list[dict[str, Any]]], page_includes: dict[str, Any] | None) -> None:
    if not page_includes:
        return

    for key, items in page_includes.items():
        if not isinstance(items, list):
            continue

        bucket = target.setdefault(key, [])
        identity_key = IDENTITY_KEYS.get(key)
        existing = set()
        if identity_key:
            existing = {item.get(identity_key) for item in bucket}

        for item in items:
            if not isinstance(item, dict):
                continue
            if identity_key:
                identity = item.get(identity_key)
                if identity in existing:
                    continue
                existing.add(identity)
            bucket.append(item)


def lookup_tweets_by_ids(auth_context: AuthContext, settings: Settings, tweet_ids: list[str]) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if not tweet_ids:
        return [], {}, {}

    hydrated: list[dict[str, Any]] = []
    includes: dict[str, list[dict[str, Any]]] = {}
    last_rate_limit: dict[str, Any] = {}

    for tweet_id_batch in chunked(tweet_ids, 100):
        payload, response = request_x(
            auth_context,
            "GET",
            "/tweets",
            params=build_tweet_lookup_params(tweet_id_batch),
            settings=settings,
        )
        page_items = payload.get("data") or []
        if not isinstance(page_items, list):
            raise XApiError("Tweet lookup response contained an unexpected `data` shape.")

        hydrated.extend(page_items)
        merge_includes(includes, payload.get("includes"))
        last_rate_limit = parse_rate_limit(response.headers)

    by_id = {str(tweet.get("id")): tweet for tweet in hydrated if isinstance(tweet, dict) and tweet.get("id")}
    ordered = [by_id[tweet_id] for tweet_id in tweet_ids if tweet_id in by_id]
    return ordered, includes, last_rate_limit


def build_user_index(includes: dict[str, list[dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return {
        str(user.get("id")): user
        for user in includes.get("users", [])
        if isinstance(user, dict) and user.get("id")
    }


def post_url_for_tweet_id(tweet_id: str) -> str:
    return f"https://x.com/i/web/status/{tweet_id}"


def build_discord_webhook_payload(
    tweet: dict[str, Any],
    includes: dict[str, list[dict[str, Any]]],
    *,
    monitor_label: str,
) -> dict[str, Any]:
    user_index = build_user_index(includes)
    author = user_index.get(str(tweet.get("author_id")), {})
    author_name = author.get("name") or "Unknown author"
    author_username = author.get("username")
    post_url = post_url_for_tweet_id(str(tweet["id"]))
    tweet_text = (tweet.get("text") or "").replace("\r\n", "\n").strip()
    short_text = truncate_text(tweet_text, 3500) or "(no text)"

    embed: dict[str, Any] = {
        "title": truncate_text(f"New X bookmark detected: {tweet.get('id')}", 256),
        "url": post_url,
        "description": short_text,
        "color": 0x1D9BF0,
        "timestamp": tweet.get("created_at"),
        "footer": {"text": f"Bookmark monitor • {monitor_label}"},
        "fields": [
            {"name": "Post", "value": post_url, "inline": False},
        ],
    }

    if author_username:
        embed["author"] = {
            "name": f"{author_name} (@{author_username})",
            "url": f"https://x.com/{author_username}",
        }
    else:
        embed["author"] = {"name": author_name}

    urls = []
    entities = tweet.get("entities")
    if isinstance(entities, dict):
        urls = entities.get("urls") or []
    if urls and isinstance(urls[0], dict):
        expanded_url = urls[0].get("unwound_url") or urls[0].get("expanded_url")
        title = urls[0].get("title") or "Attached link"
        if expanded_url:
            embed["fields"].append(
                {
                    "name": "Link",
                    "value": f"[{truncate_text(title, 100)}]({expanded_url})",
                    "inline": False,
                }
            )
        images = urls[0].get("images") or []
        if images and isinstance(images[0], dict) and images[0].get("url"):
            embed["image"] = {"url": images[0]["url"]}

    return {
        "content": f"🔖 New X bookmark detected in `{monitor_label}`",
        "embeds": [embed],
        "allowed_mentions": {"parse": []},
    }


def send_discord_webhook(webhook_url: str, payload: dict[str, Any]) -> None:
    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
    except requests.RequestException as exc:
        raise XApiError(f"Discord webhook request could not be completed: {exc}") from exc
    if response.status_code >= 400:
        raise XApiError(
            f"Discord webhook request failed ({response.status_code} {response.reason}): {response.text[:500]}"
        )


def get_authenticated_user(auth_context: AuthContext, settings: Settings) -> dict[str, Any]:
    payload, _ = request_x(
        auth_context,
        "GET",
        "/users/me",
        params={
            "user.fields": ",".join(DEFAULT_USER_FIELDS),
        },
        settings=settings,
    )
    user = payload.get("data")
    if not isinstance(user, dict):
        raise XApiError("Authenticated user response did not include `data`.")
    return user


def collect_bookmark_folders(
    auth_context: AuthContext,
    settings: Settings,
    user: dict[str, Any],
    *,
    limit: int | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    remaining = limit
    next_token = None
    page_count = 0
    truncated = False
    folders: list[dict[str, Any]] = []
    last_rate_limit: dict[str, Any] = {}

    while True:
        current_page_size = page_size
        if remaining is not None:
            current_page_size = min(current_page_size, remaining)
            if current_page_size <= 0:
                truncated = True
                break

        params: dict[str, Any] = {"max_results": current_page_size}
        if next_token:
            params["pagination_token"] = next_token

        payload, response = request_x(
            auth_context,
            "GET",
            f"/users/{user['id']}/bookmarks/folders",
            params=params,
            settings=settings,
        )
        page_count += 1

        page_items = payload.get("data") or []
        if not isinstance(page_items, list):
            raise XApiError("Bookmark folders response contained an unexpected `data` shape.")

        folders.extend(page_items)
        last_rate_limit = parse_rate_limit(response.headers)

        if remaining is not None:
            remaining -= len(page_items)
            if remaining <= 0:
                truncated = bool(payload.get("meta", {}).get("next_token"))
                break

        next_token = payload.get("meta", {}).get("next_token")
        if not next_token:
            break

    return {
        "count": len(folders),
        "pages_fetched": page_count,
        "truncated": truncated,
        "folders": folders,
        "rate_limit": last_rate_limit,
    }


def collect_bookmarks(
    auth_context: AuthContext,
    settings: Settings,
    user: dict[str, Any],
    *,
    limit: int | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    remaining = limit
    next_token = None
    page_count = 0
    truncated = False
    bookmarks: list[dict[str, Any]] = []
    includes: dict[str, list[dict[str, Any]]] = {}
    last_rate_limit: dict[str, Any] = {}

    while True:
        current_page_size = page_size
        if remaining is not None:
            current_page_size = min(current_page_size, remaining)
            if current_page_size <= 0:
                truncated = True
                break

        params: dict[str, Any] = {
            "max_results": current_page_size,
            "tweet.fields": ",".join(DEFAULT_TWEET_FIELDS),
            "expansions": ",".join(DEFAULT_EXPANSIONS),
            "user.fields": ",".join(DEFAULT_USER_FIELDS),
            "media.fields": ",".join(DEFAULT_MEDIA_FIELDS),
            "poll.fields": ",".join(DEFAULT_POLL_FIELDS),
            "place.fields": ",".join(DEFAULT_PLACE_FIELDS),
        }
        if next_token:
            params["pagination_token"] = next_token

        payload, response = request_x(
            auth_context,
            "GET",
            f"/users/{user['id']}/bookmarks",
            params=params,
            settings=settings,
        )
        page_count += 1

        page_items = payload.get("data") or []
        if not isinstance(page_items, list):
            raise XApiError("Bookmark response contained an unexpected `data` shape.")

        bookmarks.extend(page_items)
        merge_includes(includes, payload.get("includes"))
        last_rate_limit = parse_rate_limit(response.headers)

        if remaining is not None:
            remaining -= len(page_items)
            if remaining <= 0:
                truncated = bool(payload.get("meta", {}).get("next_token"))
                break

        next_token = payload.get("meta", {}).get("next_token")
        if not next_token:
            break

    return {
        "count": len(bookmarks),
        "pages_fetched": page_count,
        "truncated": truncated,
        "bookmarks": bookmarks,
        "includes": includes,
        "rate_limit": last_rate_limit,
    }


def collect_bookmark_folder_ids(
    auth_context: AuthContext,
    settings: Settings,
    user: dict[str, Any],
    folder_id: str,
    *,
    page_size: int = 100,
) -> dict[str, Any]:
    tweet_ids: list[str] = []
    next_token = None
    page_count = 0
    last_rate_limit: dict[str, Any] = {}

    while True:
        params: dict[str, Any] | None = None
        if next_token:
            params = {"pagination_token": next_token}

        payload, response = request_x(
            auth_context,
            "GET",
            f"/users/{user['id']}/bookmarks/folders/{folder_id}",
            params=params,
            settings=settings,
        )
        page_count += 1

        page_items = payload.get("data") or []
        if not isinstance(page_items, list):
            raise XApiError("Bookmark folder response contained an unexpected `data` shape.")

        for item in page_items:
            if isinstance(item, dict) and item.get("id"):
                tweet_ids.append(str(item["id"]))

        last_rate_limit = parse_rate_limit(response.headers)
        next_token = payload.get("meta", {}).get("next_token")
        if not next_token:
            break

    return {
        "count": len(tweet_ids),
        "pages_fetched": page_count,
        "bookmark_ids": tweet_ids,
        "rate_limit": last_rate_limit,
    }


def load_monitor_state(path: Path) -> dict[str, Any]:
    state = load_json(path)
    if isinstance(state, dict):
        return state
    return {"targets": {}}


def save_monitor_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def monitor_target_key(folder_id: str | None) -> str:
    if folder_id:
        return f"folder:{folder_id}"
    return "all"


def current_bookmark_snapshot(
    auth_context: AuthContext,
    settings: Settings,
    user: dict[str, Any],
    *,
    folder_id: str | None,
    page_size: int,
) -> dict[str, Any]:
    if folder_id:
        folder_result = collect_bookmark_folder_ids(
            auth_context,
            settings,
            user,
            folder_id,
            page_size=page_size,
        )
        bookmarks, includes, tweet_lookup_rate_limit = lookup_tweets_by_ids(
            auth_context,
            settings,
            folder_result["bookmark_ids"],
        )
        folder_result["bookmarks"] = bookmarks
        folder_result["includes"] = includes
        folder_result["tweet_lookup_rate_limit"] = tweet_lookup_rate_limit
        return folder_result

    return collect_bookmarks(
        auth_context,
        settings,
        user,
        page_size=page_size,
    )


def notify_new_bookmarks(
    webhook_url: str,
    *,
    monitor_label: str,
    new_ids: list[str],
    bookmarks: list[dict[str, Any]],
    includes: dict[str, list[dict[str, Any]]],
) -> None:
    bookmark_by_id = {
        str(bookmark.get("id")): bookmark
        for bookmark in bookmarks
        if isinstance(bookmark, dict) and bookmark.get("id")
    }

    for tweet_id in reversed(new_ids):
        bookmark = bookmark_by_id.get(tweet_id)
        if not bookmark:
            continue
        payload = build_discord_webhook_payload(
            bookmark,
            includes,
            monitor_label=monitor_label,
        )
        send_discord_webhook(webhook_url, payload)


def fetch_bookmark_folders(args: argparse.Namespace, settings: Settings, token_file: Path) -> None:
    auth_context = choose_auth(settings, token_file)
    user = get_authenticated_user(auth_context, settings)
    folders_result = collect_bookmark_folders(
        auth_context,
        settings,
        user,
        limit=args.limit,
        page_size=args.page_size,
    )

    result = {
        "fetched_at": now_iso(),
        "auth_mode": auth_context.mode,
        "auth_source": auth_context.source,
        "user": user,
        **folders_result,
    }
    write_json_result(result, args, f"{folders_result['count']} bookmark folders")


def fetch_bookmarks(args: argparse.Namespace, settings: Settings, token_file: Path) -> None:
    auth_context = choose_auth(settings, token_file)
    user = get_authenticated_user(auth_context, settings)
    bookmarks_result = collect_bookmarks(
        auth_context,
        settings,
        user,
        limit=args.limit,
        page_size=args.page_size,
    )

    result = {
        "fetched_at": now_iso(),
        "auth_mode": auth_context.mode,
        "auth_source": auth_context.source,
        "user": user,
        **bookmarks_result,
    }
    write_json_result(result, args, f"{bookmarks_result['count']} bookmarks")


def fetch_bookmark_folder(args: argparse.Namespace, settings: Settings, token_file: Path) -> None:
    auth_context = choose_auth(settings, token_file)
    user = get_authenticated_user(auth_context, settings)
    folder_result = collect_bookmark_folder_ids(
        auth_context,
        settings,
        user,
        args.folder_id,
        page_size=args.page_size,
    )
    bookmarks, includes, tweet_rate_limit = lookup_tweets_by_ids(auth_context, settings, folder_result["bookmark_ids"])
    result = {
        "fetched_at": now_iso(),
        "auth_mode": auth_context.mode,
        "auth_source": auth_context.source,
        "user": user,
        "folder_id": args.folder_id,
        "count": folder_result["count"],
        "pages_fetched": folder_result["pages_fetched"],
        "bookmark_ids": folder_result["bookmark_ids"],
        "bookmarks": bookmarks,
        "includes": includes,
        "rate_limit": {
            "folder_lookup": folder_result["rate_limit"],
            "tweet_lookup": tweet_rate_limit,
        },
    }
    write_json_result(result, args, f"{folder_result['count']} folder bookmarks")


def delete_bookmark(args: argparse.Namespace, settings: Settings, token_file: Path) -> None:
    auth_context = choose_auth(settings, token_file)
    user = get_authenticated_user(auth_context, settings)

    payload, response = request_x(
        auth_context,
        "DELETE",
        f"/users/{user['id']}/bookmarks/{args.tweet_id}",
        settings=settings,
    )
    result = {
        "fetched_at": now_iso(),
        "auth_mode": auth_context.mode,
        "auth_source": auth_context.source,
        "user": user,
        "tweet_id": args.tweet_id,
        "result": payload,
        "rate_limit": parse_rate_limit(response.headers),
    }
    write_json_result(result, args, f"bookmark deletion result for {args.tweet_id}")


def watch_bookmarks(args: argparse.Namespace, settings: Settings, token_file: Path) -> None:
    webhook_url = args.webhook_url or settings.discord_webhook_url
    if not webhook_url:
        raise XApiError(
            "Discord webhook URL is required. Set `DISCORD_WEBHOOK_URL` in config.env or pass `--webhook-url`."
        )

    state_file = Path(args.state_file).expanduser().resolve()
    auth_context = choose_auth(settings, token_file)
    user = get_authenticated_user(auth_context, settings)
    folder_id = args.folder_id or settings.monitor_folder_id or None
    target_key = monitor_target_key(folder_id)
    monitor_label = f"folder:{folder_id}" if folder_id else "all bookmarks"

    def run_once() -> None:
        snapshot = current_bookmark_snapshot(
            auth_context,
            settings,
            user,
            folder_id=folder_id,
            page_size=args.page_size,
        )
        current_ids = [
            str(bookmark_id)
            for bookmark_id in (
                snapshot.get("bookmark_ids")
                or [bookmark.get("id") for bookmark in snapshot.get("bookmarks", []) if isinstance(bookmark, dict)]
            )
            if bookmark_id
        ]
        state = load_monitor_state(state_file)
        targets = state.setdefault("targets", {})
        previous_entry = targets.get(target_key) or {}
        previous_ids = [str(bookmark_id) for bookmark_id in previous_entry.get("ids", []) if bookmark_id]

        if not previous_ids and not args.notify_existing:
            targets[target_key] = {
                "ids": current_ids,
                "count": len(current_ids),
                "updated_at": now_iso(),
            }
            save_monitor_state(state_file, state)
            print(
                f"[{datetime.now().isoformat(timespec='seconds')}] Initialized monitor snapshot for {monitor_label} with {len(current_ids)} bookmarks. No webhook sent."
            )
            return

        previous_id_set = set(previous_ids)
        new_ids = [bookmark_id for bookmark_id in current_ids if bookmark_id not in previous_id_set]

        if new_ids:
            notify_new_bookmarks(
                webhook_url,
                monitor_label=monitor_label,
                new_ids=new_ids,
                bookmarks=snapshot.get("bookmarks", []),
                includes=snapshot.get("includes", {}),
            )
            print(
                f"[{datetime.now().isoformat(timespec='seconds')}] Sent {len(new_ids)} webhook notification(s) for {monitor_label}."
            )
        else:
            print(
                f"[{datetime.now().isoformat(timespec='seconds')}] No new bookmarks detected for {monitor_label}. Current count: {len(current_ids)}."
            )

        targets[target_key] = {
            "ids": current_ids,
            "count": len(current_ids),
            "updated_at": now_iso(),
        }
        save_monitor_state(state_file, state)

    if args.once:
        run_once()
        return

    while True:
        try:
            run_once()
        except XApiError as exc:
            print(
                f"[{datetime.now().isoformat(timespec='seconds')}] Watch iteration failed for {monitor_label}: {exc}",
                file=sys.stderr,
            )
        time.sleep(args.interval)


def login(args: argparse.Namespace, settings: Settings, token_file: Path) -> None:
    if not settings.client_id:
        raise XApiError("`X_CLIENT_ID` is required for OAuth 2.0 login.")

    redirect_uri = args.redirect_uri or settings.redirect_uri
    if not redirect_uri:
        raise XApiError(
            "Redirect URI is required. Pass `--redirect-uri` or set `X_BOOKMARKS_REDIRECT_URI` to the exact callback registered in the X Developer Console."
        )

    scopes = [scope for scope in args.scopes.split() if scope]
    state = secrets.token_urlsafe(24)
    verifier = make_code_verifier()
    challenge = make_code_challenge(verifier)
    auth_url = build_authorization_url(settings.client_id, redirect_uri, scopes, state, challenge)

    print("Open the following URL and authorize the app:\n")
    print(auth_url)
    print()

    if not args.no_browser:
        try:
            webbrowser.open(auth_url, new=1, autoraise=False)
        except Exception:
            pass

    callback_input = input("Paste the full callback URL (or just the query string):\n> ").strip()
    code, returned_state = parse_callback_input(callback_input)
    if returned_state != state:
        raise XApiError("State mismatch detected while completing OAuth 2.0 login.")

    token = exchange_code_for_token(settings, code, verifier, redirect_uri)
    token["scope"] = token.get("scope") or " ".join(scopes)
    save_json(token_file, token)

    print(f"Saved OAuth 2.0 token to {token_file}")
    if token.get("expires_at"):
        expires_at = datetime.fromtimestamp(int(token["expires_at"]), tz=timezone.utc).isoformat()
        print(f"Access token expires at: {expires_at}")
    if token.get("refresh_token"):
        print("Refresh token stored for automatic renewal.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch X bookmarks using OAuth 2.0 or OAuth 1.0a.")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE), help="Path to a config.env file.")
    parser.add_argument("--token-file", default=str(DEFAULT_TOKEN_FILE), help="Path to the OAuth 2.0 token cache file.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser("login", help="Run the OAuth 2.0 PKCE login flow and cache a user token.")
    login_parser.add_argument(
        "--redirect-uri",
        help="Redirect URI registered in the X Developer Console. Defaults to X_BOOKMARKS_REDIRECT_URI.",
    )
    login_parser.add_argument(
        "--scopes",
        default=" ".join(DEFAULT_SCOPES),
        help="Space-separated OAuth 2.0 scopes. Default: tweet.read users.read bookmark.read offline.access",
    )
    login_parser.add_argument("--no-browser", action="store_true", help="Do not try to open the authorization URL in a browser.")
    login_parser.set_defaults(func=login)

    folders_parser = subparsers.add_parser("list-folders", help="List bookmark folders for the authenticated user.")
    folders_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of bookmark folders to return. Omit to fetch all pages.",
    )
    folders_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Folders per request (1-100). Default: 100.",
    )
    folders_parser.add_argument("--output", help="Write JSON output to a file instead of stdout.")
    folders_parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON.")
    folders_parser.set_defaults(func=fetch_bookmark_folders)

    fetch_parser = subparsers.add_parser("fetch", help="Fetch bookmarked posts for the authenticated user.")
    fetch_parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of bookmarks to return. Omit to fetch all pages.",
    )
    fetch_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Bookmarks per request (1-100). Default: 100.",
    )
    fetch_parser.add_argument("--output", help="Write JSON output to a file instead of stdout.")
    fetch_parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON.")
    fetch_parser.set_defaults(func=fetch_bookmarks)

    fetch_folder_parser = subparsers.add_parser("fetch-folder", help="Fetch bookmarked posts from a specific bookmark folder.")
    fetch_folder_parser.add_argument("--folder-id", required=True, help="Bookmark folder ID, for example from x.com/i/bookmarks/<folder_id>.")
    fetch_folder_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Bookmarks per folder request (1-100). Default: 100.",
    )
    fetch_folder_parser.add_argument("--output", help="Write JSON output to a file instead of stdout.")
    fetch_folder_parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON.")
    fetch_folder_parser.set_defaults(func=fetch_bookmark_folder)

    delete_parser = subparsers.add_parser("delete-bookmark", help="Remove a bookmarked post from the authenticated user's bookmarks.")
    delete_parser.add_argument("--tweet-id", required=True, help="Post ID to remove from bookmarks.")
    delete_parser.add_argument("--output", help="Write JSON output to a file instead of stdout.")
    delete_parser.add_argument("--compact", action="store_true", help="Emit compact JSON instead of pretty-printed JSON.")
    delete_parser.set_defaults(func=delete_bookmark)

    watch_parser = subparsers.add_parser("watch", help="Monitor bookmarks and post newly detected items to a Discord webhook.")
    watch_parser.add_argument("--folder-id", help="Monitor only a specific bookmark folder ID. Omit to monitor all bookmarks.")
    watch_parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Polling interval in seconds for continuous mode. Default: 300.",
    )
    watch_parser.add_argument(
        "--page-size",
        type=int,
        default=100,
        help="Bookmarks per X API request (1-100). Default: 100.",
    )
    watch_parser.add_argument(
        "--state-file",
        default=str(DEFAULT_MONITOR_STATE_FILE),
        help="Path to the local bookmark monitor state file.",
    )
    watch_parser.add_argument(
        "--webhook-url",
        help="Discord webhook URL. Defaults to DISCORD_WEBHOOK_URL in config.env.",
    )
    watch_parser.add_argument(
        "--notify-existing",
        action="store_true",
        help="On the first run, notify for already bookmarked items instead of only storing the initial snapshot.",
    )
    watch_parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single poll iteration and exit instead of looping forever.",
    )
    watch_parser.set_defaults(func=watch_bookmarks)

    return parser


def validate_args(args: argparse.Namespace) -> None:
    if getattr(args, "page_size", 100) < 1 or getattr(args, "page_size", 100) > 100:
        raise XApiError("`--page-size` must be between 1 and 100.")
    if args.command in {"fetch", "list-folders"} and args.limit is not None and args.limit < 1:
        raise XApiError("`--limit` must be a positive integer.")
    if getattr(args, "interval", 1) < 1:
        raise XApiError("`--interval` must be a positive integer.")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    env_file = Path(args.env_file).expanduser().resolve()
    token_file = Path(args.token_file).expanduser().resolve()

    load_project_env(env_file)
    settings = Settings.from_env()

    try:
        validate_args(args)
        args.func(args, settings, token_file)
    except (XApiError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
