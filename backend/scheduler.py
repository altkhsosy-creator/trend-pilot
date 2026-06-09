from apscheduler.schedulers.background import BackgroundScheduler
from viral_engine import get_viral_story
from script import generate_full_content
from voice import text_to_speech
from video import create_video
from package_builder import build_content_package
from notify import send_notification

_latest_package: dict = {}


def job():
    global _latest_package

    story = get_viral_story()
    topic = story["title"]

    content = generate_full_content(topic)
    title = content.get("title", topic)
    script = content.get("script", "")
    description = content.get("description", "")
    tags = content.get("tags", [])

    audio = text_to_speech(script)
    video = create_video(audio, script)

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
    send_notification("Daily Content Package Ready!")
    return package


def get_latest_package() -> dict:
    return _latest_package


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", hours=24)
    scheduler.start()
