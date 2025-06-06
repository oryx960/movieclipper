import json
import os
from pathlib import Path


CONFIG_DIR = Path(os.environ.get("MOVIECLIPPER_CONFIG_DIR", "."))
CONFIG_PATH = CONFIG_DIR / "config.json"

def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config():
    _ensure_dir()
    if CONFIG_PATH.exists():
        data = json.loads(CONFIG_PATH.read_text())
    else:
        data = {}
    data.setdefault("processed_movies", [])
    data.setdefault("jellyfin", {"url": "", "api_key": ""})
    data.setdefault("library_path", "/movies")
    data.setdefault("last_jellyfin_scan", "1970-01-01T00:00:00")
    return data

def save_config(data):
    _ensure_dir()
    CONFIG_PATH.write_text(json.dumps(data, indent=2))
