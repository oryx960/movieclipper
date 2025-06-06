import subprocess
from pathlib import Path
import random
import logging

logger = logging.getLogger(__name__)

def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        logger.info("ffmpeg found")
        return True
    except Exception as exc:
        logger.error("ffmpeg check failed: %s", exc)
        return False


def get_duration(path: Path) -> float:
    """Return duration of a media file in seconds."""
    logger.debug("Getting duration for %s", path)
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
        duration = float(result.stdout.strip())
        logger.debug("Duration for %s: %s", path, duration)
        return duration
    except ValueError:
        return 0.0


def create_clip(movie: Path, dest: Path, duration: float, progress: dict | None = None):
    """Create a short clip for *movie* at *dest* updating *progress* if provided."""
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
        "-progress",
        "-",
        "-nostats",
        str(dest),
    ]
    logger.info("Running ffmpeg for %s", movie)
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    total_ms = 10 * 1_000_000
    if progress is not None:
        progress["movie_progress"] = 0
    while True:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            continue
        line = line.strip()
        if line.startswith("out_time_ms="):
            try:
                out_ms = int(line.split("=")[1])
                pct = min(100, int(out_ms * 100 / total_ms))
                if progress is not None:
                    progress["movie_progress"] = pct
            except ValueError:
                pass
        elif line.startswith("progress=") and line.split("=")[1] == "end":
            if progress is not None:
                progress["movie_progress"] = 100
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        logger.error("ffmpeg failed for %s: %s", movie, stderr)
