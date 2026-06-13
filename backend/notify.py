import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def _post(payload: dict):
    """Internal helper — sends a message to Telegram."""
    if not TELEGRAM_BOT_TOKEN:
        print("[notify] No TELEGRAM_BOT_TOKEN found")
        return None
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, json=payload, timeout=10)
        return response
    except Exception as e:
        print(f"[notify] Error: {e}")
        return None


def send_notification(message: str):
    """Send a plain text notification to Telegram."""
    _post({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    })


def send_approval_request(video_type: str, video_name: str, scheduled_time: str):
    """Send an approval request with inline ✅/❌ buttons."""
    keyboard = {
        "inline_keyboard": [[
            {"text": "✅ Publish", "callback_data": f"approve_{video_type}_{video_name}"},
            {"text": "❌ Skip",   "callback_data": f"reject_{video_type}_{video_name}"},
        ]]
    }
    _post({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": (
            f"📺 *Publication Request*\n\n"
            f"Type: `{video_type}`\n"
            f"File: `{video_name}`\n"
            f"Scheduled: `{scheduled_time}`"
        ),
        "parse_mode": "Markdown",
        "reply_markup": keyboard,
    })


def send_content_package_notification(
    story_title: str,
    long_video_path: str,
    shorts_paths: list[str],
):
    """
    Sends a rich Telegram notification with:
    - Story title
    - Long video preview info
    - Links / names of all Shorts
    """
    short_lines = ""
    for i, path in enumerate(shorts_paths, 1):
        name = os.path.basename(path)
        label = ["🪝 Hook", "🌀 Plot Twist", "🔥 Climax"][i - 1] if i <= 3 else f"Short {i}"
        short_lines += f"  {label}: `{name}`\n"

    long_name = os.path.basename(long_video_path) if long_video_path else "N/A"

    message = (
        f"🎬 *New True Crime Video Ready*\n\n"
        f"📖 *Story:* {story_title}\n\n"
        f"🎥 *Long Video:* `{long_name}`\n\n"
        f"✂️ *Shorts ({len(shorts_paths)}):*\n"
        f"{short_lines}\n"
        f"⏰ Scheduled for publishing today."
    )

    _post({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    })
    print(f"[notify] Content package notification sent — {len(shorts_paths)} shorts")


def handle_callback(callback_data: str) -> str:
    """Process inline button responses (approve/reject)."""
    if callback_data.startswith("approve_"):
        send_notification(f"✅ Approved for publishing: `{callback_data}`")
        return "approved"
    elif callback_data.startswith("reject_"):
        send_notification(f"❌ Skipped: `{callback_data}`")
        return "rejected"
    return "unknown"
