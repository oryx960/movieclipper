import logging
from pathlib import Path
from typing import Iterator, List

from .config import load_config, save_config
from .ffmpeg_utils import get_duration, create_clip

logger = logging.getLogger(__name__)


def _find_movies(directory: Path) -> Iterator[Path]:
    exts = {".mkv", ".mp4", ".avi", ".mov"}
    for path in directory.rglob("*"):
        if "backdrops" in path.parts:
            continue
        if path.suffix.lower() in exts and path.is_file():
            yield path


def get_movies_to_process(directory: Path) -> List[Path]:
    """Return movies needing backdrop clips."""
    config = load_config()
    processed = set(config.get("processed_movies", []))
    movies = []
    for p in _find_movies(directory):
        backdrop_path = p.parent / "backdrops" / p.name
        if not backdrop_path.exists() or str(p) not in processed:
            movies.append(p)
    return movies


def scan_movies(directory: str, stop_event=None, progress: dict | None = None) -> Iterator[Path]:
    """Scan directory for movies and generate backdrop clips."""
    directory = Path(directory)
    movies = get_movies_to_process(directory)
    logger.info("Scanning %s for movies", directory)
    if not movies:
        logger.info("No unprocessed movies found")
    else:
        logger.info("%d movies queued for processing", len(movies))
    config = load_config()
    processed = set(config.get("processed_movies", []))

    for movie in movies:
        if stop_event and stop_event.is_set():
            logger.info("Scan stopped by user")
            break
        logger.info("Processing %s", movie)
        if progress is not None:
            progress["movie_progress"] = 0
        duration = get_duration(movie)
        backdrop_dir = movie.parent / "backdrops"
        out_path = backdrop_dir / movie.name
        if not out_path.exists():
            logger.info("Creating clip for %s", movie)
            create_clip(movie, out_path, duration, progress)
        else:
            logger.info("Clip already exists for %s", movie)
        processed.add(str(movie))
        config["processed_movies"] = list(processed)
        save_config(config)
        if progress is not None:
            progress["movie_progress"] = 100
        yield movie
