"""
youtube_upload.py — رفع الفيديوهات تلقائياً على YouTube
يستخدم refresh_token مخزّن كـ secret لتجنب تسجيل الدخول كل مرة
"""

import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# -------------------------------------------------------
# Credentials من environment secrets
# -------------------------------------------------------
YT_CLIENT_ID      = os.getenv("YOUTUBE_CLIENT_ID", "")
YT_CLIENT_SECRET  = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YT_REFRESH_TOKEN  = os.getenv("YOUTUBE_REFRESH_TOKEN", "")

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]


def _get_youtube_client():
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        raise ValueError(
            "[youtube] Missing credentials — set YOUTUBE_CLIENT_ID, "
            "YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN in secrets"
        )

    creds = Credentials(
        token=None,
        refresh_token=YT_REFRESH_TOKEN,
        client_id=YT_CLIENT_ID,
        client_secret=YT_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    creds.refresh(Request())
    return build("youtube", "v3", credentials=creds, cache_discovery=False)


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
    category_id: str = "25",
    privacy: str = "public",
    made_for_kids: bool = False,
) -> str:
    """
    يرفع الفيديو على YouTube ويعيد video_id
    category_id=25 → News & Politics | 27 → Education
    privacy: public / unlisted / private
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"[youtube] Video not found: {video_path}")

    youtube = _get_youtube_client()

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:500],
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "madeForKids": made_for_kids,
            "selfDeclaredMadeForKids": made_for_kids,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,
    )

    print(f"[youtube] Uploading: {title[:60]}...")
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"[youtube] Upload progress: {pct}%")

    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"[youtube] ✅ Uploaded! {url}")
    return video_id


def upload_short(
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] | None = None,
) -> str:
    """
    يرفع Short — نفس upload_video لكن بعنوان يحتوي #Shorts
    """
    short_title = title[:90] + " #Shorts"
    short_desc = description + "\n\n#Shorts #TrueCrime #UnsolvedMysteries"
    return upload_video(
        video_path=video_path,
        title=short_title,
        description=short_desc,
        tags=(tags or []) + ["Shorts", "TrueCrime", "UnsolvedMysteries"],
        privacy="public",
    )


def generate_description(title: str, script: str, tags: list[str]) -> str:
    """يولّد وصفاً احترافياً للفيديو"""
    hook = script[:300].strip()
    tags_str = " ".join(f"#{t.replace(' ', '')}" for t in tags[:15])
    return f"""{hook}...

━━━━━━━━━━━━━━━━━━━━━━
🔔 Subscribe for daily True Crime stories
👍 Like if this story shocked you
💬 Comment your theory below
━━━━━━━━━━━━━━━━━━━━━━

{tags_str}

#TrueCrime #UnsolvedMysteries #ColdCase #Mystery #CriminalMinds #TrueCrimeDaily"""
