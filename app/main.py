from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import logging
from threading import Thread, Event
from pathlib import Path
import shutil

from app.ffmpeg_utils import check_ffmpeg
from app.config import load_config, save_config
from datetime import datetime
from app.jellyfin import test_jellyfin_connection, get_latest_item_time
from app.scanner import scan_movies, get_movies_to_process

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scan_thread = None
stop_event = Event()
progress = {"current": "", "index": 0, "total": 0, "movie_progress": 0}
recent = []
connection_log = ""

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    config = load_config()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "config": config,
            "progress": progress,
            "recent": recent,
            "connection_log": connection_log,
        },
    )

@app.get("/progress")
async def progress_status():
    return {"progress": progress, "recent": recent}

@app.post("/test-jellyfin")
async def test_jellyfin(url: str = Form(...), api_key: str = Form(...)):
    global connection_log
    success, message = test_jellyfin_connection(url, api_key)
    connection_log = message
    return {"success": success, "message": message}

@app.post("/save-jellyfin")
async def save_jellyfin(
    url: str = Form(...),
    api_key: str = Form(...),
    library_path: str = Form(...),
    clip_length: int = Form(10),
):
    config = load_config()
    config["jellyfin"] = {"url": url, "api_key": api_key}
    config["library_path"] = library_path
    config["clip_length"] = clip_length
    save_config(config)
    return RedirectResponse("/", status_code=303)

@app.post("/start-scan")
async def start_scan():
    global scan_thread
    global connection_log
    logger.info("Start scan requested")
    config = load_config()
    latest = get_latest_item_time(config["jellyfin"]["url"], config["jellyfin"]["api_key"])
    last_scan = datetime.fromisoformat(config.get("last_jellyfin_scan"))
    if latest and latest <= last_scan:
        logger.info("No new items found on Jellyfin; skipping scan")
        return RedirectResponse("/", status_code=303)

    if scan_thread and scan_thread.is_alive():
        logger.info("Scan already running")
        return RedirectResponse("/", status_code=303)

    movies = get_movies_to_process(Path(config["library_path"]))
    logger.info("Found %d movies to process", len(movies))
    progress["index"] = 0
    progress["total"] = len(movies)
    progress["current"] = ""
    progress["movie_progress"] = 0
    stop_event.clear()
    connection_log = ""

    def _run():
        logger.info("Scan thread started")
        for movie in scan_movies(config["library_path"], stop_event, progress):
            recent.insert(0, movie.name)
            del recent[5:]
        logger.info("Scan thread finished")
        progress["current"] = ""
        progress["movie_progress"] = 0
        if latest:
            config["last_jellyfin_scan"] = latest.isoformat()
            save_config(config)

    scan_thread = Thread(target=_run, daemon=True)
    scan_thread.start()
    return RedirectResponse("/", status_code=303)


@app.post("/stop-scan")
async def stop_scan():
    global scan_thread
    stop_event.set()
    if scan_thread:
        scan_thread.join()
        scan_thread = None
    progress["current"] = ""
    progress["index"] = 0
    progress["total"] = 0
    progress["movie_progress"] = 0
    return RedirectResponse("/", status_code=303)


@app.post("/clear-backdrops")
async def clear_backdrops():
    config = load_config()
    library = Path(config["library_path"])
    for backdrop in library.rglob("backdrops"):
        if backdrop.is_dir():
            shutil.rmtree(backdrop)
    return RedirectResponse("/", status_code=303)

@app.on_event("startup")
def startup_event():
    if not check_ffmpeg():
        logger.error("ffmpeg is not installed or not available in PATH")
