import json
import sys
import os

# ✅ Add path manually
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "services", "v1", "ffmpeg")))

from ffmpeg_compose import process_ffmpeg_compose


with open("payload.json", "r") as f:
    payload = json.load(f)

outputs, metadata = process_ffmpeg_compose(payload, job_id="localtest")

print("✅ Output files:", outputs)
print("🧠 Metadata:", metadata)
