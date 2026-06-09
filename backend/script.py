from openai import OpenAI
from config import OPENAI_API_KEY
import json

client = OpenAI(api_key=OPENAI_API_KEY)


def generate_full_content(topic: str) -> dict:
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

    raw = response.choices[0].message.content
    return json.loads(raw)


def generate_script(topic: str) -> str:
    content = generate_full_content(topic)
    return content.get("script", "")
