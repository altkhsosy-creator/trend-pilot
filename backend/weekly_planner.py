"""
weekly_planner.py — يخطط وينتج محتوى الأسبوع (3 أيام نشر) لقناة "المحقق شادو"
يُشغَّل عبر: python3 weekly_planner.py   (أو من الجدولة الأسبوعية بالسكجولر)
"""

import os
import re
import json
import random
from datetime import datetime, timedelta
from openai import OpenAI

from config import OPENAI_API_KEY
from viral_engine import fetch_stories
from footage_provider import get_footage_for_scenes

BASE = os.path.dirname(os.path.abspath(__file__))
WEEKLY_DIR = os.path.join(BASE, "weekly_content")
DATA_DIR = os.path.join(BASE, "data")
STORY_HISTORY_FILE = os.path.join(DATA_DIR, "story_history.json")

PUBLISH_DAYS = [d.strip().lower() for d in os.getenv("PUBLISH_DAYS", "monday,thursday,saturday").split(",")]

WORDS_PER_SECOND_AR = 2.5
SECS_PER_CLIP = 8
TARGET_WORDS_MIN = 500
TARGET_WORDS_MAX = 650

_WEEKDAY_INDEX = {"monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
                  "friday": 4, "saturday": 5, "sunday": 6}

STOPWORDS_AR = {
    'جريمة', 'جرائم', 'قتل', 'مقتل', 'قاتل', 'القاتل', 'ضحية', 'ضحايا',
    'شرطة', 'الشرطة', 'تحقيق', 'تحقيقات', 'محكمة', 'المحكمة', 'قضية',
    'اعتقال', 'اعتقل', 'متهم', 'المتهم', 'اتهام', 'جثة', 'الجثة', 'مصرع',
    'وفاة', 'وفاته', 'وفاتها', 'موت', 'مات', 'ماتت', 'اختفاء', 'مفقود',
    'مفقودة', 'هروب', 'هارب', 'سجن', 'السجن', 'عقوبة', 'حكم', 'اعدام',
    'انتحار', 'حادثة', 'حادث', 'عثور', 'العثور', 'كشف', 'كشفت', 'فاجعة',
    'مروعة', 'مروع', 'صادمة', 'صادم', 'مأساة', 'مأساوية', 'خطيرة',
    'خطير', 'غامضة', 'غامض', 'سرقة', 'اغتصاب', 'تعذيب', 'عنف', 'ضرب',
    'اصابة', 'مصاب', 'مصابة', 'بعد', 'قبل', 'خلال', 'التي', 'الذي',
    'حيث', 'عندما', 'كانت', 'كان', 'هذا', 'هذه', 'فيها', 'منها', 'عليها',
    'ادعت', 'ادعاء', 'كواليس', 'تفاصيل', 'بلاغ', 'سيدة', 'رجل', 'فتاة',
    'شاب', 'امرأة', 'طفل', 'طفلة',
}

STOPWORDS_EN = {
    'murder', 'murdered', 'murderer', 'killed', 'killing', 'killer',
    'victim', 'victims', 'police', 'suspect', 'suspects', 'arrest',
    'arrested', 'investigation', 'investigators', 'court', 'trial',
    'case', 'body', 'bodies', 'death', 'died', 'dead', 'missing',
    'disappeared', 'disappearance', 'prison', 'jail', 'sentence',
    'sentenced', 'convicted', 'guilty', 'crime', 'crimes', 'evidence',
    'scene', 'shot', 'stabbed', 'strangled', 'found', 'discovered',
    'confession', 'confessed', 'charged', 'charges', 'homicide',
    'shocking', 'mysterious', 'mystery', 'tragic', 'tragedy',
    'brutal', 'violent', 'attack', 'attacked', 'assault', 'after',
    'before', 'during', 'when', 'this', 'that', 'their', 'there',
    'were', 'been', 'from', 'with', 'about', 'have', 'says', 'said',
    'woman', 'women', 'girl', 'girls', 'child', 'children', 'family',
}
_SYSTEM_PROMPT = """أنت كاتب سيناريو محترف لقناة يوتيوب عربية بمجال الجرائم الحقيقية
(true crime) اسمها "المحقق شادو". أسلوبك متوتر، غامض، ومشوّق — تبني الحلقة
بحيث يبقى المشاهد "عالق" لآخر ثانية."""


def _build_user_prompt(topic: str, source_info: str = "") -> str:
    source_block = f"\nتفاصيل إضافية عن الخبر (استخدمها لبناء سرد غني ومفصّل، لا تقتصر على العنوان فقط):\n{source_info}\n" if source_info else ""
    return f"""استخدم هذا الخبر كمصدر للقصة:

العنوان الأصلي: {topic}
{source_block}

اكتب محتوى بالعربية الفصحى المبسطة (يفهمها كل الجمهور العربي)، بالتزام تام بما يلي:

## صيغة العنوان (title)
[شخص/حادثة محددة] + [تفصيل صادم برقم أو واقعة] + [سؤال أو جملة تطارد الذهن]
مثال: "اختفت لمدة 9 سنوات… ولما وجدوها، الشرطة رفضت تصديق قصتها"
يجب أن يحتوي رقم أو تاريخ أو تفصيل ملموس واحد على الأقل. الحد الأقصى 100 حرف.

## هيكلية السكربت (7 مراحل) — الطول الإجمالي {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX} كلمة بالضبط
1. **الهوك** (أول جملتين) — صادم ومباشر، بدون أي مقدمة أو ترحيب
2. **الوعد** — لمحة عن الصدمة القادمة بدون كشفها
3. **البداية الطبيعية** — تعريف الشخصية بحياة عادية (يبني تعاطف)
4. **نقطة الانقلاب** — الحدث المحوري (الجريمة/الاختفاء)
5. **التصعيد المتدرج** — الجزء الأطول، مع جملة "قطع نمط" صادمة أو سؤال بلاغي كل 20-30 ثانية كلام (كل ~70-90 كلمة) لإعادة شد الانتباه
6. **الذروة/الكشف**
7. **الخاتمة** — سؤال مفتوح يطارد الذهن + دعوة للاشتراك بجملة طبيعية غير مباشرة

## المشاهد المرئية (scene_queries)
قسّم نص السكربت إلى مشاهد متتالية بمعدل مشهد كل 15-20 كلمة تقريباً (بترتيب ظهورها
بالسكربت). لكل مشهد، أعطِ استعلام بحث بالإنجليزية (2-4 كلمات فقط، لوصف مشهد مرئي
عام يناسب الجو العام للجملة — مثال: "dark empty hallway", "police car night",
"woman crying window") يُستخدم للبحث عن لقطة فيديو مناسبة من مكتبة Pexels.
عدد عناصر scene_queries يجب أن يطابق تقريباً عدد المشاهد الفعلي (استنتجه من طول
السكربت، بمعدل مشهد كل 15-20 كلمة).

## المطلوب — أرجع JSON فقط بهذا الشكل بالضبط:
{{
  "title": "العنوان الرئيسي بالصيغة أعلاه",
  "script": "السكربت الكامل بالعربية، {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX} كلمة",
  "description": "وصف يوتيوب بالعربية 100-150 كلمة، مع هوك بالسطرين الأولين ودعوة للاشتراك وهاشتاقات مناسبة",
  "keywords": ["كلمة1", "كلمة2", "... 6-10 كلمات عربية مفتاحية مميزة بالقصة (أسماء، أماكن، تفاصيل محددة — تجنب الكلمات العامة بالنيتش)"],
  "scene_queries": ["query 1 بالإنجليزي", "query 2 بالإنجليزي", "..."]
}}

أرجع JSON صالح فقط — بدون أي نص إضافي أو علامات markdown."""


def _build_outline_prompt(topic: str, source_info: str = "") -> str:
    source_block = f"\nتفاصيل إضافية عن الخبر:\n{source_info}\n" if source_info else ""
    return f"""استخدم هذا الخبر كمصدر للقصة:
العنوان الأصلي: {topic}
{source_block}
اكتب مخطط تفصيلي (outline) بالعربية لسكربت قناة "المحقق شادو" (true crime)،
مقسّم لـ7 مراحل. لكل مرحلة، اكتب 3-5 جمل تلخص الأحداث والتفاصيل الملموسة
(أسماء، أماكن، أرقام، حوار متخيّل معقول) اللي بتنكشف فيها — هذا مخطط توجيهي
فقط، مو السكربت الكامل.

## المراحل المطلوبة:
1. hook — الهوك (صادم ومباشر)
2. promise — الوعد بالصدمة القادمة
3. normal — حياة الضحية/الشخصية الطبيعية قبل الحادثة
4. turning_point — نقطة الانقلاب (الجريمة/الاختفاء)
5. escalation — التصعيد المتدرج (المرحلة الأطول — اكتب 4-5 تفاصيل/أحداث فرعية متتالية مفصولة بـ" | ")
6. climax — الذروة والكشف
7. ending — الخاتمة وسؤال مفتوح

أرجع JSON فقط بهذا الشكل:
{{
  "title": "عنوان صادم بالعربية الفصحى فقط (بدون أي كلمة إنجليزية وبدون أقواس أو علامة +) — يحتوي شخص/حادثة محددة، تفصيل صادم برقم أو واقعة، وسؤال يطارد الذهن، مثال: اختفت لمدة 9 سنوات… ولما وجدوها رفضت الشرطة تصديق قصتها — حد أقصى 100 حرف",
  "hook": "...", "promise": "...", "normal": "...", "turning_point": "...",
  "escalation": "تفصيل1 | تفصيل2 | تفصيل3 | تفصيل4 | تفصيل5", "climax": "...", "ending": "..."
}}
أرجع JSON صالح فقط."""


def _build_expand_prompt(topic: str, outline: dict) -> str:
    return f"""بناءً على هذا المخطط، اكتب السكربت الكامل بالعربية الفصحى المبسطة
لقناة "المحقق شادو" — أسلوب متوتر، غامض، مشوّق:

العنوان: {outline.get("title", topic)}

المخطط (وسّع كل نقطة لفقرة كاملة بتفاصيل حسية وحوار وتشويق — بدون تلخيص):
1. الهوك: {outline.get("hook", "")}
2. الوعد: {outline.get("promise", "")}
3. البداية الطبيعية: {outline.get("normal", "")}
4. نقطة الانقلاب: {outline.get("turning_point", "")}
5. التصعيد المتدرج: {outline.get("escalation", "")}
6. الذروة والكشف: {outline.get("climax", "")}
7. الخاتمة: {outline.get("ending", "")}

## متطلبات إلزامية — لا تتجاهل أي منها:
1. السكربت يجب أن يكون {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX} كلمة على الأقل. عدّ الكلمات ووسّع كل مرحلة بما يكفي.
2. استخدم علامة "…" مباشرة داخل الجمل نفسها (8 مرات على الأقل) لخلق وقفات درامية طبيعية — مثال صحيح: "وكانت الشرفة... ملطخة بالدماء". ممنوع منعاً باتاً كتابة أي وصف نصي زي "(وقفة درامية)" أو "(pause)" أو أي كلمة توضيحية بين قوسين — هذا نص سيُقرأ بصوت عالٍ حرفياً، فقط علامة "…" وحدها مسموحة.
3. عبارات تعليق شخصي متكررة مثل "الشيء اللي بيصدمني بهالقصة…"، "ما بقدر أوقف تفكيري بـ…".
4. سؤال مفتوح يطارد الذهن بالفقرة الأخيرة.
5. نقطة تشويق أو تصعيد كل ~150 كلمة.
6. ممنوع الحشو — كل جملة تكشف معلومة أو تبني رعب أو تعمّق الغموض.
7. قسّم السكربت لمشاهد مرئية (scene_queries بالإنجليزي، 2-4 كلمات لكل مشهد، مشهد كل 15-20 كلمة تقريباً).

أرجع JSON فقط:
{{
  "title": "{outline.get("title", topic)}",
  "script": "السكربت الكامل، {TARGET_WORDS_MIN}-{TARGET_WORDS_MAX} كلمة، لا يقل عن ذلك",
  "description": "وصف يوتيوب 100-150 كلمة مع هوك وهاشتاقات",
  "keywords": ["6-10 كلمات عربية مفتاحية"],
  "scene_queries": ["query1 بالإنجليزي", "query2", "..."]
}}
أرجع JSON صالح فقط."""


def generate_arabic_content(topic: str, source_info: str = "") -> dict:
    client = OpenAI(api_key=OPENAI_API_KEY)

    # المرحلة 1: بناء مخطط (outline) للقصة
    print("[planner] بناء مخطط القصة (outline)...")
    outline_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_outline_prompt(topic, source_info)},
        ],
        response_format={"type": "json_object"},
        temperature=0.85,
    )
    outline = json.loads(outline_response.choices[0].message.content)

    # المرحلة 2: توسيع المخطط لسكربت كامل
    expand_prompt = _build_expand_prompt(topic, outline)
    result = None
    for attempt in range(1, 4):
        print(f"[planner] محاولة {attempt}/3 لتوسيع السكربت...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": expand_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.85 + (attempt - 1) * 0.05,
        )
        result = json.loads(response.choices[0].message.content)
        result["_outline"] = outline
        # طبقة حماية إضافية: حذف أي نص توضيحي بين قوسين قد يتسرب للسكربت
        # (زي "(وقفة درامية)") — هذا نص سيُقرأ بصوت عالٍ حرفياً لو بقي
        if "script" in result:
            result["script"] = re.sub(r"\([^)]{0,40}\)", "", result["script"]).strip()
            result["script"] = re.sub(r"\s{2,}", " ", result["script"])
        words = len(result.get("script", "").split())
        if words >= TARGET_WORDS_MIN - 150:
            if attempt > 1:
                print(f"[planner] ✅ نجح بالمحاولة {attempt} ({words} كلمة)")
            return result
        print(f"[planner] ⚠️ محاولة {attempt}: السكربت قصير ({words} كلمة) — إعادة المحاولة...")
    print("[planner] ⚠️ انتهت المحاولات — استخدام آخر نتيجة")
    return result


def _load_story_history() -> dict:
    if os.path.exists(STORY_HISTORY_FILE):
        try:
            return json.load(open(STORY_HISTORY_FILE, encoding="utf-8"))
        except Exception as e:
            print(f"[planner] تعذّرت قراءة story_history.json: {e}")
    return {"stories": []}


def _save_story_history(history: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(STORY_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def _is_published(title_en: str, published_keywords: set) -> bool:
    words = [w.lower() for w in re.findall(r"[A-Za-z]+", title_en) if len(w) > 3]
    matches = sum(1 for w in words if w in published_keywords)
    return matches >= 3


def _next_date_for_day(day_name: str) -> datetime:
    target = _WEEKDAY_INDEX[day_name]
    today = datetime.utcnow()
    delta = (target - today.weekday()) % 7
    return today + timedelta(days=delta)


def _calc_num_clips(script: str) -> int:
    word_count = len(script.split())
    duration_sec = word_count / WORDS_PER_SECOND_AR
    return max(8, round(duration_sec / SECS_PER_CLIP))


def plan_week():
    print(f"[planner] ===== Weekly planning started: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} =====")

    history = _load_story_history()
    published_keywords_en = set()
    for s in history.get("stories", []):
        for kw in s.get("keywords_en", []):
            if kw.lower() not in STOPWORDS_EN:
                published_keywords_en.add(kw.lower())

    print("[planner] Fetching stories...")
    stories = fetch_stories()

    unique_stories = []
    seen_titles = set()
    for story in stories:
        title = story.get("title", "")[:80]
        if title in seen_titles:
            continue
        if _is_published(story.get("title", ""), published_keywords_en):
            print(f"[planner] ⏭️ Skipping published: {title[:50]}")
            continue
        seen_titles.add(title)
        unique_stories.append(story)
        if len(unique_stories) == len(PUBLISH_DAYS):
            break

    print(f"[planner] ✅ Got {len(unique_stories)} stories")

    if not unique_stories:
        print("[planner] ❌ لا توجد قصص جديدة صالحة — إنهاء بدون إنشاء محتوى")
        return

    week_dir_date = _next_date_for_day(PUBLISH_DAYS[0])
    week_dir_name = f"week_{week_dir_date.strftime('%Y_%m_%d')}"
    week_dir = os.path.join(WEEKLY_DIR, week_dir_name)
    print(f"[planner] Week directory: {week_dir}")

    for i, story in enumerate(unique_stories):
        day_name = PUBLISH_DAYS[i]
        print(f"\n[planner] Processing Day {i+1} ({day_name})...")
        topic = story.get("title", "")
        story_description = story.get("description", "")
        story_content = story.get("content", "")
        source_info = "\n".join(filter(None, [story_description, story_content]))
        print(f"[planner] Story: {topic[:60]}...")

        content = generate_arabic_content(topic, source_info)
        outline = content.pop("_outline", {})
        ar_title = content.get("title", topic)
        script = content.get("script", "")
        description = content.get("description", "")
        keywords_ar = content.get("keywords", [])
        scene_queries = content.get("scene_queries", [])

        word_count = len(script.split())
        num_clips = _calc_num_clips(script)
        print(f"[planner] AR Title: {ar_title}")
        print(f"[planner] Script: {word_count} words")
        print(f"[planner] Dynamic clips: {num_clips} (based on {word_count} words)")

        if not scene_queries:
            scene_queries = ["dark mysterious atmosphere"] * num_clips
        elif len(scene_queries) < num_clips:
            while len(scene_queries) < num_clips:
                scene_queries.append(random.choice(scene_queries))
        elif len(scene_queries) > num_clips:
            scene_queries = scene_queries[:num_clips]

        day_dir = os.path.join(week_dir, f"day_{i+1}_{day_name}")
        os.makedirs(day_dir, exist_ok=True)

        with open(os.path.join(day_dir, "story.txt"), "w", encoding="utf-8") as f:
            f.write(f"{topic}\nSource: {story.get('url', '')}\n")
        with open(os.path.join(day_dir, "script.txt"), "w", encoding="utf-8") as f:
            f.write(f"{ar_title}\n\n{script}")
        with open(os.path.join(day_dir, "description.txt"), "w", encoding="utf-8") as f:
            f.write(description)
        with open(os.path.join(day_dir, "keywords.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(keywords_ar))
        with open(os.path.join(day_dir, "outline.json"), "w", encoding="utf-8") as f:
            json.dump(outline, f, ensure_ascii=False, indent=2)

        footage_dir = os.path.join(day_dir, "footage")
        get_footage_for_scenes(scene_queries, footage_dir)
        print(f"[planner] ✅ Day {i+1} ready")

        en_words = [w.lower() for w in re.findall(r"[A-Za-z]+", topic)
                    if len(w) > 3 and w.lower() not in STOPWORDS_EN]
        ar_words = [w for w in re.findall(r"[\u0600-\u06FF]+", ar_title)
                    if len(w) > 3 and w not in STOPWORDS_AR]
        history["stories"].append({
            "title_en": topic,
            "title_ar": ar_title,
            "keywords_en": en_words,
            "keywords_ar": ar_words,
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
        })

    _save_story_history(history)
    print("\n[planner] ===== Weekly planning complete! =====")
    print(f"[planner] Content saved to: {week_dir}")


if __name__ == "__main__":
    plan_week()
