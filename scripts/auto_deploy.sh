#!/bin/bash
# Auto-Deploy Script — يسحب التحديثات من GitHub تلقائياً ويعيد التشغيل إذا وُجد تغيير

REPO_DIR="/root/trend-pilot"
LOG_FILE="/var/log/trendpilot_deploy.log"
LOCK_FILE="/tmp/trendpilot_deploy.lock"

# منع التشغيل المتوازي
if [ -f "$LOCK_FILE" ]; then
    exit 0
fi
touch "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

cd "$REPO_DIR" || exit 1

# ── تحديث .env من .env.sync.b64 (مشفّر base64) ──
ENV_SYNC_B64="$REPO_DIR/backend/.env.sync.b64"
ENV_FILE="$REPO_DIR/backend/.env"
if [ -f "$ENV_SYNC_B64" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 تحديث .env من .env.sync.b64..." >> "$LOG_FILE"
    DECODED=$(base64 -d "$ENV_SYNC_B64" 2>/dev/null)
    while IFS= read -r line; do
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        KEY="${line%%=*}"
        if grep -q "^${KEY}=" "$ENV_FILE" 2>/dev/null; then
            sed -i "s|^${KEY}=.*|${line}|" "$ENV_FILE"
        else
            echo "$line" >> "$ENV_FILE"
        fi
    done <<< "$DECODED"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ .env محدَّث بنجاح" >> "$LOG_FILE"
fi

# ── فحص TRIGGER_NOW أولاً (بغض النظر عن حالة الكود) ──
TRIGGER_FILE="$REPO_DIR/TRIGGER_NOW"
if [ -f "$TRIGGER_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎬 TRIGGER_NOW — تشغيل الـ job فوراً..." >> "$LOG_FILE"
    rm -f "$TRIGGER_FILE"
    RESP=$(curl -s -X POST http://localhost:8000/run 2>&1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Job triggered: $RESP" >> "$LOG_FILE"
fi

# جلب آخر commits من GitHub بدون تطبيق
git fetch origin main --quiet 2>/dev/null

LOCAL=$(git rev-parse HEAD 2>/dev/null)
REMOTE=$(git rev-parse origin/main 2>/dev/null)

if [ "$LOCAL" = "$REMOTE" ]; then
    exit 0
fi

# يوجد تحديث جديد
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 تحديث جديد: $LOCAL → $REMOTE" >> "$LOG_FILE"

git pull origin main --quiet >> "$LOG_FILE" 2>&1

# تحديث .env مرة أخرى بعد pull (حتى لو تغيّر .env.sync.b64)
if [ -f "$ENV_SYNC_B64" ]; then
    DECODED=$(base64 -d "$ENV_SYNC_B64" 2>/dev/null)
    while IFS= read -r line; do
        [[ "$line" =~ ^#.*$ || -z "$line" ]] && continue
        KEY="${line%%=*}"
        if grep -q "^${KEY}=" "$ENV_FILE" 2>/dev/null; then
            sed -i "s|^${KEY}=.*|${line}|" "$ENV_FILE"
        else
            echo "$line" >> "$ENV_FILE"
        fi
    done <<< "$DECODED"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Pull ناجح — إعادة التشغيل..." >> "$LOG_FILE"

tmux kill-session -t trendpilot 2>/dev/null
sleep 2
bash /root/start_trendpilot.sh >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 السيرفر أُعيد تشغيله بنجاح" >> "$LOG_FILE"

# إذا وُجد ملف TRIGGER_NOW بعد الـ pull — شغّل الـ job
if [ -f "$TRIGGER_FILE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🎬 TRIGGER_NOW مكتشف — انتظار بدء السيرفر (25 ثانية)..." >> "$LOG_FILE"
    sleep 25
    RESP=$(curl -s -X POST http://localhost:8000/run 2>&1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Job triggered: $RESP" >> "$LOG_FILE"
    rm -f "$TRIGGER_FILE"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🗑️ TRIGGER_NOW حُذف" >> "$LOG_FILE"
fi
