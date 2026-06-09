import json
from config import OPENAI_API_KEY, MOCK_MODE


# --------------------------------------------------
# MOCK DATA — used when MOCK_MODE=true
# --------------------------------------------------

_MOCK_SCRIPT = """
Have you ever wondered what it would feel like to wake up one morning and discover that everything you thought you knew was completely wrong? That's exactly what happened to a small team of scientists working deep in a remote laboratory — and what they found changed the course of human history forever.

It started with a simple experiment. Nothing unusual, nothing groundbreaking — or so they thought. The lead researcher, a quiet woman named Dr. Elena Marsh, had spent fifteen years studying a phenomenon that most of her colleagues dismissed as noise. But Elena was not the kind of person who walked away from a mystery.

On the morning of March 4th, she walked into her lab at 6 AM, coffee in hand, and noticed something strange on her monitor. The readings were off — not by a little, but by a factor of one thousand. Her first instinct was that the equipment had malfunctioned. So she checked it. Then checked it again. The equipment was fine.

What she was looking at was real.

Over the next seventy-two hours, Elena and her team ran every test they could think of. They brought in outside experts. They double-checked their math. They questioned their own sanity. And yet, the result was always the same: what they had discovered was something that should not exist — at least not according to everything science had told us up to that point.

Word spread quickly. Within a week, researchers from six countries had flown in to verify the findings. Within a month, the story had leaked to the press — not through any official channel, but through a late-night phone call from a nervous junior scientist who could not sleep.

The public reaction was immediate. Some people were fascinated. Some were terrified. Some refused to believe it at all, insisting it was a hoax, a government conspiracy, or the product of faulty instruments. But the evidence kept piling up, and eventually even the most skeptical voices went quiet.

Here is what made this discovery so extraordinary: it did not just challenge one theory, or one branch of science. It challenged the entire framework through which we understand the physical world. It raised questions that humanity had never had to ask before — and answered some questions that we thought were unanswerable.

Elena gave one interview. Just one. She sat across from a journalist in a sparse conference room, hands folded on the table, and said something that stopped the world cold. She said: we have been looking at the universe from the wrong end of the telescope. Everything we know is true. But we have been reading it backwards.

Nobody fully understood what she meant at first. But over the months and years that followed, as the implications of her discovery rippled outward into physics, biology, philosophy, and even politics, people began to understand. And once you understand it, you cannot unsee it.

This is the story of how one woman, in one lab, on one ordinary morning, cracked open a door that had been sealed shut for the entire history of human civilization. And what came through that door was not a monster, and it was not a miracle. It was something far more unsettling: the truth.

Stay with me. Because by the time this video is over, you will never look at the world the same way again.
""".strip()

_MOCK_DESCRIPTION = """
What if everything you knew was wrong? In this video, we explore the true story of a breakthrough discovery that shook the scientific community — and why it matters to every single one of us.

From the quiet early-morning moment when it all began, to the global shockwave that followed, this is a story about curiosity, courage, and what happens when the truth refuses to stay hidden.

Whether you are a science lover, a history buff, or just someone who enjoys a story that keeps you on the edge of your seat — this one is for you.

🔔 Subscribe for daily stories that make you think differently about the world.
👇 Drop a comment below: What discovery has surprised you the most?

#science #viral #discovery #mystery #truth #history #documentary #storytelling #mindblowing #facts
"""

_MOCK_TAGS = [
    "viral discovery", "science mystery", "mind blowing facts",
    "true story", "history documentary", "unknown facts",
    "scientific breakthrough", "storytelling", "educational",
    "conspiracy truth"
]


def _mock_content(topic: str) -> dict:
    return {
        "title": f"The Shocking Truth About {topic} That Nobody Wants You to Know",
        "script": _MOCK_SCRIPT,
        "description": _MOCK_DESCRIPTION.strip(),
        "tags": _MOCK_TAGS,
    }


# --------------------------------------------------
# REAL — uses OpenAI when MOCK_MODE=false
# --------------------------------------------------

def _real_content(topic: str) -> dict:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""You are a viral YouTube content strategist and scriptwriter.

Given this trending topic: "{topic}"

Return a JSON object with EXACTLY these fields:
{{
  "title": "SEO-optimized viral YouTube title (max 100 chars, curiosity-driven)",
  "script": "Full 8–10 minute YouTube storytelling script. Strong hook in first 5 seconds. Story format. Emotional and curiosity-driven. Simple English.",
  "description": "YouTube video description (150–300 words). Include a hook, what the video covers, and a CTA. SEO-optimized.",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5", "tag6", "tag7", "tag8", "tag9", "tag10"]
}}

Return ONLY valid JSON, no markdown, no extra text."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


# --------------------------------------------------
# Public API
# --------------------------------------------------

def generate_full_content(topic: str) -> dict:
    if MOCK_MODE:
        print(f"[MOCK_MODE] Skipping OpenAI — returning fake content for: {topic}")
        return _mock_content(topic)
    return _real_content(topic)


def generate_script(topic: str) -> str:
    return generate_full_content(topic).get("script", "")
