#Start APP
import uvicorn
from app.self_check import run_checks

if __name__ == "__main__":
    if run_checks():
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
