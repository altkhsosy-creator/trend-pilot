import os
import subprocess
import tempfile
import requests
import re

from scene_router import split_into_scenes
from ai_video import generate_ai_scene

import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

try:
    from moviepy.editor import (
        VideoFileClip, ColorClip, TextClip, CompositeVideoClip,
        AudioFileClip, CompositeAudioClip, concatenate_videoclips, ImageClip,
    )
except ImportError:
    from moviepy import (
        VideoFileClip, ColorClip, TextClip, CompositeVideoClip,
        AudioFileClip, CompositeAudioClip, concatenate_videoclips, ImageClip,
    )

from assets.music import get_music_for_segment
import numpy as np

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")


def _set_dur(clip, duration):
    if hasattr(clip, 'with_duration'):
        return clip.with_duration(duration)
    return clip.set_duration(duration)


def _set_audio(clip, audio):
    if hasattr(clip, 'with_audio'):
        return clip.with_audio(audio)
    return clip.set_audio(audio)


W, H = 960, 540


def add_segment_music(video_segment, segment_type, duration):
    """إضافة موسيقى مناسبة لنوع المقطع مع خفض الصوت"""
    music_file = get_music_for_segment(segment_type)
    music_path = os.path.join(os.path.dirname(__file__), "assets", "music", music_file)

    if not os.path.exists(music_path):
        return video_segment

    try:
        music = AudioFileClip(music_path)
        music = music.subclip(0, min(duration, music.duration))
        music = music.volumex(0.25)  # 25% من صوت الراوي

        if video_segment.audio:
            final_audio = CompositeAudioClip([video_segment.audio, music])
            return _set_audio(video_segment, final_audio)
        else:
            return _set_audio(video_segment, music)
    except Exception as e:
        print(f"[music] فشل إضافة الموسيقى ({segment_type}): {e}")
        return video_segment


def get_stock_video_urls(query="motivation business success", n=8):
    """يجلب فيديوهات من Pexels حسب موضوع القصة"""
    if not PEXELS_API_KEY:
        return []

    # تحسين الـ query حسب نوع القصة
    queries = {
        "business": "business success entrepreneur",
        "tech": "technology future coding",
        "horror": "dark mystery suspense",
        "inspirational": "sunset mountain hope",
        "science": "science space discovery",
        "default": "motivation viral trend"
    }

    actual_query = queries.get(query, query) if isinstance(query, str) else queries["default"]

    url = f"https://api.pexels.com/videos/search?query={actual_query}&per_page={n}&orientation=landscape"
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


def make_gradient_card(text, duration, is_hook=False):
    """
    Renders text onto a gradient using PIL — single static ImageClip.
    No per-frame Python rendering, so encoding is fast.
    """
    from PIL import Image, ImageDraw, ImageFont

    arr = np.zeros((H, W, 3), dtype=np.uint8)
    for y in range(H):
        t = y / H
        if is_hook:
            arr[y, :] = [int(100 + 100 * t), int(20 + 40 * t), int(20 + 30 * t)]
        else:
            arr[y, :] = [int(5 + 25 * t), int(5 + 15 * t), int(20 + 45 * t)]

    pil_img = Image.fromarray(arr)
    draw = ImageDraw.Draw(pil_img)

    words = text.strip().split()
    lines, line = [], []
    for w in words:
        line.append(w)
        if len(" ".join(line)) > 28:
            lines.append(" ".join(line[:-1]))
            line = [w]
    if line:
        lines.append(" ".join(line))

    fontsize = 48 if is_hook else 40
    font = None
    for fp in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
    ]:
        try:
            font = ImageFont.truetype(fp, fontsize)
            break
        except Exception:
            pass
    if font is None:
        font = ImageFont.load_default()

    y0 = H // 2 - len(lines) * (fontsize // 2 + 8)
    for i, ln in enumerate(lines[:5]):
        try:
            bbox = draw.textbbox((0, 0), ln, font=font)
            x = (W - (bbox[2] - bbox[0])) // 2
            draw.text((x, y0 + i * (fontsize + 8)), ln, fill=(255, 255, 255), font=font)
        except Exception:
            pass

    card = _set_dur(ImageClip(np.array(pil_img)), duration)

    # تأثير zoom بطيء: من scale=1.0 إلى scale=1.05 على مدى المقطع
    card = card.resize(lambda t: 1 + 0.05 * (t / duration))
    # قص لإعادة الأبعاد الأصلية (W×H) بعد التكبير
    card = card.crop(
        x_center=card.w / 2,
        y_center=card.h / 2,
        width=W,
        height=H,
    )

    return card


def extract_segments_with_hooks(script):
    """
    يقسم السكريبت إلى أجزاء تفصل بين الـ hooks
    ويعيد قائمة: [(نص, هل هو hook؟), ...]
    """
    # البحث عن hooks المحاطة بـ ✨ ✨
    pattern = r'✨(.*?)✨'
    parts = re.split(pattern, script, flags=re.DOTALL)

    segments = []
    for i, part in enumerate(parts):
        part = part.strip()
        if not part:
            continue
        # الأجزاء الفردية (بعد الـ split) هي hooks إذا كان i فردي
        is_hook = (i % 2 == 1)
        if is_hook:
            # تنظيف الـ hook من الرموز الإضافية
            part = part.replace("*", "").strip()
        segments.append((part, is_hook))

    # إذا لم يتم العثور على hooks، استخدم الطريقة القديمة
    if len(segments) <= 1:
        sentences = [s.strip() for s in script.replace("\n", " ").split(".") if len(s.strip()) > 10]
        return [(s, False) for s in sentences[:8]]

    return segments


def create_zoom_effect(clip, zoom_factor=1.1, duration=None):
    """يضيف تأثير تكبير بطيء (Ken Burns effect)"""
    if duration is None:
        duration = clip.duration

    def make_frame(t):
        frame = clip.get_frame(t)
        h, w = frame.shape[:2]
        scale = 1 + (zoom_factor - 1) * (t / duration)
        new_h, new_w = int(h * scale), int(w * scale)
        from moviepy.video.fx.resize import resize
        zoomed = resize(clip, newsize=(new_w, new_h))
        return zoomed.get_frame(t)

    return clip.fl(make_frame)


def create_video(audio_path, script, output="video.mp4", story_type="default"):
    """
    النسخة المطورة: تحترم الـ hooks وتضيف تأثيرات بصرية مختلفة لكل hook
    """
    audio = AudioFileClip(audio_path)
    total = audio.duration

    # استخراج الأجزاء مع تحديد أيها hooks
    segments = extract_segments_with_hooks(script)
    print(f"[video] تم العثور على {len(segments)} مقطع ({sum(1 for _,h in segments if h)} hooks)")

    # جلب فيديوهات خلفية
    urls = get_stock_video_urls(story_type, n=len(segments) + 3)

    scenes = []
    with tempfile.TemporaryDirectory() as tmp:
        # تحميل الفيديوهات
        video_paths = []
        for u in urls:
            p = download_clip(u, tmp)
            if p:
                video_paths.append(p)

        # حساب مدة كل مقطع
        duration_per_segment = total / max(len(segments), 1)

        # تحديد مواضع الـ hooks لتحديد نوع كل منها
        hook_indices = [i for i, (_, h) in enumerate(segments) if h]
        n_hooks = len(hook_indices)

        for idx, (text, is_hook) in enumerate(segments):
            # مدة هذا المقطع
            seg_dur = min(duration_per_segment, 7.0)
            if is_hook:
                seg_dur = max(2.5, seg_dur * 0.7)

            # تحديد نوع المقطع للموسيقى
            if is_hook:
                hook_pos = hook_indices.index(idx)
                if n_hooks == 1 or hook_pos == 0:
                    seg_music_type = "hook_start"
                elif hook_pos == n_hooks - 1:
                    seg_music_type = "hook_end"
                else:
                    seg_music_type = "hook_middle"
            elif idx == len(segments) - 1:
                seg_music_type = "closing"
            else:
                seg_music_type = "story_normal"

            # محاولة استخدام فيديو حقيقي
            video_used = False
            if idx < len(video_paths) and not is_hook:
                try:
                    raw = VideoFileClip(video_paths[idx])
                    dur = min(seg_dur, raw.duration)
                    raw = raw.subclip(0, dur)

                    # تكبير (zoom) للحركة
                    scale = max(W / raw.w, H / raw.h)
                    raw = raw.resize(scale)

                    xc = (raw.w - W) / 2
                    yc = (raw.h - H) / 2
                    raw = raw.crop(x1=xc, y1=yc, x2=xc + W, y2=yc + H)

                    raw = add_segment_music(raw, seg_music_type, dur)
                    scenes.append(raw)
                    video_used = True
                    print(f"[video] مقطع {idx+1}: فيديو ✓ | موسيقى: {seg_music_type}")
                except Exception as e:
                    print(f"[video] فشل الفيديو: {e}")

            if not video_used:
                card = make_gradient_card(text, seg_dur, is_hook=is_hook)
                card = add_segment_music(card, seg_music_type, seg_dur)
                scenes.append(card)
                print(f"[video] مقطع {idx+1}: {'🔥 HOOK' if is_hook else 'بطاقة عادية'} | موسيقى: {seg_music_type}")

    # دمج جميع المشاهد
    if not scenes:
        scenes.append(ColorClip(size=(W, H), color=(10, 10, 30), duration=total))

    final = concatenate_videoclips(scenes, method="compose")

    # ضبط المدة لتطابق الصوت
    if final.duration < total:
        loop = scenes[-1].loop(duration=total - final.duration + 0.1)
        final = concatenate_videoclips([final, loop], method="compose")
    elif final.duration > total:
        final = final.subclip(0, total)

    # خلط صوت الراوي مع الموسيقى الخلفية (إن وُجدت)
    if final.audio:
        final = _set_audio(final, CompositeAudioClip([audio, final.audio]))
    else:
        final = _set_audio(final, audio)

    # تصدير الفيديو
    tmp_out = output + ".tmp.mp4"
    final.write_videofile(
        tmp_out, fps=24, codec="libx264", audio_codec="aac",
        preset="ultrafast", threads=4, logger=None,
    )

    # إعادة ترميز لضمان التوافق
    result = subprocess.run(
        ["ffmpeg", "-i", tmp_out, "-movflags", "+faststart", "-c", "copy", output, "-y"],
        capture_output=True,
    )
    if os.path.exists(tmp_out):
        os.remove(tmp_out)

    if result.returncode != 0:
        import shutil
        shutil.move(tmp_out if os.path.exists(tmp_out) else output, output)

    # إحصاءات عن الفيديو المنتج
    hook_count = sum(1 for _,h in segments if h)
    print(f"\n🎬 [video] تم إنتاج الفيديو → {output}")
    print(f"   - عدد hooks مرئية: {hook_count}")
    print(f"   - مدة الفيديو: {total:.1f} ثانية")
    print(f"   - عدد المشاهد: {len(scenes)}")

    return output


def create_hybrid_video(audio_path, script, output="video.mp4"):
    """نفس النسخة المطورة ولكن مع دعم AI scenes"""
    return create_video(audio_path, script, output)


# دالة اختبار سريع
if __name__ == "__main__":
    # اختبار استخراج hooks
    test_script = """
    هذه قصة عن رجل غير حياته.

    ✨ 💥 مفاجأة صادمة... كل ما قلته لك كان خطأ! ✨

    بدأ من الصفر وبنى إمبراطورية.

    ✨ 👑 وهذا هو السر الذي يخفيه الأغنياء عنك ✨

    استمر في العمل حتى نجح.

    ✨ ⏱️ لديك 5 ثوانٍ فقط... 5..4..3.. ✨
    """

    segments = extract_segments_with_hooks(test_script)
    for txt, is_hook in segments:
        print(f"{'🔥 HOOK' if is_hook else '📖 TEXT'}: {txt[:50]}...")