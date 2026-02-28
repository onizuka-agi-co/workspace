# ONIZUKA Character Reference

## Assets

| File | Style | Description |
|------|-------|-------------|
| `onizuka-realistic.jpg` | Semi-realistic | Dramatic, detailed digital painting style |
| `onizuka-chibi.jpg` | Chibi/Cute | Simplified, playful cartoon style |

## Character Details

### Core Features
- **種族**: 鬼（Oni demon）
- **髪**: 長い黒髪、高い位置で結わえ（赤い紐）
- **角**: 小さな湾曲した二本角（頭頂部）
- **目**: 赤みがかった鋭い眼差し
- **牙**: 小さな牙（口元に見える）
- **耳飾り**: 赤いタッセルのイヤリング

### 服装
- **色**: 赤＋金＋黒
- **様式**: 伝統的な和風装束
- **装飾**: 金の円形飾り（胸元）、タッセル、渦巻き模様

### 雰囲気
- **リアル版**: 劇的、神秘的、力強い
- **ちび版**: 愛らしい、茶目っ気、親しみやすい

---

## Prompt Templates

### リアル版（Dramatic Style）

```
A semi-realistic anime-style illustration of an oni demon character:
long flowing black hair tied in a high bun with a red cord,
small curved red horns on the head,
sharp red-tinted eyes with intense gaze,
small fang visible at the mouth,
wearing a traditional Japanese red and gold robe with intricate patterns,
gold circular ornaments with tassels on the chest,
red tassel earrings,
dramatic lighting with warm ember-like background,
digital painting aesthetic with smooth gradients,
rich saturated colors (deep black, fiery reds, warm gold accents)
```

### ちび版（Chibi Style）

```
A cute chibi-style cartoon illustration of an oni demon character:
compact rounded head with big expressive red eyes,
short spiky black hair tied in a high bun with a red band,
small pointed red horns,
tiny fang, mischievous expression,
simplified red and gold traditional robe with gold swirling patterns,
gold ornaments with tassels on the chest,
red tassel earrings,
bold outlines, flat colors, minimal shading,
playful and approachable vibe,
solid simple background
```

### 汎用（General）

```
An oni demon with red horns and long black hair tied in a high bun,
wearing a traditional red and gold Japanese robe,
gold ornaments and tassels,
red eyes, small fang,
[追加のシーン/ポーズ/背景をここに記述]
```

---

## 使用例

### 基本生成
```bash
uv run scripts/generate.py \
  --prompt "An oni demon with red horns, long black hair in a high bun, wearing a red and gold traditional Japanese robe, dramatic lighting" \
  --aspect-ratio 3:4 \
  --resolution 1K
```

### 背景付き
```bash
uv run scripts/generate.py \
  --prompt "An oni demon with red horns and red eyes, wearing a red and gold robe, standing under a full moon with cherry blossoms falling, mystical Japanese temple in background" \
  --aspect-ratio 16:9 \
  --resolution 2K
```

### ちび版
```bash
uv run scripts/generate.py \
  --prompt "A cute chibi oni demon character with small red horns, big red eyes, wearing a red and gold kimono, playful pose, simple background" \
  --aspect-ratio 1:1 \
  --resolution 1K
```

---

## 注意点

- nanobanana2は**テキストから画像生成のみ**対応（画像入力非対応）
- 一貫性を保つため、上記プロンプトテンプレートをベースに使用
- キャラクターの一貫性は100%保証されないが、主要な特徴は維持される
