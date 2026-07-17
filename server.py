import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()
latest_status = "Waiting for data from sensor..."
TEMPLATE = pathlib.Path("templates/index.html").read_text(encoding="utf-8")

def build_html(data: dict):
    cards = []
    for sensor_name, sensor_data in data.items():
        parts = [f"<b>{sensor_name}</b>"]
        for metric_name, value in sensor_data.items():
            rating = sensor_data.get(f"{metric_name}_rating", "")
            if rating:
                parts.append(f"{metric_name}: {value} ({rating})")
            else:
                parts.append(f"{metric_name}: {value}")

        cards.append("<p>" + "<br>".join(parts) + "</p>")

    return "\n".join(cards)

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
    return build_html(latest_status)

@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    return HTMLResponse(content=TEMPLATE)
