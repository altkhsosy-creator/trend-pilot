"""
short_generator.py — شورتات عربية مستقلة، مبنية على نفس قصة الفيديو الطويل
(مش قصة جديدة مستقلة، ومش قص عشوائي — كل شورت مبني على مرحلة محددة من outline.json)

3 شورتات لكل قصة:
  0. Hook Short   — من hook + promise (بداية القصة، ينتهي بسؤال معلّق)
  1. Plot Twist   — من turning_point (لحظة الانقلاب، مفهومة لحالها)
  2. Climax       — من climax (لحظة الكشف، بدون الحل الكامل)
"""
import os
import json
import tempfile
from openai import OpenAI

from config import OPENAI_API_KEY
from voice import text_to_speech
from video import (
    _ffmpeg_trim_clip, _ffmpeg_make_title_card, _get_audio_duration,
    _ffmpeg_make_color_clip, download_clip, get_stock_video_urls,
)
from subtitle_engine import generate_subtitles, write_srt, burn_subtitles
import subprocess

SHORT_W, SHORT_H = 1080, 1920  # عمودي 9:16
SHORT_SYSTEM_PROMPT = """أنت كاتب سيناريو محترف لقناة يوتيوب عربية بمجال الجرائم الحقيقية
(true crime) اسمها "المحقق شادو". تكتب الآن Short (فيديو قصير 45-55 ثانية) قائم بذاته."""

_SHORT_ROLES = [
    {
        "key": "hook",
        "label": "Hook",
        "source_fields": ["hook", "promise"],
        "instruction": (
            "اكتب سكربت Short عربي قائم بذاته (110-130 كلمة)، بناءً على المعلومات التالية فقط "
            "(بداية القصة):\n{source}\n\n"
            "يجب أن:\n"
            "1. يبدأ بجملة افتتاحية صادمة خاصة فيه (غير مأخوذة حرفياً من أي نص آخر)\n"
            "2. يبني تشويق سريع خلال 30-35 ثانية\n"
            "3. ينتهي بجملة تحويل واضحة نحو الفيديو الكامل، مثل: "
            "'باقي القصة الكاملة موجودة على القناة'"
        ),
    },
    {
        "key": "twist",
        "label": "Plot Twist",
        "source_fields": ["turning_point"],
        "instruction": (
            "اكتب سكربت Short عربي قائم بذاته (110-130 كلمة)، عن لحظة الانقلاب التالية بالقصة "
            "(يجب أن يُفهم بذاته دون الحاجة لمشاهدة الفيديو الكامل أولاً):\n{source}\n\n"
            "يجب أن:\n"
            "1. يبدأ بجملة افتتاحية صادمة خاصة فيه (غير مكررة)\n"
            "2. يشرح لحظة الانقلاب بوضوح ودراما\n"
            "3. ينتهي بجملة تحويل نحو الفيديو الكامل، مثل: "
            "'التفاصيل الكاملة لهاي القضية على القناة'"
        ),
    },
    {
        "key": "climax",
        "label": "Climax",
        "source_fields": ["climax"],
        "instruction": (
            "اكتب سكربت Short عربي قائم بذاته (110-130 كلمة)، عن لحظة الذروة/الكشف التالية "
            "(بدون كشف الحل الكامل أو النهاية):\n{source}\n\n"
            "يجب أن:\n"
            "1. يبدأ بجملة افتتاحية صادمة خاصة فيه (غير مكررة)\n"
            "2. يبني الذروة بدون إعطاء الحل الكامل\n"
            "3. ينتهي بجملة تحويل نحو الفيديو الكامل، مثل: "
            "'الفيديو الكامل بيوريكم شو صار فعلاً بالتفصيل'"
        ),
    },
]


def _build_short_script(role: dict, outline: dict) -> dict:
    """يستدعي GPT مرة وحدة خفيفة لصياغة مرحلة outline محددة كسكربت شورت مستقل ومصقول."""
    source = " ".join(outline.get(f, "") for f in role["source_fields"]).strip()
    if not source:
        source = "(لا توجد تفاصيل كافية — اكتب مقدمة عامة مشوّقة عن قضية جريمة غامضة)"

    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = role["instruction"].format(source=source) + (
        '\n\nأرجع JSON فقط: {"script": "السكربت الكامل 110-130 كلمة"}'
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SHORT_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.85,
    )
    return json.loads(response.choices[0].message.content)


def _create_vertical_video(audio_path: str, footage_dir: str, output: str, story_type: str = "default") -> str:
    """ينتج فيديو عمودي (1080x1920) من كليبات الـfootage المتاحة، بدون موسيقى خلفية."""
    total = _get_audio_duration(audio_path)
    if total <= 0:
        raise RuntimeError(f"[short] لم يُعثر على مدة الصوت: {audio_path}")

    footage_clips = []
    if footage_dir and os.path.isdir(footage_dir):
        footage_clips = sorted(
            os.path.join(footage_dir, f)
            for f in os.listdir(footage_dir)
            if f.lower().endswith(".mp4")
        )

    seg_dur = 6.0
    n_segments = max(1, round(total / seg_dur))
    seg_dur = round(total / n_segments, 3)

    with tempfile.TemporaryDirectory() as tmp:
        segment_files = []
        for idx in range(n_segments):
            raw_path = os.path.join(tmp, f"seg_{idx:02d}.mp4")
            used_video = False
            if footage_clips:
                clip = footage_clips[idx % len(footage_clips)]
                offset = (idx // len(footage_clips)) * seg_dur
                _ffmpeg_trim_clip(clip, raw_path, seg_dur, w=SHORT_W, h=SHORT_H,
                                  fade_in=0.2, fade_out=0.2, start_offset=offset)
                if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
                    used_video = True
            if not used_video:
                urls = get_stock_video_urls(story_type, n=2)
                for url in urls:
                    clip = download_clip(url, tmp)
                    if clip:
                        _ffmpeg_trim_clip(clip, raw_path, seg_dur, w=SHORT_W, h=SHORT_H,
                                          fade_in=0.2, fade_out=0.2)
                        if os.path.exists(raw_path) and os.path.getsize(raw_path) > 1000:
                            used_video = True
                            break
            if not used_video:
                _ffmpeg_make_color_clip(raw_path, seg_dur, w=SHORT_W, h=SHORT_H, color="0x0A0A1E")
            segment_files.append(raw_path)

        concat_list = os.path.join(tmp, "concat.txt")
        with open(concat_list, "w") as f:
            for sf in segment_files:
                f.write(f"file '{sf}'\n")

        raw_video = os.path.join(tmp, "raw_video.mp4")
        subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_list, "-c", "copy", raw_video],
            capture_output=True
        )
        subprocess.run(
            ["ffmpeg", "-y", "-i", raw_video, "-i", audio_path,
             "-map", "0:v", "-map", "1:a",
             "-t", str(total + 1),
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
             "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", "-shortest",
             output],
            capture_output=True
        )
    return output


def generate_independent_shorts(title: str, outline: dict, footage_dir: str, shorts_dir: str,
                                 num_shorts: int = 3) -> list[str]:
    """
    الدالة الرئيسية — تولّد 3 شورتات عربية مبنية على نفس outline القصة الأصلية
    (Hook / Plot Twist / Climax)، كل وحدة صوت + فيديو عمودي + ترجمة محروقة.
    ترجع قائمة مسارات ملفات الشورتات الناتجة.
    """
    os.makedirs(shorts_dir, exist_ok=True)
    outputs = []

    for i, role in enumerate(_SHORT_ROLES[:num_shorts]):
        print(f"[short] بناء Short {i} ({role['label']})...")
        try:
            data = _build_short_script(role, outline)
            script = data.get("script", "").strip()
            if not script:
                print(f"[short] ⚠️ Short {i} ({role['label']}): سكربت فارغ — تخطّي")
                continue

            audio = text_to_speech(script)

            raw_video_path = os.path.join(shorts_dir, f"short_{i}_raw.mp4")
            _create_vertical_video(audio, footage_dir, raw_video_path)

            aligned = generate_subtitles(audio, script)
            srt_path = os.path.join(shorts_dir, f"short_{i}.srt")
            write_srt(aligned, srt_path)

            final_path = os.path.join(shorts_dir, f"short_{i}.mp4")
            burn_subtitles(raw_video_path, srt_path, final_path)

            if os.path.exists(raw_video_path):
                os.remove(raw_video_path)

            outputs.append(final_path)
            print(f"[short] ✅ Short {i} ({role['label']}) جاهز: {final_path}")
        except Exception as e:
            print(f"[short] ❌ Short {i} ({role['label']}) فشل: {e}")

    return outputs
