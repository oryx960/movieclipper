import logging
from pathlib import Path
from typing import Iterator, List

from .config import load_config, save_config
from .ffmpeg_utils import get_duration, create_clip

logger = logging.getLogger(__name__)


def _find_movies(directory: Path) -> Iterator[Path]:
    exts = {".mkv", ".mp4", ".avi", ".mov"}
    for path in directory.rglob("*"):
        if path.suffix.lower() in exts and path.is_file():
            yield path


def get_movies_to_process(directory: Path) -> List[Path]:
    config = load_config()
    processed = set(config.get("processed_movies", []))
    return [p for p in _find_movies(directory) if str(p) not in processed]


def scan_movies(directory: str, stop_event=None) -> Iterator[Path]:
    """Scan directory for movies and generate backlog clips."""
    directory = Path(directory)
    movies = get_movies_to_process(directory)
    config = load_config()
    processed = set(config.get("processed_movies", []))

    for movie in movies:
        if stop_event and stop_event.is_set():
            logger.info("Scan stopped by user")
            break
        logger.info("Processing %s", movie)
        duration = get_duration(movie)
        backlog_dir = movie.parent / "backlog"
        out_path = backlog_dir / movie.name
        if not out_path.exists():
            create_clip(movie, out_path, duration)
        processed.add(str(movie))
        config["processed_movies"] = list(processed)
        save_config(config)
        yield movie
