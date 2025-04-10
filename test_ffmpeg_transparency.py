import json
from services.v1.ffmpeg.ffmpeg_compose import process_ffmpeg_compose

# Load the JSON test input
with open("test_ffmpeg_webm_transparency.json", "r") as f:
    payload = json.load(f)

# Extract job ID and call the FFmpeg processor
data = payload[0]['data']['json']
job_id = data['id']

output_files, metadata = process_ffmpeg_compose(data, job_id)

# Print results
print("✅ Output files:", output_files)
print("📊 Metadata:", json.dumps(metadata, indent=2))
