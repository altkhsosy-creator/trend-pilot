import os
import time
import schedule
from datetime import datetime
from notify import send_notification

# مسارات الملفات
LONG_VIDEO_PATH = "/root/trend-pilot/backend/video.mp4"
SHORTS_DIR = "/root/trend-pilot/backend/output/shorts"
PUBLISHED_LOG = "/root/trend-pilot/backend/published_log.txt"

# أوقات النشر اليومية الأساسية
LONG_VIDEO_TIME = "10:00"
SHORTS_TIMES = ["12:00", "16:00", "19:00"]

# أوقات النشر حسب اليوم
WEEKDAY_LONG_VIDEO = {
    0: "09:00",   # الإثنين
    1: "09:00",   # الثلاثاء
    2: "07:00",   # الأربعاء
    3: "17:00",   # الخميس
    4: "12:00",   # الجمعة
    5: "12:00",   # السبت
    6: "10:00"    # الأحد
}

WEEKDAY_SHORTS = {
    0: ["12:00", "17:00", "20:00"],
    1: ["12:00", "17:00", "20:00"],
    2: ["12:00", "17:00", "20:00"],
    3: ["13:00", "17:00", "20:00"],
    4: ["12:00", "16:00", "19:00"],
    5: ["11:00", "15:00", "20:00"],
    6: ["12:00", "16:00", "19:00"]
}

def get_today_long_time():
    from datetime import datetime
    today = datetime.now().weekday()
    return WEEKDAY_LONG_VIDEO.get(today, LONG_VIDEO_TIME)

def get_today_shorts_times():
    from datetime import datetime
    today = datetime.now().weekday()
    return WEEKDAY_SHORTS.get(today, SHORTS_TIMES)

def is_already_published(video_name):
    if not os.path.exists(PUBLISHED_LOG):
        return False
    with open(PUBLISHED_LOG, 'r') as f:
        return video_name in f.read()

def mark_as_published(video_name):
    with open(PUBLISHED_LOG, 'a') as f:
        f.write(f"{video_name}|{datetime.now()}\n")

def request_approval(video_type, video_path, scheduled_time):
    video_name = os.path.basename(video_path)
    message = f"📺 طلب موافقة على النشر\n\nالنوع: {video_type}\nالملف: {video_name}\nالموعد المحدد: {scheduled_time}\n\n✅ /approve_{video_type.replace(' ', '_')}_{video_name}\n❌ /reject_{video_type.replace(' ', '_')}_{video_name}"
    send_notification(message)
    return video_name

def publish_long_video():
    video_name = os.path.basename(LONG_VIDEO_PATH)
    if is_already_published(f"long_{video_name}"):
        print(f"[publisher] Long video {video_name} already published")
        return
    request_approval("Long Video", LONG_VIDEO_PATH, get_today_long_time())
    mark_as_published(f"long_{video_name}")
    send_notification(f"✅ تم تأكيد نشر الفيديو الطويل: {video_name}")

def publish_shorts():
    if not os.path.exists(SHORTS_DIR):
        return
    shorts_files = [f for f in os.listdir(SHORTS_DIR) if f.endswith('.mp4')]
    for short_file in shorts_files:
        short_path = os.path.join(SHORTS_DIR, short_file)
        if is_already_published(f"short_{short_file}"):
            continue
        request_approval("Short Video", short_path, "مساءً")

def schedule_publishing():
    import schedule
    schedule.every().day.at(get_today_long_time()).do(publish_long_video)
    for short_time in get_today_shorts_times():
        schedule.every().day.at(short_time).do(publish_shorts)

def run_scheduler():
    import schedule
    print("[publisher] Starting publishing scheduler...")
    schedule_publishing()
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler()
