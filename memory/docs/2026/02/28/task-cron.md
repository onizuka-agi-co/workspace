## TASK確認cronの修正

### 問題
- OpenClawのcronジョブが不安定
- TASK確認通知が1時間ごとに重複送信される

### 原因
- OpenClawのcronはメインセッションで動作
- セッションの再起動時にジョブが重複登録される可能性

### 解決策
- s6サービスとして実装し直す
- Dockerコンテナ内で安定動作

### 作成したサービス
**パス:** `/config/s6-services/task-check-webhook/`

**構成:**
- `config.env` - Webhook URL、間隔、パス設定
- `run` - s6サービス実行スクリプト

### 動作確認
```bash
# サービス状態確認
docker exec agi-ws-futodama s6-svstat /run/service/task-check-webhook

# ログ確認
docker exec agi-ws-futodama tail -f /config/.local/state/futodama/task-check-webhook.log

# 再起動
docker compose restart
```

### 結果
- s6サービスとして安定動作
- 1時間ごとにTASK.mdを確認し、未着手タスクを通知
- TASK.mdがGitHub Projectに移行済みの場合は適切に案内
### 関連リンク
- ツイート: https://x.com/onizuka_renjiii/status/2027576221526331582
