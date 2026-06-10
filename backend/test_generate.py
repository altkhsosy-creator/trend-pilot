"""
test_generate.py — توليد عدة فيديوهات تجريبية
يولّد 3 فيديوهات بمواضيع مختلفة ويحفظها في backend/test_output/
"""

import os, sys, time

os.makedirs("test_output", exist_ok=True)

TOPICS = [
    {
        "title": "The scientist who discovered a black hole in his backyard",
        "script": (
            "Nobody believed him at first. He was just an amateur astronomer with a cheap telescope. "
            "But what he discovered one night shocked the entire scientific community. "
            "A gravitational anomaly, invisible to the naked eye, was pulling objects in his yard. "
            "The government arrived within 48 hours. They never revealed what they found. "
            "His neighbors reported strange lights for weeks afterward. "
            "To this day, the official explanation remains classified."
        ),
    },
    {
        "title": "The abandoned town that nobody is allowed to visit",
        "script": (
            "Deep in the mountains, there is a town that was evacuated overnight in 1987. "
            "The residents left everything behind — food on the tables, cars in the driveways. "
            "Researchers who tried to enter reported feeling an impossible dread. "
            "Two journalists went in and came back speaking a language nobody recognized. "
            "Satellite images show movement in the streets — but the town is officially empty. "
            "The government has blocked every attempt to investigate further."
        ),
    },
    {
        "title": "The child who remembered a past life in perfect detail",
        "script": (
            "When James was three years old, he started drawing maps of places he had never been. "
            "He knew the names of streets in a city he had never visited. "
            "Investigators were shocked to discover every detail was accurate — from 60 years ago. "
            "He described a secret room in a house that was demolished in 1952. "
            "When his parents took him to that city, he walked directly to the location. "
            "Scientists have no explanation for what he revealed that day."
        ),
    },
]

from voice import text_to_speech
from video import create_video
from emotion_engine import optimize_for_narration
from retention_engine import insert_retention_hooks

results = []

for i, topic in enumerate(TOPICS):
    print(f"\n{'='*55}")
    print(f"[{i+1}/3] Generating: {topic['title'][:50]}...")
    print(f"{'='*55}")
    start = time.time()

    script = optimize_for_narration(insert_retention_hooks(topic["script"]))

    audio_path = f"test_output/voice_{i+1}.mp3"
    video_path = f"test_output/video_{i+1}.mp4"

    audio = text_to_speech(script)
    os.rename(audio, audio_path)

    video = create_video(audio_path, script, output=video_path)

    elapsed = round(time.time() - start, 1)
    size_mb = round(os.path.getsize(video_path) / (1024*1024), 1)

    results.append({
        "index": i + 1,
        "title": topic["title"],
        "video": video_path,
        "size_mb": size_mb,
        "time_s": elapsed,
    })

    print(f"\n✅ Video {i+1} done | {size_mb}MB | {elapsed}s")

print(f"\n{'='*55}")
print("ALL DONE — Results:")
print(f"{'='*55}")
for r in results:
    print(f"  [{r['index']}] {r['video']} | {r['size_mb']}MB | {r['time_s']}s")
    print(f"       {r['title']}")
print(f"{'='*55}")
