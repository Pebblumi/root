# generate_script.py
import os, json, random
from pathlib import Path
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

DEFAULT_TOPICS = [
    "AI is changing how we make videos",
    "The most surprising science facts of 2026",
    "How AI learns to see the world",
    "A day in the life of an AI assistant",
]

# Fallback chain: explicit env var → random default
TRENDING_TOPIC = os.environ.get("TRENDING_TOPIC", "").strip()
if not TRENDING_TOPIC:
    TRENDING_TOPIC = random.choice(DEFAULT_TOPICS)

print(f"📌 Using topic: {TRENDING_TOPIC}")

SYSTEM_PROMPT = """
You are a viral YouTube Shorts scriptwriter.
Create a fast-paced, 60-second vertical Short about the given trending topic.

Return ONLY valid JSON with this exact structure:
{
  "title": "Clickable YouTube Shorts title (under 60 chars)",
  "description": "Short SEO description with 3-5 hashtags",
  "tags": ["tag1", "tag2", "tag3"],
  "scenes": [
    {
      "scene_number": 1,
      "on_screen_text": "Text overlay (max 8 words)",
      "image_prompt": "Detailed visual prompt for a 9:16 vertical AI image. Specify subject, style, lighting, mood. No text in image."
    }
  ]
}

Rules:
- Exactly 6 scenes, each ~10 seconds.
- Scene 1 must be a HOOK within the first 2 seconds.
- Use on_screen_text for captions (Shorts are often watched muted).
- End with a loop-friendly final frame.
- Keep content brand-safe and suitable for general audiences.
"""

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=f"{SYSTEM_PROMPT}\n\nTrending topic: {TRENDING_TOPIC}",
    config={"response_mime_type": "application/json"},
)

story = json.loads(response.text.strip())
Path("script.json").write_text(json.dumps(story, indent=2), encoding="utf-8")
print(f"✅ Script saved. Title: {story['title']} | Scenes: {len(story['scenes'])}")
