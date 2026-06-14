"""
get_youtube_token.py — تشغيل مرة واحدة فقط للحصول على refresh_token
شغّل هذا الملف يدوياً: python3 get_youtube_token.py
ثم انسخ الـ refresh_token وأضفه كـ secret باسم YOUTUBE_REFRESH_TOKEN
"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

CLIENT_ID     = os.getenv("YOUTUBE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")

if not CLIENT_ID or not CLIENT_SECRET:
    print("❌ Missing YOUTUBE_CLIENT_ID or YOUTUBE_CLIENT_SECRET in secrets!")
    exit(1)

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"

auth_url, _ = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    include_granted_scopes="true",
)

print("\n" + "="*60)
print("STEP 1: افتح هذا الرابط في المتصفح:")
print("="*60)
print(f"\n{auth_url}\n")
print("="*60)
print("STEP 2: سجّل الدخول بحساب YouTube القناة")
print("STEP 3: انسخ الكود الذي يظهر بعد الموافقة")
print("="*60 + "\n")

code = input("الصق الكود هنا: ").strip()

flow.fetch_token(code=code)
creds = flow.credentials

print("\n" + "="*60)
print("✅ تم الحصول على التوكن!")
print("="*60)
print(f"\nYOUTUBE_REFRESH_TOKEN:\n{creds.refresh_token}\n")
print("="*60)
print("أضف هذا الـ refresh_token كـ secret باسم: YOUTUBE_REFRESH_TOKEN")
print("="*60 + "\n")
