"""
thumbnail.py — مولّد Thumbnail احترافي بأسلوب True Crime
تصميم معدّل لأقصى CTR:
  - وجه/شخصية درامية على اليسار (Pexels)
  - تدرج شفاف يربط الوجه بالخلفية
  - كلمة صادمة كبيرة جداً على اليمين (hook word)
  - العنوان الكامل أصغر تحتها
  - شريط "TRUE CRIME" أعلى
  - تأثيرات سينمائية داكنة
"""

import os
import re
import random
import requests
from io import BytesIO
from PIL import (
    Image, ImageDraw, ImageFont, ImageFilter,
    ImageEnhance, ImageOps
)

# -------------------------------------------------------
# الثوابت
# -------------------------------------------------------
W, H         = 1280, 720
PEXELS_KEY   = os.getenv("PEXELS_API_KEY", "")
OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "output", "thumbnails")

FONT_BEBAS   = os.path.join(os.path.dirname(__file__), "assets", "fonts", "BebasNeue.ttf")
FONT_BOLD    = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# ألوان
RED          = (220, 30,  30)
RED_DARK     = (160, 0,   0)
WHITE        = (255, 255, 255)
YELLOW       = (255, 220, 50)
BLACK        = (0,   0,   0)
DARK_OVERLAY = (0,   0,   0,  170)


# -------------------------------------------------------
# 1. جلب صورة خلفية من Pexels
# -------------------------------------------------------
_FALLBACK_QUERIES = [
    "dark crime scene fog", "mystery dark alley", "abandoned building night",
    "crime investigation dark", "shadow mystery night",
]

# استعلامات وجوه درامية حسب نوع القصة
_FACE_QUERIES = {
    "murder":      ["dramatic woman portrait dark shadow", "man dark dramatic portrait mystery"],
    "missing":     ["worried woman dark portrait dramatic", "missing person shadow dark"],
    "spy":         ["mysterious woman dark portrait spy", "shadow person dark dramatic"],
    "cold_case":   ["detective woman dark dramatic", "investigator shadow portrait"],
    "serial":      ["scared woman dark dramatic portrait", "horror shadow person dark"],
    "default":     ["dramatic person portrait dark mystery", "woman shadow dark dramatic mystery",
                    "man dark portrait dramatic thriller"],
}

# كلمات قوية لاستخراج الـ hook
_SHOCK_WORDS = {
    "dead", "killed", "murdered", "missing", "vanished", "disappeared",
    "fake", "unknown", "unsolved", "never", "secret", "exposed", "caught",
    "found", "buried", "identity", "identities", "years", "nobody", "alone",
    "survived", "escaped", "confessed", "sentenced", "executed",
}


def _pexels_query(title: str) -> str:
    t = title.lower()
    if any(w in t for w in ["zodiac", "cipher", "code", "mystery"]):
        return "dark cipher mystery night"
    if any(w in t for w in ["murder", "killer", "homicide", "victim"]):
        return "dark crime scene night moody"
    if any(w in t for w in ["disappear", "missing", "vanish"]):
        return "dark fog missing person forest"
    if any(w in t for w in ["cold case", "unsolved", "investigation"]):
        return "detective investigation dark room"
    if any(w in t for w in ["serial", "ripper", "bundy", "dahmer", "manson"]):
        return "dark criminal shadow horror"
    return "true crime dark mystery"


def _fetch_pexels_image(query: str, orientation: str = "landscape") -> Image.Image | None:
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "per_page": 8, "orientation": orientation},
            timeout=10,
        )
        photos = r.json().get("photos", [])
        if not photos:
            return None
        photo = random.choice(photos[:5])
        url = photo["src"]["large2x"]
        img_data = requests.get(url, timeout=15).content
        return Image.open(BytesIO(img_data)).convert("RGB")
    except Exception as e:
        print(f"[thumbnail] Pexels fetch failed: {e}")
        return None


def _fetch_face_image(story_type: str = "default") -> Image.Image | None:
    """يجلب صورة شخص/وجه درامي من Pexels حسب نوع القصة"""
    queries = _FACE_QUERIES.get(story_type, _FACE_QUERIES["default"])
    for query in queries:
        img = _fetch_pexels_image(query, orientation="portrait")
        if img:
            return img
    # fallback landscape
    return _fetch_pexels_image("dramatic person dark mystery portrait")


def _extract_hook_words(title: str) -> str:
    """
    يستخرج 2-3 كلمات صادمة من العنوان لعرضها كبيرة في الـ Thumbnail.
    مثال: "She Was Found Dead With 9 Fake Identities" → "9 FAKE IDENTITIES"
    """
    words = title.split()

    # ابحث عن رقم + الكلمة التالية
    for i, w in enumerate(words):
        if w.isdigit() and i + 1 < len(words):
            next_words = words[i+1: i+3]
            return (w + " " + " ".join(next_words)).upper()

    # ابحث عن كلمة صادمة + الكلمة التالية
    for i, w in enumerate(words):
        if w.lower().rstrip(".,!?") in _SHOCK_WORDS and i + 1 < len(words):
            return (w + " " + words[i+1]).upper().rstrip(".,!?")

    # fallback: أول كلمتين مؤثرتين
    clean = [w for w in words if len(w) > 3]
    return " ".join(clean[:2]).upper() if len(clean) >= 2 else title[:20].upper()


def _composite_face_left(bg: Image.Image, face: Image.Image) -> Image.Image:
    """
    يضع الوجه على الجانب الأيسر مع تدرج شفاف نحو اليمين.
    الوجه يشغل ~50% من العرض.
    """
    face_w = int(W * 0.52)
    face_h = H

    # قص الوجه للحجم المطلوب (portrait crop من المركز)
    fw, fh = face.size
    scale = max(face_w / fw, face_h / fh)
    new_fw, new_fh = int(fw * scale), int(fh * scale)
    face_resized = face.resize((new_fw, new_fh), Image.LANCZOS)
    # اقتصاص من المركز
    left = (new_fw - face_w) // 2
    top = max(0, new_fh - face_h)  # احتفظ بالوجه في الأعلى
    face_cropped = face_resized.crop((left, top, left + face_w, top + face_h))

    # تطبيق التعتيم الدرامي على الوجه
    face_dark = ImageEnhance.Brightness(face_cropped).enhance(0.55)
    face_dark = ImageEnhance.Contrast(face_dark).enhance(1.4)
    face_dark = ImageEnhance.Color(face_dark).enhance(0.6)

    # إنشاء gradient mask: أبيض على اليسار → شفاف على اليمين
    grad = Image.new("L", (face_w, face_h))
    for x in range(face_w):
        # قوي في اليسار، يتلاشى في آخر 35%
        fade_start = int(face_w * 0.60)
        if x <= fade_start:
            val = 255
        else:
            val = int(255 * (1 - (x - fade_start) / (face_w - fade_start)) ** 1.5)
        for y in range(face_h):
            grad.putpixel((x, y), val)

    # دمج الوجه مع الخلفية
    result = bg.copy().convert("RGBA")
    face_rgba = face_dark.convert("RGBA")
    face_rgba.putalpha(grad)
    result.paste(face_rgba, (0, 0), face_rgba)
    return result.convert("RGB")


# -------------------------------------------------------
# 2. تأثيرات الصورة
# -------------------------------------------------------
def _apply_cinematic_grade(img: Image.Image) -> Image.Image:
    """تعتيم دراماتيكي + تشبع لوني منخفض + حدة"""
    img = img.resize((W, H), Image.LANCZOS)
    img = ImageEnhance.Brightness(img).enhance(0.35)
    img = ImageEnhance.Contrast(img).enhance(1.6)
    img = ImageEnhance.Color(img).enhance(0.5)
    img = ImageEnhance.Sharpness(img).enhance(1.4)
    return img


def _add_vignette(img: Image.Image) -> Image.Image:
    """إطار داكن على الحواف يسحب النظر للمركز"""
    vignette = Image.new("L", (W, H), 0)
    draw = ImageDraw.Draw(vignette)
    for i in range(180):
        alpha = int(255 * (1 - (i / 180) ** 0.6))
        draw.rectangle([i, i, W - i, H - i], outline=alpha)
    vignette = vignette.filter(ImageFilter.GaussianBlur(radius=55))
    mask = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mask.putalpha(ImageOps.invert(vignette))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    result = Image.alpha_composite(img.convert("RGBA"), dark)
    mask2 = vignette
    blended = Image.composite(
        Image.new("RGB", (W, H), BLACK),
        img.convert("RGB"),
        mask2,
    )
    return blended


def _add_red_glow(img: Image.Image) -> Image.Image:
    """ضوء أحمر خافت ينبثق من المركز السفلي"""
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    cx, cy = W // 2, H + 100
    for r in range(420, 0, -15):
        alpha = int(55 * (1 - r / 420) ** 1.5)
        draw.ellipse(
            [cx - r * 2, cy - r, cx + r * 2, cy + r],
            fill=(180, 0, 0, alpha)
        )
    glow_blur = glow.filter(ImageFilter.GaussianBlur(radius=30))
    base = img.convert("RGBA")
    result = Image.alpha_composite(base, glow_blur)
    return result.convert("RGB")


def _add_noise(img: Image.Image) -> Image.Image:
    """حبيبات فيلمية خفيفة"""
    try:
        import numpy as np
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, 4, arr.shape)
        arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
        return Image.fromarray(arr)
    except ImportError:
        return img


# -------------------------------------------------------
# 3. رسم النص
# -------------------------------------------------------
def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(FONT_BOLD, size)


def _wrap_title(title: str, max_chars: int = 22) -> list[str]:
    """يقسم العنوان لسطرين أو ثلاثة"""
    words = title.upper().split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += (" " if current else "") + word
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def _draw_text_with_shadow(
    draw: ImageDraw.ImageDraw,
    pos: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    color: tuple,
    shadow_offset: int = 4,
    shadow_blur: bool = False,
):
    sx, sy = pos[0] + shadow_offset, pos[1] + shadow_offset
    draw.text((sx, sy), text, font=font, fill=(0, 0, 0, 200))
    draw.text(pos, text, font=font, fill=color)


def _draw_outlined_text(
    draw: ImageDraw.ImageDraw,
    pos: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
    outline: tuple = BLACK,
    outline_width: int = 4,
):
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)
    draw.text((x, y), text, font=font, fill=fill)


# -------------------------------------------------------
# 4. مولّد الـ Thumbnail الرئيسي
# -------------------------------------------------------
def create_thumbnail(
    title: str,
    output_path: str | None = None,
    subtitle: str = "",
    story_type: str = "true_crime",
) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    if not output_path:
        safe = re.sub(r"[^\w]", "_", title[:40]).lower()
        output_path = os.path.join(OUTPUT_DIR, f"thumb_{safe}.jpg")

    # ── 1. خلفية ─────────────────────────────────────────
    bg_query = _pexels_query(title)
    bg = _fetch_pexels_image(bg_query)
    if bg is None:
        bg = Image.new("RGB", (W, H), (8, 8, 14))
    else:
        bg = _apply_cinematic_grade(bg)
    bg = _add_vignette(bg)
    bg = _add_red_glow(bg)
    bg = _add_noise(bg)

    # ── 2. وجه/شخصية على اليسار ──────────────────────────
    face_type = "default"
    tl = title.lower()
    if any(w in tl for w in ["murder", "killer", "killed", "dead"]):
        face_type = "murder"
    elif any(w in tl for w in ["missing", "vanish", "disappear"]):
        face_type = "missing"
    elif any(w in tl for w in ["spy", "agent", "cia", "kgb", "identity"]):
        face_type = "spy"
    elif any(w in tl for w in ["serial", "ripper", "bundy"]):
        face_type = "serial"
    elif any(w in tl for w in ["cold case", "unsolved"]):
        face_type = "cold_case"

    face = _fetch_face_image(face_type)
    if face:
        bg = _composite_face_left(bg, face)
        print(f"[thumbnail] 👤 وجه درامي أُضيف ({face_type})")
    else:
        print("[thumbnail] ⚠️ لم يُعثر على وجه — تصميم نص فقط")

    canvas = bg.convert("RGBA")

    # طبقة داكنة شفافة على اليمين لإبراز النص
    right_overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rod = ImageDraw.Draw(right_overlay)
    right_x = int(W * 0.45)
    for x in range(right_x, W):
        alpha = int(180 * ((x - right_x) / (W - right_x)) ** 0.6)
        rod.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
    canvas = Image.alpha_composite(canvas, right_overlay)

    draw = ImageDraw.Draw(canvas)

    # ── 3. شريط "TRUE CRIME" أعلى ────────────────────────
    bar_h = 68
    draw.rectangle([0, 0, W, bar_h], fill=(RED_DARK[0], RED_DARK[1], RED_DARK[2], 245))
    draw.rectangle([0, bar_h, W, bar_h + 3], fill=(RED[0], RED[1], RED[2], 255))
    font_label = _load_font(FONT_BEBAS, 48)
    label_text = "★  TRUE CRIME  ★"
    lb = draw.textbbox((0, 0), label_text, font=font_label)
    draw.text(((W - lb[2]) // 2, 10), label_text, font=font_label, fill=WHITE)

    # ── 4. الكلمة الصادمة الكبيرة (hook word) ────────────
    hook = _extract_hook_words(title)
    hook_words = hook.split()
    RIGHT_X = int(W * 0.50)   # بداية منطقة النص على اليمين
    RIGHT_W = W - RIGHT_X - 30  # عرض المنطقة

    # اختر حجم خط يناسب الكلمة
    font_hook = _load_font(FONT_BEBAS, 130)
    for size in [130, 110, 92, 76]:
        font_hook = _load_font(FONT_BEBAS, size)
        max_w = max(draw.textbbox((0, 0), w, font=font_hook)[2] for w in hook_words)
        if max_w <= RIGHT_W:
            break

    hook_line_h = draw.textbbox((0, 0), "A", font=font_hook)[3] + 6
    hook_total_h = hook_line_h * len(hook_words)
    hook_start_y = bar_h + int((H - bar_h - hook_total_h) * 0.30)

    for i, hw in enumerate(hook_words):
        hb = draw.textbbox((0, 0), hw, font=font_hook)
        hx = RIGHT_X + (RIGHT_W - hb[2]) // 2
        hy = hook_start_y + i * hook_line_h
        # ظل قوي
        for dx, dy in [(-4,-4),(4,-4),(-4,4),(4,4),(0,-5),(0,5),(-5,0),(5,0)]:
            draw.text((hx+dx, hy+dy), hw, font=font_hook, fill=(0,0,0,255))
        # الكلمة الأولى بالأصفر، الباقي بالأبيض
        color = YELLOW if i == 0 else WHITE
        draw.text((hx, hy), hw, font=font_hook, fill=color)

    # خط أحمر فاصل
    sep_y = hook_start_y + hook_total_h + 14
    draw.rectangle([RIGHT_X + 10, sep_y, W - 30, sep_y + 3], fill=RED)

    # ── 5. العنوان الكامل (أصغر، تحت الكلمة الصادمة) ────
    font_title = _load_font(FONT_BEBAS, 52)
    title_lines = _wrap_title(title, max_chars=24)
    title_line_h = draw.textbbox((0, 0), "A", font=font_title)[3] + 4
    ty = sep_y + 16
    for line in title_lines:
        tb = draw.textbbox((0, 0), line, font=font_title)
        tx = RIGHT_X + (RIGHT_W - tb[2]) // 2
        for dx, dy in [(-3,-3),(3,-3),(-3,3),(3,3)]:
            draw.text((tx+dx, ty+dy), line, font=font_title, fill=(0,0,0,220))
        draw.text((tx, ty), line, font=font_title, fill=WHITE)
        ty += title_line_h

    # ── 6. Badge أسفل اليمين ─────────────────────────────
    badge_text = "UNSOLVED" if any(w in tl for w in ["unsolved", "mystery", "unknown", "nobody"]) else "COLD CASE"
    font_badge = _load_font(FONT_BEBAS, 34)
    bb = draw.textbbox((0, 0), badge_text, font=font_badge)
    bx = RIGHT_X + 10
    by = H - 72
    draw.rectangle([bx - 6, by - 4, bx + bb[2] + 6, by + bb[3] + 4], fill=RED)
    draw.text((bx, by), badge_text, font=font_badge, fill=WHITE)

    # ── 7. حفظ ───────────────────────────────────────────
    final = canvas.convert("RGB")
    final.save(output_path, "JPEG", quality=96, optimize=True)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"[thumbnail] ✅ {output_path} | {size_kb}KB")
    return output_path
