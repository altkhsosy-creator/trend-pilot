"""
scheduler.py — الجدولة اليومية: تركيب الفيديو من المحتوى الجاهز (weekly_planner)
ونشره على يوتيوب، مع توزيع الشورتات على أيام منفصلة.

الجدولة الفعلية (cron) تُضبط خارج هذا الملف عبر systemd/apscheduler.
هذا الملف يوفّر job() تُستدعى مرة يومياً.
"""

import os
import json
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler

from voice import text_to_speech
from video import create_video
from thumbnail import create_thumbnail
from short_generator import generate_independent_shorts
from youtube_upload import upload_video, upload_short, set_thumbnail

BASE = os.path.dirname(os.path.abspath(__file__))
WEEKLY_DIR = os.path.join(BASE, "weekly_content")

PUBLISH_DAYS = [d.strip().lower() for d in os.getenv("PUBLISH_DAYS", "monday,thursday,saturday").split(",")]

# الأيام اللي فيها نشر شورت "متأخر" فقط (بدون فيديو طويل جديد)، وأي يوم/index مصدره
# index: 0=Hook, 1=Plot Twist, 2=Climax
SHORT_ONLY_DAYS = {
    "tuesday":  ("monday", 1),
    "friday":   ("thursday", 2),
    "sunday":   ("saturday", 1),
}

_WEEKDAY_NAMES = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def _find_latest_week_dir() -> str | None:
    if not os.path.isdir(WEEKLY_DIR):
        return None
    weeks = sorted(
        [d for d in os.listdir(WEEKLY_DIR) if d.startswith("week_") and os.path.isdir(os.path.join(WEEKLY_DIR, d))],
        reverse=True,
    )
    return os.path.join(WEEKLY_DIR, weeks[0]) if weeks else None


def _find_day_dir(week_dir: str, day_name: str) -> str | None:
    matches = [d for d in os.listdir(week_dir) if day_name in d.lower()]
    return os.path.join(week_dir, matches[0]) if matches else None


def _load_day_content(day_dir: str) -> dict:
    def _read(name):
        path = os.path.join(day_dir, name)
        return open(path, encoding="utf-8").read().strip() if os.path.exists(path) else ""

    script_raw = _read("script.txt")
    lines = script_raw.split("\n\n", 1)
    title = lines[0].strip() if lines else ""
    script = lines[1].strip() if len(lines) > 1 else script_raw

    description = _read("description.txt")
    keywords_raw = _read("keywords.txt")
    tags = [k.strip() for k in keywords_raw.split("\n") if k.strip()]

    outline_path = os.path.join(day_dir, "outline.json")
    outline = {}
    if os.path.exists(outline_path):
        try:
            outline = json.load(open(outline_path, encoding="utf-8"))
        except Exception:
            outline = {}
    return {"title": title, "script": script, "description": description, "tags": tags, "outline": outline}


def _load_published(day_dir: str) -> dict:
    path = os.path.join(day_dir, "published.json")
    if os.path.exists(path):
        try:
            return json.load(open(path, encoding="utf-8"))
        except Exception:
            pass
    return {"long": False, "short_0": False, "short_1": False, "short_2": False}


def _save_published(day_dir: str, status: dict):
    with open(os.path.join(day_dir, "published.json"), "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)


def _produce_long_video_and_shorts(day_dir: str, content: dict, status: dict):
    """ينتج الفيديو الطويل + الثلاث شورتات، يرفع الطويل + شورت الـHook فقط، ويحفظ الباقي لأيام لاحقة."""
    title = content["title"]
    script = content["script"]
    description = content["description"]
    tags = content["tags"]
    outline = content.get("outline", {})

    print(f"[scheduler] Title: {title}")
    print(f"[scheduler] Script: {len(script.split())} words")

    audio = text_to_speech(script)
    print(f"[scheduler] Audio: {audio}")

    video_path = create_video(audio, script, output=os.path.join(day_dir, "video.mp4"), title=title, footage_dir=os.path.join(day_dir, "footage"))
    print(f"[scheduler] Video: {video_path}")

    thumbnail_path = None
    try:
        hook_line = script.split("\n")[0][:80].strip()
        thumbnail_path = create_thumbnail(title, subtitle=hook_line)
        print(f"[scheduler] Thumbnail: {thumbnail_path}")
    except Exception as e:
        print(f"[scheduler] ⚠️ Thumbnail failed: {e}")

    shorts_dir = os.path.join(day_dir, "shorts")
    os.makedirs(shorts_dir, exist_ok=True)
    shorts_paths = generate_independent_shorts(
        title=title, outline=outline,
        footage_dir=os.path.join(day_dir, "footage"),
        shorts_dir=shorts_dir, num_shorts=3,
    )
    print(f"[scheduler] {len(shorts_paths)} shorts generated and saved to {shorts_dir}")

    if not status["long"]:
        try:
            yt_id = upload_video(video_path=video_path, title=title, description=description,
                                  tags=tags, privacy="private")
            print(f"[scheduler] ✅ Long video: https://www.youtube.com/watch?v={yt_id}")
            if thumbnail_path:
                set_thumbnail(yt_id, thumbnail_path)
            status["long"] = True
        except Exception as e:
            print(f"[scheduler] ❌ Long video upload failed: {e}")

    _publish_short(day_dir, shorts_dir, 0, title, description, tags, status)

    _save_published(day_dir, status)


def _publish_short(source_day_dir: str, shorts_dir: str, index: int, title: str,
                    description: str, tags: list, status: dict):
    key = f"short_{index}"
    if status.get(key):
        print(f"[scheduler] Short {index} already published — skipping")
        return

    short_path = os.path.join(shorts_dir, f"short_{index}.mp4")
    if not os.path.exists(short_path):
        print(f"[scheduler] ❌ Short {index} file not found at {short_path}")
        return

    angle_labels = ["Hook", "Plot Twist", "Climax"]
    label = angle_labels[index] if index < len(angle_labels) else f"Part {index+1}"
    short_title = f"{title[:80]} — {label}"

    try:
        sid = upload_short(video_path=short_path, title=short_title, description=description, tags=tags)
        print(f"[scheduler] ✅ Short {index} ({label}): https://youtube.com/shorts/{sid}")
        status[key] = True
        _save_published(source_day_dir, status)
    except Exception as e:
        print(f"[scheduler] ❌ Short {index} upload failed: {e}")


def job():
    today = datetime.utcnow()
    day_name = _WEEKDAY_NAMES[today.weekday()]
    print(f"[scheduler] ===== Daily job started: {today.strftime('%Y-%m-%d %H:%M')} ({day_name}) =====")

    week_dir = _find_latest_week_dir()
    if not week_dir:
        print("[scheduler] ❌ No weekly content found — run weekly_planner.py first")
        return

    if day_name in PUBLISH_DAYS:
        day_dir = _find_day_dir(week_dir, day_name)
        if not day_dir:
            print(f"[scheduler] ❌ No content for {day_name}")
            return
        content = _load_day_content(day_dir)
        status = _load_published(day_dir)
        _produce_long_video_and_shorts(day_dir, content, status)

    elif day_name in SHORT_ONLY_DAYS:
        source_day_name, short_index = SHORT_ONLY_DAYS[day_name]
        source_day_dir = _find_day_dir(week_dir, source_day_name)
        if not source_day_dir:
            print(f"[scheduler] ❌ No source content for {source_day_name} (needed for {day_name}'s short)")
            return
        content = _load_day_content(source_day_dir)
        status = _load_published(source_day_dir)
        shorts_dir = os.path.join(source_day_dir, "shorts")
        _publish_short(source_day_dir, shorts_dir, short_index, content["title"],
                        content["description"], content["tags"], status)

    else:
        print(f"[scheduler] {day_name}: no publishing action scheduled")

    print(f"[scheduler] ===== Daily job completed: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} =====")


def run_weekly_planner():
    from weekly_planner import plan_week
    plan_week()


if __name__ == "__main__":
    import sys
    if "--plan-week" in sys.argv:
        run_weekly_planner()
    elif "--run-job" in sys.argv:
        job()
    else:
        scheduler = BlockingScheduler(timezone="UTC")
        publish_days_str = ",".join(PUBLISH_DAYS)
        short_only_days_str = ",".join(SHORT_ONLY_DAYS.keys())
        all_days = f"{publish_days_str},{short_only_days_str}"
        scheduler.add_job(job, "cron", day_of_week=all_days, hour=18, minute=0)
        scheduler.add_job(run_weekly_planner, "cron", day_of_week="sun", hour=6, minute=0)
        print(f"[scheduler] Started — publish days: {publish_days_str} | short-only days: {short_only_days_str} | all at 18:00 UTC")
        print("[scheduler] Weekly planner: Sunday 06:00 UTC")
        scheduler.start()
