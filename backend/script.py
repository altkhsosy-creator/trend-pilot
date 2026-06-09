from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_script(topic):
    prompt = f"""
Write a viral YouTube storytelling script in English.

Topic: {topic}

Requirements:
- 8–10 minutes
- Strong hook in first 5 seconds
- Story format
- Emotional + curiosity-driven
- Simple English
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
