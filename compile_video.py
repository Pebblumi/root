# compile_video.py
from pathlib import Path
from moviepy.editor import VideoFileClip, concatenate_videoclips

CLIPS_DIR = Path("clips")
OUTPUT = Path("output/short_final.mp4")
OUTPUT.parent.mkdir(exist_ok=True)

paths = sorted(CLIPS_DIR.glob("scene_*.mp4"))
if len(paths) != 6:
    raise RuntimeError(f"Expected 6 clips, found {len(paths)}")

clips = [VideoFileClip(str(p)) for p in paths]
final = concatenate_videoclips(clips, method="compose")

print(f"Total duration: {final.duration:.1f} seconds")
assert 58 <= final.duration <= 62, "Duration outside 60s target"

final.write_videofile(str(OUTPUT), fps=24, codec="libx264",
                      audio_codec="aac", threads=4)

final.close()
for c in clips:
    c.close()
print(f"🎬 Saved {OUTPUT}")
