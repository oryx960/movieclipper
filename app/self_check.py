import sys
import logging
from .ffmpeg_utils import check_ffmpeg
from .config import load_config

logger = logging.getLogger(__name__)


def run_checks() -> bool:
    ok = True
    if not check_ffmpeg():
        logger.error("ffmpeg not found")
        ok = False
    try:
        load_config()
    except Exception as exc:
        logger.error("Failed to load config: %s", exc)
        ok = False
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    if not run_checks():
        sys.exit(1)
