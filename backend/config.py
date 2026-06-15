import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY          = os.getenv("OPENAI_API_KEY")
TELEGRAM_BOT_TOKEN      = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID        = os.getenv("TELEGRAM_CHAT_ID")
PEXELS_API_KEY          = os.getenv("PEXELS_API_KEY")
ELEVENLABS_API_KEY      = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID     = os.getenv("ELEVENLABS_VOICE_ID", "")
MOCK_MODE               = os.getenv("MOCK_MODE",               "true").lower() == "true"
ENABLE_EMOTION_ENGINE   = os.getenv("ENABLE_EMOTION_ENGINE",   "true").lower()  == "true"
USE_ELEVENLABS          = os.getenv("USE_ELEVENLABS",          "false").lower() == "true"

# TTS_ENGINE: "openai" | "elevenlabs" | "gtts"
# openai   — best quality, uses OPENAI_API_KEY (already set), voice=onyx
# elevenlabs — premium, needs ELEVENLABS_API_KEY
# gtts     — free, robotic (fallback only)
TTS_ENGINE              = os.getenv("TTS_ENGINE", "openai")
OPENAI_TTS_VOICE        = os.getenv("OPENAI_TTS_VOICE", "onyx")   # onyx=deep/dramatic, nova=warm, alloy=neutral
