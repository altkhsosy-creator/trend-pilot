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

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Pull ناجح — إعادة التشغيل..." >> "$LOG_FILE"

tmux kill-session -t trendpilot 2>/dev/null
sleep 2
bash /root/start_trendpilot.sh >> "$LOG_FILE" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 السيرفر أُعيد تشغيله بنجاح" >> "$LOG_FILE"
