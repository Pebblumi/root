# upload_youtube.py
import os, json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

VIDEO_PATH = Path("output/short_final.mp4")
if not VIDEO_PATH.exists():
    raise FileNotFoundError(f"Video not found: {VIDEO_PATH}")

script = json.loads(Path("script.json").read_text(encoding="utf-8"))

# Build credentials from refresh token (no interactive login needed)
creds = Credentials(
    token=None,
    refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["YOUTUBE_CLIENT_ID"],
    client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)

youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

title = script["title"]
if not title.lower().endswith("#shorts"):
    title = (title[:90] + " #Shorts") if len(title) < 95 else title[:95] + " #Shorts"

body = {
    "snippet": {
        "title": title,
        "description": f"{script['description']}\n\n#Shorts",
        "tags": script.get("tags", []) + ["shorts", "trending", "viral"],
        "categoryId": "24",   # Entertainment
        "defaultLanguage": "en",
        "defaultAudioLanguage": "en",
    },
    "status": {
        "privacyStatus": "private",           # review in Studio first
        "selfDeclaredMadeForKids": False,      # general audience
        "license": "youtube",
        "embeddable": True,
    },
}

media = MediaFileUpload(str(VIDEO_PATH), mimetype="video/mp4",
                        resumable=True, chunksize=4 * 1024 * 1024)

print("📤 Uploading to YouTube...")
request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

response = None
try:
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"   progress: {int(status.progress() * 100)}%")
except HttpError as e:
    raise RuntimeError(f"YouTube upload failed: {e.content.decode()}") from e

video_id = response["id"]
print(f"✅ Uploaded: https://youtu.be/{video_id}")
print(f"   Video ID: {video_id}")
