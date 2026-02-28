# 🧪 Nested Sub-Agents 実験結果

## 実験概要
OpenClawのNested Sub-Agents（オーケストレーターパターン）を検証

## 設定変更
```json5
agents.defaults.subagents: {
  maxConcurrent: 8,
  maxSpawnDepth: 2,      // 2段階ネスト許可
  maxChildrenPerAgent: 5,
  model: "zai/glm-4.7"  // Workerはglm-4.7使用
}
```

## 実験1: Webアプリ作成
- **構成**: Main → Orchestrator → Worker 1/2/3
- **結果**: カウンターアプリ作成成功
- **ファイル**: webapp/index.html, style.css, script.js

## 実験2: レビューパターン
- **構成**: Orchestrator → Developer / Designer / Devil's Advocate
- **結果**: 1/3成功（2つはAPIレート制限）
- **重要発見**: HTMLとCSSのクラス名不一致を検出

## 確認できたこと
✅ オーケストレーターパターン正常動作
✅ Workerごとのモデル指定可能
✅ 「悪魔の代弁者」ペルソナで実装検証可能
⚠️ 同時並列実行でAPIレート制限の可能性

## 学び
- Workerはglm-4.7を推奨（レート制限回避）
- 調停者も自ら検証を行う設計が良い
- ペルソナ別Workerで多角的レビューが可能
