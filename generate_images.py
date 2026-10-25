# generate_images.py
import os, json, time, urllib.parse
from pathlib import Path
import httpx

POLLINATIONS = "https://gen.pollinations.ai"
POLL_KEY = os.environ["POLLINATIONS_API_KEY"]
CATBOX = "https://catbox.moe/user/api.php"
IMG_DIR = Path("images")
IMG_DIR.mkdir(exist_ok=True)

script = json.loads(Path("script.json").read_text(encoding="utf-8"))


def generate_image(prompt: str, index: int) -> Path:
    """Download a 9:16 image from Pollinations."""
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{POLLINATIONS}/image/{encoded}"
    params = {
        "model": "flux",       # reliable image model
        "width": 720,
        "height": 1280,        # 9:16 vertical
        "nologo": "true",
    }
    headers = {"Authorization": f"Bearer {POLL_KEY}"}
    out = IMG_DIR / f"scene_{index:02d}.jpg"

    for attempt in range(3):
        try:
            with httpx.stream("GET", url, params=params, headers=headers,
                              timeout=120.0, follow_redirects=True) as r:
                if r.status_code != 200:
                    body = r.read().decode("utf-8", errors="replace")
                    print(f"⚠️ Scene {index} attempt {attempt+1} ({r.status_code}): {body[:200]}")
                    time.sleep(3)
                    continue
                with open(out, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
            print(f"✅ Image {index:02d} saved ({out.stat().st_size/1024:.1f} KB)")
            return out
        except httpx.RequestError as e:
            print(f"⚠️ Scene {index} network error: {e}")
            time.sleep(3)
    raise RuntimeError(f"Failed to generate image {index}")


def upload_to_catbox(image_path: Path) -> str:
    """Upload to Catbox (free, no auth) and return public URL."""
    with open(image_path, "rb") as f:
        r = httpx.post(
            CATBOX,
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (image_path.name, f, "image/jpeg")},
            timeout=60.0,
        )
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Catbox upload failed: {url}")
    print(f"   → Hosted: {url}")
    return url


# --- Main ---
public_urls = []
for i, scene in enumerate(script["scenes"], start=1):
    path = generate_image(scene["image_prompt"], i)
    url = upload_to_catbox(path)
    public_urls.append(url)
    time.sleep(1)

# Save the URLs for the JSON2Video step
Path("image_urls.json").write_text(json.dumps(public_urls, indent=2), encoding="utf-8")
print(f"✅ All {len(public_urls)} images hosted. URLs saved to image_urls.json")
