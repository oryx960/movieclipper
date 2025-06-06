from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import logging
from threading import Thread, Event
from pathlib import Path

from app.ffmpeg_utils import check_ffmpeg
from app.config import load_config, save_config
from app.jellyfin import test_jellyfin_connection
from app.scanner import scan_movies, get_movies_to_process

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scan_thread = None
stop_event = Event()
progress = {"current": "", "index": 0, "total": 0}
recent = []

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    config = load_config()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "config": config, "progress": progress, "recent": recent},
    )

@app.post("/test-jellyfin")
async def test_jellyfin(url: str = Form(...), api_key: str = Form(...)):
    result = test_jellyfin_connection(url, api_key)
    return {"success": result, "message": "Connection OK" if result else "Failed"}

@app.post("/save-jellyfin")
async def save_jellyfin(url: str = Form(...), api_key: str = Form(...), library_path: str = Form(...)):
    config = load_config()
    config["jellyfin"] = {"url": url, "api_key": api_key}
    config["library_path"] = library_path
    save_config(config)
    return RedirectResponse("/", status_code=303)

@app.post("/start-scan")
async def start_scan():
    global scan_thread
    config = load_config()
    if scan_thread and scan_thread.is_alive():
        return RedirectResponse("/", status_code=303)

    movies = get_movies_to_process(Path(config["library_path"]))
    progress["index"] = 0
    progress["total"] = len(movies)
    progress["current"] = ""
    stop_event.clear()

    def _run():
        for idx, movie in enumerate(scan_movies(config["library_path"], stop_event), start=1):
            progress["index"] = idx
            progress["current"] = movie.name
            recent.insert(0, movie.name)
            del recent[5:]
        progress["current"] = ""

    scan_thread = Thread(target=_run, daemon=True)
    scan_thread.start()
    return RedirectResponse("/", status_code=303)


@app.post("/stop-scan")
async def stop_scan():
    stop_event.set()
    return RedirectResponse("/", status_code=303)

@app.on_event("startup")
def startup_event():
    if not check_ffmpeg():
        logger.error("ffmpeg is not installed or not available in PATH")
