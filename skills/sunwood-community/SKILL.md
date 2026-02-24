---
name: sunwood-community
description: "Sunwood AI OSS Hub (https://x.com/i/communities/2010195061309587967) への投稿専用スキル。引用リツイート投稿や解説付き投稿に使用。"
---

# Sunwood Community - Sunwood AI OSS Hub 投稿スキル

Sunwood AI OSS Hub コミュニティへの投稿専用。

**コミュニティ:** https://x.com/i/communities/2010195061309587967

## Quick Start

```bash
# 引用リツイート（解説付き）
uv run skills/sunwood-community/scripts/quote_to_community.py <ポストURL> "解説文"

# 例
uv run skills/sunwood-community/scripts/quote_to_community.py https://x.com/user/status/123 "これは面白い記事です！"
```

## ログ保存

投稿するたびに自動でログを保存します。

**保存場所:** `skills/sunwood-community/logs/YYYY-MM-DD/`

**ファイル名:** `HH-MM-SS_<元ツイートID>.json`

**ログ内容:**
```json
{
  "timestamp": "2026-02-24T04:30:00+00:00",
  "original_tweet": {
    "id": "123456789",
    "text": "元のツイート本文",
    "url": "https://x.com/i/status/123456789"
  },
  "community_post": {
    "id": "987654321",
    "text": "投稿したテキスト",
    "url": "https://x.com/i/status/987654321"
  }
}
```

## スクリプト一覧

### quote_to_community.py - 引用リツイート投稿

```bash
uv run skills/sunwood-community/scripts/quote_to_community.py <ポストURL> "解説文"
```

シンプル版。引数2つだけ：
1. ポストURL（またはツイートID）
2. 解説文

### x_community.py - 汎用コミュニティ投稿

```bash
# 通常投稿
uv run skills/sunwood-community/scripts/x_community.py post "投稿テキスト"

# 引用リツイート
uv run skills/sunwood-community/scripts/x_community.py quote <URL> "解説"
```

### x_community_quote.py - テンプレート付き引用投稿

```bash
# テンプレート使用
uv run skills/sunwood-community/scripts/x_community_quote.py quote <URL> "解説" --template notable

# プレビュー
uv run skills/sunwood-community/scripts/x_community_quote.py preview <URL> "解説"
```

**テンプレート:**
| 名前 | フォーマット |
|------|-------------|
| `notable` | 🔍 注目ポスト解説 |
| `news` | 📰 ニュース紹介 |
| `tip` | 💡 Tips・豆知識 |

## 設定

コミュニティID固定: `2010195061309587967` (Sunwood AI OSS Hub)

## 必要なファイル

- `x-tokens.json` - アクセストークン（workspace直下）
- `x-client-credentials.json` - クライアント認証情報

## 注意点

- `community_id` + `quote_tweet_id` の併用は403エラー（API制限）
- URLをテキストに含める形式で投稿（引用カードとして表示）
