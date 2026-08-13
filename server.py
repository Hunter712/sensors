import json
import pathlib
from typing import List, Dict, Any
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

# Path configuration
LIGHTNING_FILE = pathlib.Path("lightning_events.json")

# In-memory storage for weather status
latest_status = {"message": "Waiting for data from sensor..."}


def load_lightning_events() -> List[Dict[str, Any]]:
    """Reads and returns all recorded lightning events from the JSON file."""
    if not LIGHTNING_FILE.exists():
        return []
    try:
        content = LIGHTNING_FILE.read_text(encoding="utf-8")
        return json.loads(content) if content.strip() else []
    except Exception as e:
        print(f"Error reading lightning storage file: {e}")
        return []


def save_lightning_events(events: List[Dict[str, Any]]) -> None:
    """Writes the updated list of lightning events to the JSON file."""
    try:
        LIGHTNING_FILE.write_text(json.dumps(events, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"Error writing lightning storage file: {e}")


@app.post("/api/weather")
async def receive_weather_data(request: Request):
    global latest_status
    try:
        latest_status = await request.json()
    except Exception as e:
        latest_status = {"error": f"Invalid JSON: {e}"}
    return {"status": "success"}


@app.get("/api/weather")
async def get_weather_data():
    return latest_status


@app.post("/api/lightning")
async def receive_lightning_data(request: Request):
    """Appends incoming lightning strike payload to JSON file storage."""
    try:
        payload = await request.json()
        events = load_lightning_events()
        events.append(payload)
        save_lightning_events(events)
        return {"status": "success"}
    except Exception as e:
        return {"error": f"Invalid JSON or file write error: {e}"}


@app.get("/api/lightning")
async def get_lightning_data():
    """Returns all recorded lightning strike events from the JSON file."""
    return load_lightning_events()


@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    html = pathlib.Path("templates/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)