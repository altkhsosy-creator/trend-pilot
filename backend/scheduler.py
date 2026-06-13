import os
import shutil
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from viral_engine import get_viral_story
from hook_ai import detect_story_type
from script import generate_script, generate_full_content
from voice import text_to_speech
from video import create_video
from package_builder import build_content_package
from notify import send_notification
from short_generator import extract_shorts

VIDEOS_DIR = os.path.join(os.path.dirname(__file__), "output", "videos")

_latest_package: dict = {}


def job():
    """
    الوظيفة الرئيسية التي تعمل كل 24 ساعة
    تجلب قصة فيروسية وتنتج فيديو كامل
    """
    global _latest_package

    print("[scheduler] Starting daily job...")

    # 1. جلب أفضل قصة فيروسية من Reddit
    story = get_viral_story()
    topic = story["title"]
    print(f"[scheduler] Selected story: {topic[:80]}...")

    # 2. تحديد نوع القصة (لتحسين الـ hooks والتصميم)
    story_type = detect_story_type(topic)
    print(f"[scheduler] Story type: {story_type}")

    # 3. توليد المحتوى الكامل (عنوان، وصف، تاغات)
    content = generate_full_content(topic)
    title = content.get("title", topic)
    description = content.get("description", "")
    tags = content.get("tags", [])
    print(f"[scheduler] Generated title: {title[:60]}...")

    # 4. توليد السكريبت
    script = generate_script()
    print(f"[scheduler] Script generated: {len(script)} characters")

    # 5. تحويل النص إلى صوت (MP3)
    audio = text_to_speech(script)
    print(f"[scheduler] Audio generated: {audio}")

    # 6. إنشاء الفيديو (مع تمرير نوع القصة للـ video.py)
    video = create_video(audio, script, story_type=story_type)
    print(f"[scheduler] Video generated: {video}")
    send_notification(f"🎬 فيديو اليوم جاهز!\n\nالعنوان: {title}\n📹 رابط المعاينة: http://46.101.250.86:5001")

    # استخراج Shorts من الفيديو الطويل
    shorts_paths = extract_shorts(video, num_shorts=3, duration=60)
    print(f"[scheduler] Extracted {len(shorts_paths)} shorts")

    # 7. تجميع كل شيء في حزمة محتوى واحدة
    package = build_content_package(
        topic=topic,
        title=title,
        script=script,
        description=description,
        tags=tags,
        audio_path=audio,
        video_path=video,
    )

    # 8. حفظ نسخة أرشيفية من الفيديو بـ timestamp
    os.makedirs(VIDEOS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archived_video = os.path.join(VIDEOS_DIR, f"video_{timestamp}.mp4")
    if os.path.exists(video):
        shutil.copy2(video, archived_video)
        print(f"[scheduler] Archived video → {archived_video}")
    package["archived_video"] = f"video_{timestamp}.mp4"

    # نسخ Shorts إلى مجلد النشر
    shorts_dir = "/root/trend-pilot/backend/output/shorts"
    os.makedirs(shorts_dir, exist_ok=True)

    # هذا افتراض أن لديك قائمة shorts_paths
    # إذا لم تكن موجودة، سنضيفها لاحقاً
    if 'shorts_paths' in dir() and shorts_paths:
        for i, short_path in enumerate(shorts_paths):
            if os.path.exists(short_path):
                short_dest = os.path.join(shorts_dir, f"short_{i+1}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4")
                shutil.copy(short_path, short_dest)
                print(f"[scheduler] Copied short to: {short_dest}")

    _latest_package = package
    print("[scheduler] Daily job completed successfully!")

    # 9. إرسال إشعار (يمكن تفعيل Telegram لاحقاً)
    send_notification(f"✅ Daily Content Package Ready!\n📹 {title[:50]}...")

    return package


def get_latest_package() -> dict:
    """
    يعيد آخر حزمة محتوى تم إنتاجها
    يمكن استخدامها بواسطة الـ API لعرضها في الـ frontend
    """
    return _latest_package


def start_scheduler():
    """
    يبدأ جدولة المهام - تعمل كل 24 ساعة
    """
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", hours=24)
    scheduler.start()
    print("[scheduler] ========================================")
    print("[scheduler] 🚀 Scheduler started successfully!")
    print("[scheduler] 📅 Will run every 24 hours")
    print("[scheduler] ⏱️ Next job: in 24 hours")
    print("[scheduler] ========================================")


# للاختبار اليدوي - شغل الملف مباشرة
if __name__ == "__main__":
    print("[scheduler] Running manual test...")
    result = job()
    print(f"\n✅ Test completed! Package ready with video: {result.get('video_path', 'N/A')}")