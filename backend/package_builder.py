import json
from datetime import datetime, timezone


def build_content_package(
    topic: str,
    title: str,
    script: str,
    description: str,
    tags: list,
    audio_path: str,
    video_path: str,
) -> dict:
    content_package = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_topic": topic,
        "title": title,
        "script": script,
        "audio_file": audio_path,
        "video_file": video_path,
        "shorts": [
            {"label": "Short 1", "file": "short1.mp4"},
            {"label": "Short 2", "file": "short2.mp4"},
        ],
        "youtube_description": description,
        "youtube_tags": tags,
    }

    with open("content_package.json", "w", encoding="utf-8") as f:
        json.dump(content_package, f, ensure_ascii=False, indent=2)

    return content_package
