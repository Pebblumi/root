# generate_images.py (updated to use JSON2Video media upload)
import os, json, time, urllib.parse
from pathlib import Path
import httpx

POLLINATIONS = "https://gen.pollinations.ai"
POLL_KEY = os.environ["POLLINATIONS_API_KEY"]
JSON2VIDEO_KEY = os.environ["JSON2VIDEO_API_KEY"]
J2V_MEDIA_ENDPOINT = "https://api.json2video.com/v2/media/file"

IMG_DIR = Path("images")
IMG_DIR.mkdir(exist_ok=True)

script = json.loads(Path("script.json").read_text(encoding="utf-8"))


def generate_image(prompt: str, index: int) -> Path:
    """Download a 9:16 image from Pollinations."""
    encoded = urllib.parse.quote(prompt, safe="")
    url = f"{POLLINATIONS}/image/{encoded}"
    params = {
        "model": "flux",
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


def upload_to_json2video(image_path: Path, index: int) -> str:
    """
    Upload an image to JSON2Video's media library and return its public URL.
    Uses the two-step presigned URL flow.
    """
    file_size = image_path.stat().st_size
    filename = f"scene_{index:02d}.jpg"

    # Step 1: Request a presigned upload URL
    register_payload = {
        "name": filename,
        "contentType": "image/jpeg",
        "size": file_size,
        "folder": "shorts-assets",
    }

    register_resp = httpx.post(
        J2V_MEDIA_ENDPOINT,
        headers={"x-api-key": JSON2VIDEO_KEY, "Content-Type": "application/json"},
        json=register_payload,
        timeout=30.0,
    )
    register_resp.raise_for_status()
    data = register_resp.json()

    upload_url = data["uploadUrl"]
    file_url = data["fileUrl"]

    # Step 2: PUT the file bytes to the presigned URL
    with open(image_path, "rb") as f:
        put_resp = httpx.put(
            upload_url,
            headers={"Content-Type": "image/jpeg"},
            content=f,
            timeout=120.0,
        )
    put_resp.raise_for_status()

    print(f"   → Uploaded to JSON2Video CDN: {file_url}")
    return file_url


# --- Main ---
public_urls = []
for i, scene in enumerate(script["scenes"], start=1):
    local_path = generate_image(scene["image_prompt"], i)
    cdn_url = upload_to_json2video(local_path, i)
    public_urls.append(cdn_url)
    time.sleep(1)  # small pause between uploads

Path("image_urls.json").write_text(json.dumps(public_urls, indent=2), encoding="utf-8")
print(f"✅ All {len(public_urls)} images uploaded to JSON2Video CDN")
