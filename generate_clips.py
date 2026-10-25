# generate_clips.py (corrected for bytedance/seedance-1-lite)
import os, json, time, urllib.parse
from pathlib import Path
import httpx

BASE_URL = "https://gen.pollinations.ai"
API_KEY = os.environ["POLLINATIONS_API_KEY"]
OUTPUT_DIR = Path("clips")
OUTPUT_DIR.mkdir(exist_ok=True)

script = json.loads(Path("script.json").read_text(encoding="utf-8"))
PROMPTS = [s["video_prompt"] for s in script["scenes"]]


def generate_clip(prompt: str, index: int) -> Path:
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{BASE_URL}/video/{encoded}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    out = OUTPUT_DIR / f"scene_{index:02d}.mp4"

    # Try durations in order of preference; seedance-1-lite works best with 10 or 5
    for duration in (10, 5, 8):
        params = {
            "model": "bytedance/seedance-1-lite",   # ✅ New canonical model ID
            "duration": duration,
            "aspectRatio": "9:16",
            "safe": "privacy,sexual,violence,shield",
        }

        try:
            with httpx.stream(
                "GET", url, params=params, headers=headers,
                timeout=300.0, follow_redirects=True
            ) as r:
                if r.status_code != 200:
                    body = r.read().decode("utf-8", errors="replace")
                    print(f"⚠️ Scene {index:02d} duration={duration} failed ({r.status_code}): {body}")
                    continue  # try the next duration

                with open(out, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)

            print(f"✅ Scene {index:02d} saved with duration={duration} "
                  f"({out.stat().st_size / 1024:.1f} KB)")
            return out

        except httpx.RequestError as e:
            print(f"⚠️ Scene {index:02d} network error with duration={duration}: {e}")
            continue

    raise RuntimeError(f"❌ Scene {index:02d} failed for all duration options")


for i, prompt in enumerate(PROMPTS, start=1):
    generate_clip(prompt, i)
    if i < len(PROMPTS):
        time.sleep(2)
