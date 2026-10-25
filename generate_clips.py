# generate_clips.py
import os, json, time, urllib.parse
from pathlib import Path
import httpx

BASE_URL = "https://gen.pollinations.ai"
API_KEY = os.environ["POLLINATIONS_API_KEY"]
OUTPUT_DIR = Path("clips")
OUTPUT_DIR.mkdir(exist_ok=True)

script = json.loads(Path("script.json").read_text(encoding="utf-8"))
PROMPTS = [s["video_prompt"] for s in script["scenes"]]


def generate_clip(prompt: str, index: int, duration: int = 10) -> Path:
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{BASE_URL}/video/{encoded}"
    params = {
        "model": "seedance",       # supports 2–10s
        "duration": duration,
        "aspectRatio": "9:16",    # vertical for Shorts
        "safe": "privacy,sexual,violence,shield",
        "nologo": "true",
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    out = OUTPUT_DIR / f"scene_{index:02d}.mp4"

    with httpx.stream("GET", url, params=params, headers=headers,
                      timeout=300.0, follow_redirects=True) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)

    print(f"✅ Scene {index:02d} saved ({out.stat().st_size/1024:.1f} KB)")
    return out


for i, prompt in enumerate(PROMPTS, start=1):
    generate_clip(prompt, i)
    if i < len(PROMPTS):
        time.sleep(2)   # gentle pacing between API calls
