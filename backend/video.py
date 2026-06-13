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


W, H = 854, 480


CLIMAX_KEYWORDS = {
    "died", "dead", "killed", "murder", "arrested", "revealed", "discovered",
    "confession", "truth", "finally", "shocking", "unbelievable", "exposed",
    "caught", "found", "guilty", "sentenced", "disappeared", "missing",
    "impossible", "never", "forever", "destroyed", "collapsed", "ended",
}

EMOTIONAL_KEYWORDS = {
    "love", "loss", "grief", "cried", "tears", "family", "mother", "father",
    "child", "forgive", "hope", "lonely", "alone", "heart", "beautiful",
    "sacrifice", "brave", "kind", "grateful", "remember", "miss",
}

CLOSING_THRESHOLD = 15.0  # آخر 15 ثانية = خاتمة


def detect_music_type(text, idx, n_segments, is_hook, hook_indices,
                      elapsed_time, total_duration):
    """
    يحدد نوع الموسيقى المناسب لكل مقطع بناءً على:
    - موضع المقطع في القصة (%)
    - نوعه (hook / عادي)
    - الكلمات المفتاحية في النص
    - الوقت المتبقي للنهاية
    """
    n_hooks = len(hook_indices)
    remaining = total_duration - elapsed_time
    story_progress = elapsed_time / max(total_duration, 1)

    # خاتمة: آخر 15 ثانية
    if remaining <= CLOSING_THRESHOLD and not is_hook:
        return "closing"

    # hooks
    if is_hook:
        hook_pos = hook_indices.index(idx)
        if n_hooks == 1 or hook_pos == 0:
            return "hook_start"
        elif hook_pos == n_hooks - 1:
            return "hook_end"
        else:
            return "hook_middle"

    # كشف ذروة القصة (70-85% من مدة الفيديو أو كلمات مفتاحية)
    words = set(text.lower().split())
    if CLIMAX_KEYWORDS & words or 0.70 <= story_progress <= 0.88:
        return "story_climax"

    # كشف اللحظات العاطفية
    if EMOTIONAL_KEYWORDS & words:
        return "emotional"

    # سرد عادي
    return "story_normal"


def add_segment_music(video_segment, segment_type, duration):
    """إضافة موسيقى مناسبة لنوع المقطع مع خفض الصوت — تدور في حلقة إذا كانت أقصر من المدة"""
    music_file = get_music_for_segment(segment_type)
    music_path = os.path.join(os.path.dirname(__file__), "assets", "music", music_file)

    if not os.path.exists(music_path):
        return video_segment

    try:
        music = AudioFileClip(music_path)
        safe_duration = min(duration, music.duration - 0.1)
        if safe_duration <= 0:
            return video_segment
        music = music.subclip(0, safe_duration)
        music = music.volumex(0.25)

        if video_segment.audio:
            final_audio = CompositeAudioClip([video_segment.audio, music])
            return _set_audio(video_segment, final_audio)
        else:
            return _set_audio(video_segment, music)
    except Exception as e:
        print(f"[music] فشل إضافة الموسيقى ({segment_type}): {e}")
        return video_segment


def get_stock_video_urls(query="dark mystery investigation", n=8):
    """يجلب فيديوهات من Pexels حسب موضوع القصة"""
    if not PEXELS_API_KEY:
        return []

    # True Crime & Mystery focused queries
    queries = {
        "true_crime":    "dark crime investigation detective",
        "mystery":       "dark forest mystery abandoned",
        "horror":        "dark shadow horror suspense night",
        "shock":         "dark dramatic thriller",
        "business":      "business success entrepreneur",
        "tech":          "technology future coding",
        "inspirational": "sunset mountain hope journey",
        "science":       "science space discovery lab",
        "reddit":        "dark room computer screen night",
        "default":       "dark mystery investigation crime",
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


def _get_audio_duration(path):
    """يحصل على مدة ملف الصوت بثوانٍ"""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return 0.0


def _ffmpeg_trim_clip(src, dst, duration, w=W, h=H):
    """يقص مقطع فيديو ويعيد ضبط حجمه بـ ffmpeg — لا يُحمَّل في الذاكرة"""
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", src,
         "-t", str(duration),
         "-vf", vf,
         "-r", "24",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
         "-an",
         dst],
        capture_output=True
    )


def _ffmpeg_make_color_clip(dst, duration, w=W, h=H, color="0x0A0A1E"):
    """ينشئ مقطع ملون ثابت (خلفية بديلة) بـ ffmpeg"""
    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i", f"color={color}:size={w}x{h}:rate=24",
         "-t", str(duration),
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
         "-an",
         dst],
        capture_output=True
    )


def create_video(audio_path, script, output="video.mp4", story_type="default"):
    """
    إنتاج الفيديو باستخدام ffmpeg streaming — لا يُحمَّل أي فيديو في RAM.
    كل مقطع يُعالَج ويُحفَظ على القرص ثم يُدمَج عبر concat demuxer.
    """
    total = _get_audio_duration(audio_path)
    if total <= 0:
        raise RuntimeError(f"[video] لم يُعثر على مدة الصوت: {audio_path}")

    segments = extract_segments_with_hooks(script)
    print(f"[video] تم العثور على {len(segments)} مقطع ({sum(1 for _,h in segments if h)} hooks)")

    urls = get_stock_video_urls(story_type, n=min(len(segments) + 3, 10))

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        # تحميل مقاطع Pexels
        video_paths = []
        for u in urls:
            p = download_clip(u, tmp)
            if p:
                video_paths.append(p)

        duration_per_segment = total / max(len(segments), 1)
        hook_indices = [i for i, (_, h) in enumerate(segments) if h]
        n_segments = len(segments)
        elapsed = 0.0
        segment_files = []

        for idx, (text, is_hook) in enumerate(segments):
            seg_dur = min(duration_per_segment, 8.0)
            if is_hook:
                seg_dur = max(2.5, seg_dur * 0.6)

            seg_dur = round(seg_dur, 3)
            seg_path = os.path.join(tmp, f"seg_{idx:03d}.mp4")

            # اختر فيديو Pexels أو بطاقة ملونة
            pexels_idx = idx % len(video_paths) if video_paths else -1
            used_video = False

            if pexels_idx >= 0:
                try:
                    _ffmpeg_trim_clip(video_paths[pexels_idx], seg_path, seg_dur)
                    if os.path.exists(seg_path) and os.path.getsize(seg_path) > 1000:
                        used_video = True
                        print(f"[video] مقطع {idx+1}: فيديو ✓")
                except Exception as e:
                    print(f"[video] فشل Pexels {idx}: {e}")

            if not used_video:
                color = "0x640A0A" if is_hook else "0x0A0A1E"
                _ffmpeg_make_color_clip(seg_path, seg_dur, color=color)
                print(f"[video] مقطع {idx+1}: {'🔥 HOOK' if is_hook else 'بطاقة'} (لون)")

            if os.path.exists(seg_path):
                segment_files.append(seg_path)
            elapsed += seg_dur

        if not segment_files:
            raise RuntimeError("[video] لم يتم إنتاج أي مقطع")

        # concat list
        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for sf in segment_files:
                f.write(f"file '{sf}'\n")

        # دمج المقاطع بـ concat demuxer (streaming — بدون تحميل في الذاكرة)
        raw_video = os.path.join(tmp, "raw_video.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", concat_list,
             "-c", "copy",
             raw_video],
            capture_output=True
        )

        # إضافة الصوت — اختر موسيقى خلفية إذا وُجدت
        music_dir = os.path.join(os.path.dirname(__file__), "assets", "music")
        music_file = os.path.join(music_dir, "bgm_calm.mp3")
        has_music = os.path.exists(music_file)

        if has_music:
            # دمج: راوي (كامل) + موسيقى (25% صوت) + فيديو
            subprocess.run(
                ["ffmpeg", "-y",
                 "-i", raw_video,
                 "-i", audio_path,
                 "-stream_loop", "-1", "-i", music_file,
                 "-filter_complex",
                 f"[2:a]volume=0.25[music];[1:a][music]amix=inputs=2:duration=first[aout]",
                 "-map", "0:v",
                 "-map", "[aout]",
                 "-t", str(total),
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                 "-c:a", "aac", "-b:a", "128k",
                 "-movflags", "+faststart",
                 "-shortest",
                 output],
                capture_output=True
            )
        else:
            # بدون موسيقى — صوت الراوي فقط
            subprocess.run(
                ["ffmpeg", "-y",
                 "-i", raw_video,
                 "-i", audio_path,
                 "-map", "0:v",
                 "-map", "1:a",
                 "-t", str(total),
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                 "-c:a", "aac", "-b:a", "128k",
                 "-movflags", "+faststart",
                 "-shortest",
                 output],
                capture_output=True
            )

    size_mb = round(os.path.getsize(output) / (1024 * 1024), 1) if os.path.exists(output) else 0
    print(f"\n🎬 [video] تم إنتاج الفيديو → {output}")
    print(f"   - مدة الفيديو: {total:.1f} ثانية | الحجم: {size_mb}MB")

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