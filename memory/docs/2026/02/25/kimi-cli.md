# Kimi CLI 修正

## 背景
Dockerイメージに Kimi Code CLI を追加したが、`abc` ユーザーで `source /lsiopy/bin/activate` 後に `kimi --version` を実行すると `command not found` になる問題が発生。

## 内容

### 原因調査
- `kimi` は `/usr/local/bin/kimi` に存在していた
- ただし実体は `/root/.local/bin/kimi` へのシンボリックリンク
- `abc` ユーザーは `/root` を辿れないため実行不可
- さらに `kimi` のスクリプト shebang が `/root/.local/.../python` を向くため、単純コピーでも `bad interpreter: Permission denied` になった

### 対応
- 現在のコンテナを即時修復:
  - Kimi CLI を `/opt/kimi-home` に再インストール
  - `/usr/local/bin/kimi`, `/usr/local/bin/kimi-cli` を `/opt/kimi-home/.local/bin/*` に向け直し
- 再発防止:
  - `Dockerfile` のKimiインストール先を `/root` から `/opt/kimi-home` に変更
  - `chmod -R a+rX /opt/kimi-home` を追加して非rootユーザーから参照可能にした

## 結果

- `abc` ユーザーで `kimi --version` 成功
- `source /lsiopy/bin/activate` 後でも `kimi --version` 成功
- バージョン確認: `kimi 1.13.0`

## 決定事項
- [x] Kimi CLI は共有可能なパス（`/opt/kimi-home`）にインストールする
- [x] Dockerfile を修正して恒久対応する
