import json
import os
from datetime import datetime, timezone

OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "latest_package.json")
HISTORY_DIR = os.path.join(OUTPUT_DIR, "history")


def build_content_package(
    topic: str,
    title: str,
    script: str,
    description: str,
    tags: list,
    audio_path: str,
    video_path: str,
) -> dict:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")

    content_package = {
        "generated_at": now.isoformat(),
        "source_topic": topic,
        "title": title,
        "script": script,
        "audio_path": audio_path,
        "video_path": video_path,
        "shorts": ["short1.mp4", "short2.mp4"],
        "youtube_description": description,
        "youtube_tags": tags,
    }

    # latest (overwritten every time)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(content_package, f, ensure_ascii=False, indent=2)

    # history snapshot — one file per generation
    history_file = os.path.join(HISTORY_DIR, f"video_{timestamp}.json")
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(content_package, f, ensure_ascii=False, indent=2)

    return content_package
