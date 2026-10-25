# generate_clips.py (corrected)
import os, json, time, urllib.parse
from pathlib import Path
import httpx

BASE_URL = "https://gen.pollinations.ai"
API_KEY = os.environ["POLLINATIONS_API_KEY"]
OUTPUT_DIR = Path("clips")
OUTPUT_DIR.mkdir(exist_ok=True)

script = json.loads(Path("script.json").read_text(encoding="utf-8"))
PROMPTS = [s["video_prompt"] for s in script["scenes"]]


def generate_clip(prompt: str, index: int, duration: int = 8) -> Path:
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{BASE_URL}/video/{encoded}"
    params = {
        "model": "seedance",
        "duration": duration,        # 8 is accepted by the validator
        "aspectRatio": "9:16",      # vertical for Shorts
        "safe": "privacy,sexual,violence,shield",
        # "nologo": "true",         # REMOVED: not a documented video parameter
    }
    headers = {"Authorization": f"Bearer {API_KEY}"}
    out = OUTPUT_DIR / f"scene_{index:02d}.mp4"

    try:
        with httpx.stream(
            "GET", url, params=params, headers=headers,
            timeout=300.0, follow_redirects=True
        ) as r:
            if r.status_code != 200:
                # Print the actual error body so you can see what's wrong
                print(f"❌ Scene {index:02d} failed ({r.status_code}):")
                print(r.read().decode("utf-8", errors="replace"))
                r.raise_for_status()

            with open(out, "wb") as f:
                for chunk in r.iter_bytes():
                    f.write(chunk)

    except httpx.HTTPStatusError:
        # Re-raise so the workflow fails, but the error body is already printed
        raise

    print(f"✅ Scene {index:02d} saved ({out.stat().st_size / 1024:.1f} KB)")
    return out


for i, prompt in enumerate(PROMPTS, start=1):
    generate_clip(prompt, i)
    if i < len(PROMPTS):
        time.sleep(2)
