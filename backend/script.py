import json
from openai import OpenAI
from config import OPENAI_API_KEY, MOCK_MODE
from viral_engine import get_viral_story
from hook_ai import detect_story_type, generate_hook
from retention_engine import insert_retention_hooks
from emotion_engine import optimize_for_narration

client = None


# --------------------------------------------------
# MOCK DATA — True Crime / Unsolved Mysteries style
# --------------------------------------------------

_MOCK_SCRIPT = """
The one detail the FBI missed… changed everything about this case.

In 1970, a woman was found dead in a remote valley in Norway. She was lying in a sleeping bag, surrounded by bottles of pills. Her face had been partially burned. Her fingerprints had been removed. And every label on every piece of clothing she was wearing had been cut out.

✨ Nobody knew who she was. ✨

Investigators called her the Isdal Woman — named after the Isdal Valley where her body was discovered. And for over fifty years, she remained one of the most puzzling unidentified cases in modern European history.

Here's what makes this case impossible to walk away from.

She hadn't just wandered into that valley. She had planned to be there. Investigators traced her movements across Europe — Belgium, Switzerland, Italy, Germany, Norway — using a network of fake identities and altered passports. She checked into hotels under at least nine different names.

✨ Nine. ✨

In one of her suitcases left at a train station, police found a coded diary. Rows of letters and numbers that no one could crack. For decades.

Now — before you assume this was just a sad story about a troubled woman — here's what the forensic evidence actually showed.

The pills found near her body? They weren't enough to kill her. The official cause of death listed phenobarbital poisoning combined with burns — but the fire didn't start until after she was already dying. Someone arranged the scene.

✨ This was not a suicide. ✨

In 2016, a Norwegian public broadcaster launched a full reinvestigation. Forensic scientists rebuilt her facial structure. Linguists analyzed her accent from witness interviews. Intelligence experts reviewed her travel patterns.

What they concluded was carefully worded — but unmistakable. The Isdal Woman had almost certainly been working as an intelligence operative during the Cold War. Her movements matched the travel patterns of known agents. Her use of coded communication and multiple identities was professional-grade tradecraft.

Someone killed her. And whoever killed her had the resources and the access to make sure she was never identified.

Here's the detail that the FBI — and most Western intelligence agencies — never fully addressed.

Her coded diary was finally partially decoded in 2017. And inside it, investigators found references to at least three other individuals — using the same cipher structure. None of those individuals have ever been publicly identified.

She knew people. People who are still unknown. People who may still be alive.

Stop and think about what that means. Somewhere, right now, there may be people who knew exactly who the Isdal Woman was — who she was working for, why she was killed, and who gave the order.

And they have never said a word.

The case remains officially open. Norwegian police have never closed it. Her identity has never been confirmed. The three names in the coded diary have never been released.

Here's the question I keep coming back to — and I don't have an answer for it:

If she was an intelligence operative, why would the agency she worked for allow her to remain unidentified for over fifty years? Why not quietly claim her? Why not give her a name, even a false one, and close the file?

Unless closing the file would reveal something worse than leaving it open.

The Isdal Woman is buried in a Catholic cemetery in Bergen, Norway. Her grave marker reads: Ukjent Kvinne. Unknown Woman.

She's been there for fifty-four years.

And we still don't know her name.
""".strip()

_MOCK_DESCRIPTION = """
In 1970, a woman was found dead in a Norwegian valley. Every label on her clothing had been cut out. Her fingerprints had been removed. She had traveled across Europe under nine different fake identities. And she left behind a coded diary that took nearly 50 years to partially crack.

This is the Isdal Woman — one of the most chilling unsolved mysteries in Cold War history.

🔔 Subscribe for true crime and unsolved mysteries every week.
👇 Drop a comment: Do you think she was a spy?

#truecrime #unsolvedmysteries #coldcase #isdal #coldwar #documentary #mystery #crimestory #investigation
""".strip()

_MOCK_TAGS = [
    "true crime", "unsolved mysteries", "cold case", "Isdal Woman", "Cold War spy",
    "unidentified woman", "forensic", "mystery", "documentary", "criminal investigation"
]


def _mock_content(topic: str) -> dict:
    return {
        "title": "She Was Found Dead With 9 Fake Identities — 54 Years Later, Nobody Knows Her Name",
        "script": _MOCK_SCRIPT,
        "description": _MOCK_DESCRIPTION,
        "tags": _MOCK_TAGS,
    }


# --------------------------------------------------
# generate_script — standalone, fetches own story
# --------------------------------------------------

def generate_script() -> str:
    if MOCK_MODE:
        print("[MOCK_MODE] Skipping OpenAI — returning mock True Crime script")
        return optimize_for_narration(insert_retention_hooks(_MOCK_SCRIPT))

    story = get_viral_story()
    story_type = detect_story_type(story['title'])
    hook = generate_hook(story['title'], story_type)

    prompt = f"""
You are a master True Crime storyteller in the style of MrBallen and Rotten Mango.

Start the script with EXACTLY this hook:

"{hook}"

Rules:
- Hook is first 10-15 seconds — it must stop the scroll immediately
- Then drop straight into the story with zero fluff
- Add dramatic pauses (…) before every major revelation
- Include emotional analysis — what was the victim feeling? What was the killer thinking?
- Add a cliffhanger every 90 seconds to maintain retention
- Add personal commentary: "Here's what gets me about this case…", "The detail I can't stop thinking about…"
- Length: 2200-2600 words (10-12 minutes of narration)
- End with an open question that haunts the viewer

Use this TRUE CRIME story as your source:
Title: {story['title']}

Structure:
1. Scroll-stopping hook (exact text above)
2. Setting the scene — who, where, when
3. The crime / disappearance / mystery unfolds
4. Investigation — what did authorities find?
5. The twist or revelation
6. Personal commentary and emotional analysis
7. Haunting closing question

Style: dark, serious, investigative. No humor. No clickbait. Real storytelling.
"""

    _client = OpenAI(api_key=OPENAI_API_KEY)
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_script = response.choices[0].message.content
    final_script = optimize_for_narration(insert_retention_hooks(raw_script))
    return final_script


# --------------------------------------------------
# _real_content — full package for the pipeline
# --------------------------------------------------

_SYSTEM_PROMPT = """You are a master True Crime storyteller.

Your style: MrBallen and Rotten Mango. Dark, serious, investigative. No fluff, no humor.

RULES:
- Every script starts with a scroll-stopping hook in the first 10 seconds
- Add dramatic pauses (…) before revelations
- Include emotional analysis and personal commentary
- Add a cliffhanger every 90 seconds
- Base everything on real documented events — no fiction
- Length: 10-12 minutes (2200-2600 words)
- End with a haunting open question

Script structure:
1. Scroll-stopping hook
2. Setting the scene
3. The crime / disappearance unfolds
4. Investigation and evidence
5. The twist or revelation
6. Personal commentary
7. Haunting closing question"""


def _real_content(topic: str) -> dict:
    user_prompt = f"""Use this TRUE CRIME story as your source:

Title: {topic}

CRITICAL REQUIREMENTS — do NOT skip any:
1. Script MUST be 2200-2600 words minimum. Count them. If shorter, expand with more detail.
2. Script MUST contain dramatic pauses (…) at least 15 times before key revelations.
3. Script MUST include personal commentary phrases like "Here's what gets me about this…", "I can't stop thinking about…", "The detail that haunts me…"
4. Script MUST end with a haunting open question in the LAST paragraph.
5. Add a cliffhanger or tension spike every 90 seconds of narration.
6. NEVER use filler phrases. Every sentence must either reveal information, build dread, or deepen mystery.

Return a JSON object with EXACTLY these fields:
{{
  "title": "YouTube title — max 100 chars, shocking hook, real name/date/place. NO clickbait. Dark, serious, investigative tone.",
  "script": "FULL 2200-2600 word True Crime script. All 7 parts required. No skipping.",
  "description": "YouTube description 150-250 words. Hook in first 2 lines. Story summary. Subscribe CTA. True crime hashtags.",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"]
}}

Return ONLY valid JSON — no markdown, no code fences, no extra text."""

    _client = OpenAI(api_key=OPENAI_API_KEY)

    for attempt in range(1, 4):  # حتى 3 محاولات
        print(f"[script] محاولة {attempt}/3 لتوليد السكريبت...")
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.85 + (attempt - 1) * 0.05,  # رفع الإبداع مع كل محاولة
        )

        result = json.loads(response.choices[0].message.content)
        script = result.get("script", "")
        words = len(script.split())

        if words >= 2000:
            if attempt > 1:
                print(f"[script] ✅ نجح في المحاولة {attempt} ({words:,} كلمة)")
            return result

        print(f"[script] ⚠️ محاولة {attempt}: السكريبت قصير ({words:,} كلمة) — إعادة المحاولة...")

    print(f"[script] ⚠️ انتهت المحاولات — يُستخدم آخر نتيجة")
    return result


# --------------------------------------------------
# Script Quality Checker
# --------------------------------------------------

def check_script_quality(script: str, title: str = "") -> dict:
    """يفحص جودة السكريبت ويطبع تقريراً مفصلاً"""
    words = len(script.split())
    chars = len(script)
    duration_min = round(words / 150, 1)  # متوسط 150 كلمة/دقيقة

    # فحص الأجزاء السبعة
    structure_checks = {
        "Hook":           any(w in script[:400] for w in ["…", "?", "one detail", "what if", "nobody", "here's"]),
        "Setting":        any(w in script.lower() for w in ["in ", "was found", "lived", "worked", "town", "city", "year"]),
        "Crime unfolds":  any(w in script.lower() for w in ["disappeared", "murdered", "killed", "found dead", "missing", "vanished"]),
        "Investigation":  any(w in script.lower() for w in ["police", "detective", "investigat", "evidence", "forensic", "autopsy"]),
        "Twist":          any(w in script.lower() for w in ["but", "however", "twist", "revealed", "discovered", "shocking"]),
        "Commentary":     any(p in script for p in ["gets me", "I keep", "can't stop", "Here's what", "think about"]),
        "Closing Q":      "?" in script[-300:],
    }

    # إحصاءات
    pauses = script.count("…")
    hooks_inserted = sum(1 for h in [
        "changed everything", "didn't end", "mystery deepens",
        "get really strange", "no one was prepared", "happened next"
    ] if h in script.lower())

    # تحديد المستوى
    score = sum(structure_checks.values())
    if words >= 2200 and score >= 6:
        level = "🟢 ممتاز"
    elif words >= 1800 and score >= 4:
        level = "🟡 جيد"
    else:
        level = "🔴 يحتاج تحسين"

    # طباعة التقرير
    print("\n" + "="*55)
    print(f"📋 تقرير جودة السكريبت — {level}")
    print("="*55)
    if title:
        print(f"📌 العنوان: {title[:70]}")
    print(f"📝 الكلمات  : {words:,}  (المطلوب: 2200-2600)")
    print(f"⏱️  المدة    : ~{duration_min} دقيقة  (المطلوب: 10-12)")
    print(f"⏸️  توقفات…  : {pauses}  (كلما زاد كلما أفضل)")
    print(f"🔗 hooks    : {hooks_inserted}  (كل 90 ثانية)")
    print("\n📐 البنية السبعية:")
    for part, ok in structure_checks.items():
        print(f"  {'✅' if ok else '❌'} {part}")
    print(f"\n🏆 النتيجة: {score}/7 أجزاء — {level}")
    print("="*55 + "\n")

    return {
        "words": words, "duration_min": duration_min,
        "score": score, "level": level,
        "pauses": pauses, "structure": structure_checks,
    }


# --------------------------------------------------
# Public API
# --------------------------------------------------

def generate_full_content(topic: str) -> dict:
    if MOCK_MODE:
        print(f"[MOCK_MODE] Skipping OpenAI — returning mock True Crime content for: {topic}")
        result = _mock_content(topic)
    else:
        result = _real_content(topic)

    check_script_quality(result["script"], result.get("title", ""))
    return result
