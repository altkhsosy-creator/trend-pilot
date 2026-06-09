import json
from config import OPENAI_API_KEY, MOCK_MODE


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
# REAL — uses OpenAI when MOCK_MODE=false
# --------------------------------------------------

_SYSTEM_PROMPT = """You are an elite YouTube scriptwriter specialising in viral, high-retention documentary-style content.

Your scripts follow real events, documented cases, Reddit mysteries, true crime, and verifiable social phenomena — NOT pure fiction or made-up science.

Core rules:
1. Open with a single concrete, shocking sentence that happened in real life — name, date, place if possible.
2. Every 30–60 seconds of script (roughly every 150–200 words) insert a hard retention hook: a shocking fact, a twist, an unanswered question, or a direct challenge to the viewer ("Here's what nobody talks about...", "Stop. Before you keep watching, consider this...").
3. Use curiosity gaps constantly — hint at information, then delay the reveal.
4. Include at least two verifiable, specific factual claims (real statistics, documented cases, named people or places).
5. End with an unresolved question, open mystery, or disturbing implication — never a tidy conclusion.
6. Language: conversational, present-tense where possible, short punchy sentences mixed with longer ones.
7. No fictional scientists, no made-up labs, no "scientists discovered" vague claims — ground everything in reality."""


def _real_content(topic: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    user_prompt = f"""Trending topic / story seed: "{topic}"

Return a JSON object with EXACTLY these fields:
{{
  "title": "Viral YouTube title — max 100 chars. Use a real hook: name/date/place or shocking claim. High CTR.",
  "script": "Full 7–9 minute YouTube script (~1200–1500 words). Opens with a real event or documented case. Retention hooks every ~150 words. Curiosity gaps. Shocking factual claims. Ends with an unresolved question or open mystery. NO fictional characters or invented science. Reddit/true-mystery/real-events tone.",
  "description": "YouTube description 150–250 words. Hook in first 2 lines. Summary of story. SEO tags. CTA to subscribe and comment.",
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


def generate_script(topic: str) -> str:
    return generate_full_content(topic).get("script", "")
