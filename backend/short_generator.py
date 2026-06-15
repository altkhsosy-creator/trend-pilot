"""
short_generator.py — Shorts مستقلة بمحتوى فريد لكل قصة
كل Short: سؤال صادم واحد → إجابة 30 ثانية → CTA للقناة
المدة: 45-55 ثانية | الدقة: 1080x1920 (عمودي لـ Shorts)
"""

import os
import json
import tempfile
import subprocess
import random
import requests
from io import BytesIO
from openai import OpenAI
from config import OPENAI_API_KEY, MOCK_MODE

SHORT_W, SHORT_H = 1080, 1920          # عمودي 9:16
SHORT_DURATION   = 52                   # ثانية مستهدفة
SHORTS_DIR = os.path.join(os.path.dirname(__file__), "output", "shorts")
FONT_PATH  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PEXELS_KEY = os.getenv("PEXELS_API_KEY", "")

# -------------------------------------------------------
# الزوايا الثلاث لكل Short
# -------------------------------------------------------
_ANGLES = [
    {
        "label": "detail",
        "hook_template": "One detail in this case that nobody talks about…",
        "instruction": (
            "Write a 45-second Short script (exactly 110-130 words) about ONE shocking specific detail "
            "from this True Crime story that most people overlook. "
            "Structure:\n"
            "1. ONE shocking question (1 sentence, ends with '?')\n"
            "2. The jaw-dropping answer with real facts/numbers (4-5 sentences)\n"
            "3. CTA: 'The full story is on our channel. Watch it now.'\n\n"
            "Tone: dark, urgent, no fluff. Every word earns its place."
        ),
    },
    {
        "label": "twist",
        "hook_template": "The moment investigators realized everything was wrong…",
        "instruction": (
            "Write a 45-second Short script (exactly 110-130 words) about the KEY TWIST or revelation "
            "in this True Crime story — the moment when everything changed. "
            "Structure:\n"
            "1. ONE haunting setup sentence about what everyone believed\n"
            "2. 'Then investigators discovered…' — the shocking twist (4-5 sentences)\n"
            "3. CTA: 'The full case breakdown is on our channel. Don't miss it.'\n\n"
            "Tone: suspenseful, revelatory. Build dread then release it."
        ),
    },
    {
        "label": "question",
        "hook_template": "The question nobody has been able to answer for decades…",
        "instruction": (
            "Write a 45-second Short script (exactly 110-130 words) that poses the CENTRAL UNANSWERED "
            "QUESTION of this True Crime story and shows why it's impossible to answer. "
            "Structure:\n"
            "1. State the haunting question directly (1-2 sentences)\n"
            "2. Show 3 pieces of conflicting evidence that make it unsolvable (3-4 sentences)\n"
            "3. 'We dig into every piece of evidence on our channel. Watch the full story.'\n\n"
            "Tone: mysterious, haunting. Leave the viewer unable to look away."
        ),
    },
]


# -------------------------------------------------------
# 1. توليد سكريبت Short بـ GPT
# -------------------------------------------------------
def _generate_short_script(title: str, story_summary: str, angle: dict) -> str:
    """يولّد سكريبت Short مستقل (~120 كلمة) بزاوية محددة"""
    if MOCK_MODE:
        return (
            f"{angle['hook_template']} "
            "She traveled under 9 different names. Every label was cut from her clothes. "
            "Her fingerprints had been removed. She'd been carrying a coded diary "
            "that took 47 years to partially crack. "
            "And the three names inside it have never been made public. "
            "The full story is on our channel. Watch it now."
        )

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = f"""True Crime story: {title}

Summary context: {story_summary[:600]}

{angle['instruction']}

Return ONLY the script text — no labels, no quotes, no JSON. Plain narration text only."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=250,
    )
    return response.choices[0].message.content.strip()


# -------------------------------------------------------
# 2. TTS للـ Short
# -------------------------------------------------------
def _tts_short(text: str, output_path: str) -> bool:
    """يحوّل نص الـ Short إلى صوت MP3"""
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
            speed=1.05,  # أسرع قليلاً للـ Shorts
        )
        response.stream_to_file(output_path)
        return os.path.exists(output_path) and os.path.getsize(output_path) > 500
    except Exception as e:
        print(f"[shorts] ❌ TTS failed: {e}")
        return False


# -------------------------------------------------------
# 3. جلب فيديو Pexels عمودي للـ Short
# -------------------------------------------------------
_SHORT_QUERIES = {
    "detail":   ["dark mystery investigation portrait", "shadow person dramatic dark"],
    "twist":    ["crime scene dark discovery dramatic", "detective dark room"],
    "question": ["mystery dark fog dramatic", "unknown person shadow night"],
}


def _get_pexels_portrait_video(query: str) -> str | None:
    """يجلب فيديو عمودي أو مربع من Pexels ويحفظه مؤقتاً"""
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "per_page": 8, "orientation": "portrait"},
            timeout=10,
        )
        videos = r.json().get("videos", [])
        if not videos:
            # fallback إلى landscape
            r = requests.get(
                "https://api.pexels.com/videos/search",
                headers={"Authorization": PEXELS_KEY},
                params={"query": query, "per_page": 8, "orientation": "landscape"},
                timeout=10,
            )
            videos = r.json().get("videos", [])
        if not videos:
            return None

        video = random.choice(videos[:5])
        # أحسن دقة متاحة
        files = sorted(video.get("video_files", []),
                       key=lambda f: f.get("width", 0), reverse=True)
        url = next((f["link"] for f in files if f.get("width", 0) >= 480), None)
        if not url:
            return None

        tmp = tempfile.mktemp(suffix=".mp4")
        with requests.get(url, stream=True, timeout=30) as resp:
            with open(tmp, "wb") as f:
                for chunk in resp.iter_content(65536):
                    f.write(chunk)
        return tmp if os.path.getsize(tmp) > 5000 else None
    except Exception as e:
        print(f"[shorts] ⚠️ Pexels video fetch failed: {e}")
        return None


# -------------------------------------------------------
# 4. بناء الفيديو العمودي بـ ffmpeg
# -------------------------------------------------------
def _get_audio_duration(path: str) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    try:
        return float(result.stdout.strip())
    except Exception:
        return SHORT_DURATION


def _build_short_video(
    audio_path: str,
    script_text: str,
    angle_label: str,
    output_path: str,
) -> bool:
    """
    يبني فيديو Short عمودي 1080x1920:
    - لقطة Pexels عمودية كخلفية
    - درجة لونية سينمائية داكنة
    - نص الـ hook أعلى (كبير أصفر)
    - نص الـ CTA أسفل (أبيض)
    - شريط أحمر "#SHORTS / TRUE CRIME" أعلى
    """
    duration = _get_audio_duration(audio_path)
    if duration <= 0:
        duration = SHORT_DURATION

    # جلب فيديو خلفية
    queries = _SHORT_QUERIES.get(angle_label, _SHORT_QUERIES["detail"])
    raw_clip = None
    for q in queries:
        raw_clip = _get_pexels_portrait_video(q)
        if raw_clip:
            break

    with tempfile.TemporaryDirectory() as tmp:
        bg_path = os.path.join(tmp, "bg.mp4")

        if raw_clip and os.path.exists(raw_clip):
            # تحويل وتكبير لـ 1080x1920 + درجة لونية سينمائية
            vf = (
                f"scale={SHORT_W}:{SHORT_H}:force_original_aspect_ratio=increase,"
                f"crop={SHORT_W}:{SHORT_H},"
                f"curves=r='0/0 0.15/0.07 0.75/0.60 1/0.85':"
                f"g='0/0 0.15/0.09 0.75/0.58 1/0.82':"
                f"b='0/0.04 0.4/0.33 0.75/0.56 1/0.78',"
                f"fade=t=in:st=0:d=0.4"
            )
            subprocess.run(
                ["ffmpeg", "-y", "-stream_loop", "-1", "-i", raw_clip,
                 "-t", str(duration + 1),
                 "-vf", vf,
                 "-r", "30",
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
                 "-an", bg_path],
                capture_output=True,
            )
            try:
                os.remove(raw_clip)
            except Exception:
                pass
        else:
            # fallback — خلفية سوداء
            subprocess.run(
                ["ffmpeg", "-y",
                 "-f", "lavfi", "-i",
                 f"color=0x0A0A1E:size={SHORT_W}x{SHORT_H}:rate=30",
                 "-t", str(duration + 1),
                 "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
                 "-an", bg_path],
                capture_output=True,
            )

        if not os.path.exists(bg_path) or os.path.getsize(bg_path) < 1000:
            return False

        # استخراج جمل النص
        sentences = [s.strip() for s in script_text.replace("\n", " ").split(".") if len(s.strip()) > 10]
        hook_text  = sentences[0][:80] if sentences else "TRUE CRIME"
        cta_text   = sentences[-1][:80] if len(sentences) > 1 else "Watch the full story on our channel."

        def _esc(t):
            return (t.replace("\\", "\\\\").replace("'", "\\'")
                     .replace(":", "\\:").replace("[", "\\[")
                     .replace("]", "\\]").replace("%", "\\%"))

        hook_esc  = _esc(hook_text.upper())
        cta_esc   = _esc(cta_text)
        label_esc = _esc("▶  TRUE CRIME  #SHORTS")

        # طبقة نص كاملة
        drawtext = (
            # شريط أحمر أعلى
            f"drawbox=x=0:y=0:w={SHORT_W}:h=110:color=0x9A0000@0.92:t=fill,"
            f"drawbox=x=0:y=110:w={SHORT_W}:h=4:color=0xDD1E1E:t=fill,"
            # label
            f"drawtext=fontfile={FONT_PATH}:text='{label_esc}':"
            f"fontsize=52:fontcolor=white:x=(w-text_w)/2:y=22,"
            # hook كبير — أصفر — في الوسط
            f"drawbox=x=0:y={SHORT_H//2 - 200}:w={SHORT_W}:h=260:color=black@0.55:t=fill,"
            f"drawtext=fontfile={FONT_PATH}:text='{hook_esc}':"
            f"fontsize=70:fontcolor=0xFFDD22:x=(w-text_w)/2:y={SHORT_H//2 - 180}:"
            f"fontsize=70:line_spacing=12:wrap=1:fix_bounds=1,"
            # خط فاصل أحمر
            f"drawbox=x=80:y={SHORT_H - 320}:w={SHORT_W - 160}:h=4:color=0xDD1E1E:t=fill,"
            # CTA أسفل
            f"drawbox=x=0:y={SHORT_H - 300}:w={SHORT_W}:h=180:color=black@0.70:t=fill,"
            f"drawtext=fontfile={FONT_PATH}:text='{cta_esc}':"
            f"fontsize=48:fontcolor=white:x=(w-text_w)/2:y={SHORT_H - 290}:"
            f"line_spacing=10:wrap=1:fix_bounds=1"
        )

        final_path = os.path.join(tmp, "final.mp4")
        subprocess.run(
            ["ffmpeg", "-y",
             "-i", bg_path,
             "-i", audio_path,
             "-map", "0:v", "-map", "1:a",
             "-vf", drawtext,
             "-t", str(duration),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
             "-c:a", "aac", "-b:a", "128k",
             "-movflags", "+faststart", "-shortest",
             final_path],
            capture_output=True,
        )

        if os.path.exists(final_path) and os.path.getsize(final_path) > 5000:
            import shutil
            shutil.copy2(final_path, output_path)
            return True

    return False


# -------------------------------------------------------
# 5. الدالة الرئيسية — Public API
# -------------------------------------------------------
def generate_independent_shorts(
    title: str,
    script: str,
    num_shorts: int = 3,
) -> list[str]:
    """
    يولّد 3 Shorts مستقلة بمحتوى فريد:
      Short 1 — "detail"   : تفصيل صادم واحد لم ينتبه له أحد
      Short 2 — "twist"   : لحظة كشف النقيض
      Short 3 — "question": السؤال الذي لا جواب له

    يعيد قائمة بمسارات ملفات mp4.
    """
    os.makedirs(SHORTS_DIR, exist_ok=True)

    # ملخص مختصر من السكريبت (أول 800 حرف)
    story_summary = script[:800].strip()

    results = []
    angles = _ANGLES[:num_shorts]

    for i, angle in enumerate(angles):
        label = angle["label"]
        print(f"[shorts] 📱 إنتاج Short {i+1}/3 — زاوية: {label.upper()}")

        try:
            # أ. توليد السكريبت
            short_script = _generate_short_script(title, story_summary, angle)
            word_count = len(short_script.split())
            print(f"[shorts] ✏️ سكريبت: {word_count} كلمة")

            # ب. TTS
            audio_path = os.path.join(SHORTS_DIR, f"short_{i+1}_{label}_audio.mp3")
            if not _tts_short(short_script, audio_path):
                print(f"[shorts] ⚠️ TTS فشل للـ {label} — تخطي")
                continue

            # ج. بناء الفيديو
            out_path = os.path.join(SHORTS_DIR, f"short_{i+1}_{label}.mp4")
            success = _build_short_video(audio_path, short_script, label, out_path)

            if success:
                size_mb = round(os.path.getsize(out_path) / (1024 * 1024), 1)
                print(f"[shorts] ✅ Short {i+1} جاهز → {os.path.basename(out_path)} | {size_mb}MB")
                results.append(out_path)
            else:
                print(f"[shorts] ❌ فشل بناء Short {i+1} ({label})")

        except Exception as e:
            print(f"[shorts] ❌ خطأ في Short {i+1} ({label}): {e}")
            continue

    print(f"[shorts] 📱 {len(results)}/3 Shorts اكتملت بمحتوى مستقل")
    return results


# -------------------------------------------------------
# الدالة القديمة — نقطع من الفيديو الطويل (احتياطية فقط)
# -------------------------------------------------------
def extract_shorts(long_video_path: str, num_shorts: int = 3, duration: int = 60) -> list[str]:
    """
    محجوزة للاستخدام الاحتياطي فقط.
    استخدم generate_independent_shorts() بدلاً منها.
    """
    print("[shorts] ⚠️ extract_shorts() قديمة — استخدم generate_independent_shorts()")
    return []
