import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

app = FastAPI()
latest_status = {"message": "Waiting for data from sensor..."}
TEMPLATE = pathlib.Path("templates/index.html").read_text(encoding="utf-8")

def build_html(data: dict):
    cards = []
    for sensor_name, sensor_data in data.items():
        parts = [f"<div class='card'><h3>{sensor_name}</h3>"]
        for metric_name, value in sensor_data.items():
            parts.append(f"<p>{metric_name}: {value}</p>")
        parts.append("</div>")
        cards.append("".join(parts))
    return "<div class='cards'>" + "".join(cards) + "</div>"

@app.post("/api/weather")
async def receive_weather_data(request: Request):
    global latest_status
    try:
        latest_status = await request.json()
    except Exception as e:
        latest_status = {"error": f"Invalid JSON: {e}"}
    return {"status": "success"}

@app.get("/api/weather", response_class=PlainTextResponse)
async def get_weather_data():
    return build_html(latest_status)

@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    return HTMLResponse(content=TEMPLATE)
