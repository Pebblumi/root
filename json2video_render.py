# json2video_render.py
import os, json, time
from pathlib import Path
import requests

J2V_KEY = os.environ["JSON2VIDEO_API_KEY"]
BASE = "https://api.json2video.com/v2"

script = json.loads(Path("script.json").read_text(encoding="utf-8"))
image_urls = json.loads(Path("image_urls.json").read_text(encoding="utf-8"))

# Build 6 scenes × 10 seconds = 60 seconds
scenes = []
for scene, img_url in zip(script["scenes"], image_urls):
    scenes.append({
        "duration": 10,
        "elements": [
            {
                "type": "image",
                "src": img_url,
                "duration": 10,
                "zoom": 2,   # slow zoom-in Ken Burns effect
            },
            {
                "type": "text",
                "text": scene["on_screen_text"],
                "duration": 10,
                "style": "001",
                "position": "bottom",
            },
        ],
    })

payload = {
    "resolution": "full-hd",
    "quality": "high",
    "scenes": scenes,
}

# Submit
print("🚀 Submitting to JSON2Video...")
r = requests.post(f"{BASE}/movies", headers={"x-api-key": J2V_KEY}, json=payload, timeout=30)
if r.status_code != 200:
    raise RuntimeError(f"Submit failed ({r.status_code}): {r.text}")

project_id = r.json()["project"]
print(f"✅ Project created: {project_id}")

# Poll
print("⏳ Rendering...")
video_url = None
deadline = time.time() + 600
while time.time() < deadline:
    sr = requests.get(f"{BASE}/movies", headers={"x-api-key": J2V_KEY},
                      params={"project": project_id}, timeout=15)
    sr.raise_for_status()
    movie = sr.json().get("movie", {})
    status = movie.get("status")
    print(f"   status: {status}")
    if status == "done":
        video_url = movie.get("url")
        break
    if status in ("error", "timeout"):
        raise RuntimeError(f"Render failed: {movie}")
    time.sleep(10)

if not video_url:
    raise TimeoutError("Render exceeded 10 minutes")

# Download
Path("output").mkdir(exist_ok=True)
out = Path("output/short_final.mp4")
print(f"⬇️ Downloading {video_url}")
with requests.get(video_url, stream=True, timeout=120) as resp:
    resp.raise_for_status()
    with open(out, "wb") as f:
        for chunk in resp.iter_content(8192):
            f.write(chunk)

print(f"✅ Saved {out} ({out.stat().st_size/1024/1024:.1f} MB)")
