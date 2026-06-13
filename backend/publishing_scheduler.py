import os
import time
import schedule
from datetime import datetime
from notify import send_notification, send_approval_request, send_content_package_notification

# -------------------------------------------------------
# Paths
# -------------------------------------------------------
BASE = "/root/trend-pilot/backend" if os.path.exists("/root/trend-pilot") else os.path.dirname(__file__)
LONG_VIDEO_PATH = os.path.join(BASE, "video.mp4")
SHORTS_DIR      = os.path.join(BASE, "output", "shorts")
PUBLISHED_LOG   = os.path.join(BASE, "published_log.txt")
STORY_TITLE_FILE = os.path.join(BASE, "current_story_title.txt")

# -------------------------------------------------------
# Publishing schedule
# -------------------------------------------------------

# Long video — morning slot per weekday
WEEKDAY_LONG_VIDEO = {
    0: "09:00",   # Monday
    1: "09:00",   # Tuesday
    2: "07:00",   # Wednesday
    3: "17:00",   # Thursday
    4: "12:00",   # Friday
    5: "12:00",   # Saturday
    6: "10:00",   # Sunday
}

# 3 Shorts — noon / afternoon / evening per weekday
WEEKDAY_SHORTS = {
    0: ["12:00", "17:00", "20:00"],
    1: ["12:00", "17:00", "20:00"],
    2: ["12:00", "17:00", "20:00"],
    3: ["13:00", "17:00", "20:00"],
    4: ["12:00", "16:00", "19:00"],
    5: ["11:00", "15:00", "20:00"],
    6: ["12:00", "16:00", "19:00"],
}

DEFAULT_LONG_TIME  = "10:00"
DEFAULT_SHORT_TIMES = ["12:00", "16:00", "19:00"]


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------

def get_today_long_time() -> str:
    return WEEKDAY_LONG_VIDEO.get(datetime.now().weekday(), DEFAULT_LONG_TIME)


def get_today_shorts_times() -> list[str]:
    return WEEKDAY_SHORTS.get(datetime.now().weekday(), DEFAULT_SHORT_TIMES)


def get_story_title() -> str:
    """Reads the current story title from disk (written by the main pipeline)."""
    if os.path.exists(STORY_TITLE_FILE):
        with open(STORY_TITLE_FILE, "r") as f:
            return f.read().strip()
    return "Untitled True Crime Story"


def get_shorts_list() -> list[str]:
    """Returns sorted list of Short video paths in the shorts directory."""
    if not os.path.exists(SHORTS_DIR):
        return []
    return sorted([
        os.path.join(SHORTS_DIR, f)
        for f in os.listdir(SHORTS_DIR)
        if f.endswith(".mp4")
    ])


def is_already_published(key: str) -> bool:
    if not os.path.exists(PUBLISHED_LOG):
        return False
    with open(PUBLISHED_LOG, "r") as f:
        return key in f.read()


def mark_as_published(key: str):
    with open(PUBLISHED_LOG, "a") as f:
        f.write(f"{key}|{datetime.now().isoformat()}\n")


# -------------------------------------------------------
# Publish actions
# -------------------------------------------------------

def publish_long_video():
    """Morning slot — request approval for the long video, then notify."""
    video_name = os.path.basename(LONG_VIDEO_PATH)
    if is_already_published(f"long_{video_name}"):
        print(f"[publisher] Long video already published: {video_name}")
        return

    story_title = get_story_title()
    scheduled_time = get_today_long_time()

    # Rich content-package notification first
    shorts = get_shorts_list()
    send_content_package_notification(story_title, LONG_VIDEO_PATH, shorts)

    # Then inline approval request
    send_approval_request("Long Video", video_name, f"Morning — {scheduled_time}")
    mark_as_published(f"long_{video_name}")
    print(f"[publisher] ✅ Long video approval request sent: {video_name}")


def publish_short(short_path: str, slot_label: str):
    """Publish one Short at a specific time slot."""
    short_name = os.path.basename(short_path)
    if is_already_published(f"short_{short_name}"):
        print(f"[publisher] Short already published: {short_name}")
        return

    story_title = get_story_title()
    send_approval_request("Short", short_name, slot_label)
    mark_as_published(f"short_{short_name}")
    print(f"[publisher] ✅ Short approval request sent: {short_name} @ {slot_label}")


def publish_shorts_slot(slot_index: int, slot_label: str):
    """
    Publish one Short per time slot.
    slot_index 0=noon, 1=afternoon, 2=evening
    """
    shorts = get_shorts_list()
    if slot_index < len(shorts):
        publish_short(shorts[slot_index], slot_label)
    else:
        print(f"[publisher] No short available for slot {slot_index} ({slot_label})")


# -------------------------------------------------------
# Scheduler setup
# -------------------------------------------------------

def schedule_publishing():
    long_time = get_today_long_time()
    short_times = get_today_shorts_times()

    # Long video — morning
    schedule.every().day.at(long_time).do(publish_long_video)
    print(f"[publisher] Long video scheduled at {long_time}")

    # 3 Shorts — noon / afternoon / evening
    slot_labels = ["Noon", "Afternoon", "Evening"]
    for i, (t, label) in enumerate(zip(short_times, slot_labels)):
        schedule.every().day.at(t).do(publish_shorts_slot, slot_index=i, slot_label=f"{label} — {t}")
        print(f"[publisher] Short {i+1} ({label}) scheduled at {t}")


def run_scheduler():
    print("[publisher] Starting True Crime publishing scheduler…")
    schedule_publishing()
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    run_scheduler()
