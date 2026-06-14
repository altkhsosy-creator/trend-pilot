"""
get_youtube_token.py — تشغيل مرة واحدة فقط للحصول على refresh_token
شغّل هذا الملف يدوياً: python3 get_youtube_token.py
ثم انسخ الـ refresh_token وأضفه كـ secret باسم YOUTUBE_REFRESH_TOKEN
"""

import os
import re
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

REDIRECT_URI = "http://localhost:8080/"

client_config = {
    "installed": {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "redirect_uris": [REDIRECT_URI],
    }
}

flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
flow.redirect_uri = REDIRECT_URI

auth_url, _ = flow.authorization_url(
    access_type="offline",
    prompt="consent",
)

print("\n" + "="*60)
print("STEP 1: افتح هذا الرابط في المتصفح:")
print("="*60)
print(f"\n{auth_url}\n")
print("="*60)
print("STEP 2: سجّل الدخول واضغط Allow/Continue")
print("STEP 3: ستظهر صفحة خطأ 'refused to connect'")
print("         هذا طبيعي — انظر لشريط الرابط (URL bar)")
print("STEP 4: انسخ الـ URL كاملاً من شريط المتصفح")
print("         يبدأ بـ: http://localhost:8080/?code=...")
print("="*60 + "\n")

callback_url = input("الصق الـ URL كاملاً هنا: ").strip()

# استخراج الكود من الـ URL
match = re.search(r"[?&]code=([^&]+)", callback_url)
if not match:
    print("❌ لم يُعثر على code في الرابط — تأكد من نسخ الرابط كاملاً")
    exit(1)

code = match.group(1)
print(f"✅ Code extracted: {code[:20]}...")

flow.fetch_token(code=code)
creds = flow.credentials

print("\n" + "="*60)
print("✅ تم الحصول على refresh_token!")
print("="*60)
print(f"\nYOUTUBE_REFRESH_TOKEN:\n{creds.refresh_token}\n")
print("="*60)
print("أضفه كـ secret باسم: YOUTUBE_REFRESH_TOKEN")
print("="*60 + "\n")
