import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()
latest_status = {"message": "Waiting for data from sensor..."}
latest_lightning = {"status": "clear", "message": "No lightning events recorded."}

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
    """Stores incoming lightning strike metrics."""
    global latest_lightning
    try:
        latest_lightning = await request.json()
    except Exception as e:
        latest_lightning = {"error": f"Invalid JSON: {e}"}
    return {"status": "success"}


@app.get("/api/lightning")
async def get_lightning_data():
    """Returns current lightning status payload."""
    return latest_lightning

@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    html = pathlib.Path("templates/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)