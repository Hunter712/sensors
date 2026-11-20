import json
import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse

app = FastAPI()

INDEX_FILE = Path(__file__).resolve().parent / "templates" / "index.html"

latest_status: dict[str, Any] = {
    "data": {"message": "Waiting for data from sensor..."},
    "updated_at": None
}
subscribers: set[asyncio.Queue] = set()


def get_sse_payload() -> str:
    payload = {
        **latest_status,
        "server_time": datetime.now(timezone.utc).isoformat()
    }
    return f"data: {json.dumps(payload)}\n\n"


def broadcast(message: str) -> None:
    for q in list(subscribers):
        if q.full():
            q.get_nowait()
        q.put_nowait(message)


@app.post("/api/weather")
async def receive_weather_data(payload: dict[str, Any]):
    global latest_status
    latest_status = {
        "data": payload,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    broadcast(get_sse_payload())
    return {"status": "success"}


@app.get("/api/weather/stream")
async def stream_weather():
    queue = asyncio.Queue(maxsize=1)
    subscribers.add(queue)

    async def event_generator():
        yield get_sse_payload()
        try:
            while True:
                yield await queue.get()
        finally:
            subscribers.discard(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/", response_class=HTMLResponse)
async def get_weather_page():
    return HTMLResponse(content=INDEX_FILE.read_text(encoding="utf-8"))