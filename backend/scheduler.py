from apscheduler.schedulers.background import BackgroundScheduler
from trends import get_trends, select_top_trend
from script import generate_script
from voice import text_to_speech
from video import create_video
from notify import send_notification

def job():
    trends = get_trends()
    top = select_top_trend(trends)

    script = generate_script(top["title"])
    audio = text_to_speech(script)
    video = create_video(audio)

    send_notification("Video is ready!")

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, "interval", hours=24)
    scheduler.start()
