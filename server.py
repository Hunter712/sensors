import pathlib
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()
latest_status_string = "Waiting for data from sensor..."

def format_data(data: dict):
    result = []
    for sensor_name in data:
        result.append("\n".join(data[sensor_name]))
    return result

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
