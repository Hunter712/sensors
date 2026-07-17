import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()
latest_status = {"message": "Waiting for data from sensor..."}

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


@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    html = pathlib.Path("templates/index.html").read_text(encoding="utf-8")
    return HTMLResponse(content=html)