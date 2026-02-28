# 背景画像設定

トップページのヒーローセクションに薄く背景画像を表示。

## 設定

```css
.VPHero::before {
  content: '';
  position: absolute;
  background-image: url('/memory/hero-bg.jpg');
  background-size: cover;
  background-position: center;
  opacity: 0.20;  /* ライトモード */
}

.dark .VPHero::before {
  opacity: 0.12;  /* ダークモード */
}
```

## 調整履歴

| 不透明度 | 結果 |
|---------|------|
| 8% | 薄すぎる |
| 15% | まだ薄い |
| 20% | **採用** - 見やすい |

## ファイル

- 画像: `docs/public/hero-bg.jpg`
- CSS: `docs/.vitepress/theme/custom.css`

[← 戻る](./)
