from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .routes import overview, atebox, video

app = FastAPI(title="Aishow GUI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(overview.router, prefix="/overview", tags=["overview"])
app.include_router(atebox.router, prefix="/atebox", tags=["atebox"])
app.include_router(video.router, prefix="/video", tags=["video"])


@app.get("/healthz")
async def healthz():
    return {"ok": True}
