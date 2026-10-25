# generate_script.py
import os, json
from pathlib import Path
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

TRENDING_TOPIC = os.environ.get("TRENDING_TOPIC", "Tesla flying car")

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
      "video_prompt": "Detailed visual prompt for 9:16 vertical text-to-video. Specify action, camera angle, mood."
    }
  ]
}

Rules:
- Exactly 6 scenes, each ~10 seconds.
- Scene 1 must be a HOOK within the first 2 seconds.
- Use on_screen_text for captions (Shorts are often watched muted).
- End with a loop-friendly final frame.
- Keep all content brand-safe and suitable for a general audience.
"""

response = client.models.generate_content(
    model="gemini-3-flash-preview",   # free-tier model
    contents=f"{SYSTEM_PROMPT}\n\nTrending topic: {TRENDING_TOPIC}",
    config={"response_mime_type": "application/json"},  # force JSON
)

story = json.loads(response.text.strip())
Path("script.json").write_text(json.dumps(story, indent=2), encoding="utf-8")
print(f"✅ Script saved for: {TRENDING_TOPIC}")
print(f"Title: {story['title']}")
print(f"Scenes: {len(story['scenes'])}")
