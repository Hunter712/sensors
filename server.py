from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()
latest_status_string = "Waiting for data from sensor..."

@app.post("/api/weather")
async def receive_weather_data(request: Request):
    global latest_status_string
    raw_body = await request.body()
    latest_status_string = raw_body.decode('utf-8')
    return {"status": "success"}

@app.get("/", response_class=PlainTextResponse)
async def get_weather_page():
    headers = {"Refresh": "1"}
    return PlainTextResponse(content=latest_status_string, headers=headers)
