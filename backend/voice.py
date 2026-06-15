"""
voice.py — Text-to-Speech generation
TTS_ENGINE controls which engine is used:
  "openai"      — OpenAI TTS (default, uses existing OPENAI_API_KEY, voice=onyx)
  "elevenlabs"  — ElevenLabs (premium, needs ELEVENLABS_API_KEY)
  "gtts"        — gTTS free fallback (robotic)
"""

import os
import time
import logging

logger = logging.getLogger(__name__)

from config import (
    OPENAI_API_KEY,
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    TTS_ENGINE,
    OPENAI_TTS_VOICE,
)

OUTPUT_FILE = "voice.mp3"
_DEFAULT_ELEVENLABS_VOICE = "21m00Tcm4TlvDq8ikWAM"  # Rachel


# -------------------------------------------------------
# Engine 1 — OpenAI TTS
# -------------------------------------------------------

def text_to_speech_openai(text: str) -> str:
    """OpenAI TTS — deep, dramatic voice ideal for True Crime narration."""
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    # OpenAI TTS max 4096 chars per request — split if needed
    MAX_CHARS = 4000
    chunks = [text[i:i+MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]

    audio_parts = []
    for i, chunk in enumerate(chunks):
        response = client.audio.speech.create(
            model="tts-1-hd",
            voice=OPENAI_TTS_VOICE,
            input=chunk,
            speed=0.92,
        )
        part_file = f"voice_part_{i}.mp3"
        response.stream_to_file(part_file)
        audio_parts.append(part_file)

    if len(audio_parts) == 1:
        os.rename(audio_parts[0], OUTPUT_FILE)
    else:
        _merge_audio_parts(audio_parts, OUTPUT_FILE)

    return OUTPUT_FILE


def _merge_audio_parts(parts: list, output: str):
    """Merge multiple mp3 parts into one file using ffmpeg."""
    import subprocess
    list_file = "audio_parts.txt"
    with open(list_file, "w") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file, "-c", "copy", output],
        check=True, capture_output=True
    )
    for p in parts:
        try:
            os.remove(p)
        except Exception:
            pass
    try:
        os.remove(list_file)
    except Exception:
        pass


# -------------------------------------------------------
# Engine 2 — ElevenLabs
# -------------------------------------------------------

def text_to_speech_elevenlabs(text: str) -> str:
    """ElevenLabs TTS — premium quality."""
    import requests

    voice_id = ELEVENLABS_VOICE_ID or _DEFAULT_ELEVENLABS_VOICE
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
    }
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.50,
            "similarity_boost": 0.75,
            "style": 0.35,
            "use_speaker_boost": True,
        },
    }

    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()

    with open(OUTPUT_FILE, "wb") as f:
        f.write(response.content)

    return OUTPUT_FILE


# -------------------------------------------------------
# Engine 3 — gTTS (free fallback)
# -------------------------------------------------------

def text_to_speech_gtts(text: str) -> str:
    """gTTS free fallback — robotic but works offline."""
    from gtts import gTTS
    tts = gTTS(text)
    tts.save(OUTPUT_FILE)
    return OUTPUT_FILE


# -------------------------------------------------------
# Public API
# -------------------------------------------------------

def text_to_speech(text: str) -> str:
    """
    Main TTS function. Engine selected by TTS_ENGINE env var.
    Always falls back to gTTS if primary engine fails.

    TTS_ENGINE options:
      "openai"     — OpenAI tts-1-hd, voice=onyx (default)
      "elevenlabs" — ElevenLabs premium
      "gtts"       — free gTTS fallback
    """
    start = time.time()
    engine_used = "unknown"
    engine = TTS_ENGINE.lower()

    try:
        if engine == "openai":
            result = text_to_speech_openai(text)
            engine_used = f"openai/{OPENAI_TTS_VOICE}"

        elif engine == "elevenlabs" and ELEVENLABS_API_KEY:
            result = text_to_speech_elevenlabs(text)
            engine_used = "elevenlabs"

        else:
            result = text_to_speech_gtts(text)
            engine_used = "gtts"

    except Exception as e:
        print(f"[voice] {engine} failed: {e} — falling back to gTTS")
        logger.error("[voice] %s failed: %s — falling back to gTTS", engine, e)
        result = text_to_speech_gtts(text)
        engine_used = "gtts (fallback)"

    elapsed = round(time.time() - start, 2)
    size_kb = round(os.path.getsize(result) / 1024, 1) if os.path.exists(result) else 0

    print(f"[voice] engine={engine_used} | time={elapsed}s | size={size_kb}KB | file={result}")
    logger.info("[voice] engine=%s | time=%ss | size=%sKB | file=%s",
                engine_used, elapsed, size_kb, result)

    return result
