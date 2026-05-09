#!/usr/bin/env bash
set -euo pipefail

SERVICE_DIR="/config/s6-services/agi-glossary"
mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DIR/config.env" <<'EOF'
GLOSSARY_SCRIPT='/config/.openclaw/workspace/project/agi-glossary/generate.py'
DISCORD_WEBHOOK_URL=''
DISCORD_CHANNEL_ID=''
X_POST_ENABLED='false'
SCHEDULE_HOUR='9'
SCHEDULE_MINUTE='0'
EOF
chmod 600 "$SERVICE_DIR/config.env"

cat > "$SERVICE_DIR/run" <<'RUNEOF'
#!/usr/bin/env bash
set -euo pipefail

SERVICE_DIR="/config/s6-services/agi-glossary"
ENV_FILE="$SERVICE_DIR/config.env"

if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a
fi

: "${GLOSSARY_SCRIPT:?Glossary script path required}"
: "${SCHEDULE_HOUR:=9}"
: "${SCHEDULE_MINUTE:=0}"

LOG="/config/.local/state/futodama/agi-glossary.log"
mkdir -p "$(dirname "$LOG")"
touch "$LOG"
exec >>"$LOG" 2>&1

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] agi-glossary service start"

while true; do
  NOW=$(date +%H:%M)
  TARGET=$(printf "%02d:%02d" "$SCHEDULE_HOUR" "$SCHEDULE_MINUTE")
  
  if [ "$NOW" = "$TARGET" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Generating glossary..."
    
    RESULT=$(uv run "$GLOSSARY_SCRIPT" generate 2>&1) || {
      echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Error: $RESULT"
      sleep 120
      continue
    }
    
    IDX=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['index'])")
    
    # Mark as posted
    uv run "$GLOSSARY_SCRIPT" mark-posted "$IDX"
    
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Posted term #$IDX"
    
    # Wait 2 min to avoid re-trigger
    sleep 120
  fi
  
  sleep 30
done
RUNEOF
chmod +x "$SERVICE_DIR/run"

echo "Created agi-glossary s6 service at $SERVICE_DIR"
RUNEOF
chmod +x "$SERVICE_DIR/../setup-agi-glossary.sh" 2>/dev/null || true

echo "Setup script created"
