"""
voice.py — Text-to-Speech generation
Supports ElevenLabs (primary) with automatic gTTS fallback.
Controlled by USE_ELEVENLABS in .env
"""

import os
import time
import logging

logger = logging.getLogger(__name__)

# -------------------------------------------------------
# Config
# -------------------------------------------------------

from config import (
    ELEVENLABS_API_KEY,
    ELEVENLABS_VOICE_ID,
    USE_ELEVENLABS,
)

OUTPUT_FILE = "voice.mp3"

# Default ElevenLabs voice — "Rachel" (documentary-friendly)
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"


# -------------------------------------------------------
# ElevenLabs
# -------------------------------------------------------

def text_to_speech_elevenlabs(text: str) -> str:
    """
    Generate speech via ElevenLabs API.
    Returns path to voice.mp3 on success.
    Raises on failure so the caller can fall back to gTTS.
    """
    import requests

    voice_id = ELEVENLABS_VOICE_ID or _DEFAULT_VOICE_ID
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
# gTTS fallback
# -------------------------------------------------------

def text_to_speech_gtts(text: str) -> str:
    """Generate speech via gTTS (fallback)."""
    from gtts import gTTS
    tts = gTTS(text)
    tts.save(OUTPUT_FILE)
    return OUTPUT_FILE


# -------------------------------------------------------
# Public API — used by scheduler.py
# -------------------------------------------------------

def text_to_speech(text: str) -> str:
    """
    Main TTS function. Routes to ElevenLabs or gTTS based on config.
    Always falls back to gTTS if ElevenLabs fails.
    Logs engine used, generation time, and output file size.
    """
    start = time.time()
    engine_used = "unknown"

    if USE_ELEVENLABS and ELEVENLABS_API_KEY:
        try:
            result = text_to_speech_elevenlabs(text)
            engine_used = "elevenlabs"
        except Exception as e:
            logger.error("[voice] ElevenLabs failed: %s — falling back to gTTS", e)
            print(f"[voice] ElevenLabs failed: {e} — falling back to gTTS")
            result = text_to_speech_gtts(text)
            engine_used = "gtts (fallback)"
    else:
        result = text_to_speech_gtts(text)
        engine_used = "gtts"

    elapsed = round(time.time() - start, 2)
    size_kb = round(os.path.getsize(result) / 1024, 1) if os.path.exists(result) else 0

    print(f"[voice] engine={engine_used} | time={elapsed}s | size={size_kb}KB | file={result}")
    logger.info(
        "[voice] engine=%s | time=%ss | size=%sKB | file=%s",
        engine_used, elapsed, size_kb, result,
    )

    return result
