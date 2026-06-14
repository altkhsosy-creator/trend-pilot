#!/bin/bash
# =============================================================
# TrendPilot — DigitalOcean Server Setup Script
# شغّله مرة واحدة فقط بعد cloning المشروع
# الاستخدام: bash deploy_setup.sh
# =============================================================

set -e
echo ""
echo "======================================================="
echo "  TrendPilot — Server Setup Starting..."
echo "======================================================="

# ── 1. تحديث النظام وتثبيت الأدوات ──────────────────────────
echo ""
echo "[1/6] Installing system dependencies..."
apt-get update -qq
apt-get install -y -qq \
    python3 python3-pip python3-venv \
    ffmpeg \
    tmux \
    git \
    curl \
    fonts-dejavu-core \
    2>/dev/null

echo "  ✅ System packages installed"

# ── 2. إعداد مجلد المشروع ────────────────────────────────────
echo ""
echo "[2/6] Setting up project directory..."
cd /root/trend-pilot/backend
mkdir -p output/videos output/shorts output/thumbnails output/history assets/fonts

# تحميل خط BebasNeue
if [ ! -f "assets/fonts/BebasNeue.ttf" ]; then
    echo "  Downloading BebasNeue font..."
    python3 -c "
import requests
r = requests.get('https://github.com/google/fonts/raw/main/ofl/bebasneue/BebasNeue-Regular.ttf', timeout=15)
open('assets/fonts/BebasNeue.ttf', 'wb').write(r.content)
print('  ✅ BebasNeue.ttf downloaded')
" 2>/dev/null || echo "  ⚠️  Font download failed — using fallback"
fi

echo "  ✅ Directories ready"

# ── 3. تثبيت Python packages ─────────────────────────────────
echo ""
echo "[3/6] Installing Python packages..."
pip3 install -q \
    openai \
    gTTS \
    requests \
    Pillow \
    python-dotenv \
    apscheduler \
    schedule \
    google-api-python-client \
    google-auth-oauthlib \
    google-auth-httplib2 \
    python-telegram-bot \
    fastapi \
    uvicorn \
    numpy

echo "  ✅ Python packages installed"

# ── 4. إعداد متغيرات البيئة ──────────────────────────────────
echo ""
echo "[4/6] Setting up environment variables..."

ENV_FILE="/root/trend-pilot/backend/.env"

if [ ! -f "$ENV_FILE" ]; then
cat > "$ENV_FILE" << 'ENVEOF'
# ── TrendPilot Environment Variables ──
# عدّل هذه القيم بمفاتيحك الحقيقية

OPENAI_API_KEY=YOUR_OPENAI_API_KEY
PEXELS_API_KEY=YOUR_PEXELS_API_KEY
NEWS_API_KEY=YOUR_NEWS_API_KEY
GEMINI_API_KEY=YOUR_GEMINI_API_KEY

# Telegram
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=YOUR_TELEGRAM_CHAT_ID

# YouTube
YOUTUBE_CLIENT_ID=YOUR_YOUTUBE_CLIENT_ID
YOUTUBE_CLIENT_SECRET=YOUR_YOUTUBE_CLIENT_SECRET
YOUTUBE_REFRESH_TOKEN=YOUR_YOUTUBE_REFRESH_TOKEN

# GitHub
GITHUB_TOKEN=YOUR_GITHUB_TOKEN

# Mode
MOCK_MODE=false
ENVEOF
    echo "  ⚠️  Created .env file — edit it with your API keys:"
    echo "      nano /root/trend-pilot/backend/.env"
else
    echo "  ✅ .env file already exists"
fi

# ── 5. إنشاء systemd services للتشغيل التلقائي ────────────────
echo ""
echo "[5/6] Creating systemd services..."

# Service 1: مولّد الفيديو اليومي
cat > /etc/systemd/system/trendpilot-generator.service << 'EOF'
[Unit]
Description=TrendPilot Video Generator (Daily)
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/trend-pilot/backend
EnvironmentFile=/root/trend-pilot/backend/.env
ExecStart=/usr/bin/python3 scheduler.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Service 2: جدولة النشر والإشعارات
cat > /etc/systemd/system/trendpilot-publisher.service << 'EOF'
[Unit]
Description=TrendPilot Publishing Scheduler
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/trend-pilot/backend
EnvironmentFile=/root/trend-pilot/backend/.env
ExecStart=/usr/bin/python3 publishing_scheduler.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable trendpilot-generator trendpilot-publisher
echo "  ✅ systemd services created and enabled"

# ── 6. ملف tmux كبديل سهل ───────────────────────────────────
echo ""
echo "[6/6] Creating tmux start script..."

cat > /root/start_trendpilot.sh << 'EOF'
#!/bin/bash
# تشغيل TrendPilot داخل tmux
cd /root/trend-pilot/backend

# تحميل متغيرات البيئة
set -a
source .env
set +a

# بدء session جديد
tmux new-session -d -s trendpilot -x 220 -y 50

# نافذة 1: مولّد الفيديو
tmux rename-window -t trendpilot:0 'generator'
tmux send-keys -t trendpilot:generator "python3 scheduler.py" Enter

# نافذة 2: جدولة النشر
tmux new-window -t trendpilot -n 'publisher'
tmux send-keys -t trendpilot:publisher "python3 publishing_scheduler.py" Enter

# نافذة 3: API server
tmux new-window -t trendpilot -n 'api'
tmux send-keys -t trendpilot:api "uvicorn main:app --host 0.0.0.0 --port 8000" Enter

echo ""
echo "✅ TrendPilot started in tmux!"
echo ""
echo "Commands:"
echo "  tmux attach -t trendpilot        # دخول tmux"
echo "  tmux kill-session -t trendpilot  # إيقاف كل شيء"
echo "  Ctrl+B then D                    # خروج من tmux بدون إيقاف"
echo ""
EOF

chmod +x /root/start_trendpilot.sh
echo "  ✅ tmux script ready: /root/start_trendpilot.sh"

# ── النهاية ───────────────────────────────────────────────────
echo ""
echo "======================================================="
echo "  ✅ Setup Complete!"
echo "======================================================="
echo ""
echo "NEXT STEPS:"
echo ""
echo "  1. Edit your API keys:"
echo "     nano /root/trend-pilot/backend/.env"
echo ""
echo "  2a. Start with tmux (RECOMMENDED for testing):"
echo "      bash /root/start_trendpilot.sh"
echo ""
echo "  2b. OR start with systemd (for permanent 24/7):"
echo "      systemctl start trendpilot-generator"
echo "      systemctl start trendpilot-publisher"
echo ""
echo "  3. Check logs:"
echo "      journalctl -u trendpilot-generator -f"
echo "      journalctl -u trendpilot-publisher -f"
echo ""
echo "======================================================="
