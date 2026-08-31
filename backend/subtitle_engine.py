"""
subtitle_engine.py — ترجمة نصية متزامنة (subtitles) للفيديو
يجمع بين:
- توقيت Whisper الدقيق (مبني على الصوت الفعلي)
- نص السكربت الأصلي المضمون الصحة (بدل نص Whisper المسموع، لتفادي أخطاء الأرقام/الأسماء)
"""
import os
import subprocess
import whisper

_model = None


def _get_model():
    global _model
    if _model is None:
        print("[subtitle] Loading Whisper model (small)...")
        _model = whisper.load_model("small")
    return _model


def _get_whisper_segments(audio_path: str) -> list:
    """يرجع توقيت Whisper فقط (start, end, عدد كلمات لكل مقطع) — بدون الاعتماد على نصه"""
    model = _get_model()
    print("[subtitle] استخراج توقيت الصوت (Whisper)...")
    result = model.transcribe(audio_path, language="ar", task="transcribe")
    segments = []
    for seg in result["segments"]:
        word_count = len(seg["text"].split())
        segments.append({
            "start": seg["start"],
            "end": seg["end"],
            "word_count": max(word_count, 1),
        })
    print(f"[subtitle] {len(segments)} مقطع زمني")
    return segments


def _distribute_script_over_segments(script: str, segments: list) -> list:
    """يوزع نص السكربت الأصلي الصحيح على توقيت Whisper، بالتناسب مع كل مقطع"""
    words = script.split()
    total_weight = sum(s["word_count"] for s in segments) or 1
    total_words = len(words)

    result = []
    idx = 0
    for i, seg in enumerate(segments):
        if i == len(segments) - 1:
            chunk_words = words[idx:]
        else:
            n = max(1, round(total_words * (seg["word_count"] / total_weight)))
            chunk_words = words[idx:idx + n]
            idx += n
        if chunk_words:
            result.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": " ".join(chunk_words),
            })
    return result


def generate_subtitles(audio_path: str, script: str) -> list:
    """
    الدالة الرئيسية — تُرجع قائمة {"start","end","text"} تجمع توقيت Whisper
    الدقيق مع نص السكربت الأصلي المضمون الصحة.
    """
    segments = _get_whisper_segments(audio_path)
    return _distribute_script_over_segments(script, segments)


def _fmt_srt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = t % 60
    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")


def write_srt(aligned_segments: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as f:
        for i, seg in enumerate(aligned_segments, start=1):
            f.write(f"{i}\n")
            f.write(f"{_fmt_srt_time(seg['start'])} --> {_fmt_srt_time(seg['end'])}\n")
            f.write(f"{seg['text']}\n\n")


def burn_subtitles(video_path: str, srt_path: str, output_path: str) -> str:
    """يحرق الترجمة على الفيديو عبر ffmpeg — نص أبيض بحافة سوداء، أسفل الفيديو"""
    abs_srt = os.path.abspath(srt_path)
    escaped_srt = abs_srt.replace("\\", "/").replace(":", "\\:")
    style = (
        "FontName=DejaVu Sans Bold,FontSize=14,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=1,"
        "Alignment=2,MarginV=60"
    )
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", video_path,
         "-vf", f"subtitles={escaped_srt}:force_style='{style}'",
         "-c:a", "copy",
         output_path],
        capture_output=True
    )
    if result.returncode != 0 or not os.path.exists(output_path):
        print(f"[subtitle] ⚠️ فشل حرق الترجمة: {result.stderr[-500:]}")
        return video_path
    return output_path
