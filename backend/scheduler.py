from apscheduler.schedulers.background import BackgroundScheduler
from viral_engine import get_viral_story
from hook_ai import detect_story_type
from script import generate_script, generate_full_content
from voice import text_to_speech
from video import create_video
from package_builder import build_content_package
from notify import send_notification

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

    # 4. توليد السكريبت (مع تمرير القصة ونوعها)
    script = generate_script(topic, story_type)
    print(f"[scheduler] Script generated: {len(script)} characters")

    # 5. تحويل النص إلى صوت (MP3)
    audio = text_to_speech(script)
    print(f"[scheduler] Audio generated: {audio}")

    # 6. إنشاء الفيديو (مع تمرير نوع القصة للـ video.py)
    video = create_video(audio, script, story_type=story_type)
    print(f"[scheduler] Video generated: {video}")

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

    _latest_package = package
    print("[scheduler] Daily job completed successfully!")

    # 8. إرسال إشعار (يمكن تفعيل Telegram لاحقاً)
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