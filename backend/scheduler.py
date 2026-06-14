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
from youtube_upload import upload_video, upload_short, generate_description

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
    yt_description = generate_description(title, script, tags)
    package = build_content_package(
        topic=topic,
        title=title,
        script=script,
        description=yt_description,
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

    # 9. رفع على YouTube (إذا كانت credentials موجودة)
    yt_video_id = None
    yt_short_ids = []
    try:
        print("[scheduler] Uploading main video to YouTube...")
        yt_video_id = upload_video(
            video_path=video,
            title=title,
            description=yt_description,
            tags=tags,
            privacy="public",
        )
        package["youtube_url"] = f"https://www.youtube.com/watch?v={yt_video_id}"
        print(f"[scheduler] ✅ Main video uploaded: {package['youtube_url']}")

        # رفع الـ Shorts
        for i, short_path in enumerate(shorts_paths):
            if os.path.exists(short_path):
                short_labels = ["Hook", "Plot Twist", "Climax"]
                label = short_labels[i] if i < len(short_labels) else f"Part {i+1}"
                short_title = f"{title[:70]} — {label}"
                sid = upload_short(
                    video_path=short_path,
                    title=short_title,
                    description=yt_description,
                    tags=tags,
                )
                yt_short_ids.append(sid)
                print(f"[scheduler] ✅ Short {i+1} uploaded: https://youtube.com/shorts/{sid}")

    except ValueError as e:
        print(f"[scheduler] ⚠️ YouTube upload skipped: {e}")
    except Exception as e:
        print(f"[scheduler] ❌ YouTube upload failed: {e}")

    # 10. إشعار Telegram
    yt_link = package.get("youtube_url", "لم يُرفع بعد")
    shorts_count = len(yt_short_ids)
    send_notification(
        f"✅ فيديو اليوم جاهز!\n\n"
        f"📹 {title[:60]}\n\n"
        f"🔗 YouTube: {yt_link}\n"
        f"✂️ Shorts: {shorts_count} مقاطع"
    )

    _latest_package = package
    print("[scheduler] ✅ Daily job completed!")
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