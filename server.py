from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()
latest_status_string = "Waiting for data from sensor..."

def format_data(data: dict):
    lines = []
    for name, metrics in data.items():
        parts = [f"{name} - "]
        if "temperature" in metrics:
            parts.append(f"temp: {metrics['temperature']:.2f}°C({metrics.get('temperature_rating','')})")
        if "humidity" in metrics:
            parts.append(f"hum: {metrics['humidity']:.2f}%({metrics.get('humidity_rating','')})")
        if "pressure" in metrics:
            parts.append(f"press: {metrics['pressure']:.2f}hPa({metrics.get('pressure_rating','')})")
        if "gas" in metrics:
            parts.append(f"gas: {metrics['gas']:.2f}Ohm({metrics.get('gas_rating','')})")
        lines.append(" ".join(parts))
    return "\n".join(lines)

@app.post("/api/weather")
async def receive_weather_data(request: Request):
    global latest_status
    try:
        latest_status = await request.json()
    except Exception as e:
        latest_status = {"error": f"Invalid JSON: {e}"}
    return {"status": "success"}

@app.get("/", response_class=PlainTextResponse)
async def get_weather_page():
    if "error" in latest_status:
        body = latest_status["error"]
    elif latest_status.get("message"):
        body = latest_status["message"]
    else:
        body = format_data(latest_status)

    headers = {"Refresh": "1"}
    return PlainTextResponse(content=body, headers=headers)
