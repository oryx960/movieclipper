import subprocess
from pathlib import Path
import random

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except Exception:
        return False


def get_duration(path: Path) -> float:
    """Return duration of a media file in seconds."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def create_clip(movie: Path, dest: Path, duration: float):
    dest.parent.mkdir(parents=True, exist_ok=True)
    start = 0
    if duration > 190:
        start_min = 180
        start_max = max(int(duration / 2), start_min)
        if start_max - start_min > 10:
            start = random.randint(start_min, start_max - 10)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        str(movie),
        "-t",
        "10",
        "-c:v",
        "libx265",
        "-preset",
        "ultrafast",
        "-crf",
        "30",
        "-c:a",
        "aac",
        str(dest),
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
