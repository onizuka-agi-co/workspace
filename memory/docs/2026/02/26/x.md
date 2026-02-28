# Xコミュニティ投稿スキル開発

## 概要
X（Twitter）のコミュニティ機能への投稿に特化したスキルを開発。

## 作成したスキル

### x-community
コミュニティへの基本投稿機能
- コミュニティID指定で投稿
- share_with_followersオプション

### sunwood-community
Sunwood AI OSS Hub専用の投稿スキル
- コミュニティID固定: 2010195061309587967
- 引用リツイート投稿機能
- テンプレート機能

## 重要なAPI制限

```
community_id + quote_tweet_id の併用 = 403 Forbidden
```

回避策: URLをテキストに含める形式で投稿

## ディレクトリ構造

```
workspace/
├── skills/
│   ├── x-read/
│   ├── x-write/
│   ├── x-community/
│   └── sunwood-community/
├── project/
└── data/x/
    ├── x-tokens.json
    ├── x-client-credentials.json
    └── x-community-config.json
```

## 使い方

```bash
# 引用リツイート投稿
uv run skills/sunwood-community/scripts/quote_to_community.py <URL> "解説文"
```