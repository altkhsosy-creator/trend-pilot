import json
import os
from datetime import datetime, timezone

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "latest_package.json")


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

    content_package = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_topic": topic,
        "title": title,
        "script": script,
        "audio_path": audio_path,
        "video_path": video_path,
        "shorts": ["short1.mp4", "short2.mp4"],
        "youtube_description": description,
        "youtube_tags": tags,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(content_package, f, ensure_ascii=False, indent=2)

    with open("content_package.json", "w", encoding="utf-8") as f:
        json.dump(content_package, f, ensure_ascii=False, indent=2)

    return content_package
