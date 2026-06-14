"""
thumbnail.py — مولّد Thumbnail احترافي بأسلوب True Crime
يولّد صورة 1280x720 لكل قصة مع:
  - خلفية Pexels مخصصة + تعتيم دراماتيكي
  - vignette داكن على الحواف
  - عنوان بخط BebasNeue كبير
  - شريط أحمر "TRUE CRIME" أعلى
  - تأثير ضوء أحمر خافت في الخلفية
"""

import os
import re
import textwrap
import requests
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
DARK_OVERLAY = (0,   0,   0,  170)   # شفافية الطبقة الداكنة


# -------------------------------------------------------
# 1. جلب صورة خلفية من Pexels
# -------------------------------------------------------
_FALLBACK_QUERIES = [
    "dark crime scene fog", "mystery dark alley", "abandoned building night",
    "crime investigation dark", "shadow mystery night",
]

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


def _fetch_pexels_image(query: str) -> Image.Image | None:
    if not PEXELS_KEY:
        return None
    try:
        r = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": PEXELS_KEY},
            params={"query": query, "per_page": 5, "orientation": "landscape"},
            timeout=10,
        )
        photos = r.json().get("photos", [])
        if not photos:
            return None
        url = photos[0]["src"]["large2x"]
        img_data = requests.get(url, timeout=15).content
        from io import BytesIO
        img = Image.open(BytesIO(img_data)).convert("RGB")
        return img
    except Exception as e:
        print(f"[thumbnail] Pexels fetch failed: {e}")
        return None


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

    # ── الخلفية ──────────────────────────────────────────
    query = _pexels_query(title)
    bg = _fetch_pexels_image(query)

    if bg is None:
        bg = Image.new("RGB", (W, H), (10, 10, 15))
    else:
        bg = _apply_cinematic_grade(bg)

    bg = _add_vignette(bg)
    bg = _add_red_glow(bg)
    bg = _add_noise(bg)

    canvas = bg.convert("RGBA")

    # ── طبقة شفافة داكنة فوق الصورة ──────────────────────
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 90))
    canvas = Image.alpha_composite(canvas, overlay)

    draw = ImageDraw.Draw(canvas)

    # ── شريط أحمر أعلى "TRUE CRIME" ──────────────────────
    bar_h = 68
    draw.rectangle([0, 0, W, bar_h], fill=(RED_DARK[0], RED_DARK[1], RED_DARK[2], 240))
    draw.rectangle([0, bar_h, W, bar_h + 3], fill=(RED[0], RED[1], RED[2], 255))

    font_label = _load_font(FONT_BEBAS, 48)
    label_text = "★  TRUE CRIME  ★"
    bbox = draw.textbbox((0, 0), label_text, font=font_label)
    lw = bbox[2] - bbox[0]
    draw.text(((W - lw) // 2, 10), label_text, font=font_label, fill=WHITE)

    # ── خط فاصل أحمر ──────────────────────────────────────
    draw.rectangle([60, H - 240, W - 60, H - 236], fill=RED)

    # ── العنوان الرئيسي ────────────────────────────────────
    font_title_big  = _load_font(FONT_BEBAS, 118)
    font_title_med  = _load_font(FONT_BEBAS, 96)
    font_title_sml  = _load_font(FONT_BEBAS, 78)

    lines = _wrap_title(title, max_chars=20)
    n = len(lines)
    font_t = font_title_big if n == 1 else (font_title_med if n == 2 else font_title_sml)

    line_h = draw.textbbox((0, 0), "A", font=font_t)[3] + 8
    total_text_h = line_h * n
    start_y = H - 240 - total_text_h - 20

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_t)
        lw = bbox[2] - bbox[0]
        x = (W - lw) // 2
        y = start_y + i * (line_h + 4)

        # ظل قوي
        for dx, dy in [(-5,-5),(5,-5),(-5,5),(5,5),(0,-6),(0,6),(-6,0),(6,0)]:
            draw.text((x + dx, y + dy), line, font=font_t, fill=(0, 0, 0, 255))

        # النص الأبيض مع تحديد الكلمة الأولى بلون أصفر/أحمر
        words = line.split()
        if i == 0 and len(words) >= 1:
            # رسم الكلمة الأولى بالأصفر والباقي بالأبيض
            cursor_x = x
            for wi, word in enumerate(words):
                color = YELLOW if wi == 0 else WHITE
                draw.text((cursor_x, y), word + " ", font=font_t, fill=color)
                wbox = draw.textbbox((0, 0), word + " ", font=font_t)
                cursor_x += wbox[2] - wbox[0]
        else:
            draw.text((x, y), line, font=font_t, fill=WHITE)

    # ── subtitle أو hook ──────────────────────────────────
    if subtitle:
        sub = subtitle[:60].upper()
        font_sub = _load_font(FONT_BEBAS, 46)
        bbox = draw.textbbox((0, 0), sub, font=font_sub)
        sw = bbox[2] - bbox[0]
        sx = (W - sw) // 2
        sy = H - 90
        _draw_outlined_text(draw, (sx, sy), sub, font_sub, YELLOW, BLACK, 3)

    # ── رقم "UNSOLVED" أو "SOLVED" badge ────────────────
    badge_font = _load_font(FONT_BEBAS, 36)
    badge_text = "UNSOLVED" if "unsolved" in title.lower() or "mystery" in title.lower() else "TRUE CRIME"
    badge_w = draw.textbbox((0, 0), badge_text, badge_font)[2]
    bx, by = 60, H - 80
    draw.rectangle([bx - 8, by - 4, bx + badge_w + 8, by + 42], fill=RED)
    draw.text((bx, by), badge_text, font=badge_font, fill=WHITE)

    # ── حفظ ───────────────────────────────────────────────
    final = canvas.convert("RGB")
    final.save(output_path, "JPEG", quality=96, optimize=True)
    size_kb = os.path.getsize(output_path) // 1024
    print(f"[thumbnail] ✅ {output_path} | {size_kb}KB")
    return output_path
