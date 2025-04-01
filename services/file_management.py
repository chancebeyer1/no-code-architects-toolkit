from urllib.parse import urlparse
import os
import uuid
import requests

def download_file(url, storage_path="/tmp/"):
    # Parse file extension from URL path (e.g. .jpg, .webm, .txt)
    parsed_url = urlparse(url)
    _, ext = os.path.splitext(parsed_url.path)
    if not ext:
        ext = ".bin"  # fallback

    file_id = str(uuid.uuid4())
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)

    local_filename = os.path.join(storage_path, f"{file_id}{ext}")

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(local_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return local_filename



def delete_old_files():
    now = time.time()
    for filename in os.listdir(STORAGE_PATH):
        file_path = os.path.join(STORAGE_PATH, filename)
        if os.path.isfile(file_path) and os.stat(file_path).st_mtime < now - 3600:
            os.remove(file_path)
