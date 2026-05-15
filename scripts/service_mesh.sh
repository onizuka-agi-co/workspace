#!/usr/bin/env bash
set -euo pipefail

# ONIZUKA Service Mesh — 全s6サービス統合監視スクリプト
# Issue: https://github.com/onizuka-agi-co/secretary-bot/issues/230

SERVICE_DIR="/config/s6-services"
LOG_DIR="/config/.local/state/futodama"
REPORT_DIR="/config/.openclaw/workspace/data/service-mesh"
DISCORD_WEBHOOK_FILE="/config/.openclaw/workspace/data/x/x-discord-webhook.json"

mkdir -p "$REPORT_DIR" "$LOG_DIR"

# --- ヘルスチェック ---
check_services() {
  local up=0 down=0 not_running=0 crashed=0 total=0
  local services=""

  for svc_path in "$SERVICE_DIR"/*/; do
    local name
    name=$(basename "$svc_path")
    [ -f "$svc_path/run" ] || continue
    total=$((total + 1))

    local stat
    stat=$(s6-svstat "/run/service/$name" 2>/dev/null || echo "unknown")

    local status_icon="❓"
    local status_text="unknown"

    if echo "$stat" | grep -q "^up"; then
      status_icon="✅"
      status_text="up"
      up=$((up + 1))
    elif echo "$stat" | grep -q "exitcode"; then
      status_icon="🔴"
      status_text="crashed"
      crashed=$((crashed + 1))
    elif echo "$stat" | grep -q "not running"; then
      status_icon="⏸️"
      status_text="not_running"
      not_running=$((not_running + 1))
    elif echo "$stat" | grep -q "not started"; then
      status_icon="⏸️"
      status_text="not_started"
      not_running=$((not_running + 1))
    else
      down=$((down + 1))
    fi

    services+="$status_icon $name ($status_text)\n"
  done

  # レポート生成
  local ts
  ts=$(date -u +%Y-%m-%dT%H:%M:%SZ)

  cat > "$REPORT_DIR/latest.json" <<EOF
{
  "timestamp": "$ts",
  "total": $total,
  "up": $up,
  "crashed": $crashed,
  "not_running": $not_running,
  "down": $down,
  "health_pct": $(awk "BEGIN {printf \"%.1f\", $up * 100 / $total}")
}
EOF

  # Markdownレポート
  cat > "$REPORT_DIR/latest.md" <<EOF
# 🔧 ONIZUKA Service Mesh Health Report

**Generated:** $ts
**Health:** $up/$total services running ($(awk "BEGIN {printf \"%.0f\", $up * 100 / $total}")%)

## Status Summary
- ✅ Running: $up
- 🔴 Crashed: $crashed
- ⏸️ Not running: $not_running
- ❓ Other: $down

## Services
$(echo -e "$services")
EOF

  echo "$ts | $up/$total up | $crashed crashed | $not_running not_running"
  return 0
}

# --- 自動修復（クラッシュしたサービスの再起動）---
auto_heal() {
  local healed=0

  for svc_path in "$SERVICE_DIR"/*/; do
    local name
    name=$(basename "$svc_path")
    [ -f "$svc_path/run" ] || continue

    local stat
    stat=$(s6-svstat "/run/service/$name" 2>/dev/null || echo "unknown")

    if echo "$stat" | grep -q "exitcode"; then
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Restarting crashed service: $name"
      s6-svc -r "/run/service/$name" 2>/dev/null || true
      healed=$((healed + 1))
      echo "$name: restart attempted" >> "$LOG_DIR/service-mesh.log"
    fi
  done

  echo "Auto-healed: $healed services"
}

# --- Discord通知 ---
notify_discord() {
  local report_file="$REPORT_DIR/latest.json"
  [ -f "$report_file" ] || return 0

  local total up crashed not_running
  total=$(jq -r '.total' "$report_file")
  up=$(jq -r '.up' "$report_file")
  crashed=$(jq -r '.crashed' "$report_file")
  not_running=$(jq -r '.not_running' "$report_file")
  health=$(jq -r '.health_pct' "$report_file")
  ts=$(jq -r '.timestamp' "$report_file")

  local color="65280"  # green
  [ "$crashed" -gt 0 ] && color="16711680"  # red
  [ "$not_running" -gt 3 ] && color="16776960"  # yellow

  # Build service list
  local svc_list=""
  for svc_path in "$SERVICE_DIR"/*/; do
    local name
    name=$(basename "$svc_path")
    [ -f "$svc_path/run" ] || continue
    local stat
    stat=$(s6-svstat "/run/service/$name" 2>/dev/null || echo "unknown")
    if echo "$stat" | grep -q "^up"; then
      svc_list+="✅ $name\n"
    elif echo "$stat" | grep -q "exitcode"; then
      svc_list+="🔴 $name\n"
    else
      svc_list+="⏸️ $name\n"
    fi
  done

  local payload
  payload=$(cat <<EOJSON
{
  "embeds": [{
    "title": "🔧 Service Mesh Health Report",
    "color": $color,
    "fields": [
      {"name": "Health", "value": "$up/$total ($health%)", "inline": true},
      {"name": "Crashed", "value": "$crashed", "inline": true},
      {"name": "Stopped", "value": "$not_running", "inline": true},
      {"name": "Services", "value": "$(echo -e "$svc_list" | head -20 | tr '\n' ' ')"}
    ],
    "footer": {"text": "ONIZUKA Service Mesh"},
    "timestamp": "$ts"
  }],
  "allowed_mentions": {"parse": []}
}
EOJSON
)

  # Use webhook if available
  if [ -f "$DISCORD_WEBHOOK_FILE" ]; then
    local webhook_url
    webhook_url=$(jq -r '.webhook_url // .url // empty' "$DISCORD_WEBHOOK_FILE" 2>/dev/null || true)
    if [ -n "$webhook_url" ]; then
      curl -s -X POST "$webhook_url" \
        -H "Content-Type: application/json" \
        -H "User-Agent: ONIZUKA-ServiceMesh/1.0" \
        -d "$payload" > /dev/null 2>&1 || true
    fi
  fi
}

# --- メイン実行 ---
COMMAND="${1:-check}"

case "$COMMAND" in
  check)
    check_services
    ;;
  heal)
    auto_heal
    ;;
  report)
    check_services
    notify_discord
    ;;
  status)
    # 個別サービスステータス
    for svc_path in "$SERVICE_DIR"/*/; do
      name=$(basename "$svc_path")
      [ -f "$svc_path/run" ] || continue
      stat=$(s6-svstat "/run/service/$name" 2>/dev/null || echo "unknown")
      echo "$name: $stat"
    done
    ;;
  json)
    check_services > /dev/null
    cat "$REPORT_DIR/latest.json"
    ;;
  *)
    echo "Usage: $0 {check|heal|report|status|json}"
    echo "  check   - Health check all services"
    echo "  heal    - Auto-restart crashed services"
    echo "  report  - Health check + Discord notification"
    echo "  status  - Show individual service status"
    echo "  json    - Output health report as JSON"
    exit 1
    ;;
esac
