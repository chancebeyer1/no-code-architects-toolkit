import os
import subprocess
import json
from services.file_management import download_file

STORAGE_PATH = "/tmp/"

def get_extension_from_format(format_name):
    format_to_extension = {
        'mp4': 'mp4', 'mov': 'mov', 'avi': 'avi', 'mkv': 'mkv', 'webm': 'webm', 'gif': 'gif',
        'apng': 'apng', 'jpg': 'jpg', 'jpeg': 'jpg', 'png': 'png', 'image2': 'png', 'rawvideo': 'raw',
        'mp3': 'mp3', 'wav': 'wav', 'aac': 'aac', 'flac': 'flac', 'ogg': 'ogg'
    }
    return format_to_extension.get(format_name.lower(), 'mp4')

def get_metadata(filename, metadata_requests, job_id):
    metadata = {}
    if metadata_requests.get('thumbnail'):
        thumbnail_filename = f"{os.path.splitext(filename)[0]}_thumbnail.jpg"
        thumbnail_command = [
            'ffmpeg', '-i', filename, '-vf', 'select=eq(n\\,0)', '-vframes', '1', thumbnail_filename
        ]
        try:
            subprocess.run(thumbnail_command, check=True, capture_output=True, text=True)
            if os.path.exists(thumbnail_filename):
                metadata['thumbnail'] = thumbnail_filename
        except subprocess.CalledProcessError as e:
            print(f"Thumbnail generation failed: {e.stderr}")

    if metadata_requests.get('filesize'):
        metadata['filesize'] = os.path.getsize(filename)

    if metadata_requests.get('encoder') or metadata_requests.get('duration') or metadata_requests.get('bitrate'):
        ffprobe_command = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', filename
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        probe_data = json.loads(result.stdout)

        if metadata_requests.get('duration'):
            metadata['duration'] = float(probe_data['format']['duration'])
        if metadata_requests.get('bitrate'):
            metadata['bitrate'] = int(probe_data['format']['bit_rate'])

        if metadata_requests.get('encoder'):
            metadata['encoder'] = {}
            for stream in probe_data['streams']:
                if stream['codec_type'] == 'video':
                    metadata['encoder']['video'] = stream.get('codec_name', 'unknown')
                elif stream['codec_type'] == 'audio':
                    metadata['encoder']['audio'] = stream.get('codec_name', 'unknown')

    return metadata

def process_ffmpeg_compose(data, job_id):
    output_filenames = []
    textfile_path = None
    fontfile_path = None
    command = ["ffmpeg"]

    # Global options
    for option in data.get("global_options", []):
        command.append(option["option"])
        if "argument" in option and option["argument"] is not None:
            command.append(str(option["argument"]))

    # Inputs
    for input_data in data["inputs"]:
        if "options" in input_data:
            for option in input_data["options"]:
                command.append(option["option"])
                if "argument" in option and option["argument"] is not None:
                    command.append(str(option["argument"]))

        input_path = download_file(input_data["file_url"], STORAGE_PATH)

        if input_path.endswith(".txt"):
            textfile_path = input_path
            print("📄 Found textfile path:", textfile_path)
        elif input_path.endswith(".ttf"):
            fontfile_path = input_path
            print("🔤 Found fontfile path:", fontfile_path)
        else:
            command.extend(["-i", input_path])

    # Replace __TEXTFILE__ and __FONTFILE__
    if data.get("filters"):
        for filter_obj in data["filters"]:
            if "filter" in filter_obj:
                print("🔍 Original filter:", filter_obj["filter"])

                # Replace textfile
                if "textfile=__TEXTFILE__" in filter_obj["filter"]:
                    if not textfile_path:
                        raise Exception("❌ __TEXTFILE__ used in filter, but no .txt input found.")
                    print("✅ Replacing __TEXTFILE__ with:", textfile_path)
                    filter_obj["filter"] = filter_obj["filter"].replace(
                        "textfile=__TEXTFILE__", f"textfile='{textfile_path}'"
                    )

                # Replace fontfile
                if "fontfile=__FONTFILE__" in filter_obj["filter"]:
                    if fontfile_path:
                        print("✅ Replacing __FONTFILE__ with:", fontfile_path)
                        filter_obj["filter"] = filter_obj["filter"].replace(
                            "fontfile=__FONTFILE__", f"fontfile='{fontfile_path}'"
                        )
                    else:
                        # fallback to font= if fontfile not found
                        font_name = data.get("fallback_font", "Arial")
                        print(f"⚠️ No font file provided. Falling back to font='{font_name}'")
                        filter_obj["filter"] = filter_obj["filter"].replace(
                            "fontfile=__FONTFILE__", f"font='{font_name}'"
                        )

                print("✅ Updated filter:", filter_obj["filter"])

        # Add combined filter_complex
        filter_complex = ";".join(filter_obj["filter"] for filter_obj in data["filters"])
        command.extend(["-filter_complex", filter_complex])

    # Outputs
    for i, output in enumerate(data["outputs"]):
        format_name = None
        for option in output["options"]:
            if option["option"] == "-f":
                format_name = option.get("argument")
                break

        extension = get_extension_from_format(format_name) if format_name else 'mp4'
        output_filename = os.path.join(STORAGE_PATH, f"{job_id}_output_{i}.{extension}")
        output_filenames.append(output_filename)

        for option in output["options"]:
            command.append(option["option"])
            if "argument" in option and option["argument"] is not None:
                command.append(str(option["argument"]))
        
        if format_name == "webm":
            command.extend([
                "-c:v", "libvpx-vp9",        # use VP9 for better quality & transparency
                "-b:v", "1M",                # required for VP9
                "-pix_fmt", "yuva420p",     # enable transparency
                "-auto-alt-ref", "0"        # required for transparency
            ])
        
        command.append(output_filename)

    # Log the full command
    print("🔧 Final FFmpeg command:")
    print(" ".join(command))

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg stderr:", e.stderr)
        raise Exception(f"FFmpeg command failed: {e.stderr}")

    # Get metadata
    metadata = []
    if data.get("metadata"):
        for output_filename in output_filenames:
            metadata.append(get_metadata(output_filename, data["metadata"], job_id))

    return output_filenames, metadata
