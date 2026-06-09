import json
from openai import OpenAI
from config import OPENAI_API_KEY, MOCK_MODE
from viral_engine import get_viral_story
from hook_engine import detect_story_type, generate_hook

client = OpenAI(api_key=OPENAI_API_KEY)


# --------------------------------------------------
# MOCK DATA — real-event / Reddit-mystery style
# --------------------------------------------------

_MOCK_SCRIPT = """
In 2003, a 37-year-old man in Columbus, Ohio woke up one morning convinced he was 26.

He didn't recognize the woman sleeping next to him. He didn't recognize his own house. And when he looked in the mirror, he saw the face of a stranger — older, tired, worn in ways he couldn't explain.

His name was Gary. And the last thing he remembered was a Tuesday in 1992.

Here's what makes this story impossible to ignore: Gary didn't have amnesia the way movies describe it. He wasn't in a coma. He hadn't been in an accident. He had simply been living — working, eating, raising two kids — for eleven years — with no memory of any of it.

His wife told investigators he had seemed completely normal the entire time. Paid the bills. Showed up to work. Came home. Said "I love you" before bed.

But Gary remembered none of it.

Now — before you write this off as a fake — here's what the doctors found. And this is the part that will stick with you long after this video ends.

When they ran brain scans, there was no tumor. No stroke damage. No physical explanation whatsoever. What they found instead was a pattern of neural activity that one neurologist described as — and I'm quoting directly here — "like watching two different people living in the same brain, taking turns."

Gary was eventually diagnosed with a dissociative fugue state — a real, documented condition where the brain essentially creates a second operating self. The terrifying part? The doctors told him it could happen again at any time.

He could go to bed tonight as himself — and wake up as someone else.

Stop for a second and think about what that means. Every decision you made today, every memory you're building right now — what if none of it is guaranteed to stay with you?

Gary spent years trying to piece together the decade he lost. He talked to coworkers who remembered him laughing at lunch. Friends who said he seemed completely fine. His daughter, who was two years old in 1992 and thirteen when he "woke up," tried to explain to her father who she was — and watched him cry, not from sadness, but from the complete absence of recognition.

There's a detail that Gary shared in a 2006 interview that I can't stop thinking about. During those eleven years — the years he has no memory of — he apparently kept a journal. Dozens of notebooks filled with daily entries.

He read them after. Every single page.

He said it felt like reading about a stranger who happened to have his name.

Here's the question that no one has been able to answer — not the neurologists, not the psychologists, not Gary himself: if a version of you lived for eleven years, made decisions, built relationships, raised children — and then simply stopped existing — was that person you?

And if it wasn't you — then who was it?

Gary's case was never fully explained. There are three other documented cases with almost identical patterns from the same decade. Researchers at two separate universities have been quietly studying them. As of the last update in late 2022, they still don't have an answer.

The journals Gary kept are sitting in a storage unit in Ohio. He has never gone back to read them a second time.

He says he's afraid of what he might find.
""".strip()

_MOCK_DESCRIPTION = """
In 2003, a man in Ohio woke up believing he was 26 — but he was actually 37. Eleven years of his life were simply gone. His wife had no idea. His kids had grown up around him. And doctors found something in his brain scans that they still can't explain.

This video dives into one of the most disturbing documented cases of dissociative fugue on record — a real condition, with real victims, and zero answers.

What happens when your brain builds an entirely different version of you — and lets it live your life while you're gone?

🔔 Subscribe for real stories that are stranger than fiction.
👇 Comment below: Would you want to read the journals?

#truemystery #psychology #unsolved #reddit #realstory #brainscience #dissociation #viral #mindblowing #documentary
""".strip()

_MOCK_TAGS = [
    "true mystery", "unsolved cases", "real story", "psychology facts",
    "dissociative fugue", "reddit mystery", "mind blowing", "true crime adjacent",
    "viral story", "documentary"
]


def _mock_content(topic: str) -> dict:
    return {
        "title": "He Woke Up in 2003 With No Memory of 11 Years — Doctors Found Something Terrifying",
        "script": _MOCK_SCRIPT,
        "description": _MOCK_DESCRIPTION,
        "tags": _MOCK_TAGS,
    }


# --------------------------------------------------
# generate_script — standalone, fetches own story
# --------------------------------------------------

def generate_script() -> str:
    if MOCK_MODE:
        print("[MOCK_MODE] Skipping OpenAI — returning mock script")
        return _MOCK_SCRIPT

    story = get_viral_story()
    story_type = detect_story_type(story['title'])
    hook = generate_hook(story['title'], story_type)

    prompt = f"""
You are a viral YouTube documentary script writer.

IMPORTANT:
Start the script with this EXACT hook:

"{hook}"

Rules:
- Hook must be first 5–10 seconds of video
- Then immediately transition into story
- Maintain high curiosity every 30–60 seconds
- Keep viewer retention extremely high
- Length: 1500–1800 words
- Ending must be unresolved or shocking

Use this REAL viral Reddit story as your source:

Title: {story['title']}
Score: {story['score']}

Structure:
1. Hook (use the exact hook above)
2. Context
3. Escalation
4. Community reaction
5. Hidden truth / insight
6. Ending twist

Make it feel like a real unexplained internet phenomenon.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# --------------------------------------------------
# _real_content — full package for the pipeline
# --------------------------------------------------

_SYSTEM_PROMPT = """You are a professional YouTube viral documentary script writer.

RULES:
- Do NOT write fictional science stories
- Base everything on real internet discussion and documented events
- Make it engaging like a Netflix documentary
- Add a strong hook in first 5 seconds
- Add mini hooks every 30–60 seconds
- Increase curiosity gradually
- End with an unresolved or shocking question

Script structure:
1. Hook
2. Context
3. Escalation
4. Community reaction
5. Hidden truth / insight
6. Ending twist

Make it feel like a real unexplained internet phenomenon."""


def _real_content(topic: str) -> dict:
    user_prompt = f"""Use this REAL viral Reddit story as source:

Title: {topic}

Return a JSON object with EXACTLY these fields:
{{
  "title": "Viral YouTube title — max 100 chars. Real hook: name/date/place or shocking claim. High CTR.",
  "script": "Full 7–9 minute YouTube script (1500–1800 words). Follows the 6-part structure. Mini hooks every ~150 words. Ends with unresolved question or shocking twist.",
  "description": "YouTube description 150–250 words. Hook in first 2 lines. Story summary. CTA to subscribe and comment. SEO hashtags.",
  "tags": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8","tag9","tag10"]
}}

Return ONLY valid JSON — no markdown, no code fences, no extra text."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.85,
    )

    return json.loads(response.choices[0].message.content)


# --------------------------------------------------
# Public API
# --------------------------------------------------

def generate_full_content(topic: str) -> dict:
    if MOCK_MODE:
        print(f"[MOCK_MODE] Skipping OpenAI — returning mock content for: {topic}")
        return _mock_content(topic)
    return _real_content(topic)
