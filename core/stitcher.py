"""
Lossless TS Segment Stitcher & Container Remuxer
Assembles downloaded stream chunks into a coherent video file.
"""

import os
import shutil
import subprocess
from typing import List, Tuple


def stitch_segments(segments: List[Tuple[int, bytes]], output_path: str) -> str:
    """Concatenates ordered MPEG-TS segments into a single video file."""
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Sort sequentially by index
    sorted_segments = sorted(segments, key=lambda x: x[0])

    is_mp4_target = output_path.lower().endswith(".mp4")
    temp_ts_path = output_path if not is_mp4_target else output_path + ".tmp.ts"

    with open(temp_ts_path, "wb") as out_f:
        for idx, chunk in sorted_segments:
            out_f.write(chunk)

    # If output target is .mp4 and ffmpeg is installed, remux losslessly
    if is_mp4_target and shutil.which("ffmpeg"):
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                temp_ts_path,
                "-c",
                "copy",
                "-bsf:a",
                "aac_adtstoasc",
                output_path,
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            if os.path.exists(temp_ts_path):
                os.remove(temp_ts_path)
            return output_path
        except Exception:
            # Fallback: rename .tmp.ts to .ts if ffmpeg remux fails
            fallback_ts = output_path.rsplit(".", 1)[0] + ".ts"
            if os.path.exists(temp_ts_path):
                os.rename(temp_ts_path, fallback_ts)
            return fallback_ts

    return temp_ts_path
