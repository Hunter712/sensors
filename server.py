from pathlib import Path
from typing import Any
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
INDEX_HTML = (BASE_DIR / "templates" / "index.html").read_text(encoding="utf-8")

# In-memory storage for weather status
latest_status: dict[str, Any] = {"message": "Waiting for data from sensor..."}


@app.post("/api/weather")
async def receive_weather_data(payload: dict[str, Any]):
    global latest_status
    latest_status = payload
    return {"status": "success"}


@app.get("/api/weather")
async def get_weather_data():
    return latest_status


@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    return HTMLResponse(content=INDEX_HTML)