from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from automation_hub.api import router
from automation_hub.database import initialize

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize()
    yield


app = FastAPI(title="AI Automation Hub", version="0.1.0", lifespan=lifespan)
app.include_router(router)
app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "execution_mode": "simulation"}


def run() -> None:
    import uvicorn
    uvicorn.run("automation_hub.main:app", host="0.0.0.0", port=8000)

