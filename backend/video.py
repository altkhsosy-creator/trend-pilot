import os
import subprocess
import tempfile
import requests

from scene_router import split_into_scenes
from ai_video import generate_ai_scene

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

from moviepy.editor import (
    VideoFileClip, ColorClip, TextClip, CompositeVideoClip,
    AudioFileClip, concatenate_videoclips, ImageClip,
)
import numpy as np

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
W, H = 1280, 720


def get_stock_video_urls(query="nature landscape", n=5):
    if not PEXELS_API_KEY:
        return []
    url = f"https://api.pexels.com/videos/search?query={query}&per_page={n}&orientation=landscape"
    headers = {"Authorization": PEXELS_API_KEY}
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        links = []
        for video in data.get("videos", []):
            best = None
            for f in video.get("video_files", []):
                if f.get("quality") == "sd" and f.get("width", 0) >= 320:
                    if best is None or f.get("width", 0) > best.get("width", 0):
                        best = f
            if best:
                links.append(best["link"])
        return links[:n]
    except Exception as e:
        print(f"[video] Pexels failed: {e}")
        return []


def download_clip(url, tmp_dir):
    try:
        r = requests.get(url, timeout=30, stream=True)
        r.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".mp4", dir=tmp_dir)
        with os.fdopen(fd, "wb") as f:
            for chunk in r.iter_content(chunk_size=65536):
                f.write(chunk)
        return path
    except Exception as e:
        print(f"[video] Download failed: {e}")
        return None


def make_gradient_card(text, duration):
    gradient = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / H
        gradient[y, :] = [int(5 + 25 * t), int(5 + 15 * t), int(20 + 45 * t)]

    bg = ImageClip(gradient).set_duration(duration)

    words = text.strip().split()
    lines, line = [], []
    for w in words:
        line.append(w)
        if len(" ".join(line)) > 30:
            lines.append(" ".join(line[:-1]))
            line = [w]
    if line:
        lines.append(" ".join(line))

    overlays = [bg]
    y0 = H // 2 - len(lines) * 42
    for i, ln in enumerate(lines[:5]):
        try:
            txt = TextClip(ln, fontsize=44, color="white", font="Arial",
                           method="label").set_duration(duration)
            txt = txt.set_position(("center", y0 + i * 52))
            overlays.append(txt)
        except Exception:
            pass

    return CompositeVideoClip(overlays, size=(W, H)).set_duration(duration)


def create_video(audio_path, script, output="video.mp4"):
    audio = AudioFileClip(audio_path)
    total = audio.duration

    sentences = [s.strip() for s in script.replace("\n", " ").split(".") if len(s.strip()) > 10][:6]
    if not sentences:
        sentences = [script[:120]]

    urls = get_stock_video_urls("viral science news", n=5)

    scenes = []
    clip_dur = max(3.0, total / max(len(sentences), 1))

    with tempfile.TemporaryDirectory() as tmp:
        paths = []
        for u in urls:
            p = download_clip(u, tmp)
            if p:
                paths.append(p)
                print(f"[video] Downloaded clip {len(paths)}")

        for i, sent in enumerate(sentences):
            if i < len(paths):
                try:
                    raw = VideoFileClip(paths[i])
                    dur = min(clip_dur, raw.duration)
                    raw = raw.subclip(0, dur)

                    scale = max(W / raw.w, H / raw.h)
                    raw = raw.resize(scale)

                    xc = (raw.w - W) / 2
                    yc = (raw.h - H) / 2
                    raw = raw.crop(x1=xc, y1=yc, x2=xc + W, y2=yc + H)

                    scenes.append(raw)
                    print(f"[video] Scene {i+1}: stock clip ✓")
                    continue
                except Exception as e:
                    print(f"[video] Scene {i+1}: stock clip failed — {e}")

            card = make_gradient_card(sent, clip_dur)
            scenes.append(card)
            print(f"[video] Scene {i+1}: gradient card")

    if not scenes:
        scenes.append(ColorClip(size=(W, H), color=(10, 10, 30), duration=total))

    final = concatenate_videoclips(scenes, method="compose")
    if final.duration < total:
        loop = scenes[-1].loop(duration=total - final.duration + 0.1)
        final = concatenate_videoclips([final, loop], method="compose")
    final = final.set_audio(audio)

    tmp_out = output + ".tmp.mp4"
    final.write_videofile(
        tmp_out, fps=24, codec="libx264", audio_codec="aac",
        preset="ultrafast", threads=2, logger=None,
    )

    result = subprocess.run(
        ["ffmpeg", "-i", tmp_out, "-movflags", "+faststart", "-c", "copy", output, "-y"],
        capture_output=True,
    )
    if os.path.exists(tmp_out):
        os.remove(tmp_out)

    if result.returncode != 0:
        import shutil
        shutil.move(tmp_out if os.path.exists(tmp_out) else output, output)

    print(f"[video] Done → {output}")
    return output


def create_hybrid_video(audio_path, script, output="video.mp4"):

    audio = AudioFileClip(audio_path)
    scenes = split_into_scenes(script)

    final_clips = []
    ai_index = 0

    for i, scene in enumerate(scenes):

        if scene["type"] == "ai":
            # AI scene (placeholder or future API)
            clip_path = generate_ai_scene(scene["text"], ai_index)
            ai_index += 1

            clip = ColorClip(size=(1280, 720), color=(255, 0, 0), duration=3)
            clip = clip.set_duration(3)

        else:
            # Pexels fallback
            clip = ColorClip(size=(1280, 720), color=(0, 0, 0), duration=4)

        final_clips.append(clip)

    video = concatenate_videoclips(final_clips).set_audio(audio)
    video.write_videofile(output, fps=24)

    return output
