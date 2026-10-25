# upload_youtube.py
import os, json
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

VIDEO_PATH = Path("output/short_final.mp4")
script = json.loads(Path("script.json").read_text(encoding="utf-8"))

creds = Credentials(
    token=None,
    refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
    token_uri="https://oauth2.googleapis.com/token",
    client_id=os.environ["YOUTUBE_CLIENT_ID"],
    client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
    scopes=["https://www.googleapis.com/auth/youtube.upload"],
)

youtube = build("youtube", "v3", credentials=creds)

body = {
    "snippet": {
        "title": f"{script['title']} #Shorts",
        "description": f"{script['description']}\n\n#Shorts",
        "tags": script["tags"] + ["shorts", "viral", "trending"],
        "categoryId": "24",   # Entertainment
    },
    "status": {
        "privacyStatus": "private",            # review before publishing
        "selfDeclaredMadeForKids": False,       # general audience
    },
}

media = MediaFileUpload(str(VIDEO_PATH), mimetype="video/*",
                        resumable=True, chunksize=1024*1024)

request = youtube.videos().insert(part="snippet,status",
                                  body=body, media_body=media)

response = None
while response is None:
    status, response = request.next_chunk()
    if status:
        print(f"Upload progress: {int(status.progress()*100)}%")

print(f"✅ Uploaded: https://youtu.be/{response['id']}")
