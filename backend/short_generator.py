import os
import subprocess
from moviepy.video.io.VideoFileClip import VideoFileClip


def extract_shorts(long_video_path: str, num_shorts: int = 3, duration: int = 60) -> list[str]:
    """
    Extracts 3 Shorts from the strongest moments of a True Crime video:
      Short 1 — Hook       (first 5%  of video — scroll-stopping opener)
      Short 2 — Plot Twist (50% mark  — mid-story revelation)
      Short 3 — Climax     (80% mark  — peak shocking moment)

    Returns a list of output file paths.
    """
    if not os.path.exists(long_video_path):
        print(f"[shorts] Video not found: {long_video_path}")
        return []

    # Path resolution — works on DigitalOcean server and Replit
    server_path = "/root/trend-pilot/backend/output/shorts"
    local_path = os.path.join(os.path.dirname(__file__), "output", "shorts")
    output_dir = server_path if os.path.exists("/root/trend-pilot") else local_path
    os.makedirs(output_dir, exist_ok=True)

    # Get total duration
    with VideoFileClip(long_video_path) as video:
        total_duration = video.duration

    # The 3 key moments — labeled for True Crime storytelling
    moment_labels = ["hook", "plot_twist", "climax"]
    positions = [
        max(0, total_duration * 0.05),   # Hook — grab them immediately
        total_duration * 0.50,            # Plot Twist — mid-story revelation
        total_duration * 0.80,            # Climax — the shocking peak
    ]

    shorts_paths = []
    for i, (label, start_time) in enumerate(zip(moment_labels, positions[:num_shorts])):
        end_time = min(start_time + duration, total_duration)
        output_path = os.path.join(output_dir, f"short_{i+1}_{label}_{int(start_time)}.mp4")

        cmd = [
            "ffmpeg", "-i", long_video_path,
            "-ss", str(start_time), "-to", str(end_time),
            "-c", "copy", "-avoid_negative_ts", "make_zero",
            output_path, "-y",
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"[shorts] ✅ {label.upper()} short → {os.path.basename(output_path)}")
            shorts_paths.append(output_path)
        except Exception as e:
            print(f"[shorts] ❌ Failed {label}: {e}")

    return shorts_paths
