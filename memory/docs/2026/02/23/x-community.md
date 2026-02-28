# X コミュニティ投稿スキル

## 作成したスキル

```
skills/
├── x-community/       # コミュニティ投稿専用
│   ├── SKILL.md
│   └── scripts/x_community.py
└── x-community-quote/ # 引用解説コミュニティ投稿
    ├── SKILL.md
    └── scripts/x_community_quote.py
```

## X API v2 コミュニティ投稿の仕様

**エンドポイント:** `POST /2/tweets`

**パラメータ:**
```json
{
  "text": "投稿テキスト",
  "community_id": "2010195061309587967",
  "share_with_followers": true
}
```

## 重要な制限

- `community_id` と `quote_tweet_id` の併用は **403 Forbidden**
- 引用リツイートしたい場合は URL をテキストに含める形で対応

## デフォルト設定

- `share_with_followers: true` - フォロワーにも表示（デフォルト）
- `--no-share` オプションでコミュニティのみに変更可能

## x-community コマンド

```bash
# コミュニティへ投稿（フォロワーにも表示）
uv run skills/x-community/scripts/x_community.py post "投稿テキスト"

# コミュニティのみ
uv run skills/x-community/scripts/x_community.py post "投稿テキスト" --no-share

# 設定確認
uv run skills/x-community/scripts/x_community.py config
```

## x-community-quote コマンド

```bash
# 引用解説投稿
uv run skills/x-community-quote/scripts/x_community_quote.py quote <URL> "解説"

# テンプレート使用
uv run skills/x-community-quote/scripts/x_community_quote.py quote <URL> "解説" --template notable

# プレビュー（投稿せず確認）
uv run skills/x-community-quote/scripts/x_community_quote.py preview <URL> "解説"
```

### テンプレート

| 名前 | フォーマット |
|------|-------------|
| `notable` | 🔍 注目ポスト解説 |
| `news` | 📰 ニュース紹介 |
| `tip` | 💡 Tips・豆知識 |

## 設定ファイル

`x-community-config.json` - デフォルトコミュニティID等:
```json
{
  "community_id": "2010195061309587967"
}
```

## tweet.fields でコミュニティ情報取得

```python
params = {
    'tweet.fields': 'community_id,created_at,public_metrics,author_id'
}
```

コミュニティに投稿されたツイートかどうかは `community_id` フィールドで判定可能。

[← 戻る](./)
