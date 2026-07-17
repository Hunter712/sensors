from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()
latest_status_string = "Waiting for data from sensor..."

def format_sensor_data(data: dict):
    result = ""
    for sensor_name, sensor_data in data.items():
        result += f"{sensor_data}\n"
    return result

@app.post("/api/weather")
async def receive_weather_data(request: Request):
    global latest_status
    try:
        latest_status = await request.json()
    except Exception as e:
        latest_status = {"error": f"Invalid JSON: {e}"}
    return {"status": "success"}

@app.get("/")
async def get_weather_page():
    headers = {"Refresh": "1", "Content-Type": "application/json; charset=utf-8"}
    return JSONResponse(content=format_sensor_data(latest_status), headers=headers)
