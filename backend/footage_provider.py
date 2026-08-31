"""
footage_provider.py — يجلب مقاطع فيديو من Pexels لكل مشهد بالسكربت
يُستخدم من weekly_planner.py

المدخل: قائمة استعلامات بحث بالإنجليزي (query لكل مشهد)
المخرج: قائمة ملفات فيديو محمّلة محلياً + تقرير نجاح/فشل
"""

import os
import requests

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"

# جودة الفيديو المفضّلة (الأصغر حجماً كفاية لفيديو عمودي/تركيب)
PREFERRED_HEIGHT_MIN = 720
PREFERRED_HEIGHT_MAX = 1920


def _pick_best_video_file(video_files: list[dict]) -> str | None:
    """يختار أفضل رابط تحميل من قائمة ملفات الفيديو اللي بترجعها Pexels."""
    candidates = [
        f for f in video_files
        if f.get("height") and PREFERRED_HEIGHT_MIN <= f["height"] <= PREFERRED_HEIGHT_MAX
        and f.get("file_type") == "video/mp4"
    ]
    if not candidates:
        candidates = [f for f in video_files if f.get("file_type") == "video/mp4"]
    if not candidates:
        return None
    candidates.sort(key=lambda f: f.get("height", 0))
    return candidates[0]["link"]


def search_clip(query: str) -> dict | None:
    """
    يبحث عن مقطع فيديو واحد بـ Pexels يطابق الاستعلام.
    بيرجع dict فيها: {"url": رابط التحميل, "query": الاستعلام, "pexels_id": ID}
    أو None لو ما لقى شي.
    """
    if not PEXELS_API_KEY:
        print("[footage] ❌ PEXELS_API_KEY غير موجود")
        return None

    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 5, "orientation": "portrait"}

    try:
        r = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=15)
        r.raise_for_status()
        videos = r.json().get("videos", [])
        if not videos:
            return None

        video = videos[0]
        link = _pick_best_video_file(video.get("video_files", []))
        if not link:
            return None

        return {"url": link, "query": query, "pexels_id": video.get("id")}

    except Exception as e:
        print(f"[footage] ⚠️ فشل البحث عن '{query}': {e}")
        return None


def download_clip(clip_info: dict, save_path: str) -> bool:
    """يحمّل مقطع الفيديو ويحفظه بالمسار المحدد."""
    try:
        r = requests.get(clip_info["url"], stream=True, timeout=60)
        r.raise_for_status()
        with open(save_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"[footage] ⚠️ فشل تحميل '{clip_info.get('query')}': {e}")
        return False


def get_footage_for_scenes(scene_queries: list[str], output_dir: str) -> list[str]:
    """
    الدالة الرئيسية — تستخدم من weekly_planner.py
    تاخد قائمة استعلامات (وحدة لكل مشهد)، وترجع قائمة أسماء الملفات المحمّلة
    (بنفس الترتيب). لو استعلام معيّن فشل، بتعيد استخدام آخر لقطة ناجحة (fallback)
    بدل ما توقف العملية.
    """
    os.makedirs(output_dir, exist_ok=True)
    # تنظيف الكليبات القديمة قبل التحميل — يمنع تراكم مشاهد من قصص سابقة
    # بنفس المجلد (كانت تسبب خلط مشاهد غير مرتبطة بالسرد الحالي)
    for _old in os.listdir(output_dir):
        if _old.lower().endswith(".mp4"):
            try:
                os.remove(os.path.join(output_dir, _old))
            except Exception:
                pass
    downloaded_files = []
    last_successful_clip = None

    for i, query in enumerate(scene_queries, start=1):
        scene_num = str(i).zfill(2)
        safe_query = "".join(c if c.isalnum() or c == " " else "" for c in query)
        safe_query = "_".join(safe_query.lower().split())[:40]
        filename = f"scene_{scene_num}_{safe_query}.mp4"
        save_path = os.path.join(output_dir, filename)

        clip_info = search_clip(query)

        if clip_info and download_clip(clip_info, save_path):
            downloaded_files.append(filename)
            last_successful_clip = save_path
            print(f"[footage] ✅ Scene {i}: {filename}")
        elif last_successful_clip:
            import shutil
            shutil.copy(last_successful_clip, save_path)
            downloaded_files.append(filename)
            print(f"[footage] ⚠️ Scene {i}: لا يوجد تطابق — أعيد استخدام آخر لقطة ({filename})")
        else:
            print(f"[footage] ❌ Scene {i}: فشل كلياً ولا توجد لقطة احتياطية بعد")

    print(f"[footage] Footage: {len(downloaded_files)}/{len(scene_queries)} clips ready")
    return downloaded_files
