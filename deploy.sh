#!/bin/bash
echo "=========================================" >> /root/deploy.log
echo "Deployment started at $(date)" >> /root/deploy.log

cd /root/trend-pilot
git pull origin main

pkill -f "scheduler.py"
sleep 2

cd /root/trend-pilot/backend
source ../venv/bin/activate
nohup python3 scheduler.py > /root/scheduler.log 2>&1 &

# تشغيل خدمة الجدولة إذا لم تكن تعمل
if ! pgrep -f "publishing_scheduler.py" > /dev/null; then
    cd /root/trend-pilot/backend
    source ../venv/bin/activate
    nohup python publishing_scheduler.py > /root/publisher.log 2>&1 &
    echo "Publishing scheduler started" >> /root/deploy.log
fi

echo "Deployment finished at $(date)" >> /root/deploy.log
echo "=========================================" >> /root/deploy.log
