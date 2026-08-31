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


W, H = 1920, 1080


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


def _build_dynamic_music_track(segment_music_info, music_dir, output_path):
    """
    يبني مسار موسيقي ديناميكي يتغير مع كل مقطع.
    segment_music_info: list of (duration_seconds, music_type)
    يُخرج ملف AAC بنفس مدة الفيديو بالضبط.
    """
    if not segment_music_info:
        return None

    cmd = ["ffmpeg", "-y"]
    filter_parts = []

    for i, (duration, music_type) in enumerate(segment_music_info):
        music_file = get_music_for_segment(music_type)
        music_path = os.path.join(music_dir, music_file)
        if not os.path.exists(music_path):
            music_path = os.path.join(music_dir, "bgm_calm.mp3")
        cmd += ["-stream_loop", "-1", "-i", music_path]
        filter_parts.append(
            f"[{i}:a]atrim=duration={round(duration, 3)},"
            f"asetpts=PTS-STARTPTS,volume=0.08[m{i}]"
        )

    n = len(segment_music_info)
    concat_inputs = "".join(f"[m{i}]" for i in range(n))
    filter_complex = ";".join(filter_parts) + f";{concat_inputs}concat=n={n}:v=0:a=1[music_out]"

    cmd += ["-filter_complex", filter_complex,
            "-map", "[music_out]",
            "-c:a", "aac", "-b:a", "128k",
            output_path]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 500:
        types_used = list(dict.fromkeys(t for _, t in segment_music_info))
        print(f"[music] ✅ مسار ديناميكي ({n} مقاطع) → {' → '.join(types_used)}")
        return output_path

    print(f"[music] ⚠️ فشل بناء المسار الديناميكي، سيُستخدم الملف الثابت")
    return None


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
    # إذا لم يتم العثور على hooks، استخدم الطريقة القديمة — بدون تحديد عدد ثابت،
    # نأخذ كل جمل السكربت (مقسّمة على . ! ؟ ...) حتى لا يُقتطع أي جزء من المحتوى
    if len(segments) <= 1:
        raw = re.split(r'[.!؟\n]+', script)
        sentences = [s.strip() for s in raw if len(s.strip()) > 10]
        return [(s, False) for s in sentences]

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


def _ffmpeg_trim_clip(src, dst, duration, w=W, h=H, fade_in=0.3, fade_out=0.3, start_offset=0.0):
    """
    يقص مقطع فيديو مع:
    - تدرج لوني سينمائي (cinematic grade)
    - fade-in من الأسود في البداية
    - fade-out للأسود في النهاية
    """
    fade_out_start = max(0.0, duration - fade_out)
    vf = (
        f"scale={w}:{h}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h},"
        # تدرج لوني سينمائي — داكن، درامي، بارد
        f"curves=r='0/0 0.15/0.07 0.75/0.62 1/0.88':"
        f"g='0/0 0.15/0.09 0.75/0.60 1/0.84':"
        f"b='0/0.04 0.4/0.35 0.75/0.58 1/0.80',"
        # fade-in من الأسود
        f"fade=t=in:st=0:d={fade_in},"
        # fade-out للأسود
        f"fade=t=out:st={round(fade_out_start, 3)}:d={fade_out}"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(round(max(start_offset, 0.0), 3)), "-i", src,
         "-t", str(duration),
         "-vf", vf,
         "-r", "24",
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
         "-an",
         dst],
        capture_output=True
    )


# مدد المقاطع حسب نوع المشهد — لخلق إيقاع وثائقي
SEGMENT_DURATIONS = {
    "hook_start":    (3.0, 5.0),   # بداية سريعة لشد الانتباه
    "hook_middle":   (3.5, 5.5),   # hook وسطي
    "hook_end":      (2.5, 4.0),   # ذروة hook — أسرع قطع
    "story_normal":  (5.0, 8.0),   # سرد عادي — أطول للتنفس
    "story_tension": (3.0, 5.0),   # توتر — قطع أسرع
    "story_climax":  (2.5, 4.0),   # ذروة — أسرع قطع
    "emotional":     (6.0, 9.0),   # عاطفي — أبطأ للتأمل
    "closing":       (5.0, 7.0),   # خاتمة — هادئة ومدروسة
}


def get_segment_duration(music_type: str, audio_dur_per_seg: float) -> float:
    """يحسب مدة المقطع المناسبة بناءً على نوعه وإيقاع الصوت"""
    min_dur, max_dur = SEGMENT_DURATIONS.get(music_type, (4.0, 7.0))
    # نطابق مع إيقاع الصوت لكن ضمن الحدود الدرامية
    return round(min(max_dur, max(min_dur, audio_dur_per_seg * 0.8)), 3)


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


FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def _esc(text):
    """تهريب النص لـ ffmpeg drawtext"""
    return (text
            .replace("\\", "\\\\")
            .replace("'", "\\'")
            .replace(":", "\\:")
            .replace("[", "\\[")
            .replace("]", "\\]")
            .replace("%", "\\%"))


def _wrap_text(text, max_chars=52):
    """تقسيم النص إلى سطرين بحد أقصى max_chars في السطر"""
    words = text.strip().split()
    lines, line = [], []
    for w in words:
        if len(" ".join(line + [w])) > max_chars:
            if line:
                lines.append(" ".join(line))
            line = [w]
        else:
            line.append(w)
    if line:
        lines.append(" ".join(line))
    return lines[:2]


def _ffmpeg_make_title_card(dst, title, duration=5, w=W, h=H):
    """بطاقة عنوان دراماتيكية في بداية الفيديو"""
    label = _esc("TRUE CRIME")
    title_lines = _wrap_text(title, max_chars=42)
    title_text = _esc(title_lines[0])
    title_text2 = _esc(title_lines[1]) if len(title_lines) > 1 else ""

    drawtext = (
        f"drawtext=fontfile={FONT_PATH}:text='{label}':"
        f"fontsize=60:fontcolor=0xFF3333:x=(w-text_w)/2:y=h/2-200:"
        f"alpha='if(lt(t,0.5),t/0.5,1)',"

        f"drawtext=fontfile={FONT_PATH}:text='{title_text}':"
        f"fontsize=88:fontcolor=white:x=(w-text_w)/2:y=h/2-90:"
        f"box=1:boxcolor=black@0.0:alpha='if(lt(t,0.5),t/0.5,1)'"
    )
    if title_text2:
        drawtext += (
            f",drawtext=fontfile={FONT_PATH}:text='{title_text2}':"
            f"fontsize=88:fontcolor=white:x=(w-text_w)/2:y=h/2+20:"
            f"alpha='if(lt(t,0.5),t/0.5,1)'"
        )

    subprocess.run(
        ["ffmpeg", "-y",
         "-f", "lavfi", "-i", f"color=black:size={w}x{h}:rate=24",
         "-t", str(duration),
         "-vf", drawtext,
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
         "-an", dst],
        capture_output=True
    )


def _ffmpeg_add_text_overlay(src, dst, text, w=W, h=H):
    """يضيف نص القصة كـ subtitle في أسفل الفيديو"""
    lines = _wrap_text(text, max_chars=52)
    line1 = _esc(lines[0]) if lines else ""
    line2 = _esc(lines[1]) if len(lines) > 1 else ""

    if not line1:
        try:
            import shutil
            shutil.copy(src, dst)
        except Exception:
            pass
        return

    box = "box=1:boxcolor=black@0.65:boxborderw=22"
    y1 = "h-220" if line2 else "h-160"
    y2 = "h-130"

    drawtext = (
        f"drawtext=fontfile={FONT_PATH}:text='{line1}':"
        f"fontsize=68:fontcolor=white:x=(w-text_w)/2:y={y1}:{box}"
    )
    if line2:
        drawtext += (
            f",drawtext=fontfile={FONT_PATH}:text='{line2}':"
            f"fontsize=68:fontcolor=white:x=(w-text_w)/2:y={y2}:{box}"
        )

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", src,
         "-vf", drawtext,
         "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
         "-an", dst],
        capture_output=True
    )
    if result.returncode != 0 or not os.path.exists(dst):
        import shutil
        shutil.copy(src, dst)


def _segment_pexels_query(text, story_type="default"):
    """يستخرج كلمات مفتاحية من نص المقطع لجلب فيديو Pexels مناسب"""
    keywords = {
        "investigation": "detective investigation crime scene",
        "killer": "dark alley danger shadow night",
        "murder": "crime scene police investigation dark",
        "cipher": "code puzzle mystery dark",
        "police": "police car lights crime investigation",
        "evidence": "forensic laboratory evidence crime",
        "body": "crime scene investigation dark forest",
        "disappear": "fog mystery abandoned dark",
        "confession": "dark room shadow dramatic",
        "victim": "empty street night dark danger",
        "suspect": "shadow silhouette mystery dark",
        "secret": "dark corridor mystery shadow",
        "fear": "dark stormy night suspense",
        "unknown": "fog dark mystery abandoned",
    }
    text_lower = text.lower()
    for kw, query in keywords.items():
        if kw in text_lower:
            return query
    return "dark mystery investigation crime"


def create_video(audio_path, script, output="video.mp4", story_type="default", title="", footage_dir=None):
    """
    إنتاج الفيديو باستخدام ffmpeg streaming مع:
    - Title Card دراماتيكي في البداية
    - Text Overlay على كل مقطع
    - Pexels queries مخصصة لكل مقطع
    """
    total = _get_audio_duration(audio_path)
    if total <= 0:
        raise RuntimeError(f"[video] لم يُعثر على مدة الصوت: {audio_path}")

    segments = extract_segments_with_hooks(script)
    n_hooks = sum(1 for _, h in segments if h)
    print(f"[video] {len(segments)} مقطع ({n_hooks} hooks) | {total:.1f}s")

    os.makedirs(os.path.dirname(output) if os.path.dirname(output) else ".", exist_ok=True)

    # حساب hook_indices لتحديد نوع الموسيقى
    hook_indices = [i for i, (_, h) in enumerate(segments) if h]
    segment_music_info = []  # list of (duration, music_type)
    elapsed_time = 0.0

    footage_clips = []
    if footage_dir and os.path.isdir(footage_dir):
        footage_clips = sorted(
            os.path.join(footage_dir, f)
            for f in os.listdir(footage_dir)
            if f.lower().endswith(".mp4")
        )
        if footage_clips:
            print(f"[video] استخدام {len(footage_clips)} كليب مُحمّل مسبقاً من {footage_dir}")
        clip_durations = {c: _get_audio_duration(c) for c in footage_clips}
        clip_usage_count = {c: 0 for c in footage_clips}

    with tempfile.TemporaryDirectory() as tmp:
        segment_files = []

        # ── 0. Title Card (5 ثوانٍ) ──────────────────────────────
        if title:
            title_path = os.path.join(tmp, "seg_title.mp4")
            _ffmpeg_make_title_card(title_path, title, duration=5)
            if os.path.exists(title_path) and os.path.getsize(title_path) > 500:
                segment_files.append(title_path)
                segment_music_info.append((5.0, "hook_start"))
                print("[video] ✅ Title Card أُضيف")

        duration_per_segment = total / max(len(segments), 1)

        # ── تمريرة أولى: نحسب مدة كل مقطع حسب نوعه (بدون قص فعلي)،
        # ثم نطبّع (scale) كل المدد بنسبة موحدة بحيث يساوي مجموعها
        # مدة الصوت الفعلية بالضبط — هذا يمنع فقدان أي جزء من الصوت/الفيديو
        title_dur = 5.0 if title else 0.0
        available_duration = max(total - title_dur, 1.0)

        raw_durations = []
        music_types = []
        _probe_elapsed = 0.0
        for _idx, (_text, _is_hook) in enumerate(segments):
            _mt = detect_music_type(
                _text, _idx, len(segments), _is_hook,
                hook_indices, _probe_elapsed, total
            )
            _d = get_segment_duration(_mt, duration_per_segment)
            music_types.append(_mt)
            raw_durations.append(_d)
            _probe_elapsed += _d

        raw_total = sum(raw_durations) or 1.0
        scale = available_duration / raw_total
        seg_durations = [max(1.5, round(d * scale, 3)) for d in raw_durations]

        for idx, (text, is_hook) in enumerate(segments):
            music_type = music_types[idx]
            seg_dur = seg_durations[idx]

            seg_start_time = elapsed_time
            segment_music_info.append((seg_dur, music_type))
            elapsed_time += seg_dur

            # fade أسرع عند الـ hooks والذروات، أبطأ عند العاطفي والسرد
            is_intense = music_type in ("hook_start", "hook_end", "story_climax")
            fade_dur = 0.2 if is_intense else 0.4

            raw_path = os.path.join(tmp, f"raw_{idx:03d}.mp4")
            used_video = False

            if footage_clips:
                # اختيار الكليب المناسب بناءً على موقع المقطع الزمني ضمن مدة السكربت الكلية
                clip_slot_dur = total / len(footage_clips)
                clip_idx = min(len(footage_clips) - 1, int(seg_start_time / clip_slot_dur))
                local_clip = footage_clips[clip_idx]

                # لو أعيد استخدام نفس الكليب (لأن المقاطع أكثر من الكليبات المتاحة)،
                # نقص من نقطة مختلفة داخل الكليب نفسه بدل الإعادة من الصفر دائماً —
                # يحافظ على توافق الكليب مع لحظة القصة، ويمنع تكرار نفس الفريمات بالضبط
                usage = clip_usage_count.get(local_clip, 0)
                clip_own_dur = clip_durations.get(local_clip, 0) or 0
                if usage > 0 and clip_own_dur > seg_dur:
                    start_offset = (usage * seg_dur) % max(clip_own_dur - seg_dur, 0.1)
                else:
                    start_offset = 0.0
                clip_usage_count[local_clip] = usage + 1

                _ffmpeg_trim_clip(local_clip, raw_path, seg_dur,
                                  fade_in=fade_dur, fade_out=fade_dur,
                                  start_offset=start_offset)
                if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
                    used_video = True

            if not used_video:
                # fallback: جلب حي من Pexels (فقط لو ما فيه footage مسبق أو فشل القص المحلي)
                query = _segment_pexels_query(text, story_type)
                urls = get_stock_video_urls(query, n=2)

                for url in urls:
                    clip = download_clip(url, tmp)
                    if clip:
                        _ffmpeg_trim_clip(clip, raw_path, seg_dur,
                                          fade_in=fade_dur, fade_out=fade_dur)
                        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
                            used_video = True
                            break

            if not used_video:
                color = "0x640A0A" if is_hook else "0x0A0A1E"
                _ffmpeg_make_color_clip(raw_path, seg_dur, color=color)

            final_seg = raw_path
            if os.path.exists(final_seg):
                segment_files.append(final_seg)
                icon = "🎬" if used_video else ("🔥" if is_hook else "🃏")
                print(f"[video] مقطع {idx+1}: {icon} | {music_type} | {seg_dur}s")

        if not segment_files:
            raise RuntimeError("[video] لم يتم إنتاج أي مقطع")

        # دمج بـ concat demuxer
        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for sf in segment_files:
                f.write(f"file '{sf}'\n")

        raw_video = os.path.join(tmp, "raw_video.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", concat_list, "-c", "copy", raw_video],
            capture_output=True
        )

        # إضافة الصوت + موسيقى خلفية ديناميكية
        music_dir = os.path.join(os.path.dirname(__file__), "assets", "music")
        dynamic_music_path = os.path.join(tmp, "dynamic_music.aac")
        music_track = _build_dynamic_music_track(
            segment_music_info, music_dir, dynamic_music_path
        )

        # fallback إلى ملف ثابت إذا فشل الديناميكي
        if not music_track:
            music_track = os.path.join(music_dir, "bgm_suspense.mp3")
            if not os.path.exists(music_track):
                music_track = os.path.join(music_dir, "bgm_calm.mp3")
            use_stream_loop = True
        else:
            use_stream_loop = False

        has_music = False  # الموسيقى الخلفية معطّلة بقرار — كانت تؤثر سلباً على صوت الراوي

        if has_music:
            if use_stream_loop:
                music_input = ["-stream_loop", "-1", "-i", music_track]
                audio_filter = "[2:a]volume=0.08[music];[1:a][music]amix=inputs=2:duration=first:normalize=0[aout]"
            else:
                music_input = ["-i", music_track]
                audio_filter = "[1:a][2:a]amix=inputs=2:duration=first:normalize=0[aout]"

            subprocess.run(
                ["ffmpeg", "-y",
                 "-i", raw_video,
                 "-i", audio_path,
                 *music_input,
                 "-filter_complex", audio_filter,
                 "-map", "0:v", "-map", "[aout]",
                 "-t", str(total + 5),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                 "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", "-shortest",
                 output],
                capture_output=True
            )
        else:
            subprocess.run(
                ["ffmpeg", "-y",
                 "-i", raw_video, "-i", audio_path,
                 "-map", "0:v", "-map", "1:a",
                 "-t", str(total + 5),
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                 "-c:a", "aac", "-b:a", "192k",
                 "-movflags", "+faststart", "-shortest",
                 output],
                capture_output=True
            )

    size_mb = round(os.path.getsize(output) / (1024 * 1024), 1) if os.path.exists(output) else 0
    print(f"\n🎬 [video] → {output} | {total:.0f}s | {size_mb}MB")
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